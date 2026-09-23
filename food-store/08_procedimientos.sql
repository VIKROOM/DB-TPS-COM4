-- ============================================================================
-- Food Store — 08_procedimientos.sql (Parte D) · Unidad 3 · Semana 1
-- Procedimientos almacenados en PL/pgSQL (objetivo 6 del TPI: faltaban
-- objetos invocables con CALL).
-- Spec: specs/spec_procedimientos_almacenados.md
-- Base de trabajo: foodstore_u3 (copia) · Motor: PostgreSQL 17
-- ============================================================================

-- ----------------------------------------------------------------------------
-- P1 · registrar_pedido: registro de venta transaccional en el motor.
--   Inserta pedido + lineas (precio congelado) y descuenta stock, todo en
--   una unica transaccion. Refuerza las reglas de integridad R1/R2/R3 ya
--   existentes y evita sobreventa bajo concurrencia (SELECT ... FOR UPDATE).
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE registrar_pedido(
    p_cliente_id  BIGINT,
    p_forma_pago  forma_pago,
    p_items       JSONB,
    INOUT p_pedido_id BIGINT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_item      JSONB;
    v_producto  BIGINT;
    v_cantidad  INTEGER;
    v_stock     INTEGER;
    v_precio    NUMERIC(10,2);
BEGIN
    -- R1: el cliente debe existir y estar activo.
    IF NOT EXISTS (SELECT 1 FROM cliente WHERE id = p_cliente_id AND activo = TRUE) THEN
        RAISE EXCEPTION 'R1: no se puede registrar un pedido para el cliente % (inactivo o inexistente).',
            p_cliente_id;
    END IF;

    -- 1) Insertar el pedido y recuperar su id.
    INSERT INTO pedido (cliente_id, forma_pago)
    VALUES (p_cliente_id, p_forma_pago)
    RETURNING id INTO p_pedido_id;

    -- 2) Procesar cada linea del JSONB.
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_producto := (v_item->>'producto_id')::BIGINT;
        v_cantidad := (v_item->>'cantidad')::INTEGER;

        IF v_producto IS NULL OR v_cantidad IS NULL THEN
            RAISE EXCEPTION 'Item invalido: se requiere producto_id y cantidad (JSON: %)', v_item;
        END IF;

        IF v_cantidad <= 0 THEN
            RAISE EXCEPTION 'Item invalido: cantidad debe ser > 0 (recibido: %)', v_cantidad;
        END IF;

        -- R2 + bloqueo: producto existente y activo. FOR UPDATE fija el
        -- precio y el stock para este pedido y evita sobreventa concurrente.
        SELECT p.stock, p.precio
        INTO   v_stock, v_precio
        FROM   producto p
        WHERE  p.id = v_producto
          AND  p.activo = TRUE
        FOR UPDATE;

        IF v_stock IS NULL THEN
            RAISE EXCEPTION 'R2: no se puede vender el producto % (inactivo o inexistente).',
                v_producto;
        END IF;

        -- R3: no vender mas unidades de las disponibles.
        IF v_cantidad > v_stock THEN
            RAISE EXCEPTION 'R3: stock insuficiente para el producto %: pide % pero hay % disponibles.',
                v_producto, v_cantidad, v_stock;
        END IF;

        -- 3) Insertar la linea con el precio congelado (R4).
        INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario)
        VALUES (p_pedido_id, v_producto, v_cantidad, v_precio);

        -- 4) Descontar el stock.
        UPDATE producto SET stock = stock - v_cantidad WHERE id = v_producto;
    END LOOP;
END;
$$;

-- ----------------------------------------------------------------------------
-- P2 · ajustar_stock: reposicion/ajuste manual de inventario. Procedimiento
--   con mutacion real y resultado por OUT + RAISE NOTICE. Valida vigencia del
--   producto, bloquea la fila y rechaza stock negativo.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE ajustar_stock(
    p_producto_id     BIGINT,
    p_delta           INTEGER,
    INOUT p_nuevo_stock INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_stock  INTEGER;
BEGIN
    SELECT p.stock
    INTO   v_stock
    FROM   producto p
    WHERE  p.id = p_producto_id
      AND  p.activo = TRUE
    FOR UPDATE;

    IF v_stock IS NULL THEN
        RAISE EXCEPTION 'Producto % inexistente o inactivo (no se puede ajustar stock).', p_producto_id;
    END IF;

    -- stock >= 0 (regla del DDL, reforzada a nivel de operacion).
    IF v_stock + p_delta < 0 THEN
        RAISE EXCEPTION 'Stock no puede quedar negativo: producto % tiene % y el ajuste pedido es %',
            p_producto_id, v_stock, p_delta;
    END IF;

    UPDATE producto SET stock = v_stock + p_delta WHERE id = p_producto_id;

    p_nuevo_stock := v_stock + p_delta;
    RAISE NOTICE 'Stock del producto % ajustado: % -> %', p_producto_id, v_stock, p_nuevo_stock;
END;
$$;