-- ============================================================================
-- TP3 · Parte 2 — Laboratorio: consultas lentas sobre la base masiva
-- Base: foodstore_tp3 · Motor: PostgreSQL 17.10
-- ============================================================================
-- Nota: la consigna pide elegir consultas de queries.sql; ese archivo no forma
-- parte del material disponible en este entorno, por lo que se usan "variantes
-- propias sobre el modelo" (explícitamente permitido por la consigna), que
-- reproducen los dos ejemplos que la propia guía menciona —"listado de
-- productos por categoría" e "historial de pedidos por usuario sin índice"—
-- más una agregación grande sobre detalle_pedido.
--
-- Estado inicial: la copia foodstore_tp3 solo tiene los índices de PK/UNIQUE
-- del esquema original (verificado con \di antes de empezar). Todas las
-- consultas incluyen el filtro de borrado lógico (eliminado = FALSE).
-- Protocolo de medición: cada EXPLAIN (ANALYZE, BUFFERS) se corre DOS veces y
-- se guarda la segunda (caché caliente), para que la comparación antes/después
-- no dependa de la primera lectura fría de disco.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- C1 · Listado de productos vigentes de una categoría, ordenados por precio
--      (consulta típica del menú/cartilla). Devuelve ~8.335 filas de 50.003.
-- ----------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.nombre, p.precio, p.stock
FROM producto p
WHERE p.categoria_id = 2          -- Pizzas
  AND p.eliminado = FALSE
ORDER BY p.precio;

-- ----------------------------------------------------------------------------
-- C2 · Historial de pedidos de un usuario vigente, más recientes primero
--      (pantalla "mis pedidos"). Devuelve ~10 filas sobre 200.001.
-- ----------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
SELECT pe.id, pe.fecha, pe.estado, pe.forma_pago
FROM pedido pe
WHERE pe.usuario_id = 1000
  AND pe.eliminado = FALSE
ORDER BY pe.fecha DESC;

-- ----------------------------------------------------------------------------
-- C3 · Top 10 de productos más vendidos (reporte gerencial).
--      Agregación completa sobre ~500.365 líneas de detalle_pedido.
-- ----------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
SELECT d.producto_id, SUM(d.cantidad) AS unidades_vendidas
FROM detalle_pedido d
GROUP BY d.producto_id
ORDER BY unidades_vendidas DESC
LIMIT 10;
