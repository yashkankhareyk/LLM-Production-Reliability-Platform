"""
LangGraph workflow builder.

Graph:
    START → vector_search → evaluate_vector
                              │
                ┌─────────────┼──────────────┐
                ▼ sufficient   ▼ try_local
          select_sources    local_search
                              │
                              ▼
                         evaluate_local
                              │
                ┌─────────────┼──────────────┐
                ▼ sufficient   ▼ try_s3
          select_sources    s3_search
                              │
                              ▼
                        select_sources
                              │
                              ▼
                           generate
                              │
                              ▼
                             END
"""
import time
import logging
from langgraph.graph import StateGraph, END

from shared.events.publisher import emit_event
from apps.orchestration.core.state import RAGState
from apps.orchestration.core.nodes import RAGNodes

logger = logging.getLogger(__name__)


def build_rag_graph(nodes: RAGNodes):
    """Build and compile the LangGraph RAG workflow."""

    graph = StateGraph(RAGState)

    # Add nodes
    graph.add_node("vector_search", nodes.vector_search)
    graph.add_node("evaluate_vector", nodes.evaluate_vector)
    graph.add_node("local_search", nodes.local_search)
    graph.add_node("evaluate_local", nodes.evaluate_local)
    graph.add_node("s3_search", nodes.s3_search)
    graph.add_node("select_sources", nodes.select_sources)
    graph.add_node("generate", nodes.generate)

    # Define flow
    graph.set_entry_point("vector_search")

    graph.add_edge("vector_search", "evaluate_vector")

    # After vector evaluation: either sufficient or try local
    graph.add_conditional_edges(
        "evaluate_vector",
        nodes.should_try_local,
        {
            "sufficient": "select_sources",
            "try_local": "local_search",
        },
    )

    graph.add_edge("local_search", "evaluate_local")

    # After local evaluation: either sufficient or try S3
    graph.add_conditional_edges(
        "evaluate_local",
        nodes.should_try_s3,
        {
            "sufficient": "select_sources",
            "try_s3": "s3_search",
        },
    )

    graph.add_edge("s3_search", "select_sources")
    graph.add_edge("select_sources", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


class RAGAgent:
    """High-level agent that runs the LangGraph workflow."""

    def __init__(
        self,
        vector_retriever,
        local_retriever,
        s3_retriever,
        llm_chat_fn,
    ):
        self.nodes = RAGNodes(
            vector_retriever=vector_retriever,
            local_retriever=local_retriever,
            s3_retriever=s3_retriever,
            llm_chat_fn=llm_chat_fn,
        )
        self.graph = build_rag_graph(self.nodes)
        logger.info("✅ LangGraph RAG agent initialized")

    async def run(
        self,
        query: str,
        correlation_id: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> dict:
        """Run the full RAG agent workflow."""

        await emit_event(
            "agent.workflow.started",
            correlation_id=correlation_id,
            layer="orchestration",
            payload={"query": query[:100]},
        )

        total_start = time.time()

        # Initial state
        initial_state: RAGState = {
            "query": query,
            "correlation_id": correlation_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "vector_results": [],
            "local_results": [],
            "s3_results": [],
            "best_sources": [],
            "search_path": [],
            "current_step": "start",
            "step_details": [],
            "answer": "",
            "provider": "",
            "model": "",
            "tokens_used": 0,
            "total_latency_ms": 0,
            "error": None,
        }

        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)

            total_ms = round(
                (time.time() - total_start) * 1000, 2
            )

            await emit_event(
                "agent.workflow.completed",
                correlation_id=correlation_id,
                layer="orchestration",
                payload={
                    "search_path": final_state["search_path"],
                    "sources_found": len(
                        final_state.get("best_sources", [])
                    ),
                    "provider": final_state.get("provider", ""),
                    "tokens_used": final_state.get("tokens_used", 0),
                    "total_latency_ms": total_ms,
                    "steps_executed": len(
                        final_state.get("step_details", [])
                    ),
                },
            )

            return {
                "answer": final_state.get("answer", ""),
                "provider": final_state.get("provider", ""),
                "model": final_state.get("model", ""),
                "tokens_used": final_state.get("tokens_used", 0),
                "sources": [
                    {
                        "content": s.content,
                        "source_type": s.source_type,
                        "source_path": s.source_path,
                        "score": s.score,
                    }
                    for s in final_state.get("best_sources", [])
                ],
                "search_path": final_state["search_path"],
                "step_details": final_state["step_details"],
                "total_latency_ms": total_ms,
                "correlation_id": correlation_id,
            }

        except Exception as e:
            total_ms = round(
                (time.time() - total_start) * 1000, 2
            )

            await emit_event(
                "agent.workflow.failed",
                correlation_id=correlation_id,
                layer="orchestration",
                payload={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "total_latency_ms": total_ms,
                },
            )

            logger.error(
                f"Agent workflow failed: {e}", exc_info=True
            )

            return {
                "answer": f"Agent error: {str(e)}",
                "provider": "none",
                "model": "error",
                "tokens_used": 0,
                "sources": [],
                "search_path": [],
                "step_details": [],
                "total_latency_ms": total_ms,
                "correlation_id": correlation_id,
                "error": str(e),
            }

    def get_graph_info(self) -> dict:
        """Return graph structure info."""
        return {
            "nodes": [
                {
                    "name": "vector_search",
                    "description": "Search FAISS vector store",
                },
                {
                    "name": "evaluate_vector",
                    "description": "Check if vector results are good enough (score >= 0.4)",
                },
                {
                    "name": "local_search",
                    "description": "Keyword search in local files (fallback 1)",
                },
                {
                    "name": "evaluate_local",
                    "description": "Check if local results exist",
                },
                {
                    "name": "s3_search",
                    "description": "Search S3/mock storage (fallback 2)",
                },
                {
                    "name": "select_sources",
                    "description": "Pick best sources from all results",
                },
                {
                    "name": "generate",
                    "description": "Call LLM with context to generate answer",
                },
            ],
            "edges": [
                {"from": "START", "to": "vector_search"},
                {"from": "vector_search", "to": "evaluate_vector"},
                {
                    "from": "evaluate_vector",
                    "to": "select_sources",
                    "condition": "score >= 0.4",
                },
                {
                    "from": "evaluate_vector",
                    "to": "local_search",
                    "condition": "score < 0.4",
                },
                {"from": "local_search", "to": "evaluate_local"},
                {
                    "from": "evaluate_local",
                    "to": "select_sources",
                    "condition": "results found",
                },
                {
                    "from": "evaluate_local",
                    "to": "s3_search",
                    "condition": "no results",
                },
                {"from": "s3_search", "to": "select_sources"},
                {"from": "select_sources", "to": "generate"},
                {"from": "generate", "to": "END"},
            ],
        }