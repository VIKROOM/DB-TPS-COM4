# Kiro · Requirements — TP Unidad 4 (FNBC y desnormalización controlada)

## Alcance

Refactorizar el esquema heredado `control_lote_almacen` hasta la Forma Normal
de Boyce-Codd (FNBC), migrar sus datos sin pérdida dentro de una transacción
reversible y documentar una desnormalización controlada para el Top 5 de
categorías. El alcance no incluye cambios al modelo transaccional de Food
Store ni a la interfaz de la aplicación.

## Requisitos en notación EARS

### REQ-01 — Detección de la violación de FNBC

- **WHEN** se analiza
  `control_lote_almacen(lote_id, deposito_id, responsable_control_id)` con las
  dependencias funcionales reales
  `DF1: {lote_id, deposito_id} → {responsable_control_id}` y
  `DF2: {responsable_control_id} → {deposito_id}`
- **THE SYSTEM SHALL** identificar que `DF2` tiene un determinante que no es
  superclave y concluir que la relación **no** está en FNBC.
- **Se prueba con:** `informe/Informe_TP_U4_FNBC_Desnormalizacion_FoodStore.md`
  (partes a–d) y `sql/tp_fnbc_control_lote.sql`.

### REQ-02 — Descomposición sin pérdida

- **WHEN** se refactoriza el esquema
- **THE SYSTEM SHALL** crear:
  - `responsable_deposito(responsable_control_id PK, deposito_id)`;
  - `control_lote(lote_id, responsable_control_id PK, FK a
    responsable_deposito)`;
  - la vista de compatibilidad `v_control_lote_almacen` que reconstruya
    `(lote_id, deposito_id, responsable_control_id)` mediante `JOIN`.
- **Se prueba con:** `sql/tp_fnbc_control_lote.sql` y la consulta de
  equivalencia (debe devolver 0 filas).

### REQ-03 — Migración sin pérdida

- **WHEN** se migran los datos de `control_lote_almacen`
- **THE SYSTEM SHALL** copiar todas las filas sin perder ni duplicar:
  - un registro por `responsable_control_id` en `responsable_deposito`;
  - un registro por `(lote_id, responsable_control_id)` en `control_lote`.
- **THE SYSTEM SHALL** comparar la vista de compatibilidad contra la tabla
  original y abortar si la consulta de diferencias devuelve alguna fila.
- **Se prueba con:** `sql/tp_fnbc_control_lote_migracion_segura.sql`.

### REQ-04 — Transacción reversible y plan de reversión

- **WHEN** se ejecuta la migración
- **THE SYSTEM SHALL**:
  1. tomar un respaldo previo de `control_lote_almacen`
     (`control_lote_almacen_backup` o `pg_dump -t`);
  2. ejecutar el DDL y el DML dentro de `BEGIN … COMMIT`;
  3. abortar con `RAISE EXCEPTION` si la verificación de equivalencia falla,
     de modo que el `ROLLBACK` deje el esquema y los datos originales intactos;
  4. documentar el procedimiento de reversión posterior al `COMMIT`
     (recrear la tabla original desde la vista o el backup y eliminar los
     objetos nuevos).
- **Se prueba con:** ejecución forzada de fallo y `ROLLBACK` en
  `sql/tp_fnbc_control_lote_migracion_segura.sql`; plan detallado en
  `kiro/design.md` §Plan de reversión.

### REQ-05 — Desnormalización controlada

- **WHEN** se implementa la tabla `ventas_categoria_dia`
- **THE SYSTEM SHALL**:
  - recalcularla siempre desde la fuente de verdad
    (`detalle_pedido`, `producto`, `pedido`, `categoria`);
  - mantenerla sincronizada con triggers `AFTER` sobre `detalle_pedido` y
    `pedido`;
  - proveer una consulta de auditoría que devuelva 0 filas si la tabla está
    sincronizada;
  - permitir eliminarla y regenerarla sin pérdida de información transaccional.
- **Se prueba con:** `sql/tp_desnormalizacion_top_categorias.sql` (carga
  inicial + consulta de auditoría).

### REQ-06 — Medición antes/después

- **WHEN** se compara la consulta original contra la desnormalizada
- **THE SYSTEM SHALL** registrar `EXPLAIN (ANALYZE, BUFFERS)` antes y después,
  el tiempo de ejecución y el nodo dominante del plan.
- **Se prueba con:** la tabla comparativa del informe de U4 (hoy con
  `[COMPLETAR DATO REAL]`; debe completarse con salidas ejecutadas).

### REQ-07 — Uso de IA documentado

- **WHEN** se utiliza un asistente de IA en la Unidad 4
- **THE SYSTEM SHALL** registrar herramienta, finalidad, prompt o spec,
  propuesta aceptada o descartada y la decisión humana en `BITACORA_IA.md` y
  `DUIA.md`.
- **Se prueba con:** bitácora de U4 (hoy ausente; ver §6.2 del informe técnico).

## Trazabilidad requisito → artefacto

| Requisito | Artefacto | Evidencia |
|---|---|---|
| REQ-01 | `sql/tp_fnbc_control_lote.sql`, informe U4 | análisis DF y FNBC |
| REQ-02 | `sql/tp_fnbc_control_lote.sql` | DDL de R1/R2 y vista |
| REQ-03 | `sql/tp_fnbc_control_lote_migracion_segura.sql` | consulta de diferencias = 0 filas |
| REQ-04 | `sql/tp_fnbc_control_lote_migracion_segura.sql`, `kiro/design.md` | `BEGIN/COMMIT`, `RAISE EXCEPTION`, plan de rollback |
| REQ-05 | `sql/tp_desnormalizacion_top_categorias.sql` | triggers + auditoría |
| REQ-06 | informe U4, tabla comparativa | `EXPLAIN (ANALYZE, BUFFERS)` |
| REQ-07 | `BITACORA_IA.md`, `DUIA.md` | prompts/specs y decisión humana |

## Criterios de aceptación

- La descomposición elimina la violación de FNBC sin perder la terna original.
- La vista `v_control_lote_almacen` devuelve exactamente las filas de
  `control_lote_almacen` (0 diferencias).
- La migración se ejecuta en una transacción y un fallo simulado no deja
  cambios parciales.
- Existe un plan de reversión reproducible posterior al `COMMIT`.
- `ventas_categoria_dia` se mantiene desde la fuente de verdad y su consulta de
  auditoría devuelve 0 filas.
- Las mediciones antes/después están registradas con salidas reales.
- Todo uso de IA de U4 está declarado en bitácora y DUIA.
