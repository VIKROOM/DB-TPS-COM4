# spec: vista_productos_vigentes

**Objetivo:** simplificar el acceso al listado de productos vigentes con su
categoría (cartilla/menú de la tienda y reportes de catálogo). Reutilizable por
consultas y futuros objetos programables (Semana 6).

**Columnas a exponer:**
- `producto.id`
- `producto.nombre`
- `producto.precio`
- `producto.stock`
- `categoria.nombre AS categoria`

**Filtro de vigencia:** `producto.activo = TRUE` y `categoria.activo = TRUE`
(baja lógica del dominio). No se exponen columnas de auditoría internas.

**Seguridad:** no aplica ocultamiento en esta vista (no hay credenciales en la
tabla origen).

**Criterio de aceptación:** la vista devuelve exactamente las mismas filas y
columnas que la consulta equivalente escrita a mano (verificación con EXCEPT,
0 diferencias).