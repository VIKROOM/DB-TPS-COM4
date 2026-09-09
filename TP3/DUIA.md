# TP3 · Declaración de Uso de IA (DUIA)

**TP:** 3 · Optimización asistida por IA sobre Food Store (Unidad 2, Semana 3)
**Esquema:** Food Store (proyecto integrador) · **Motor:** PostgreSQL 17.10
**Base de trabajo:** `foodstore_tp3` (copia, según protocolo de seguridad de la
cátedra; la base `foodstore` de producción no fue modificada — verificado)
**Política aplicada:** la IA propone, el estudiante verifica. Ningún script,
índice o reescritura se ejecutó sin lectura línea por línea; ninguna propuesta
se aceptó sin medición real (EXPLAIN ANALYZE) o sin una razón de revisión
explicada.

---

## Tabla de usos relevantes (formato de la consigna)

| Herramienta | Para qué se usó | Prompt / spec (resumen) | Se aceptó / se descartó — por qué |
|---|---|---|---|
| OpenCode | **Parte 1** — Revisión línea por línea del script provisto `Genera_registros.sql` contra el esquema real (volcado con `pg_dump --schema-only`) y verificación posterior a la carga (conteos, rangos, FK, UNIQUE, distribución) | "Verificá el script de carga contra las restricciones reales del esquema (CHECK, UNIQUE, FK, ENUM) y comprobá el resultado de la carga sobre la copia" | **Aceptado** el protocolo de verificación. La verificación **detectó un defecto real** del script: sus subconsultas `ORDER BY random()` no correlacionadas se evaluaron una sola vez (InitPlan) → 50.000 productos en 1 categoría, 200.000 pedidos de 1 usuario, 622 mil detalles sobre 6 productos. Confirmado con datos antes de actuar. |
| OpenCode | **Parte 1** — Generación de `correccion_distribucion.sql` | "Corregí la distribución sin violar restricciones y sin tocar la base de producción: redistribuí productos→categorías y pedidos→usuarios en forma uniforme, y regenerá los detalles con aleatoriedad real por fila (CTE MATERIALIZED + row_number), todo en una transacción y con ANALYZE final" | **Aceptado con modificaciones**: la lectura línea a línea reveló que el filtro `mail LIKE '%@test.com'` también alcanzaba a los usuarios seed (usan ese dominio) — desvío menor, documentado en `informe_carga.md`. Se verificó la lógica rn/módulo/hashtext y la salida real (UPDATE 50000 · UPDATE 200001 · DELETE 622417 · INSERT 500365) y la distribución final (8.333–8.335 por categoría, 10 pedidos por usuario, 49.998 productos distintos en detalles). |
| OpenCode | **Parte 2** — Propuesta de índices y reescrituras a partir de los planes reales *antes* (C1, C2, C3) | "Acá están los EXPLAIN (ANALYZE, BUFFERS) reales de tres consultas lentas sobre la base masiva; proponé reescrituras y/o índices que los mejoren, justificando qué nodo ataca cada propuesta" | **Aceptadas** I1 `(categoria_id, eliminado, precio)`, I2 `(usuario_id, eliminado, fecha)`, I3 `(producto_id, cantidad)` tras revisar cada DDL y medir después: 1.36× / 225× / 2.42×. **Descartadas:** índice `(precio)` solo (no ataca el filtro selectivo), reescritura con funciones de ventana para C3 (no ataca ningún nodo del plan real), y la variante `INCLUDE (nombre, stock)` — **probada y descartada con datos**: el planner no la eligió y 4.798 vs 4.941 ms es ruido, con ~1.9× de tamaño. La predicción de la IA "el Sort desaparece" (I1) **no se cumplió**; el índice se aceptó igual por la caída de buffers (1728→904) y se documentó el desvío. |
| OpenCode | **Parte 3** — Explicación en lenguaje natural, nodo por nodo, del plan real de C2 *después* (solo se le dio el texto del plan) | "Explicá este plan de EXPLAIN ANALYZE en lenguaje natural, nodo por nodo, para alguien que aprende a leer planes" (sin SQL, sin esquema, sin más contexto) | **Usado como insumo del ejercicio**, no como verdad: la auditoría frase por frase (`lectura_critica.md`) marcó **6 de 13 afirmaciones incorrectas o imprecisas** — costo estimado leído como milisegundos (×3), "el índice evita acceder a la tabla" (es Index Scan, no Index Only: sí toca el heap), `Backward` atribuido a un DDL `DESC` inexistente, `shared hit=8` leído como filas en vez de páginas, y "Execution Time incluye Planning Time" (falso). Cada corrección se verificó contra el plan guardado y el DDL real del índice. |
| OpenCode | **Parte 4** — Generación de SQL a partir de las specs precisas A (resumen) y B (subconsulta), sin mostrarle ninguna solución previa | Spec A: categorías vigentes + cantidad de productos vigentes (incluidas las de cantidad 0), alias fijos, orden definido, sin SELECT *, JOIN+GROUP BY. Spec B: usuarios vigentes con ≥1 pedido vigente TERMINADO, columnas fijas, orden determinístico (mail UNIQUE), LIMIT 25, subconsulta | **Aceptado tras revisión**: en A, el punto crítico es `COUNT(p.id)` (con `COUNT(*)` las categorías vacías darían 1, violando la spec) y el filtro `p.eliminado = FALSE` en el `ON` (en el `WHERE` excluiría las categorías sin productos vigentes). En B, se verificó que `IN` no duplica filas y que `usuario_id NOT NULL` elimina la diferencia teórica IN/EXISTS por NULLs. **Equivalencia verificada formalmente** contra la versión alternativa propia: `EXCEPT` en ambos sentidos = 0 filas, conteos iguales, y caso borde (categoría eliminada + categoría vaciada) probado dentro de una transacción con `ROLLBACK`. |
| OpenCode | **Parte 5** — Estrategia para la consulta común de la competencia | "Medí y compará estrategias (índices, variantes INCLUDE, reescrituras) sobre la consulta común fijada; registrá tiempos reales antes/después" | **Aceptado** el índice I1 como estrategia (13.580 → 4.941 ms, 2.75×). **Descartada** la variante INCLUDE con la medición real (ver fila Parte 2). Registro completo y bitácora de decisiones en `registro_competencia.md`. |
| Kiro | — | — | **No utilizado** en esta entrega: el equipo trabajó la práctica completa con OpenCode. |

---

## Verificación humana (resumen del equipo)

- Todo script (el provisto por la cátedra, los generados por la IA y los
  propios) fue **leído línea por línea antes de ejecutarse**; los que se
  aceptaron están en este repo tal como se ejecutaron.
- Toda ejecución destructiva o masiva corrió sobre la **copia**
  `foodstore_tp3`, dentro de **transacciones**, con **respaldos `pg_dump -Fc`**
  previos en `Tp3\backups\` (paths y tamaños en `informe_carga.md`). La base
  `foodstore` quedó verificada como intacta (3 productos · 1 pedido · 2
  detalles).
- Ninguna propuesta de la IA se aplicó "porque lo dijo la IA": cada índice
  aceptado tiene su plan *antes*, su justificación nodo por nodo y su plan
  *después* con la medición real; cada propuesta descartada tiene su razón (de
  revisión o de medición) documentada.
- Las afirmaciones de la IA sobre planes (Parte 3) se contrastaron contra los
  planes guardados en texto, no contra la memoria de la corrida.
- Para la **defensa oral** el equipo debe poder explicar: por qué el orden
  igualdad→igualdad→rango/orden en I1 e I2; por qué I3 habilita Index Only
  Scan con `Heap Fetches: 0` (y el rol del VACUUM previo); por qué C1 mejoró
  poco y el Sort sobrevivió; por qué se descartó el INCLUDE; y la causa del
  defecto InitPlan del script de carga.
