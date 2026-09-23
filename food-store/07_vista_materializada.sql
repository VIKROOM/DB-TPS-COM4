-- ============================================================================
-- Vista materializada (Parte C) · Facturacion por categoria y mes
-- 1) Medir la consulta original SIN materializar (Q6).
-- 2) Crear la vista materializada con WITH DATA e indice unico.
-- 3) Medir la consulta contra la materializada (misma fecha de corte).
-- ============================================================================
\timing on
\pset footer off

-- Paso 1 · consulta original (reporte agregado costoso, ~400k lineas)
EXPLAIN (ANALYZE, BUFFERS)
SELECT cat.nombre                     AS categoria,
       date_trunc('month', p.fecha)   AS mes,
       SUM(lp.cantidad * lp.precio_unitario) AS facturado
FROM   linea_pedido lp
JOIN   pedido       p   ON p.id   = lp.pedido_id
JOIN   producto     pr  ON pr.id  = lp.producto_id
JOIN   categoria    cat ON cat.id = pr.categoria_id
GROUP  BY cat.nombre, date_trunc('month', p.fecha)
ORDER  BY mes, categoria;

-- Paso 2 · crear la materializada CON DATOS (los datos deben estar listos al
--          momento de crear, porque el reporte se consume de inmediato)
CREATE MATERIALIZED VIEW mv_facturacion_categoria_mes AS
SELECT cat.nombre                     AS categoria,
       date_trunc('month', p.fecha)   AS mes,
       SUM(lp.cantidad * lp.precio_unitario) AS facturado
FROM   linea_pedido lp
JOIN   pedido       p   ON p.id   = lp.pedido_id
JOIN   producto     pr  ON pr.id  = lp.producto_id
JOIN   categoria    cat ON cat.id = pr.categoria_id
GROUP  BY cat.nombre, date_trunc('month', p.fecha)
ORDER  BY mes, categoria
WITH DATA;

-- Indice unico: imprescindible para poder usar REFRESH CONCURRENTLY despues
CREATE UNIQUE INDEX mv_facturacion_cat_mes_uniq
    ON mv_facturacion_categoria_mes (mes, categoria);

-- Paso 3 · medir la consulta contra la materializada
EXPLAIN (ANALYZE, BUFFERS)
SELECT categoria, mes, facturado
FROM   mv_facturacion_categoria_mes
ORDER  BY mes, categoria;