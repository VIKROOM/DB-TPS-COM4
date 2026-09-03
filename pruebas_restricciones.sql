-- ============================================================================
-- Pruebas de verificación de las restricciones de integridad (Parte 1)
-- Ejecutado sobre foodstore_tp2 (copia) dentro de UNA transaccion.
-- El DDL se incluye via \i, las pruebas usan bloques DO para capturar
-- los errores esperados (RAISE EXCEPTION de los triggers) sin abortar.
-- ============================================================================

BEGIN;

-- 1) Aplicar las restricciones (DDL transaccional)
\i restricciones_integridad.sql

-- ---------------------------------------------------------------------------
-- REGLA 1: cliente inactivo no genera pedidos
-- ---------------------------------------------------------------------------
UPDATE cliente SET activo = FALSE WHERE id = 1;
SELECT 'R1: cliente 1 dado de baja' AS paso;

DO $$
BEGIN
  BEGIN
    BEGIN
      INSERT INTO pedido (cliente_id, forma_pago) VALUES (1, 'EFECTIVO');
      RAISE NOTICE 'R1-INVALIDO = FALLO (el trigger no rechazo, BUG)';
    EXCEPTION WHEN others THEN
      RAISE NOTICE 'R1-INVALIDO OK: pedido a cliente inactivo rechazado -> %', SQLERRM;
    END;
  END;
END $$;

UPDATE cliente SET activo = TRUE WHERE id = 1;
SELECT 'R1: cliente 1 reactivado' AS paso;

DO $$
BEGIN
  INSERT INTO pedido (cliente_id, forma_pago) VALUES (1, 'EFECTIVO');
  RAISE NOTICE 'R1-VALIDO OK: pedido a cliente activo aceptado';
END $$;

-- ---------------------------------------------------------------------------
-- REGLA 2: producto inactivo no se vende en lineas nuevas
-- (pedido de prueba creado arriba; usar lastval para no chocar con PK)
-- ---------------------------------------------------------------------------
UPDATE producto SET activo = FALSE WHERE id = 2;
SELECT 'R2: producto 2 (Coca) dado de baja' AS paso;

DO $$
DECLARE
  v_pedido BIGINT := (
     SELECT max(id) FROM pedido
  );
BEGIN
  BEGIN
    BEGIN
      INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario)
      VALUES (v_pedido, 2, 1, 800.00);
      RAISE NOTICE 'R2-INVALIDO = FALLO (el trigger no rechazo, BUG)';
    EXCEPTION WHEN others THEN
      RAISE NOTICE 'R2-INVALIDO OK: linea con producto inactivo rechazada -> %', SQLERRM;
    END;
  END;
END $$;

UPDATE producto SET activo = TRUE WHERE id = 2;
SELECT 'R2: producto 2 reactivado' AS paso;

DO $$
DECLARE
  v_pedido BIGINT := (SELECT max(id) FROM pedido);
BEGIN
  INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario)
  VALUES (v_pedido, 1, 1, 1050.00);
  RAISE NOTICE 'R2-VALIDO OK: linea con producto activo aceptada';
END $$;

-- ---------------------------------------------------------------------------
-- REGLA 3: cantidad no superior al stock
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  v_pedido BIGINT := (SELECT max(id) FROM pedido);
BEGIN
  BEGIN
    BEGIN
      -- producto 1 (Muzzarella) stock = 20
      INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario)
      VALUES (v_pedido, 1, 5000, 1050.00);
      RAISE NOTICE 'R3-INVALIDO = FALLO (el trigger no rechazo, BUG)';
    EXCEPTION WHEN others THEN
      RAISE NOTICE 'R3-INVALIDO OK: cantidad sobre stock rechazada -> %', SQLERRM;
    END;
  END;
END $$;

DO $$
DECLARE
  v_pedido BIGINT := (SELECT max(id) FROM pedido);
BEGIN
  -- producto 2 (Coca) stock = 50, aun sin linea en este pedido
  INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario)
  VALUES (v_pedido, 2, 3, 800.00);
  RAISE NOTICE 'R3-VALIDO OK: cantidad dentro del stock aceptada';
END $$;

-- ---------------------------------------------------------------------------
-- Inspeccion del efecto antes de decidir COMMIT o ROLLBACK
-- ---------------------------------------------------------------------------
SELECT 'Estado despues de las pruebas (transaccion aun abierta):' AS estado;
SELECT p.id AS pedido, count(lp.producto_id) AS lineas
FROM pedido p
LEFT JOIN linea_pedido lp ON lp.pedido_id = p.id
GROUP BY p.id
ORDER BY p.id;

-- Comentario de cierre: si todo se ve correcto, correr COMMIT;
-- si algo fallo, ROLLBACK; (la ejecucion manual decide).
ROLLBACK;
SELECT 'ROLLBACK aplicado: la transaccion de prueba NO persistio cambios' AS fin;
