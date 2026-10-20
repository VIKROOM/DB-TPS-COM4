-- ============================================================================
-- TP U5 - PARTE D: Verificación de equivalencia tras anonimización
-- Archivo: 05_verificacion_equivalencia_anonimizacion.sql
-- ============================================================================

-- Conteo por rol: deben coincidir exactamente
SELECT rol, count(*) AS cantidad
FROM usuario
GROUP BY rol
ORDER BY rol;

SELECT rol, count(*) AS cantidad
FROM usuario_anon
GROUP BY rol
ORDER BY rol;

-- Distribución por eliminado: deben coincidir exactamente
SELECT eliminado, count(*) AS cantidad
FROM usuario
GROUP BY eliminado
ORDER BY eliminado;

SELECT eliminado, count(*) AS cantidad
FROM usuario_anon
GROUP BY eliminado
ORDER BY eliminado;

-- Totales: deben coincidir
SELECT (SELECT count(*) FROM usuario) AS total_original,
       (SELECT count(*) FROM usuario_anon) AS total_anon,
       (SELECT count(*) FROM usuario) = (SELECT count(*) FROM usuario_anon) AS totales_iguales;
