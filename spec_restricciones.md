# Spec — Restricciones de integridad para Food Store (Parte 1)

> Regla de fondo: _se delega la escritura, nunca la decisión_. Esta spec se escribe **antes** de generar el script, porque una spec ambigua produce un script ambiguo.

**Motor objetivo:** PostgreSQL 17 · **Base de trabajo:** `foodstore_tp2` (copia)
**Tablas involucradas:** `cliente`, `producto`, `pedido`, `linea_pedido`

---

## Regla 1 — Clientes inactivos no pueden generar pedidos nuevos

- **Tabla/columna:** se valida en `pedido` al insertar, leyendo `cliente.activo`.
- **Enunciado:** un pedido nuevo no puede pertenecer a un cliente dado de baja (`cliente.activo = FALSE`).
- **Por qué:** el esquema usa baja lógica (R7). Si un cliente está inactivo, no debe seguir operando (generar compras). Hoy esto lo valida la aplicación; con el trigger queda garantizado en el motor.
- **Comportamiento esperado:** `INSERT INTO pedido (cliente_id, forma_pago) ...` para un cliente inactivo → error.

## Regla 2 — Productos inactivos no se pueden vender en líneas nuevas

- **Tabla/columna:** se valida en `linea_pedido` al insertar, leyendo `producto.activo`.
- **Enunciado:** una línea de pedido nueva no puede referenciar un producto dado de baja (`producto.activo = FALSE`).
- **Por qué:** la baja lógica (R7) implica que un producto retirado no sigue vendiéndose. Requiere un trigger porque combina dos tablas.
- **Comportamiento esperado:** `INSERT INTO linea_pedido` con un `producto_id` inactivo → error.

## Regla 3 — La cantidad vendida no puede superar el stock disponible

- **Tabla/columna:** se valida en `linea_pedido` al insertar y al actualizar `cantidad`, comparando con `producto.stock`.
- **Enunciado:** `linea_pedido.cantidad <= producto.stock` para el producto de esa línea.
- **Por qué:** control de stock (R5: `stock >= 0`). Evita vender más unidades de las que hay en el depot. Requiere trigger porque interviene `producto.stock`.
- **Comportamiento esperado:** `INSERT`/`UPDATE` de una línea con `cantidad > producto.stock` → error.

---

## Alcance / fuera de alcance

- **Dentro:** triggers `BEFORE INSERT`/`BEFORE UPDATE` y `RAISE EXCEPTION` con mensajes descriptivos.
- **Fuera:** actualización automática de `stock` al vender (eso es lógica de negocio transaccional, no una restricción de integridad; se documenta como decisión).
- **Fuera:** descontar stock automáticamente. Se mantiene solo la regla que **impide** vender de más.
