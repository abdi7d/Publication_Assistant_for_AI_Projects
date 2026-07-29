from typing import Tuple, Dict, Any
from .response_filter import detect_pii, profanity_score


class OutputGuard:
    SEVERITY_BLOCK = 0.8

    @classmethod
    def moderate(cls, text: str) -> Tuple[bool, Dict[str, Any]]:
        # compute simple safety metrics
        pii = detect_pii(text)
        prof = profanity_score(text)
        risk = max(pii.get("score", 0.0), prof)
        safe = risk < cls.SEVERITY_BLOCK
        metadata = {"pii": pii, "profanity_score": prof, "risk": risk}
        return safe, metadata
