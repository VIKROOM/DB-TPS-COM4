# Informe TP U5 - Administración y Seguridad de Food Store

**Asignatura:** Base de Datos II  
**Unidad:** 5 - Administración y Seguridad  
**Modalidad:** OpenCode, Kiro y Git  
**Repositorio:** https://github.com/VIKROOM/DB-TPS-COM4.git

## PARTE A. Diseño e implementación de roles y permisos con mínimo privilegio

### A.1 Especificación en Kiro
Se redactaron `kiro/requirements.md` y `kiro/design.md` con roles, justificación por rol, principio de mínimo privilegio y criterios de aceptación.

**Roles definidos:** `rol_app_lectura`, `rol_app_escritura`, `rol_soporte`, `rol_reportes`, `app_web`, `admin_datos`.

### A.2 Implementación (`sql/01_roles_permisos_minimo_privilegio.sql`)
- Creación de roles de grupo y login.
- Asignación con `GRANT ... TO`.
- Permisos por objeto y **permiso a nivel de columna** sobre `usuario` (`SELECT` acotado + `UPDATE(celular)` para `rol_soporte`).
- `ALTER DEFAULT PRIVILEGES` para heredar política en objetos futuros.
- Sin `SUPERUSER` para `app_web`.

### A.3 Verificación
Se verifica con `\du` y con:
```sql
SELECT grantee, table_schema, table_name, privilege_type, column_name
FROM information_schema.role_table_grants
WHERE grantee IN ('rol_app_lectura','rol_app_escritura','rol_soporte','rol_reportes','app_web','admin_datos')
ORDER BY grantee, table_name, privilege_type;
```
Resultado esperado: **ni más, ni menos** que lo previsto en la especificación de Kiro.

### A.4 Auditoría con OpenCode
Se pidió auditoría a OpenCode. Propuso `GRANT ALL ON ALL TABLES...` para `rol_soporte` -> **rechazado y corregido** por validación humana. Registrado en `BITACORA.md`.

## PARTE B. Activación y prueba de la auditoría

### B.1 Configuración
Parámetros activados en entorno de desarrollo:
- `log_connections = on`
- `log_disconnections = on`
- `log_statement = mod` (registra operaciones de modificación)

Documentado en `sql/02_auditoria_configuracion_y_pruebas.sql`.

### B.2 Secuencia de pruebas
Ejecutada: lectura, inserción, actualización e intento fallido de login. Fragmento capturado en `logs/fragmento_log_pruebas_auditoria.txt`.

### B.3 Análisis del log
**Útil:** quién, qué, cuándo, desde dónde, conexiones/desconexiones.  
**Fuera de alcance nativo:** detalle fila por fila (valores old/new), trazabilidad completa por columna/acción con contexto, correlación avanzada -> requiere extensión como **pgaudit**.

### B.4 Log como activo sensible
Sí, el archivo de log es un **activo sensible** (puede contener información de autenticación, IPs, sentencias). Debe poder leerlo **únicamente personal autorizado** con permisos mínimos del SO (lectura restringida) y/o con privilegios acotados del motor. Nunca exponerse públicamente.

## PARTE C. Laboratorio: simulacro de incidente de acceso indebido

### C.1 Simulacro ejecutado (controlado)
Secuencia sobre entorno propio:
1. Varios intentos fallidos contra `fn_autenticar`
2. Inicio de sesión exitoso
3. Lectura masiva de `usuario`
4. Intento de otorgar membresía en `admin_datos` / operación reservada a rol de bajo privilegio

Script: `sql/03_simulacro_incidente_acceso_indebido.sql`

### C.2 Verificación del intento de escalamiento
El intento **falló** con `permission denied` para otorgar membresía/operación reservada. El esquema de permisos se mantuvo conforme al principio de mínimo privilegio.

### C.3 Anonimización del log
Se extrajo el fragmento correspondiente, se reemplazaron mails/nombres/PII por valores sintéticos. Guardado en `logs/log_incidente_anonimizado.txt`.

### C.4 Reconstrucción con OpenCode (sin contexto extra)
Log anonimizado enviado a OpenCode. Respuesta recibida registrada.

### C.5 Contraste IA vs ejecución real
- **Acertó:** identificó intentos fallidos, éxito posterior, lectura masiva e intento de escalamiento.
- **Omitió/infirió:** asumió origen geográfico/fecha con mayor certeza de la que el log sustenta.
- **No sustentado:** algunas inferencias causales no estaban explícitas en el log anonimizado.

### C.6 Decisión de contención (equipo)
Decisión tomada por el equipo con base en evidencia:
- **Bloquear/restringir** sesiones sospechosas
- **Revisar membresías** de roles y privilegios
- **Forzar cambio de credenciales** si aplica
- **Reforzar monitoreo/auditoría**
- **Mantener esquema con mínimo privilegio**

La decisión **no** fue automática, sino validada críticamente contra lo ejecutado.

## PARTE D. Protección de datos personales: anonimización y verificación de equivalencia

### D.1 Creación de usuario_anon
Generada con datos **sintéticos deterministas** (`sql/04_usuario_anon_anonimizacion.sql`):
- `nombre/apellido`: `NombreAnonN/ApellidoAnonN`
- `mail`: `md5(id + salt)@anon.foodstore.test`
- `celular`: sintético
- `contrasena`: `***ANON***`
- Se preservan `id`, `rol`, `eliminado`, `created_at` para análisis agregados

### D.2 Verificación de equivalencia
Ejecutado `sql/05_verificacion_equivalencia_anonimizacion.sql`.  
**Resultado:** conteos por `rol`, por `eliminado` y totales **coinciden exactamente** entre `usuario` y `usuario_anon`. Anonimizar no distorsiona lo que la base tiene para decir en conjunto.

## ENTREGABLES

- `sql/01_roles_permisos_minimo_privilegio.sql`
- `sql/02_auditoria_configuracion_y_pruebas.sql`
- `sql/03_simulacro_incidente_acceso_indebido.sql`
- `sql/04_usuario_anon_anonimizacion.sql`
- `sql/05_verificacion_equivalencia_anonimizacion.sql`
- `kiro/requirements.md`, `kiro/design.md`
- `logs/fragmento_log_pruebas_auditoria.txt`, `logs/log_incidente_anonimizado.txt`
- `BITACORA.md` (trazable, con corrección por exceso de privilegio)
- `informe/Informe_TP_U5_Seguridad_FoodStore.md`
- **ÚNICO PDF:** `TP_U5_Seguridad_FoodStore.pdf`
- Repositorio: https://github.com/VIKROOM/DB-TPS-COM4.git
