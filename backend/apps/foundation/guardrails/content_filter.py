"""Content moderation — block harmful, toxic, or inappropriate content."""
import re
import logging
from shared.schemas.chat import ChatRequest
from apps.foundation.guardrails.models import (
    GuardrailResult,
    GuardrailAction,
)

logger = logging.getLogger(__name__)

# Blocked content categories
BLOCKED_PATTERNS = [
    # Violence
    r"\b(how to make|instructions for|steps to create)\b.*(bomb|explosive|weapon|poison)",
    r"\b(kill|murder|assassinate|harm)\b.*\b(person|people|someone|anyone)\b",

    # Illegal activities
    r"\b(how to hack|bypass security|steal credentials|crack password)\b",
    r"\b(create malware|write virus|ransomware code)\b",

    # Self-harm
    r"\b(how to|ways to)\b.*(hurt myself|end my life|commit suicide)\b",
]

# Warn patterns (not blocked but flagged)
WARN_PATTERNS = [
    r"\b(password|secret key|api key|token)\b.*\b(is|are|was)\b",
    r"\b(ignore previous|ignore above|disregard)\b.*\b(instructions|prompt|rules)\b",
]

# Blocked keywords (exact match, case-insensitive)
BLOCKED_KEYWORDS = set()
# Add keywords if needed:
# BLOCKED_KEYWORDS = {"keyword1", "keyword2"}


def check_content(request: ChatRequest) -> GuardrailResult:
    """Check message content for harmful patterns."""

    all_content = " ".join(
        msg.content for msg in request.messages
    ).lower()

    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        match = re.search(pattern, all_content, re.IGNORECASE)
        if match:
            logger.warning(
                f"Content blocked: matched pattern '{pattern}' "
                f"in text: '...{match.group()}...'"
            )
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.BLOCK,
                guard_name="content_filter",
                message="Request contains prohibited content",
                details={
                    "reason": "blocked_pattern",
                    "matched": match.group()[:50],
                },
            )

    # Check blocked keywords
    words = set(all_content.split())
    blocked_found = words.intersection(BLOCKED_KEYWORDS)
    if blocked_found:
        logger.warning(
            f"Content blocked: keywords {blocked_found}"
        )
        return GuardrailResult(
            passed=False,
            action=GuardrailAction.BLOCK,
            guard_name="content_filter",
            message="Request contains blocked keywords",
            details={"keywords": list(blocked_found)},
        )

    # Check warn patterns
    warnings = []
    for pattern in WARN_PATTERNS:
        match = re.search(pattern, all_content, re.IGNORECASE)
        if match:
            warnings.append(match.group()[:50])

    if warnings:
        logger.info(f"Content warnings: {warnings}")
        return GuardrailResult(
            passed=True,
            action=GuardrailAction.WARN,
            guard_name="content_filter",
            message=f"Content warnings: {len(warnings)} patterns flagged",
            details={"warnings": warnings},
        )

    return GuardrailResult(
        passed=True,
        action=GuardrailAction.ALLOW,
        guard_name="content_filter",
        message="Content check passed",
    )