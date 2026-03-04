import logging
from typing import List, Optional

from shared.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    RetrievalSource,
)
from shared.interfaces.retrieval import RetrievalStrategy

logger = logging.getLogger(__name__)

VECTOR_SCORE_THRESHOLD = 0.4


class RAGService:
    def __init__(
        self,
        vector_retriever: RetrievalStrategy,
        local_retriever: RetrievalStrategy,
        s3_retriever: RetrievalStrategy,
        llm_chat_fn,
    ):
        self.vector = vector_retriever
        self.local = local_retriever
        self.s3 = s3_retriever
        self.llm_chat = llm_chat_fn

    async def answer(self, request: ChatRequest) -> ChatResponse:
        query = request.messages[-1].content
        cid = request.correlation_id

        # ── FALLBACK CHAIN ──────────────────────────────

        # 1. Vector Search
        logger.info(f"[{cid}] Step 1: Vector search...")
        sources = await self.vector.search(query, top_k=5)

        search_layer = "vector"
        good_sources = [
            s for s in sources
            if s.score >= VECTOR_SCORE_THRESHOLD
        ]

        if not good_sources:
            # 2. Local Search
            logger.info(
                f"[{cid}] Step 2: Vector weak "
                f"(best={sources[0].score if sources else 'none'}), "
                f"trying local..."
            )
            local_sources = await self.local.search(query)
            if local_sources:
                good_sources = local_sources
                search_layer = "local"
            else:
                # 3. S3 Search
                logger.info(
                    f"[{cid}] Step 3: Local empty, trying S3..."
                )
                s3_sources = await self.s3.search(query)
                if s3_sources:
                    good_sources = s3_sources
                    search_layer = "s3"

        logger.info(
            f"[{cid}] Found {len(good_sources)} sources "
            f"from {search_layer}"
        )

        # ── BUILD PROMPT ────────────────────────────────

        if good_sources:
            context_parts = []
            for s in good_sources[:5]:
                context_parts.append(
                    f"[Source: {s.source_path} | "
                    f"Score: {s.score}]\n{s.content}"
                )
            context_text = "\n\n---\n\n".join(context_parts)

            system_msg = ChatMessage(
                role="system",
                content=(
                    "You are a helpful assistant. Answer the "
                    "user's question using ONLY the context below. "
                    "If the answer is in the context, provide it "
                    "clearly. If not found, say so.\n\n"
                    f"CONTEXT:\n{context_text}"
                ),
            )
            augmented_messages = [system_msg] + request.messages
        else:
            augmented_messages = request.messages
            logger.info(f"[{cid}] No sources found anywhere")

        # ── CALL LLM ───────────────────────────────────

        augmented_request = ChatRequest(
            messages=augmented_messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            correlation_id=request.correlation_id,
        )

        response = await self.llm_chat(augmented_request)
        response.sources = good_sources[:5] if good_sources else []

        return response