-- ============================================================================
-- TP3 · Parte 1 — Verificación posterior a la carga masiva (Genera_registros.sql)
-- Base: foodstore_tp3 (copia de trabajo creada desde plantilla `foodstore`)
-- Motor: PostgreSQL 17.10 · Cliente: psql
-- Se ejecuta DESPUÉS del COMMIT del script de carga. Todas las verificaciones
-- deben cumplir la condición indicada en el comentario de cada bloque.
-- ============================================================================

\timing on

-- 1) Conteos mínimos exigidos por la consigna:
--    >= 50.000 productos, >= 20.000 usuarios, >= 200.000 pedidos con detalles.
SELECT 'categoria'     AS tabla, count(*) AS filas FROM categoria
UNION ALL SELECT 'producto',       count(*) FROM producto
UNION ALL SELECT 'usuario',        count(*) FROM usuario
UNION ALL SELECT 'pedido',         count(*) FROM pedido
UNION ALL SELECT 'detalle_pedido', count(*) FROM detalle_pedido
ORDER BY tabla;

-- 2) Productos generados distribuidos entre TODAS las categorías existentes
--    (el script asigna categoría al azar; ninguna categoría debe quedar vacía).
SELECT c.id, c.nombre, count(p.id) AS productos
FROM categoria c
LEFT JOIN producto p ON p.categoria_id = c.id
GROUP BY c.id, c.nombre
ORDER BY c.id;

-- 3) Rangos exigidos en los productos generados: precio entre 500 y 5000,
--    stock entre 0 y 200. Debe devolver 0 filas fuera de rango.
SELECT count(*) AS fuera_de_rango
FROM producto
WHERE nombre LIKE 'Producto %'
  AND (precio NOT BETWEEN 500 AND 5000 OR stock NOT BETWEEN 0 AND 200);

-- 4) Integridad referencial: no deben existir huérfanos (0 en las 3 columnas).
SELECT
  (SELECT count(*) FROM producto p
     LEFT JOIN categoria c ON c.id = p.categoria_id
     WHERE c.id IS NULL)                          AS productos_sin_categoria,
  (SELECT count(*) FROM pedido pe
     LEFT JOIN usuario u ON u.id = pe.usuario_id
     WHERE u.id IS NULL)                          AS pedidos_sin_usuario,
  (SELECT count(*) FROM detalle_pedido d
     LEFT JOIN pedido pe ON pe.id = d.pedido_id
     WHERE pe.id IS NULL)                         AS detalles_sin_pedido,
  (SELECT count(*) FROM detalle_pedido d
     LEFT JOIN producto p ON p.id = d.producto_id
     WHERE p.id IS NULL)                          AS detalles_sin_producto;

-- 5) UNIQUE de usuario.mail: la cantidad de mails distintos debe igualar el
--    total de usuarios (0 duplicados).
SELECT count(*) AS total_usuarios,
       count(DISTINCT mail) AS mails_distintos,
       count(*) - count(DISTINCT mail) AS duplicados
FROM usuario;

-- 6) CHECK detalle_pedido.cantidad > 0 y líneas por pedido entre 1 y 4.
SELECT count(*) AS detalles_cantidad_invalida
FROM detalle_pedido WHERE cantidad <= 0 OR cantidad > 4;

SELECT min(lineas) AS min_lineas_por_pedido,
       max(lineas) AS max_lineas_por_pedido,
       round(avg(lineas), 2) AS promedio_lineas
FROM (SELECT pedido_id, count(*) AS lineas
      FROM detalle_pedido GROUP BY pedido_id) l;

-- 7) Distribución de estado y forma_pago en los pedidos generados
--    (debe cubrir los 4 estados y las 3 formas de pago del ENUM).
SELECT estado, forma_pago, count(*)
FROM pedido
GROUP BY estado, forma_pago
ORDER BY estado, forma_pago;

-- 8) Fechas de pedido dentro del último año (el script usa
--    CURRENT_DATE - (random()*365)::int).
SELECT min(fecha) AS fecha_min, max(fecha) AS fecha_max
FROM pedido;

-- 9) El script terminó con ANALYZE: las estadísticas deben estar actualizadas
--    (last_analyze no nulo en las 4 tablas).
SELECT relname, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE relname IN ('producto','usuario','pedido','detalle_pedido')
ORDER BY relname;

-- 10) La base de producción `foodstore` NO fue tocada: este script corre solo
--     sobre foodstore_tp3. (Verificación manual: psql -d foodstore -c
--     "SELECT count(*) FROM producto;" debe seguir devolviendo 3.)
