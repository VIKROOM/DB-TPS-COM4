-- ============================================================================
-- TP3 · Parte 4 · Spec B — versión generada por la IA (OpenCode) a partir de
-- specs.md, sin mostrarle ninguna solución previa.
-- Estructura: subconsulta IN (no correlacionada).
-- ============================================================================
SELECT u.nombre, u.apellido, u.mail
FROM usuario u
WHERE u.eliminado = FALSE
  AND u.id IN (SELECT pe.usuario_id
               FROM pedido pe
               WHERE pe.estado = 'TERMINADO'
                 AND pe.eliminado = FALSE)
ORDER BY u.apellido ASC, u.nombre ASC, u.mail ASC
LIMIT 25;

-- Nota de revisión: el IN no duplica filas (semántica de conjuntos: cada
-- usuario se evalúa una vez contra el conjunto de ids), cumple el "una sola
-- vez" de la spec sin necesidad de DISTINCT.
