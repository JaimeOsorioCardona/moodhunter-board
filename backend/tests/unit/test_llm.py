"""Unit tests for LLM Gateway, deterministic fallback, and resilience."""

import pytest
from app.infrastructure.llm.circuit_breaker import BreakerState, CircuitBreaker
from app.infrastructure.llm.fallback import build_deterministic_fallback
from app.infrastructure.llm.gemini_gateway import GeminiGateway


def test_deterministic_fallback_structure():
    snapshot = {
        "counts": {"created": 2, "in_review": 1, "in_progress": 3, "paused": 1, "done": 4},
        "items": [
            {
                "ref": "a1b2c3d4",
                "title": "Migrar login legacy",
                "status": "paused",
                "updated": "2026-10-01",
                "days_without_update": 12,
            }
        ],
    }
    result = build_deterministic_fallback(snapshot)

    assert result["source"] == "fallback"
    assert "headline" in result
    assert len(result["headline"]) <= 140
    assert "11 solicitudes" in result["headline"]
    assert len(result["highlights"]) >= 1
    assert any("pausada" in r for r in result["risks"])
    assert any("días sin movimiento" in r for r in result["risks"])
    assert len(result["next_actions"]) >= 1


@pytest.mark.anyio
async def test_gateway_without_api_key_returns_fallback_immediately():
    gateway = GeminiGateway(api_key=None)
    snapshot = {"counts": {"created": 1, "done": 1}, "items": []}

    result = await gateway.generate_summary(snapshot)
    assert result["source"] == "fallback"
    assert "Tablero con 2 solicitudes" in result["headline"]


@pytest.mark.anyio
async def test_gateway_tripped_breaker_returns_fallback_without_network():
    breaker = CircuitBreaker(failure_threshold=1)
    breaker.record_failure()
    assert breaker.state == BreakerState.OPEN

    gateway = GeminiGateway(api_key="fake-key", circuit_breaker=breaker)
    snapshot = {"counts": {"created": 0}, "items": []}

    result = await gateway.generate_summary(snapshot)
    assert result["source"] == "fallback"
