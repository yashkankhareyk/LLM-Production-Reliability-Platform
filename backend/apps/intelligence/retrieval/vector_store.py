"""Vector retrieval using FAISS + sentence-transformers."""
import os
import json
import logging
import numpy as np
from typing import List
from pathlib import Path

from shared.interfaces.retrieval import RetrievalStrategy
from shared.schemas.chat import RetrievalSource

logger = logging.getLogger(__name__)

try:
    import faiss
    from sentence_transformers import SentenceTransformer

    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    logger.warning("faiss/sentence-transformers not installed")


class VectorStoreRetrieval(RetrievalStrategy):
    """
    FAISS-based vector search.
    Documents are stored as JSON alongside the FAISS index.
    """

    def __init__(self, store_path: str, model_name: str = "all-MiniLM-L6-v2"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)

        self.index_path = self.store_path / "index.faiss"
        self.docs_path = self.store_path / "documents.json"

        if VECTOR_AVAILABLE:
            self.encoder = SentenceTransformer(model_name)
            self.dimension = self.encoder.get_sentence_embedding_dimension()
            self._load_or_create_index()
        else:
            self.index = None
            self.documents = []

    def _load_or_create_index(self):
        if self.index_path.exists() and self.docs_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.docs_path, "r") as f:
                self.documents = json.load(f)
            logger.info(
                f"Loaded vector store: {len(self.documents)} documents"
            )
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.documents = []
            logger.info("Created empty vector store")

    def ingest(self, texts: List[str], source_paths: List[str]):
        """Add documents to the vector store."""
        if not VECTOR_AVAILABLE:
            raise RuntimeError("Vector dependencies not installed")

        embeddings = self.encoder.encode(texts)
        embeddings = np.array(embeddings).astype("float32")

        self.index.add(embeddings)

        for text, path in zip(texts, source_paths):
            self.documents.append(
                {"content": text, "source_path": path}
            )

        # Persist
        faiss.write_index(self.index, str(self.index_path))
        with open(self.docs_path, "w") as f:
            json.dump(self.documents, f)

        logger.info(f"Ingested {len(texts)} documents")

    async def search(
        self, query: str, top_k: int = 3
    ) -> List[RetrievalSource]:
        if not VECTOR_AVAILABLE or self.index is None:
            return []
        if self.index.ntotal == 0:
            return []

        query_vec = self.encoder.encode([query])
        query_vec = np.array(query_vec).astype("float32")

        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue

            # Convert L2 distance to similarity score (0-1)
            score = 1.0 / (1.0 + float(dist))
            doc = self.documents[idx]

            results.append(
                RetrievalSource(
                    content=doc["content"],
                    source_type="vector",
                    source_path=doc["source_path"],
                    score=round(score, 4),
                )
            )

        return results

    async def health_check(self) -> bool:
        return VECTOR_AVAILABLE and self.index is not None