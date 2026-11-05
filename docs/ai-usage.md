# Uso de Inteligencia Artificial en el Desarrollo (MOOD HUNTER)

> **Requisito de la prueba técnica:** Documentar de manera transparente qué herramientas de IA se utilizaron, para qué tareas, qué decisiones fueron tomadas por el ingeniero y qué correcciones humanas fueron necesarias.

---

## 1. Herramientas Utilizadas y Propósito

| Herramienta | Caso de Uso en el Proyecto |
|---|---|
| **Google Antigravity & Gemini 3.8 Flash** | Pair programming, diseño de arquitectura hexagonal, scaffolding de tipos TypeScript, generación de fixtures de pruebas y diseño responsive. |
| **Google Gemini API (`gemini-1.5-flash`)** | Modelo integrado en tiempo de ejecución (`runtime`) dentro del backend para el análisis y resumen ejecutivo del tablero de solicitudes. |

---

## 2. Decisiones Humanas y Validación Crítica

Durante el desarrollo, la IA propuso diferentes alternativas que fueron evaluadas, filtradas o corregidas manualmente:

1. **Rechazo del State Pattern orientado a clases:**  
   *Sugerencia inicial:* Crear clases polimórficas `CreatedState`, `InReviewState`, `PausedState` con métodos `advance()`.  
   *Decisión humana:* Se descartó en favor de una **FSM declarativa en diccionario** (`ALLOWED: dict[Status, frozenset[Status]]`). En este dominio los estados no ejecutan lógica polimórfica distinta; representan un grafo estático de adyacencia. Un diccionario es 100% determinista, legible en una sola pantalla y se valida en microsegundos.

2. **Decisión de Código HTTP 409 Conflict frente a 422:**  
   *Análisis:* Muchas APIs devuelven 400 o 422 para cualquier error de negocio.  
   *Decisión humana:* Se estableció la distinción estricta según el estándar HTTP RFC 9110: 422 se reserva para fallos de payload (Pydantic), mientras que 409 se utiliza cuando el payload es válido pero colisiona con el estado actual del recurso en la base de datos.

3. **Corrección de Compatibilidad SQLite vs MySQL en Pruebas Unitarias:**  
   *Incidencia detectada:* En SQLite, declarar claves primarias autoincrementales como `BigInteger` causa fallos de integridad `NOT NULL constraint failed: requests.id` porque SQLite requiere afinidad `INTEGER`.  
   *Corrección humana:* Se implementó `BigInteger().with_variant(Integer, "sqlite")` en los modelos SQLAlchemy para mantener `BIGINT UNSIGNED` en MySQL de producción y permitir pruebas ultrarrápidas en SQLite en memoria sin requerir contenedores activos.

4. **Prevención de Lazy Loading en SQLAlchemy Async:**  
   *Incidencia:* En Python asíncrono, acceder a relaciones ORM no cargadas explícitamente (`lazy="select"`) bloquea o genera excepciones de contexto verde.  
   *Corrección humana:* Se configuró `selectinload` y `joinedload` en las consultas del repositorio, y se desacopló el retorno mediante entidades de dominio puras (`RequestEntity`).

---

## 3. Estrategia de Prompting y Minimización de Datos en Runtime

Para la integración con el LLM en producción, se aplicaron principios de ingeniería de prompts y privacidad:

### 1. Minimización de Datos (Privacy & Token Efficiency)
- **Qué se envía al LLM:**
  - Conteos agregados por estado (`counts`).
  - Lista acotada (máx 50 ítems), priorizando solicitudes `paused` y las de mayor inactividad.
  - Para cada ítem: únicamente un prefijo corto de referencia (`public_id[:8]`), título truncado a 80 caracteres, estado y días de inactividad calculados en el servidor.
- **Qué NO se envía:**
  - Descripciones completas, identificadores UUID completos, marcas de tiempo con milisegundos, claves foráneas o datos internos.
- **Justificación:** Reduce el costo en más de un 80%, evita que el LLM cometa errores de conteo aritmético (el backend suma los números) y minimiza la superficie de datos expuestos a terceros.

### 2. Resiliencia de Producción (Aislamiento Total)
- Timeout estricto de 5 segundos.
- Circuit Breaker con apertura a los 3 fallos consecutivos y sonda de recuperación a los 60 segundos.
- Fallback determinista local que asegura que el endpoint siempre responda `200 OK` con información veraz y relevante incluso si la API de IA está caída o la cuota se agota.
- Caché SHA-256 en memoria con TTL de 5 minutos para eliminar costos por clics redundantes.
