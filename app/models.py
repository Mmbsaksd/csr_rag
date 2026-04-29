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