# Kiro - Design TP U5

## Objetivo
Diseñar un esquema de seguridad verificable para Food Store: roles/permisos (mínimo privilegio), auditoría, simulacro de incidente con análisis crítico, anonimización y verificación de equivalencia.

## Estrategia

### A) Roles y Permisos
1. Crear roles de grupo primero (NOINHERIT donde aplique según criterio).
2. Crear roles de login y asignarlos con GRANT ... TO.
3. Otorgar USAGE sobre schema public.
4. Otorgar privilegios por objeto. Usar privilegios a nivel de columna cuando convenga.
5. Configurar ALTER DEFAULT PRIVILEGES para objetos futuros.
6. Verificar con \du e information_schema.role_table_grants.

### B) Auditoría
1. Activar log_connections, log_disconnections, log_statement='mod' (o nivel que registre modificaciones).
2. Ejecutar secuencia: lectura, inserción, actualización, intento fallido de login.
3. Capturar fragmento de log.
4. Analizar qué queda registrado y qué quedaría fuera (noción pgaudit).

### C) Simulacro de incidente
1. Ejecutar: intentos fallidos contra fn_autenticar -> login exitoso -> lectura masiva de usuario -> intento de escalamiento.
2. Verificar si el intento de escalamiento falla. Si no falla -> hallazgo y corrección obligatoria.
3. Anonimizar log (mails/nombres/PII) antes de enviarlo a IA.
4. Pedir reconstrucción a OpenCode SIN contexto extra.
5. Contrastar: aciertos/omisiones/afirmaciones no sustentadas por log.
6. Decisión de contención tomada por el equipo (documentada).

### D) Anonimización
1. Crear/reutilizar usuario_anon con datos sintéticos deterministas.
2. Verificar equivalencia agregada: conteo por rol, conteo por eliminado. Deben coincidir.

## Medidas de seguridad aplicadas
- Sin SUPERUSER para app_web
- Mínimo privilegio por objeto/columna
- Logs tratados como activo sensible (acceso restringido)
- PII anonimizado antes de compartir con IA
- Validación humana obligatoria ante sugerencias de IA
- Bitácora trazable con al menos un caso de corrección por exceso de privilegio
- Todo ejecutado exclusivamente en entorno de desarrollo