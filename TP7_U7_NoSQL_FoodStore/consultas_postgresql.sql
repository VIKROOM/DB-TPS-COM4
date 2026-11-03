-- ============================================================================
-- TP Unidad 7 - Food Store NoSQL
-- Consultas PostgreSQL equivalentes (consigna 5) y comprobaciones de origen.
--
-- Uso (desde la raiz de TP7_U7_NoSQL_FoodStore):
--   psql -U postgres -h localhost -d foodstore -v ON_ERROR_STOP=1 ^
--        -f consultas_postgresql.sql
--
-- Se trabaja sobre el mismo subconjunto migrado: pedido.id BETWEEN 1 AND 12.
-- La regla de estado es identica a la usada en la extraccion:
--   fecha_corte = max(fecha del lote) + 1 dia
--   TERMINADO   si fecha <= fecha_corte - 30 dias
--   PENDIENTE   en caso contrario
-- ============================================================================

\pset border 2
\pset pager off
\encoding UTF8

\echo ''
\echo '=== Contexto del subconjunto (origen) ==='
SELECT count(*)                        AS pedidos,
       count(DISTINCT p.cliente_id)    AS clientes,
       (SELECT count(*) FROM linea_pedido WHERE pedido_id BETWEEN 1 AND 12) AS lineas,
       min(p.fecha)::date              AS fecha_min,
       max(p.fecha)::date              AS fecha_max
FROM pedido p
WHERE p.id BETWEEN 1 AND 12;

-- ----------------------------------------------------------------------------
-- 5.b) Equivalente a la consulta MongoDB por estado.
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== 5.b) Pedidos con estado TERMINADO (equivalente PostgreSQL) ==='
WITH corte AS (
    SELECT max(fecha) + interval '1 day' AS fecha_corte
    FROM pedido
    WHERE id BETWEEN 1 AND 12
),
lote AS (
    SELECT p.id,
           p.fecha,
           p.forma_pago,
           CASE
               WHEN p.fecha <= c.fecha_corte - interval '30 days' THEN 'TERMINADO'
               ELSE 'PENDIENTE'
           END AS estado
    FROM pedido p
    CROSS JOIN corte c
    WHERE p.id BETWEEN 1 AND 12
)
SELECT id AS pedido_id, estado
FROM lote
WHERE estado = 'TERMINADO'
ORDER BY id;

\echo ''
\echo '--- IDs TERMINADO (formato comparable con MongoDB) ---'
WITH corte AS (
    SELECT max(fecha) + interval '1 day' AS fecha_corte
    FROM pedido WHERE id BETWEEN 1 AND 12
)
SELECT count(*)                                   AS cantidad,
       string_agg(p.id::text, ',' ORDER BY p.id)  AS ids
FROM pedido p
CROSS JOIN corte c
WHERE p.id BETWEEN 1 AND 12
  AND p.fecha <= c.fecha_corte - interval '30 days';

-- ----------------------------------------------------------------------------
-- 5.c) Equivalente a la consulta MongoDB por producto dentro de las lineas.
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== 5.c) Pedidos que contienen el producto 1 (Muzzarella) ==='
SELECT DISTINCT p.id AS pedido_id
FROM pedido p
JOIN linea_pedido lp ON lp.pedido_id = p.id
WHERE p.id BETWEEN 1 AND 12
  AND lp.producto_id = 1
ORDER BY p.id;

\echo ''
\echo '--- IDs producto 1 (formato comparable con MongoDB) ---'
SELECT count(*)                                 AS cantidad,
       string_agg(id::text, ',' ORDER BY id)     AS ids
FROM (
    SELECT DISTINCT p.id
    FROM pedido p
    JOIN linea_pedido lp ON lp.pedido_id = p.id
    WHERE p.id BETWEEN 1 AND 12
      AND lp.producto_id = 1
) s;

-- ----------------------------------------------------------------------------
-- Tabla de verificacion del lado PostgreSQL (la comparacion final con
-- MongoDB se arma en el informe y la valida verificar_entrega.ps1).
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== Tabla de verificacion PostgreSQL ==='
WITH corte AS (
    SELECT max(fecha) + interval '1 day' AS fecha_corte
    FROM pedido WHERE id BETWEEN 1 AND 12
),
lote AS (
    SELECT p.id,
           CASE
               WHEN p.fecha <= c.fecha_corte - interval '30 days' THEN 'TERMINADO'
               ELSE 'PENDIENTE'
           END AS estado
    FROM pedido p
    CROSS JOIN corte c
    WHERE p.id BETWEEN 1 AND 12
),
totales AS (
    SELECT lp.pedido_id, sum(lp.cantidad * lp.precio_unitario) AS total
    FROM linea_pedido lp
    WHERE lp.pedido_id BETWEEN 1 AND 12
    GROUP BY lp.pedido_id
)
SELECT 'b) estado TERMINADO' AS consulta,
       count(*)                            AS cantidad,
       string_agg(l.id::text, ',' ORDER BY l.id) AS ids,
       sum(t.total)                        AS importe
FROM lote l
JOIN totales t ON t.pedido_id = l.id
WHERE l.estado = 'TERMINADO'
UNION ALL
SELECT 'c) producto 1',
       count(*),
       string_agg(id::text, ',' ORDER BY id),
       sum(total)
FROM (
    SELECT DISTINCT l.id, t.total
    FROM lote l
    JOIN linea_pedido lp ON lp.pedido_id = l.id
    JOIN totales t       ON t.pedido_id = l.id
    WHERE lp.producto_id = 1
) s;

-- ----------------------------------------------------------------------------
-- Comprobaciones de integridad del origen que deben conservarse al migrar.
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== Integridad 1: no hay lineas huerfanas (producto inexistente) ==='
SELECT count(*) AS lineas_huerfanas
FROM linea_pedido lp
WHERE lp.pedido_id BETWEEN 1 AND 12
  AND NOT EXISTS (SELECT 1 FROM producto pr WHERE pr.id = lp.producto_id);

\echo ''
\echo '=== Integridad 2: cantidades positivas e importes no negativos ==='
SELECT count(*) AS lineas_invalidas
FROM linea_pedido
WHERE pedido_id BETWEEN 1 AND 12
  AND (cantidad <= 0 OR precio_unitario < 0);

\echo ''
\echo '=== Integridad 3: precio historico vs precio actual del catalogo ==='
-- Demuestra que precio_unitario es una instantanea: si cambiara el catalogo,
-- los pedidos ya cerrados no deben modificarse.
SELECT count(*) FILTER (WHERE lp.precio_unitario <> pr.precio) AS lineas_con_precio_historico_distinto,
       count(*)                                               AS lineas_totales
FROM linea_pedido lp
JOIN producto pr ON pr.id = lp.producto_id
WHERE lp.pedido_id BETWEEN 1 AND 12;

\echo ''
\echo '=== Integridad 4: total por pedido calculado desde las lineas ==='
SELECT lp.pedido_id,
       count(*)                                AS lineas,
       sum(lp.cantidad)                        AS unidades,
       sum(lp.cantidad * lp.precio_unitario)   AS total
FROM linea_pedido lp
WHERE lp.pedido_id BETWEEN 1 AND 12
GROUP BY lp.pedido_id
ORDER BY lp.pedido_id;

\echo ''
\echo '=== c) Productos distintos referenciados en el lote (IDs para cruzar) ==='
SELECT string_agg(producto_id::text, ',' ORDER BY producto_id) AS producto_ids
FROM (
    SELECT DISTINCT lp.producto_id
    FROM linea_pedido lp
    WHERE lp.pedido_id BETWEEN 1 AND 12
) s;
