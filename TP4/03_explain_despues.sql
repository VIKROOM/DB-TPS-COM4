-- TP4 Parte 1 - Planes DESPUES de optimizar (foodstore_tp3)
\pset footer off

-- QA: misma consulta (ahora con idx_linea_pedido_producto)
EXPLAIN ANALYZE
SELECT p.id, p.fecha, pr.nombre AS producto,
       lp.cantidad, lp.cantidad * lp.precio_unitario AS subtotal
FROM   linea_pedido lp
JOIN   pedido   p  ON p.id  = lp.pedido_id
JOIN   producto pr ON pr.id = lp.producto_id
WHERE  lp.producto_id = 100
ORDER  BY p.fecha DESC
LIMIT  50;

-- QB: reescritura equivalente (top 100 pedidos recientes con cliente y total)
EXPLAIN ANALYZE
SELECT t.id, t.fecha,
       c.nombre || ' ' || c.apellido AS cliente,
       SUM(lp.cantidad * lp.precio_unitario) AS total
FROM   (SELECT id, fecha, cliente_id FROM pedido
        ORDER BY fecha DESC, id DESC LIMIT 100) t
JOIN   cliente c ON c.id = t.cliente_id
JOIN   linea_pedido lp ON lp.pedido_id = t.id
GROUP  BY t.id, t.fecha, c.nombre, c.apellido
ORDER  BY t.fecha DESC, t.id DESC;