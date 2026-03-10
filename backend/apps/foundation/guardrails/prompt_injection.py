"""Prompt injection detection — block attempts to manipulate the LLM."""
import re
import logging
from shared.schemas.chat import ChatRequest
from apps.foundation.guardrails.models import (
    GuardrailResult,
    GuardrailAction,
)

logger = logging.getLogger(__name__)

# Prompt injection patterns
INJECTION_PATTERNS = [
    # Direct override attempts
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules|directions)",
    r"disregard\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)",
    r"forget\s+(all\s+)?(previous|above|your)\s+(instructions|prompts|rules|training)",

    # Role hijacking
    r"you\s+are\s+now\s+(a|an)\s+",
    r"pretend\s+(you\s+are|to\s+be)\s+",
    r"act\s+as\s+(if\s+you\s+are|a|an)\s+",
    r"switch\s+to\s+.*\s+mode",
    r"enter\s+.*\s+mode",

    # System prompt extraction
    r"(show|reveal|display|print|output)\s+(your|the)\s+(system\s+)?(prompt|instructions|rules)",
    r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions|rules|guidelines)",
    r"repeat\s+(your|the)\s+(system\s+)?(prompt|instructions|rules)",

    # Encoding bypass attempts
    r"base64\s*(encode|decode)",
    r"\\x[0-9a-fA-F]{2}",

    # Delimiter injection
    r"```\s*system",
    r"\[SYSTEM\]",
    r"\[INST\]",
    r"<\|im_start\|>",
    r"<\|system\|>",
]

# Suspicious but not always malicious
SUSPICIOUS_PATTERNS = [
    r"do\s+not\s+follow\s+",
    r"override\s+",
    r"bypass\s+",
    r"jailbreak",
    r"DAN\s+mode",
]


def check_prompt_injection(
    request: ChatRequest,
) -> GuardrailResult:
    """Check for prompt injection attempts in user messages."""

    # Only check user messages (not system messages)
    user_content = " ".join(
        msg.content
        for msg in request.messages
        if msg.role == "user"
    ).lower()

    if not user_content:
        return GuardrailResult(
            passed=True,
            action=GuardrailAction.ALLOW,
            guard_name="prompt_injection",
            message="No user content to check",
        )

    # Check injection patterns
    for pattern in INJECTION_PATTERNS:
        match = re.search(
            pattern, user_content, re.IGNORECASE
        )
        if match:
            logger.warning(
                f"Prompt injection detected: "
                f"'{match.group()[:80]}'"
            )
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.BLOCK,
                guard_name="prompt_injection",
                message="Potential prompt injection detected",
                details={
                    "pattern_matched": pattern[:50],
                    "matched_text": match.group()[:80],
                },
            )

    # Check suspicious patterns (warn only)
    warnings = []
    for pattern in SUSPICIOUS_PATTERNS:
        match = re.search(
            pattern, user_content, re.IGNORECASE
        )
        if match:
            warnings.append(match.group()[:50])

    if warnings:
        logger.info(
            f"Suspicious patterns: {warnings}"
        )
        return GuardrailResult(
            passed=True,
            action=GuardrailAction.WARN,
            guard_name="prompt_injection",
            message=f"Suspicious patterns found: {len(warnings)}",
            details={"warnings": warnings},
        )

    return GuardrailResult(
        passed=True,
        action=GuardrailAction.ALLOW,
        guard_name="prompt_injection",
        message="No injection patterns detected",
    )