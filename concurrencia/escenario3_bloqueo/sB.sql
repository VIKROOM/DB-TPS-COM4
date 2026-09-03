-- Escenario 3 - Espera por bloqueo - SESION B (FOR UPDATE bloqueado hasta COMMIT de A)
SELECT to_char(now(),'HH24:MI:SS') AS inicio_intento;
SELECT to_char(now(),'HH24:MI:SS') AS inicio;
\echo '>>> B pide FOR UPDATE sobre la fila 1 (debe esperar a que A haga COMMIT):'
SELECT to_char(now(),'HH24:MI:SS') AS antes;
SELECT id, nombre, stock FROM producto WHERE id = 1 FOR UPDATE;
SELECT to_char(now(),'HH24:MI:SS') AS despues;
\echo '>>> B obtuvo el bloqueo SOLO despues del COMMIT de A (espera comprobada)';