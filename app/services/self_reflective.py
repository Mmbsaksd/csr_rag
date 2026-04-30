from app.services.llm_service import LLMService
from app.models import ReflectionResult, SelfReflectiveResult, RetrievedChunk
from app.config import get_settings
from datetime import datetime
from loguru import logger
import json

class SelfReflectiveService:
    def __init__(self):
        self.settings = get_settings()
        self.llm = LLMService()

    def generate_initial_answer(
            self,
            query: str,
            retrieved_chunks: list[RetrievedChunk]
    )-> str:
        """Generate initial answer from retrieved chunks"""

        context = "\n\n".join([
            f"Document {i}: \n{chunk.content}"
            for i, chunk in enumerate(retrieved_chunks)
        ])

        prompt = f"""Answer the following query using the provided documents.

Query: {query}

Documents:
{context}

Provide a clear, accurate answer."""
        
        system_prompt = "You are a helpful assistant that answers questions based on provided context."

        return self.llm.generate_response(prompt, system_prompt)
    
    def reflect_on_answer()

