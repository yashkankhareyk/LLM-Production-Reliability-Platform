"""Vector retrieval with keyword + exact match filtering."""
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

    def __init__(
        self,
        store_path: str,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.store_path = Path(store_path).resolve()
        self.store_path.mkdir(parents=True, exist_ok=True)

        self.index_path = self.store_path / "index.faiss"
        self.docs_path = self.store_path / "documents.json"

        logger.info(f"Vector store path: {self.store_path}")

        if VECTOR_AVAILABLE:
            logger.info(
                f"Loading embedding model: {model_name}"
            )
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
            self.index = faiss.read_index(
                str(self.index_path)
            )
            with open(self.docs_path, "r") as f:
                self.documents = json.load(f)
            logger.info(
                f"Loaded vector store: "
                f"{len(self.documents)} docs"
            )
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []
            logger.info("Created empty vector store")

    def ingest(
        self, texts: List[str], source_paths: List[str]
    ):
        if not VECTOR_AVAILABLE:
            raise RuntimeError("Vector deps not installed")
        if not texts:
            return

        self.store_path.mkdir(parents=True, exist_ok=True)

        embeddings = self.encoder.encode(
            texts,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        embeddings = np.array(embeddings).astype("float32")

        self.index.add(embeddings)

        for text, path in zip(texts, source_paths):
            self.documents.append(
                {"content": text, "source_path": path}
            )

        self.store_path.mkdir(parents=True, exist_ok=True)

        faiss.write_index(
            self.index, str(self.index_path.resolve())
        )
        with open(
            str(self.docs_path.resolve()), "w"
        ) as f:
            json.dump(self.documents, f, indent=2)

        logger.info(
            f"Ingested {len(texts)} chunks. "
            f"Total: {len(self.documents)}"
        )

    def clear(self):
        if VECTOR_AVAILABLE:
            self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = []

        if self.index_path.exists():
            self.index_path.unlink()
        if self.docs_path.exists():
            self.docs_path.unlink()

        self.store_path.mkdir(parents=True, exist_ok=True)
        logger.info("Vector store cleared")

    def _extract_query_names(
        self, query: str
    ) -> List[str]:
        query_lower = query.lower()

        stop_words = {
            "give", "me", "details", "of", "about",
            "what", "is", "the", "who", "how", "much",
            "does", "tell", "show", "find", "get",
            "salary", "department", "information",
            "info", "data", "record", "employee",
            "please", "can", "you", "for", "their",
            "his", "her", "and", "or", "in", "at",
            "from", "with", "performance", "score",
            "rating", "job", "title", "position",
            "works", "working", "work",
        }

        words = query_lower.split()
        name_words = [
            w
            for w in words
            if w not in stop_words and len(w) > 1
        ]

        names = []
        if name_words:
            names.append(" ".join(name_words))
            for w in name_words:
                if len(w) > 2:
                    names.append(w)

        return names

    def _score_document(
        self,
        content: str,
        query: str,
        vector_score: float,
    ) -> float:
        content_lower = content.lower()
        query_lower = query.lower()

        # Signal 1: Keyword matching
        query_terms = [
            term
            for term in query_lower.split()
            if len(term) > 2
        ]

        if query_terms:
            keyword_matches = sum(
                1
                for term in query_terms
                if term in content_lower
            )
            keyword_score = keyword_matches / len(
                query_terms
            )
        else:
            keyword_score = 0

        # Signal 2: Exact name matching
        names = self._extract_query_names(query)
        name_score = 0

        for name in names:
            if name in content_lower:
                name_score = 1.0
                break
            name_parts = name.split()
            parts_found = sum(
                1
                for part in name_parts
                if part in content_lower and len(part) > 2
            )
            if name_parts and parts_found > 0:
                partial = parts_found / len(name_parts)
                name_score = max(name_score, partial)

        # Combine signals
        if name_score >= 1.0:
            combined = (
                name_score * 0.6
                + keyword_score * 0.2
                + vector_score * 0.2
            )
        elif name_score > 0:
            combined = (
                name_score * 0.4
                + keyword_score * 0.3
                + vector_score * 0.3
            )
        elif keyword_score > 0:
            combined = (
                keyword_score * 0.5
                + vector_score * 0.5
            )
        else:
            combined = vector_score * 0.3

        return round(combined, 4)

    async def search(
        self, query: str, top_k: int = 5
    ) -> List[RetrievalSource]:
        if not VECTOR_AVAILABLE or self.index is None:
            return []
        if self.index.ntotal == 0:
            return []

        fetch_k = min(
            max(top_k * 10, 50), self.index.ntotal
        )

        query_vec = self.encoder.encode(
            [query], normalize_embeddings=True
        )
        query_vec = np.array(query_vec).astype("float32")

        scores, indices = self.index.search(
            query_vec, fetch_k
        )

        scored_results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            doc = self.documents[idx]

            combined_score = self._score_document(
                content=doc["content"],
                query=query,
                vector_score=float(score),
            )

            scored_results.append(
                {
                    "content": doc["content"],
                    "source_path": doc["source_path"],
                    "vector_score": round(
                        float(score), 4
                    ),
                    "combined_score": combined_score,
                }
            )

        scored_results.sort(
            key=lambda x: x["combined_score"],
            reverse=True,
        )

        results = []
        for item in scored_results[:top_k]:
            results.append(
                RetrievalSource(
                    content=item["content"],
                    source_type="vector",
                    source_path=item["source_path"],
                    score=item["combined_score"],
                )
            )

        if results:
            logger.info(
                f"Vector search: '{query}' → "
                f"top: {results[0].source_path} "
                f"(combined={results[0].score}, "
                f"vector={scored_results[0]['vector_score']})"
            )
        else:
            logger.info(
                f"Vector search: '{query}' → no results"
            )

        return results

    async def health_check(self) -> bool:
        return VECTOR_AVAILABLE and self.index is not None