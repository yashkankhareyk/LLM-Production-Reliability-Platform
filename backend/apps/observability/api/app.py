# FastAPI app factory
"""Layer 4: Observability — query events, runs, metrics."""
from fastapi import FastAPI, Query
from typing import Optional, List
from shared.events.event_bus import InMemoryEventBus


def create_app() -> FastAPI:
    app = FastAPI(
        title="Layer 4: Observability",
        version="0.3.0",
        description="Query events, view runs, check metrics",
    )

    bus = InMemoryEventBus()

    # ─── HEALTH ─────────────────────────────────────

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "layer": "observability",
            "total_events": bus.total_events,
        }

    # ─── ALL EVENTS ─────────────────────────────────

    @app.get("/internal/obs/events")
    async def get_events(
        correlation_id: Optional[str] = Query(
            None, description="Filter by correlation ID"
        ),
        event_type: Optional[str] = Query(
            None, description="Filter by event type"
        ),
        layer: Optional[str] = Query(
            None,
            description="Filter by layer (foundation, intelligence)",
        ),
        limit: int = Query(50, le=500),
    ):
        events = bus.get_events(
            correlation_id=correlation_id,
            event_type=event_type,
            layer=layer,
            limit=limit,
        )

        return {
            "total": len(events),
            "events": [
                {
                    "event_id": e.event_id,
                    "correlation_id": e.correlation_id,
                    "event_type": e.event_type,
                    "layer": e.layer,
                    "timestamp": e.timestamp.isoformat(),
                    "payload": e.payload,
                }
                for e in events
            ],
        }

    # ─── RUNS (grouped by correlation_id) ───────────

    @app.get("/internal/obs/runs")
    async def get_runs(
        limit: int = Query(20, le=100),
    ):
        runs = bus.get_runs(limit=limit)
        return {"total": len(runs), "runs": runs}

    # ─── SINGLE RUN DETAIL ──────────────────────────

    @app.get("/internal/obs/runs/{correlation_id}")
    async def get_run(correlation_id: str):
        events = bus.get_events(
            correlation_id=correlation_id, limit=100
        )

        if not events:
            return {
                "error": "No events found for this correlation_id"
            }

        # Build timeline
        timeline = []
        providers_used = set()
        search_layers = set()
        total_tokens = 0
        status = "in_progress"

        for e in events:
            timeline.append(
                {
                    "time": e.timestamp.isoformat(),
                    "event": e.event_type,
                    "layer": e.layer,
                    "details": e.payload,
                }
            )

            provider = e.payload.get("provider")
            if provider:
                providers_used.add(provider)

            search_layer = e.payload.get("search_layer")
            if search_layer:
                search_layers.add(search_layer)

            tokens = e.payload.get("tokens_used", 0)
            total_tokens += tokens

            if "completed" in e.event_type:
                status = "completed"
            if "failed" in e.event_type:
                status = "failed"

        # Calculate total latency
        if len(events) >= 2:
            first = events[0].timestamp
            last = events[-1].timestamp
            total_latency = (
                last - first
            ).total_seconds() * 1000
        else:
            total_latency = 0

        return {
            "correlation_id": correlation_id,
            "status": status,
            "total_events": len(events),
            "total_tokens": total_tokens,
            "total_latency_ms": round(total_latency, 2),
            "providers_used": list(providers_used),
            "search_layers_used": list(search_layers),
            "timeline": timeline,
        }

    # ─── METRICS ────────────────────────────────────

    @app.get("/internal/obs/metrics")
    async def get_metrics():
        all_events = bus.get_events(limit=10000)

        total_requests = len(
            [
                e
                for e in all_events
                if e.event_type == "llm.request.started"
            ]
        )
        total_completed = len(
            [
                e
                for e in all_events
                if e.event_type == "llm.request.completed"
            ]
        )
        total_failed = len(
            [
                e
                for e in all_events
                if "failed" in e.event_type
            ]
        )
        total_rag = len(
            [
                e
                for e in all_events
                if e.event_type == "rag.request.started"
            ]
        )

        # Provider usage
        provider_counts = {}
        for e in all_events:
            if e.event_type == "llm.provider.success":
                p = e.payload.get("provider", "unknown")
                provider_counts[p] = (
                    provider_counts.get(p, 0) + 1
                )

        # Search layer usage
        search_counts = {}
        for e in all_events:
            if e.event_type == "rag.search.completed":
                sl = e.payload.get(
                    "final_search_layer", "unknown"
                )
                search_counts[sl] = (
                    search_counts.get(sl, 0) + 1
                )

        # Average latency
        latencies = [
            e.payload.get("latency_ms", 0)
            for e in all_events
            if e.event_type == "llm.request.completed"
            and e.payload.get("latency_ms")
        ]
        avg_latency = (
            round(sum(latencies) / len(latencies), 2)
            if latencies
            else 0
        )

        # Total tokens
        total_tokens = sum(
            e.payload.get("tokens_used", 0)
            for e in all_events
            if e.payload.get("tokens_used")
        )

        return {
            "total_events": len(all_events),
            "llm_requests": total_requests,
            "llm_completed": total_completed,
            "llm_failures": total_failed,
            "rag_requests": total_rag,
            "provider_usage": provider_counts,
            "search_layer_usage": search_counts,
            "avg_latency_ms": avg_latency,
            "total_tokens_used": total_tokens,
        }

    # ─── EVENT TYPES ────────────────────────────────

    @app.get("/internal/obs/event-types")
    async def get_event_types():
        all_events = bus.get_events(limit=10000)
        types = {}
        for e in all_events:
            types[e.event_type] = (
                types.get(e.event_type, 0) + 1
            )

        return {
            "event_types": [
                {"type": k, "count": v}
                for k, v in sorted(
                    types.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ]
        }

    # ─── CLEAR EVENTS ──────────────────────────────

    @app.delete("/internal/obs/events")
    async def clear_events():
        count = bus.total_events
        bus.clear()
        return {
            "status": "cleared",
            "events_deleted": count,
        }

    return app