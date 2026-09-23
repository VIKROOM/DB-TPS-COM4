-- ============================================================================
-- Food Store - queries.sql (heredado de Semanas 3 y 4, adaptadas al esquema
-- real del equipo: cliente/linea_pedido)
-- Es la fuente de la "carga de trabajo real" que se va a indexar en la
-- Parte A de la Unidad 3.
-- ============================================================================

-- Q1 · Ranking de clientes vigentes por gasto total (reporte gerencial,
--      analitica de la Semana 4). Cruza cliente + pedido + linea_pedido.
SELECT c.id, c.nombre, c.apellido,
       SUM(lp.cantidad * lp.precio_unitario) AS gasto,
       RANK() OVER (ORDER BY SUM(lp.cantidad * lp.precio_unitario) DESC) AS puesto
FROM   cliente c
JOIN   pedido p        ON p.cliente_id = c.id
JOIN   linea_pedido lp ON lp.pedido_id = p.id
WHERE  c.activo = TRUE
GROUP  BY c.id, c.nombre, c.apellido
ORDER  BY puesto, c.id;

-- Q2 · Total por pedido de un cliente (pantalla "mis pedidos").
SELECT p.id, p.fecha,
       SUM(lp.cantidad * lp.precio_unitario) AS total
FROM   pedido p
JOIN   linea_pedido lp ON lp.pedido_id = p.id
WHERE  p.cliente_id = :cliente_id
GROUP  BY p.id, p.fecha
ORDER  BY p.fecha, p.id;

-- Q3 · Detalle de pedido con producto (ticket de venta).
SELECT p.id AS pedido_id, p.fecha, pr.nombre AS producto,
       lp.cantidad, lp.precio_unitario,
       lp.cantidad * lp.precio_unitario AS subtotal
FROM   linea_pedido lp
JOIN   pedido   p  ON p.id  = lp.pedido_id
JOIN   producto pr ON pr.id = lp.producto_id
WHERE  p.id = :pedido_id
ORDER  BY pr.nombre;

-- Q4 · Productos vigentes de una categoria, por precio (menu/cartilla).
SELECT p.id, p.nombre, p.precio, p.stock
FROM   producto p
WHERE  p.categoria_id = :categoria_id
  AND  p.activo = TRUE
ORDER  BY p.precio;

-- Q5 · Top 100 pedidos recientes con cliente y total (home de admin).
SELECT p.id, p.fecha,
       c.nombre || ' ' || c.apellido AS cliente,
       SUM(lp.cantidad * lp.precio_unitario) AS total
FROM   pedido p
JOIN   cliente c ON c.id = p.cliente_id
JOIN   linea_pedido lp ON lp.pedido_id = p.id
GROUP  BY p.id, p.fecha, c.nombre, c.apellido
ORDER  BY p.fecha DESC
LIMIT  100;

-- Q6 · Facturacion por categoria y mes (reporte agregado costoso, Semana 4)
--      >> candidato a vista materializada en la Parte C.
SELECT cat.nombre                     AS categoria,
       date_trunc('month', p.fecha)   AS mes,
       SUM(lp.cantidad * lp.precio_unitario) AS facturado
FROM   linea_pedido lp
JOIN   pedido       p   ON p.id   = lp.pedido_id
JOIN   producto     pr  ON pr.id  = lp.producto_id
JOIN   categoria    cat ON cat.id = pr.categoria_id
GROUP  BY cat.nombre, date_trunc('month', p.fecha)
ORDER  BY mes, categoria;