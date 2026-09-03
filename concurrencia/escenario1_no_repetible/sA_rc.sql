-- ============================================================================
-- Escenario 1 - Lectura no repetible - SESION A
-- NIVEL: READ COMMITTED (default de PostgreSQL)
-- Comandos exactos de la sesion A; la sesion B corre en paralelo (sB1.sql)
-- ============================================================================
BEGIN;
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

SELECT 'SESION A (READ COMMITTED)' AS quien, now() AS momento;
\echo '>>> Lectura 1 (inicio de transaccion):'
SELECT id, nombre, precio FROM producto WHERE id = 2;

\echo '>>> A espera 5 segundos mientras B actualiza y confirma...'
SELECT pg_sleep(5);

\echo '>>> Lectura 2 (misma transaccion, despues del COMMIT de B):'
SELECT id, nombre, precio FROM producto WHERE id = 2;

COMMIT;
\echo '>>> FIN SESION A (RR: verificar resultado en reporte)';
