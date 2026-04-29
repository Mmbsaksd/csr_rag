from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    SparseVector, SparseVectorParams, Modifier,
    Prefetch, FusionQuery, Fusion
)
from app.config import get_settings
from app.services.sparse_vector_service import SparseVectorService
from loguru import logger
from uuid import uuid4

class VectorStore:
    def __init__(self):
        self.settings = get_settings()
        self.client = QdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key
        )
        self.collection_name = self.settings.qdrant_collection_name
        self.sparse_service = SparseVectorService()
        self._ensure_collection()

    def _ensure_collection(self):
        """Create hybrid collection with dense and sparse vectors if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "dense": VectorParams(
                            size=self.settings.embedding_dimensions,
                            distance=Distance.COSINE
                        )
                    },
                    sparse_vectors_config={
                        "sparse": SparseVectorParams()
                    }
                )
                logger.info(f"Created hybrid collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Collection creation error: {e}")
            raise

    def upsert_chunks(
            self,
            chunks: list[str],
            embeddings: list[list[float]],
            metadatas: list[dict]
    ) -> list[str]:
        """Insert chunks with both dense and sparse vectors"""
        points = []
        chunk_ids = []

        for chunk, embedding, metadata in zip(chunks, embeddings, metadatas):
            chunk_id = str(uuid4())
            chunk_ids.append(chunk_id)

            sparse_vector = self.sparse_service.generate_sparse_vector(chunk)
            points.append(PointStruct(
                id=chunk_id,
                vector={
                    "dense": embedding,
                    "sparse": sparse_vector
                },
                payload={
                    "content": chunk,
                    **metadata
                }
            ))

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} chunks with dual vectors")
            return chunk_ids
        except Exception as e:
            logger.error(f"Upsert error: {e}")
            raise

    def search_dense(
            self,
            query_vector: list[float],
            top_k: int,
            search_filter=None
    )-> list:
        """Dense-only semantic search"""
        return self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            using="dense",
            query_filter=search_filter,
            limit=top_k,
            with_payload=True
        ).points

    def search_sparse(
            self,
            query_text: str,
            top_k: int,
            search_filter=None
    )-> list:
        """Sparse-only keyword search (BM25)"""
        sparse_query = self.sparse_service.generate_sparse_vector(query_text)

        return self.client.query_points(
            collection_name=self.collection_name,
            query=sparse_query,
            using="sparse",
            query_filter=search_filter,
            limit=top_k,
            with_payload=True
        ).points
    
    def search_hybrid(
            self,
            query_vector: list[float],
            query_text: str,
            top_k: int,
            search_filter=None
    )-> list:
        """Hybrid search with RRF fusion"""

        sparse_query = self.sparse_service.generate_sparse_vector(query_text)
        
        return self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(query=sparse_query, using='sparse', limit=top_k *3),
                Prefetch(query=query_vector, using="dense", limit=top_k * 3)
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            query_filter=search_filter,
            limit=top_k,
            with_payload=True
        ).points
    
    def search(
            self,
            query_vector: list[float],
            top_k: int = 5,
            filter_conditions: dict | None = None,
            mode: str = "hybrid",
            query_text: str | None = None
    ) -> list[dict]:
        """
        Search for similar chunks using specified mode.

        Args:
            query_vector: Dense embedding vector
            top_k: Number of results to return
            filter_conditions: Optional filter conditions
            mode: Search mode - "dense", "sparse", or "hybrid" (default)
            query_text: Original query text (required for sparse/hybrid modes)

        Returns:
            List of search results with scores and metadata
        """
        try:
            search_filter = None
            if filter_conditions:
                pass

            if mode == "dense":
                results = self.search_dense(query_vector, top_k, search_filter)

            elif mode == "sparse":
                if not query_text:
                    raise ValueError("query_text required for sparse search")
                results = self.search_sparse(query_text, top_k, search_filter)
            
            elif mode == "hybrid":
                if not query_text:
                    raise ValueError("query_text required for hybrid search")
                results = self.search_hybrid(query_vector, query_text, top_k, search_filter)
            
            else:
                raise ValueError(f"Invalid search mode: {mode}. Must be 'dense', 'sparse', or 'hybrid'")
            
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "content": hit.payload.get("content"),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "content"}
                }
                for hit in results
            ]

        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    def delete_by_source(self, source_file: str):
        """Delete all chunks from a source file"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="source_file",
                            match=MatchValue(value=source_file)
                        )
                    ]
                )
            )
        except Exception as e:
            logger.error(f"Delete error: {e}")
            raise
