from __future__ import annotations
import re
from typing import Tuple

MAX_PROMPT_CHARS = 20000
MAX_PROMPT_TOKENS = 5000
RE_INVALID_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_text(text: str) -> str:
    """Strip invalid control characters and normalize whitespace."""
    if text is None:
        return ""
    text = RE_INVALID_CHARS.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def validate_prompt_length(text: str) -> Tuple[bool, str]:
    if not text or not text.strip():
        return False, "empty_prompt"
    if len(text) > MAX_PROMPT_CHARS:
        return False, "prompt_too_large"
    return True, "ok"


def has_suspicious_chars(text: str) -> bool:
    return bool(re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text or ""))


def simple_token_estimate(text: str) -> int:
    return max(1, len(text or "") // 4)


def validate_prompt_tokens(text: str) -> Tuple[bool, str]:
    tokens = simple_token_estimate(text)
    if tokens > MAX_PROMPT_TOKENS:
        return False, "tokens_exceed_limit"
    return True, "ok"


__all__ = [
    "sanitize_text",
    "validate_prompt_length",
    "has_suspicious_chars",
    "validate_prompt_tokens",
]
