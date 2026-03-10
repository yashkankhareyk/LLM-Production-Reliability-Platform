"""Input validation — reject malformed or suspicious requests."""
import logging
from typing import List
from shared.schemas.chat import ChatRequest, ChatMessage
from apps.foundation.guardrails.models import (
    GuardrailResult,
    GuardrailAction,
)

logger = logging.getLogger(__name__)

# Limits
MAX_MESSAGES = 50
MAX_MESSAGE_LENGTH = 10000  # characters per message
MAX_TOTAL_LENGTH = 50000  # total characters across all messages
MAX_TOKENS_ALLOWED = 4096
VALID_ROLES = {"user", "assistant", "system"}


def validate_input(request: ChatRequest) -> GuardrailResult:
    """Validate request structure and content."""

    # Check message count
    if len(request.messages) == 0:
        return GuardrailResult(
            passed=False,
            action=GuardrailAction.BLOCK,
            guard_name="input_validator",
            message="No messages provided",
        )

    if len(request.messages) > MAX_MESSAGES:
        return GuardrailResult(
            passed=False,
            action=GuardrailAction.BLOCK,
            guard_name="input_validator",
            message=f"Too many messages: {len(request.messages)} "
            f"(max: {MAX_MESSAGES})",
        )

    # Check roles
    for msg in request.messages:
        if msg.role not in VALID_ROLES:
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.BLOCK,
                guard_name="input_validator",
                message=f"Invalid role: '{msg.role}'. "
                f"Use: {VALID_ROLES}",
            )

    # Check individual message length
    for i, msg in enumerate(request.messages):
        if len(msg.content) > MAX_MESSAGE_LENGTH:
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.BLOCK,
                guard_name="input_validator",
                message=f"Message {i+1} too long: "
                f"{len(msg.content)} chars "
                f"(max: {MAX_MESSAGE_LENGTH})",
            )

    # Check total length
    total_length = sum(
        len(msg.content) for msg in request.messages
    )
    if total_length > MAX_TOTAL_LENGTH:
        return GuardrailResult(
            passed=False,
            action=GuardrailAction.BLOCK,
            guard_name="input_validator",
            message=f"Total content too long: "
            f"{total_length} chars "
            f"(max: {MAX_TOTAL_LENGTH})",
        )

    # Check max tokens
    if request.max_tokens > MAX_TOKENS_ALLOWED:
        return GuardrailResult(
            passed=False,
            action=GuardrailAction.BLOCK,
            guard_name="input_validator",
            message=f"max_tokens too high: "
            f"{request.max_tokens} "
            f"(max: {MAX_TOKENS_ALLOWED})",
        )

    # Check temperature
    if not (0 <= request.temperature <= 2):
        return GuardrailResult(
            passed=False,
            action=GuardrailAction.BLOCK,
            guard_name="input_validator",
            message=f"Temperature must be 0-2, "
            f"got: {request.temperature}",
        )

    # Check last message is from user
    if request.messages[-1].role != "user":
        return GuardrailResult(
            passed=False,
            action=GuardrailAction.BLOCK,
            guard_name="input_validator",
            message="Last message must be from 'user'",
        )

    # Check for empty content
    for i, msg in enumerate(request.messages):
        if not msg.content or not msg.content.strip():
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.BLOCK,
                guard_name="input_validator",
                message=f"Message {i+1} has empty content",
            )

    return GuardrailResult(
        passed=True,
        action=GuardrailAction.ALLOW,
        guard_name="input_validator",
        message="Input validation passed",
    )