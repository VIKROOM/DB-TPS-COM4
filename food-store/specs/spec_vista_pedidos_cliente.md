# spec: vista_pedidos_cliente (con criterio de seguridad)

**Objetivo:** reporte de pedidos con los datos del cliente que los solicitó
(panel administrativo y "mis pedidos"), sin exponer datos personales sensibles
del cliente.

> **Adaptación documentada del enunciado:** la consigna pide "exponer usuario
> sin la columna contraseña". El esquema real del equipo modela al comprador
> como tabla `cliente` (que no posee columna de credenciales). El criterio de
> seguridad se aplica igualmente: **la vista NO expone las columnas de
> contacto/identificación personal del cliente** (`email`, `telefono`) que en
> este esquema son los datos protegidos por el criterio visto en la teoría.
> De este modo puede otorgarse SELECT sobre la vista sin dar acceso a la tabla
> base `cliente` (defensa oral: se justifica esta equivalencia).

**Columnas a exponer:**
- `pedido.id AS pedido_id`
- `pedido.id AS nro_pedido`
- `pedido.fecha`
- `pedido.forma_pago`
- `cliente.id AS cliente_id`
- `cliente.nombre AS nombre_cliente`
- `cliente.apellido AS apellido_cliente`

**Columnas a ocultar por seguridad:** `cliente.email`, `cliente.telefono`,
`cliente.created_at`. Con `SELECT` sobre la vista no se accede a datos de
contacto del cliente desde la tabla base.

**Filtro de vigencia:** `cliente.activo = TRUE`.

**Criterio de aceptación:** equivalencia exacta (EXCEPT en ambos sentidos, 0
diferencias) contra la consulta manual con las mismas columnas.