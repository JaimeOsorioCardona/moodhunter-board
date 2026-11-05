"""Google Gemini API Gateway adapter with resiliency, timeout, and schema validation."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
import httpx
from pydantic import BaseModel, Field

from app.application.ports import ILLMGateway
from app.infrastructure.llm.circuit_breaker import CircuitBreaker
from app.infrastructure.llm.fallback import build_deterministic_fallback

logger = logging.getLogger("moodhunter.llm")

SYSTEM_INSTRUCTION = """Eres un analista de operaciones. Recibes un snapshot JSON de un tablero de
solicitudes con estados: created, in_review, in_progress, paused, done.
Responde SOLO en JSON válido con este esquema:
{
  "headline": string (máx 140 caracteres),
  "highlights": string[] (máx 4, una línea cada una),
  "risks": string[] (máx 3; menciona solicitudes pausadas o sin movimiento > 7 días),
  "next_actions": string[] (máx 3, imperativas)
}
Reglas: usa únicamente los datos recibidos; no inventes solicitudes ni cifras;
español neutro; sin markdown."""


class LLMOutputSchema(BaseModel):
    headline: str = Field(..., max_length=140)
    highlights: list[str] = Field(default_factory=list, max_length=4)
    risks: list[str] = Field(default_factory=list, max_length=3)
    next_actions: list[str] = Field(default_factory=list, max_length=3)


class GeminiGateway(ILLMGateway):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        timeout_seconds: float = 5.0,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    async def generate_summary(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Generate executive summary using Gemini API, with automatic fallback on any failure."""
        # 1. If no API key configured, use deterministic fallback immediately
        if not self.api_key or not self.api_key.strip():
            logger.info("GEMINI_API_KEY no configurada. Usando fallback determinista.")
            return build_deterministic_fallback(snapshot)

        # 2. Check Circuit Breaker
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker abierto. Solicitud derivada a fallback determinista.")
            return build_deterministic_fallback(snapshot)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{SYSTEM_INSTRUCTION}\n\nSNAPSHOT:\n{json.dumps(snapshot, ensure_ascii=False)}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout_seconds)) as client:
                response = await client.post(url, json=payload)

            if response.status_code != 200:
                logger.error("Gemini API respondió con status %d: %s", response.status_code, response.text)
                self.circuit_breaker.record_failure()
                return build_deterministic_fallback(snapshot)

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                logger.error("Gemini API no devolvió candidatos.")
                self.circuit_breaker.record_failure()
                return build_deterministic_fallback(snapshot)

            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

            # Parse and validate with Pydantic
            parsed_json = json.loads(raw_text)
            validated = LLMOutputSchema.model_validate(parsed_json)

            self.circuit_breaker.record_success()
            logger.info("Resumen generado exitosamente vía Gemini LLM.")

            return {
                "source": "llm",
                "headline": validated.headline,
                "highlights": validated.highlights,
                "risks": validated.risks,
                "next_actions": validated.next_actions,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            }

        except (httpx.TimeoutException, httpx.RequestError) as net_err:
            logger.warning("Timeout o error de red contactando a Gemini (%s). Fallback activado.", net_err)
            self.circuit_breaker.record_failure()
            return build_deterministic_fallback(snapshot)
        except (json.JSONDecodeError, Exception) as val_err:
            logger.warning("Error de parsing o validación de respuesta LLM (%s). Fallback activado.", val_err)
            self.circuit_breaker.record_failure()
            return build_deterministic_fallback(snapshot)
