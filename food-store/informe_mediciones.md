# Informe de mediciones — Unidad 3 · Semana 1

**Proyecto:** Food Store · **Base de trabajo:** `foodstore_u3` (copia según
protocolo de seguridad; `foodstore` de producción intacta) · **Motor:**
PostgreSQL 17 · **Volumen:** 2 categorías · 50.002 productos · 20.001 clientes
· 200.001 pedidos · 400.002 líneas de pedido.

> **Nota heredada del enunciado (equivalencia documentada):** el enunciado
> genérico menciona tablas `usuario` / `detalle_pedido`. El esquema real del
> proyecto (Semanas 1-4) usa `cliente` / `linea_pedido` para los mismos roles
> (`usuario` → `cliente`, `detalle_pedido` → `linea_pedido`); el trabajo se
> realiza sobre los objetos realmente existentes, sin modificar el modelo.

## Protocolo de medición

- Cada `EXPLAIN (ANALYZE, BUFFERS)` se ejecuta **dos veces**; se conserva la
  segunda corrida (caché caliente) para que la comparación no dependa de la
  primera lectura fría de disco.
- Antes de cualquier DDL se respalda con `pg_dump -Fc` en `../backups/`.
- Las cargas de escritura corren dentro de `BEGIN ... ROLLBACK`.

## Parte A — Plan de indexado

### Consultas candidatas identificadas (hoy resuelven con Seq Scan)

| # | Consulta | Tabla grande | Plan hoy | Tiempo hoy |
|---|----------|--------------|----------|-----------|
| C1 | Ventas de un producto (historial) | `linea_pedido` (400k) | `Parallel Seq Scan` | 36,6 ms |
| C2 | Búsqueda por nombre (menú) `ILIKE %txt%` | `producto` (50k) | `Seq Scan` | 31,6 ms |
| C3 | Reposición de stock (`stock <= 10`) | `producto` (50k) | `Seq Scan` | 7,0 ms |
| C4 | Ranking de clientes por gasto | `linea_pedido` + `pedido` | `Parallel Seq Scan` x2 | 362 ms |

### Antes / Después (caché caliente)

| Consulta | Índice | Plan ANTES | Plan DESPUÉS | Tiempo ANTES | Tiempo DESPUÉS | Mejora |
|----------|--------|------------|--------------|--------------|----------------|--------|
| C1 | `idx_linea_pedido_producto` btree `(producto_id)` INCLUDE `(cantidad, precio_unitario)` | Seq Scan | `Bitmap Heap/Index Scan` + Index Scan (pedido_pkey) | 36,6 ms | 0,3 ms | ~122× |
| C2 | `idx_producto_nombre_trgm` GIN (pg_trgm) parcial `WHERE activo` | Seq Scan | `Bitmap Index Scan` trigram | 31,6 ms | 1,2 ms | ~27× |
| C3 | `idx_producto_stock_parcial` btree `(stock)` parcial `WHERE activo AND stock <= 10` | Seq Scan | `Bitmap Index Scan` parcial | 7,0 ms | 4,5 ms | ~1,5× |

Planes completos en `planes/` (`Q_antes_warm.txt`, `Q_despues_warm.txt`).

**C1** — cambio de plan: `Parallel Seq Scan on linea_pedido` (+85.000 buffers)
→ `Bitmap Index Scan on idx_linea_pedido_producto` con 8 filas y fetch al heap
mínimo. La FK más usada de la tabla más grande estaba sin índice.

**C2** — un b-tree clásico no puede resolver `LIKE %...%`; con `pg_trgm` el
plan pasa a `Bitmap Index Scan` y la búsqueda deja de barrer 50k filas.

**C3** — la mejora es menor (1,5×) porque el índice parcial reduce el costo de
lectura pero el `ORDER BY stock` sigue ordenando 2.771 filas. Aceptado: evita
el Seq Scan completo y el costo de mantenimiento es bajo (escribir en
`producto` es mucho menos frecuente que en `linea_pedido`).

**C4 (no indexado — justificación del descarte por sobreindexación):** la
consulta de ranking agrega TODA `linea_pedido` (400k filas) entre todos los
clientes; ningún índice puede reducir las filas a leer (el plan ya usa las PK
para los join). Un índice en `pedido(cliente_id)` (propuesto por la IA, D1 en
`indices.sql`) se **descartó**: `cliente_id` ya está indexado por
`idx_pedido_cliente` desde la Semana 1, sería duplicado. El segundo descarte
(D2) fue `idx_producto_categoria_dup` `(categoria_id, nombre)`: la restricción
`UNIQUE (categoria_id, nombre)` ya crea ese índice como soporte, sería un
objeto redundante.

### Costo de escritura (INSERT masivo en `linea_pedido`)

Carga: 1.000 `pedido` + 4.000 `linea_pedido` (5.000 INSERTs), dentro de
`BEGIN...ROLLBACK`.

| Métrica | ANTES | DESPUÉS | Delta |
|---------|-------|---------|-------|
| 1.000 pedidos | 21,6 ms | 19,9 ms | −8% |
| 1.000 líneas | 20,7 ms | 24,2 ms | +17% |
| 3.000 líneas | 42,1 ms | 63,5 ms | +51% |
| **Total** | **84,4 ms** | **107,6 ms** | **+28%** |

**Lectura del resultado:** los índices cuestan en la escritura de
`linea_pedido` (+28% en una carga de 5.000 INSERTs), que es la tabla de mayor
frecuencia de escritura. En una aplicación real este costo se amortiza porque
el INSERT suele ser transaccional y en lote; a cambio, la lectura de las
consultas C1-C3 cae hasta 122×. Ese es el trade-off que se evalúa en la
defensa oral: **no existe un índice gratis**, solo índices donde la mejora de
lectura justifica el costo de mantenimiento.

## Parte B — Vistas (verificación de equivalencia)

Tres vistas en `views.sql`, generadas por OpenCode desde los specs en `specs/`:

| Vista | Reporte | Verificación EXCEPT (vista↔manual) |
|-------|---------|-------------------------------------|
| `v_productos_vigentes` | productos vigentes con su categoría (menú) | 0 y 0 filas de diferencia |
| `v_pedidos_cliente` | pedidos con datos del cliente | 0 y 0 filas de diferencia |
| `v_detalle_pedido_producto` | detalle de pedido con nombre de producto | 0 y 0 filas de diferencia |

Cada vista se verificó en **ambas direcciones** del `EXCEPT` (filas de la vista
que no están en la consulta manual, y viceversa); todas dieron **0 filas**
(script `06_verificacion_vistas.sql`).

**Criterio de seguridad aplicado (vista `v_pedidos_cliente`):** el enunciado
pide ocultar la columna `contraseña` del usuario. El esquema real del equipo
modela al comprador como `cliente` (sin credenciales). La vista oculta las
columnas de contacto protegidas del esquema real —`email` y `telefono`— y se
verificó que la vista **no las expone** (0 columnas sensibles). Con `SELECT`
sobre la vista se puede dar acceso a los pedidos sin abrir la tabla base
`cliente`. La equivalencia se hace sobre el subconjunto de columnas expuestas,
que es exactamente lo que la vista garantiza.

## Parte C — Vista materializada (medición)

**Reporte elegido:** facturación por categoría y mes (Q6 de `queries.sql`),
agregación costosa sobre `linea_pedido` (400k filas).

Vista materializada `mv_facturacion_categoria_mes` creada en
`07_vista_materializada.sql` con `WITH DATA` e índice único
`(mes, categoria)` que habilita el `REFRESH CONCURRENTLY`.

| Métrica | Consulta original (sin materializar) | Consulta sobre la materializada |
|---------|--------------------------------------|---------------------------------|
| Plan | `Parallel Seq Scan` sobre `linea_pedido` y `pedido`, 4 tablas | `Seq Scan` directo sobre 26 filas |
| Tiempo | **484,9 ms** | **0,026 ms** (~18.600×) |
| Duración psql (con \timing) | 496 ms | 1,2 ms |

`REFRESH MATERIALIZED VIEW CONCURRENTLY` verificado OK (no bloquea lecturas
concurrentes; requiere el índice único).

**Frecuencia de refresco y su implicancia:** el dato cambia solo cuando entra
al menos un pedido o línea nuevo (no hay UPDATE/DELETE de histórico). Con el
uso esperado del reporte (panel gerencial que se consulta varias veces por
día, no por minuto), el refresco aconsejado es **una vez al final del día**
(`REFRESH MATERIALIZED VIEW CONCURRENTLY` en el mismo cierre que procesa la
recaudación). Implicancia para los usuarios: entre refresco y refresco, el
reporte refleja la facturación del **período cerrado anterior** — un pedido de
hoy no cuenta hasta el próximo cierre. Esto es aceptable porque el objetivo
del reporte es la foto mensual de categorías (semana analítica), no el saldo
en tiempo real; si un área necesitara datos al día, se acorta el intervalo de
refresco (ej. cada hora) a costo de re-agregar las 400k líneas varias veces al
día.

## Parte D — Procedimientos almacenados (objetivo 6 del TPI)

**Pieza faltante detectada por la auditoría del TPI:** el repo tenía vistas
(Parte B) y funciones trigger (TP2), pero **ningún objeto invocado con `CALL`**.
Se agregaron dos procedimientos en PL/pgSQL (`08_procedimientos.sql`, spec en
`specs/spec_procedimientos_almacenados.md`):

| # | Procedimiento | Qué hace | Cómo se probó |
|---|---------------|----------|---------------|
| P1 | `registrar_pedido(cliente_id, forma_pago, items JSONB, OUT pedido_id)` | Registro de venta transaccional: valida cliente activo (R1), inserta pedido, recorre el JSONB de líneas validando producto activo (R2) y stock (R3) con `SELECT ... FOR UPDATE` (anti-sobreventa), inserta la línea con el precio congelado (R4) y descuenta el stock. Cualquier error revierte todo (atomicidad). | verificación en `09_verificacion_procedimientos.sql` |
| P2 | `ajustar_stock(producto_id, delta, OUT nuevo_stock)` | Reposición/ajuste manual de inventario: valida vigencia, bloquea la fila, rechaza stock negativo y devuelve el nuevo valor por OUT + `RAISE NOTICE`. | idem |

**Resultados verificados (corrida real, dentro de `BEGIN...ROLLBACK`):**

- **P1 válido:** `CALL registrar_pedido(1, 'EFECTIVO', '[{1,2},{2,3}]', ...)` →
  pedido `202003` creado con 2 líneas y total 4.500,00; stock de Muzzarella
  20→18 y Coca 50→47 (descontado exactamente lo vendido).
- **P1 inválidos (todos rechazados con la regla correcta):**
  - cliente 2 inactivo → `R1: no se puede registrar un pedido para el cliente 2`.
  - producto 3 inactivo → `R2: no se puede vender el producto 3`.
  - cantidad 999 > stock 18 → `R3: stock insuficiente ... pide 999 pero hay 18`.
  - En el caso R3 con 2 ítems (uno válido y el otro inválido), el stock **no
    se descontó de ningún ítem** → atomicidad confirmada (stock siguió 18/47).
- **P2 válido:** `CALL ajustar_stock(1, 10, ...)` → 18→28.
- **P2 inválido:** ajuste −999999 → `Stock no puede quedar negativo`, stock
  intacto.
- `ROLLBACK` final: `pedido` quedó en 200.001 y `stock` en 20 (nada persistió).

**Nota de soporte del motor (JSONB):** `p_items` usa el tipo `JSONB` (pedido
por la cátedra), entregando las líneas del pedido como un único argumento
tipado y demostrando tipos modernos de PostgreSQL en objetos programables.

**Salida real completa:** `planes/verificacion_procedimientos.txt`.