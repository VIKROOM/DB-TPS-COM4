# Declaración de Uso de IA (DUIA) — Unidad 3 · Semana 1

**Proyecto:** Food Store (integraciones de Semanas 1-4) · **Tema:** índices,
vistas y vistas materializadas · **Herramientas:** Kiro (especificación),
OpenCode (agente de codificación en terminal), Git/GitHub.

> **Regla de la cátedra:** la especificación se hace primero en Kiro (se
> conserva en `specs/`); la generación la ejecuta OpenCode en la terminal; todo
> script generado se leyó y comprendió línea por línea antes de ejecutarlo, y
> se probó sobre la copia `foodstore_u3` dentro de transacciones reversibles
> (BEGIN...ROLLBACK) con respaldo previo `pg_dump -Fc` en `../backups/`.

## Registro de interacciones

### 1 · Reconocimiento del esquema y punto de partida

- **Herramienta:** OpenCode · **Propósito:** inspeccionar.
- **Intervención de IA:** leyó el PDF de la consigna (`BD2_TP_Unidad3_Semana1_Indices_Vistas.pdf`), el `schema.sql` heredado y la base `foodstore`/`foodstore_tp3`.
- **Decisión humana clave (equivalencia documentada):** el enunciado menciona
  `usuario`/`detalle_pedido`; el esquema real de las Semanas 1-4 usa
  `cliente`/`linea_pedido`. **Aceptado no modificar el modelo**: se trabajó
  sobre los objetos realmente existentes y la equivalencia quedó documentada
  en informe y specs.
- **Decisión de volumen:** se amplió `data.sql` al orden del TP3 (50k
  productos · 20k clientes · 200k pedidos · 400k líneas) para que los planes
  sean observables.

### 2 · Especificaciones (Kiro)

Cada pieza del trabajo se especificó primero y su spec se conserva en `specs/`:
`spec_indice_linea_pedido_producto.md`, `spec_busqueda_nombre_producto.md`,
`spec_indice_producto_stock_parcial.md`, `spec_vista_productos_vigentes.md`,
`spec_vista_pedidos_cliente.md`, `spec_vista_detalle_pedido_producto.md`,
`spec_vista_materializada_facturacion.md`. Las specs fijan objetivo, SQL
exacto, columnas candidatas y criterio de aceptación (se le entrega el problema
a la IA, no la orden "creá un índice" a ciegas).

### 3 · Indices (Parte A) — generación y revisión

| # | Propuesta de la IA | Aceptación | Justificación |
|---|--------------------|-----------|---------------|
| I1 | btree `linea_pedido(producto_id)` INCLUDE `(cantidad, precio_unitario)` | **Aceptado** | Cambia `Parallel Seq Scan` (400k filas) por `Bitmap/Index Scan`; 36,6 → 0,3 ms. |
| I2 | GIN trigram `producto(nombre)` parcial `WHERE activo` | **Aceptado** | Habilita `ILIKE %...%`; 31,6 → 1,2 ms. |
| I3 | btree parcial `producto(stock)` `WHERE activo AND stock <= 10` | **Aceptado** | Evita el Seq Scan en reposición; 7,0 → 4,5 ms. |
| D1 | btree `pedido(forma_pago)` | **Descartado (sobreindexación)** | ENUM de 3 valores = baja cardinalidad; no reduce filas significativamente y agrega costo de escritura. |
| D2 | btree `producto(categoria_id, nombre)` | **Descartado (duplicado)** | Ya existe la restricción `UNIQUE (categoria_id, nombre)` (crea ese índice) y `idx_producto_categoria`. |

- **Revisión línea por línea:** cada `CREATE INDEX` se leyó y se validó contra
  su spec antes de ejecutarlo (tipo, columnas, condición parcial).
- **Costo de escritura medido:** carga de 5.000 INSERTs en `linea_pedido`
  antes 84,4 ms → después 107,6 ms (+28%). Aceptado: 122× de ganancia de
  lectura justifica el mantenimiento en la tabla de mayor volumen.

### 4 · Vistas (Parte B) — generación y verificación

- **Propuestas de la IA:** `v_productos_vigentes`, `v_pedidos_cliente`,
  `v_detalle_pedido_producto` generadas a partir de los specs.
- **Verificación de equivalencia:** cada vista se comparó contra su consulta
  manual con `EXCEPT` en ambas direcciones → **0 diferencias** en las tres
  (script `06_verificacion_vistas.sql`).
- **Criterio de seguridad:** el enunciado pide ocultar `contraseña`; el
  esquema real (`cliente`) no tiene credenciales, por lo que `v_pedidos_cliente`
  oculta las columnas de contacto protegidas (`email`, `telefono`). Verificado
  que la vista no las expone. **Aceptado con la adaptación documentada.**

### 5 · Vista materializada (Parte C)

- **Propuesta de la IA:** `mv_facturacion_categoria_mes` con `WITH DATA` e
  índice único `(mes, categoria)` para `REFRESH CONCURRENTLY`.
- **Verificación:** consulta original 484,9 ms → materializada 0,026 ms
  (~18.600×). `REFRESH CONCURRENTLY` probado OK.
- **Decisión** de frecuencia de refresco: diaria (cierre de día); documento en
  el informe qué implica para los usuarios (dato del período anterior).

## Resumen de decisiones

- **Aceptado:** 3 índices, 3 vistas, 1 vista materializada (con índice único).
- **Descartado:** 2 propuestas por sobreindexación (D1 baja cardinalidad, D2
  duplicado de UNIQUE existente).
- **Modificado:** equivalencias de nomenclatura del enunciado (usuario→cliente,
  detalle_pedido→linea_pedido; contraseña→email/telefono), siempre documentadas
  y verificadas.
- Los planes de ejecución y resultados quedaron versionados en `planes/` y el
  informe en `informe_mediciones.md`.

## Verificación objetiva

- `foodstore` (producción) intacta (no se conectó escritura a ella).
- Todo se ejecutó sobre `foodstore_u3` (copia), con `pg_dump -Fc` previo,
  y las cargas de escritura dentro de `BEGIN...ROLLBACK`.
- `git log` del presente TP muestra un commit por pieza (spec, índice/vista,
  informe), según el Punto 5 de la consigna.