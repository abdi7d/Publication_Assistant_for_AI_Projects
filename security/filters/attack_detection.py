import re
from typing import Tuple, List

SUSPICIOUS_PATTERNS = [
    r"ignore (previous|prior) instructions",
    r"disregard (previous|prior) instructions",
    r"follow only the instructions",
    r"system prompt",
    r"sudo",
    r"execute.*code",
    r"open the (file|system) prompt",
]

COMPILED = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]


def score_prompt_risk(prompt: str) -> Tuple[float, List[str]]:
    """Return a risk score between 0-1 and list of matched reasons."""
    score = 0.0
    reasons: List[str] = []
    for rx in COMPILED:
        if rx.search(prompt):
            reasons.append(rx.pattern)
            score += 0.25

    # simple heuristics
    if len(prompt) > 10000:
        score = min(1.0, score + 0.4)
        reasons.append("excessive_length")

    # suspicious token patterns e.g., base64 blobs or long encoded sequences
    if re.search(r"[A-Za-z0-9+/]{100,}=*", prompt):
        reasons.append("encoded_blob")
        score += 0.25

    return min(score, 1.0), reasons
