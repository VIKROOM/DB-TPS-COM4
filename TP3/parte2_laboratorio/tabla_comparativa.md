# TP3 · Parte 2 — Tabla comparativa de resultados (sección 2.2)

**Base:** `foodstore_tp3` (50.003 productos · 20.003 usuarios · 200.001 pedidos
· 500.365 detalles) · **Motor:** PostgreSQL 17.10
**Protocolo de medición:** `EXPLAIN (ANALYZE, BUFFERS)`, dos corridas por
medición, se registra la segunda (caché caliente). Estado *antes*: solo índices
de PK/UNIQUE del esquema. Estado *después*: índices I1–I3 de `indices.sql`
(verificados contra el plan real antes de aceptarlos). Tras crear los índices
se corrió `ANALYZE`; antes de medir se corrió `VACUUM ANALYZE` para que el
visibility map habilite index-only scans comparables.

Planes completos en `planes/C{n}_{antes|despues}.txt`.

---

| Consulta | Plan antes (nodo, cost, tiempo real) | Cambio aplicado | Plan después (nodo, cost, tiempo real) | Mejora |
|---|---|---|---|---|
| **C1** — Productos vigentes de una categoría ordenados por precio (`categoria_id=2`, ~8.335 filas de 50.003) | `Sort` (cost=2892.42..2913.24, actual 9.685..10.122 ms, rows=8335) sobre `Seq Scan on producto` (Filter: NOT eliminado AND categoria_id=2, **Rows Removed by Filter: 41.668**, Buffers hit=1728) · **Execution Time: 10.486 ms** | **I1:** `CREATE INDEX idx_producto_cat_elim_precio ON producto (categoria_id, eliminado, precio)` | `Sort` (cost=2592.20..2613.10, actual 6.751..7.325 ms, rows=8335) sobre `Bitmap Heap Scan` (Heap Blocks exact=864, Buffers hit=901) ← `Bitmap Index Scan on idx_producto_cat_elim_precio` (Index Cond: categoria_id=2 AND eliminado=false, hit=37) · **Execution Time: 7.726 ms** | **1.36×** (10.486 → 7.726 ms) |
| **C2** — Historial de pedidos de un usuario, más recientes primero (`usuario_id=1000`, 10 filas de 200.001) | `Gather Merge` (cost=5780.74..5781.67, actual 33.131..36.821 ms) ← `Sort` (fecha DESC) ← `Parallel Seq Scan on pedido`, 2 workers (**Rows Removed by Filter: 66.664 por loop**, Buffers hit=3813) · **Execution Time: 36.934 ms** | **I2:** `CREATE INDEX idx_pedido_usu_elim_fecha ON pedido (usuario_id, eliminado, fecha)` | `Index Scan Backward using idx_pedido_usu_elim_fecha` (cost=0.42..24.37, actual 0.038..0.041 ms, rows=10, Index Cond: usuario_id=1000 AND eliminado=false, **Buffers hit=8**, sin nodo Sort) · **Execution Time: 0.164 ms** | **225×** (36.934 → 0.164 ms) |
| **C3** — Top 10 productos más vendidos (agregación sobre 500.365 líneas) | `Limit` ← `Sort` top-N heapsort (actual 149.731..149.732 ms) ← `HashAggregate` (49.998 grupos, Memory 4881kB) ← `Seq Scan on detalle_pedido` (rows=500365, Buffers hit=4749 **read=2406**) · **Execution Time: 150.645 ms** | **I3:** `CREATE INDEX idx_detalle_cubriente ON detalle_pedido (producto_id, cantidad)` (cubriente: contiene todas las columnas que toca la consulta) | `Limit` ← `Sort` top-N ← `GroupAggregate` (rows=49998) ← `Index Only Scan using idx_detalle_cubriente` (**Heap Fetches: 0**, Buffers hit=1013, sin lecturas de disco) · **Execution Time: 62.328 ms** | **2.42×** (150.645 → 62.328 ms) |

---

## Análisis honesto de cada resultado (criterio de aceptación de la consigna)

**C2 — la mejora enorme, y por qué.** El plan antes leía la tabla completa en
paralelo (3.813 buffers, ~200.000 filas descartadas por el filtro) para
recuperar 10 filas, y además ordenaba. Con I2, las dos columnas de igualdad
(`usuario_id`, `eliminado`) son Index Cond y la tercera (`fecha`) entrega las
filas ya ordenadas: el nodo Sort desaparece y el recorrido *backward* resuelve
el `DESC`. De 3.813 buffers a 8. La predicción (atacar el Seq Scan y el Sort)
se confirmó exactamente.

**C3 — mejora real pero acotada, y por qué.** La agregación necesita las
500.365 líneas igual: no hay filtro que reducir. El índice cubriente no achica
el volumen de filas, achica el volumen de **datos leídos**: 7.155 buffers
(heap) → 1.013 buffers (solo índice, `Heap Fetches: 0` gracias al VACUUM
previo), y el GroupAggregate reemplaza al HashAggregate porque el índice ya
entrega las filas agrupadas por `producto_id`. 2.42× es lo esperable cuando el
cuello es el volumen y no la selectividad.

**C1 — la mejora chica, documentada en lugar de escondida.** I1 no eliminó el
nodo Sort como predecía la justificación inicial: con ~8.335 filas coincidentes
(17% de la tabla), el planificador prefirió Bitmap Heap Scan + Sort antes que
un Index Scan ordenado por `precio` con 8.335 heap fetches aleatorios. La
ganancia real viene de dejar de leer las 41.668 filas de otras categorías
(1.728 → 904 buffers). Lección: cuando el resultado es un porcentaje grande de
la tabla, un índice compuesto "igualdad + orden" no siempre elimina el Sort;
decide el planner con sus costos, y la medición manda.

## Propuestas de la IA descartadas (con evidencia)

| Propuesta | Decisión | Por qué (con datos) |
|---|---|---|
| `CREATE INDEX ON producto (precio)` para C1 | **Descartada en revisión** (no se aplicó) | El filtro selectivo es `categoria_id` (1/6 de la tabla); `precio` solo sirve al ORDER BY. Un índice solo de precio obligaría a recorrerlo completo + heap fetches por cada fila de la categoría: estrictamente peor que I1. No hace falta medirlo para rechazarlo, pero la medición de I1 confirma que el camino por categoría es el correcto. |
| `... (categoria_id, eliminado, precio) INCLUDE (nombre, stock)` para volver C1/C5 *index only* | **Probada y descartada** | Se creó sobre la copia (2.888 kB vs 1.552 kB del índice simple, ~1.9×) y se midió: el planner **no lo eligió** — siguió con Bitmap Heap Scan sobre el índice simple. C5: 4.798 ms vs 4.941 ms (ruido); C1: 7.429 ms vs 7.726 ms (ruido). Evidencia: `../parte5_competencia/planes/competencia_despues_include.txt` y `planes/C1_despues_include.txt`. Costo de escritura y tamaño duplicados sin ganancia medible → `DROP INDEX`. |
| Reescritura de C3 con ventana (`SUM() OVER (PARTITION BY producto_id)`) | **Descartada en revisión** | Ventana sobre 500.365 filas materializa el particionado completo y no habilita el `LIMIT 10` temprano; `GROUP BY` + top-N heapsort (lo que ya hace el plan) es la forma barata. Rechazada sin aplicar: no ataca ningún nodo del plan real. |
