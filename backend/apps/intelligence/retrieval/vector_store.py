"""Vector retrieval using FAISS + sentence-transformers."""
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
    logger.warning(
        "faiss/sentence-transformers not installed. "
        "Run: pip install faiss-cpu sentence-transformers"
    )


class VectorStoreRetrieval(RetrievalStrategy):

    def __init__(
        self,
        store_path: str,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)

        self.index_path = self.store_path / "index.faiss"
        self.docs_path = self.store_path / "documents.json"

        if VECTOR_AVAILABLE:
            logger.info(f"Loading embedding model: {model_name}")
            self.encoder = SentenceTransformer(model_name)
            self.dimension = (
                self.encoder.get_sentence_embedding_dimension()
            )
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
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []
            logger.info("Created empty vector store")

    def ingest(self, texts: List[str], source_paths: List[str]):
        """Add documents to the vector store."""
        if not VECTOR_AVAILABLE:
            raise RuntimeError(
                "Vector dependencies not installed. "
                "Run: pip install faiss-cpu sentence-transformers"
            )

        if not texts:
            return

        # Encode
        embeddings = self.encoder.encode(
            texts, show_progress_bar=True, normalize_embeddings=True
        )
        embeddings = np.array(embeddings).astype("float32")

        # Add to index
        self.index.add(embeddings)

        # Store documents
        for text, path in zip(texts, source_paths):
            self.documents.append(
                {"content": text, "source_path": path}
            )

        # Persist to disk
        faiss.write_index(self.index, str(self.index_path))
        with open(self.docs_path, "w") as f:
            json.dump(self.documents, f, indent=2)

        logger.info(
            f"Ingested {len(texts)} chunks. "
            f"Total: {len(self.documents)}"
        )

    def clear(self):
        """Delete all documents and reset index."""
        if VECTOR_AVAILABLE:
            self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = []

        if self.index_path.exists():
            self.index_path.unlink()
        if self.docs_path.exists():
            self.docs_path.unlink()

        logger.info("Vector store cleared")

    async def search(
        self, query: str, top_k: int = 3
    ) -> List[RetrievalSource]:
        if not VECTOR_AVAILABLE or self.index is None:
            return []
        if self.index.ntotal == 0:
            return []

        # Encode query
        query_vec = self.encoder.encode(
            [query], normalize_embeddings=True
        )
        query_vec = np.array(query_vec).astype("float32")

        # Search
        scores, indices = self.index.search(query_vec, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue

            doc = self.documents[idx]

            results.append(
                RetrievalSource(
                    content=doc["content"],
                    source_type="vector",
                    source_path=doc["source_path"],
                    score=round(float(score), 4),
                )
            )

        return results

    async def health_check(self) -> bool:
        return VECTOR_AVAILABLE and self.index is not None