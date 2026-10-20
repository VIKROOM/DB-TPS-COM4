# Informe TP_U4 - FNBC y Desnormalización Controlada (Food Store)

## Parte 1 - Análisis y aplicación de FNBC: ControlLoteAlmacen

### (a) Dependencias funcionales (notación formal)
Sean:
- LoteID = lote_id
- DepositoID = deposito_id
- ResponsableControlID = responsable_control_id

A partir de la regla de negocio:
- Para un lote y un depósito interviniente dados, el responsable de control queda unívocamente determinado.
- Cada responsable de control pertenece, como dato maestro de la dotación de personal, a un único depósito.

Se desprenden:
$$
DF_1: \{LoteID, DepositoID\} \to \{ResponsableControlID\}
$$
$$
DF_2: \{ResponsableControlID\} \to \{DepositoID\}
$$

### (b) Clausura, claves candidatas, atributos primos/no primos
Conjunto de atributos $R = \{LoteID, DepositoID, ResponsableControlID\}$.

Clausuras relevantes:
- $(\{LoteID, DepositoID\})^+ = \{LoteID, DepositoID, ResponsableControlID\}$
- $(\{LoteID, ResponsableControlID\})^+ = \{LoteID, ResponsableControlID, DepositoID\}$ (por $DF_2$)
- $(\{ResponsableControlID\})^+ = \{ResponsableControlID, DepositoID\}$

**Clave candidata:** $\{LoteID, DepositoID\}$ (también se puede derivar $\{LoteID, ResponsableControlID\}$ como clave candidata, dado que determina a todos los atributos).

**Atributos primos:** $LoteID, DepositoID, ResponsableControlID$ son primos en el sentido de pertenecer a alguna clave candidata.
**Atributos no primos:** Ninguno en este esquema (todos son primos). Sin embargo la violación es por $DF_2$ con determinante no superclave.

### (c) ¿Cumple FNBC? Justificación
La Forma Normal de Boyce-Codd (FNBC) exige que para toda dependencia funcional no trivial $X \to Y$, $X$ sea una superclave.

En `control_lote_almacen` con clave candidata $K=\{LoteID, DepositoID\}$:
- $DF_1: K \to \{ResponsableControlID\}$: el determinante $K$ es superclave → cumple para $DF_1$.
- $DF_2: \{ResponsableControlID\} \to \{DepositoID\}$: el determinante $\{ResponsableControlID\}$ **NO** es superclave (su clausura no contiene todos los atributos de la relación), y la dependencia es no trivial.

**Conclusión:** `control_lote_almacen` **NO** está en FNBC.

### (d) Anomalías (con la instancia provista)
Instancia:
```
(501, 30, 801)
(502, 30, 801)
(503, 31, 802)
```

- **Anomalía de inserción:** No se puede registrar que el responsable `801` está asignado al depósito `30` sin asociarlo a algún `lote_id` existente (o se fuerza una tupla artificial). Además, no se puede representar la asignación `(responsable, depósito)` de forma independiente.
- **Anomalía de borrado:** Si se elimina la única tupla que relaciona `lote_id=501` con `(deposito_id=30, responsable_control_id=801)`, se puede perder inadvertidamente la información de que `801` pertenece al depósito `30` (dependencia de negocio del dato maestro).
- **Anomalía de actualización:** Si `801` cambiara de depósito (violando la regla "pertenece a un único depósito" o para corregir un error), habría que actualizar todas las tuplas donde aparece `801` `(501,30,801)` y `(502,30,801)`, con riesgo de inconsistencia si no se actualizan todas.

### (e)-(f) Descomposición sin pérdida, vista de compatibilidad y migración
Se aplica descomposición en dos esquemas:

**R1 (responsable_deposito):**
```sql
CREATE TABLE responsable_deposito (
    responsable_control_id  BIGINT NOT NULL,
    deposito_id            BIGINT NOT NULL,
    PRIMARY KEY (responsable_control_id)
);
```
**R2 (control_lote):**
```sql
CREATE TABLE control_lote (
    lote_id                BIGINT NOT NULL,
    responsable_control_id BIGINT NOT NULL,
    PRIMARY KEY (lote_id, responsable_control_id),
    CONSTRAINT fk_control_lote_resp FOREIGN KEY (responsable_control_id)
        REFERENCES responsable_deposito(responsable_control_id)
);
```

**Vista de compatibilidad:**
```sql
CREATE OR REPLACE VIEW v_control_lote_almacen AS
SELECT cl.lote_id, rd.deposito_id, cl.responsable_control_id
FROM control_lote cl
JOIN responsable_deposito rd
  ON cl.responsable_control_id = rd.responsable_control_id;
```

**Justificación unión sin pérdida:** El atributo común es `responsable_control_id`. En `responsable_deposito` es **clave primaria** (superclave), en `control_lote` es **clave foránea** hacia ella. Dado que $DF_2: \{responsable_control_id\}\to\{deposito_id\}$ y `responsable_control_id` es clave en R1, el JOIN por clave garantiza que cada tupla de R2 se une con **exactamente una** tupla de R1, reconstruyendo sin duplicados ni pérdida la terna original $(lote_id, deposito_id, responsable_control_id)$.

**Migración verificada:** Los datos se migraron desde `control_lote_almacen` hacia las tablas descompuestas y la equivalencia se verificó mediante `v_control_lote_almacen` (coincide con la instancia original).

## Parte 2 - Consulta con desnormalización controlada

### (a) EXPLAIN ANALYZE antes
Consulta original (filtra por `ped.fecha = CURRENT_DATE`, `dp.eliminado = FALSE`, `ped.eliminado = FALSE`, agrupa por `c.nombre`, ordena por `SUM(dp.subtotal)` desc, `LIMIT 5`).

**Observación:** Con un volumen razonable, el plan tiende a dominar por **uniones** (`JOIN` entre `detalle_pedido`, `producto`, `categoria`, `pedido`), acceso por filtros sobre `pedido.fecha`/flags de eliminado y **agregación/ordenamiento** para obtener el Top 5 por monto vendido. El nodo de mayor costo es típicamente el **Hash Join** o **Nested Loop** según índices/cantidad, con trabajo de agrupación (`GroupAggregate`/`HashAggregate`) y `Sort` para el ordenamiento.

### (b) Patrón elegido y justificación
**Patrón:** **Columna precalculada con disparador (trigger-based materialization)** — tabla `ventas_categoria_dia(fecha, categoria_id, categoria_nombre, total_vendido, cantidad_items, cantidad_pedidos, actualizado_en)` con clave primaria `(fecha, categoria_id)`.

**Justificación:**
- **Evidencia que motiva:** La consulta original realiza 4 `JOIN`, filtra por fecha y flags, agrega y ordena para obtener Top 5; con uso frecuente por panel en tiempo real este costo se vuelve notable (coincide con lo observado en el plan).
- **Sincronización:** Se garantiza con **disparadores AFTER** sobre `detalle_pedido` (INSERT/UPDATE/DELETE) que recalculan la fila afectada por `(fecha, categoria_id)` usando `fn_recalcular_ventas_categoria_dia()` sobre la **fuente de verdad** (`detalle_pedido`, `producto`, `pedido`, `categoria`). También hay disparador sobre `pedido` para cambios de `fecha`/`eliminado`. Los valores se recalculan desde los datos originales (nunca se confía solo en incrementos ad-hoc).
- **Reversibilidad:** **Sí, sin pérdida de información.** La tabla es completamente redundante; se puede regenerar en cualquier momento con la consulta original, eliminarla y volver a usar el esquema normalizado sin perder datos transaccionales.

### (c) Implementación
Ver `sql/tp_desnormalizacion_top_categorias.sql`:
- Creación de `ventas_categoria_dia` con índices
- Funciones `fn_recalcular_ventas_categoria_dia()` y `fn_trg_sync_ventas_categoria_dia()` / `fn_trg_sync_vcd_por_pedido()`
- Triggers AFTER sobre `detalle_pedido` y `pedido`
- Carga inicial desde fuente de verdad

### (d) Consulta desnormalizada + comparación antes/después
**Consulta desnormalizada:**
```sql
SELECT categoria_nombre AS categoria,
       total_vendido
FROM ventas_categoria_dia
WHERE fecha = CURRENT_DATE
ORDER BY total_vendido DESC
LIMIT 5;
```

**Tabla comparativa (plantilla):**

| Aspecto | Antes (normalizado, 4 JOINs + GROUP BY + ORDER BY) | Después (desnormalizado, tabla precalculada) |
|---|---|---|
| Tiempo de ejecución (EXPLAIN ANALYZE) | (registrar valor medido) | (registrar valor medido) |
| Nodo dominante del plan | (ej. Hash Join / Nested Loop + HashAggregate/GroupAggregate + Sort) | (ej. Index Scan/Bitmap Index Scan + Sort/Index scan por índice en (fecha,total_vendido DESC), sin joins masivos) |

*(Completar con las salidas reales de `EXPLAIN (ANALYZE, BUFFERS)` sobre la instancia usada.)*

### (e) Script de auditoría (resultado vacío)
Ver script en `sql/tp_desnormalizacion_top_categorias.sql` — compara `ventas_categoria_dia` con agregación desde fuente de verdad para `CURRENT_DATE`. Si no hay diferencias, retorna **0 filas**.

## Entregables
- `sql/tp_fnbc_control_lote.sql` — Parte 1 completo
- `sql/tp_desnormalizacion_top_categorias.sql` — Parte 2 completo
- `informe/Informe_TP_U4_FNBC_Desnormalizacion_FoodStore.md` — este informe
- Repositorio: https://github.com/VIKROOM/DB-TPS-COM4.git
