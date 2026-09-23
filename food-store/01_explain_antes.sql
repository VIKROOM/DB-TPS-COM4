-- ============================================================================
-- Mediciones ANTES de crear los nuevos indices (Parte A, paso 4)
-- Base: foodstore_u3 | Protocolo: EXPLAIN (ANALYZE, BUFFERS), 2 corridas,
-- se conserva la segunda (caché caliente). Con \timing para el tiempo real.
-- ============================================================================
\timing on
\pset footer off

-- Q1 · Ranking de clientes por gasto (agrega toda linea_pedido)
EXPLAIN (ANALYZE, BUFFERS)
SELECT c.id, c.nombre, c.apellido,
       SUM(lp.cantidad * lp.precio_unitario) AS gasto,
       RANK() OVER (ORDER BY SUM(lp.cantidad * lp.precio_unitario) DESC) AS puesto
FROM   cliente c
JOIN   pedido p        ON p.cliente_id = c.id
JOIN   linea_pedido lp ON lp.pedido_id = p.id
WHERE  c.activo = TRUE
GROUP  BY c.id, c.nombre, c.apellido
ORDER  BY puesto, c.id;

-- Q2 · Total por pedido de un cliente: cliente con mayor volumen de pedidos
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.fecha,
       SUM(lp.cantidad * lp.precio_unitario) AS total
FROM   pedido p
JOIN   linea_pedido lp ON lp.pedido_id = p.id
WHERE  p.cliente_id = (SELECT cliente_id FROM pedido GROUP BY cliente_id ORDER BY count(*) DESC LIMIT 1)
GROUP  BY p.id, p.fecha
ORDER  BY p.fecha, p.id;

-- Q3 · Detalle de pedido con producto (pedido grande)
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id AS pedido_id, p.fecha, pr.nombre AS producto,
       lp.cantidad, lp.precio_unitario,
       lp.cantidad * lp.precio_unitario AS subtotal
FROM   linea_pedido lp
JOIN   pedido   p  ON p.id  = lp.pedido_id
JOIN   producto pr ON pr.id = lp.producto_id
WHERE  p.id = (SELECT pedido_id FROM linea_pedido GROUP BY pedido_id ORDER BY count(*) DESC LIMIT 1)
ORDER  BY pr.nombre;

-- Q4 · Productos vigentes de una categoria (menu/cartilla)
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.nombre, p.precio, p.stock
FROM   producto p
WHERE  p.categoria_id = 1
  AND  p.activo = TRUE
ORDER  BY p.precio;

-- Q5 · Top 100 pedidos recientes con cliente y total
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.fecha,
       c.nombre || ' ' || c.apellido AS cliente,
       SUM(lp.cantidad * lp.precio_unitario) AS total
FROM   pedido p
JOIN   cliente c ON c.id = p.cliente_id
JOIN   linea_pedido lp ON lp.pedido_id = p.id
GROUP  BY p.id, p.fecha, c.nombre, c.apellido
ORDER  BY p.fecha DESC
LIMIT  100;