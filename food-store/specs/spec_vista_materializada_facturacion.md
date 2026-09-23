# spec: vista_materializada_facturacion_categoria_mes

**Objetivo:** acelerar el reporte agregado de facturación por categoría y mes
(reporte gerencial costoso de la Semana 4). Como el dato solo cambia al entrar
un nuevo pedido/línea, se materializa una vez por período y se refresca con
`REFRESH MATERIALIZED VIEW CONCURRENTLY`.

**Consulta origen (Q6 de queries.sql):**
```sql
SELECT cat.nombre AS categoria,
       date_trunc('month', p.fecha) AS mes,
       SUM(lp.cantidad * lp.precio_unitario) AS facturado
FROM   linea_pedido lp
JOIN   pedido    p   ON p.id   = lp.pedido_id
JOIN   producto  pr  ON pr.id  = lp.producto_id
JOIN   categoria cat ON cat.id = pr.categoria_id
GROUP  BY cat.nombre, date_trunc('month', p.fecha)
ORDER  BY mes, categoria;
```

**Criterio de aceptación:**
- crear con `WITH DATA` (el reporte debe poder consumirse de inmediato);
- índice único sobre `(mes, categoria)` para permitir `REFRESH CONCURRENTLY`;
- el tiempo de consulta sobre la materializada debe ser ostensiblemente menor
  que el de la consulta original (no materializada).