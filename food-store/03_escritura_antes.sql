-- ============================================================================
-- Costo de ESCRITURA ANTES de los nuevos indices (Parte A, paso 5)
-- Carga: 1.000 pedidos nuevos con ~4 lineas cada uno (aprox. 4.000 INSERTs).
-- Se ejecuta dentro de una transaccion y se deshace (ROLLBACK): no modifica
-- la tabla base de forma permanente (protocolo de seguridad de la catedra).
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