"""Guardrail models and types."""
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class GuardrailAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    REDACT = "redact"


class GuardrailResult(BaseModel):
    passed: bool
    action: GuardrailAction
    guard_name: str
    message: str = ""
    details: dict = {}


class GuardrailReport(BaseModel):
    """Combined result of all guardrail checks."""
    allowed: bool
    results: List[GuardrailResult]
    blocked_by: Optional[str] = None
    warnings: List[str] = []
    redacted_content: Optional[str] = None