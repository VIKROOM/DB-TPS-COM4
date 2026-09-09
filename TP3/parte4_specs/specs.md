# TP3 · Parte 4 — Especificaciones precisas (specs)

Las dos specs siguientes se redactaron **antes** de pedir el SQL a la IA y fijan
explícitamente: tablas involucradas, filtro de borrado lógico, columnas de
salida (y sus alias), orden y criterio de corte. Esquema destino: Food Store
(base `foodstore_tp3`, PostgreSQL 17).

---

## Spec A — Consulta de resumen (agregación)

> Generá una consulta SQL para PostgreSQL 17 sobre el esquema Food Store que
> devuelva, **para cada categoría vigente** (`categoria.eliminado = FALSE`), el
> nombre de la categoría y la cantidad de **productos vigentes**
> (`producto.eliminado = FALSE`) que pertenecen a ella.
>
> - Las categorías vigentes **sin productos vigentes deben aparecer con
>   cantidad 0** (no pueden quedar excluidas).
> - Un producto eliminado no cuenta, aunque su categoría esté vigente.
> - Columnas de salida, en este orden y con estos alias exactos:
>   `nombre_categoria`, `cantidad_productos`.
> - Orden: por `cantidad_productos` descendente; desempate por
>   `nombre_categoria` ascendente.
> - Prohibido `SELECT *`. Sin `LIMIT`. Sin CTEs ni funciones de ventana:
>   agregación con `JOIN` + `GROUP BY`.

**Versión generada por la IA:** `consulta_A_generada_ia.sql`
**Versión alternativa propia (subconsulta correlacionada en el SELECT-list,
sin JOIN ni GROUP BY):** `consulta_A_alternativa_propia.sql`

---

## Spec B — Consulta con subconsulta

> Generá una consulta SQL para PostgreSQL 17 sobre el esquema Food Store que
> devuelva los **usuarios vigentes** (`usuario.eliminado = FALSE`) que tengan
> **al menos un pedido vigente** (`pedido.eliminado = FALSE`) en estado
> `'TERMINADO'`.
>
> - Un usuario con varios pedidos TERMINADOS debe aparecer **una sola vez**.
> - Los pedidos eliminados no cuentan, aunque su estado sea TERMINADO.
> - Columnas de salida, en este orden: `nombre`, `apellido`, `mail`
>   (de `usuario`).
> - Orden: `apellido` ascendente, luego `nombre` ascendente, luego `mail`
>   ascendente (el mail es UNIQUE, así el orden es determinístico y la
>   verificación de equivalencia con `LIMIT` tiene sentido).
> - Corte: `LIMIT 25`.
> - Prohibido `SELECT *`. La condición de existencia debe resolverse con una
>   subconsulta (no con JOIN).

**Versión generada por la IA:** `consulta_B_generada_ia.sql` (subconsulta `IN`)
**Versión alternativa propia (misma pregunta, otra estructura de subconsulta):**
`consulta_B_alternativa_propia.sql` (`EXISTS` correlacionado)

---

## Verificación de equivalencia

`verificacion_equivalencia.sql` comprueba formalmente, sobre la base masiva:

1. `(A) EXCEPT (B)` y `(B) EXCEPT (A)` → ambas deben devolver **0 filas**.
2. Conteo de filas de cada versión → deben coincidir.
3. Lo mismo para B (con el `LIMIT 25` y el orden determinístico incluidos).
4. **Caso borde de Spec A dentro de una transacción con ROLLBACK**: se marca
   una categoría como eliminada y se eliminan lógicamente todos los productos
   de otra (para forzar el caso "categoría vigente con cantidad 0"); ambas
   versiones deben seguir siendo equivalentes también ahí. El ROLLBACK
   garantiza que la base de trabajo no cambia.

Salida real de la ejecución: `salida_verificacion.txt`.
