-- ============================================================================
-- TP3 · Parte 4 · Spec A — versión alternativa PROPIA del estudiante.
-- Misma pregunta, otra estructura: subconsulta correlacionada (escalar) en el
-- SELECT-list, sin JOIN ni GROUP BY.
-- ============================================================================
SELECT c.nombre AS nombre_categoria,
       (SELECT COUNT(*)
        FROM producto p
        WHERE p.categoria_id = c.id
          AND p.eliminado = FALSE) AS cantidad_productos
FROM categoria c
WHERE c.eliminado = FALSE
ORDER BY cantidad_productos DESC, nombre_categoria ASC;

-- Equivalencia con la versión de la IA:
--   * LEFT JOIN + COUNT(p.id): cada categoría produce exactamente una fila;
--     el conteo de ids no nulos de producto es 0 si no hubo coincidencias.
--   * Subconsulta escalar: COUNT(*) sobre el conjunto vacío devuelve 0, y una
--     subconsulta escalar con agregado siempre devuelve exactamente una fila,
--     así que ninguna categoría vigente queda excluida.
--   * El orden es idéntico (mismas claves, mismos alias).
-- Se verifica formalmente con EXCEPT en verificacion_equivalencia.sql.
