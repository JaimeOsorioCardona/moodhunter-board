# Arquitectura del Sistema: Tablero de Solicitudes (MOOD HUNTER)

Este documento detalla los principios de diseño, la estructura de capas y los patrones arquitectónicos implementados en la solución.

---

## 1. Principio Fundamental: Arquitectura Limpia / Hexagonal Simplificada

El sistema adopta una arquitectura en capas concéntricas con regla de dependencia unidireccional hacia el centro:

```
┌────────────────────────────────────────────────────────┐
│                      Presentation                      │
│        (FastAPI routers, Pydantic schemas, UI)         │
└───────────────────────────┬────────────────────────────┘
                            │  depende de
                            ▼
┌────────────────────────────────────────────────────────┐
│                      Application                       │
│    (RequestService, SummaryService, Puertos/Interfaces)│
└───────────────────────────┬────────────────────────────┘
                            │  depende de
                            ▼
┌────────────────────────────────────────────────────────┐
│                        Domain                          │
│     (Entidades, FSM declarativa, Excepciones puras)    │
│            * CERO dependencias externas *              │
└────────────────────────────────────────────────────────┘
                            ▲
                            │  implementan puertos
┌───────────────────────────┴────────────────────────────┘
│                     Infrastructure                     │
│  (SQLAlchemy Repositories, Unit of Work, Gemini LLM)   │
└────────────────────────────────────────────────────────┘
```

### Regla de Independencia de Dominio
- El paquete `app/domain/` no importa **FastAPI**, **SQLAlchemy**, **Pydantic** ni bibliotecas de terceros.
- Toda la lógica de negocio, validación de estados y excepciones son tipos nativos de Python (`StrEnum`, dataclasses, `Exception`).
- Esto garantiza que el núcleo de negocio sea testeable en milisegundos sin levantar motores de base de datos ni servidores web.

---

## 2. Patrones Arquitectónicos y Justificación

| Patrón | Ubicación | Justificación Técnica |
|---|---|---|
| **FSM Declarativa** (Diccionario / Grafo dirigido) | `app/domain/fsm.py` | Evita la complejidad innecesaria de jerarquías de clases cuando los estados no tienen comportamiento polimórfico, sino únicamente reglas deterministas de adyacencia y transiciones permitidas. |
| **Unit of Work (UoW)** | `app/infrastructure/db/uow.py` | Garantiza atomicidad estricta (`ACID`): la actualización del estado de una solicitud y la inserción del registro correspondiente en `request_status_history` se confirman (`commit`) o revierten (`rollback`) juntas. |
| **Repository** | `app/infrastructure/db/repositories.py` | Aísla las consultas de persistencia (SQLAlchemy ORM) desacoplando la capa de aplicación de los detalles del motor de base de datos. |
| **Ports & Adapters (Hexagonal)** | `app/application/ports.py` → `GeminiGateway` | Define interfaces abstractas (`ILLMGateway`, `IUnitOfWork`, `IRequestRepository`). Permite sustituir el proveedor de IA (o mockearlo en pruebas unitarias) sin tocar la capa de aplicación. |
| **Circuit Breaker** | `app/infrastructure/llm/circuit_breaker.py` | Protege contra cascadas de fallos cuando el proveedor externo (Gemini API) experimenta latencia, errores 5xx o agotamiento de cuota (429). |
| **Deterministic Fallback** | `app/infrastructure/llm/fallback.py` | Asegura alta disponibilidad: si el servicio de IA no está disponible o no se configura API key, el usuario sigue recibiendo un resumen estructurado y la API responde siempre `200 OK`. |

---

## 3. Concurrencia y Control Transaccional

### Bloqueo Pesimista a Nivel de Fila (`SELECT ... FOR UPDATE`)
Para evitar que dos usuarios o procesos hagan clic simultáneamente en transiciones conflictivas (Race Conditions) y violen la FSM:
1. Al invocar `POST /api/v1/requests/{public_id}/transitions`, el `RequestService` solicita al repositorio el registro con bloqueo exclusivo (`for_update=True`).
2. En MySQL, esto emite `SELECT ... FOR UPDATE` dentro de la transacción activa del UoW.
3. Se evalúa la transición con `assert_transition(current_status, target_status)`.
4. Si la transición es válida, se actualiza el estado, se incrementa la columna `version`, se inserta en `request_status_history` y se confirma la transacción.
5. Cualquier transacción concurrente que intente leer la misma fila para actualizarla esperará a que el bloqueo se libere, encontrando el nuevo estado y siendo rechazada con `409 Conflict` si ya no es una transición válida.

---

## 4. Observabilidad y Monitoreo

- **Request ID Middleware:** Cada solicitud HTTP recibe o genera un UUID `X-Request-ID` que se propaga en cabeceras de respuesta y registros de log.
- **Structured JSON Logging:** Todos los logs se emiten en formato JSON estructurado con `time`, `level`, `request_id`, `method`, `path`, `status` y `duration_ms`.
- **Healthcheck:** El endpoint `GET /health` comprueba activamente la conectividad con la base de datos y expone el estado del Circuit Breaker.
