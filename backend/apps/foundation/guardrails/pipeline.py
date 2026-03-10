"""
Guardrails pipeline — runs all checks in sequence.
This is the main entry point for all guardrail checks.
"""
import logging
from typing import Optional
from shared.schemas.chat import ChatRequest, ChatResponse, ChatMessage
from shared.events.publisher import emit_event
from apps.foundation.guardrails.models import (
    GuardrailReport,
    GuardrailResult,
    GuardrailAction,
)
from apps.foundation.guardrails.input_validator import (
    validate_input,
)
from apps.foundation.guardrails.content_filter import (
    check_content,
)
from apps.foundation.guardrails.pii_detector import (
    check_pii,
    redact_pii,
)
from apps.foundation.guardrails.prompt_injection import (
    check_prompt_injection,
)
from apps.foundation.guardrails.rate_limiter import (
    rate_limiter,
)
from apps.foundation.guardrails.output_validator import (
    validate_output,
)

logger = logging.getLogger(__name__)


class GuardrailsPipeline:
    """
    Runs all guardrail checks before and after LLM calls.

    Usage:
        pipeline = GuardrailsPipeline()

        # Before LLM call
        report = await pipeline.check_input(request)
        if not report.allowed:
            return blocked_response(report)

        # If PII redaction needed, get modified request
        safe_request = pipeline.apply_redactions(request, report)

        # Call LLM...
        response = await llm.chat(safe_request)

        # After LLM call
        safe_response = await pipeline.check_output(response)
    """

    def __init__(self, pii_mode: str = "warn"):
        """
        Args:
            pii_mode: "warn", "block", or "redact"
        """
        self.pii_mode = pii_mode

    async def check_input(
        self,
        request: ChatRequest,
        client_id: str = "default",
    ) -> GuardrailReport:
        """Run all input guardrail checks."""
        results = []
        warnings = []
        blocked_by = None

        cid = request.correlation_id

        # ── 1. Rate Limiting ───────────────────────
        rate_result = rate_limiter.check_rate_limit(
            client_id
        )
        results.append(rate_result)
        if not rate_result.passed:
            blocked_by = "rate_limiter"
            await self._emit_guardrail_event(
                cid, rate_result
            )
            return GuardrailReport(
                allowed=False,
                results=results,
                blocked_by=blocked_by,
            )

        # ── 2. Input Validation ────────────────────
        input_result = validate_input(request)
        results.append(input_result)
        if not input_result.passed:
            blocked_by = "input_validator"
            await self._emit_guardrail_event(
                cid, input_result
            )
            return GuardrailReport(
                allowed=False,
                results=results,
                blocked_by=blocked_by,
            )

        # ── 3. Prompt Injection ────────────────────
        injection_result = check_prompt_injection(request)
        results.append(injection_result)
        if not injection_result.passed:
            blocked_by = "prompt_injection"
            await self._emit_guardrail_event(
                cid, injection_result
            )
            return GuardrailReport(
                allowed=False,
                results=results,
                blocked_by=blocked_by,
            )
        if injection_result.action == GuardrailAction.WARN:
            warnings.append(injection_result.message)

        # ── 4. Content Filter ──────────────────────
        content_result = check_content(request)
        results.append(content_result)
        if not content_result.passed:
            blocked_by = "content_filter"
            await self._emit_guardrail_event(
                cid, content_result
            )
            return GuardrailReport(
                allowed=False,
                results=results,
                blocked_by=blocked_by,
            )
        if content_result.action == GuardrailAction.WARN:
            warnings.append(content_result.message)

        # ── 5. PII Detection ──────────────────────
        pii_result = check_pii(
            request, mode=self.pii_mode
        )
        results.append(pii_result)
        if not pii_result.passed:
            blocked_by = "pii_detector"
            await self._emit_guardrail_event(
                cid, pii_result
            )
            return GuardrailReport(
                allowed=False,
                results=results,
                blocked_by=blocked_by,
            )
        if pii_result.action == GuardrailAction.WARN:
            warnings.append(pii_result.message)

        # ── All checks passed ──────────────────────
        await emit_event(
            "guardrails.input.passed",
            correlation_id=cid,
            layer="foundation",
            payload={
                "checks_run": len(results),
                "warnings": len(warnings),
            },
        )

        return GuardrailReport(
            allowed=True,
            results=results,
            warnings=warnings,
        )

    def apply_redactions(
        self,
        request: ChatRequest,
        report: GuardrailReport,
    ) -> ChatRequest:
        """Apply PII redaction if needed."""
        needs_redaction = any(
            r.action == GuardrailAction.REDACT
            for r in report.results
        )

        if not needs_redaction:
            return request

        # Redact PII from all messages
        redacted_messages = []
        for msg in request.messages:
            redacted_content = redact_pii(msg.content)
            redacted_messages.append(
                ChatMessage(
                    role=msg.role,
                    content=redacted_content,
                )
            )

        return ChatRequest(
            messages=redacted_messages,
            use_rag=request.use_rag,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            correlation_id=request.correlation_id,
        )

    async def check_output(
        self, response: ChatResponse
    ) -> ChatResponse:
        """Run output guardrails on LLM response."""
        result = validate_output(response)

        if result.action == GuardrailAction.REDACT:
            # Redact sensitive data from output
            redacted_content = redact_pii(
                response.message.content
            )
            response.message.content = redacted_content

            await emit_event(
                "guardrails.output.redacted",
                correlation_id=response.correlation_id,
                layer="foundation",
                payload=result.details,
            )

        elif result.action == GuardrailAction.WARN:
            await emit_event(
                "guardrails.output.warning",
                correlation_id=response.correlation_id,
                layer="foundation",
                payload=result.details,
            )

        return response

    async def _emit_guardrail_event(
        self,
        correlation_id: str,
        result: GuardrailResult,
    ):
        """Emit event when a guardrail blocks or warns."""
        await emit_event(
            f"guardrails.{result.guard_name}.{result.action.value}",
            correlation_id=correlation_id,
            layer="foundation",
            payload={
                "guard": result.guard_name,
                "action": result.action.value,
                "message": result.message,
                "details": result.details,
            },
        )