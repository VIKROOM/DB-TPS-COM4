-- ============================================================================
-- Escenario 1 - Lectura no repetible - SESION A en REPEATABLE READ
-- Muestra que, a diferencia de READ COMMITTED, la 2da lectura NO cambia.
-- La sesion B (sB1.sql) vuelve a actualizar y confirma durante la espera.
-- ============================================================================
BEGIN;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

SELECT 'SESION A (REPEATABLE READ)' AS quien, now() AS momento;
\echo '>>> Lectura 1 (inicio de transaccion):'
SELECT id, nombre, precio FROM producto WHERE id = 2;

\echo '>>> A espera 5 segundos mientras B actualiza y confirma...'
SELECT pg_sleep(5);

\echo '>>> Lectura 2 (misma transaccion, despues del COMMIT de B):'
SELECT id, nombre, precio FROM producto WHERE id = 2;

COMMIT;
\echo '>>> FIN SESION A (RR)';
