-- ============================================================================
-- TP3 · Parte 5 — Consulta común de la competencia (fijada por la cátedra)
-- "Listado de productos por categoría con filtro de precio y orden, sin índice"
-- Base masiva común: foodstore_tp3 (50.003 productos, 6 categorías)
-- ============================================================================

-- La consulta (idéntica para todos los equipos):
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.nombre, p.precio, p.stock
FROM producto p
WHERE p.categoria_id = 2              -- Pizzas
  AND p.eliminado = FALSE
  AND p.precio BETWEEN 1000 AND 3000  -- filtro de precio
ORDER BY p.precio DESC;               -- orden

-- Gana el mejor TIEMPO REAL (Execution Time de EXPLAIN ANALYZE), no el costo
-- estimado. Protocolo del equipo: 2 corridas por medición, se registra la
-- segunda (caché caliente); la medición "antes" se tomó con la base sin
-- índices propios (solo PK/UNIQUE del esquema), la medición "después" con el
-- índice idx_producto_cat_elim_precio aplicado (Parte 2, I1).
