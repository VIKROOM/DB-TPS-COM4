-- ============================================================================
-- TP3 · Parte 2 — Índices propuestos por la IA (OpenCode), revisados línea a
-- línea por el estudiante y ACEPTADOS tras la verificación contra el plan real
-- Base: foodstore_tp3 (copia de trabajo) · Motor: PostgreSQL 17.10
-- Cada CREATE INDEX justifica qué nodo del plan "antes" ataca.
-- ============================================================================

\timing on

-- ----------------------------------------------------------------------------
-- I1 (para C1 y para la consulta de la Parte 5)
-- Plan antes: Seq Scan sobre producto (50.003 filas, ~4.400 buffers) + Sort
--   explícito de las ~8.335 filas que pasan el filtro.
-- Qué ataca:
--   * El filtro (categoria_id = 2 AND eliminado = FALSE) queda como Index Cond
--     de igualdad sobre las dos primeras columnas -> el motor llega directo a
--     las filas de la categoría sin recorrer la tabla.
--   * El ORDER BY precio queda cubierto por la tercera columna: dentro de
--     (categoria_id, eliminado) el índice ya está ordenado por precio, así que
--     el nodo Sort debería desaparecer del plan.
--     [VERIFICACIÓN REAL: el planner prefirió Bitmap Heap Scan + Sort (el
--     resultado es ~17% de la tabla; un Index Scan ordenado implicaría miles
--     de heap fetches aleatorios). La predicción del Sort NO se cumplió, pero
--     el índice se acepta igual: 10.486 -> 7.726 ms y buffers 1728 -> 904,
--     porque deja de leer las 41.668 filas de otras categorías. Ver
--     tabla_comparativa.md, "Análisis honesto de C1".]
-- Orden de columnas: igualdad, igualdad, orden/rango (regla estándar E-S-R).
-- ----------------------------------------------------------------------------
CREATE INDEX idx_producto_cat_elim_precio
    ON producto (categoria_id, eliminado, precio);

-- ----------------------------------------------------------------------------
-- I2 (para C2)
-- Plan antes: Seq Scan sobre pedido (200.001 filas) + Sort de las ~10 filas
--   del usuario. El costo dominante es leer la tabla entera para encontrar 10
--   filas.
-- Qué ataca:
--   * (usuario_id, eliminado) como Index Cond de igualdad -> acceso directo a
--     los pedidos del usuario vigente.
--   * fecha como tercera columna -> ORDER BY fecha DESC se resuelve leyendo el
--     índice hacia atrás (Backward Index Scan), sin nodo Sort.
-- ----------------------------------------------------------------------------
CREATE INDEX idx_pedido_usu_elim_fecha
    ON pedido (usuario_id, eliminado, fecha);

-- ----------------------------------------------------------------------------
-- I3 (para C3)
-- Plan antes: Seq Scan sobre detalle_pedido (~500.365 filas, todas sus
--   columnas) + HashAggregate.
-- Qué ataca: índice CUBRIENTE de la agregación: las únicas columnas que la
--   consulta toca (producto_id, cantidad) están en el índice, habilitando un
--   Index Only Scan que no visita el heap (si el visibility map está al día,
--   por eso se corrió VACUUM ANALYZE antes de medir) y que además entrega las
--   filas agrupadas/ordenadas por producto_id, permitiendo GroupAggregate en
--   lugar de HashAggregate.
-- ----------------------------------------------------------------------------
CREATE INDEX idx_detalle_cubriente
    ON detalle_pedido (producto_id, cantidad);

-- ----------------------------------------------------------------------------
-- PROPUESTAS DESCARTADAS (documentadas en tabla_comparativa.md y DUIA.md):
--   * CREATE INDEX ON producto (precio): descartada en la revisión — el filtro
--     selectivo es categoria_id (1/6 de la tabla); un índice solo de precio no
--     sirve a la igualdad y obligaría a recorrerlo entero + heap fetches.
--   * CREATE INDEX ON producto (categoria_id, eliminado, precio)
--     INCLUDE (nombre, stock): propuesta por la IA para hacer C1 "index only";
--     se midió en la Parte 5 y NO mejoró el tiempo real de forma relevante
--     (ver registro_competencia.md) -> se descartó: duplica casi el tamaño del
--     índice y penaliza cada INSERT/UPDATE de producto.
-- ----------------------------------------------------------------------------

-- Estadísticas al día tras crear los índices (el CREATE INDEX ya las usa, pero
-- se explicita ANALYZE para las mediciones "después").
ANALYZE producto;
ANALYZE pedido;
ANALYZE detalle_pedido;
