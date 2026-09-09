-- TP4 Parte 3 - 2 especificaciones con verificación de equivalencia (foodstore_tp3)

-- (a) RANKING: clientes vigentes con al menos un pedido; gasto total y puesto
--     (RANK, los empates comparten puesto y dejan huecos). Orden: puesto, id.

-- V1: función de ventana directamente sobre la agregación
SELECT c.id, c.nombre, c.apellido,
       SUM(lp.cantidad * lp.precio_unitario) AS gasto,
       RANK() OVER (ORDER BY SUM(lp.cantidad * lp.precio_unitario) DESC) AS puesto
FROM   cliente c
JOIN   pedido p        ON p.cliente_id = c.id
JOIN   linea_pedido lp ON lp.pedido_id = p.id
WHERE  c.activo = TRUE
GROUP  BY c.id, c.nombre, c.apellido
ORDER  BY puesto, c.id;

-- V2: estructura distinta (ROW_NUMBER + MIN de ventana en vez de RANK):
--     rango = posicion de la PRIMERA fila del grupo de empate.
WITH gastos AS (
    SELECT c.id, c.nombre, c.apellido,
           SUM(lp.cantidad * lp.precio_unitario) AS gasto
    FROM   cliente c
    JOIN   pedido p        ON p.cliente_id = c.id
    JOIN   linea_pedido lp ON lp.pedido_id = p.id
    WHERE  c.activo = TRUE
    GROUP  BY c.id, c.nombre, c.apellido
),
r AS (
    SELECT g.id, g.nombre, g.apellido, g.gasto,
           ROW_NUMBER() OVER (ORDER BY g.gasto DESC, g.id) AS rn
    FROM   gastos g
)
SELECT r.id, r.nombre, r.apellido, r.gasto,
       MIN(r.rn) OVER (PARTITION BY r.gasto) AS puesto
FROM   r
ORDER  BY puesto, r.id;

-- (b) SUBCONSULTA CORRELACIONADA: para cada pedido del cliente 6 que tiene al
--     menos una linea de pedido, devolver id, fecha y total del pedido
--     (suma de cantidad x precio_unitario). Orden: fecha, id.
--     La especificacion fija el filtro "al menos una línea" porque una
--     subconsulta escalar correlacionada devolveria el pedido aunque no tenga
--     lineas (total NULL), mientras que el join + GROUP BY no (trampa que la
--     propia practica advierte).

-- V1: subconsulta escalar correlacionada (con EXISTS para fijar la semantica)
SELECT p.id, p.fecha,
       (SELECT SUM(lp.cantidad * lp.precio_unitario)
        FROM   linea_pedido lp
        WHERE  lp.pedido_id = p.id) AS total
FROM   pedido p
WHERE  p.cliente_id = 6
  AND  EXISTS (SELECT 1 FROM linea_pedido lp WHERE lp.pedido_id = p.id)
ORDER  BY p.fecha, p.id;

-- V2: estructura distinta (join + agregacion + GROUP BY)
SELECT p.id, p.fecha,
       SUM(lp.cantidad * lp.precio_unitario) AS total
FROM   pedido p
JOIN   linea_pedido lp ON lp.pedido_id = p.id
WHERE  p.cliente_id = 6
GROUP  BY p.id, p.fecha
ORDER  BY p.fecha, p.id;

-- ============================ VERIFICACIÓN ============================
-- (a) Ranking: diferencias V1 vs V2
SELECT count(*) AS dif_a_V1_menos_V2 FROM (
  ( SELECT c.id, c.nombre, c.apellido,
           SUM(lp.cantidad * lp.precio_unitario) AS gasto,
           RANK() OVER (ORDER BY SUM(lp.cantidad * lp.precio_unitario) DESC) AS puesto
    FROM cliente c JOIN pedido p ON p.cliente_id = c.id
                   JOIN linea_pedido lp ON lp.pedido_id = p.id
    WHERE c.activo = TRUE GROUP BY c.id, c.nombre, c.apellido )
  EXCEPT
  ( WITH gastos AS (
        SELECT c.id, c.nombre, c.apellido,
               SUM(lp.cantidad * lp.precio_unitario) AS gasto
        FROM cliente c JOIN pedido p ON p.cliente_id = c.id
                       JOIN linea_pedido lp ON lp.pedido_id = p.id
        WHERE c.activo = TRUE GROUP BY c.id, c.nombre, c.apellido ),
        r AS (
        SELECT g.id, g.nombre, g.apellido, g.gasto,
               ROW_NUMBER() OVER (ORDER BY g.gasto DESC, g.id) AS rn
        FROM gastos g )
    SELECT r.id, r.nombre, r.apellido, r.gasto,
           MIN(r.rn) OVER (PARTITION BY r.gasto) AS puesto
    FROM r )
) d;

SELECT count(*) AS dif_a_V2_menos_V1 FROM (
  ( WITH gastos AS (
        SELECT c.id, c.nombre, c.apellido,
               SUM(lp.cantidad * lp.precio_unitario) AS gasto
        FROM cliente c JOIN pedido p ON p.cliente_id = c.id
                       JOIN linea_pedido lp ON lp.pedido_id = p.id
        WHERE c.activo = TRUE GROUP BY c.id, c.nombre, c.apellido ),
        r AS (
        SELECT g.id, g.nombre, g.apellido, g.gasto,
               ROW_NUMBER() OVER (ORDER BY g.gasto DESC, g.id) AS rn
        FROM gastos g )
    SELECT r.id, r.nombre, r.apellido, r.gasto,
           MIN(r.rn) OVER (PARTITION BY r.gasto) AS puesto
    FROM r )
  EXCEPT
  ( SELECT c.id, c.nombre, c.apellido,
           SUM(lp.cantidad * lp.precio_unitario) AS gasto,
           RANK() OVER (ORDER BY SUM(lp.cantidad * lp.precio_unitario) DESC) AS puesto
    FROM cliente c JOIN pedido p ON p.cliente_id = c.id
                   JOIN linea_pedido lp ON lp.pedido_id = p.id
    WHERE c.activo = TRUE GROUP BY c.id, c.nombre, c.apellido )
) d;

-- (b) Total por pedido del cliente 6: diferencias V1 vs V2
SELECT count(*) AS dif_b_V1_menos_V2 FROM (
  ( SELECT p.id, p.fecha,
           (SELECT SUM(lp.cantidad * lp.precio_unitario)
            FROM linea_pedido lp WHERE lp.pedido_id = p.id) AS total
    FROM pedido p
    WHERE p.cliente_id = 6
      AND EXISTS (SELECT 1 FROM linea_pedido lp WHERE lp.pedido_id = p.id) )
  EXCEPT
  ( SELECT p.id, p.fecha, SUM(lp.cantidad * lp.precio_unitario) AS total
    FROM pedido p JOIN linea_pedido lp ON lp.pedido_id = p.id
    WHERE p.cliente_id = 6 GROUP BY p.id, p.fecha )
) d;

SELECT count(*) AS dif_b_V2_menos_V1 FROM (
  ( SELECT p.id, p.fecha, SUM(lp.cantidad * lp.precio_unitario) AS total
    FROM pedido p JOIN linea_pedido lp ON lp.pedido_id = p.id
    WHERE p.cliente_id = 6 GROUP BY p.id, p.fecha )
  EXCEPT
  ( SELECT p.id, p.fecha,
           (SELECT SUM(lp.cantidad * lp.precio_unitario)
            FROM linea_pedido lp WHERE lp.pedido_id = p.id) AS total
    FROM pedido p
    WHERE p.cliente_id = 6
      AND EXISTS (SELECT 1 FROM linea_pedido lp WHERE lp.pedido_id = p.id) )
) d;