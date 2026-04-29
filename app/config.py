from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding="utf-8")

    # Azure OpenAI
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_api_version: str


    # Qdrant
    qdrant_url: str
    qdrant_api_key: str 
    qdrant_collection_name: str = "crag_documents"

    #AzureOpenAI Models
    azure_openai_embedding_deployment_name: str = "text-embedding-3-small"
    azure_openai_deployment_name: str = "gpt-4o-mini"
    embedding_dimensions: int = 1536

    #Upload
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024 #50MB



@lru_cache
def get_settings()-> Settings:
    return Settings()