-- ============================================================================
-- Costo de ESCRITURA DESPUES de los nuevos indices (Parte A, paso 5)
-- Misma carga que 03_escritura_antes.sql (1.000 pedidos + 4.000 lineas),
-- dentro de una transaccion deshecha (ROLLBACK).
-- ============================================================================
\timing on

BEGIN;

INSERT INTO pedido (cliente_id, fecha, forma_pago)
SELECT ((i - 1) % 20001) + 1,
       timestamp '2025-01-01' + random() * interval '364 days',
       (ARRAY['EFECTIVO','TARJETA','TRANSFERENCIA'])[1 + floor(random() * 3)::int]::forma_pago
FROM   generate_series(1, 1000) AS s(i);

INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario)
SELECT (SELECT min(id) FROM pedido) + (i - 1),
       1 + ((i * 7) % 50002),
       1 + floor(random() * 20)::int,
       (500 + floor(random() * 4501))::numeric(10,2)
FROM   generate_series(1, 1000) AS s(i);

INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario)
SELECT (SELECT min(id) FROM pedido) + ((i - 1) / 4),
       1 + ((i * 13 + 5) % 50002),
       1 + floor(random() * 20)::int,
       (500 + floor(random() * 4501))::numeric(10,2)
FROM   generate_series(1, 3000) AS s(i);

ROLLBACK;