-- ============================================================================
-- TP_U4_FNBC_Desnormalizacion_FoodStore - Parte 1 (migración segura)
-- Archivo: tp_fnbc_control_lote_migracion_segura.sql
--
-- Objetivo:
--   Migrar control_lote_almacen a un esquema en FNBC
--   (responsable_deposito + control_lote) dentro de una transacción
--   reversible, con respaldo previo y verificación bidireccional.
--
-- Diferencia con tp_fnbc_control_lote.sql:
--   * tp_fnbc_control_lote.sql es el script de análisis/demostración: hace
--     DROP TABLE y recrea la instancia de ejemplo. NO debe ejecutarse sobre
--     una base con datos reales.
--   * Este script NO elimina la tabla original: la conserva y solo agrega los
--     objetos nuevos. Si la verificación falla, ROLLBACK deja todo como estaba.
--
-- Uso:
--   psql -h localhost -U <usuario> -d <base> -v ON_ERROR_STOP=1 \
--        -f sql/tp_fnbc_control_lote_migracion_segura.sql
--
-- Plan de reversión: ver kiro/design.md §Reversión post-COMMIT y el bloque
-- comentado al final de este archivo.
-- ============================================================================

\set ON_ERROR_STOP on

-- ----------------------------------------------------------------------------
-- 1) Respaldo previo (fuera de la transacción, para que sobreviva a un ROLLBACK)
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.control_lote_almacen') IS NULL THEN
        RAISE EXCEPTION 'No existe public.control_lote_almacen: no hay nada que migrar';
    END IF;

    IF to_regclass('public.control_lote_almacen_backup') IS NULL THEN
        EXECUTE 'CREATE TABLE control_lote_almacen_backup AS TABLE control_lote_almacen';
        RAISE NOTICE 'Respaldo creado: control_lote_almacen_backup';
    ELSE
        RAISE NOTICE 'Ya existe control_lote_almacen_backup: se conserva el respaldo previo';
    END IF;
END $$;

SELECT 'respaldo' AS control, count(*) AS filas
FROM control_lote_almacen_backup;

-- ----------------------------------------------------------------------------
-- 2) Migración transaccional
-- ----------------------------------------------------------------------------
BEGIN;

CREATE TABLE IF NOT EXISTS responsable_deposito (
    responsable_control_id  BIGINT NOT NULL,
    deposito_id            BIGINT NOT NULL,
    PRIMARY KEY (responsable_control_id)
);

CREATE TABLE IF NOT EXISTS control_lote (
    lote_id                BIGINT NOT NULL,
    responsable_control_id BIGINT NOT NULL,
    PRIMARY KEY (lote_id, responsable_control_id),
    CONSTRAINT fk_control_lote_resp FOREIGN KEY (responsable_control_id)
        REFERENCES responsable_deposito(responsable_control_id)
);

INSERT INTO responsable_deposito (responsable_control_id, deposito_id)
SELECT DISTINCT responsable_control_id, deposito_id
FROM control_lote_almacen
ON CONFLICT (responsable_control_id) DO NOTHING;

INSERT INTO control_lote (lote_id, responsable_control_id)
SELECT lote_id, responsable_control_id
FROM control_lote_almacen
ON CONFLICT (lote_id, responsable_control_id) DO NOTHING;

CREATE OR REPLACE VIEW v_control_lote_almacen AS
SELECT cl.lote_id, rd.deposito_id, cl.responsable_control_id
FROM control_lote cl
JOIN responsable_deposito rd
  ON cl.responsable_control_id = rd.responsable_control_id;

-- ----------------------------------------------------------------------------
-- 3) Verificación bidireccional: la vista debe reconstruir exactamente la
--    tabla original. Si falta o sobra una fila, se aborta y ROLLBACK deshace.
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_perdidas BIGINT;
    v_espurias  BIGINT;
BEGIN
    SELECT count(*)
      INTO v_perdidas
      FROM control_lote_almacen cla
      LEFT JOIN v_control_lote_almacen v
        ON cla.lote_id = v.lote_id
       AND cla.deposito_id = v.deposito_id
       AND cla.responsable_control_id = v.responsable_control_id
     WHERE v.lote_id IS NULL;

    SELECT count(*)
      INTO v_espurias
      FROM v_control_lote_almacen v
      LEFT JOIN control_lote_almacen cla
        ON cla.lote_id = v.lote_id
       AND cla.deposito_id = v.deposito_id
       AND cla.responsable_control_id = v.responsable_control_id
     WHERE cla.lote_id IS NULL;

    IF v_perdidas > 0 OR v_espurias > 0 THEN
        RAISE EXCEPTION
            'Migración FNBC abortada: filas perdidas=%, filas espurias=%. ROLLBACK.',
            v_perdidas, v_espurias;
    END IF;

    RAISE NOTICE 'Verificación OK: la vista reconstruye la tabla original (0 diferencias)';
END $$;

COMMIT;

-- ----------------------------------------------------------------------------
-- 4) Evidencia posterior al COMMIT
-- ----------------------------------------------------------------------------
SELECT 'equivalencia' AS control,
       (SELECT count(*) FROM control_lote_almacen) AS filas_original,
       (SELECT count(*) FROM v_control_lote_almacen) AS filas_vista,
       (SELECT count(*) FROM control_lote_almacen_backup) AS filas_backup;

SELECT 'migracion_ok' AS estado,
       (SELECT count(*) FROM responsable_deposito) AS responsables,
       (SELECT count(*) FROM control_lote) AS asignaciones;

-- ============================================================================
-- PLAN DE REVERSIÓN (post-COMMIT) - ejecutar solo si se decide volver atrás
-- ============================================================================
-- BEGIN;
--
-- -- 1) Reconstruir la tabla original desde el respaldo (o desde la vista).
-- CREATE TABLE control_lote_almacen_restaurada AS
-- SELECT lote_id, deposito_id, responsable_control_id
-- FROM control_lote_almacen_backup;
--
-- -- 2) Verificar que no haya diferencias con el respaldo.
-- SELECT count(*) AS diferencias
-- FROM (
--     SELECT * FROM control_lote_almacen_restaurada
--     EXCEPT
--     SELECT * FROM control_lote_almacen_backup
-- ) d;
--
-- -- 3) Reemplazar la tabla original (renombrar, no borrar).
-- ALTER TABLE control_lote_almacen RENAME TO control_lote_almacen_migrada;
-- ALTER TABLE control_lote_almacen_restaurada RENAME TO control_lote_almacen;
--
-- -- 4) Eliminar los objetos nuevos.
-- DROP VIEW  IF EXISTS v_control_lote_almacen;
-- DROP TABLE IF EXISTS control_lote;
-- DROP TABLE IF EXISTS responsable_deposito;
--
-- COMMIT;
-- ============================================================================
-- PRUEBA DE ROLLBACK (opcional, en una copia de prueba):
--   Insertar en control_lote_almacen una fila que viole DF2 (mismo
--   responsable_control_id con dos deposito_id distintos) y volver a ejecutar
--   este script. La verificación bidireccional detecta la fila perdida,
--   RAISE EXCEPTION aborta y ROLLBACK deja la base sin objetos nuevos.
-- ============================================================================
