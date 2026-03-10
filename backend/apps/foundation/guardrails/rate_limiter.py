"""Rate limiting — prevent abuse and control costs."""
import time
import logging
from collections import defaultdict
from apps.foundation.guardrails.models import (
    GuardrailResult,
    GuardrailAction,
)

logger = logging.getLogger(__name__)

# Rate limit configuration
REQUESTS_PER_MINUTE = 30
REQUESTS_PER_HOUR = 200
TOKEN_BUDGET_PER_HOUR = 100000  # max tokens per hour


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        # Track requests per IP/user
        self.request_log = defaultdict(list)
        # Track token usage
        self.token_log = defaultdict(list)

    def _clean_old_entries(
        self, entries: list, window_seconds: int
    ) -> list:
        """Remove entries older than the window."""
        now = time.time()
        return [
            entry
            for entry in entries
            if now - entry["time"] < window_seconds
        ]

    def check_rate_limit(
        self, client_id: str = "default"
    ) -> GuardrailResult:
        """Check if client has exceeded rate limits."""
        now = time.time()

        # Clean old entries
        self.request_log[client_id] = (
            self._clean_old_entries(
                self.request_log[client_id], 3600
            )
        )

        entries = self.request_log[client_id]

        # Check per-minute limit
        last_minute = [
            e for e in entries if now - e["time"] < 60
        ]
        if len(last_minute) >= REQUESTS_PER_MINUTE:
            logger.warning(
                f"Rate limit: {client_id} exceeded "
                f"{REQUESTS_PER_MINUTE}/min"
            )
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.BLOCK,
                guard_name="rate_limiter",
                message=f"Rate limit exceeded: "
                f"{len(last_minute)}/{REQUESTS_PER_MINUTE} "
                f"requests per minute",
                details={
                    "limit": REQUESTS_PER_MINUTE,
                    "window": "1 minute",
                    "current": len(last_minute),
                },
            )

        # Check per-hour limit
        if len(entries) >= REQUESTS_PER_HOUR:
            logger.warning(
                f"Rate limit: {client_id} exceeded "
                f"{REQUESTS_PER_HOUR}/hour"
            )
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.BLOCK,
                guard_name="rate_limiter",
                message=f"Rate limit exceeded: "
                f"{len(entries)}/{REQUESTS_PER_HOUR} "
                f"requests per hour",
                details={
                    "limit": REQUESTS_PER_HOUR,
                    "window": "1 hour",
                    "current": len(entries),
                },
            )

        # Check token budget
        self.token_log[client_id] = (
            self._clean_old_entries(
                self.token_log[client_id], 3600
            )
        )
        total_tokens = sum(
            e.get("tokens", 0)
            for e in self.token_log[client_id]
        )

        if total_tokens >= TOKEN_BUDGET_PER_HOUR:
            logger.warning(
                f"Token budget: {client_id} exceeded "
                f"{TOKEN_BUDGET_PER_HOUR}/hour"
            )
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.BLOCK,
                guard_name="rate_limiter",
                message=f"Token budget exceeded: "
                f"{total_tokens}/{TOKEN_BUDGET_PER_HOUR} "
                f"tokens per hour",
                details={
                    "limit": TOKEN_BUDGET_PER_HOUR,
                    "current": total_tokens,
                },
            )

        # Record this request
        self.request_log[client_id].append(
            {"time": now}
        )

        return GuardrailResult(
            passed=True,
            action=GuardrailAction.ALLOW,
            guard_name="rate_limiter",
            message="Rate limit OK",
            details={
                "requests_this_minute": len(last_minute) + 1,
                "requests_this_hour": len(entries) + 1,
                "tokens_this_hour": total_tokens,
            },
        )

    def record_tokens(
        self, client_id: str, tokens: int
    ):
        """Record token usage after response."""
        self.token_log[client_id].append(
            {"time": time.time(), "tokens": tokens}
        )


# Global singleton
rate_limiter = RateLimiter()