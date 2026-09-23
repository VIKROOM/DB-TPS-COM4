# Spec — Procedimientos almacenados en PL/pgSQL (Parte D / Objetivo 6 del TPI)

> Regla de fondo: _se delega la escritura, nunca la decisión_. Esta spec se
> escribe **antes** de generar el script. Un procedimiento mal especificado no
> existe: defino contrato de entrada/salida, reglas de negocio y criterio de
> verificación antes de escribir el primer `CREATE PROCEDURE`.

**Motor objetivo:** PostgreSQL 17 · **Base de trabajo:** `foodstore_u3` (copia)
**Objetivo general del TPI que cubre:** "Vistas, funciones y **procedimientos
almacenados** desarrollados en PL/pgSQL" — hoy el repo tiene vistas y funciones
trigger, pero **ningún procedimiento almacenado** con `CALL`. Esta es la pieza
faltante de la entrega.

---

## Procedimiento P1 — `registrar_pedido`

Registro de venta transaccional realizado **en el motor**: inserta el pedido,
inserta sus líneas (con el precio congelado del producto) y descuenta el stock,
todo dentro de una única transacción. Es el complemento natural de los triggers
de integridad (R1/R2/R3) ya existentes: mientras esos triggers **impiden** lo
inválido, este procedimiento implementa la **operación válida completa**.

### Contrato

- **Nombre:** `registrar_pedido(p_cliente_id, p_forma_pago, p_items)`
- **Entrada:**
  - `p_cliente_id BIGINT` — id del cliente que compra.
  - `p_forma_pago forma_pago` — ENUM (`EFECTIVO` | `TARJETA` | `TRANSFERENCIA`).
  - `p_items JSONB` — arreglo de `[{"producto_id": …, "cantidad": …}]`.
    El tipo JSONB es un requisito del motor pedido por la cátedra y además
    permite entregar las líneas del pedido como un único argumento tipado.
- **Salida:** `p_pedido_id BIGINT` OUT — id del pedido recién insertado (para
  poder consultarlo/verificarlo después del `CALL`).
- **Comportamiento:**
  1. Valida que el cliente exista y esté `activo = TRUE` (R1 del TP2).
  2. Inserta `pedido` (`cliente_id`, `forma_pago`, `fecha = now()`).
  3. Por cada ítem del `JSONB`:
     - valida que tenga `producto_id` y `cantidad > 0`;
     - valida que el producto exista y esté `activo = TRUE` (R2);
     - **bloquea la fila del producto (`SELECT ... FOR UPDATE`)** para evitar
       sobreventa bajo concurrencia;
     - valida `cantidad <= producto.stock` (R3 del TP2);
     - inserta `linea_pedido` con `precio_unitario` = precio actual (congelado
       en la línea, R4);
     - descuenta `producto.stock -= cantidad`.
  4. Si cualquier validación falla → `RAISE EXCEPTION` y toda la operación se
     revierte (atomicidad en el motor).
- **Reglas fuera de alcance:** no recalcula `subtotal` (se calcula al vuelo por
  R4/3FN); no maneja pagos externos; no define transacciones internas al
  procedimiento (el `CALL` corre dentro de la transacción que lo invoca).

### Criterio de aceptación (verificable)

- `CALL registrar_pedido(...)` con ítems válidos → devuelve `p_pedido_id`;
  `pedido` y sus `linea_pedido` existen; `stock` de los productos quedó
  reducido exactamente en las cantidades vendidas.
- `CALL` con cliente inactivo → error controlado.
- `CALL` con producto inactivo / inexistente → error controlado.
- `CALL` con `cantidad > stock` → error controlado, **sin** descontar stock
  de los ítems anteriores (atomicidad).
- La prueba íntegra corre dentro de una única transacción con `ROLLBACK` final
  (protocolo de seguridad): nada queda persistido en la base de trabajo.

---

## Procedimiento P2 — `ajustar_stock`

Reposición/ajuste manual de inventario: modifica el stock de un producto
vigente y devuelve el nuevo valor. Procedimiento **con mutación real** y
resultado por parámetro OUT, cubriendo las tres formas de intercambio que la
materia distingue (argumentos, OUT/INOUT, mensajes/contadores).

### Contrato

- **Nombre:** `ajustar_stock(p_producto_id, p_delta)`
- **Entrada:**
  - `p_producto_id BIGINT` — producto a reajustar.
  - `p_delta INTEGER` — variación (positivo = reposición/ingreso, negativo =
    baja/egreso manual).
- **Salida:** `p_nuevo_stock INTEGER` OUT — stock resultante.
- **Comportamiento:**
  1. Valida que el producto exista y esté `activo = TRUE`.
  2. Bloquea la fila (`FOR UPDATE`) y lee el stock actual.
  3. Calcula el nuevo stock; si queda negativo → `RAISE EXCEPTION` (regla
     `stock >= 0` del DDL, reforzada en el motor a nivel de operación).
  4. Aplica `UPDATE producto SET stock = nuevo`.
  5. Devuelve el nuevo stock por OUT y emite `RAISE NOTICE` con el cambio
     (a+->b) para trazabilidad de la operación.
- **Fuera de alcance:** no audita históricamente el movimiento (el esquema no
  tiene tabla de movimientos; fuera del contrato de datos).

### Criterio de aceptación

- `CALL ajustar_stock(id_producto, +10)`: stock queda +10 y el OUT devuelve el
  nuevo valor; verificable con `SELECT stock` de la misma tabla.
- `CALL ajustar_stock(id_producto, -999999)`: error controlado (stock no
  negativo) y el stock no cambia (atomicidad de la operación).
- La prueba corre dentro de una transacción con `ROLLBACK` final.