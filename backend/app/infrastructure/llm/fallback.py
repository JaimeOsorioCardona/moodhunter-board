"""Deterministic local fallback generator when LLM is unreachable or disabled."""

from datetime import datetime, timezone
from typing import Any


def build_deterministic_fallback(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Construct an informative executive summary locally without AI dependencies.

    Guarantees that the system never breaks and the user receives valuable insights.
    """
    counts = snapshot.get("counts", {})
    created = counts.get("created", 0)
    in_review = counts.get("in_review", 0)
    in_progress = counts.get("in_progress", 0)
    paused = counts.get("paused", 0)
    done = counts.get("done", 0)
    total = created + in_review + in_progress + paused + done

    # Headline (max 140 chars)
    if total == 0:
        headline = "El tablero no registra solicitudes activas actualmente."
    else:
        headline = (
            f"Tablero con {total} solicitudes: {in_progress} en progreso, "
            f"{in_review} en revisión y {paused} pausadas."
        )[:140]

    # Highlights
    highlights = [
        f"Volumen total: {total} solicitudes registradas en el flujo.",
        f"{done} solicitud(es) finalizada(s) con éxito ({(done * 100 // total) if total else 0}% completitud).",
        f"{in_progress} solicitud(es) en desarrollo activo y {in_review} en fase de evaluación.",
    ]
    if created > 0:
        highlights.append(f"{created} nueva(s) solicitud(es) en espera de revisión.")

    # Risks (paused items or stagnated items)
    risks = []
    if paused > 0:
        risks.append(f"Atención: {paused} solicitud(es) en estado 'pausada' que requieren diagnóstico o desbloqueo.")

    # Detect items with > 7 days without update in snapshot
    stagnant_items = [
        item for item in snapshot.get("items", [])
        if item.get("days_without_update", 0) >= 7 and item.get("status") != "done"
    ]
    if stagnant_items:
        first = stagnant_items[0]
        risks.append(
            f"Inactividad: '{first.get('title')}' lleva {first.get('days_without_update')} días sin movimiento."
        )

    if not risks:
        risks.append("No se detectan bloqueos críticos ni solicitudes estancadas en el tablero.")

    # Next actions
    next_actions = []
    if created > 0:
        next_actions.append("Revisar y clasificar las solicitudes en estado 'created'.")
    if paused > 0:
        next_actions.append("Evaluar los motivos de pausa para reanudar a 'in_progress' o reevaluar.")
    if in_progress > 0:
        next_actions.append("Monitorear el avance del trabajo en curso para llevarlo a 'done'.")
    if not next_actions:
        next_actions.append("Registrar nuevas solicitudes para iniciar el ciclo operativo.")

    return {
        "source": "fallback",
        "headline": headline,
        "highlights": highlights[:4],
        "risks": risks[:3],
        "next_actions": next_actions[:3],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
    }
