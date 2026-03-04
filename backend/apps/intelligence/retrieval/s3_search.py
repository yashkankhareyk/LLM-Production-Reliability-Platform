"""S3/MinIO search — deepest fallback layer."""
import logging
from typing import List

from shared.interfaces.retrieval import RetrievalStrategy
from shared.schemas.chat import RetrievalSource

logger = logging.getLogger(__name__)


class S3Retrieval(RetrievalStrategy):
    """
    Searches documents stored in S3/MinIO.
    For MVP: uses a local mock directory.
    Later: connects to real S3/MinIO.
    """

    def __init__(self, bucket_path: str = "./data/s3_mock"):
        from pathlib import Path

        self.bucket_path = Path(bucket_path)
        self.bucket_path.mkdir(parents=True, exist_ok=True)

    async def search(
        self, query: str, top_k: int = 3
    ) -> List[RetrievalSource]:
        results = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        for filepath in self.bucket_path.rglob("*.*"):
            if filepath.suffix not in [".txt", ".md", ".json"]:
                continue

            try:
                content = filepath.read_text(encoding="utf-8")
                content_lower = content.lower()

                matches = sum(
                    1 for term in query_terms if term in content_lower
                )
                if matches == 0:
                    continue

                score = matches / len(query_terms)

                results.append(
                    RetrievalSource(
                        content=content[:500],
                        source_type="s3",
                        source_path=f"s3://mock/{filepath.name}",
                        score=round(score, 4),
                    )
                )
            except Exception as e:
                logger.warning(f"Error reading {filepath}: {e}")

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    async def health_check(self) -> bool:
        return self.bucket_path.exists()