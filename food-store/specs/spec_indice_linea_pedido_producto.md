# spec: indice_linea_pedido_producto

**Objetivo:** acelerar el reporte "ventas de un producto" (historial), consulta
frecuente de la pantalla de administración de Food Store.

**Consulta afectada:**
```sql
SELECT p.id, p.fecha, lp.cantidad, lp.precio_unitario,
       lp.cantidad * lp.precio_unitario AS subtotal
FROM   linea_pedido lp
JOIN   pedido p ON p.id = lp.pedido_id
WHERE  lp.producto_id = 100
ORDER  BY p.fecha DESC
LIMIT  50;
```

**Frecuencia:** alta (se consulta cada vez que un admin abre el detalle de un
producto).

**Columnas candidatas:** `linea_pedido.producto_id` (alta selectividad: 400.002
filas, ~8 filas por producto). `cantidad` y `precio_unitario` como INCLUDE para
index-only scan (evitar tocar el heap).

**Criterio de aceptación:** el plan pasa de `Seq Scan on linea_pedido` a
`Index Scan` (o Bitmap) y el tiempo de ejecución baja al menos un orden de
magnitud.