-- ============================================================================
-- TP8 · Unidad 8 · Consigna 2.a
-- Vista v_snapshot_movil: la "instantanea" que viaja a la tablet.
--
-- Decisiones de diseno:
--   - precio_centavos: entero, para no viajar con punto flotante.
--   - disponible = activo AND stock > 0  (se puede vender ahora).
--   - eliminado  = NOT activo            (lapida de baja logica).
--   - Se incluyen los productos dados de baja: la lapida tambien viaja, para
--     que la tablet sepa que el producto existia y ya no esta.
--   - fecha_copia: momento en que se genera la instantanea.
-- ============================================================================

CREATE OR REPLACE VIEW v_snapshot_movil AS
SELECT p.id                               AS producto_id,
       p.nombre                           AS nombre,
       round(p.precio * 100)::bigint      AS precio_centavos,
       p.stock                            AS stock_visto,
       (p.activo AND p.stock > 0)         AS disponible,
       (NOT p.activo)                     AS eliminado,
       now()                              AS fecha_copia
FROM producto p
ORDER BY p.id;

SELECT 'vista_creada' AS objeto, count(*) AS filas FROM v_snapshot_movil;
