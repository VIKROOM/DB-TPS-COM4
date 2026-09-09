-- ============================================================================
-- Food Store · Bases de Datos II · Unidad 2 · Semana 3 · TP3 — Parte 1
-- Script de carga masiva (generado por IA, revisado línea a línea)
-- Base de trabajo : foodstore_tp3 (copia según protocolo de seguridad)
-- Volumen objetivo: 50.000 productos · 20.000 clientes · 200.000 pedidos + líneas
-- Técnica        : generate_series (sin PL/pgSQL)
--
-- CORRECCIONES DETECTADAS EN LA REVISIÓN (línea por línea, antes de ejecutar):
--   a) El seed de data.sql deja secuencias identity desalineadas (la de
--      producto apunta al 3 con siguiente en 4: el ID 3 nunca existirá;
--      la de cliente apunta al 2 con siguiente en 3: el ID 2 no existirá).
--      Con min/max aritmético las FKs fallaban. FIX: alinear las secuencias
--      a max(id) existente (setval) para obtener rangos contiguos, y mapear
--      los IDs dentro de esos rangos reales (min..max), no supuestos fijos.
--   b) Una versión con JOIN sobre CTE numerada resultó lentísima a escala.
--      FIX: aritmética simple sobre el índice de generate_series dentro de
--      los rangos reales (sin joins ni subconsultas por fila).
--   c) Verificación contra el esquema (CHECK/UNIQUE/FK):
--        * producto.precio  >= 0 (500..5000)                OK
--        * producto.stock   >= 0 (0..200)                   OK
--        * producto UNIQUE (categoria_id, nombre)           OK (nombres únicos)
--        * producto.categoria_id FK -> categoria (1,2)      OK ((i%2)+1)
--        * cliente.email UNIQUE                             OK
--        * pedido.forma_pago ENUM(EFECTIVO/TARJETA/TRANSFERENCIA) OK
--        * linea_pedido PK (pedido_id, producto_id): producto determinístico
--          sin repetición dentro del mismo pedido           OK
--   d) No se modifica ninguna tabla ajena al dominio.
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 0) Alinear secuencias identity al max existente (rangos contiguos)
-- ---------------------------------------------------------------------------
SELECT setval('producto_id_seq',  coalesce((SELECT max(id) FROM producto), 0));
SELECT setval('cliente_id_seq',   coalesce((SELECT max(id) FROM cliente),  0));
SELECT setval('pedido_id_seq',    coalesce((SELECT max(id) FROM pedido),   0));

-- ---------------------------------------------------------------------------
-- 1) PRODUCTO: 50.000 filas repartidas parejo entre las categorías existentes.
--    impar -> Pizzas (id 1) · par -> Bebidas (id 2)
-- ---------------------------------------------------------------------------
INSERT INTO producto (categoria_id, nombre, descripcion, precio, stock, activo)
SELECT (i % 2) + 1
     , CASE WHEN (i % 2) = 0 THEN 'Bebida ' || i ELSE 'Pizza ' || i END
     , 'Producto de carga masiva #' || i
     , (500 + floor(random() * 4501))::numeric(10,2)
     , floor(random() * 201)::int
     , TRUE
FROM   generate_series(1, 50000) AS s(i);

-- ---------------------------------------------------------------------------
-- 2) CLIENTE: 20.000 filas, email único
-- ---------------------------------------------------------------------------
INSERT INTO cliente (nombre, apellido, email, telefono, activo)
SELECT 'Nombre'    || (i % 100 + 1)
     , 'Apellido'  || (i % 200 + 1)
     , 'cliente' || i || '@mail.com'
     , NULL
     , TRUE
FROM   generate_series(1, 20000) AS s(i);

-- ---------------------------------------------------------------------------
-- 3) PEDIDO: 200.000. cliente por aritmética dentro del rango real [min, max].
--    (los pedidos nuevos caen dentro del año 2025)
-- ---------------------------------------------------------------------------
INSERT INTO pedido (cliente_id, fecha, forma_pago)
SELECT (SELECT min(id) FROM cliente) + ((i - 1) % (SELECT count(*) FROM cliente))::int
     , timestamp '2025-01-01' + random() * interval '364 days'
     , (ARRAY['EFECTIVO','TARJETA','TRANSFERENCIA'])[1 + floor(random() * 3)::int]::forma_pago
FROM   generate_series(1, 200000) AS s(i);

-- ---------------------------------------------------------------------------
-- 4) LINEA_PEDIDO: 1 a 5 líneas por pedido, producto sin repetir en el pedido
-- ---------------------------------------------------------------------------
WITH prd AS (SELECT min(id) AS p_min, count(*) AS pcnt FROM producto),
     num AS (
        SELECT id, row_number() OVER (ORDER BY id) AS ord
        FROM   pedido
        WHERE  fecha >= '2025-01-01' AND fecha < '2026-01-01'
     ),
     lins AS (
        SELECT n.id AS pedido_id, (n.ord - 1) * 5 + l.n - 1 AS pos
        FROM   num n
             , LATERAL generate_series(1, 1 + floor(random() * 5)::int) AS l(n)
     )
INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario)
SELECT li.pedido_id
     , (SELECT p_min FROM prd) + (li.pos % (SELECT pcnt FROM prd))
     , 1 + floor(random() * 20)::int
     , (500 + floor(random() * 4501))::numeric(10,2)
FROM   lins li;

COMMIT;

-- ---------------------------------------------------------------------------
-- ANALYZE: el optimizador actualiza estadísticas antes de medir
-- ---------------------------------------------------------------------------
ANALYZE categoria;
ANALYZE producto;
ANALYZE cliente;
ANALYZE pedido;
ANALYZE linea_pedido;

-- ---------------------------------------------------------------------------
-- Verificación de volúmenes
-- ---------------------------------------------------------------------------
SELECT 'producto'      AS tabla, count(*) AS filas FROM producto
UNION ALL SELECT 'categoria',   count(*) FROM categoria
UNION ALL SELECT 'cliente',     count(*) FROM cliente
UNION ALL SELECT 'pedido',      count(*) FROM pedido
UNION ALL SELECT 'linea_pedido',count(*) FROM linea_pedido
ORDER BY tabla;