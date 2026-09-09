-- ============================================================================
-- TP3 · Parte 4 · Spec A — versión generada por la IA (OpenCode) a partir de
-- specs.md, sin mostrarle ninguna solución previa.
-- Estructura pedida: JOIN + GROUP BY. Revisada línea a línea por el estudiante.
-- ============================================================================
SELECT c.nombre    AS nombre_categoria,
       COUNT(p.id) AS cantidad_productos
FROM categoria c
LEFT JOIN producto p
       ON p.categoria_id = c.id
      AND p.eliminado = FALSE          -- el filtro de vigencia del producto va
                                       -- en el ON, no en el WHERE: si fuera en
                                       -- el WHERE, una categoría sin productos
                                       -- vigentes quedaría excluida (la fila
                                       -- del LEFT JOIN tendría p.* = NULL y
                                       -- NULL = FALSE no pasa el filtro).
WHERE c.eliminado = FALSE              -- solo categorías vigentes
GROUP BY c.id, c.nombre                -- GROUP BY por id (PK) + nombre:
                                       -- funcionalmente dependiente, válido
                                       -- en PostgreSQL y estable aunque dos
                                       -- categorías tuvieran igual nombre.
ORDER BY COUNT(p.id) DESC, c.nombre ASC;

-- Nota de revisión: COUNT(p.id) y no COUNT(*), porque COUNT(*) contaría 1 en
-- las categorías sin productos vigentes (la fila preservada por el LEFT JOIN)
-- en lugar de 0, violando la spec.
