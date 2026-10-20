-- ============================================================================
-- TP U5 - PARTE B: Activación y prueba de auditoría
-- Archivo: 02_auditoria_configuracion_y_pruebas.sql
-- ============================================================================

-- 1) CONFIGURACIÓN DEL SERVIDOR (documentar en informe)
-- En postgresql.conf o con ALTER SYSTEM (entorno de desarrollo):
-- ALTER SYSTEM SET log_connections = 'on';
-- ALTER SYSTEM SET log_disconnections = 'on';
-- ALTER SYSTEM SET log_statement = 'mod';  -- registra DDL/DML
-- SELECT pg_reload_conf();

-- Valores mínimos requeridos:
-- log_connections = on
-- log_disconnections = on
-- log_statement = mod (al menos registra operaciones de modificación)

-- 2) SECUENCIA DE PRUEBAS
-- Conectar con distintos roles/sesiones y ejecutar:

-- a) Lectura
SELECT count(*) FROM producto WHERE eliminado = FALSE;

-- b) Inserción (ejemplo controlado - ajustar a datos válidos)
-- BEGIN;
-- INSERT INTO categoria(nombre, descripcion) VALUES ('CAT_AUDIT_TEST','PRUEBA AUDITORIA') ON CONFLICT DO NOTHING;
-- COMMIT;

-- c) Actualización
-- BEGIN;
-- UPDATE producto SET descripcion = COALESCE(descripcion,'') WHERE id = (SELECT id FROM producto LIMIT 1);
-- COMMIT;

-- d) Intento de inicio de sesión fallido
-- Simular desde cliente/psql con credenciales incorrectas contra fn_autenticar o conexión directa.
-- Registrar fragmento de log resultante en logs/fragmento_log_pruebas_auditoria.txt

-- 3) ANÁLISIS (para informe)
-- Útil para auditoría: quién (usuario/rol), qué (sentencia), cuándo (timestamp), desde dónde (host/puerto), conexión/desconexión.
-- Fuera de alcance nativo (noción): detalle fila por fila con valores antiguos/nuevos, usuario que realmente ejecutó acción
-- heredada, trazabilidad por objeto/columna con contexto completo -> pgaudit permite mayor granularidad.
