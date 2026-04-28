"""
Sparse Vector Service for BM25-style keyword search.
Generates sparse vectors from text using tokenization and term frequency analysis.
"""
import re
from collections import Counter
from typing import List, Dict
from qdrant_client.models import SparseVector

class SparseVectorService:
    """Service for generating sparse vectors for BM25-style search."""

    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'this', 'but', 'they', 'have', 'had',
        'what', 'when', 'where', 'who', 'which', 'why', 'how', 'or', 'if',
        'each', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'can', 'just', 'should', 'now'
    }


    def tokenize(self, text: str)-> List[str]:
        """
        Tokenize text into individual terms.

        Args:
            text: Input text to tokenize

        Returns:
            List of lowercase tokens with stop words removed
        """
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+(?:-[a-z0-9]+)*\b', text)
        tokens = [t for t in tokens if t not in self.STOP_WORDS]
        return tokens
    
    def _hash_token(self, token: str) -> int:
        """
        Hash a token to a consistent index.
        Uses Python's built-in hash function with modulo to create stable indices.

        Args:
            token: Token to hash

        Returns:
            Integer index in sparse vector space
        """
        return abs(hash(token))%(2**32)
    
    def generate_sparse_vector(self, text: str)-> SparseVector:
        """
        Generate a sparse vector from text using BM25-style tokenization.

        Args:
            text: Input text to convert to sparse vector

        Returns:
            SparseVector with token indices and term frequencies
        """
        tokens = self.tokenize(text)
        term_frequencies = Counter(tokens)

        indices = []
        values = []

        for token, freq in term_frequencies.items():
            index = self._hash_token(token)
            indices.append(index)
            values.append(float(freq))

        return SparseVector(indices=indices, values=values)
    
    def generate_sparse_vectors_batch(self, texts: List[str])-> List[SparseVector]:
        """
        Generate sparse vectors for multiple texts.

        Args:
            texts: List of texts to convert to sparse vectors

        Returns:
            List of SparseVectors
        """
        return [self.generate_sparse_vector(text) for text in texts]