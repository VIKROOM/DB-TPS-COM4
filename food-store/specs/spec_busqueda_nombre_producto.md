# spec: indice_busqueda_nombre_producto

**Objetivo:** acelerar la búsqueda por nombre en el menú/catálogo
(`ILIKE %texto%`), consulta frecuente de la tienda.

**Consulta afectada:**
```sql
SELECT id, nombre, precio
FROM   producto
WHERE  nombre ILIKE '%pizza 25000%'
  AND  activo = TRUE;
```

**Frecuencia:** alta (buscador del front de la tienda y del panel admin).

**Columnas candidatas:** `producto.nombre` con coincidencia parcial
(`LIKE %...%`), que un índice b-tree clásico no puede resolver. Se requiere un
índice GIN con la extensión `pg_trgm` (nivel 1: índice trigram), acotado con la
condición parcial `WHERE activo` para reducir el tamaño.

**Criterio de aceptación:** el plan pasa de `Seq Scan on producto` a
`Bitmap Index Scan` sobre el índice trigram, con baja de tiempo observable.