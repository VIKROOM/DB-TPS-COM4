-- ============================================================================
-- TP3 · Parte 4 · Spec B — versión alternativa PROPIA del estudiante.
-- Misma pregunta, otra estructura de subconsulta: EXISTS correlacionado.
-- ============================================================================
SELECT u.nombre, u.apellido, u.mail
FROM usuario u
WHERE u.eliminado = FALSE
  AND EXISTS (SELECT 1
              FROM pedido pe
              WHERE pe.usuario_id = u.id      -- correlación con el usuario
                AND pe.estado = 'TERMINADO'
                AND pe.eliminado = FALSE)
ORDER BY u.apellido ASC, u.nombre ASC, u.mail ASC
LIMIT 25;

-- Equivalencia con la versión de la IA:
--   * u.id IN (SELECT usuario_id ...): verdadero sii el id del usuario está en
--     el conjunto de dueños de pedidos TERMINADOS vigentes.
--   * EXISTS (... pe.usuario_id = u.id ...): verdadero sii existe al menos un
--     pedido TERMINADO vigente de ese usuario. Misma condición de pertenencia.
--   * Cuidado teórico: IN y EXISTS difieren si la subconsulta de IN pudiera
--     producir NULL (usuario_id es NOT NULL en el esquema -> no aplica).
--   * Mismo orden determinístico (mail es UNIQUE) -> mismo LIMIT 25.
-- Se verifica formalmente con EXCEPT en verificacion_equivalencia.sql.
