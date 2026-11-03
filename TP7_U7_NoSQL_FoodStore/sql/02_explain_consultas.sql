-- ============================================================================
-- TP Unidad 7 - Food Store NoSQL
-- Planes de ejecucion de las consultas equivalentes (consigna 5 y 7).
-- No se usa para afirmar superioridad de rendimiento: solo para documentar
-- cuantas filas/documentos examina cada motor con el mismo filtro.
--
-- Uso:
--   psql -U postgres -h localhost -d foodstore -f sql/02_explain_consultas.sql
-- ============================================================================

\pset pager off
\encoding UTF8

\echo ''
\echo '=== EXPLAIN b) pedidos TERMINADO (misma regla de estado) ==='
EXPLAIN (ANALYZE, BUFFERS)
WITH corte AS (
    SELECT max(fecha) + interval '1 day' AS fecha_corte
    FROM pedido WHERE id BETWEEN 1 AND 12
)
SELECT p.id
FROM pedido p
CROSS JOIN corte c
WHERE p.id BETWEEN 1 AND 12
  AND p.fecha <= c.fecha_corte - interval '30 days';

\echo ''
\echo '=== EXPLAIN c) pedidos que contienen el producto 1 ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT DISTINCT p.id
FROM pedido p
JOIN linea_pedido lp ON lp.pedido_id = p.id
WHERE p.id BETWEEN 1 AND 12
  AND lp.producto_id = 1;

\echo ''
\echo '=== Conteos de referencia para comparar con MongoDB ==='
SELECT 'b) TERMINADO' AS consulta, count(*) AS filas
FROM pedido p
CROSS JOIN (SELECT max(fecha) + interval '1 day' AS f FROM pedido WHERE id BETWEEN 1 AND 12) c
WHERE p.id BETWEEN 1 AND 12 AND p.fecha <= c.f - interval '30 days'
UNION ALL
SELECT 'c) producto 1', count(DISTINCT p.id)
FROM pedido p
JOIN linea_pedido lp ON lp.pedido_id = p.id
WHERE p.id BETWEEN 1 AND 12 AND lp.producto_id = 1;
