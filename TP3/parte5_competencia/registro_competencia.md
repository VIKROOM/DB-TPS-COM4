# TP3 · Parte 5 — Registro de la competencia de optimización

**Consulta común fijada por la cátedra** (idéntica para todos los equipos,
ver `consulta_comun.sql`): listado de productos por categoría con filtro de
precio y orden, **sin índice**, sobre la base masiva común (`foodstore_tp3`,
50.003 productos):

```sql
SELECT p.id, p.nombre, p.precio, p.stock
FROM producto p
WHERE p.categoria_id = 2
  AND p.eliminado = FALSE
  AND p.precio BETWEEN 1000 AND 3000
ORDER BY p.precio DESC;
```

**Regla:** gana el mejor **tiempo real** (`Execution Time` de EXPLAIN
ANALYZE), no el costo estimado. Protocolo del equipo: 2 corridas por
medición, se registra la segunda (caché caliente). La medición *antes* se tomó
sobre la copia sin índices propios (solo PK/UNIQUE del esquema); la *después*,
con el cambio aceptado aplicado.

## Registro

| Equipo | Estrategia aplicada | Tiempo antes (ms) | Tiempo después (ms) | Mejora (x) |
|---|---|---|---|---|
| **Comisión 4 — Equipo (este repo)** | Índice compuesto `idx_producto_cat_elim_precio ON producto (categoria_id, eliminado, precio)` — igualdad + igualdad + rango/orden. Se probó además la variante `INCLUDE (nombre, stock)` y se **descartó con datos** (abajo). | **13.580** | **4.941** | **2.75×** |
| (otros equipos — completar en clase) | … | … | … | … |

## Evidencia (planes completos)

| Momento | Archivo | Nodo crítico | Buffers | Execution Time |
|---|---|---|---|---|
| Antes (sin índice) | `planes/competencia_antes.txt` | `Sort` (quicksort, 300kB) ← `Seq Scan on producto`, Filter con **Rows Removed: 46.266** | shared hit=1728 | **13.580 ms** |
| Después (I1 aplicado) | `planes/competencia_despues.txt` | `Sort` ← `Bitmap Heap Scan` (Heap Blocks exact=860) ← `Bitmap Index Scan on idx_producto_cat_elim_precio`, **Index Cond con las 3 condiciones** (categoria_id=2, eliminado=false, precio 1000..3000) | shared hit=882 (37→19 de índice) | **4.941 ms** |
| Variante INCLUDE | `planes/competencia_despues_include.txt` | El planner **no eligió** el índice INCLUDE: mismo plan Bitmap sobre el índice simple | shared hit=882 | 4.798 ms (ruido) |

## Bitácora del equipo: qué se probó, qué se aceptó, qué se descartó y por qué

1. **Aceptado — índice compuesto (categoria_id, eliminado, precio):** las dos
   igualdades como prefijo dejan el rango de `precio` como tercera columna,
   así las tres condiciones entran al `Index Cond` y el bitmap devuelve solo
   los 3.737 TIDs candidatos (19 buffers de índice). Elimina la lectura de
   46.266 filas que no calificaban. Medido: 13.580 → 4.941 ms (2.75×).
2. **Descartado — `INCLUDE (nombre, stock)` (propuesta de la IA):** buscaba un
   Index Only Scan sin Sort (el índice INCLUDE entrega las filas en orden de
   precio y contiene todo el SELECT). Creado y medido en la copia: 2.888 kB
   contra 1.552 kB del simple (~1.9×), y el planner siguió eligiendo el Bitmap
   Heap Scan sobre el índice simple — tiempos 4.798 vs 4.941 ms, diferencia
   dentro del ruido. Con ~7,5% de la tabla en el resultado, el planner
   prefiere leer 860 bloques de heap ordenados por bloque (bitmap) antes que
   recorrer el índice ancho. Sin ganancia medible y con ~2× de costo de
   almacenamiento/escritura → `DROP INDEX`, documentado.
3. **Descartado — índice simple `(precio)`:** el filtro selectivo es la
   categoría (1/6 de la tabla); un índice solo de precio no resuelve las
   igualdades y obligaría a recorrer todo el rango 1000–3000 de las 6
   categorías. Rechazado en la revisión, sin llegar a aplicarse.
4. **Observación honesta:** el nodo `Sort` (3.737 filas, quicksort 300kB)
   sobrevive en el plan ganador: con esta cantidad de filas el planner estima
   más barato bitmap+sort que un Index Scan Backward ordenado con heap
   fetches. La ganancia de la competencia vino por el lado de los **buffers y
   las filas leídas** (1728→882; 50.003→3.737), no por eliminar el orden.

**Tiempo que defiende el equipo: 4.941 ms** (Execution Time real, segunda
corrida, plan en `planes/competencia_despues.txt`).
