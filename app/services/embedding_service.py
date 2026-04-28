from openai import AzureOpenAI
from app.config import get_settings
from loguru import logger

class EmbeddingService:
    def __init__(self):
        self.settings = get_settings()
        self.client = AzureOpenAI(
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_endpoint=self.settings.azure_openai_endpoint,
        )
        self.model = self.settings.azure_openai_embedding_deployment_name

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for single text"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    def embed_batch(
            self,
            texts: list[str],
            batch_size: int = 100
    ) -> list[list[float]]:
        """Generate embeddings for batch of texts"""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

            except Exception as e:
                logger.error(f"Batch embedding error: {e}")
                raise

        return embeddings