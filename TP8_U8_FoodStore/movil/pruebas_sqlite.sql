-- ============================================================================
-- TP8 · Unidad 8 · Consigna 1.c
-- Pruebas de la base de la tablet (SQLite)
--
-- Requiere: schema_sqlite.sql ejecutado y snapshot_servidor / producto_cache
-- cargados con la instantanea inicial (productos 1 a 5).
--
-- Ejecutar con:  sqlite3 foodstore_movil.db < pruebas_sqlite.sql
-- Los INSERT de C7 fallan a proposito: el cliente sqlite3 informa el error y
-- continua; luego el ROLLBACK deja la base sin filas nuevas.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- Limpieza de los borradores de prueba (no toca el catalogo).
DELETE FROM cola_sync;
DELETE FROM item_borrador;
DELETE FROM pedido_borrador;

-- ----------------------------------------------------------------------------
-- 1) Borrador completo confirmado con BEGIN ... COMMIT
--    cabecera + 2 items + solicitud en cola_sync
-- ----------------------------------------------------------------------------
BEGIN;
INSERT INTO pedido_borrador (id_local, usuario, forma_pago, fecha)
VALUES ('11111111-1111-4111-8111-111111111111', 'vendedor-demo', 'EFECTIVO',
        '2026-11-04T10:00:00Z');

INSERT INTO item_borrador (id_local, producto_id, cantidad, precio_centavos_visto)
VALUES ('11111111-1111-4111-8111-111111111111', 1, 2, 105000),
       ('11111111-1111-4111-8111-111111111111', 2, 1,  80000);

INSERT INTO cola_sync (solicitud_uuid, id_local, estado)
VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        '11111111-1111-4111-8111-111111111111', 'PENDIENTE');
COMMIT;

SELECT '1_borrador_confirmado' AS prueba,
       (SELECT count(*) FROM pedido_borrador
         WHERE id_local = '11111111-1111-4111-8111-111111111111') AS cabeceras,
       (SELECT count(*) FROM item_borrador
         WHERE id_local = '11111111-1111-4111-8111-111111111111') AS items,
       (SELECT count(*) FROM cola_sync
         WHERE id_local = '11111111-1111-4111-8111-111111111111') AS solicitudes;

-- ----------------------------------------------------------------------------
-- 2) Operacion deshecha con ROLLBACK: no deben quedar filas.
-- ----------------------------------------------------------------------------
BEGIN;
INSERT INTO pedido_borrador (id_local, usuario, forma_pago, fecha)
VALUES ('22222222-2222-4222-8222-222222222222', 'vendedor-demo', 'TARJETA',
        '2026-11-04T10:05:00Z');
INSERT INTO item_borrador (id_local, producto_id, cantidad, precio_centavos_visto)
VALUES ('22222222-2222-4222-8222-222222222222', 1, 5, 105000);
ROLLBACK;

SELECT '2_rollback_sin_filas' AS prueba,
       (SELECT count(*) FROM pedido_borrador
         WHERE id_local = '22222222-2222-4222-8222-222222222222') AS cabeceras,
       (SELECT count(*) FROM item_borrador
         WHERE id_local = '22222222-2222-4222-8222-222222222222') AS items;

-- ----------------------------------------------------------------------------
-- 3) Caso C1: el catalogo disponible se consulta sin conectarse al servidor.
--    (La tablet solo lee producto_cache.)
-- ----------------------------------------------------------------------------
SELECT 'C1_catalogo_offline' AS prueba,
       id, nombre, precio_centavos, stock_visto
FROM producto_cache
WHERE disponible = 1 AND eliminado = 0
ORDER BY nombre;

-- ----------------------------------------------------------------------------
-- 4) Caso C7a: cantidad 0 -> CHECK(cantidad > 0) falla.
--    El borrador se inserta dentro de la transaccion, pero el ROLLBACK lo
--    deshace: no quedan filas nuevas.
-- ----------------------------------------------------------------------------
BEGIN;
INSERT INTO pedido_borrador (id_local, usuario, forma_pago, fecha)
VALUES ('33333333-3333-4333-8333-333333333333', 'vendedor-demo', 'EFECTIVO',
        '2026-11-04T10:10:00Z');
INSERT INTO item_borrador (id_local, producto_id, cantidad, precio_centavos_visto)
VALUES ('33333333-3333-4333-8333-333333333333', 1, 0, 105000); -- ERROR: cantidad > 0
ROLLBACK;

SELECT 'C7a_cantidad_cero' AS prueba,
       (SELECT count(*) FROM pedido_borrador
         WHERE id_local = '33333333-3333-4333-8333-333333333333') AS cabeceras,
       (SELECT count(*) FROM item_borrador
         WHERE id_local = '33333333-3333-4333-8333-333333333333') AS items;

-- ----------------------------------------------------------------------------
-- 5) Caso C7b: producto inexistente -> FK a producto_cache falla.
--    Igual que C7a: ROLLBACK y sin filas nuevas.
-- ----------------------------------------------------------------------------
BEGIN;
INSERT INTO pedido_borrador (id_local, usuario, forma_pago, fecha)
VALUES ('44444444-4444-4444-8444-444444444444', 'vendedor-demo', 'EFECTIVO',
        '2026-11-04T10:15:00Z');
INSERT INTO item_borrador (id_local, producto_id, cantidad, precio_centavos_visto)
VALUES ('44444444-4444-4444-8444-444444444444', 999999, 1, 100); -- ERROR: FK producto inexistente
ROLLBACK;

SELECT 'C7b_producto_inexistente' AS prueba,
       (SELECT count(*) FROM pedido_borrador
         WHERE id_local = '44444444-4444-4444-8444-444444444444') AS cabeceras,
       (SELECT count(*) FROM item_borrador
         WHERE id_local = '44444444-4444-4444-8444-444444444444') AS items;
