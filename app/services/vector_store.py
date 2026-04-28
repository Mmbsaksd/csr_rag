from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    SparseVector, SparseVectorParams, Modifier,
    Prefetch, FusionQuery, Fusion
)
from app.config import get_settings