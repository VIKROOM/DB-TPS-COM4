# spec: indice_producto_stock_parcial

**Objetivo:** acelerar el reporte de reposición de stock ("qué hay que
reponer"), consulta frecuente del sector de compras.

**Consulta afectada:**
```sql
SELECT id, nombre, stock
FROM   producto
WHERE  stock <= 10
  AND  activo = TRUE
ORDER  BY stock;
```

**Frecuencia:** media-alta (corre periódicamente en el panel de compras).

**Columnas candidatas:** `producto.stock` (selectividad media-alta en los
rangos bajos) con la condición parcial `WHERE activo` (baja lógica del
dominio). Al filtrar solo los activos, el índice es menor que indexar stock
completo.

**Criterio de aceptación:** el plan pasa de `Seq Scan on producto` a
`Index Scan` y el costo estimado y el tiempo bajan.