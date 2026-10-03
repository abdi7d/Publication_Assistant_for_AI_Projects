from typing import Callable, Dict, Any
from .backoff import exponential_backoff


DEFAULT_POLICIES: Dict[str, Dict[str, Any]] = {
    "llm": {"max_attempts": 5, "base": 0.5, "factor": 2.0, "max_delay": 30.0},
    "tool": {"max_attempts": 4, "base": 0.2, "factor": 2.0, "max_delay": 10.0},
    "http": {"max_attempts": 3, "base": 0.5, "factor": 1.5, "max_delay": 5.0},
}


def get_policy(name: str) -> Dict[str, Any]:
    return DEFAULT_POLICIES.get(name, DEFAULT_POLICIES["http"])


def jittered_delay_calculator(policy_name: str) -> Callable[[int], float]:
    policy = get_policy(policy_name)

    def calc(attempt: int) -> float:
        return exponential_backoff(attempt, base=policy["base"], factor=policy["factor"], max_delay=policy["max_delay"])

    return calc
from dataclasses import dataclass
from typing import Optional


@dataclass
class RetryPolicy:
    max_retries: int = 5
    base_delay: float = 0.5
    factor: float = 2.0
    max_delay: float = 60.0
    retry_on_exceptions: tuple = (Exception,)
    retry_budget: Optional[int] = None  # maximum retries per time window (optional)


DEFAULT_RETRY_POLICY = RetryPolicy()
