# TP Unidad 6 - Mantenimiento, respaldo y recuperación de Food Store

**Asignatura:** Bases de Datos II · **Comisión 4** · **Motor:** PostgreSQL 16+ (laboratorio: 17.10)
**Proyecto integrador:** Food Store · **Repositorio:** <https://github.com/VIKROOM/DB-TPS-COM4>

Procedimiento completo de respaldo lógico, monitoreo, mantenimiento y simulacro de recuperación sobre `foodstore`, con evidencias y medición de RPO/RTO.

## Estructura

```
TP6_U6_Mantenimiento_FoodStore/
├── SPEC_U6.md                     Especificación y plan (1 página)
├── backup_foodstore.ps1           Respaldo custom fechado, con log, SHA-256 y retención
├── health_check.sql               4+ controles de salud (tamaño, actividad, tablas, consultas)
├── maintenance.sql                Observación de autovacuum + VACUUM (ANALYZE) justificado
├── restore_test.ps1               Simulacro contra reloj en foodstore_restore_test
├── informe_u6.md / informe_u6.pdf Informe post-incidente (1 página)
├── BITACORA_IA.md                 Uso de IA: propuesta, revisión humana y corrección
├── README.md
├── soporte/
│   ├── 00_preparacion_entorno.sql Esquema mantenimiento.bitacora + vista de compatibilidad
│   ├── 01_roles_mantenimiento.sql Roles de mínimo privilegio (sin contraseñas)
│   ├── 02_simular_actividad.sql   Genera tuplas muertas bajo el umbral de autovacuum
│   ├── setup_pgpass.ps1           Configura contraseñas y pgpass.conf (fuera del repo)
│   ├── conteos_validacion.sql     Snapshot y comparación de conteos (fuente única)
│   ├── validaciones_restauracion.sql Controles manuales post-restauración
│   └── verificar_entrega.ps1      Autoevaluación objetiva de la entrega
├── evidencias/                    Salidas reales de las ejecuciones
├── logs/                          Logs por corrida (fecha, resultado, código de salida)
└── backups/                       Archivos .dump (no se versionan)
```

## Requisitos

- PostgreSQL 16 o superior con `psql`, `pg_dump`, `pg_restore`, `createdb` y `dropdb` en el PATH o en `C:\Program Files\PostgreSQL\<version>\bin`.
- Base `foodstore` creada y poblada (esquema del proyecto + `data.sql`).
- PowerShell 5.1 o superior.
- El archivo `%APPDATA%\postgresql\pgpass.conf` con las credenciales de los roles de mantenimiento. **Nunca** se versiona.

> **Nota de compatibilidad:** el modelo integrador del equipo nombra la tabla `linea_pedido`. El enunciado del TP usa `detalle_pedido`. Para cumplir literalmente las validaciones se crea la vista de compatibilidad `public.detalle_pedido` sobre `linea_pedido` (sin alterar el DDL del modelo). El respaldo incluye la vista y las validaciones funcionan con ambos nombres.

## Preparación (una sola vez)

```powershell
$psql = "C:\Program Files\PostgreSQL\17\bin\psql.exe"

# 1) Roles de mínimo privilegio (sin contraseñas en el archivo)
& $psql -h localhost -U postgres -d foodstore -v ON_ERROR_STOP=1 -f .\soporte\01_roles_mantenimiento.sql

# 2) Esquema de bitácora, grants y vista de compatibilidad
& $psql -h localhost -U postgres -d foodstore -v ON_ERROR_STOP=1 -f .\soporte\00_preparacion_entorno.sql

# 3) Contraseñas de los roles + pgpass.conf (pide la contraseña en consola, no la escribe en el repo)
.\soporte\setup_pgpass.ps1
```

`setup_pgpass.ps1` pide una contraseña de laboratorio para `mant_backup`, `mant_monitor` y `mant_restore`, ejecuta `ALTER ROLE ... PASSWORD` por entrada estándar y escribe `%APPDATA%\postgresql\pgpass.conf` con permisos restringidos al usuario actual. Para automatizar la preparación sin consola interactiva se puede definir `$env:MANT_PASSWORD` solo durante esa ejecución: no se escribe en el repositorio ni queda persistida. Si `PGPASSWORD` está definida (por ejemplo, para la conexión administrativa), el script la elimina antes de verificar `pgpass.conf` porque `PGPASSWORD` tiene prioridad sobre el archivo.

## Ejecución

```powershell
# 1) Respaldo diario (genera backups/*.dump, logs/*.log, snapshot de conteos y SHA-256)
.\backup_foodstore.ps1

# 2) Chequeo de salud (antes y después del mantenimiento)
& $psql -h localhost -U mant_monitor -d foodstore -X -f .\health_check.sql

# 3) Revisión y mantenimiento justificado
& $psql -h localhost -U postgres -d foodstore -X -f .\maintenance.sql

# 4) Simulacro contra reloj (no toca foodstore)
.\restore_test.ps1 -Force
```

Parámetros útiles:

```powershell
.\backup_foodstore.ps1 -Base foodstore -RetencionDias 14 -Destino D:\Respaldos\foodstore
.\restore_test.ps1 -BackupFile .\backups\foodstore_20261102_230000.dump -Force
```

## Qué hace cada script

### `backup_foodstore.ps1`

1. Verifica el entorno y crea `backups/` y `logs/`.
2. Registra un snapshot de conteos **antes** del respaldo (`logs/counts_*.txt`) para comparar luego de restaurar.
3. Ejecuta `pg_dump -Fc -Z 6 -w` sobre `foodstore` con `mant_backup` (sin contraseña en el script).
4. Aborta si `pg_dump` falla; elimina el archivo `.parcial` y registra `ERROR` en el log y en `mantenimiento.bitacora`.
5. Verifica el archivo con `pg_restore --list`, lo renombra (nunca deja un parcial con nombre válido) y calcula SHA-256.
6. Aplica retención solo a archivos propios (`foodstore_YYYYMMDD_HHMMSS.dump*`) más antiguos que N días.
7. Devuelve exit code 0 solo si todo el procedimiento terminó bien.

### `health_check.sql`

Cuatro controles mínimos y complementos: tamaño de la base y de las tablas; conexiones, transacciones, cache hit y sesiones; estado de tablas (tuplas vivas/muertas, autovacuum, ANALYZE, scans); consultas activas y bloqueos; edad de XID y antigüedad del último respaldo OK.

### `maintenance.sql`

Primero observa: parámetros de autovacuum, transacciones largas, tuplas muertas y estadísticas. Luego ejecuta **solo** `VACUUM (ANALYZE)` sobre las tablas que superan el umbral documentado (≥ 5 % de tuplas muertas y ≥ 1.000 filas, o ≥ 10.000 muertas), mediante `\gexec`. Nunca usa `VACUUM FULL`. Deja constancia en `mantenimiento.bitacora`.

### `restore_test.ps1`

1. Toma el último `.dump` (o el indicado) y verifica que `pg_restore --list` lo lea.
2. Verifica que `rolconnlimit` del rol de restauración alcance para `-j 4` (preflight, al menos 7).
3. Si `foodstore_restore_test` existe, solo la recrea con `-Force`; aborta si el destino es `foodstore` o no termina en `_restore_test`.
4. Arranca el cronómetro **inmediatamente antes** de `createdb`.
5. Restaura con `pg_restore --no-owner --no-privileges --exit-on-error -j 4` usando `mant_restore` (`CREATEDB`, sin superusuario). El rol tiene `CONNECTION LIMIT 10` porque `-j 4` necesita el proceso principal más hasta cuatro trabajadores; con un límite menor la restauración falla por conexiones rechazadas (ver `BITACORA_IA.md`).
6. Valida conteos contra el snapshot previo al respaldo, `productos_invalidos = 0`, `detalles_invalidos = 0` y huérfanos = 0.
7. Detiene el cronómetro al terminar las validaciones y registra RTO observado, antigüedad del respaldo (RPO observado), nombre/fecha del respaldo y resultado en `logs/restore_metrics.json`.
8. No elimina la base de prueba: queda disponible para inspección. La limpieza es manual y explícita:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\dropdb.exe" -h localhost -U postgres --if-exists foodstore_restore_test
```

## Resultados de la corrida de laboratorio (2026-11-02)

| Control | Resultado |
|---|---|
| Respaldo | `foodstore_20261102_224500.dump`, 7.338.155 bytes, SHA-256 verificado |
| RTO observado | 4,91 s (objetivo ≤ 20 min) |
| RPO observado | 658 s (10 min 58 s) de antigüedad del respaldo (objetivo ≤ 24 h) |
| Conteos | 7/7 coincidentes con el snapshot previo |
| Integridad lógica | `productos_invalidos = 0`, `detalles_invalidos = 0`, huérfanos = 0 |
| Estructura | 16 restricciones y vista `public.detalle_pedido` restauradas |
| Prueba de falla | `pg_dump` con tabla inexistente: exit 1, log `ERROR` y sin `.dump` válido |

## Evidencias

Las salidas reales de la corrida están en `evidencias/`: log de respaldo, listado del dump, SHA-256, salida de salud antes/después, salida de mantenimiento, log de restauración, validaciones, métricas RPO/RTO y prueba de falla de `pg_dump`.

## Autoevaluación

```powershell
.\soporte\verificar_entrega.ps1
```

Compara la entrega contra la consigna punto por punto (archivos, requisitos de seguridad, consultas mínimas, ausencia de `VACUUM FULL` y de contraseñas, evidencias y métricas). El resultado se guarda en `evidencias/verificacion_entrega.txt`.

## Seguridad

- No se versionan `backups/` ni `pgpass.conf`.
- Los scripts no contienen contraseñas ni las imprimen.
- `foodstore` es la única base protegida contra restauración/destrucción; el simulacro trabaja exclusivamente sobre `foodstore_restore_test`.
- `restore_test.ps1 -Force` es la única operación destructiva y está acotada a la base descartable.
