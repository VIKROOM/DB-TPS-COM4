-- TP4 Parte 4 - Consulta comun de la competencia (foodstore_tp3)
-- Mide antes/despues del unico cambio propuesto (indice idx_linea_pedido_producto).

SELECT ca.nombre AS categoria,
       ROUND(SUM(lp.cantidad * lp.precio_unitario)::numeric, 2) AS facturacion
FROM   linea_pedido lp
JOIN   producto   pr ON pr.id = lp.producto_id
JOIN   categoria  ca ON ca.id = pr.categoria_id
WHERE  ca.activo = TRUE AND pr.activo = TRUE
GROUP  BY ca.nombre
ORDER  BY facturacion DESC
LIMIT  10;