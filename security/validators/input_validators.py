import re
from typing import Tuple

try:
    from pydantic import BaseModel, ValidationError, field_validator
except Exception:  # pragma: no cover
    from pydantic.v1 import BaseModel, ValidationError, validator as field_validator  # type: ignore

from ..configs.config_loader import settings


RE_INVALID_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


class PromptModel(BaseModel):
    prompt: str

    if hasattr(BaseModel, "model_validator"):
        @field_validator("prompt")
        @classmethod
        def not_empty(cls, v: str) -> str:
            if not v or not v.strip():
                raise ValueError("Prompt cannot be empty")
            if RE_INVALID_CHARS.search(v):
                raise ValueError("Prompt contains invalid control characters")
            if len(v.encode("utf-8")) > settings.MAX_PROMPT_LENGTH:
                raise ValueError("Prompt exceeds maximum allowed length")
            return v
    else:
        @field_validator("prompt")
        @classmethod
        def not_empty(cls, v: str) -> str:
            if not v or not v.strip():
                raise ValueError("Prompt cannot be empty")
            if RE_INVALID_CHARS.search(v):
                raise ValueError("Prompt contains invalid control characters")
            if len(v.encode("utf-8")) > settings.MAX_PROMPT_LENGTH:
                raise ValueError("Prompt exceeds maximum allowed length")
            return v


def validate_prompt(prompt: str) -> Tuple[bool, str]:
    try:
        PromptModel(prompt=prompt)
        return True, ""
    except ValidationError as e:
        return False, str(e)
