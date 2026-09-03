-- Escenario 4 - Interbloqueo - SESION A
-- Espera con LOOP real hasta que B haya bloqueado producto 2 (flag aviso),
-- garantizando que el cruce se produce con ambas filas ya bloqueadas.
BEGIN;
\echo '>>> A bloquea producto 1:'
SELECT id FROM producto WHERE id = 1 FOR UPDATE;

\echo '>>> A espera (hasta 20s) que B bloquee producto 2:'
DO $$
DECLARE
  i int := 0;
BEGIN
  LOOP
    EXIT WHEN EXISTS (SELECT 1 FROM sync_deadlock WHERE id = 1 AND aviso = TRUE) OR i > 200;
    PERFORM pg_sleep(0.1);
    i := i + 1;
  END LOOP;
END $$;

\echo '>>> A (ya con fila 1) intenta fila 2 que B tiene -> forma ciclo:'
SELECT id FROM producto WHERE id = 2 FOR UPDATE;
COMMIT;