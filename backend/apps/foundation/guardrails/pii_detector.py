"""PII detection and redaction — protect sensitive data."""
import re
import logging
from shared.schemas.chat import ChatRequest
from apps.foundation.guardrails.models import (
    GuardrailResult,
    GuardrailAction,
)

logger = logging.getLogger(__name__)

# PII patterns
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "ssn": r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
}

# Redaction replacements
REDACTION_MAP = {
    "email": "[EMAIL_REDACTED]",
    "phone": "[PHONE_REDACTED]",
    "ssn": "[SSN_REDACTED]",
    "credit_card": "[CC_REDACTED]",
    "ip_address": "[IP_REDACTED]",
}


def detect_pii(text: str) -> dict:
    """Detect PII in text and return findings."""
    findings = {}

    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            findings[pii_type] = len(matches)

    return findings


def redact_pii(text: str) -> str:
    """Replace PII with redaction markers."""
    redacted = text

    for pii_type, pattern in PII_PATTERNS.items():
        replacement = REDACTION_MAP.get(
            pii_type, "[REDACTED]"
        )
        redacted = re.sub(pattern, replacement, redacted)

    return redacted


def check_pii(
    request: ChatRequest,
    mode: str = "warn",
) -> GuardrailResult:
    """
    Check for PII in request messages.

    Modes:
      "warn"   — allow but flag PII found
      "block"  — reject if PII found
      "redact" — replace PII with markers
    """
    all_content = " ".join(
        msg.content for msg in request.messages
    )

    findings = detect_pii(all_content)

    if not findings:
        return GuardrailResult(
            passed=True,
            action=GuardrailAction.ALLOW,
            guard_name="pii_detector",
            message="No PII detected",
        )

    total_pii = sum(findings.values())
    logger.warning(
        f"PII detected: {findings} "
        f"(total: {total_pii} instances)"
    )

    if mode == "block":
        return GuardrailResult(
            passed=False,
            action=GuardrailAction.BLOCK,
            guard_name="pii_detector",
            message=f"PII detected: {total_pii} instances. "
            f"Types: {list(findings.keys())}",
            details={"findings": findings},
        )

    elif mode == "redact":
        return GuardrailResult(
            passed=True,
            action=GuardrailAction.REDACT,
            guard_name="pii_detector",
            message=f"PII redacted: {total_pii} instances",
            details={
                "findings": findings,
                "redacted": True,
            },
        )

    else:  # warn
        return GuardrailResult(
            passed=True,
            action=GuardrailAction.WARN,
            guard_name="pii_detector",
            message=f"PII warning: {total_pii} instances found",
            details={"findings": findings},
        )