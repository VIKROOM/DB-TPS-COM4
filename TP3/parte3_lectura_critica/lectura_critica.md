# TP3 · Parte 3 — Lectura crítica de la explicación generada por IA

**Plan analizado:** `plan_analizado.txt` (consulta C2 de la Parte 2 —historial
de pedidos de un usuario— con `idx_pedido_usu_elim_fecha` aplicado, medido en
real sobre `foodstore_tp3`).
**Explicación auditada:** `explicacion_ia.md` (generada por OpenCode a partir
solo del texto del plan).
**Método:** contraste frase por frase contra el plan real y contra el DDL del
índice (`../parte2_laboratorio/indices.sql`). Se marca ✅ lo correcto y ❌ lo
incorrecto o impreciso, con la evidencia.

---

## Tabla de hallazgos

| # | Afirmación de la IA | ¿Correcta? | Corrección / evidencia del plan real |
|---|---|---|---|
| 1 | "El plan tiene un único nodo: Index Scan Backward sobre `pedido` usando `idx_pedido_usu_elim_fecha`" | **Sí** ✅ | El plan muestra exactamente un nodo, sin hijos. La lectura estructural es correcta. |
| 2 | "El costo estimado va de **0,42 a 24,37 milisegundos**" | **No** ❌ | **Confunde costo estimado con tiempo real.** `cost=0.42..24.37` está en **unidades arbitrarias de costo** del planificador (referidas al costo de lectura secuencial de una página), no en milisegundos. El tiempo real de la corrida está en otra parte del plan: `Execution Time: 0.164 ms`. Son ~150 veces distintos: si 24.37 fueran ms, la consulta habría tardado eso, no 0.164 ms. |
| 3 | "Arranca en 0,42 ms (lo que tarda en devolver la primera fila)" | **No** ❌ | Mezcla dos conceptos: el **startup cost** (0.42, unidades de costo) con el **startup time real** (`actual time=0.038..`: la primera fila llegó a los 0,038 ms). El número en ms del arranque real es 0.038, no 0.42. |
| 4 | "`Index Cond: (usuario_id = 1000 AND eliminado = false)`: el índice filtra por ambas condiciones y evita recorrer la tabla entera" | **Sí** ✅ | Correcto y verificable: ambas condiciones aparecen como `Index Cond` (no como `Filter`), es decir se resuelven dentro del recorrido del índice. Comparar con el plan *antes* (`C2_antes.txt`): allí el `Parallel Seq Scan` leía las 200.001 filas y descartaba 66.664 por trabajador con `Rows Removed by Filter`. |
| 5 | "Gracias al índice **no se accede a la tabla `pedido`**: todos los datos se obtienen del propio índice" | **No** ❌ | **Atribuye al índice una propiedad que no tiene.** El nodo es `Index Scan`, **no** `Index Only Scan`: por cada entrada del índice **sí visita la fila del heap** para obtener `id`, `estado` y `forma_pago`, columnas que el índice `(usuario_id, eliminado, fecha)` no contiene. Los `shared hit=8` incluyen páginas del índice **y** del heap. Quien sí evita el heap es el índice cubriente de C3 (`C3_despues.txt`: `Index Only Scan ... Heap Fetches: 0`). |
| 6 | "La dirección `Backward` indica que el índice fue creado en orden descendente (`fecha DESC`)" | **No** ❌ | **Atribuye la causa al revés.** El índice se creó con el orden ascendente por defecto: `CREATE INDEX idx_pedido_usu_elim_fecha ON pedido (usuario_id, eliminado, fecha)` (ver `indices.sql`). `Backward` significa que el executor **recorre** ese índice ASC de atrás hacia adelante para satisfacer el `ORDER BY fecha DESC` de la consulta sin agregar un nodo `Sort`. Es una propiedad de la lectura, no del DDL. |
| 7 | "`actual time=0.038..0.041`: primera fila a los 0,038 ms, fin a los 0,041 ms" | **Sí** ✅ | Interpretación correcta del par startup..total en ms para el nodo, `loops=1`. |
| 8 | "Como el tiempo total de la consulta es 24,37 ms, la diferencia se va en el recorrido del índice" | **No** ❌ | Reincide en el error #2: inventa un "tiempo total" de 24,37 ms que no existe en el plan. El tiempo total real es `Execution Time: 0.164 ms`, y el nodo terminó a los 0,041 ms. No hay ninguna "diferencia" que explicar; el resto hasta 0,164 ms es apertura/cierre del executor. La frase construye una narrativa causal sobre un número mal interpretado. |
| 9 | "El planificador predijo exactamente la cantidad de filas (`rows=10` estimado vs `actual rows=10`): estadísticas al día" | **Sí** ✅ | Correcto: el estimado del nodo (10) coincide con el real (10). Coherente con el `ANALYZE pedido` ejecutado tras crear el índice y con la distribución uniforme lograda en la Parte 1 (~10 pedidos por usuario). |
| 10 | "`width=20`: cada fila ocupa en promedio 20 bytes" | **Sí** ✅ | Correcto: es el ancho promedio estimado (en bytes) de las columnas proyectadas por el nodo. |
| 11 | "`Buffers: shared hit=8`: la consulta leyó **8 filas** desde los buffers compartidos" | **No** ❌ | **Confunde filas con páginas.** `shared hit=8` son **8 bloques (páginas) de 8 KB** encontrados en shared buffers (nivel `hit`, sin ir a disco). Con 10 filas devueltas en 8 páginas (índice + heap), leer "8 filas" no tendría sentido: el plan dice `rows=10`. La ausencia de `shared read` confirma que ninguna página requirió lectura de disco. |
| 12 | "`Execution Time` ya incluye al `Planning Time`, la consulta completa tardó 0,164 ms en total" | **No** ❌ | Falso: PostgreSQL reporta `Planning Time` y `Execution Time` **por separado** y el `Execution Time` **no** incluye la planificación (mide de arranque a cierre del executor). El tiempo total de la sentencia para el cliente es ≈ 1.846 + 0.164 ≈ 2,01 ms. Dato relevante: en esta consulta ya optimizada **la planificación tarda ~11 veces más que la ejecución**; la IA lo invierte. |
| 13 | "`loops=1` confirma que el nodo se ejecutó una sola vez" | **Sí** ✅ | Correcto. (Contraste con `C2_antes.txt`, donde el nodo paralelo mostraba `loops=3`: líder + 2 trabajadores.) |

---

## Síntesis de la lectura crítica

De 13 afirmaciones auditadas, **7 son correctas y 6 son incorrectas o
imprecisas**. Los tres patrones de error que advierte la consigna aparecen
literalmente en la explicación:

1. **Confundir costo estimado con milisegundos** (afirmaciones 2, 3 y 8): todo
   el primer párrafo construye una escala de tiempos ficticia a partir de
   `cost=0.42..24.37`.
2. **Atribuir la mejora a la causa equivocada** (afirmaciones 5 y 6): le da al
   índice propiedades de *index only scan* que no tiene (la consulta sí toca el
   heap) y explica el `Backward` como una propiedad del DDL cuando es una
   decisión de lectura del executor; además ignora que la verdadera ganancia
   frente al plan *antes* es haber eliminado el `Parallel Seq Scan` de 200.001
   filas y el `Sort`, no "evitar la tabla".
3. **Ignorar o tergiversar contadores** (afirmaciones 11 y 12): `shared hit`
   son páginas, no filas; `Execution Time` no incluye `Planning Time`.

**Conclusión del equipo:** la explicación de la IA sirve como primer borrador
de lectura (identifica bien los nodos, el Index Cond y las estimaciones de
filas), pero **no se puede confiar en su interpretación de unidades ni en sus
atribuciones causales**: cada número debe contrastarse contra el plan real y
cada "porque" contra el DDL y el plan anterior. Para la defensa oral, el equipo
debe poder explicar por qué el plan mejoró: índice compuesto
`(usuario_id, eliminado, fecha)` → Index Cond de igualdad en las dos primeras
columnas + orden por la tercera → acceso directo a ~10 filas y desaparición
del `Sort` (recorrido *backward*), 36,934 ms → 0,164 ms.
