-- ============================================================================
-- Mediciones DESPUES de crear los indices (Parte A, paso 4) — 2 corridas, warm
-- ============================================================================
\timing on
\pset footer off

-- D1 · Ventas de un producto (historial)
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.fecha, lp.cantidad, lp.precio_unitario,
       lp.cantidad * lp.precio_unitario AS subtotal
FROM   linea_pedido lp
JOIN   pedido p ON p.id = lp.pedido_id
WHERE  lp.producto_id = 100
ORDER  BY p.fecha DESC
LIMIT  50;

-- D2 · Busqueda por nombre (menu)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, nombre, precio FROM producto WHERE nombre ILIKE '%pizza 25000%' AND activo = TRUE;

-- D3 · Reposicion de stock
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, nombre, stock
FROM   producto
WHERE  stock <= 10
  AND  activo = TRUE
ORDER  BY stock;