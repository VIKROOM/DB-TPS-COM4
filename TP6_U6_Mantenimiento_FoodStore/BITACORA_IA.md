# BITACORA_IA.md - Uso de OpenCode en el TP U6

Registro de lo que produjo la IA, qué se revisó línea por línea y qué se corrigió antes de aceptarlo. La IA generó una primera versión de la especificación, los scripts y el informe a partir de `SPEC_U6.md` y del material de la Unidad 6; **ninguna propuesta se aceptó sin verificarla contra la consigna y contra el motor real**.

| # | Pedido a OpenCode | Propuesta de la IA | Revisión humana y corrección aplicada |
|---|---|---|---|
| 1 | Generar el respaldo en PowerShell siguiendo la spec. | Script con `PGPASSWORD` embebido y usuario `postgres` para simplificar la conexión. | **RECHAZADO.** Viola la regla de no exponer contraseñas y el mínimo privilegio. Se reemplazó por el rol `mant_backup` (solo lectura) y autenticación vía `pgpass.conf`; el script usa `-w` para fallar en vez de pedir contraseña. |
| 2 | Incluir una tarea de mantenimiento periódica. | `VACUUM FULL` semanal para "recuperar espacio". | **RECHAZADO.** `VACUUM FULL` bloquea la tabla y la consigna lo prohíbe como mantenimiento rutinario. Se reemplazó por `VACUUM (ANALYZE)` condicionado a la observación previa de tuplas muertas, con umbral documentado y registro en bitácora. |
| 3 | Automatizar la restauración de prueba. | `DROP DATABASE foodstore_restore_test` al finalizar, sin confirmación. | **AJUSTADO.** Se eliminó el borrado automático. La única operación destructiva es recrear la base descartable con `-Force`, y el script aborta si el destino es `foodstore` o no termina en `_restore_test`. |
| 4 | Usar las tablas del enunciado (`detalle_pedido`). | Consultas y validaciones literales sobre `detalle_pedido`. | **CORREGIDO.** El esquema real del proyecto usa `linea_pedido`. Se creó la vista de compatibilidad `public.detalle_pedido` sobre `linea_pedido` y se documentó la equivalencia; no se alteró el DDL del modelo. |
| 5 | Detectar la instalación de PostgreSQL. | Ruta fija `C:\Program Files\PostgreSQL\16\bin`. | **CORREGIDO.** El laboratorio tiene PostgreSQL 17.10. El script autodetecta la versión instalada (o recibe `-PgBin`), evitando una dependencia frágil de la ruta. |
| 6 | Ejecutar la restauración con el usuario de referencia `postgres`. | Restaurar como superusuario. | **AJUSTADO.** Se creó `mant_restore` con `CREATEDB` y lectura, sin superusuario. La restauración se probó con ese rol y funcionó porque el dump no requiere extensiones ni ownership especial. |
| 7 | Restaurar más rápido con `pg_restore -j 4`. | `-j 4 --single-transaction`. | **CORREGIDO.** `--single-transaction` es incompatible con `-j`. Se usó `-j 4 --exit-on-error` y se verificó el código de salida. |
| 8 | Redactar el informe post-incidente. | Texto genérico con RPO/RTO "aproximados". | **REEMPLAZADO.** Se exigieron valores observados: fecha/hora del respaldo, antigüedad calculada, cronómetro real, conteos comparados e invalid=0. El informe final usa las métricas de `logs/restore_metrics.json`. |
| 9 | Registrar el resultado del respaldo en `mantenimiento.bitacora`. | `INSERT` con variables `psql` pasadas por `-c`. | **CORREGIDO EN EJECUCIÓN.** `psql` no interpola variables en `-c`; el `INSERT` fallaba y el respaldo quedaba sin registro. Se pasó a un archivo SQL temporal ejecutado con `-f` y se verificó la fila `OK` en la bitácora. |
| 10 | Restaurar en paralelo con `pg_restore -j 4`. | Rol `mant_restore` con `CONNECTION LIMIT 2`. | **CORREGIDO EN EJECUCIÓN.** La primera restauración falló con `FATAL: demasiadas conexiones para el rol "mant_restore"`. `-j 4` necesita 5 conexiones; se elevó el límite a 10 de forma idempotente y el simulacro se repitió con éxito. |
| 11 | Configurar `pgpass.conf` de forma repetible. | `icacls` dejaba el archivo en solo lectura y la segunda rotación fallaba; además `PGPASSWORD` administrativa tenía prioridad sobre el archivo. | **CORREGIDO EN EJECUCIÓN.** Se conserva permiso de escritura del dueño para permitir rotaciones y se elimina `PGPASSWORD` antes de verificar las conexiones con `pgpass.conf`. |
| 12 | Ejecutar el SQL de evidencias post-restauración. | `ORDER BY tabla::text` sobre un alias de salida. | **CORREGIDO EN EJECUCIÓN.** PostgreSQL no acepta un alias con cast en `ORDER BY`; se cambió a `ORDER BY conrelid::regclass::text, contype, conname` y el script de evidencias terminó con exit 0. |

## Verificación aplicada a cada entrega

1. Lectura línea por línea del script contra `SPEC_U6.md`.
2. Prueba manual en el entorno de laboratorio (PostgreSQL 17.10) antes de darlo por válido.
3. Prueba de falla: se ejecutó el respaldo con una tabla inexistente en `-PgDumpExtra` para confirmar que `pg_dump` termina con código ≠ 0, deja log `ERROR`, elimina el `.parcial` y no genera un `.dump` válido.
4. Restauración real en `foodstore_restore_test` y comparación de conteos contra el snapshot previo al respaldo: RTO 4,91 s, RPO 658 s, 7/7 conteos, invalid=0 y huérfanos=0.
5. Ejecución de `soporte/verificar_entrega.ps1` como autoevaluación objetiva contra la consigna.
