from typing import Dict, Any, Tuple
from .attack_detection import score_prompt_risk


class PromptGuard:
    """High-level guard for prompts before sending to LLMs."""

    RISK_THRESHOLD = 0.6

    @classmethod
    def evaluate(cls, prompt: str) -> Tuple[bool, Dict[str, Any]]:
        """Return (allowed, metadata)."""
        score, reasons = score_prompt_risk(prompt)
        allowed = score < cls.RISK_THRESHOLD
        return allowed, {"score": score, "reasons": reasons}
