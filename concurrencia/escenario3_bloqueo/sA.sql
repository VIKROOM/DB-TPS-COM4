-- Escenario 3 - Espera por bloqueo - SESION A (FOR UPDATE + COMMIT)
BEGIN;
\echo '>>> A bloquea fila producto 1 con FOR UPDATE y se queda 5s:'
SELECT id, nombre, stock FROM producto WHERE id = 1 FOR UPDATE;
SELECT pg_sleep(5);
COMMIT;
\echo '>>> A hizo COMMIT: libero el bloqueo de la fila 1';