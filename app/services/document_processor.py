from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from pathlib import Path
from datetime import datetime
from loguru import logger
import tiktoken

class DocumentProcessor:
    def __init__(self):
        self.converter = DocumentConverter()
        self.chunker = HybridChunker()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def process_document(
            self,
            file_path: str,
            file_type: str,
    ) -> tuple[list[str],list[dict]]:
        """
        Process document and return chunks with metadata
        Returns: (chunks, metadata_list)
        """
        try:
            result = self.converter.convert(file_path)
            doc = result.document

            chunk_iter = self.chunker.chunk(doc)

            chunks = []
            metadatas = []

            for idx, chunk in enumerate(chunk_iter):
                content = chunk.text
                chunks.append(content)

                metadata = self._create_metadata()
        except Exception as e:
            logger.info(f"Document processing error: {e}")
            raise