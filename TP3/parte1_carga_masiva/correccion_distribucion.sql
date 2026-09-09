-- ============================================================================
-- TP3 · Parte 1 — correccion_distribucion.sql
-- Base: foodstore_tp3 (copia de trabajo) · Motor: PostgreSQL 17.10
-- ============================================================================
-- PROPÓSITO
--   Genera_registros.sql (archivo provisto por la cátedra) carga los VOLÚMENES
--   pedidos (50.000 productos, 20.000 usuarios, 200.000 pedidos, ~622.000
--   detalles) y respeta todas las restricciones (CHECK, UNIQUE, FK), pero la
--   verificación posterior detectó un defecto de distribución:
--
--     * producto.categoria_id  -> los 50.000 productos quedaron en UNA sola
--       categoría (id 2). La consigna pide "distribuidos en las categorías
--       existentes".
--     * pedido.usuario_id      -> los 200.000 pedidos quedaron asignados a UN
--       solo usuario (id 17837).
--     * detalle_pedido.producto_id -> las ~622.000 líneas referencian solo 6
--       productos distintos.
--
--   CAUSA (ver informe_carga.md): las subconsultas no correlacionadas con
--   ORDER BY random() LIMIT n — (SELECT id FROM categoria ORDER BY random()
--   LIMIT 1), (SELECT id FROM usuario ORDER BY random() LIMIT 1) y el
--   CROSS JOIN LATERAL (... ORDER BY random() LIMIT 4) — fueron resueltas por
--   el planificador como InitPlan y evaluadas UNA SOLA VEZ al inicio de la
--   ejecución, no por fila. Las funciones aleatorias del SELECT-list simples
--   (precio, stock, fecha, estado, cantidad) sí se evaluaron por fila.
--
-- CORRECCIÓN
--   Este script redistribuye los datos generados SIN alterar el resto del
--   estado y SIN modificar los datos semilla (usuario/pedido/producto seed con
--   mail que no es @test.com / nombre que no es 'Producto N'):
--     1) productos generados  -> categorías, en forma uniforme (round-robin
--        sobre una permutación aleatoria: distribución exactamente pareja).
--     2) pedidos generados    -> usuarios, en forma uniforme (~10 c/u).
--     3) detalles de los pedidos generados -> se regeneran con 1 a 4 líneas
--        por pedido y productos aleatorios por fila (se elimina la degeneración
--        de 6 productos). Las 2 líneas semilla se conservan.
--   Todo dentro de UNA transacción (protocolo de seguridad: respaldo previo en
--   backups/, copia de trabajo, COMMIT explícito). Termina con ANALYZE para
--   que el optimizador refleje la nueva distribución antes de medir (Parte 2).
--
--   Las randomizaciones por fila usan expresiones en el SELECT-list de CTEs
--   MATERIALIZED (evaluación fila a fila garantizada) y cruces por
--   row_number(), nunca subconsultas volátiles no correlacionadas.
-- ============================================================================

\timing on
BEGIN;

-- ----------------------------------------------------------------------------
-- FIX 1 — producto.categoria_id: distribución uniforme entre categorías.
-- Permutación aleatoria de los productos generados + asignación round-robin
-- por módulo => cantidades exactamente parejas (50.000 / 6 ≈ 8.333-8.334).
-- ----------------------------------------------------------------------------
WITH cats AS MATERIALIZED (
    SELECT id AS categoria_id,
           (row_number() OVER (ORDER BY id) - 1)::int AS crn,
           (count(*)     OVER ())::int               AS n
    FROM categoria
),
shuffled AS MATERIALIZED (
    SELECT p.id AS producto_id,
           ((row_number() OVER (ORDER BY random()) - 1)
             % (SELECT n FROM cats LIMIT 1))::int AS crn
    FROM producto p
    WHERE p.nombre LIKE 'Producto %'          -- solo los generados
)
UPDATE producto p
SET categoria_id = c.categoria_id
FROM shuffled s
JOIN cats c ON c.crn = s.crn
WHERE p.id = s.producto_id;

-- ----------------------------------------------------------------------------
-- FIX 2 — pedido.usuario_id: redistribución uniforme de los pedidos generados
-- entre TODOS los usuarios (~200.000 / 20.003 ≈ 10 pedidos por usuario).
-- El pedido semilla (usuario no @test.com) conserva su dueño original.
-- ----------------------------------------------------------------------------
WITH usrs AS MATERIALIZED (
    SELECT id AS usuario_id,
           (row_number() OVER (ORDER BY id) - 1)::int AS urn,
           (count(*)     OVER ())::int                AS n
    FROM usuario
),
shuffled AS MATERIALIZED (
    SELECT pe.id AS pedido_id,
           ((row_number() OVER (ORDER BY random()) - 1)
             % (SELECT n FROM usrs LIMIT 1))::int AS urn
    FROM pedido pe
    JOIN usuario u ON u.id = pe.usuario_id
    WHERE u.mail LIKE '%@test.com'            -- solo los generados
)
UPDATE pedido pe
SET usuario_id = u.usuario_id
FROM shuffled s
JOIN usrs u ON u.urn = s.urn
WHERE pe.id = s.pedido_id;

-- ----------------------------------------------------------------------------
-- FIX 3 — detalle_pedido: regeneración de las líneas de los pedidos generados.
-- Se borran las ~622.000 líneas degeneradas (solo 6 productos distintos) y se
-- reinsertan con productos aleatorios REALES por fila:
--   * 4 candidatos por pedido (k = 1..4), cada uno con un producto sorteado
--     por fila (random() en el SELECT-list de una CTE MATERIALIZED).
--   * n_lineas estable por pedido (hash determinístico del id, 1..4).
--   * cantidad 1..3 por línea (como el script original).
--   * ON CONFLICT DO NOTHING cubre sorteos duplicados dentro del mismo pedido
--     (PK (pedido_id, producto_id)), igual que el script original.
-- Las 2 líneas semilla no se tocan.
-- ----------------------------------------------------------------------------
DELETE FROM detalle_pedido d
USING pedido pe, usuario u
WHERE d.pedido_id = pe.id
  AND pe.usuario_id = u.id
  AND u.mail LIKE '%@test.com';

WITH nums AS MATERIALIZED (
    SELECT pe.id AS pedido_id,
           (1 + floor(random() * (SELECT count(*) FROM producto)))::bigint AS prod_rn,
           1 + abs(hashtext(pe.id::text)::bigint % 4)                      AS n_lineas,
           ks.k
    FROM pedido pe
    JOIN usuario u ON u.id = pe.usuario_id
    CROSS JOIN generate_series(1, 4) AS ks(k)
    WHERE u.mail LIKE '%@test.com'
),
prods AS MATERIALIZED (
    SELECT id AS producto_id,
           row_number() OVER (ORDER BY id) AS rn
    FROM producto
),
lineas AS (
    SELECT n.pedido_id,
           pr.producto_id,
           n.n_lineas,
           row_number() OVER (PARTITION BY n.pedido_id ORDER BY random()) AS rn
    FROM nums n
    JOIN prods pr ON pr.rn = n.prod_rn
)
INSERT INTO detalle_pedido (pedido_id, producto_id, cantidad)
SELECT l.pedido_id,
       l.producto_id,
       (1 + floor(random() * 3))::int
FROM lineas l
WHERE l.rn <= l.n_lineas
ON CONFLICT (pedido_id, producto_id) DO NOTHING;

COMMIT;

-- ----------------------------------------------------------------------------
-- Estadísticas actualizadas para el optimizador (igual que el script original).
-- ----------------------------------------------------------------------------
ANALYZE producto;
ANALYZE usuario;
ANALYZE pedido;
ANALYZE detalle_pedido;
