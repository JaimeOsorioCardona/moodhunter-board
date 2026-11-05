"""Unit tests for the Circuit Breaker pattern."""

import time
from app.infrastructure.llm.circuit_breaker import BreakerState, CircuitBreaker


def test_circuit_breaker_initially_closed():
    breaker = CircuitBreaker(failure_threshold=3, reset_timeout=1.0)
    assert breaker.state == BreakerState.CLOSED
    assert breaker.can_execute() is True


def test_circuit_breaker_trips_to_open_after_threshold_failures():
    breaker = CircuitBreaker(failure_threshold=3, reset_timeout=1.0)

    breaker.record_failure()
    assert breaker.state == BreakerState.CLOSED
    assert breaker.can_execute() is True

    breaker.record_failure()
    assert breaker.state == BreakerState.CLOSED
    assert breaker.can_execute() is True

    breaker.record_failure()
    # 3 failures reached -> should trip to OPEN
    assert breaker.state == BreakerState.OPEN
    assert breaker.can_execute() is False


def test_circuit_breaker_transitions_to_half_open_after_timeout():
    breaker = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)

    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == BreakerState.OPEN
    assert breaker.can_execute() is False

    # Wait for reset timeout
    time.sleep(0.15)
    assert breaker.can_execute() is True
    assert breaker.state == BreakerState.HALF_OPEN


def test_circuit_breaker_recovers_to_closed_on_success():
    breaker = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)

    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == BreakerState.OPEN

    time.sleep(0.15)
    assert breaker.can_execute() is True  # Enters HALF_OPEN

    breaker.record_success()
    assert breaker.state == BreakerState.CLOSED
    assert breaker.consecutive_failures == 0
