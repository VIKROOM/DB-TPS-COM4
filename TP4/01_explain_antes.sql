-- TP4 Parte 1 - Planes ANTES de optimizar (foodstore_tp3)
\pset footer off

-- QA: Ventas de un producto (historial) - cruza linea_pedido + pedido + producto
EXPLAIN ANALYZE
SELECT p.id, p.fecha, pr.nombre AS producto,
       lp.cantidad, lp.cantidad * lp.precio_unitario AS subtotal
FROM   linea_pedido lp
JOIN   pedido   p  ON p.id  = lp.pedido_id
JOIN   producto pr ON pr.id = lp.producto_id
WHERE  lp.producto_id = 100
ORDER  BY p.fecha DESC
LIMIT  50;

-- QB: Top 100 pedidos recientes con cliente y total - cruza pedido + cliente + linea_pedido
EXPLAIN ANALYZE
SELECT p.id, p.fecha,
       c.nombre || ' ' || c.apellido AS cliente,
       SUM(lp.cantidad * lp.precio_unitario) AS total
FROM   pedido p
JOIN   cliente c ON c.id = p.cliente_id
JOIN   linea_pedido lp ON lp.pedido_id = p.id
GROUP  BY p.id, p.fecha, c.nombre, c.apellido
ORDER  BY p.fecha DESC
LIMIT  100;