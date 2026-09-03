-- Escenario 2 - Lectura fantasma - SESION A (REPEATABLE READ)
BEGIN;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
\echo '>>> COUNT 1 (inicio):'
SELECT count(*) AS pizzas FROM producto WHERE categoria_id = 1;
\echo '>>> A espera 5s mientras B inserta una pizza nueva y confirma...'
SELECT pg_sleep(5);
\echo '>>> COUNT 2 (misma transaccion, despues de COMMIT de B):'
SELECT count(*) AS pizzas FROM producto WHERE categoria_id = 1;
COMMIT;
