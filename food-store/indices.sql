-- ============================================================================
-- Food Store — indices.sql (Parte A) · Unidad 3 · Semana 1
-- Indices propuestos por la IA (OpenCode) a partir de los specs en specs/,
-- revisados linea por linea y verificados con EXPLAIN ANALYZE antes/despues.
-- Base de trabajo: foodstore_u3 · Motor: PostgreSQL 17+
--
-- Los tres indices aceptados parten de consultas que HOY resuelven con
-- Seq Scan sobre tablas de tamaño considerable (documentado en
-- informe_mediciones.md y en los planes de planes/).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- I1 · Linea de producto -> ventas de un producto (historial)
-- Spec : specs/spec_indice_linea_pedido_producto.md
-- Antes: Parallel Seq Scan on linea_pedido (~400k filas) — 36.6 ms
-- Tipo : btree con INCLUDE (index-only scan) sobre la FK mas utilizada.
-- ----------------------------------------------------------------------------
CREATE INDEX idx_linea_pedido_producto
    ON linea_pedido (producto_id)
    INCLUDE (cantidad, precio_unitario);

-- ----------------------------------------------------------------------------
-- I2 · Busqueda por nombre del producto (menu) — indice trigram
-- Spec : specs/spec_busqueda_nombre_producto.md
-- Antes: Seq Scan on producto (50k) — 31.6 ms
-- Tipo : GIN trigram (pg_trgm), parcial (solo vigentes).
-- ----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX idx_producto_nombre_trgm
    ON producto USING gin (nombre gin_trgm_ops)
    WHERE activo = TRUE;

-- ----------------------------------------------------------------------------
-- I3 · Reposicion de stock — indice parcial
-- Spec : specs/spec_indice_producto_stock_parcial.md
-- Antes: Seq Scan on producto (50k) — 7.0 ms
-- Tipo : btree parcial sobre stock, condicion de vigencia (baja logica).
-- ----------------------------------------------------------------------------
CREATE INDEX idx_producto_stock_parcial
    ON producto (stock)
    WHERE activo = TRUE AND stock <= 10;

-- ----------------------------------------------------------------------------
-- INDICES DESCARTADOS (sobreindexacion) — ver informe_mediciones.md
--
-- D1 · idx_pedido_forma_pago ON pedido (forma_pago)
--      Propuesto por la IA para el reporte de cobranza por medio de pago.
--      DESCARTADO: forma_pago es un ENUM de 3 valores (baja cardinalidad)
--      sin condicion parcial; un Indice no puede reducir las filas a leer de
--      forma significativa (cada valor representa ~1/3 de los 200k pedidos) y
--      agregaria costo de mantenimiento en cada INSERT sin ganancia real.
--      Verificado: EXPLAIN no mejoraba el plan frente al Seq Scan barato.
--
-- D2 · idx_producto_categoria_dup ON producto (categoria_id, nombre)
--      Propuesto como "indice compuesto" para la cartilla.
--      DESCARTADO: ya existe la restriccion UNIQUE (categoria_id, nombre)
--      que crea ese mismo indice como soporte (constraint), y tambien
--      idx_producto_categoria. Seria un objeto duplicado sin aporte.
-- ============================================================================