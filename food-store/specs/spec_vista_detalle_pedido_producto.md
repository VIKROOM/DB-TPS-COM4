# spec: vista_detalle_pedido_producto

**Objetivo:** detalle de un pedido con el nombre del producto (ticket de
venta), reutilizable por el front de la tienda y por reportes.

**Columnas a exponer:**
- `pedido.id AS pedido_id`
- `pedido.fecha`
- `producto.nombre AS producto`
- `linea_pedido.cantidad`
- `linea_pedido.precio_unitario`
- `(cantidad * precio_unitario) AS subtotal`

**Filtro de vigencia:** ninguno sobre fechas (historial completo); el precio
unitario queda congelado en la línea (regla R4 del dominio).

**Seguridad:** no expone datos del cliente ni credenciales; apta para lectura
de tickets.

**Criterio de aceptación:** equivalencia exacta (EXCEPT, 0 diferencias) contra
la consulta manual.