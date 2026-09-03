-- ============================================================================
-- Escenario 1 - Lectura no repetible - SESION B
-- Actualiza y confirma el precio del producto 2 MIENTRAS la sesion A lee.
-- ============================================================================
\echo '>>> SESION B inicia con 1.5s de retardo'
SELECT pg_sleep(2);

BEGIN;
UPDATE producto SET precio = 850.00 WHERE id = 2;
COMMIT;

\echo '>>> SESION B confirmo: precio del producto 2 ahora es 850.00';
SELECT id, nombre, precio FROM producto WHERE id = 2;
