"""
LangGraph nodes — each node is one step in the RAG workflow.
Each node receives state, does work, returns state updates.
"""
import time
import logging
from typing import List

from shared.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    RetrievalSource,
)
from shared.events.publisher import emit_event
from shared.interfaces.retrieval import RetrievalStrategy
from apps.orchestration.core.state import RAGState

logger = logging.getLogger(__name__)

VECTOR_SCORE_THRESHOLD = 0.4


class RAGNodes:
    """All nodes for the RAG LangGraph workflow."""

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

    # ─── NODE: Vector Search ───────────────────────

    async def vector_search(self, state: RAGState) -> dict:
        cid = state["correlation_id"]
        query = state["query"]

        logger.info(f"[{cid[:8]}] 🔍 Node: vector_search")

        await emit_event(
            "agent.node.started",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "vector_search",
                "query": query[:100],
            },
        )

        start = time.time()
        results = await self.vector.search(query, top_k=5)
        elapsed = round((time.time() - start) * 1000, 2)

        best_score = results[0].score if results else 0

        await emit_event(
            "agent.node.completed",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "vector_search",
                "results_count": len(results),
                "best_score": best_score,
                "latency_ms": elapsed,
            },
        )

        step_detail = {
            "node": "vector_search",
            "results": len(results),
            "best_score": best_score,
            "latency_ms": elapsed,
        }

        return {
            "vector_results": results,
            "search_path": state["search_path"] + ["vector"],
            "current_step": "vector_search",
            "step_details": state["step_details"] + [step_detail],
        }

    # ─── NODE: Evaluate Vector Results ─────────────

    async def evaluate_vector(self, state: RAGState) -> dict:
        cid = state["correlation_id"]
        results = state.get("vector_results", [])

        good = [
            r for r in results
            if r.score >= VECTOR_SCORE_THRESHOLD
        ]

        decision = "sufficient" if good else "insufficient"

        await emit_event(
            "agent.node.decision",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "evaluate_vector",
                "decision": decision,
                "threshold": VECTOR_SCORE_THRESHOLD,
                "best_score": results[0].score if results else 0,
                "good_results": len(good),
                "total_results": len(results),
            },
        )

        logger.info(
            f"[{cid[:8]}] 📊 Vector evaluation: {decision} "
            f"({len(good)} good results)"
        )

        return {"current_step": "evaluate_vector"}

    # ─── NODE: Local Search ────────────────────────

    async def local_search(self, state: RAGState) -> dict:
        cid = state["correlation_id"]
        query = state["query"]

        logger.info(f"[{cid[:8]}] 📁 Node: local_search")

        await emit_event(
            "agent.node.started",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "local_search",
                "reason": "vector_below_threshold",
            },
        )

        start = time.time()
        results = await self.local.search(query, top_k=5)
        elapsed = round((time.time() - start) * 1000, 2)

        await emit_event(
            "agent.node.completed",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "local_search",
                "results_count": len(results),
                "latency_ms": elapsed,
            },
        )

        step_detail = {
            "node": "local_search",
            "results": len(results),
            "latency_ms": elapsed,
        }

        return {
            "local_results": results,
            "search_path": state["search_path"] + ["local"],
            "current_step": "local_search",
            "step_details": state["step_details"] + [step_detail],
        }

    # ─── NODE: Evaluate Local Results ──────────────

    async def evaluate_local(self, state: RAGState) -> dict:
        cid = state["correlation_id"]
        results = state.get("local_results", [])

        decision = "sufficient" if results else "empty"

        await emit_event(
            "agent.node.decision",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "evaluate_local",
                "decision": decision,
                "results_count": len(results),
            },
        )

        logger.info(
            f"[{cid[:8]}] 📊 Local evaluation: {decision}"
        )

        return {"current_step": "evaluate_local"}

    # ─── NODE: S3 Search ───────────────────────────

    async def s3_search(self, state: RAGState) -> dict:
        cid = state["correlation_id"]
        query = state["query"]

        logger.info(f"[{cid[:8]}] ☁️ Node: s3_search")

        await emit_event(
            "agent.node.started",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "s3_search",
                "reason": "local_empty",
            },
        )

        start = time.time()
        results = await self.s3.search(query, top_k=5)
        elapsed = round((time.time() - start) * 1000, 2)

        await emit_event(
            "agent.node.completed",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "s3_search",
                "results_count": len(results),
                "latency_ms": elapsed,
            },
        )

        step_detail = {
            "node": "s3_search",
            "results": len(results),
            "latency_ms": elapsed,
        }

        return {
            "s3_results": results,
            "search_path": state["search_path"] + ["s3"],
            "current_step": "s3_search",
            "step_details": state["step_details"] + [step_detail],
        }

    # ─── NODE: Select Best Sources ─────────────────

    async def select_sources(self, state: RAGState) -> dict:
        cid = state["correlation_id"]

        # Collect all valid sources
        all_sources = (
            [
                s for s in state.get("vector_results", [])
                if s.score >= VECTOR_SCORE_THRESHOLD
            ]
            + state.get("local_results", [])
            + state.get("s3_results", [])
        )

        # Sort by score
        all_sources.sort(key=lambda s: s.score, reverse=True)
        best = all_sources[:5]

        primary_layer = best[0].source_type if best else "none"

        await emit_event(
            "agent.node.completed",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "select_sources",
                "total_candidates": len(all_sources),
                "selected": len(best),
                "primary_layer": primary_layer,
                "sources": [
                    {
                        "type": s.source_type,
                        "path": s.source_path,
                        "score": s.score,
                    }
                    for s in best
                ],
            },
        )

        logger.info(
            f"[{cid[:8]}] ✅ Selected {len(best)} sources "
            f"(primary: {primary_layer})"
        )

        return {
            "best_sources": best,
            "current_step": "select_sources",
        }

    # ─── NODE: Generate Answer ─────────────────────

    async def generate(self, state: RAGState) -> dict:
        cid = state["correlation_id"]
        sources = state.get("best_sources", [])
        query = state["query"]

        logger.info(f"[{cid[:8]}] 🤖 Node: generate")

        await emit_event(
            "agent.node.started",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "generate",
                "has_context": bool(sources),
                "context_chunks": len(sources),
            },
        )

        # Build prompt with context
        if sources:
            context_parts = []
            for s in sources:
                context_parts.append(
                    f"[Source: {s.source_type} | "
                    f"{s.source_path} | "
                    f"Score: {s.score}]\n{s.content}"
                )
            context_text = "\n\n---\n\n".join(context_parts)

            messages = [
                ChatMessage(
                    role="system",
                    content=(
                        "You are a helpful assistant. "
                        "Answer using ONLY the context below. "
                        "If the answer is in the context, "
                        "provide it clearly with relevant details. "
                        "If not found in context, say so.\n\n"
                        f"CONTEXT:\n{context_text}"
                    ),
                ),
                ChatMessage(role="user", content=query),
            ]
        else:
            messages = [
                ChatMessage(role="user", content=query)
            ]

        request = ChatRequest(
            messages=messages,
            max_tokens=state.get("max_tokens", 512),
            temperature=state.get("temperature", 0.7),
            correlation_id=cid,
        )

        start = time.time()
        response = await self.llm_chat(request)
        elapsed = round((time.time() - start) * 1000, 2)

        await emit_event(
            "agent.node.completed",
            correlation_id=cid,
            layer="orchestration",
            payload={
                "node": "generate",
                "provider": response.provider,
                "model": response.model,
                "tokens_used": response.tokens_used,
                "latency_ms": elapsed,
            },
        )

        step_detail = {
            "node": "generate",
            "provider": response.provider,
            "model": response.model,
            "tokens_used": response.tokens_used,
            "latency_ms": elapsed,
        }

        return {
            "answer": response.message.content,
            "provider": response.provider,
            "model": response.model,
            "tokens_used": response.tokens_used,
            "current_step": "generate",
            "step_details": state["step_details"] + [step_detail],
        }

    # ─── CONDITIONAL EDGES ─────────────────────────

    def should_try_local(self, state: RAGState) -> str:
        """Decide: use vector results or fallback to local."""
        results = state.get("vector_results", [])
        good = [
            r for r in results
            if r.score >= VECTOR_SCORE_THRESHOLD
        ]
        if good:
            return "sufficient"
        return "try_local"

    def should_try_s3(self, state: RAGState) -> str:
        """Decide: use local results or fallback to S3."""
        results = state.get("local_results", [])
        if results:
            return "sufficient"
        return "try_s3"