"""RAG service with event emission."""
import time
import logging
from typing import List

from shared.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    RetrievalSource,
)
from shared.interfaces.retrieval import RetrievalStrategy
from shared.events.publisher import emit_event

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

    async def answer(
        self, request: ChatRequest
    ) -> ChatResponse:
        query = request.messages[-1].content
        cid = request.correlation_id
        total_start = time.time()

        # ── Event: RAG started ──────────────────────
        await emit_event(
            "rag.request.started",
            correlation_id=cid,
            layer="intelligence",
            payload={"query": query[:100]},
        )

        # ── STEP 1: Vector Search ──────────────────
        await emit_event(
            "rag.search.started",
            correlation_id=cid,
            layer="intelligence",
            payload={"search_layer": "vector"},
        )

        start = time.time()
        sources = await self.vector.search(query, top_k=5)
        vector_ms = round((time.time() - start) * 1000, 2)

        await emit_event(
            "rag.search.vector.completed",
            correlation_id=cid,
            layer="intelligence",
            payload={
                "search_layer": "vector",
                "results_count": len(sources),
                "best_score": sources[0].score
                if sources
                else 0,
                "latency_ms": vector_ms,
            },
        )

        good_sources = [
            s
            for s in sources
            if s.score >= VECTOR_SCORE_THRESHOLD
        ]
        search_layer = "vector"

        # ── STEP 2: Local Fallback ─────────────────
        if not good_sources:
            await emit_event(
                "rag.search.started",
                correlation_id=cid,
                layer="intelligence",
                payload={
                    "search_layer": "local",
                    "reason": "vector_below_threshold",
                    "vector_best_score": sources[0].score
                    if sources
                    else 0,
                },
            )

            start = time.time()
            local_sources = await self.local.search(query)
            local_ms = round(
                (time.time() - start) * 1000, 2
            )

            await emit_event(
                "rag.search.local.completed",
                correlation_id=cid,
                layer="intelligence",
                payload={
                    "search_layer": "local",
                    "results_count": len(local_sources),
                    "latency_ms": local_ms,
                },
            )

            if local_sources:
                good_sources = local_sources
                search_layer = "local"
            else:
                # ── STEP 3: S3 Fallback ────────────
                await emit_event(
                    "rag.search.started",
                    correlation_id=cid,
                    layer="intelligence",
                    payload={
                        "search_layer": "s3",
                        "reason": "local_empty",
                    },
                )

                start = time.time()
                s3_sources = await self.s3.search(query)
                s3_ms = round(
                    (time.time() - start) * 1000, 2
                )

                await emit_event(
                    "rag.search.s3.completed",
                    correlation_id=cid,
                    layer="intelligence",
                    payload={
                        "search_layer": "s3",
                        "results_count": len(s3_sources),
                        "latency_ms": s3_ms,
                    },
                )

                if s3_sources:
                    good_sources = s3_sources
                    search_layer = "s3"

        # ── Event: Search complete ─────────────────
        await emit_event(
            "rag.search.completed",
            correlation_id=cid,
            layer="intelligence",
            payload={
                "final_search_layer": search_layer,
                "total_sources": len(good_sources),
                "source_paths": [
                    s.source_path
                    for s in good_sources[:3]
                ],
            },
        )

        # ── BUILD PROMPT ───────────────────────────
        if good_sources:
            context_parts = []
            for s in good_sources[:5]:
                context_parts.append(
                    f"[Source: {s.source_path} | "
                    f"Score: {s.score}]\n{s.content}"
                )
            context_text = "\n\n---\n\n".join(
                context_parts
            )

            system_msg = ChatMessage(
                role="system",
                content=(
                    "You are a helpful assistant. "
                    "Answer using ONLY the context below. "
                    "If the answer is in the context, "
                    "provide it clearly. If not, say so.\n\n"
                    f"CONTEXT:\n{context_text}"
                ),
            )
            augmented_messages = (
                [system_msg] + request.messages
            )
        else:
            augmented_messages = request.messages

        # ── CALL LLM ──────────────────────────────
        await emit_event(
            "rag.llm.calling",
            correlation_id=cid,
            layer="intelligence",
            payload={
                "has_context": bool(good_sources),
                "context_chunks": len(good_sources),
            },
        )

        augmented_request = ChatRequest(
            messages=augmented_messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            correlation_id=cid,
        )

        response = await self.llm_chat(augmented_request)
        response.sources = (
            good_sources[:5] if good_sources else []
        )

        total_ms = round(
            (time.time() - total_start) * 1000, 2
        )

        # ── Event: RAG completed ───────────────────
        await emit_event(
            "rag.request.completed",
            correlation_id=cid,
            layer="intelligence",
            payload={
                "search_layer": search_layer,
                "sources_count": len(response.sources),
                "provider": response.provider,
                "tokens_used": response.tokens_used,
                "total_latency_ms": total_ms,
            },
        )

        return response