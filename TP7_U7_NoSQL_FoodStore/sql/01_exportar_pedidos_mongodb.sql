-- ============================================================================
-- TP Unidad 7 - Food Store NoSQL
-- Exporta el subconjunto "pedidos y detalle" de PostgreSQL a un script de
-- carga para mongosh: mongodb/02_datos_pedidos.js
--
-- Uso (desde la raiz de TP7_U7_NoSQL_FoodStore):
--   psql -U postgres -h localhost -d foodstore -v ON_ERROR_STOP=1 ^
--        -f sql/01_exportar_pedidos_mongodb.sql
--
-- Decisiones de la extraccion:
--   * Se migran los pedidos 1 a 12 de foodstore (12 pedidos, 24 lineas).
--   * Se conservan pedido_id, cliente_id y producto_id de origen.
--   * Se copian nombre de cliente, nombre/categoria de producto y
--     precio_unitario como instantanea historica de la operacion.
--   * No se copian email ni telefono del cliente (minimizacion de datos).
--   * fecha se convierte a UTC (ISODate) y los importes a Decimal128.
--   * estado: el esquema real de Food Store NO tiene columna de estado de
--     pedido. Para poder cumplir la consigna 4.b se define una regla de
--     derivacion explicita y reproducible, aplicada igual en ambos motores:
--         fecha_corte = max(fecha del lote) + 1 dia
--         TERMINADO   si fecha <= fecha_corte - 30 dias
--         PENDIENTE   en caso contrario
--     La fecha de corte depende solo de los datos migrados (no del reloj),
--     por lo que la extraccion y la comparacion son reproducibles.
--     La regla queda documentada en el informe y en mongodb/00_metadata.js.
-- ============================================================================

\encoding UTF8
\set ON_ERROR_STOP on
\pset format unaligned
\pset tuples_only on
\o mongodb/02_datos_pedidos.js

WITH corte AS (
    SELECT max(fecha) + interval '1 day' AS fecha_corte
    FROM pedido
    WHERE id BETWEEN 1 AND 12
),
base AS (
    SELECT p.id                          AS pedido_id,
           p.fecha,
           CASE
               WHEN p.fecha <= c.fecha_corte - interval '30 days' THEN 'TERMINADO'
               ELSE 'PENDIENTE'
           END                           AS estado,
           p.forma_pago::text            AS forma_pago,
           c2.id                         AS cliente_id,
           c2.nombre || ' ' || c2.apellido AS cliente_nombre
    FROM pedido p
    CROSS JOIN corte c
    JOIN cliente c2 ON c2.id = p.cliente_id
    WHERE p.id BETWEEN 1 AND 12
),
lineas AS (
    SELECT lp.pedido_id,
           lp.producto_id,
           pr.nombre                    AS producto_nombre,
           cat.nombre                   AS categoria_nombre,
           lp.cantidad,
           lp.precio_unitario,
           round(lp.cantidad * lp.precio_unitario, 2) AS subtotal
    FROM linea_pedido lp
    JOIN producto  pr  ON pr.id  = lp.producto_id
    JOIN categoria cat ON cat.id = pr.categoria_id
    WHERE lp.pedido_id BETWEEN 1 AND 12
),
items AS (
    SELECT l.pedido_id,
           string_agg(
               format('      { producto_id: %s, nombre: "%s", categoria: "%s", cantidad: %s, precio_unitario: NumberDecimal("%s"), subtotal: NumberDecimal("%s") }',
                      l.producto_id,
                      replace(l.producto_nombre,   '"', '\"'),
                      replace(l.categoria_nombre,  '"', '\"'),
                      l.cantidad,
                      to_char(l.precio_unitario, 'FM9999999990.00'),
                      to_char(l.subtotal,        'FM9999999990.00')),
               E',\n' ORDER BY l.producto_id
           ) AS items_js,
           count(*)      AS items_count,
           sum(l.subtotal) AS total
    FROM lineas l
    GROUP BY l.pedido_id
),
documentos AS (
    SELECT format(
               E'  {\n    pedido_id: %s,\n    fecha: ISODate("%s"),\n    estado: "%s",\n    forma_pago: "%s",\n    cliente: { cliente_id: %s, nombre: "%s" },\n    items: [\n%s\n    ],\n    items_count: %s,\n    total: NumberDecimal("%s")\n  }',
               b.pedido_id,
               to_char(b.fecha AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
               b.estado,
               b.forma_pago,
               b.cliente_id,
               replace(b.cliente_nombre, '"', '\"'),
               i.items_js,
               i.items_count,
               to_char(i.total, 'FM9999999990.00')
           ) AS doc,
           b.pedido_id
    FROM base b
    JOIN items i ON i.pedido_id = b.pedido_id
)
SELECT E'// ============================================================================\n// ARCHIVO GENERADO AUTOMATICAMENTE POR sql/01_exportar_pedidos_mongodb.sql\n// Fuente: PostgreSQL 17 / base foodstore / pedidos 1 a 12\n// No editar a mano: volver a ejecutar la extraccion.\n// ============================================================================\n\n' ||
       'db.pedidos.insertMany([' || E'\n' ||
       string_agg(doc, E',\n' ORDER BY pedido_id) ||
       E'\n]);\n' ||
       'print("Documentos en pedidos: " + db.pedidos.countDocuments());' AS script
FROM documentos;

\o

\pset format aligned
\pset tuples_only off
\echo ''
\echo '=== Resumen de la extraccion (mismo subconjunto que se migro) ==='
SELECT count(*)                                     AS pedidos,
       (SELECT count(*) FROM linea_pedido WHERE pedido_id BETWEEN 1 AND 12) AS lineas,
       (SELECT sum(lp.cantidad * lp.precio_unitario)
          FROM linea_pedido lp WHERE lp.pedido_id BETWEEN 1 AND 12)          AS importe_total
FROM pedido
WHERE id BETWEEN 1 AND 12;
