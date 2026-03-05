# """Vector retrieval using FAISS + sentence-transformers."""
# import os
# import json
# import logging
# import numpy as np
# from typing import List
# from pathlib import Path

# from shared.interfaces.retrieval import RetrievalStrategy
# from shared.schemas.chat import RetrievalSource

# logger = logging.getLogger(__name__)

# try:
#     import faiss
#     from sentence_transformers import SentenceTransformer

#     VECTOR_AVAILABLE = True
# except ImportError:
#     VECTOR_AVAILABLE = False
#     logger.warning("faiss/sentence-transformers not installed")


# class VectorStoreRetrieval(RetrievalStrategy):
#     """
#     FAISS-based vector search.
#     Documents are stored as JSON alongside the FAISS index.
#     """

#     def __init__(self, store_path: str, model_name: str = "all-MiniLM-L6-v2"):
#         self.store_path = Path(store_path)
#         self.store_path.mkdir(parents=True, exist_ok=True)

#         self.index_path = self.store_path / "index.faiss"
#         self.docs_path = self.store_path / "documents.json"

#         if VECTOR_AVAILABLE:
#             self.encoder = SentenceTransformer(model_name)
#             self.dimension = self.encoder.get_sentence_embedding_dimension()
#             self._load_or_create_index()
#         else:
#             self.index = None
#             self.documents = []

#     def _load_or_create_index(self):
#         if self.index_path.exists() and self.docs_path.exists():
#             self.index = faiss.read_index(str(self.index_path))
#             with open(self.docs_path, "r") as f:
#                 self.documents = json.load(f)
#             logger.info(
#                 f"Loaded vector store: {len(self.documents)} documents"
#             )
#         else:
#             self.index = faiss.IndexFlatL2(self.dimension)
#             self.documents = []
#             logger.info("Created empty vector store")

#     def ingest(self, texts: List[str], source_paths: List[str]):
#         """Add documents to the vector store."""
#         if not VECTOR_AVAILABLE:
#             raise RuntimeError("Vector dependencies not installed")

#         embeddings = self.encoder.encode(texts)
#         embeddings = np.array(embeddings).astype("float32")

#         self.index.add(embeddings)

#         for text, path in zip(texts, source_paths):
#             self.documents.append(
#                 {"content": text, "source_path": path}
#             )

#         # Persist
#         faiss.write_index(self.index, str(self.index_path))
#         with open(self.docs_path, "w") as f:
#             json.dump(self.documents, f)

#         logger.info(f"Ingested {len(texts)} documents")

#     async def search(
#         self, query: str, top_k: int = 3
#     ) -> List[RetrievalSource]:
#         if not VECTOR_AVAILABLE or self.index is None:
#             return []
#         if self.index.ntotal == 0:
#             return []

#         query_vec = self.encoder.encode([query])
#         query_vec = np.array(query_vec).astype("float32")

#         distances, indices = self.index.search(query_vec, top_k)

#         results = []
#         for dist, idx in zip(distances[0], indices[0]):
#             if idx == -1:
#                 continue

#             # Convert L2 distance to similarity score (0-1)
#             score = 1.0 / (1.0 + float(dist))
#             doc = self.documents[idx]

#             results.append(
#                 RetrievalSource(
#                     content=doc["content"],
#                     source_type="vector",
#                     source_path=doc["source_path"],
#                     score=round(score, 4),
#                 )
#             )

#         return results

#     async def health_check(self) -> bool:
#         return VECTOR_AVAILABLE and self.index is not None
"""Vector retrieval with keyword filtering for better accuracy."""
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
                f"Loaded vector store: {len(self.documents)} docs"
            )
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []
            logger.info("Created empty vector store")

    def ingest(self, texts: List[str], source_paths: List[str]):
        if not VECTOR_AVAILABLE:
            raise RuntimeError("Vector deps not installed")
        if not texts:
            return

        embeddings = self.encoder.encode(
            texts,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        embeddings = np.array(embeddings).astype("float32")

        # Add to index
        self.index.add(embeddings)

        # Store documents
        for text, path in zip(texts, source_paths):
            self.documents.append(
                {"content": text, "source_path": path}
            )

        faiss.write_index(self.index, str(self.index_path))
        with open(self.docs_path, "w") as f:
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
        logger.info("Vector store cleared")

    def _keyword_filter(
        self, query: str, results: List[dict]
    ) -> List[dict]:
        """
        Re-rank results by checking if query keywords
        actually appear in the document content.

        This fixes the problem where all structured documents
        (CSV rows) get similar vector scores.
        """
        query_lower = query.lower()
        query_terms = [
            term
            for term in query_lower.split()
            if len(term) > 2  # skip short words like "of", "me"
        ]

        if not query_terms:
            return results

        scored = []
        for result in results:
            content_lower = result["content"].lower()

            # Count how many query terms appear in content
            matches = sum(
                1
                for term in query_terms
                if term in content_lower
            )
            keyword_score = matches / len(query_terms)

            # Combined score: keyword match is weighted heavily
            # because vector similarity alone is unreliable
            # for structured data (all rows look similar)
            vector_score = result["vector_score"]

            if keyword_score > 0:
                # Boost documents that contain query keywords
                combined_score = (
                    keyword_score * 0.7 + vector_score * 0.3
                )
            else:
                # Penalize documents without keyword matches
                combined_score = vector_score * 0.3

            scored.append(
                {
                    **result,
                    "keyword_score": keyword_score,
                    "combined_score": round(combined_score, 4),
                }
            )

        # Sort by combined score
        scored.sort(
            key=lambda x: x["combined_score"], reverse=True
        )

        return scored

    async def search(
        self, query: str, top_k: int = 5
    ) -> List[RetrievalSource]:
        if not VECTOR_AVAILABLE or self.index is None:
            return []
        if self.index.ntotal == 0:
            return []

        # Get MORE results from vector search
        # then filter with keywords
        fetch_k = min(top_k * 5, self.index.ntotal)

        query_vec = self.encoder.encode(
            [query], normalize_embeddings=True
        )
        query_vec = np.array(query_vec).astype("float32")

        scores, indices = self.index.search(query_vec, fetch_k)

        # Build raw results
        raw_results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            doc = self.documents[idx]
            raw_results.append(
                {
                    "content": doc["content"],
                    "source_path": doc["source_path"],
                    "vector_score": round(float(score), 4),
                }
            )

        # Apply keyword filtering
        filtered = self._keyword_filter(query, raw_results)

        # Convert to RetrievalSource
        results = []
        for item in filtered[:top_k]:
            results.append(
                RetrievalSource(
                    content=item["content"],
                    source_type="vector",
                    source_path=item["source_path"],
                    score=item["combined_score"],
                )
            )

        # Log what happened
        if results:
            logger.info(
                f"Vector search: '{query}' → "
                f"top result: {results[0].source_path} "
                f"(score: {results[0].score})"
            )
        else:
            logger.info(f"Vector search: '{query}' → no results")

        return results

    async def health_check(self) -> bool:
        return VECTOR_AVAILABLE and self.index is not None