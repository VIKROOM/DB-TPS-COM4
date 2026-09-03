-- Escenario 2 - Lectura fantasma - SESION B (inserta fila que cumple el WHERE)
SELECT pg_sleep(2);
\echo '>>> SESION B inserta una pizza nueva en categoria 1:'
INSERT INTO producto (categoria_id, nombre, precio, stock) VALUES (1, 'Fugazzeta', 900.00, 10);
SELECT 'SESION B confirmo insercion de Fugazzeta' AS ok;
