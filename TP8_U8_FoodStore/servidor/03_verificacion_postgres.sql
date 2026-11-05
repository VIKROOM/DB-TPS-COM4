-- ============================================================================
-- TP8 · Unidad 8 · Consigna 2.c (cierre)
-- INVARIANTES del servidor: se ejecuta antes y despues de toda la simulacion.
--
-- La cantidad de pedidos, de lineas y la suma de stock deben ser identicas:
-- la tablet solo simula, nunca confirma ventas ni descuenta stock.
-- (El precio o el flag activo pueden cambiar porque son la preparacion
--  deliberada de los casos C2 y C4; eso se muestra en 04_estado_productos.sql.)
-- ============================================================================

\echo '=== INVARIANTES POSTGRESQL ==='

SELECT 'pedido'       AS tabla, count(*) AS filas FROM pedido
UNION ALL SELECT 'linea_pedido', count(*) FROM linea_pedido
UNION ALL SELECT 'producto',     count(*) FROM producto
UNION ALL SELECT 'cliente',      count(*) FROM cliente
ORDER BY tabla;

SELECT 'suma_stock' AS metrica, sum(stock)::text AS valor FROM producto
UNION ALL
SELECT 'importe_lineas',
       to_char(sum(cantidad * precio_unitario), 'FM999999990.00')
FROM linea_pedido;
