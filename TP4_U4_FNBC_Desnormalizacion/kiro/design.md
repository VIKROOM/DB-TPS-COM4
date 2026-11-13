# Kiro · Design — TP Unidad 4 (FNBC y desnormalización controlada)

## Objetivo

Refactorizar `control_lote_almacen` hasta FNBC, migrar sus datos sin pérdida en
una transacción reversible y agregar una desnormalización controlada para el
Top 5 de categorías, sin romper las consultas existentes.

## Análisis FNBC

Relación original:

```
control_lote_almacen(lote_id, deposito_id, responsable_control_id)
PK = (lote_id, deposito_id)
```

Dependencias funcionales reales:

```
DF1: {lote_id, deposito_id}         → {responsable_control_id}
DF2: {responsable_control_id}       → {deposito_id}
```

`DF2` viola FNBC porque `responsable_control_id` no es superclave. Las claves
candidatas son `{lote_id, deposito_id}` y `{lote_id, responsable_control_id}`;
`responsable_control_id` es primo por la segunda clave alterna. El comentario de
`sql/tp_fnbc_control_lote.sql:31` lo lista como no primo; se corrige esa
definición: al formar parte de una clave candidata, es primo. La descomposición
elegida es:

```
responsable_deposito(responsable_control_id PK, deposito_id)
control_lote(lote_id, responsable_control_id, PK (lote_id, responsable_control_id),
             FK responsable_control_id → responsable_deposito)
```

El atributo común `responsable_control_id` es PK en `responsable_deposito` y FK
en `control_lote`, por lo que el `JOIN` reconstruye exactamente la terna
original sin duplicados ni pérdida.

## Migración reversible

### Preparación

1. Verificar que `control_lote_almacen` exista y tenga datos.
2. Crear un respaldo lógico dentro de la misma base:
   `CREATE TABLE control_lote_almacen_backup AS TABLE control_lote_almacen;`
   (o `pg_dump -t public.control_lote_almacen -Fc` si se prefiere un archivo).
3. Registrar el conteo original:
   `SELECT count(*) FROM control_lote_almacen;`.

### Ejecución transaccional

El script `sql/tp_fnbc_control_lote_migracion_segura.sql` ejecuta:

```
BEGIN;

CREATE TABLE IF NOT EXISTS responsable_deposito (...);
CREATE TABLE IF NOT EXISTS control_lote (...);

INSERT INTO responsable_deposito (responsable_control_id, deposito_id)
SELECT DISTINCT responsable_control_id, deposito_id
FROM control_lote_almacen
ON CONFLICT (responsable_control_id) DO NOTHING;

INSERT INTO control_lote (lote_id, responsable_control_id)
SELECT lote_id, responsable_control_id
FROM control_lote_almacen
ON CONFLICT (lote_id, responsable_control_id) DO NOTHING;

CREATE OR REPLACE VIEW v_control_lote_almacen AS ...;

-- Si hay diferencias, aborta y el ROLLBACK lo deshace todo.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM control_lote_almacen cla
        LEFT JOIN v_control_lote_almacen v
          ON cla.lote_id = v.lote_id
         AND cla.deposito_id = v.deposito_id
         AND cla.responsable_control_id = v.responsable_control_id
        WHERE v.lote_id IS NULL
    ) OR EXISTS (
        SELECT 1
        FROM v_control_lote_almacen v
        LEFT JOIN control_lote_almacen cla
          ON cla.lote_id = v.lote_id
         AND cla.deposito_id = v.deposito_id
         AND cla.responsable_control_id = v.responsable_control_id
        WHERE cla.lote_id IS NULL
    ) THEN
        RAISE EXCEPTION 'Migración FNBC: la vista no reconstruye exactamente la tabla original';
    END IF;
END $$;

COMMIT;
```

La comparación es bidireccional para detectar tanto filas perdidas como filas
espurias. `psql` se ejecuta con `\set ON_ERROR_STOP on`; cualquier excepción
aborta el script y PostgreSQL rollbackea la transacción completa.

### Reversión antes del COMMIT

Si la verificación falla o se interrumpe la ejecución:

```
ROLLBACK;
```

No se crean tablas nuevas ni se modifican datos. La tabla original permanece
intacta porque nunca se elimina dentro de la transacción.

### Reversión después del COMMIT

Si la migración se confirmó y luego se decide volver al esquema anterior:

1. Reconstruir la tabla original desde la vista o el backup:
   ```
   BEGIN;
   CREATE TABLE control_lote_almacen_restaurada AS
   SELECT lote_id, deposito_id, responsable_control_id
   FROM v_control_lote_almacen;
   -- o: CREATE TABLE ... AS TABLE control_lote_almacen_backup;
   ```
2. Verificar conteos y diferencias contra `control_lote_almacen_backup`.
3. Reemplazar la tabla original:
   ```
   ALTER TABLE control_lote_almacen RENAME TO control_lote_almacen_migrada;
   ALTER TABLE control_lote_almacen_restaurada RENAME TO control_lote_almacen;
   ```
4. Eliminar los objetos nuevos:
   ```
   DROP VIEW IF EXISTS v_control_lote_almacen;
   DROP TABLE IF EXISTS control_lote;
   DROP TABLE IF EXISTS responsable_deposito;
   COMMIT;
   ```
5. Conservar `control_lote_almacen_backup` hasta validar la aplicación.

El backup no se elimina automáticamente: la decisión de borrarlo es humana y
posterior a la verificación.

## Desnormalización controlada

Tabla:

```
ventas_categoria_dia(
  fecha DATE,
  categoria_id BIGINT,
  categoria_nombre VARCHAR(80),
  total_vendido NUMERIC(12,2),
  cantidad_items BIGINT,
  cantidad_pedidos BIGINT,
  actualizado_en TIMESTAMPTZ,
  PK (fecha, categoria_id)
)
```

Reglas:

- `fn_recalcular_ventas_categoria_dia(fecha, categoria_id)` recalcula siempre
  desde `detalle_pedido`, `producto`, `pedido` y `categoria`; no confía en
  incrementos ad-hoc.
- Triggers `AFTER INSERT/UPDATE/DELETE` sobre `detalle_pedido` y
  `AFTER UPDATE` sobre `pedido` recalculan las categorías afectadas.
- La consulta de auditoría compara la tabla contra la agregación normalizada y
  debe devolver 0 filas.
- La tabla es redundante y reversible: se puede eliminar y regenerar con la
  consulta original sin perder datos transaccionales.

## Mediciones

Se registran `EXPLAIN (ANALYZE, BUFFERS)` antes y después, el tiempo de
ejecución y el nodo dominante. Las salidas se guardan en el informe de U4; no se
aceptan valores estimados.

## Uso de IA

Toda intervención de IA en U4 se registra en `BITACORA_IA.md` y `DUIA.md`:
herramienta, finalidad, prompt/spec, propuesta aceptada o descartada y decisión
humana. Ningún script se ejecuta sin lectura línea por línea, respaldo previo y
prueba en copia o transacción reversible.

## Verificación

| Control | Consulta / acción | Resultado esperado |
|---|---|---|
| Equivalencia | diferencias vista vs. tabla original | 0 filas |
| Migración fallida | forzar `RAISE EXCEPTION` | `ROLLBACK`, sin objetos nuevos |
| Reversión post-COMMIT | recrear tabla desde vista/backup | conteos iguales al backup |
| Desnormalización | auditoría `ventas_categoria_dia` | 0 filas |
| Medición | `EXPLAIN (ANALYZE, BUFFERS)` | tiempos y nodo registrados |
