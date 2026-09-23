-- ============================================================================
-- Food Store - data.sql (heredado, ampliado para la Unidad 3)
-- Base: PostgreSQL 17+ | Resume el seed original de Semana 1 y amplia el
-- volumen con generate_series para que los planes EXPLAIN sean observables.
-- Esquema real del equipo: categoria, producto, cliente, pedido, linea_pedido
-- (el enunciado menciona usuario/detalle_pedido como ejemplo generico; el
-- proyecto de las Semanas 1-4 trabajo las mismas cinco tablas con esos
-- nombres, documentado en el informe).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1) SEED ORIGINAL (Semana 1) ------------------------------------------------
-- ----------------------------------------------------------------------------
INSERT INTO categoria (nombre) VALUES
  ('Pizzas'),
  ('Bebidas');

INSERT INTO producto (categoria_id, nombre, descripcion, precio, stock, activo) VALUES
  (1, 'Muzzarella', 'Pizza clasica de muzzarella', 1050.00, 20, TRUE),
  (2, 'Coca 1.5L',  'Gaseosa de 1.5 litros',       800.00, 50, TRUE);

INSERT INTO cliente (nombre, apellido, email, telefono, activo) VALUES
  ('Ana', 'Gomez', 'ana@mail.com', '1155550001', TRUE);

INSERT INTO pedido (cliente_id, fecha, forma_pago) VALUES
  (1, now(), 'EFECTIVO');

INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario) VALUES
  (1, 1, 2, 1000.00),
  (1, 2, 1,  800.00);

-- ----------------------------------------------------------------------------
-- 2) AMPLIACION DE VOLUMEN (varios miles de filas en pedido/linea_pedido) ----
--    Alinea las secuencias al max existente para rangos contiguos y evita
--    duplicar producto dentro del mismo pedido (PK compuesta).
-- ----------------------------------------------------------------------------
SELECT setval('producto_id_seq', coalesce((SELECT max(id) FROM producto), 0));
SELECT setval('cliente_id_seq',  coalesce((SELECT max(id) FROM cliente),  0));
SELECT setval('pedido_id_seq',   coalesce((SELECT max(id) FROM pedido),   0));

-- 50.000 productos mas, repartidos entre las categorias existentes (1,2)
INSERT INTO producto (categoria_id, nombre, descripcion, precio, stock, activo)
SELECT (i % 2) + 1,
       CASE WHEN (i % 2) = 0 THEN 'Bebida ' || i ELSE 'Pizza ' || i END,
       'Producto de ampliacion #' || i,
       (500 + floor(random() * 4501))::numeric(10,2),
       floor(random() * 201)::int,
       TRUE
FROM generate_series(1, 50000) AS s(i);

-- 20.000 clientes mas, email unico
INSERT INTO cliente (nombre, apellido, email, telefono, activo)
SELECT 'Nombre'   || (i % 100 + 1),
       'Apellido' || (i % 200 + 1),
       'cliente' || i || '@mail.com',
       NULL,
       TRUE
FROM generate_series(1, 20000) AS s(i);

-- 200.000 pedidos en 2025, cliente dentro del rango real [min, max]
INSERT INTO pedido (cliente_id, fecha, forma_pago)
SELECT (SELECT min(id) FROM cliente) + ((i - 1) % (SELECT count(*) FROM cliente))::int,
       timestamp '2025-01-01' + random() * interval '364 days',
       (ARRAY['EFECTIVO','TARJETA','TRANSFERENCIA'])[1 + floor(random() * 3)::int]::forma_pago
FROM generate_series(1, 200000) AS s(i);

-- 1 a 5 lineas por pedido, producto sin repetir en el mismo pedido
WITH prd AS (SELECT min(id) AS p_min, count(*) AS pcnt FROM producto),
     num AS (
        SELECT id, row_number() OVER (ORDER BY id) AS ord
        FROM   pedido
        WHERE  fecha >= '2025-01-01' AND fecha < '2026-01-01'
     ),
     lins AS (
        SELECT n.id AS pedido_id, (n.ord - 1) * 5 + l.n - 1 AS pos
        FROM   num n,
               LATERAL generate_series(1, 1 + floor(random() * 5)::int) AS l(n)
     )
INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario)
SELECT li.pedido_id,
       (SELECT p_min FROM prd) + (li.pos % (SELECT pcnt FROM prd)),
       1 + floor(random() * 20)::int,
       (500 + floor(random() * 4501))::numeric(10,2)
FROM   lins li;

COMMIT;

-- ----------------------------------------------------------------------------
-- 3) ANALYZE para que el optimizador tenga estadisticas frescas --------------
-- ----------------------------------------------------------------------------
ANALYZE categoria;
ANALYZE producto;
ANALYZE cliente;
ANALYZE pedido;
ANALYZE linea_pedido;

-- Verificacion de volumen esperado
SELECT 'categoria'    AS tabla, count(*) AS filas FROM categoria
UNION ALL SELECT 'producto',     count(*) FROM producto
UNION ALL SELECT 'cliente',      count(*) FROM cliente
UNION ALL SELECT 'pedido',       count(*) FROM pedido
UNION ALL SELECT 'linea_pedido', count(*) FROM linea_pedido
ORDER BY tabla;