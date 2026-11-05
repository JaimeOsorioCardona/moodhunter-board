"""In-memory Circuit Breaker implementation for external LLM resiliency."""

import time
from enum import StrEnum
from typing import Any


class BreakerState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.consecutive_failures: int = 0
        self.last_failure_time: float = 0.0
        self.state: BreakerState = BreakerState.CLOSED

    def can_execute(self) -> bool:
        """Evaluate if calls can proceed through the circuit breaker."""
        now = time.monotonic()
        if self.state == BreakerState.CLOSED:
            return True

        if self.state == BreakerState.OPEN:
            if (now - self.last_failure_time) >= self.reset_timeout:
                self.state = BreakerState.HALF_OPEN
                return True
            return False

        # HALF_OPEN: allows 1 probe
        return True

    def record_success(self) -> None:
        """Reset breaker state to CLOSED upon a successful external invocation."""
        self.consecutive_failures = 0
        self.state = BreakerState.CLOSED

    def record_failure(self) -> None:
        """Track failure count and trip breaker to OPEN if threshold reached."""
        self.consecutive_failures += 1
        self.last_failure_time = time.monotonic()
        if self.consecutive_failures >= self.failure_threshold:
            self.state = BreakerState.OPEN

    def reset(self) -> None:
        """Manually force-reset the breaker to CLOSED state."""
        self.consecutive_failures = 0
        self.last_failure_time = 0.0
        self.state = BreakerState.CLOSED

    def get_metrics(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "failure_threshold": self.failure_threshold,
            "reset_timeout_seconds": self.reset_timeout,
        }
