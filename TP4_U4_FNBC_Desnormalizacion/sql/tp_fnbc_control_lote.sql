-- ============================================================================
-- TP_U4_FNBC_Desnormalizacion_FoodStore - Parte 1
-- Archivo: tp_fnbc_control_lote.sql
-- ============================================================================
-- 1) ESQUEMA ORIGINAL (contexto) - control_lote_almacen
-- Tabla tal como se presenta en la consigna
-- ============================================================================

DROP TABLE IF EXISTS control_lote_almacen CASCADE;

CREATE TABLE control_lote_almacen (
    lote_id                 BIGINT NOT NULL, -- REFERENCES lote(id)
    deposito_id             BIGINT NOT NULL, -- REFERENCES deposito(id)
    responsable_control_id  BIGINT NOT NULL, -- REFERENCES usuario(id)
    PRIMARY KEY (lote_id, deposito_id)
);

-- Instancia de ejemplo provista
INSERT INTO control_lote_almacen VALUES
    (501, 30, 801),
    (502, 30, 801),
    (503, 31, 802);

-- ============================================================================
-- 2) ANÁLISIS (a)-(d) - Resuelto en informe, pero se documenta aquí
-- Dependencias funcionales (notación formal):
-- DF1: {lote_id, deposito_id} -> {responsable_control_id}
-- DF2: {responsable_control_id} -> {deposito_id}
--
-- Claves candidatas: {lote_id, deposito_id} (única razonable). 
-- Atributos primos: lote_id, deposito_id. No primos: responsable_control_id.
-- Violación FNBC: determinante responsable_control_id no es superclave -> no está en FNBC.
-- Anomalías: inserción/borrado/actualización habilitadas por DF2.
-- ============================================================================

-- ============================================================================
-- 3) DESCOMPOSICIÓN SIN PÉRDIDA (R1,R2) + VISTA DE COMPATIBILIDAD
-- Se descompone en:
-- R1(responsable_control_id, deposito_id) con PK(responsable_control_id)
-- R2(lote_id, responsable_control_id) con PK(lote_id, responsable_control_id)
-- Vista v_control_lote_almacen recompone (lote_id, deposito_id, responsable_control_id)
-- ============================================================================

DROP VIEW IF EXISTS v_control_lote_almacen CASCADE;
DROP TABLE IF EXISTS control_lote CASCADE;
DROP TABLE IF EXISTS responsable_deposito CASCADE;

CREATE TABLE responsable_deposito (
    responsable_control_id  BIGINT NOT NULL,
    deposito_id            BIGINT NOT NULL,
    PRIMARY KEY (responsable_control_id)
);

CREATE TABLE control_lote (
    lote_id                BIGINT NOT NULL,
    responsable_control_id BIGINT NOT NULL,
    PRIMARY KEY (lote_id, responsable_control_id),
    CONSTRAINT fk_control_lote_resp FOREIGN KEY (responsable_control_id)
        REFERENCES responsable_deposito(responsable_control_id)
);

-- Vista de compatibilidad que reconstruye la relación original mediante JOIN
CREATE OR REPLACE VIEW v_control_lote_almacen AS
SELECT cl.lote_id, rd.deposito_id, cl.responsable_control_id
FROM control_lote cl
JOIN responsable_deposito rd
  ON cl.responsable_control_id = rd.responsable_control_id;

-- ============================================================================
-- 4) MIGRACIÓN DE DATOS DESDE LA INSTANCIA DE EJEMPLO
-- ============================================================================

-- Migrar: primero responsables->depósitos (un responsable por depósito según regla)
INSERT INTO responsable_deposito (responsable_control_id, deposito_id)
SELECT DISTINCT responsable_control_id, deposito_id
FROM control_lote_almacen
ON CONFLICT (responsable_control_id) DO NOTHING;

-- Migrar: (lote, responsable)
INSERT INTO control_lote (lote_id, responsable_control_id)
SELECT lote_id, responsable_control_id
FROM control_lote_almacen
ON CONFLICT (lote_id, responsable_control_id) DO NOTHING;

-- ============================================================================
-- 5) VERIFICACIÓN DE EQUIVALENCIA MEDIANTE LA VISTA DE COMPATIBILIDAD
-- ============================================================================

-- Debe reconstruir exactamente la relación original
SELECT * FROM v_control_lote_almacen ORDER BY lote_id, deposito_id;

-- Comparación directa: debería dar 0 filas si son equivalentes
-- (proyección igual al original)
SELECT cla.lote_id, cla.deposito_id, cla.responsable_control_id
FROM control_lote_almacen cla
LEFT JOIN v_control_lote_almacen v
  ON cla.lote_id = v.lote_id AND cla.deposito_id = v.deposito_id AND cla.responsable_control_id = v.responsable_control_id
WHERE v.lote_id IS NULL;

-- ============================================================================ 
-- JUSTIFICACIÓN (f): La unión es sin pérdida porque el atributo común
-- responsable_control_id es clave en responsable_deposito (PK) y aparece
-- como FK en control_lote; además rd(responsable_control_id)->(deposito_id)
-- garantiza unicidad, por lo que el JOIN por PK/FK reconstruye exactamente
-- (lote_id, deposito_id, responsable_control_id) sin generar duplicados.
-- ============================================================================
