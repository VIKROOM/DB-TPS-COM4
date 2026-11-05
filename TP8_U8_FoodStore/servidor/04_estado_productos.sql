-- ============================================================================
-- TP8 · Unidad 8 · Consigna 2.c (contexto)
-- Estado de los productos del servidor antes/despues de la simulacion.
--
-- Es esperable que cambien precio (C2) y activo (C4): son las preparaciones
-- deliberadas de los casos. Lo que NO cambia es el stock ni la cantidad de
-- pedidos (ver 03_verificacion_postgres.sql).
-- ============================================================================

\echo '=== ESTADO DE PRODUCTOS EN EL SERVIDOR ==='

SELECT id, nombre, precio, stock, activo
FROM producto
ORDER BY id;
