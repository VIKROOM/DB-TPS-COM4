-- TP3 Parte 4 - Consultas bajo especificacion precisa + verificacion EXCEPT
-- Base: foodstore_tp3

-- =====================================================================
-- SPEC A (resumen) : "Para cada categoría vigente (activo = TRUE), el
--   nombre de la categoría y la cantidad de productos VIGENTES (activo =
--   TRUE) que tiene, incluyendo las categorías sin productos vigentes con
--   cantidad 0. Ordená de mayor a menor cantidad. Sin SELECT *."
-- Tablas: categoria, producto | Filtro baja lógica en ambas.
-- =====================================================================

-- V1_A (SQL generado por IA): LEFT JOIN + COUNT
CREATE OR REPLACE VIEW v_specA_v1 AS
SELECT c.nombre, COUNT(p.id) AS cantidad_productos
FROM   categoria c
LEFT JOIN producto p ON p.categoria_id = c.id AND p.activo = TRUE
WHERE  c.activo = TRUE
GROUP  BY c.id, c.nombre
ORDER  BY cantidad_productos DESC, c.nombre;

-- V2_A (alternativa propia): subconsulta correlacionada
CREATE OR REPLACE VIEW v_specA_v2 AS
SELECT c.nombre,
       (SELECT COUNT(*) FROM producto p
        WHERE p.categoria_id = c.id AND p.activo = TRUE) AS cantidad_productos
FROM   categoria c
WHERE  c.activo = TRUE
ORDER  BY cantidad_productos DESC, c.nombre;

-- Verificación A: ambas direcciones de EXCEPT deben dar 0 filas
SELECT 'A: filas en V1 no en V2' AS chequeo, COUNT(*) AS filas FROM (SELECT * FROM v_specA_v1 EXCEPT SELECT * FROM v_specA_v2) t;
SELECT 'A: filas en V2 no en V1' AS chequeo, COUNT(*) AS filas FROM (SELECT * FROM v_specA_v2 EXCEPT SELECT * FROM v_specA_v1) t;
SELECT * FROM v_specA_v1;

-- =====================================================================
-- SPEC B (subconsulta) : "Devolver los clientes VIGENTES (activo = TRUE)
--   cuyo gasto total (Σ cantidad x precio_unitario en linea_pedido)
--   supera el gasto promedio de los clientes vigentes (incluyendo los que
--   no tienen pedidos, con gasto 0). Columnas: id, nombre, apellido,
--   gasto_total. Orden: gasto_total DESC, id ASC. Tablas: cliente,
--   pedido, linea_pedido."
-- =====================================================================

-- V1_B (SQL generado por IA): agregacion + subconsulta en HAVING
CREATE OR REPLACE VIEW v_specB_v1 AS
SELECT c.id, c.nombre, c.apellido,
       COALESCE(SUM(lp.cantidad * lp.precio_unitario), 0) AS gasto_total
FROM   cliente c
LEFT JOIN pedido p        ON p.cliente_id = c.id
LEFT JOIN linea_pedido lp ON lp.pedido_id = p.id
WHERE  c.activo = TRUE
GROUP  BY c.id, c.nombre, c.apellido
HAVING COALESCE(SUM(lp.cantidad * lp.precio_unitario), 0) > (
          SELECT AVG(g) FROM (
              SELECT COALESCE(SUM(lp2.cantidad * lp2.precio_unitario), 0) AS g
              FROM   cliente c2
              LEFT JOIN pedido p2        ON p2.cliente_id = c2.id
              LEFT JOIN linea_pedido lp2 ON lp2.pedido_id = p2.id
              WHERE  c2.activo = TRUE
              GROUP  BY c2.id
          ) AS t)
ORDER  BY gasto_total DESC, c.id;

-- V2_B (alternativa propia): CTE + JOIN
CREATE OR REPLACE VIEW v_specB_v2 AS
WITH gastos AS (
    SELECT c.id, c.nombre, c.apellido,
           COALESCE(SUM(lp.cantidad * lp.precio_unitario), 0) AS gasto_total
    FROM   cliente c
    LEFT JOIN pedido p        ON p.cliente_id = c.id
    LEFT JOIN linea_pedido lp ON lp.pedido_id = p.id
    WHERE  c.activo = TRUE
    GROUP  BY c.id, c.nombre, c.apellido
)
SELECT g.*
FROM   gastos g
WHERE  g.gasto_total > (SELECT AVG(gasto_total) FROM gastos)
ORDER  BY g.gasto_total DESC, g.id;

-- Verificación B: ambas direcciones de EXCEPT deben dar 0 filas
SELECT 'B: filas en V1 no en V2' AS chequeo, COUNT(*) AS filas FROM (SELECT * FROM v_specB_v1 EXCEPT SELECT * FROM v_specB_v2) t;
SELECT 'B: filas en V2 no en V1' AS chequeo, COUNT(*) AS filas FROM (SELECT * FROM v_specB_v2 EXCEPT SELECT * FROM v_specB_v1) t;
SELECT COUNT(*) AS total_clientes_sobre_promedio FROM v_specB_v1;