-- ============================================================================
-- TP U5 - PARTE C: Simulacro de incidente de acceso indebido (SOLO DESARROLLO)
-- Archivo: 03_simulacro_incidente_acceso_indebido.sql
-- ============================================================================

-- IMPORTANTE: Ejecutar ÚNICAMENTE contra instancia propia de Food Store en desarrollo.
-- NO probar contra sistemas de terceros.

-- SECUENCIA REQUERIDA
-- 1) Varios intentos fallidos de inicio de sesión contra fn_autenticar
-- Ejemplo:
-- SELECT fn_autenticar('noexiste@foodstore.test', 'clave_mala') AS r1;
-- SELECT fn_autenticar('noexiste2@foodstore.test', 'clave_mala') AS r2;
-- SELECT fn_autenticar('noexiste3@foodstore.test', 'clave_mala') AS r3;

-- 2) Inicio de sesión exitoso
-- SELECT fn_autenticar('usuario_valido@foodstore.test', 'clave_correcta') AS ok;

-- 3) Lectura masiva de la tabla usuario
-- SELECT * FROM usuario;  -- o COUNT(*) + SELECT con límite para evidencia

-- 4) Intento de otorgarle a un rol de bajo privilegio membresía en admin_datos
-- (o ejecutar operación reservada a admin_datos)
-- Con rol de bajo privilegio:
-- BEGIN;
-- GRANT admin_datos TO <rol_bajo_privilegio>;  -- DEBE FALLAR si esquema correcto
-- ROLLBACK;

-- VERIFICACIÓN
-- Si el GRANT anterior NO falla -> HALLAZGO: esquema de permisos tiene defecto. Corregir Parte A antes de continuar.
-- Documentar resultado en informe de contención.

-- ANONIMIZACIÓN PREVIA A IA
-- Extraer fragmento de log correspondiente a toda la secuencia
-- Reemplazar mails, nombres, hosts/sesiones identificables por valores sintéticos
-- Guardar en logs/log_incidente_anonimizado.txt
-- Enviar SOLO este log anonimizado a OpenCode (sin contexto extra)
-- Contrastar respuesta IA vs ejecución real y documentar en BITACORA.md + informe
