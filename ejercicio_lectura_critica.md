# Ejercicio de Lectura Crítica — Parte 3

**TP:** 2 · Concurrencia e IA (Parte 3)
**Regla de fondo:** ningún script generado por IA se ejecuta sin leerse antes.

El objetivo de esta parte es reconocer, sobre casos reales, **por qué** ningún script se corre sin leerse: la sintaxis puede ser correcta y la intención razonable, pero un `WHERE` que falta o una subconsulta con `NULL` puede tocar filas que no eran las que se quería. Estos son los dos scripts "generados para dar de baja registros vencidos" de la consigna, sobre el esquema genérico de la cátedra.

---

## Script 1

```sql
-- Generado para: dar de baja las funciones de películas retiradas de cartel
UPDATE funcion
SET activa = FALSE;
```

### Qué filas afectaría realmente
Tal como está escrito, el `UPDATE` **sin cláusula `WHERE`** modifica **todas las filas de la tabla `funcion`**: tanto las de películas retiradas de cartel como las películas **en cartel** y las funciones **ya pasadas**. Es decir, afecta el 100 % de la tabla (todas las funciones existentes pasan a `activa = FALSE`).

### Por qué eso no coincide con la consigna
La consigna dice: dar de baja **las funciones de películas retiradas de cartel** (un subconjunto). El script sin `WHERE` da de baja **todo**, no el subconjunto pedido. El efecto es idéntico al caso Replit de la teoría: un agente con el código "correcto" pero la **condición ausente** borró/afectó mucho más de lo solicitado.

En el esquema del proyecto (FoodStore), este mismo error aparecería por ejemplo como
```sql
UPDATE producto SET activo = FALSE;   -- daria de baja TODOS los productos, no solo los retirados
```
Donde a simple vista parece trivial pero afecta toda la tabla.

### Versión corregida
Hay que limitar el `UPDATE` con un `WHERE` que identifique exactamente el subconjunto "funciones de películas retiradas de cartel". En el esquema genérico de cátedra, la película vive en `funcion.pelicula_id` con el estado en otra tabla (o en la misma con un atributo de película); asumimos que `funcion` referencia la película por `pelicula_id` y que la película tiene `en_cartel`:

```sql
UPDATE funcion
SET activa = FALSE
WHERE pelicula_id IN (
    SELECT id FROM pelicula WHERE en_cartel = FALSE
);
```

> En el proyecto FoodStore, el equivalente corregido para "dar de baja solo los productos de una categoría retirada" sería:
> ```sql
> UPDATE producto
> SET activo = FALSE
> WHERE categoria_id IN (SELECT id FROM categoria WHERE activo = FALSE);
> ```

**Regla práctica:** un `UPDATE` (o `DELETE`) de producción sin `WHERE` es una señal de alarma. Si la consigna menciona un subconjunto, debe haber `WHERE`.

---

## Script 2

```sql
-- Generado para: limpiar las categorías sin productos asociados
DELETE FROM categoria
WHERE id NOT IN (SELECT categoria_id FROM producto);
```

### Qué filas afectaría realmente
La intención es borrar las categorías que no tienen ningún producto. Pero la subconsulta `SELECT categoria_id FROM producto` **puede devolver `NULL`** — por ejemplo, si alguna fila de `producto` tuviera `categoria_id` nulo (en este proyecto la FK lo prohíbe, pero en el esquema genérico la columna puede ser nullable). El operador `NOT IN` es delicado con `NULL`: si el conjunto de la subconsulta contiene aunque sea **un** `NULL`, la condición `id NOT IN (...)` nunca es cierta (**siempre es NULL**), y el `DELETE` **no borra ninguna fila**.

Efecto real del script:
- Si `producto.categoria_id` es **nullable** y existe al menos un `NULL` → el `DELETE` afecta **0 filas** (no limpia nada).
- Si ninguna fila tiene `NULL` → sí borra las categorías sin productos (lo deseado).

### Por qué eso no coincide con la consigna
Depende del estado de los datos:
- **Con un `NULL`** en `producto.categoria_id`: la consigna pide "limpiar las categorías sin productos", pero el script **no borra nada**. Además, de forma insidiosa, la categoría sin productos queda intacta (no cumple la consigna) **en silencio**, sin error.
- **Sin `NULL`**: funciona, pero el comportamiento correcto depende de un detalle de datos que el `NOT IN` oculta.

La regla de oro es: **`NOT IN` es peligroso con `NULL`**; la versión segura es usar `NOT EXISTS`, que maneja bien los `NULL`.

### Versión corregida (manejo de NULL)
Se usa `NOT EXISTS` para que la lógica sea correcta aunque haya `NULL` en `producto.categoria_id`:

```sql
DELETE FROM categoria c
WHERE NOT EXISTS (
    SELECT 1 FROM producto p WHERE p.categoria_id = c.id
);
```

Con `NOT EXISTS`, los `NULL` de `categoria_id` simplemente no matchean ningún `c.id`, así que se borran exactamente las categorías sin productos, sin importar si hay nulos. Es la recomendación estándar frente a `NOT IN`.

> Nota sobre el proyecto FoodStore: en `schema.sql` la FK `producto.categoria_id` es `NOT NULL`, así que en rigor no podría haber `NULL` y el `NOT IN` funcionaría. Pero en un esquema genérico —y por defensa del código— conviene igual usar `NOT EXISTS`, porque la restricción puede no existir en todas las tablas y elimina el riesgo de raíz.
> Además, en FoodStore las categorías usan **baja lógica** (`activo`), no borrado físico, así que la acción correcta del dominio sería `UPDATE categoria SET activo = FALSE WHERE NOT EXISTS (...)`.

---

## Patrón común de los casos reales (teoría)

En los incidentes documentados (Replit, Gemini CLI, PocketOS, confusión de entorno) el código era **sintácticamente válido** y la intención razonable. Lo que falló fue el paso del humano: confirmar contra qué base se corría, leer el **efecto real** del comando, y **no confiar en el reporte del agente**. Es exactamente lo que el protocolo de la Parte 0 obliga a interponer:

1. **Copia** — el error no toca nada real.
2. **Transacción** (`BEGIN ... ROLLBACK`) — permite inspeccionar las filas afectadas antes de confirmar.
3. **Respaldo** — para cuando ni siquiera la transacción alcanza.

Y, sobre los scripts, este ejercicio demuestra el caso concreto: un `UPDATE` sin `WHERE` (Script 1) y un `NOT IN` con `NULL` (Script 2) son dos formas en las que la sintaxis correcta produce un efecto distinto del consignado.