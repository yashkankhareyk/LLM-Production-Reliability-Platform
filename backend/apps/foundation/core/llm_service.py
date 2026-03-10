# """Core LLM service with event emission."""
# import time
# import logging
# from typing import List

# from shared.schemas.chat import (
#     ChatRequest,
#     ChatResponse,
#     ChatMessage,
# )
# from shared.events.publisher import emit_event
# from apps.foundation.providers.base import LLMProvider

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)


# class LLMService:
#     def __init__(self, providers: List[LLMProvider]):
#         self.providers = providers
#         logger.info(
#             f"LLMService initialized: "
#             f"{[p.name for p in providers]}"
#         )

#     async def chat(
#         self, request: ChatRequest
#     ) -> ChatResponse:
#         cid = request.correlation_id
#         errors = []

#         # ── Event: request started ──────────────────
#         await emit_event(
#             "llm.request.started",
#             correlation_id=cid,
#             layer="foundation",
#             payload={
#                 "provider_count": len(self.providers),
#                 "providers": [
#                     p.name for p in self.providers
#                 ],
#                 "message_count": len(request.messages),
#             },
#         )

#         if not self.providers:
#             await emit_event(
#                 "llm.request.failed",
#                 correlation_id=cid,
#                 layer="foundation",
#                 payload={
#                     "error": "No providers configured"
#                 },
#             )
#             return ChatResponse(
#                 message=ChatMessage(
#                     role="assistant",
#                     content="No LLM providers configured.",
#                 ),
#                 provider="none",
#                 model="no-providers",
#                 tokens_used=0,
#                 latency_ms=0,
#                 correlation_id=cid,
#             )

#         for provider in self.providers:
#             try:
#                 # ── Event: trying provider ──────────
#                 await emit_event(
#                     "llm.provider.trying",
#                     correlation_id=cid,
#                     layer="foundation",
#                     payload={"provider": provider.name},
#                 )

#                 start = time.time()
#                 response = await provider.chat(request)
#                 elapsed = (time.time() - start) * 1000

#                 # ── Event: provider success ─────────
#                 await emit_event(
#                     "llm.provider.success",
#                     correlation_id=cid,
#                     layer="foundation",
#                     payload={
#                         "provider": provider.name,
#                         "model": response.model,
#                         "tokens_used": response.tokens_used,
#                         "latency_ms": round(elapsed, 2),
#                     },
#                 )

#                 # ── Event: request completed ────────
#                 await emit_event(
#                     "llm.request.completed",
#                     correlation_id=cid,
#                     layer="foundation",
#                     payload={
#                         "provider": provider.name,
#                         "tokens_used": response.tokens_used,
#                         "latency_ms": round(elapsed, 2),
#                     },
#                 )

#                 return response

#             except Exception as e:
#                 elapsed = 0
#                 # ── Event: provider failed ──────────
#                 await emit_event(
#                     "llm.provider.failed",
#                     correlation_id=cid,
#                     layer="foundation",
#                     payload={
#                         "provider": provider.name,
#                         "error": str(e),
#                         "error_type": type(e).__name__,
#                     },
#                 )
#                 logger.error(
#                     f"❌ {provider.name}: {e}",
#                     exc_info=True,
#                 )
#                 errors.append(
#                     f"{provider.name}: {str(e)}"
#                 )
#                 continue

#         error_summary = " | ".join(errors)

#         # ── Event: all providers failed ─────────────
#         await emit_event(
#             "llm.request.all_failed",
#             correlation_id=cid,
#             layer="foundation",
#             payload={"errors": errors},
#         )

#         return ChatResponse(
#             message=ChatMessage(
#                 role="assistant",
#                 content=(
#                     f"All providers failed. "
#                     f"Errors: {error_summary}"
#                 ),
#             ),
#             provider="none",
#             model="fallback",
#             tokens_used=0,
#             latency_ms=0,
#             correlation_id=cid,
#         )
"""Core LLM service with guardrails + event emission."""
import time
import logging
from typing import List

from shared.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
)
from shared.events.publisher import emit_event
from apps.foundation.providers.base import LLMProvider
from apps.foundation.guardrails.pipeline import (
    GuardrailsPipeline,
)
from apps.foundation.guardrails.rate_limiter import (
    rate_limiter,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LLMService:
    def __init__(self, providers: List[LLMProvider]):
        self.providers = providers
        self.guardrails = GuardrailsPipeline(
            pii_mode="warn"
        )
        logger.info(
            f"LLMService initialized: "
            f"{[p.name for p in providers]}"
        )

    async def chat(
        self,
        request: ChatRequest,
        client_id: str = "default",
    ) -> ChatResponse:
        cid = request.correlation_id
        errors = []

        # ══════════════════════════════════════════
        #  PRE-LLM GUARDRAILS
        # ══════════════════════════════════════════

        report = await self.guardrails.check_input(
            request, client_id=client_id
        )

        if not report.allowed:
            logger.warning(
                f"🛡️ Request blocked by: "
                f"{report.blocked_by}"
            )

            await emit_event(
                "llm.request.blocked",
                correlation_id=cid,
                layer="foundation",
                payload={
                    "blocked_by": report.blocked_by,
                    "message": report.results[-1].message
                    if report.results
                    else "Unknown",
                },
            )

            return ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content=f"Request blocked: "
                    f"{report.results[-1].message}"
                    if report.results
                    else "Request blocked by guardrails",
                ),
                provider="guardrails",
                model="blocked",
                tokens_used=0,
                latency_ms=0,
                correlation_id=cid,
            )

        # Apply PII redaction if needed
        safe_request = self.guardrails.apply_redactions(
            request, report
        )

        # ══════════════════════════════════════════
        #  LLM CALL (with fallback)
        # ══════════════════════════════════════════

        await emit_event(
            "llm.request.started",
            correlation_id=cid,
            layer="foundation",
            payload={
                "provider_count": len(self.providers),
                "providers": [
                    p.name for p in self.providers
                ],
                "message_count": len(
                    safe_request.messages
                ),
                "guardrail_warnings": report.warnings,
            },
        )

        if not self.providers:
            return ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content="No LLM providers configured.",
                ),
                provider="none",
                model="no-providers",
                tokens_used=0,
                latency_ms=0,
                correlation_id=cid,
            )

        response = None

        for provider in self.providers:
            try:
                await emit_event(
                    "llm.provider.trying",
                    correlation_id=cid,
                    layer="foundation",
                    payload={"provider": provider.name},
                )

                start = time.time()
                response = await provider.chat(
                    safe_request
                )
                elapsed = (time.time() - start) * 1000

                await emit_event(
                    "llm.provider.success",
                    correlation_id=cid,
                    layer="foundation",
                    payload={
                        "provider": provider.name,
                        "model": response.model,
                        "tokens_used": response.tokens_used,
                        "latency_ms": round(elapsed, 2),
                    },
                )

                # Record token usage for rate limiting
                rate_limiter.record_tokens(
                    client_id, response.tokens_used
                )

                break  # Success, stop trying

            except Exception as e:
                await emit_event(
                    "llm.provider.failed",
                    correlation_id=cid,
                    layer="foundation",
                    payload={
                        "provider": provider.name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                logger.error(
                    f"❌ {provider.name}: {e}",
                    exc_info=True,
                )
                errors.append(
                    f"{provider.name}: {str(e)}"
                )
                continue

        # All providers failed
        if response is None:
            error_summary = " | ".join(errors)

            await emit_event(
                "llm.request.all_failed",
                correlation_id=cid,
                layer="foundation",
                payload={"errors": errors},
            )

            return ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content=f"All providers failed. "
                    f"Errors: {error_summary}",
                ),
                provider="none",
                model="fallback",
                tokens_used=0,
                latency_ms=0,
                correlation_id=cid,
            )

        # ══════════════════════════════════════════
        #  POST-LLM GUARDRAILS
        # ══════════════════════════════════════════

        safe_response = (
            await self.guardrails.check_output(response)
        )

        await emit_event(
            "llm.request.completed",
            correlation_id=cid,
            layer="foundation",
            payload={
                "provider": safe_response.provider,
                "tokens_used": safe_response.tokens_used,
                "latency_ms": safe_response.latency_ms,
            },
        )

        return safe_response