# Declaración de Uso de IA (DUIA) — TP N.º 8

**Asignatura:** Bases de Datos II · Comisión 4
**Integrante:** Facundo Chacón
**Fecha:** 04/11/2026
**Trabajo:** Food Store en la feria — base de la tablet, semáforo de
sincronización y cierre de la capa de datos.

## Herramientas y uso dado

| # | Herramienta | Uso dado | Prompts / specs principales |
|---|---|---|---|
| 1 | OpenCode (CLI) | Análisis de la consigna, diseño del esquema SQLite, redacción del semáforo, generación de scripts de simulación y revisión de código | “Diseñá las cuatro tablas SQLite del TP8 con FK, CHECK y STRICT, precios en centavos”; “Escribí el semáforo que solo evalúa PENDIENTE y clasifica en RECHAZADO, CONFLICTO o SIMULADO_APROBADO”; “Revisá los scripts de U3 y U5 y comprobá cada hallazgo en PostgreSQL” |
| 2 | Kiro | Especificación previa al código: requisitos EARS, diseño y tareas | `docs/kiro/requirements.md`, `docs/kiro/design.md`, `docs/kiro/tasks.md` |
| 3 | PostgreSQL 16 portable (`pgserver`) | Verificación de la vista de instantánea, exportación CSV e invariantes del servidor | `servidor/00_seed_servidor.sql` a `servidor/04_estado_productos.sql` |
| 4 | SQLite 3.37+ (módulo `sqlite3` de Python) | Creación de la base de la tablet, importación de la instantánea y pruebas del semáforo | `movil/schema_sqlite.sql`, `movil/importar_snapshot.sql`, `movil/pruebas_sqlite.sql`, `movil/semaforo.sql` |
| 5 | ReportLab | Generación del PDF del informe | `docs/generar_informe.py` |

## Qué se aceptó

- Estructura de tablas y restricciones (`STRICT`, FK, `CHECK`, centavos).
- Semáforo con prioridad rojo > amarillo > verde y evaluación solo de
  solicitudes `PENDIENTE`.
- Uso de UPSERT para refrescar `producto_cache` sin borrar lápidas.
- Hallazgos H1, H2, H3, H4 y H6 del code review, comprobados en la base.

## Qué se descartó y por qué

- Guardar precios como `REAL`: se usó entero en centavos para evitar errores de
  redondeo.
- Copiar clientes, mails o contraseñas a la tablet: no son necesarios y violan
  la minimización de datos.
- H5 (pedidos huérfanos por consumo de secuencia): se descartó porque la prueba
  mostró 0 huérfanos; `RAISE EXCEPTION` aborta la transacción.
- Presentar `SIMULADO_APROBADO` como venta: el estado es solo una simulación;
  la venta la confirma PostgreSQL.

## Verificación humana

- Cada script fue leído antes de ejecutarse y se ejecutó sobre datos inventados.
- Los resultados se contrastaron con las salidas reales de `evidencias/`, no con
  la respuesta de la IA.
- Los invariantes del servidor se compararon antes y después: pedidos, líneas,
  stock e importe no cambiaron.
- El informe se generó desde las evidencias y se revisó el PDF final.
- No se enviaron a la IA contraseñas, mails ni datos personales reales.
