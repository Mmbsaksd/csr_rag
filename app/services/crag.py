from app.services.llm_service import LLMService
from app.services.web_search import WebSearchService
from app.models import CRAGEvaluation, CRAGResult, RetrievedChunk, ChunkMetadata
from app.config import get_settings
from datetime import datetime
from loguru import logger
import json
import tiktoken

class CRAGService:
    def __init__(self):
        self.settings = get_settings()
        self.llm = LLMService()
        self.web_search = WebSearchService()

    def evaluate_relevance(
            self,
            query: str,
            retrieved_chunks: list[RetrievedChunk],
    )-> CRAGEvaluation:
        """Evaluate if retrieved chunks are relevant to query"""
        context = "\n\n".join([
            f"Chunk {i+1}: {chunk.content[:300]}"
            for i, chunk in enumerate(retrieved_chunks)
        ])


        prompt = f"""Evaluate if the following retrieved documents are relevant to answer the query.

Query: {query}

Retrieved Documents:
{context}

Provide evaluation as JSON:
{{
    "relevance_score": <float 0.0-1.0>,
    "relevance_label": "<relevant|ambiguous|irrelevant>",
    "confidence": <float 0.0-1.0>,
    "reasoning": "<brief explanation>"
}}

Scoring guide:
- relevant (0.7-1.0): Documents directly answer the query
- ambiguous (0.4-0.7): Partial information, may need web search
- irrelevant (0.0-0.4): Documents don't help answer the query
"""
        system_prompt = "You are a relevance evaluator for RAG systems. Always respond with valid JSON."
        
        try:
            response = self.llm.generate_with_json(prompt, system_prompt)
            eval_data = json.loads(response)

            relevance_score = eval_data.get("relevance_score", 0.5)
            relevance_label = eval_data.get("relevance_label", "ambiguous")
            confidence = eval_data.get("confidence", 0.7)

            need_websearch = (
                relevance_label == "irrelevant"  or
                (relevance_label == "ambiguous" and relevance_score < self.settings.crag_ambiguous_threshold)
            )

            return CRAGEvaluation(
                relevance_score=relevance_score,
                relevance_label=relevance_label,
                confidence=confidence,
                evaluation_method="llm_grader",
                needs_web_search=need_websearch,
                evaluated_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Relevance evaluation error: {e}")
            return CRAGEvaluation(
                relevance_score=0.5,
                relevance_label="ambiguous",
                confidence=0.5,
                evaluation_method="llm_grader",
                needs_web_search=True,
                evaluated_at=datetime.utcnow()
            )
        
    def execute_crag(
            self,
            query: str,
            retrieved_chunks: list[RetrievedChunk],
    )-> CRAGResult:
        """Execute Corrective RAG pipeline"""

        # Step 1: Evaluate relevance
        evaluation = self.evaluate_relevance(query, retrieved_chunks)

        logger.info(f"CRAG Evaluation: {evaluation.relevance_label} (score: {evaluation.relevance_score:.2f})")

        web_results = None
        used_web_search = False

        # Step 2: Route based on evaluation
        if evaluation.needs_web_search:
            logger.info("CRAG: Triggering web search")
            web_results = self.web_search.search(query, max_results=3)
            used_web_search=True

        return CRAGResult(
            used_web_search=used_web_search,
            evaluation=evaluation,
            retrieved_chunks=retrieved_chunks,
            web_results=web_results
        )
    
    def generate_answer_with_crag(
            self,
            query: str,
            crag_result: CRAGResult
    ) -> str:
        """Generate final answer using CRAG results"""

        context_parts = []

        if crag_result.evaluation.relevance_label == "irrelevant":
            if crag_result.web_results:
                context_parts.append("=== Web Search Results ===")
                for i, result in enumerate(crag_result.web_results,1):
                    context_parts.append(f"\nSource {i} ({result['title']}): \n{result['content']}")
        else:
            context_parts.append("=== Retrieved Documents ===")
            for i, chunk in enumerate(crag_result.retrieved_chunks,1):
                context_parts.append(f"\nDocument {i}: \n{chunk.content}")

        context = "\n".join(context_parts)

        prompt = f"""Answer the following query using the provided context.

Query: {query}

Context:
{context}

Provide a clear, accurate answer based on the context. If the context doesn't fully answer the query, acknowledge what's missing."""
        
        system_prompt = "You are a helpful assistant that answers questions based on provided context."

        return self.llm.generate(prompt, system_prompt, max_tokens=500)
    

    def get_augmented_chunks(self, crag_results: CRAGResult):
        """
        Get chunks augmented with web search results for use in Corrective RAG.
        Converts web results to RetrievedChunk format.
        """
        chunks = []
        tokenizer = tiktoken.get_encoding("cl100k_base")
        now = datetime.utcnow()

        if crag_results.evaluation.relevance_label == "irrelevant":
            if crag_results.web_results:
                for i, web_result in enumerate(crag_results.web_results):
                    content = web_result['content']
                    token_count = len(tokenizer.encode(content))
                    char_count = len(content)
                    preview = content[:100] if len(content) > 100 else content

                    metadata = ChunkMetadata(
                        chunk_id=f"web_search_{i}",
                        source_file=web_result.get('url','web_search'),
                        file_type="web_search",
                        chunk_index=i,
                        total_chunks=len(crag_results.web_results),
                        chunk_method="web_search",
                        token_count=token_count,
                        char_count=char_count,
                        content_preview=preview,
                        keywords=[],
                        created_at=now,
                        processed_at=now
                    )

                    chunks.append(
                        RetrievedChunk(
                            content=content,
                            score=0.9,
                            metadata=metadata
                        )
                    )
                
        else:
            chunks.extend(crag_results.retrieved_chunks)
            if crag_results.used_web_search and crag_results.web_results:
                for i, web_result in enumerate(crag_results.web_results):
                    content = web_result['content']
                    token_count = len(tokenizer.encode(content))
                    char_count = len(content)
                    preview = content[:100] if len(content) > 100 else content

                    metadata = ChunkMetadata(
                        chunk_id=f"web_augment_{i}",
                        source_file=web_result.get('url','web_search'),
                        file_type="web_search_augmentation",
                        chunk_index=i,
                        total_chunks=len(crag_results.web_results),
                        token_count=token_count,
                        char_count=char_count,
                        content_preview=preview,
                        keywords=[],
                        created_at=now,
                        processed_at=now
                    )
                    chunks.append(
                        RetrievedChunk(
                            content=content,
                            score=0.85,
                            metadata=metadata
                        )
                    )
        return chunks
    

