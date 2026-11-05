# Máquina de Estados Finitos (FSM) - Especificación y Reglas

Este documento describe la especificación formal del ciclo de vida de las solicitudes en MOOD HUNTER.

---

## 1. Diagrama de Estados

```
[ created ] ──────────► [ in_review ] ──────────► [ in_progress ] ──────────► [ done ]
                             │   ▲                     │   ▲                     (terminal)
                             │   │                     │   │
                             ▼   │                     ▼   │
                             └───┴──────► [ paused ] ──┴───┘
                                             │
                                             └─── Solo puede retornar a:
                                                  • in_review
                                                  • in_progress
                                                  ✗ Prohibido avanzar directo a done
                                                  ✗ Prohibido volver a created
```

---

## 2. Matriz Completa de Transiciones (25 combinaciones)

Fila = **Estado Origen** (`current`)  
Columna = **Estado Destino** (`target`)

| Desde \ Hacia | `created` | `in_review` | `in_progress` | `paused` | `done` |
|---|:---:|:---:|:---:|:---:|:---:|
| **`created`** | ❌ (No-op) | ✅ **Permitido** | ❌ Rechazado | ❌ Rechazado | ❌ Rechazado |
| **`in_review`** | ❌ Rechazado | ❌ (No-op) | ✅ **Permitido** | ✅ **Permitido** | ❌ Rechazado |
| **`in_progress`** | ❌ Rechazado | ❌ Rechazado | ❌ (No-op) | ✅ **Permitido** | ✅ **Permitido** |
| **`paused`** | ❌ Rechazado | ✅ **Permitido** | ✅ **Permitido** | ❌ (No-op) | ❌ **Rechazado** |
| **`done`** | ❌ Terminal | ❌ Terminal | ❌ Terminal | ❌ Terminal | ❌ Terminal |

---

## 3. Reglas de Negocio Explícitas

1. **Estado Inicial Obligatorio:**
   - Toda solicitud creada entra indefectiblemente en el estado `created`.
2. **Avance Secuencial Estricto:**
   - El flujo principal es hacia adelante: `created` → `in_review` → `in_progress` → `done`.
   - Saltos no adyacentes (como `created` → `in_progress` o `in_review` → `done`) son inválidos y rechazados.
3. **Comportamiento del Estado `paused`:**
   - Una solicitud solo puede ser pausada desde `in_review` o desde `in_progress`.
   - Estando en `paused`, el flujo se congela. **No puede avanzar directamente a `done`** bajo ninguna circunstancia.
   - Para avanzar o finalizar, la solicitud debe ser reanudada explícitamente hacia `in_progress` (para retomar labores) o hacia `in_review` (si requiere nueva evaluación).
4. **Estado Terminal `done`:**
   - Una solicitud en `done` no admite ninguna transición saliente; representa un estado cerrado y final.

---

## 4. Código HTTP de Error: Decisión 409 Conflict vs 422 Unprocessable

- **HTTP 409 Conflict:**  
  Se retorna cuando la petición es sintácticamente correcta y el payload es válido, pero la acción solicitada entra en **conflicto con el estado actual del recurso** en el servidor (RFC 9110 §15.5.10).
  ```json
  {
    "error": "transition_not_allowed",
    "message": "No se permite la transición de 'paused' a 'done'. Estados permitidos: ['in_progress', 'in_review'].",
    "details": {
      "current": "paused",
      "target": "done",
      "allowed": ["in_progress", "in_review"]
    }
  }
  ```
- **HTTP 422 Unprocessable Entity:**  
  Se reserva exclusivamente para errores de validación de esquema sintáctico o semántico en el cuerpo JSON (por ejemplo, enviar un slug desconocido como `target_status: "invalido"` o un título vacío).
