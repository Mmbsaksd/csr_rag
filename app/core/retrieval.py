from app.services.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService
from app.services.hyde import HydeService
from app.models import RetrievedChunk, ChunkMetadata
from app.config import get_settings
from loguru import logger

class RetrievalService:
    def __init__(self):
        self.settings = get_settings()
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
        self.hyde_service = HydeService()
        self._last_hyde_hypotheses = None

    def retrieve(
            self,
            query: str,
            top_k: int = None,
            use_hyde: bool = True,
            search_mode: str = "hybrid"
    ) -> list[RetrievedChunk]:
        """
        Retrieve relevant chunks for query with optional HYDE enhancement.

        Args:
            query: User's query
            top_k: Number of chunks to retrieve
            use_hyde: Whether to use HYDE for query expansion
            search_mode: Search mode - "dense", "sparse", or "hybrid"

        Returns:
            List of retrieved chunks
        """
        if top_k is None:
            top_k = self.settings.top_k_results

        if use_hyde:
            hypotheses = self.hyde_service.generate_hypothetical_documents(query)
            self._last_hyde_hypotheses = hypotheses

            hypothesis_vector = self.embedding_service.embed_batch(hypotheses)

            all_result = []

            for hypothesis, vector in zip(hypotheses, hypothesis_vector):
                results = self.vector_store.search(
                    query_vector=vector,
                    query_text=hypothesis,
                    top_k=top_k,
                    mode=search_mode
                )
                all_result.append(results)
            
            retrieved_chunks = 
