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

> Se completa al crear la vista materializada.