-- TP3 Parte 2 - Planes DESPUES de optimizar (foodstore_tp3)
\pset footer off

-- Q1: misma consulta (ahora con idx_producto_categoria_precio_vig)
EXPLAIN ANALYZE
SELECT nombre, precio FROM producto
WHERE categoria_id = 1 AND activo = TRUE
  AND precio BETWEEN 500 AND 1200
ORDER BY precio
LIMIT 20;

-- Q2: misma consulta (ahora con idx_producto_nombre_trgm)
EXPLAIN ANALYZE
SELECT id, nombre, precio FROM producto
WHERE nombre ILIKE '%bebida 500%' AND activo = TRUE;

-- Q3: reescritura sargable equivalente (pedidos de enero 2025)
EXPLAIN ANALYZE
SELECT COUNT(*) FROM pedido
WHERE fecha >= '2025-01-01' AND fecha < '2025-02-01';