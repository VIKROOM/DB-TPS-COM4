-- ============================================================================
-- TP U5 - PARTE D: Anonimización de datos personales
-- Archivo: 04_usuario_anon_anonimizacion.sql
-- ============================================================================

-- Crear tabla usuario_anon con datos sintéticos deterministas
DROP TABLE IF EXISTS usuario_anon CASCADE;

CREATE TABLE usuario_anon AS
SELECT 
  id,
  ('NombreAnon' || id) AS nombre,
  ('ApellidoAnon' || id) AS apellido,
  (md5(id::text || 'foodstore_u5_salt') || '@anon.foodstore.test') AS mail,
  ('11' || lpad((abs(hashtextextended(id::text, 12345)) % 90000000)::text, 8, '0')) AS celular,
  '***ANON***' AS contrasena,
  rol,
  eliminado,
  created_at
FROM usuario;

-- Índices opcionales para consultas
CREATE INDEX IF NOT EXISTS idx_usuario_anon_rol ON usuario_anon(rol);
CREATE INDEX IF NOT EXISTS idx_usuario_anon_eliminado ON usuario_anon(eliminado);

-- Verificación básica
SELECT count(*) AS total_usuario FROM usuario;
SELECT count(*) AS total_usuario_anon FROM usuario_anon;
SELECT count(*) AS diff_total FROM (SELECT id FROM usuario EXCEPT SELECT id FROM usuario_anon) x;
