-- ============================================================================
-- Food Store - Restricciones de integridad de negocio (TP2, Parte 1)
-- Generado con asistencia de IA (OpenCode) y REVISADO linea por linea por el alumno.
-- Motor: PostgreSQL 17 | Base de trabajo: foodstore_tp2 (copia, ver protocolo)
-- Reglas (spec en spec_restricciones.md):
--   R1: un cliente inactivo no puede generar pedidos nuevos.
--   R2: un producto inactivo no se puede vender en lineas de pedido nuevas.
--   R3: la cantidad vendida no puede superar el stock disponible del producto.
-- Aplicar dentro de una transaccion: BEGIN; ... pruebas ... COMMIT;
-- ============================================================================

-- ---------------------------------------------------------------------------
-- R1: no insertar pedidos para clientes inactivos
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION chk_activo_cliente_pedido() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM cliente WHERE id = NEW.cliente_id AND activo = TRUE
    ) THEN
        RAISE EXCEPTION 'No se puede crear un pedido para el cliente % (inactivo o inexistente).',
            NEW.cliente_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_chk_activo_cliente_pedido ON pedido;
CREATE TRIGGER trg_chk_activo_cliente_pedido
    BEFORE INSERT ON pedido
    FOR EACH ROW
    EXECUTE FUNCTION chk_activo_cliente_pedido();

-- ---------------------------------------------------------------------------
-- R2: no vender en lineas nuevas productos inactivos
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION chk_activo_producto_linea() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM producto WHERE id = NEW.producto_id AND activo = TRUE
    ) THEN
        RAISE EXCEPTION 'No se puede vender el producto % (inactivo o inexistente).',
            NEW.producto_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_chk_activo_producto_linea ON linea_pedido;
CREATE TRIGGER trg_chk_activo_producto_linea
    BEFORE INSERT ON linea_pedido
    FOR EACH ROW
    EXECUTE FUNCTION chk_activo_producto_linea();

-- ---------------------------------------------------------------------------
-- R3: la cantidad vendida no supera el stock disponible
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION chk_stock_linea() RETURNS trigger AS $$
DECLARE
    v_stock INTEGER;
BEGIN
    SELECT stock INTO v_stock FROM producto WHERE id = NEW.producto_id;
    IF v_stock IS NOT NULL AND NEW.cantidad > v_stock THEN
        RAISE EXCEPTION 'Stock insuficiente para el producto %: pide % pero hay % disponibles.',
            NEW.producto_id, NEW.cantidad, v_stock;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_chk_stock_linea ON linea_pedido;
CREATE TRIGGER trg_chk_stock_linea
    BEFORE INSERT OR UPDATE OF cantidad ON linea_pedido
    FOR EACH ROW
    EXECUTE FUNCTION chk_stock_linea();
