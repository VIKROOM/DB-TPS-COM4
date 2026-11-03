# Informe post-incidente — Mantenimiento de Food Store (U6)

**Alumno:** Facundo Chacón · **Comisión 4** · **Motor:** PostgreSQL 17.10
**Base principal:** `foodstore` · **Base de recuperación:** `foodstore_restore_test`
**Repositorio:** <https://github.com/VIKROOM/DB-TPS-COM4>

## Respaldo utilizado

| Dato | Valor |
|---|---|
| Archivo | `foodstore_20261102_224500.dump` (formato custom `-Fc`) |
| Fecha y hora | 2026-11-02, ejecución 22:45:00–22:45:02 |
| Tamaño | 7.338.155 bytes (7,00 MB), 45 objetos en el TOC |
| Integridad | SHA-256 `3EFB2D08…CB286CB3`, verificado antes de restaurar |
| Identidad | `mant_backup` (solo lectura + INSERT en bitácora), sin contraseña en el script |

## RPO y RTO: previsto vs. observado

| Métrica | Previsto | Observado | Cumple |
|---|---|---|---|
| **RPO** (pérdida máxima de datos) | ≤ 24 h (respaldo diario) | **658 s** (10 min 58 s de antigüedad al iniciar el simulacro) | Sí |
| **RTO** (tiempo de recuperación) | ≤ 20 min | **4,91 s** de `createdb` + `pg_restore` + validaciones | Sí |

El RTO se midió con cronómetro desde el instante anterior a `createdb` hasta completar la última validación. El RPO se calculó como la diferencia entre el inicio del simulacro y la fecha del `.dump`.

## Resultados de la validación

Restauración en `foodstore_restore_test` con `mant_restore` (`CREATEDB`, sin superusuario), `pg_restore --no-owner --no-privileges --exit-on-error -j 4`:

- **Conteos coincidentes 7/7** contra el snapshot previo al respaldo: 2 categorías, 20.001 clientes, 50.002 productos, 200.001 pedidos, 400.002 líneas, suma de cantidades 4.202.087 e importe 11.544.138.050,00.
- **`productos_invalidos = 0`**, **`detalles_invalidos = 0`** (precio/stock/cantidad dentro de rango).
- **Huérfanos referenciales = 0** en pedido→cliente y línea→pedido/producto.
- **16 restricciones** declarativas restauradas y vista de compatibilidad `public.detalle_pedido` presente.
- `foodstore` no se tocó en ningún momento: el script aborta si el destino no termina en `_restore_test`.

## Problema real encontrado

La **primera restauración falló** con `FATAL: demasiadas conexiones para el rol "mant_restore"`. El rol tenía `CONNECTION LIMIT 2`, pero `pg_restore -j 4` abre un proceso principal y hasta cuatro trabajadores (5 conexiones). El respaldo era válido: el problema era de configuración de la identidad. Se corrigió con `ALTER ROLE mant_restore CONNECTION LIMIT 10` (idempotente en `01_roles_mantenimiento.sql`) y el simulacro se repitió con éxito. También se corrigió el registro en bitácora del respaldo: `psql` no interpola variables en `-c`, por lo que se pasó a un archivo temporal con `-f`.

## Mejora concreta

La mejora concreta aplicada: se agregó a `restore_test.ps1` un **preflight** que consulta `rolconnlimit` y aborta con un mensaje claro si es menor que `-j + 2` (con `-j 4` exige al menos 7). Así, una configuración insuficiente se detecta antes de crear la base y no a mitad de la restauración. Como paso siguiente, `health_check.sql` debe alertar cuando el último respaldo OK supere las 20 h (margen sobre el RPO de 24 h), para vigilar el RPO antes del incidente.

## Uso de IA (OpenCode) y verificación

OpenCode generó la especificación, los scripts de respaldo/monitoreo/mantenimiento/restauración y este informe. **Nada se aceptó sin ejecutarlo contra el motor real**: se cargó `foodstore` (400.002 líneas), se ejecutaron los cuatro artefactos, la prueba de falla de `pg_dump` (exit 1, sin `.dump` válido) y el simulacro completo. La IA propuso y la ejecución obligó a corregir cuatro errores: variables de `psql` en `-c`, límite de conexiones de `mant_restore`, permisos de rotación de `pgpass.conf` y un `ORDER BY` inválido en el SQL de evidencias. La autoevaluación `soporte/verificar_entrega.ps1` terminó con **todos los controles en PASS**, y las salidas crudas quedaron en `evidencias/` (`restore_metrics.json`, logs, health checks y listado del dump).
