-- ============================================================================
-- TP8 · Unidad 8 · Consigna 2.a
-- Importa la instantanea del servidor (CSV exportado desde PostgreSQL) en
-- SQLite y refresca producto_cache.
--
-- Pensado para el cliente sqlite3 (usa el meta-comando .import).
-- Alternativa reproducible en Python: movil/importar_snapshot.py
--
-- Ejecutar desde la carpeta movil/:
--   sqlite3 foodstore_movil.db < importar_snapshot.sql
--
-- El CSV lo genera PostgreSQL con:
--   \copy (SELECT * FROM v_snapshot_movil) TO 'servidor_snapshot.csv' CSV HEADER
-- En ese CSV los booleanos llegan como 't' / 'f'.
-- ============================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS snapshot_servidor;
CREATE TABLE snapshot_servidor (
    producto_id     INTEGER,
    nombre          TEXT,
    precio_centavos INTEGER,
    stock_visto     INTEGER,
    disponible      INTEGER,   -- llega como 't' / 'f'; se normaliza abajo
    eliminado       INTEGER,   -- llega como 't' / 'f'; se normaliza abajo
    fecha_copia     TEXT
);

.mode csv
.import --csv --skip 1 servidor_snapshot.csv snapshot_servidor

-- psql exporta los booleanos como 't' / 'f': se normalizan a 0/1.
UPDATE snapshot_servidor
SET disponible = CASE lower(trim(disponible))
                     WHEN 't' THEN 1 WHEN 'true' THEN 1 WHEN '1' THEN 1 ELSE 0 END,
    eliminado  = CASE lower(trim(eliminado))
                     WHEN 't' THEN 1 WHEN 'true' THEN 1 WHEN '1' THEN 1 ELSE 0 END;

-- Refresco del cache local. Es un UPSERT: las filas que ya no vienen en la
-- instantanea no se borran (asi el borrador viejo conserva su referencia y
-- la lapida 'eliminado' se actualiza).
INSERT INTO producto_cache (id, nombre, precio_centavos, stock_visto, disponible, eliminado, fecha_copia)
SELECT producto_id,
       nombre,
       precio_centavos,
       stock_visto,
       CASE lower(trim(disponible))
            WHEN 't' THEN 1 WHEN 'true' THEN 1 WHEN '1' THEN 1 ELSE 0 END,
       CASE lower(trim(eliminado))
            WHEN 't' THEN 1 WHEN 'true' THEN 1 WHEN '1' THEN 1 ELSE 0 END,
       fecha_copia
FROM snapshot_servidor
WHERE 1
ON CONFLICT(id) DO UPDATE SET
    nombre          = excluded.nombre,
    precio_centavos = excluded.precio_centavos,
    stock_visto     = excluded.stock_visto,
    disponible      = excluded.disponible,
    eliminado       = excluded.eliminado,
    fecha_copia     = excluded.fecha_copia;

-- Evidencia de la importacion.
SELECT 'snapshot_importado' AS prueba,
       count(*) AS filas,
       min(fecha_copia) AS fecha_copia
FROM snapshot_servidor;

SELECT 'producto_cache' AS tabla,
       count(*) AS filas,
       sum(disponible) AS disponibles,
       sum(eliminado)  AS eliminados
FROM producto_cache;
