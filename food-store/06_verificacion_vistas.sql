-- ============================================================================
-- Verificacion de equivalencia vista vs. consulta manual (Parte B, paso 3)
-- Para cada vista: ambas direcciones del EXCEPT deben dar 0 filas.
-- ============================================================================
\pset footer off

-- V1 · v_productos_vigentes vs. consulta manual
SELECT count(*) AS dif_v1_vista_menos_manual FROM (
  ( SELECT pr.id, pr.nombre, pr.precio, pr.stock, cat.nombre AS categoria
    FROM   producto pr JOIN categoria cat ON cat.id = pr.categoria_id
    WHERE  pr.activo = TRUE AND cat.activo = TRUE )
  EXCEPT
  ( SELECT * FROM v_productos_vigentes )
) d;

SELECT count(*) AS dif_v1_manual_menos_vista FROM (
  ( SELECT * FROM v_productos_vigentes )
  EXCEPT
  ( SELECT pr.id, pr.nombre, pr.precio, pr.stock, cat.nombre AS categoria
    FROM   producto pr JOIN categoria cat ON cat.id = pr.categoria_id
    WHERE  pr.activo = TRUE AND cat.activo = TRUE )
) d;

-- V2 · v_pedidos_cliente vs. consulta manual (incluye columnas ocultas a la vista)
SELECT count(*) AS dif_v2_vista_menos_manual FROM (
  ( SELECT p.id, p.fecha, p.forma_pago, c.id, c.nombre, c.apellido
    FROM   pedido p JOIN cliente c ON c.id = p.cliente_id
    WHERE  c.activo = TRUE )
  EXCEPT
  ( SELECT * FROM v_pedidos_cliente )
) d;

SELECT count(*) AS dif_v2_manual_menos_vista FROM (
  ( SELECT * FROM v_pedidos_cliente )
  EXCEPT
  ( SELECT p.id, p.fecha, p.forma_pago, c.id, c.nombre, c.apellido
    FROM   pedido p JOIN cliente c ON c.id = p.cliente_id
    WHERE  c.activo = TRUE )
) d;

-- V3 · v_detalle_pedido_producto vs. consulta manual
SELECT count(*) AS dif_v3_vista_menos_manual FROM (
  ( SELECT p.id, p.fecha, pr.nombre, lp.cantidad, lp.precio_unitario,
           lp.cantidad * lp.precio_unitario
    FROM   linea_pedido lp
    JOIN   pedido   p  ON p.id  = lp.pedido_id
    JOIN   producto pr ON pr.id = lp.producto_id )
  EXCEPT
  ( SELECT * FROM v_detalle_pedido_producto )
) d;

SELECT count(*) AS dif_v3_manual_menos_vista FROM (
  ( SELECT * FROM v_detalle_pedido_producto )
  EXCEPT
  ( SELECT p.id, p.fecha, pr.nombre, lp.cantidad, lp.precio_unitario,
           lp.cantidad * lp.precio_unitario
    FROM   linea_pedido lp
    JOIN   pedido   p  ON p.id  = lp.pedido_id
    JOIN   producto pr ON pr.id = lp.producto_id )
) d;

-- Prueba de seguridad: la vista NO debe exponer email/telefono del cliente
SELECT count(*) AS columnas_sensibles_expuestas
FROM   information_schema.columns
WHERE  table_name = 'v_pedidos_cliente'
  AND  column_name IN ('email', 'telefono');