-- ============================================================================
-- TP8 · Unidad 8 · Consigna 2.b
-- Semaforo de sincronizacion (se ejecuta en la tablet, SQLite).
--
-- Compara cada solicitud PENDIENTE contra snapshot_servidor y guarda en
-- cola_sync el estado y el motivo:
--   Rojo    RECHAZADO           producto inexistente / no disponible /
--                               dado de baja / stock insuficiente
--   Amarillo CONFLICTO          no hay rojo, pero cambio algun precio
--   Verde    SIMULADO_APROBADO  todo coincide
--
-- Reglas:
--   - Solo se evaluan las solicitudes PENDIENTE. Repetir la simulacion no
--     reevalua lo ya resuelto (idempotencia del caso C6).
--   - NO se modifica nada en PostgreSQL. SIMULADO_APROBADO no es una venta:
--     es solo un borrador que el servidor todavia debe confirmar.
--
-- Ejecutar con:  sqlite3 foodstore_movil.db < semaforo.sql
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1) Solicitudes PENDIENTE sin items: no hay nada que comparar.
-- ----------------------------------------------------------------------------
UPDATE cola_sync
SET estado      = 'RECHAZADO',
    motivo      = 'SIN_ITEMS',
    evaluado_en = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE estado = 'PENDIENTE'
  AND NOT EXISTS (
        SELECT 1 FROM item_borrador i WHERE i.id_local = cola_sync.id_local
      );

-- ----------------------------------------------------------------------------
-- 2) Evaluacion del semaforo.
--    Se cuentan por solicitud los items de cada condicion y se decide con
--    prioridad rojo > amarillo > verde.
-- ----------------------------------------------------------------------------
WITH base AS (
    SELECT c.solicitud_uuid,
           COUNT(*) AS n_items,
           SUM(CASE WHEN s.producto_id IS NULL THEN 1 ELSE 0 END) AS n_inexistente,
           SUM(CASE WHEN s.producto_id IS NOT NULL AND s.eliminado = 1
                    THEN 1 ELSE 0 END) AS n_baja,
           SUM(CASE WHEN s.producto_id IS NOT NULL AND s.eliminado = 0
                         AND s.disponible = 0
                    THEN 1 ELSE 0 END) AS n_no_disponible,
           SUM(CASE WHEN s.producto_id IS NOT NULL AND s.eliminado = 0
                         AND s.disponible = 1 AND i.cantidad > s.stock_visto
                    THEN 1 ELSE 0 END) AS n_stock,
           SUM(CASE WHEN s.producto_id IS NOT NULL
                         AND i.precio_centavos_visto <> s.precio_centavos
                    THEN 1 ELSE 0 END) AS n_precio
    FROM cola_sync c
    JOIN item_borrador i       ON i.id_local = c.id_local
    LEFT JOIN snapshot_servidor s ON s.producto_id = i.producto_id
    WHERE c.estado = 'PENDIENTE'
    GROUP BY c.solicitud_uuid
),
evaluacion AS (
    SELECT solicitud_uuid,
           CASE
               WHEN n_inexistente   > 0 THEN 'RECHAZADO'
               WHEN n_baja          > 0 THEN 'RECHAZADO'
               WHEN n_no_disponible > 0 THEN 'RECHAZADO'
               WHEN n_stock         > 0 THEN 'RECHAZADO'
               WHEN n_precio        > 0 THEN 'CONFLICTO'
               ELSE 'SIMULADO_APROBADO'
           END AS nuevo_estado,
           CASE
               WHEN n_inexistente   > 0 THEN 'PRODUCTO_INEXISTENTE'
               WHEN n_baja          > 0 THEN 'PRODUCTO_DADO_DE_BAJA'
               WHEN n_no_disponible > 0 THEN 'PRODUCTO_NO_DISPONIBLE'
               WHEN n_stock         > 0 THEN 'STOCK_INSUFICIENTE'
               WHEN n_precio        > 0 THEN 'PRECIO_CAMBIADO'
               ELSE 'TODO_COINCIDE'
           END AS nuevo_motivo
    FROM base
)
UPDATE cola_sync
SET estado      = evaluacion.nuevo_estado,
    motivo      = evaluacion.nuevo_motivo,
    evaluado_en = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
FROM evaluacion
WHERE cola_sync.solicitud_uuid = evaluacion.solicitud_uuid
  AND cola_sync.estado = 'PENDIENTE';

-- ----------------------------------------------------------------------------
-- 3) Resumen y detalle para la evidencia.
-- ----------------------------------------------------------------------------
SELECT 'semaforo_resumen' AS prueba, estado, motivo, count(*) AS solicitudes
FROM cola_sync
GROUP BY estado, motivo
ORDER BY estado, motivo;

SELECT 'semaforo_detalle' AS prueba,
       solicitud_uuid, id_local, estado, motivo, evaluado_en
FROM cola_sync
ORDER BY creado_en, solicitud_uuid;
