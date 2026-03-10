"""Output validation — check LLM response for safety."""
import re
import logging
from shared.schemas.chat import ChatResponse
from apps.foundation.guardrails.models import (
    GuardrailResult,
    GuardrailAction,
)
from apps.foundation.guardrails.pii_detector import (
    detect_pii,
    redact_pii,
)

logger = logging.getLogger(__name__)

# Patterns that should never appear in output
BLOCKED_OUTPUT_PATTERNS = [
    r"(api[_\s]?key|secret[_\s]?key|password)\s*[:=]\s*\S+",
    r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
    r"sk-[A-Za-z0-9]{20,}",
    r"xai-[A-Za-z0-9]{20,}",
]


def validate_output(
    response: ChatResponse,
) -> GuardrailResult:
    """Validate LLM response for safety issues."""

    content = response.message.content

    if not content:
        return GuardrailResult(
            passed=True,
            action=GuardrailAction.ALLOW,
            guard_name="output_validator",
            message="Empty response",
        )

    # Check for leaked secrets/keys
    for pattern in BLOCKED_OUTPUT_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            logger.warning(
                f"Output contains sensitive data: "
                f"{match.group()[:30]}..."
            )
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.REDACT,
                guard_name="output_validator",
                message="Response contains sensitive data",
                details={
                    "type": "leaked_secret",
                    "matched": match.group()[:20] + "...",
                },
            )

    # Check for PII in output
    pii_findings = detect_pii(content)
    if pii_findings:
        logger.info(
            f"PII in output: {pii_findings}"
        )
        return GuardrailResult(
            passed=True,
            action=GuardrailAction.WARN,
            guard_name="output_validator",
            message=f"Output contains PII: {list(pii_findings.keys())}",
            details={"pii": pii_findings},
        )

    return GuardrailResult(
        passed=True,
        action=GuardrailAction.ALLOW,
        guard_name="output_validator",
        message="Output validation passed",
    )