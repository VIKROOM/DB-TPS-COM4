-- Escenario 4 - Interbloqueo - SESION B
-- Bloquea producto 2 y avisa a A (flag en sync_deadlock), luego pide fila 1.
\echo '>>> SESION B espera 1s y arranca:'
SELECT pg_sleep(1);
BEGIN;
\echo '>>> B bloquea producto 2:'
SELECT id FROM producto WHERE id = 2 FOR UPDATE;
-- Avisa a A que ya tiene fila 2
UPDATE sync_deadlock SET aviso = TRUE WHERE id = 1;
\echo '>>> B aviso a A; ahora intenta bloquear producto 1 (A lo tiene):'
SELECT id FROM producto WHERE id = 1 FOR UPDATE;
COMMIT;