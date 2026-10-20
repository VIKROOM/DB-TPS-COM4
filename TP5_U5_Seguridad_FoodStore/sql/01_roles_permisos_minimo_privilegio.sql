-- ============================================================================
-- TP U5 - PARTE A: Roles y permisos con principio de mínimo privilegio
-- Archivo: 01_roles_permisos_minimo_privilegio.sql
-- ============================================================================

-- 1) Roles de grupo
CREATE ROLE rol_app_lectura NOINHERIT;
CREATE ROLE rol_app_escritura NOINHERIT;
CREATE ROLE rol_soporte NOINHERIT;
CREATE ROLE rol_reportes NOINHERIT;

-- 2) Roles de login
CREATE ROLE app_web LOGIN PASSWORD 'cambiar_en_dev' NOINHERIT;
CREATE ROLE admin_datos LOGIN PASSWORD 'cambiar_en_dev' NOINHERIT;

-- 3) Asignación de roles de grupo a roles de login
GRANT rol_app_lectura TO app_web;
GRANT rol_app_escritura TO app_web;
GRANT rol_reportes TO app_web;
GRANT rol_soporte TO admin_datos;
GRANT rol_app_lectura TO admin_datos;

-- 4) Permisos a nivel de esquema
GRANT USAGE ON SCHEMA public TO rol_app_lectura, rol_app_escritura, rol_soporte, rol_reportes;

-- 5) Permisos mínimos por objeto
-- Lectura general acotada
GRANT SELECT ON TABLE categoria, producto, pedido, detalle_pedido TO rol_app_lectura;
GRANT SELECT ON TABLE usuario TO rol_app_lectura; -- solo lectura, se restringirá por columna si aplica

-- Escritura acotada para app
GRANT SELECT, INSERT, UPDATE ON TABLE pedido TO rol_app_escritura;
GRANT SELECT, INSERT, UPDATE ON TABLE detalle_pedido TO rol_app_escritura;
GRANT SELECT ON TABLE producto, categoria, usuario TO rol_app_escritura;

-- Reportes: solo lectura
GRANT SELECT ON TABLE pedido, detalle_pedido, producto, categoria TO rol_reportes;

-- Soporte: permisos a nivel de COLUMNA sobre usuario (mínimo privilegio)
GRANT SELECT (id, nombre, apellido, mail, celular, rol, eliminado, created_at) ON TABLE usuario TO rol_soporte;
GRANT UPDATE (celular) ON TABLE usuario TO rol_soporte;

-- Admin_datos: permisos acotados (sin SUPERUSER). Ajustar según necesidades verificadas
GRANT USAGE, CREATE ON SCHEMA public TO admin_datos;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO admin_datos;
-- Se recomienda NO otorgar DELETE/TRUNCATE masivo sin justificación

-- 6) ALTER DEFAULT PRIVILEGES para heredar política en objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO rol_app_lectura;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE ON TABLES TO rol_app_escritura;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO rol_reportes;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT (id, nombre, apellido, mail, celular, rol, eliminado, created_at), UPDATE (celular) ON TABLES TO rol_soporte;

-- 7) Verificación
-- \du
-- SELECT grantee, table_schema, table_name, privilege_type, column_name
-- FROM information_schema.role_table_grants
-- WHERE grantee IN ('rol_app_lectura','rol_app_escritura','rol_soporte','rol_reportes','app_web','admin_datos')
-- ORDER BY grantee, table_name, privilege_type;
