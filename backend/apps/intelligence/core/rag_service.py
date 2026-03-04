# RAG pipeline (rewrite→retrieve→compose)
"""
RAG Service — the core retrieval-augmented generation logic.

Fallback chain: Vector → Local → S3
"""
import logging
from typing import List, Optional

from shared.schemas.chat import (
    ChatRequest, ChatResponse, ChatMessage, RetrievalSource,
)
from shared.interfaces.retrieval import RetrievalStrategy

logger = logging.getLogger(__name__)

# Minimum score to accept vector results before falling back
VECTOR_SCORE_THRESHOLD = 0.3


class RAGService:
    def __init__(
        self,
        vector_retriever: RetrievalStrategy,
        local_retriever: RetrievalStrategy,
        s3_retriever: RetrievalStrategy,
        llm_chat_fn,  # async callable: (ChatRequest) -> ChatResponse
    ):
        self.vector = vector_retriever
        self.local = local_retriever
        self.s3 = s3_retriever
        self.llm_chat = llm_chat_fn

    async def answer(self, request: ChatRequest) -> ChatResponse:
        query = request.messages[-1].content
        cid = request.correlation_id

        # === FALLBACK CHAIN ===

        # 1. Try Vector Search
        logger.info(f"[{cid}] Searching vector store...")
        sources = await self.vector.search(query)
        search_layer = "vector"

        if not sources or sources[0].score < VECTOR_SCORE_THRESHOLD:
            # 2. Try Local Files
            logger.info(
                f"[{cid}] Vector insufficient "
                f"(score={sources[0].score if sources else 'none'}), "
                f"trying local..."
            )
            local_sources = await self.local.search(query)
            if local_sources:
                sources = local_sources
                search_layer = "local"
            else:
                # 3. Try S3
                logger.info(f"[{cid}] Local empty, trying S3...")
                s3_sources = await self.s3.search(query)
                if s3_sources:
                    sources = s3_sources
                    search_layer = "s3"

        logger.info(
            f"[{cid}] Found {len(sources)} sources from {search_layer}"
        )

        # === BUILD AUGMENTED PROMPT ===
        if sources:
            context_text = "\n\n---\n\n".join(
                f"[Source: {s.source_type} | {s.source_path} | "
                f"Score: {s.score}]\n{s.content}"
                for s in sources[:3]
            )
            system_msg = ChatMessage(
                role="system",
                content=(
                    "You are a helpful assistant. Use the following "
                    "retrieved context to answer the user's question. "
                    "If the context is not relevant, say so.\n\n"
                    f"CONTEXT:\n{context_text}"
                ),
            )
            augmented_messages = [system_msg] + request.messages
        else:
            augmented_messages = request.messages
            logger.info(f"[{cid}] No sources found, direct LLM call")

        # === CALL LLM ===
        augmented_request = ChatRequest(
            messages=augmented_messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            correlation_id=request.correlation_id,
        )

        response = await self.llm_chat(augmented_request)
        response.sources = sources[:3] if sources else []

        return response