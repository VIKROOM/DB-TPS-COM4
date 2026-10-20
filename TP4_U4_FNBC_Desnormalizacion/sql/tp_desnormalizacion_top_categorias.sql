-- ============================================================================
-- TP_U4_FNBC_Desnormalizacion_FoodStore - Parte 2
-- Archivo: tp_desnormalizacion_top_categorias.sql
-- ============================================================================

-- 5.1 Consulta original
-- SELECT c.nombre AS categoria, 
--        SUM(dp.subtotal) AS total_vendido 
-- FROM detalle_pedido dp 
-- JOIN producto pr ON pr.id = dp.producto_id 
-- JOIN categoria c ON c.id = pr.categoria_id 
-- JOIN pedido ped ON ped.id = dp.pedido_id 
-- WHERE ped.fecha = CURRENT_DATE 
--   AND dp.eliminado = FALSE 
--   AND ped.eliminado = FALSE 
-- GROUP BY c.nombre 
-- ORDER BY total_vendido DESC 
-- LIMIT 5;

-- 5.2(a) Medición antes (ejecutar sobre instancia razonablemente poblada)
-- EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
-- ... misma consulta ...

-- ============================================================================
-- 5.2(b),(c) Desnormalización controlada elegida: COLUMNA PRECALCULADA CON DISPARADOR
-- Justificación (resumida): evidencia de EXPLAIN ANALYZE (muchos JOIN + agrupación)
-- motiva precálculo; disparadores AFTER INSERT/UPDATE/DELETE sobre detalle_pedido
-- y/o cambios en pedido mantienen la redundancia sincronizada con fuente de verdad
-- (detalle_pedido.subtotal + pedido.fecha/estado/eliminado). Es reversible sin
-- pérdida (se puede recalcular con la consulta original).
-- ============================================================================

-- Tabla desnormalizada: ventas por categoría por día
DROP TABLE IF EXISTS ventas_categoria_dia CASCADE;

CREATE TABLE ventas_categoria_dia (
    fecha                DATE        NOT NULL,
    categoria_id         BIGINT      NOT NULL,
    categoria_nombre     VARCHAR(80) NOT NULL,
    total_vendido        NUMERIC(12,2) NOT NULL DEFAULT 0,
    cantidad_items       BIGINT      NOT NULL DEFAULT 0,
    cantidad_pedidos     BIGINT      NOT NULL DEFAULT 0,
    actualizado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (fecha, categoria_id)
);

CREATE INDEX IF NOT EXISTS idx_vcd_fecha_total ON ventas_categoria_dia(fecha, total_vendido DESC);

-- Función para recalcular un día/categoría desde fuente de verdad
CREATE OR REPLACE FUNCTION fn_recalcular_ventas_categoria_dia(p_fecha DATE, p_categoria_id BIGINT)
RETURNS void AS $$
DECLARE
    v_nombre VARCHAR(80);
    v_total  NUMERIC(12,2);
    v_items  BIGINT;
    v_ped    BIGINT;
BEGIN
    SELECT c.nombre INTO v_nombre FROM categoria c WHERE c.id = p_categoria_id;

    SELECT COALESCE(SUM(dp.subtotal),0), COALESCE(SUM(dp.cantidad),0), COUNT(DISTINCT dp.pedido_id)
      INTO v_total, v_items, v_ped
    FROM detalle_pedido dp
    JOIN producto pr ON pr.id = dp.producto_id
    JOIN pedido ped ON ped.id = dp.pedido_id
    WHERE ped.fecha = p_fecha
      AND pr.categoria_id = p_categoria_id
      AND dp.eliminado = FALSE
      AND ped.eliminado = FALSE;

    INSERT INTO ventas_categoria_dia(fecha, categoria_id, categoria_nombre, total_vendido, cantidad_items, cantidad_pedidos, actualizado_en)
    VALUES (p_fecha, p_categoria_id, COALESCE(v_nombre,''), v_total, v_items, v_ped, now())
    ON CONFLICT (fecha, categoria_id) DO UPDATE SET
        categoria_nombre = EXCLUDED.categoria_nombre,
        total_vendido    = EXCLUDED.total_vendido,
        cantidad_items   = EXCLUDED.cantidad_items,
        cantidad_pedidos = EXCLUDED.cantidad_pedidos,
        actualizado_en   = now();
END;
$$ LANGUAGE plpgsql;

-- Disparador: al cambiar detalle_pedido recalcula día/categoría afectada
CREATE OR REPLACE FUNCTION fn_trg_sync_ventas_categoria_dia()
RETURNS TRIGGER AS $$
DECLARE
    v_pedido_id BIGINT;
    v_fecha     DATE;
    v_cat       BIGINT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_pedido_id := OLD.pedido_id;
    ELSE
        v_pedido_id := NEW.pedido_id;
    END IF;

    SELECT ped.fecha INTO v_fecha FROM pedido ped WHERE ped.id = v_pedido_id;
    IF v_fecha IS NULL THEN
        RETURN COALESCE(NEW, OLD);
    END IF;

    -- obtener categorías afectadas (OLD y/o NEW)
    IF TG_OP = 'INSERT' THEN
        SELECT pr.categoria_id INTO v_cat FROM producto pr WHERE pr.id = NEW.producto_id;
        IF v_cat IS NOT NULL THEN PERFORM fn_recalcular_ventas_categoria_dia(v_fecha, v_cat); END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        -- si cambió producto/cantidad/subtotal/eliminado o pedido_id
        IF NEW.producto_id IS NOT NULL THEN
            SELECT pr.categoria_id INTO v_cat FROM producto pr WHERE pr.id = NEW.producto_id;
            IF v_cat IS NOT NULL THEN PERFORM fn_recalcular_ventas_categoria_dia(v_fecha, v_cat); END IF;
        END IF;
        IF OLD.producto_id IS DISTINCT FROM NEW.producto_id OR OLD.pedido_id IS DISTINCT FROM NEW.pedido_id THEN
            SELECT ped.fecha INTO v_fecha FROM pedido ped WHERE ped.id = OLD.pedido_id;
            IF v_fecha IS NOT NULL THEN
                SELECT pr.categoria_id INTO v_cat FROM producto pr WHERE pr.id = OLD.producto_id;
                IF v_cat IS NOT NULL THEN PERFORM fn_recalcular_ventas_categoria_dia(v_fecha, v_cat); END IF;
            END IF;
            SELECT ped.fecha INTO v_fecha FROM pedido ped WHERE ped.id = NEW.pedido_id;
            IF v_fecha IS NOT NULL THEN
                SELECT pr.categoria_id INTO v_cat FROM producto pr WHERE pr.id = NEW.producto_id;
                IF v_cat IS NOT NULL THEN PERFORM fn_recalcular_ventas_categoria_dia(v_fecha, v_cat); END IF;
            END IF;
            RETURN NEW;
        END IF;
        -- recalcular categoría original si cambió eliminado o montos pero mismo producto/pedido
        SELECT pr.categoria_id INTO v_cat FROM producto pr WHERE pr.id = OLD.producto_id;
        IF v_cat IS NOT NULL THEN PERFORM fn_recalcular_ventas_categoria_dia(v_fecha, v_cat); END IF;
    ELSIF TG_OP = 'DELETE' THEN
        SELECT pr.categoria_id INTO v_cat FROM producto pr WHERE pr.id = OLD.producto_id;
        IF v_cat IS NOT NULL THEN PERFORM fn_recalcular_ventas_categoria_dia(v_fecha, v_cat); END IF;
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_vcd_ins ON detalle_pedido;
DROP TRIGGER IF EXISTS trg_sync_vcd_upd ON detalle_pedido;
DROP TRIGGER IF EXISTS trg_sync_vcd_del ON detalle_pedido;

CREATE TRIGGER trg_sync_vcd_ins
AFTER INSERT ON detalle_pedido
FOR EACH ROW EXECUTE FUNCTION fn_trg_sync_ventas_categoria_dia();

CREATE TRIGGER trg_sync_vcd_upd
AFTER UPDATE ON detalle_pedido
FOR EACH ROW EXECUTE FUNCTION fn_trg_sync_ventas_categoria_dia();

CREATE TRIGGER trg_sync_vcd_del
AFTER DELETE ON detalle_pedido
FOR EACH ROW EXECUTE FUNCTION fn_trg_sync_ventas_categoria_dia();

-- Sincronizar con cambios en pedido (fecha/eliminado) - recalcular todas las categorías del pedido
CREATE OR REPLACE FUNCTION fn_trg_sync_vcd_por_pedido()
RETURNS TRIGGER AS $$
DECLARE
    r RECORD;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF OLD.fecha IS DISTINCT FROM NEW.fecha OR OLD.eliminado IS DISTINCT FROM NEW.eliminado THEN
            FOR r IN 
                SELECT DISTINCT pr.categoria_id, COALESCE(NEW.fecha, OLD.fecha) AS f
                FROM detalle_pedido dp
                JOIN producto pr ON pr.id = dp.producto_id
                WHERE dp.pedido_id = NEW.id AND dp.eliminado = FALSE
            LOOP
                PERFORM fn_recalcular_ventas_categoria_dia(r.f, r.categoria_id);
                IF OLD.fecha IS DISTINCT FROM NEW.fecha AND OLD.fecha IS NOT NULL THEN
                    PERFORM fn_recalcular_ventas_categoria_dia(OLD.fecha, r.categoria_id);
                END IF;
            END LOOP;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_vcd_pedido_upd ON pedido;
CREATE TRIGGER trg_sync_vcd_pedido_upd
AFTER UPDATE ON pedido
FOR EACH ROW EXECUTE FUNCTION fn_trg_sync_vcd_por_pedido();

-- Carga inicial
INSERT INTO ventas_categoria_dia(fecha, categoria_id, categoria_nombre, total_vendido, cantidad_items, cantidad_pedidos, actualizado_en)
SELECT ped.fecha, pr.categoria_id, c.nombre, SUM(dp.subtotal), SUM(dp.cantidad), COUNT(DISTINCT dp.pedido_id), now()
FROM detalle_pedido dp
JOIN producto pr ON pr.id = dp.producto_id
JOIN categoria c ON c.id = pr.categoria_id
JOIN pedido ped ON ped.id = dp.pedido_id
WHERE dp.eliminado = FALSE AND ped.eliminado = FALSE
GROUP BY ped.fecha, pr.categoria_id, c.nombre
ON CONFLICT (fecha, categoria_id) DO UPDATE SET
    categoria_nombre = EXCLUDED.categoria_nombre,
    total_vendido    = EXCLUDED.total_vendido,
    cantidad_items   = EXCLUDED.cantidad_items,
    cantidad_pedidos = EXCLUDED.cantidad_pedidos,
    actualizado_en   = now();

-- ============================================================================
-- 5.2(d) Consulta que lee directamente de la estructura desnormalizada
-- ============================================================================

-- Reemplaza la consulta original
SELECT categoria_nombre AS categoria,
       total_vendido
FROM ventas_categoria_dia
WHERE fecha = CURRENT_DATE
ORDER BY total_vendido DESC
LIMIT 5;

-- Medición después (ejecutar con EXPLAIN (ANALYZE, BUFFERS))
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT categoria_nombre AS categoria, total_vendido
-- FROM ventas_categoria_dia
-- WHERE fecha = CURRENT_DATE
-- ORDER BY total_vendido DESC
-- LIMIT 5;

-- ============================================================================
-- 5.2(e) Script de auditoría - debe retornar vacío si sincronizado
-- ============================================================================

-- Detecta diferencias entre fuente de verdad y tabla desnormalizada para fecha actual
WITH verdad AS (
    SELECT ped.fecha, pr.categoria_id, c.nombre AS categoria_nombre,
           SUM(dp.subtotal) AS total_vendido,
           SUM(dp.cantidad) AS cantidad_items,
           COUNT(DISTINCT dp.pedido_id) AS cantidad_pedidos
    FROM detalle_pedido dp
    JOIN producto pr ON pr.id = dp.producto_id
    JOIN categoria c ON c.id = pr.categoria_id
    JOIN pedido ped ON ped.id = dp.pedido_id
    WHERE dp.eliminado = FALSE AND ped.eliminado = FALSE
      AND ped.fecha = CURRENT_DATE
    GROUP BY ped.fecha, pr.categoria_id, c.nombre
),
desnorm AS (
    SELECT fecha, categoria_id, categoria_nombre, total_vendido, cantidad_items, cantidad_pedidos
    FROM ventas_categoria_dia
    WHERE fecha = CURRENT_DATE
)
SELECT v.fecha, v.categoria_id,
       v.total_vendido AS verdad_total, d.total_vendido AS desnorm_total,
       v.cantidad_items AS verdad_items, d.cantidad_items AS desnorm_items,
       v.cantidad_pedidos AS verdad_ped, d.cantidad_pedidos AS desnorm_ped
FROM verdad v
FULL OUTER JOIN desnorm d
  ON v.fecha = d.fecha AND v.categoria_id = d.categoria_id
WHERE COALESCE(v.total_vendido,0) <> COALESCE(d.total_vendido,0)
   OR COALESCE(v.cantidad_items,0) <> COALESCE(d.cantidad_items,0)
   OR COALESCE(v.cantidad_pedidos,0) <> COALESCE(d.cantidad_pedidos,0)
   OR v.categoria_nombre IS DISTINCT FROM d.categoria_nombre;

-- ============================================================================
-- NOTAS:
-- - Patrón elegido: columna precalculada con disparador (trigger-based materialization)
-- - Garantiza sincronización con fuente de verdad vía triggers AFTER sobre detalle_pedido/pedido
-- - Reversible sin pérdida: se puede recalcular con consulta original en cualquier momento
-- ============================================================================
