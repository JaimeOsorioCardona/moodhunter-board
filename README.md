# Tablero de Solicitudes con Flujo de Estados (MOOD HUNTER)

Sistema web full-stack para la gestión de solicitudes operativas con máquina de estados finitos (FSM) estricta, control de concurrencia a nivel de base de datos, arquitectura limpia hexagonal y asistente ejecutivo potenciado por Inteligencia Artificial con tolerancia a fallos.

---

## 1. Resumen y Alcance

El proyecto resuelve la gestión trazable de solicitudes de trabajo que deben transitar por un ciclo de vida con reglas de adyacencia estrictas:
- **Secuencia:** `created` → `in_review` → `in_progress` → `done`.
- **Regla de Pausa:** Solo se puede pausar desde `in_review` o `in_progress`. Mientras está en `paused`, está prohibido finalizarla; debe reanudarse primero a `in_progress` o `in_review`.
- **Integración con IA:** Genera resúmenes ejecutivos sobre el estado operativo general, identificando cuellos de botella y riesgos de estancamiento.
- **Aislamiento y Resiliencia:** Si la IA falla, se demora más de 5 segundos o se agota su cuota, el sistema activa un *Circuit Breaker* y responde de forma transparente con un resumen determinista local sin degradar la experiencia de usuario.

---

## 2. Stack Tecnológico y Justificación

| Tecnología | Rol | Justificación |
|---|---|---|
| **Python 3.11 + FastAPI** | Backend API | Rendimiento asíncrono nativo (ASGI), validación tipada estricta y generación automática de contratos OpenAPI / Swagger. |
| **SQLAlchemy 2.0 (Async) + aiomysql** | ORM / Persistencia | Consultas asíncronas no bloqueantes, soporte para transacciones ACID, Unit of Work y bloqueo de filas (`SELECT ... FOR UPDATE`). |
| **Pydantic v2** | Serialización / Validación | Validación ultrarrápida en Rust y tipado estricto en fronteras de red. |
| **MySQL 8.0 (InnoDB)** | Base de datos relacional | Integridad referencial con claves foráneas, aislamiento transaccional `REPEATABLE READ` y soporte para datos semilla. |
| **React 18 + TypeScript + Vite** | Frontend SPA | Desarrollo ágil, tipado estricto en contratos API y empaquetado optimizado para producción. |
| **Tailwind CSS + Lucide Icons** | Diseño y UI | Diseño responsivo (mobile-first), legible, minimalista y accesible sin hojas de estilo infladas. |
| **TanStack Query v5** | Estado del Servidor | Caché declarativa, reintentos automáticos e invalidación granular tras cada mutación. |
| **Docker & Docker Compose** | Infraestructura | Despliegue reproducible con un solo comando para MySQL 8, Backend y Frontend Nginx. |

---

## 3. Despliegue en un Solo Comando

### Requisitos previos
- Docker Desktop o Docker Engine (v20+) y Docker Compose.
- Puerto `3000` (Frontend), `8000` (Backend API) y `3306` (MySQL) disponibles.

### Pasos de ejecución
```bash
# 1. Clonar o posicionarse en la carpeta del repositorio
cd "Prueba Mood Hunter"

# 2. Copiar plantilla de variables de entorno
cp .env.example .env

# 3. (Opcional) Si cuenta con una API Key de Google Gemini, agréguela en el .env:
# GEMINI_API_KEY=AIzaSy...
# Si no la configura, el sistema funcionará 100% operativo en modo fallback automático.

# 4. Levantar los tres contenedores con Docker Compose
docker compose up --build
```

### URLs de acceso
- **Tablero Web (Frontend):** [http://localhost:3000](http://localhost:3000)
- **Documentación Interactiva (Swagger/OpenAPI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Verificación de Salud (Healthcheck):** [http://localhost:8000/health](http://localhost:8000/health)

### Ejecución Local sin Docker (Modo Desarrollo)
Si desea correr los componentes directamente en su máquina:
```bash
# Backend (con SQLite en memoria o MySQL local)
cd backend
python -m venv .venv
.\.venv\Scripts\activate   # En Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd ../frontend
npm install
npm run dev                # Servidor en http://localhost:5173 con proxy automático a backend
```

---

## 4. Variables de Entorno

| Variable | Tipo | Default | Descripción |
|---|---|---|---|
| `ENVIRONMENT` | string | `development` | Entorno de ejecución (`development`, `test`, `production`). |
| `DATABASE_URL` | string | `mysql+aiomysql://moodhunter:moodhunter_pass@db:3306/moodhunter_db` | Cadena de conexión asíncrona de SQLAlchemy. |
| `GEMINI_API_KEY` | string | `""` | Clave API de Google Gemini (opcional; activa resumen por IA). |
| `LLM_MODEL` | string | `gemini-1.5-flash` | Modelo de Google Gemini utilizado. |
| `LLM_TIMEOUT_SECONDS` | float | `5.0` | Tiempo límite de espera antes de activar el fallback. |
| `LLM_CIRCUIT_BREAKER_FAIL_THRESHOLD` | int | `3` | Número de fallos continuos antes de abrir el circuito. |
| `LLM_CIRCUIT_BREAKER_RESET_SECONDS` | int | `60` | Tiempo de espera antes de enviar una sonda de recuperación. |
| `VITE_API_URL` | string | `/api/v1` | Prefijo de ruta consumido por el cliente frontend. |

---

## 5. Arquitectura del Backend

El backend implementa una **Arquitectura Limpia / Hexagonal Simplificada**:

```
Presentation (routers, schemas Pydantic, handlers de error)
      ↓ depende de
Application (RequestService, SummaryService, puertos: ILLMGateway, IUnitOfWork)
      ↓ depende de
Domain (entidades, FSM declarativa, excepciones puras) ← Cero dependencias externas
      ↑ implementan puertos
Infrastructure (SQLAlchemy repositorios, UoW, Gemini LLM, fallback)
```

- **Regla de Dependencia:** El dominio (`app/domain/`) es independiente de frameworks y de la base de datos.
- **Unit of Work:** Asegura que cualquier transición de estado y su registro en la tabla de historial `request_status_history` se confirmen atómicamente.
- **Control de Concurrencia:** Se aplica bloqueo pesimista `SELECT ... FOR UPDATE` a nivel de fila durante la ejecución de cada transición.

Para mayor detalle, consulte la [Guía de Arquitectura](docs/architecture.md).

---

## 6. Máquina de Estados Finitos (FSM)

```
[ created ] ──────────► [ in_review ] ──────────► [ in_progress ] ──────────► [ done ] (terminal)
                             │   ▲                     │   ▲
                             │   │                     │   │
                             ▼   │                     ▼   │
                             └───┴──────► [ paused ] ──┴───┘
```

### Matriz de Transiciones
- **`created`** → solo a `in_review`.
- **`in_review`** → a `in_progress` o a `paused`.
- **`in_progress`** → a `done` o a `paused`.
- **`paused`** → solo puede retornar a `in_review` o a `in_progress`. **Nunca directamente a `done`**.
- **`done`** → estado terminal; sin transiciones salientes.

### Decisión de Código HTTP: 409 Conflict frente a 422
- Se responde **HTTP 409 Conflict** cuando una transición viola las reglas de adyacencia de la FSM (ej. intentar pasar de `created` a `in_progress`, o de `paused` a `done`). La petición es sintácticamente válida pero entra en conflicto con el estado actual del recurso en el servidor.
- Se reserva **HTTP 422** para errores de validación de sintaxis o tipos de datos en el cuerpo JSON (Pydantic).

Para la especificación formal y las 25 combinaciones posibles, consulte la [Documentación de la FSM](docs/fsm.md).

---

## 7. Modelo de Datos y Justificación

### DDL (MySQL 8)
El esquema completo reside en [`db/init.sql`](db/init.sql). Se compone de tres tablas:

1. **`statuses`**: Catálogo de estados con clave primaria numérica y clave única por slug (`code`).
2. **`requests`**: Solicitud principal con identificador público expuesto `public_id` (UUIDv4), clave foránea `status_id`, contador de versión optimista `version` y marcas temporales `created_at` y `updated_at`.
3. **`request_status_history`**: Registro inmutable de auditoría con `from_status_id` (nulo en la creación), `to_status_id` y `changed_at`.

### Justificación de Slugs y UUIDs
- **Por qué slugs (`code`) en la API:** Los slugs (`"in_review"`, `"in_progress"`) mantienen la estabilidad del contrato API independientemente de los IDs autoincrementales internos de la base de datos.
- **Por qué `public_id` (UUIDv4):** Evita la enumeración maliciosa de recursos en endpoints públicos (`/requests/1`, `/requests/2`) y desacopla la identificación externa de la estructura de claves primarias.

---

## 8. Documentación de Endpoints y Ejemplos cURL

| Método | Endpoint | Descripción | Códigos Respuesta |
|---|---|---|---|
| `POST` | `/api/v1/requests` | Crea una nueva solicitud en estado `created` | 201, 422 |
| `GET` | `/api/v1/requests` | Lista solicitudes (filtro opcional `?status=code`) | 200, 422 |
| `GET` | `/api/v1/requests/{public_id}` | Consulta detalle e historial de una solicitud | 200, 404 |
| `PATCH` | `/api/v1/requests/{public_id}` | Modifica título y/o descripción | 200, 404, 422 |
| `GET` | `/api/v1/requests/{public_id}/allowed-transitions` | Consulta destinos válidos desde el estado actual | 200, 404 |
| `POST` | `/api/v1/requests/{public_id}/transitions` | Ejecuta cambio de estado validado por la FSM | 200, 404, 409, 422 |
| `POST` | `/api/v1/requests/ai-summary` | Dispara o recupera el resumen ejecutivo | 200 |
| `GET` | `/health` | Healthcheck de base de datos y circuit breaker | 200, 503 |

### Ejemplos cURL

#### 1. Crear Solicitud
```bash
curl -X POST http://localhost:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{"title": "Configurar pasarela de pagos", "description": "Integrar webhooks de Stripe"}'
```

#### 2. Consultar Transiciones Permitidas
```bash
curl http://localhost:8000/api/v1/requests/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/allowed-transitions
```

#### 3. Ejecutar Transición Válida
```bash
curl -X POST http://localhost:8000/api/v1/requests/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/transitions \
  -H "Content-Type: application/json" \
  -d '{"target_status": "in_review"}'
```

#### 4. Ejemplo de Transición Inválida (Retorna 409 Conflict)
```bash
curl -X POST http://localhost:8000/api/v1/requests/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/transitions \
  -H "Content-Type: application/json" \
  -d '{"target_status": "done"}'
```
*Respuesta:*
```json
{
  "error": "transition_not_allowed",
  "message": "No se permite la transición de 'created' a 'done'. Estados permitidos: ['in_review'].",
  "details": {
    "current": "created",
    "target": "done",
    "allowed": ["in_review"]
  }
}
```

#### 5. Generar Resumen con IA
```bash
curl -X POST http://localhost:8000/api/v1/requests/ai-summary
```

---

## 9. Integración con LLM y Control de Costos

### Minimización de Datos
El backend precalcula los totales por estado y los días de inactividad de cada solicitud. Al modelo solo se envía:
- Conteos numéricos agregados (`counts`).
- Lista acotada (máx 50 ítems) priorizando solicitudes pausadas y de mayor inactividad.
- Campos enviados: ref corta (8 caracteres), título truncado (80 caracteres), estado y fecha de actualización.
- **No se envían** descripciones largas, UUIDs completos ni datos de auditoría interna.

### Estrategia de Resiliencia
- **Timeout estricto:** 5.0 segundos.
- **Circuit Breaker:** Si ocurren 3 fallos consecutivos, el circuito se abre por 60 segundos evitando llamadas externas.
- **Fallback Determinista:** Si la IA falla o no tiene clave, el sistema genera localmente un resumen con métricas y alertas. La respuesta siempre es `200 OK` con `"source": "fallback"`.
- **Caché:** En memoria (TTL 5 min por hash SHA-256 del snapshot) y en cliente (`localStorage`).

---

## 10. Decisiones de Frontend (UX/UI)

- **Prevención de Acciones Inválidas:** Las tarjetas de solicitud solo muestran botones para las transiciones permitidas según la FSM.
- **Feedback Inmediato y Toasts:** Las mutaciones exitosas y los errores 409 muestran notificaciones flotantes con el mensaje exacto retornado por el servidor.
- **Layout Responsivo:** Tablero Kanban multicolumna en pantallas medianas/grandes y navegación fluida por pestañas de estado en dispositivos móviles.
- **Resumen Colapsable:** Tarjeta superior con indicador visual de fuente (`Gemini AI` vs `Resumen automático`), esqueleto de carga y botón para forzar la regeneración.

---

## 11. Ejecución de Pruebas Automatizadas

La suite de pruebas cubre la matriz exhaustiva de la FSM (25 combinaciones), la resiliencia del Circuit Breaker, el fallback y la integración completa de endpoints:

```bash
# Ejecutar todas las pruebas con pytest
cd backend
.\.venv\Scripts\pytest backend\tests\ -v
```

*Resultado:* **44 pruebas unitarias e integradas pasando en menos de 1 segundo**.

---

## 12. Uso de IA en el Desarrollo

Para un desglose completo de las herramientas utilizadas, las decisiones de arquitectura y las correcciones humanas realizadas durante el desarrollo, consulte el documento:
👉 **[docs/ai-usage.md](docs/ai-usage.md)**

---

## 13. Trade-offs y Limitaciones

- **Autenticación:** Al ser una prueba técnica enfocada en FSM e integración LLM, no se implementó autenticación/roles de usuario.
- **Circuit Breaker en Memoria:** Adecuado para instancias únicas. En un despliegue horizontal multi-nodo, se recomendaría respaldarlo en Redis.
- **Paginación:** Las solicitudes se listan completas (óptimo para tableros Kanban de tamaño medio). Para decenas de miles de tarjetas convendría paginación virtualizada.

---

## 14. Mejoras Futuras

1. **WebSockets o Server-Sent Events (SSE):** Actualización en tiempo real del tablero cuando múltiples colaboradores mueven tarjetas en simultáneo.
2. **Historial visual con Timeline:** Drawer o panel lateral en la UI que renderice el historial cronológico de cambios de cada solicitud.
3. **Métricas con OpenTelemetry:** Trazas distribuidas que midan con precisión los percentiles de latencia del proveedor de IA.

---

## 15. Convención de Commits y Lectura del Historial

El repositorio sigue estrictamente la especificación **Conventional Commits** y una secuencia de hitos lógicos:

```bash
git log --oneline
```
- `chore: init monorepo structure`
- `chore(docker): add compose with mysql, backend, frontend`
- `chore: configure ruff, mypy, eslint and pre-commit`
- `feat(db): add statuses, requests and history DDL with seeds`
- `feat(db): add SQLAlchemy models and alembic baseline`
- `test(domain): add exhaustive transition matrix tests (red)` *(TDD antes de la implementación)*
- `feat(domain): implement declarative FSM and domain exceptions`
- `feat(api): add repositories and unit of work`
- `feat(api): create/list/update request endpoints`
- `feat(api): allowed-transitions and transition endpoints with row lock`
- `feat(api): global domain exception handlers`
- `test(api): integration tests for transitions`
- `feat(llm): define ILLMGateway port and snapshot builder`
- `feat(llm): add gemini adapter with timeout and schema validation`
- `feat(llm): add circuit breaker and deterministic fallback`
- `test(llm): cover timeout, quota and invalid json paths`
- `feat(web): scaffold vite react ts tailwind`
- `feat(web): add typed api client and query hooks`
- `feat(web): kanban board and request cards`
- `feat(web): create and edit dialogs`
- `feat(web): toasts and 409 handling`
- `feat(web): collapsible AI summary card with skeleton, cache and fallback badge`
- `style(web): responsive mobile layout and board integration`
- `docs: add README with setup, endpoints and rationale`
- `docs: add architecture diagrams and AI usage breakdown`
