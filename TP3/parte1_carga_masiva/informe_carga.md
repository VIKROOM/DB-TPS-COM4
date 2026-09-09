# TP3 · Parte 1 — Carga masiva: informe de ejecución y verificación

**Base de trabajo:** `foodstore_tp3` (copia) · **Base de producción:**
`foodstore` (NO tocada — verificación al final) · **Motor:** PostgreSQL 17.10
**Script de carga:** `Genera_registros.sql` (archivo provisto por la cátedra)
**Fecha de ejecución:** 2026-09-08 · Cliente: `psql`

---

## 1. Protocolo de seguridad aplicado (copia, transacción, respaldo)

1. **Copia:** la carga corre únicamente sobre `foodstore_tp3`. La copia se
   reconstruyó limpia desde plantilla para este trabajo:
   `DROP DATABASE foodstore_tp3; CREATE DATABASE foodstore_tp3 TEMPLATE foodstore;`
   (la copia preexistente tenía datos de una sesión anterior; se respaldó antes
   de reemplazarla).
2. **Respaldo previo** (`pg_dump -Fc`), en
   `D:\0001-UTN\1PRO4 CUAT2\base de datos\Unidad 2\Tp3\backups\`:
   - `foodstore_tp3_previo_20260908_210757.dump` (5,8 MB) — estado anterior de
     la copia, antes de reconstruirla.
   - `foodstore_tp3_cargada_20260908_211548.dump` (3,8 MB) — copia ya cargada
     con el script provisto, tomada **antes** de aplicar la corrección de
     distribución (punto 5).
3. **Transacción:** `Genera_registros.sql` trae su propio `BEGIN ... COMMIT`;
   se ejecutó con `psql -v ON_ERROR_STOP=1`, de modo que cualquier error
   aborta todo (no hay cargas parciales). La corrección del punto 5 también es
   una única transacción.
4. **ANALYZE:** el propio script termina con `ANALYZE` de las 4 tablas
   afectadas; se repitió tras la corrección y se agregó `VACUUM ANALYZE` antes
   de las mediciones de la Parte 2 (visibility map al día para que los
   index-only scan sean comparables).

## 2. Lectura línea por línea del script provisto (antes de ejecutarlo)

| Líneas | Qué hace | Restricciones que toca | Veredicto |
|---|---|---|---|
| 3–9 | Inserta 50.000 productos `'Producto '‖i` con `precio = random()*4500+500` (500–5000), `stock = random()*200` (0–200) y categoría sorteada | `CHECK precio>=0` ✓ · `CHECK stock>=0` ✓ · FK `categoria_id` (subconsulta sobre categorías existentes) ✓ · no hay UNIQUE sobre `producto.nombre` en el esquema, y los nombres `'Producto i'` son distintos entre sí ✓ | OK |
| 11–16 | Inserta 20.000 usuarios `usuario{i}@test.com` | `UNIQUE (usuario.mail)`: los mails generados son distintos entre sí y no chocan con el seed ✓ · `contrasena NOT NULL` ✓ | OK |
| 18–25 | Inserta 200.000 pedidos con `fecha = CURRENT_DATE - random()*365`, estado y forma de pago sorteados de los ENUM, usuario sorteado | ENUM `estado_pedido`/`forma_pago`: los literales de los ARRAY coinciden exactamente con los valores del dominio ✓ · FK `usuario_id` ✓ · `fecha NOT NULL` ✓ | OK |
| 27–41 | Genera 1–4 líneas por pedido con productos aleatorios y `cantidad = random()*3+1` (1–4); `ON CONFLICT (pedido_id, producto_id) DO NOTHING` | `CHECK cantidad>0` ✓ · PK compuesta de `detalle_pedido`: el ON CONFLICT cubre los sorteos duplicados dentro del mismo pedido ✓ · FKs `pedido_id`/`producto_id` ✓ | OK |
| 43 | `ANALYZE` de las 4 tablas | — | OK, exigido por la consigna |

El script **no toca** la base `foodstore` (producción): corre conectado a la
copia. Conclusión de la revisión: respeta CHECK, UNIQUE y FK; se aprueba su
ejecución.

## 3. Ejecución real (evidencia: `salida_carga.txt`)

Corrida con `\timing on` sobre `foodstore_tp3`:

| Paso | Filas | Tiempo |
|---|---|---|
| INSERT producto | 50.000 | 512 ms |
| INSERT usuario | 20.000 | 235 ms |
| INSERT pedido | 200.000 | 1.862 ms |
| INSERT detalle_pedido | 622.415 | 10.035 ms |
| COMMIT | — | 1,4 ms |
| ANALYZE ×4 | — | 219 + 324 + 44 + 57 ms |

## 4. Verificación posterior (evidencia: `salida_verificacion_inicial.txt`)

Cumple: conteos mínimos (50.003 productos ≥ 50.000 · 20.003 usuarios ≥ 20.000
· 200.001 pedidos ≥ 200.000 · 622.417 detalles), rangos de precio/stock
(0 fuera de rango), FKs sin huérfanos, mails sin duplicados, cantidad 1–4,
fechas dentro del último año, ENUMs cubiertos (4 estados × 3 formas de pago),
`last_analyze` poblado en las 4 tablas.

**PERO la verificación detectó un defecto de distribución** (la consigna exige
productos "distribuidos en las categorías existentes"):

```
 id |    nombre    | productos          usuarios_con_pedidos: 2 (uno con 200.000)
----+--------------+-----------         productos_distintos_en_detalles: 6
  1 | Hamburguesas |         1
  2 | Pizzas       |     50001          <-- los 50.000 generados, todos acá
  3 | Bebidas      |         1
  4 | Postres      |         0
  5 | Ensaladas    |         0
  6 | Sándwiches   |         0
```

Las ~622.000 líneas de detalle, además, referenciaban **solo 6 productos
distintos**, y los 200.000 pedidos pertenecían a **un único usuario** (id
17837).

## 5. Causa del defecto y corrección

**Causa:** las tres subconsultas no correlacionadas con `ORDER BY random()`
—`(SELECT id FROM categoria ORDER BY random() LIMIT 1)`, `(SELECT id FROM
usuario ORDER BY random() LIMIT 1)` y el `CROSS JOIN LATERAL (SELECT id FROM
producto ORDER BY random() LIMIT 4)`— fueron resueltas como **InitPlan** y
evaluadas **una sola vez** al inicio de la sentencia, no por fila: el sorteo
devolvió siempre la misma categoría, el mismo usuario y los mismos 4
productos. (Las funciones `random()` simples del SELECT-list —precio, stock,
fecha, estado, cantidad— sí se evaluaron por fila; esas columnas salieron bien
distribuidas.)

**Corrección:** `correccion_distribucion.sql` (generada con asistencia de IA,
revisada línea a línea y aceptada por el equipo; el script provisto por la
cátedra no se modifica). Con respaldo previo (punto 1.3) y en una única
transacción, redistribuye los datos ya cargados con randomizaciones por fila
garantizadas (expresiones en SELECT-list de CTEs `MATERIALIZED` + cruces por
`row_number()`):

1. productos generados → categorías (round-robin sobre permutación aleatoria:
   distribución exactamente pareja);
2. pedidos generados → usuarios (uniforme);
3. detalles de pedidos generados → se regeneran con 1–4 líneas por pedido y
   productos realmente aleatorios por fila.

Ejecución real (`salida_correccion.txt`): `UPDATE 50000` (937 ms),
`UPDATE 200001` (3,6 s), `DELETE 622417` (1,5 s), `INSERT 500365` (12,2 s),
`COMMIT` + `ANALYZE` ×4.

> Nota de revisión: el filtro "solo generados" usaba `mail LIKE '%@test.com'`,
> pero los usuarios seed de la cátedra también usan ese dominio
> (`maria@test.com`, etc.), por eso el UPDATE tocó 200.001 pedidos (el pedido
> seed también cambió de dueño) y el DELETE/INSERT regeneró también sus 2
> líneas. Se documenta como desvío menor aceptado: no viola ninguna
> restricción y la base es una copia de trabajo.

## 6. Estado final verificado (evidencia: `salida_verificacion_final.txt`)

| Verificación | Resultado |
|---|---|
| Conteos | 6 categorías · **50.003** productos · **20.003** usuarios · **200.001** pedidos · **500.365** detalles |
| Distribución por categoría | 8.335 / 8.335 / 8.334 / 8.333 / 8.333 / 8.333 ✓ pareja |
| Pedidos por usuario | 20.003 usuarios con pedidos, promedio 10, máximo 10 ✓ |
| Detalles | 49.998 productos distintos, 1–4 líneas por pedido (promedio 2,50) ✓ |
| Rangos / CHECK / UNIQUE / FK | 0 fuera de rango · 0 huérfanos · 0 mails duplicados · cantidad 1–4 ✓ |
| Estadísticas | `last_analyze` en las 4 tablas + `VACUUM ANALYZE` posterior ✓ |
| Producción intacta | `foodstore`: 3 productos · 1 pedido · 2 detalles (sin cambios) ✓ |

**Conclusión:** la base de trabajo cumple los volúmenes y la distribución que
exige la consigna, con el script provisto como instrumento de carga y una
corrección documentada del defecto de distribución detectado al verificarlo.
Lista para las mediciones de la Parte 2.
