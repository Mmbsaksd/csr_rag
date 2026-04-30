from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding="utf-8")

    # Azure OpenAI
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_api_version: str

    #Tavily
    tavily_api_key: str


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

    # HYDE Settings
    hyde_num_hypotheses: int = 3
    hyde_enabled_by_default: bool = False

    # Retrieval
    top_k_results: int=3

    # CRAG Settings
    crag_relevance_threshold: float = 0.7
    crag_ambiguous_threshold: float = 0.5



@lru_cache
def get_settings()-> Settings:
    return Settings()