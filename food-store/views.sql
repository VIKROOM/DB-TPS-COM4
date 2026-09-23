-- ============================================================================
-- Food Store — views.sql (Parte B) · Unidad 3 · Semana 1
-- Vistas generadas por OpenCode a partir de los specs en specs/.
-- Verificacion de equivalencia en 06_verificacion_vistas.sql.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- V1 · Productos vigentes con su categoria (cartilla/menu)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_productos_vigentes AS
SELECT pr.id,
       pr.nombre,
       pr.precio,
       pr.stock,
       cat.nombre AS categoria
FROM   producto  pr
JOIN   categoria cat ON cat.id = pr.categoria_id
WHERE  pr.activo = TRUE
  AND  cat.activo = TRUE;

-- ----------------------------------------------------------------------------
-- V2 · Pedidos con datos del cliente (SIN datos de contacto: aplica el
--      criterio de seguridad/ocultamiento del enunciado, adaptado al esquema
--      real donde el comprador es la tabla cliente)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_pedidos_cliente AS
SELECT p.id          AS pedido_id,
       p.fecha,
       p.forma_pago,
       c.id          AS cliente_id,
       c.nombre      AS nombre_cliente,
       c.apellido    AS apellido_cliente
FROM   pedido  p
JOIN   cliente c ON c.id = p.cliente_id
WHERE  c.activo = TRUE;

-- ----------------------------------------------------------------------------
-- V3 · Detalle de pedido con el nombre del producto (ticket de venta)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_detalle_pedido_producto AS
SELECT p.id               AS pedido_id,
       p.fecha,
       pr.nombre          AS producto,
       lp.cantidad,
       lp.precio_unitario,
       lp.cantidad * lp.precio_unitario AS subtotal
FROM   linea_pedido lp
JOIN   pedido      p  ON p.id  = lp.pedido_id
JOIN   producto    pr ON pr.id = lp.producto_id;

-- ----------------------------------------------------------------------------
-- Parte C · Vista materializada de facturacion por categoria y mes
--   Con indice unico (mes, categoria) que habilita REFRESH CONCURRENTLY.
-- ----------------------------------------------------------------------------
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

CREATE UNIQUE INDEX mv_facturacion_cat_mes_uniq
    ON mv_facturacion_categoria_mes (mes, categoria);