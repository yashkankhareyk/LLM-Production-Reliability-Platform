"""Local file search — keyword-based fallback."""
import os
import logging
from typing import List
from pathlib import Path

from shared.interfaces.retrieval import RetrievalStrategy
from shared.schemas.chat import RetrievalSource

logger = logging.getLogger(__name__)


class LocalFileRetrieval(RetrievalStrategy):
    """
    Simple keyword search through local text files.
    Fallback when vector search returns no good results.
    """

    def __init__(self, docs_dir: str):
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    async def search(
        self, query: str, top_k: int = 3
    ) -> List[RetrievalSource]:
        results = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        if not self.docs_dir.exists():
            return results

        for filepath in self.docs_dir.rglob("*.txt"):
            try:
                content = filepath.read_text(encoding="utf-8")
                content_lower = content.lower()

                # Score based on term frequency
                matches = sum(
                    1 for term in query_terms if term in content_lower
                )
                if matches == 0:
                    continue

                score = matches / len(query_terms)

                results.append(
                    RetrievalSource(
                        content=content[:500],  # First 500 chars
                        source_type="local",
                        source_path=str(filepath),
                        score=round(score, 4),
                    )
                )
            except Exception as e:
                logger.warning(f"Error reading {filepath}: {e}")
                continue

        # Sort by score, return top_k
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    async def health_check(self) -> bool:
        return self.docs_dir.exists()