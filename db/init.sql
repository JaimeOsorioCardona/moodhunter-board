-- ==============================================================================
-- MOOD HUNTER - Tablero de Solicitudes con Flujo de Estados
-- Esquema DDL y Datos Semilla (MySQL 8.0+)
-- ==============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Tabla: statuses (Catálogo de estados)
-- Justificación de slugs: los slugs ('created', 'in_review', etc.) proveen estabilidad
-- de contrato API independiente de autoincrementales, tipado seguro y legibilidad.
CREATE TABLE IF NOT EXISTS statuses (
  id          TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code        VARCHAR(32)  NOT NULL,
  name        VARCHAR(64)  NOT NULL,
  description VARCHAR(255) NULL,
  sort_order  TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uq_statuses_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tabla: requests (Solicitudes principales)
-- public_id es un UUIDv4 expuesto a clientes externos para no filtrar IDs numéricos.
-- version permite control de concurrencia optimista.
CREATE TABLE IF NOT EXISTS requests (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  public_id   CHAR(36)     NOT NULL,
  title       VARCHAR(150) NOT NULL,
  description TEXT         NULL,
  status_id   TINYINT UNSIGNED NOT NULL,
  version     INT UNSIGNED NOT NULL DEFAULT 1,
  created_at  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                           ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uq_requests_public_id (public_id),
  KEY idx_requests_status_updated (status_id, updated_at),
  KEY idx_requests_updated (updated_at),
  CONSTRAINT fk_requests_status FOREIGN KEY (status_id) REFERENCES statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabla: request_status_history (Trazabilidad y auditoría de transiciones)
CREATE TABLE IF NOT EXISTS request_status_history (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  request_id     BIGINT UNSIGNED NOT NULL,
  from_status_id TINYINT UNSIGNED NULL,
  to_status_id   TINYINT UNSIGNED NOT NULL,
  changed_at     DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_hist_request (request_id, changed_at),
  CONSTRAINT fk_hist_request FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
  CONSTRAINT fk_hist_from FOREIGN KEY (from_status_id) REFERENCES statuses(id) ON DELETE RESTRICT,
  CONSTRAINT fk_hist_to   FOREIGN KEY (to_status_id)   REFERENCES statuses(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ==============================================================================
-- DATOS SEMILLA (SEEDS)
-- ==============================================================================

-- Catálogo de estados
INSERT INTO statuses (id, code, name, description, sort_order) VALUES
 (1, 'created',     'Creada',      'Solicitud recién registrada en el sistema', 1),
 (2, 'in_review',   'En revisión', 'Solicitud en evaluación técnica y de negocio', 2),
 (3, 'in_progress', 'En progreso', 'Trabajo activo de desarrollo o ejecución', 3),
 (4, 'paused',      'Pausada',     'Detenida temporalmente por bloqueo o espera', 4),
 (5, 'done',        'Finalizada',  'Completada y aprobada satisfactoriamente', 5)
ON DUPLICATE KEY UPDATE name=VALUES(name), description=VALUES(description), sort_order=VALUES(sort_order);

-- Solicitudes de ejemplo para que el tablero inicie con datos representativos
INSERT INTO requests (id, public_id, title, description, status_id, version, created_at, updated_at) VALUES
 (1, '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d', 'Configurar webhook de pagos Stripe', 'Implementar validación de firma y manejo de eventos checkout.session.completed', 1, 1, NOW(3) - INTERVAL 2 DAY, NOW(3) - INTERVAL 2 DAY),
 (2, 'a5c7f8e1-4d2b-4e9a-8c11-9f2d5e7a8b3c', 'Refactorizar módulo de autenticación con JWT', 'Migrar almacenamiento de tokens a cookies HttpOnly y rotación de refresh tokens', 2, 2, NOW(3) - INTERVAL 4 DAY, NOW(3) - INTERVAL 1 DAY),
 (3, 'b8e2d4c6-7a1f-4b9e-9d33-1c5e7a9f2b4d', 'Optimizar consultas lentas del dashboard', 'Crear índices compuestos y cachear agregaciones pesadas en Redis', 3, 3, NOW(3) - INTERVAL 6 DAY, NOW(3) - INTERVAL 3 HOUR),
 (4, 'c1f4e7a9-2b5d-4c8e-8a22-3d6f8b1a4c5e', 'Integrar proveedor alternativo de SMS para 2FA', 'En espera de aprobación presupuestal del proveedor Twilio / MessageBird', 4, 3, NOW(3) - INTERVAL 10 DAY, NOW(3) - INTERVAL 8 DAY),
 (5, 'd3a6c9f2-5e8b-4a1d-9f44-5b7c9e2a1d3f', 'Actualizar dependencias críticas de seguridad', 'Mitigación de vulnerabilidades CVE en bibliotecas de hashing y serialización', 5, 4, NOW(3) - INTERVAL 12 DAY, NOW(3) - INTERVAL 5 DAY)
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- Historial de transiciones para las solicitudes semilla
INSERT INTO request_status_history (request_id, from_status_id, to_status_id, changed_at) VALUES
 (1, NULL, 1, NOW(3) - INTERVAL 2 DAY),
 (2, NULL, 1, NOW(3) - INTERVAL 4 DAY),
 (2, 1, 2,    NOW(3) - INTERVAL 1 DAY),
 (3, NULL, 1, NOW(3) - INTERVAL 6 DAY),
 (3, 1, 2,    NOW(3) - INTERVAL 4 DAY),
 (3, 2, 3,    NOW(3) - INTERVAL 3 HOUR),
 (4, NULL, 1, NOW(3) - INTERVAL 10 DAY),
 (4, 1, 2,    NOW(3) - INTERVAL 9 DAY),
 (4, 2, 4,    NOW(3) - INTERVAL 8 DAY),
 (5, NULL, 1, NOW(3) - INTERVAL 12 DAY),
 (5, 1, 2,    NOW(3) - INTERVAL 10 DAY),
 (5, 2, 3,    NOW(3) - INTERVAL 7 DAY),
 (5, 3, 5,    NOW(3) - INTERVAL 5 DAY);
