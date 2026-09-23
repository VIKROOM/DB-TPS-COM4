-- ============================================================================
-- Food Store — 09_verificacion_procedimientos.sql (Parte D) · Unidad 3
-- Ejecutar sobre foodstore_u3 (copia) DENTRO de una transaccion que termina
-- en ROLLBACK: nada queda persistido (protocolo de seguridad).
-- Verificacion objetiva de los procedimientos de 08_procedimientos.sql.
-- ============================================================================

BEGIN;

-- Sanity: crear los procedimientos desde el DDL transaccional.
-- (ruta absoluta: psql resuelve \i relativo al cwd, no al script)
\i 'C:/UTN/3er semestre/Bases de Datos II/UNIDAD 1/food-store/08_procedimientos.sql'

SELECT 'P1 + P2 creados' AS paso;

-- ---------------------------------------------------------------------------
-- P1 · CASO VALIDO: cliente 1 (activo) compra 2 Muzzarella (stock 20) y
--      3 Coca 1.5L (stock 50). Debe devolver un pedido_id, crear 2 lineas
--      y dejar stock 18 y 47.
-- ---------------------------------------------------------------------------
SELECT '--- P1 caso valido: precio y stock ANTES ---' AS paso;
SELECT id, nombre, stock, precio FROM producto WHERE id IN (1, 2) ORDER BY id;

\set ON_ERROR_STOP off

DO $$
DECLARE
    v_pedido BIGINT;
BEGIN
    CALL registrar_pedido(1, 'EFECTIVO', '[{"producto_id":1,"cantidad":2},{"producto_id":2,"cantidad":3}]', v_pedido);
    RAISE NOTICE 'P1-VALIDO OK: pedido % creado', v_pedido;
END $$;

-- Verificar pedido + lineas + stock descontado.
SELECT 'Pedido creado (ultimos):' AS paso;
SELECT p.id, p.cliente_id, p.forma_pago, count(lp.producto_id) AS lineas,
       SUM(lp.cantidad * lp.precio_unitario) AS total
FROM   pedido p
LEFT JOIN linea_pedido lp ON lp.pedido_id = p.id
WHERE  p.id = (SELECT max(id) FROM pedido)
GROUP  BY p.id;

SELECT 'Stock DESPUES del pedido valido (esperado 18 y 47):' AS paso;
SELECT id, nombre, stock FROM producto WHERE id IN (1, 2) ORDER BY id;

-- ---------------------------------------------------------------------------
-- P1 · CASOS INVALIDOS (bloque DO anidado captura el error sin abortar):
--   (a) cliente inactivo, (b) producto inactivo, (c) stock insuficiente.
-- ---------------------------------------------------------------------------
SELECT '--- P1 casos invalidos ---' AS paso;

DO $$
DECLARE
    v_pedido BIGINT;
BEGIN
    UPDATE cliente SET activo = FALSE WHERE id = 2;
    BEGIN
        BEGIN
            CALL registrar_pedido(2, 'EFECTIVO', '[{"producto_id":1,"cantidad":1}]', v_pedido);
            RAISE NOTICE 'P1a = FALLO (no valido el cliente inactivo, BUG)';
        EXCEPTION WHEN others THEN
            RAISE NOTICE 'P1a-INVALIDO OK: %', SQLERRM;
        END;
        UPDATE cliente SET activo = TRUE WHERE id = 2;
    END;
END $$;

DO $$
DECLARE
    v_pedido BIGINT;
BEGIN
    UPDATE producto SET activo = FALSE WHERE id = 3;
    BEGIN
        BEGIN
            CALL registrar_pedido(1, 'EFECTIVO', '[{"producto_id":3,"cantidad":1}]', v_pedido);
            RAISE NOTICE 'P1b = FALLO (no valido el producto inactivo, BUG)';
        EXCEPTION WHEN others THEN
            RAISE NOTICE 'P1b-INVALIDO OK: %', SQLERRM;
        END;
        UPDATE producto SET activo = TRUE WHERE id = 3;
    END;
END $$;

DO $$
DECLARE
    v_pedido BIGINT;
BEGIN
    -- Muzzarella tiene stock 18 tras el pedido valido; pedir 999 debe fallar
    -- y NO descontar stock de ningun item (atomicidad).
    BEGIN
        CALL registrar_pedido(1, 'EFECTIVO',
            '[{"producto_id":1,"cantidad":999},{"producto_id":2,"cantidad":5}]', v_pedido);
        RAISE NOTICE 'P1c = FALLO (no valido el stock, BUG)';
    EXCEPTION WHEN others THEN
        RAISE NOTICE 'P1c-INVALIDO OK: %', SQLERRM;
    END;
END $$;

SELECT 'Stock tras los invalidados (debe seguir 18 y 47, sin cambios):' AS paso;
SELECT id, nombre, stock FROM producto WHERE id IN (1, 2) ORDER BY id;

-- ---------------------------------------------------------------------------
-- P2 · CASO VALIDO: ajustar stock del producto 1 en +10 (18 -> 28).
-- ---------------------------------------------------------------------------
SELECT '--- P2 caso valido ---' AS paso;

DO $$
DECLARE
    v_nuevo INTEGER;
BEGIN
    CALL ajustar_stock(1, 10, v_nuevo);
    RAISE NOTICE 'P2-VALIDO OK: nuevo stock = %', v_nuevo;
END $$;

SELECT id, nombre, stock FROM producto WHERE id IN (1, 2) ORDER BY id;

-- ---------------------------------------------------------------------------
-- P2 · CASO INVALIDO: ajuste que deje stock negativo debe fallar y no tocar.
-- ---------------------------------------------------------------------------
SELECT '--- P2 caso invalido ---' AS paso;

DO $$
DECLARE
    v_nuevo INTEGER;
BEGIN
    BEGIN
        CALL ajustar_stock(1, -999999, v_nuevo);
        RAISE NOTICE 'P2-INVALIDO = FALLO (no rechazo stock negativo, BUG)';
    EXCEPTION WHEN others THEN
        RAISE NOTICE 'P2-INVALIDO OK: %', SQLERRM;
    END;
END $$;

SELECT id, nombre, stock FROM producto WHERE id IN (1, 2) ORDER BY id;

-- ---------------------------------------------------------------------------
-- Estado global antes del ROLLBACK (la transaccion aun esta abierta).
-- El pedido de la prueba se revierte junto con todo lo demas.
-- ---------------------------------------------------------------------------
SELECT count(*) AS total_pedidos_durante_prueba FROM pedido;

-- Comentario de cierre: la prueba NUNCA se confirma; se revierte todo.
ROLLBACK;
SELECT 'ROLLBACK: la verificacion NO persistio nada en foodstore_u3' AS fin;