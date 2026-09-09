-- TP3 Parte 2 - Cambios propuestos por IA (revisados línea a línea) - foodstore_tp3

-- Q1: menú por categoría + orden por precio + vigentes.
--     Ataca el nodo Sort + el Recheck del Bitmap Heap Scan: un índice
--     compuesto (categoria_id, precio) parcial sobre filas vigentes devuelve
--     las filas ya ordenadas y sin filtrar en la tabla.
CREATE INDEX idx_producto_categoria_precio_vig
    ON producto (categoria_id, precio)
    WHERE activo = TRUE;

-- Q2: búsqueda parcial de nombre ('%...%').
--     Un índice btree no resuelve LIKE '%x%'; se usa pg_trgm (GIN).
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX idx_producto_nombre_trgm
    ON producto USING gin (nombre gin_trgm_ops)
    WHERE activo = TRUE;

-- Q3: filtra por EXTRACT(MONTH/YEAR) que NO puede usar el índice en fecha.
--     Reescritura a rango equivalente (sargable) que sí usa idx_pedido_fecha.
--     (No se crea índice: se reutiliza el existente.)