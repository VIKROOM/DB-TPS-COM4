-- TP3 Parte 2 - Planes ANTES de optimizar (foodstore_tp3, base masiva)
\pset footer off

-- Q1: Cartilla/menu - productos vigentes de una categoria con rango de precio
-- (consigna comun de la competencia: listado por categoria + precio + orden)
EXPLAIN ANALYZE
SELECT nombre, precio FROM producto
WHERE categoria_id = 1 AND activo = TRUE
  AND precio BETWEEN 500 AND 1200
ORDER BY precio
LIMIT 20;

-- Q2: Busqueda de producto por nombre parcial
EXPLAIN ANALYZE
SELECT id, nombre, precio FROM producto
WHERE nombre ILIKE '%bebida 500%' AND activo = TRUE;

-- Q3: Conteo de pedidos de enero 2025 (filtro no sargable en fecha)
EXPLAIN ANALYZE
SELECT COUNT(*) FROM pedido
WHERE EXTRACT(MONTH FROM fecha) = 1 AND EXTRACT(YEAR FROM fecha) = 2025;