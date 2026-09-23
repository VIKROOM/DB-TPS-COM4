-- Diagnostico de consultas frecuentes con Seq Scan (confirmacion de candidatos)
\timing on
\pset footer off

-- Ctest1 · Ventas de un producto (historial) — filtra linea_pedido.producto_id
--          (~400k filas, sin indice en linea_pedido.producto_id en schema.sql)
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.fecha, lp.cantidad, lp.precio_unitario,
       lp.cantidad * lp.precio_unitario AS subtotal
FROM   linea_pedido lp
JOIN   pedido p ON p.id = lp.pedido_id
WHERE  lp.producto_id = 100
ORDER  BY p.fecha DESC
LIMIT  50;

-- Ctest2 · Reposicion de stock — filtra producto.stock (sin indice)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, nombre, stock
FROM   producto
WHERE  stock <= 10
  AND  activo = TRUE
ORDER  BY stock;

-- Ctest3 · Pedidos de un cliente por ventana de fechas (idx_pedido_cliente + fecha)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, fecha, forma_pago
FROM   pedido
WHERE  cliente_id = 1000
  AND  fecha BETWEEN '2025-01-01' AND '2025-06-01'
ORDER  BY fecha DESC;