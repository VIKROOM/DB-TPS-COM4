-- ============================================================================
-- TP3 · Parte 4 — Verificación formal de equivalencia (base foodstore_tp3)
-- Método de la consigna: EXCEPT en ambos sentidos; ambas direcciones deben
-- devolver 0 filas. Se agregan conteos y un caso borde transaccional.
-- ============================================================================

\echo '=== SPEC A: filas en (IA) que no están en (propia) — debe dar 0 filas ==='
(
  SELECT c.nombre AS nombre_categoria, COUNT(p.id) AS cantidad_productos
  FROM categoria c
  LEFT JOIN producto p ON p.categoria_id = c.id AND p.eliminado = FALSE
  WHERE c.eliminado = FALSE
  GROUP BY c.id, c.nombre
)
EXCEPT
(
  SELECT c.nombre,
         (SELECT COUNT(*) FROM producto p
          WHERE p.categoria_id = c.id AND p.eliminado = FALSE)
  FROM categoria c
  WHERE c.eliminado = FALSE
);

\echo '=== SPEC A: filas en (propia) que no están en (IA) — debe dar 0 filas ==='
(
  SELECT c.nombre,
         (SELECT COUNT(*) FROM producto p
          WHERE p.categoria_id = c.id AND p.eliminado = FALSE)
  FROM categoria c
  WHERE c.eliminado = FALSE
)
EXCEPT
(
  SELECT c.nombre AS nombre_categoria, COUNT(p.id) AS cantidad_productos
  FROM categoria c
  LEFT JOIN producto p ON p.categoria_id = c.id AND p.eliminado = FALSE
  WHERE c.eliminado = FALSE
  GROUP BY c.id, c.nombre
);

\echo '=== SPEC A: conteo de filas de cada versión — deben coincidir ==='
SELECT
  (SELECT count(*) FROM (
     SELECT c.nombre, COUNT(p.id)
     FROM categoria c
     LEFT JOIN producto p ON p.categoria_id = c.id AND p.eliminado = FALSE
     WHERE c.eliminado = FALSE
     GROUP BY c.id, c.nombre) ia)          AS filas_version_ia,
  (SELECT count(*) FROM (
     SELECT c.nombre,
            (SELECT COUNT(*) FROM producto p
             WHERE p.categoria_id = c.id AND p.eliminado = FALSE)
     FROM categoria c
     WHERE c.eliminado = FALSE) propia)    AS filas_version_propia;

\echo '=== SPEC A: resultado de ambas versiones (muestra para comparar a ojo) ==='
SELECT 'IA' AS version, c.nombre AS nombre_categoria, COUNT(p.id) AS cantidad_productos
FROM categoria c
LEFT JOIN producto p ON p.categoria_id = c.id AND p.eliminado = FALSE
WHERE c.eliminado = FALSE
GROUP BY c.id, c.nombre
ORDER BY COUNT(p.id) DESC, c.nombre ASC;

SELECT 'propia' AS version, c.nombre AS nombre_categoria,
       (SELECT COUNT(*) FROM producto p
        WHERE p.categoria_id = c.id AND p.eliminado = FALSE) AS cantidad_productos
FROM categoria c
WHERE c.eliminado = FALSE
ORDER BY cantidad_productos DESC, nombre_categoria ASC;

\echo '=== SPEC B: (IA) EXCEPT (propia) — debe dar 0 filas ==='
(
  SELECT u.nombre, u.apellido, u.mail
  FROM usuario u
  WHERE u.eliminado = FALSE
    AND u.id IN (SELECT pe.usuario_id FROM pedido pe
                 WHERE pe.estado = 'TERMINADO' AND pe.eliminado = FALSE)
  ORDER BY u.apellido, u.nombre, u.mail
  LIMIT 25
)
EXCEPT
(
  SELECT u.nombre, u.apellido, u.mail
  FROM usuario u
  WHERE u.eliminado = FALSE
    AND EXISTS (SELECT 1 FROM pedido pe
                WHERE pe.usuario_id = u.id
                  AND pe.estado = 'TERMINADO' AND pe.eliminado = FALSE)
  ORDER BY u.apellido, u.nombre, u.mail
  LIMIT 25
);

\echo '=== SPEC B: (propia) EXCEPT (IA) — debe dar 0 filas ==='
(
  SELECT u.nombre, u.apellido, u.mail
  FROM usuario u
  WHERE u.eliminado = FALSE
    AND EXISTS (SELECT 1 FROM pedido pe
                WHERE pe.usuario_id = u.id
                  AND pe.estado = 'TERMINADO' AND pe.eliminado = FALSE)
  ORDER BY u.apellido, u.nombre, u.mail
  LIMIT 25
)
EXCEPT
(
  SELECT u.nombre, u.apellido, u.mail
  FROM usuario u
  WHERE u.eliminado = FALSE
    AND u.id IN (SELECT pe.usuario_id FROM pedido pe
                 WHERE pe.estado = 'TERMINADO' AND pe.eliminado = FALSE)
  ORDER BY u.apellido, u.nombre, u.mail
  LIMIT 25
);

\echo '=== SPEC B: conteo SIN el LIMIT (universo completo) — deben coincidir ==='
SELECT
  (SELECT count(*) FROM usuario u
   WHERE u.eliminado = FALSE
     AND u.id IN (SELECT pe.usuario_id FROM pedido pe
                  WHERE pe.estado = 'TERMINADO' AND pe.eliminado = FALSE)) AS usuarios_ia,
  (SELECT count(*) FROM usuario u
   WHERE u.eliminado = FALSE
     AND EXISTS (SELECT 1 FROM pedido pe
                 WHERE pe.usuario_id = u.id
                   AND pe.estado = 'TERMINADO' AND pe.eliminado = FALSE))   AS usuarios_propia;

\echo '=== SPEC B: primeras 25 filas según cada versión (muestra) ==='
SELECT 'IA' AS version, u.nombre, u.apellido, u.mail
FROM usuario u
WHERE u.eliminado = FALSE
  AND u.id IN (SELECT pe.usuario_id FROM pedido pe
               WHERE pe.estado = 'TERMINADO' AND pe.eliminado = FALSE)
ORDER BY u.apellido, u.nombre, u.mail
LIMIT 25;

SELECT 'propia' AS version, u.nombre, u.apellido, u.mail
FROM usuario u
WHERE u.eliminado = FALSE
  AND EXISTS (SELECT 1 FROM pedido pe
              WHERE pe.usuario_id = u.id
                AND pe.estado = 'TERMINADO' AND pe.eliminado = FALSE)
ORDER BY u.apellido, u.nombre, u.mail
LIMIT 25;

-- ----------------------------------------------------------------------------
-- CASO BORDE Spec A (transacción con ROLLBACK — no modifica la base):
--   * categoría 4 (Postres)  -> eliminada lógicamente (debe DESAPARECER)
--   * productos de categoría 5 (Ensaladas) -> eliminados lógicamente
--     (la categoría 5 debe aparecer con cantidad_productos = 0)
--   Las dos versiones deben seguir siendo equivalentes (0 filas en ambos
--   EXCEPT) bajo estos datos modificados.
-- ----------------------------------------------------------------------------
BEGIN;

UPDATE categoria SET eliminado = TRUE WHERE id = 4;
UPDATE producto  SET eliminado = TRUE WHERE categoria_id = 5;

\echo '=== CASO BORDE: (IA) EXCEPT (propia) — debe dar 0 filas ==='
(
  SELECT c.nombre, COUNT(p.id)
  FROM categoria c
  LEFT JOIN producto p ON p.categoria_id = c.id AND p.eliminado = FALSE
  WHERE c.eliminado = FALSE
  GROUP BY c.id, c.nombre
)
EXCEPT
(
  SELECT c.nombre,
         (SELECT COUNT(*) FROM producto p
          WHERE p.categoria_id = c.id AND p.eliminado = FALSE)
  FROM categoria c
  WHERE c.eliminado = FALSE
);

\echo '=== CASO BORDE: (propia) EXCEPT (IA) — debe dar 0 filas ==='
(
  SELECT c.nombre,
         (SELECT COUNT(*) FROM producto p
          WHERE p.categoria_id = c.id AND p.eliminado = FALSE)
  FROM categoria c
  WHERE c.eliminado = FALSE
)
EXCEPT
(
  SELECT c.nombre, COUNT(p.id)
  FROM categoria c
  LEFT JOIN producto p ON p.categoria_id = c.id AND p.eliminado = FALSE
  WHERE c.eliminado = FALSE
  GROUP BY c.id, c.nombre
);

\echo '=== CASO BORDE: resultado version propia (Postres no está; Ensaladas = 0) ==='
SELECT c.nombre,
       (SELECT COUNT(*) FROM producto p
        WHERE p.categoria_id = c.id AND p.eliminado = FALSE) AS cantidad_productos
FROM categoria c
WHERE c.eliminado = FALSE
ORDER BY cantidad_productos DESC, c.nombre ASC;

ROLLBACK;

\echo '=== ROLLBACK ejecutado: la base queda intacta (verificación) ==='
SELECT count(*) AS categorias_eliminadas FROM categoria WHERE eliminado = TRUE;
