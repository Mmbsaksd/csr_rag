from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime



# ============= Response Models =============
class UploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    chunks_created: int
    status: str
    message: str

# ============= Chunk Models =============

class ChunkMetadata(BaseModel):
    chunk_id: str
    source_file: str
    file_type: str
    page_number: Optional[int] = None
    chunk_index: int
    total_chunks: int
    doc_item_type: Optional[str] = None
    parent_heading: Optional[str] = None
    hierarchy_level: Optional[int] = None
    chunk_method: str = "hybrid"
    token_count: int
    char_count: int
    content_preview: str
    keywords: list[str] = []
    created_at: datetime
    processed_at: datetime


class RetrievedChunk(BaseModel):
    content: str
    metadata: ChunkMetadata
    score: float