# TP3 · Parte 3 — Explicación generada por IA del plan real

**Protocolo seguido:** se le entregó a la IA (OpenCode) **únicamente** el texto
del plan `plan_analizado.txt` (la consulta C2 de la Parte 2, con el índice
`idx_pedido_usu_elim_fecha` ya aplicado) y se le pidió: *"Explicá este plan de
EXPLAIN ANALYZE en lenguaje natural, nodo por nodo, para alguien que está
aprendiendo a leer planes."* No se le mostró la consulta SQL, el esquema, ni
ningún otro contexto.

**Respuesta de la IA (transcripción literal):**

---

El plan tiene un único nodo, así que la consulta se resuelve en un solo paso:

1. **Nodo raíz — `Index Scan Backward using idx_pedido_usu_elim_fecha on
   pedido pe`:** PostgreSQL recorre el índice `idx_pedido_usu_elim_fecha` de la
   tabla `pedido` en dirección inversa (de atrás hacia adelante). El costo
   estimado de la consulta va de **0,42 a 24,37 milisegundos**: arranca en
   0,42 ms (lo que tarda en devolver la primera fila) y llega a 24,37 ms al
   completar las 10 filas.

2. **`Index Cond: ((usuario_id = 1000) AND (eliminado = false))`:** el índice
   filtra directamente por el usuario 1000 y descarta los registros eliminados.
   En vez de recorrer la tabla `pedido` entera, el motor salta directo a las
   entradas del índice que cumplen ambas condiciones.

3. **Gracias al índice no se accede a la tabla `pedido`:** todos los datos que
   necesita la consulta se obtienen del propio índice, sin tocar las filas
   reales de la tabla.

4. **La dirección `Backward` indica que el índice fue creado en orden
   descendente** (`fecha DESC`), por eso lo recorre "al revés" de lo habitual.

5. **`(actual time=0.038..0.041 rows=10 loops=1)`:** en la ejecución real, el
   nodo devolvió la primera fila a los 0,038 ms y terminó a los 0,041 ms. Como
   el tiempo total de la consulta es 24,37 ms, la diferencia se va en el
   recorrido del índice.

6. **`rows=10` (estimado) contra `actual rows=10`:** el planificador predijo
   exactamente la cantidad de filas, señal de que las estadísticas están al
   día. `width=20` indica que cada fila ocupa en promedio 20 bytes.

7. **`Buffers: shared hit=8`:** la consulta leyó 8 filas desde los buffers
   compartidos (la memoria caché de PostgreSQL); ninguna lectura fue a disco
   (`read=0` implícito), así que todo estaba cacheado.

8. **Tiempos finales — `Planning Time: 1.846 ms` y `Execution Time: 0.164
   ms`:** el Execution Time ya incluye al Planning Time, de modo que la
   consulta completa tardó 0,164 ms en total. `loops=1` confirma que el nodo
   se ejecutó una sola vez.

---

*La explicación anterior se contrasta frase por frase contra el plan real en
`lectura_critica.md`.*
