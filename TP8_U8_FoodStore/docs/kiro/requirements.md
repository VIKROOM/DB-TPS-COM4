# Kiro · Requirements — TP Unidad 8 (Food Store en la feria)

## Alcance

La tablet debe poder consultar el catálogo y armar borradores de pedido sin
señal. PostgreSQL sigue siendo la fuente de verdad: la tablet **propone** y el
servidor **dispone**. El alcance de esta especificación es la base SQLite de la
tablet y el semáforo de sincronización; no incluye interfaz gráfica ni una app
móvil.

## Requisitos en notación EARS

### REQ-01 — Precio cambiado

- **WHEN** el precio actual del servidor (`snapshot_servidor.precio_centavos`)
  es distinto del precio visto en el borrador
  (`item_borrador.precio_centavos_visto`)
- **THE SYSTEM SHALL** marcar la solicitud como `CONFLICTO` con motivo
  `PRECIO_CAMBIADO`, sin modificarla si ya no está `PENDIENTE`.
- **Se prueba con:** C2 (evidencia `evidencias/04_semaforo_casos.txt`).

### REQ-02 — Producto inválido o stock insuficiente

- **WHEN** algún ítem de una solicitud `PENDIENTE` referencia un producto
  inexistente, dado de baja, no disponible o con cantidad mayor al stock visto
- **THE SYSTEM SHALL** marcar la solicitud como `RECHAZADO` con el motivo
  correspondiente (`PRODUCTO_INEXISTENTE`, `PRODUCTO_DADO_DE_BAJA`,
  `PRODUCTO_NO_DISPONIBLE` o `STOCK_INSUFICIENTE`), con prioridad sobre
  `CONFLICTO`.
- **Se prueba con:** C3 y C4 (evidencia `evidencias/04_semaforo_casos.txt`) y
  C7b de SQLite (`evidencias/02_pruebas_sqlite.txt`).

### REQ-03 — Todo coincide

- **WHEN** todos los ítems existen, están disponibles, tienen stock suficiente
  y el precio coincide
- **THE SYSTEM SHALL** marcar la solicitud como `SIMULADO_APROBADO` con motivo
  `TODO_COINCIDE`, sin escribir nada en PostgreSQL: aprobado no es una venta.
- **Se prueba con:** C5 (evidencia `evidencias/04_semaforo_casos.txt`).

### REQ-04 — Idempotencia del reenvío

- **WHEN** se intenta reenviar una solicitud con un `solicitud_uuid` ya
  registrado, o se repite el semáforo sobre la misma solicitud
- **THE SYSTEM SHALL** rechazar el duplicado por clave primaria y no reevaluar
  las solicitudes ya resueltas, de modo que `evaluado_en` no cambie y quede una
  sola fila por UUID.
- **Se prueba con:** C6 (evidencia `evidencias/04_semaforo_casos.txt`).

## Trazabilidad requisito → caso → evidencia

| Requisito | Caso | Archivo de evidencia |
|---|---|---|
| REQ-01 | C2 | `evidencias/04_semaforo_casos.txt` |
| REQ-02 | C3, C4, C7b | `evidencias/04_semaforo_casos.txt`, `evidencias/02_pruebas_sqlite.txt` |
| REQ-03 | C5 | `evidencias/04_semaforo_casos.txt` |
| REQ-04 | C6 | `evidencias/04_semaforo_casos.txt` |

## Criterios de aceptación

- El esquema SQLite se crea desde cero con `PRAGMA foreign_keys = ON` y tablas
  `STRICT`.
- El precio viaja en centavos enteros y no admite negativos.
- El borrador se guarda en una transacción `BEGIN … COMMIT`; otra operación con
  `ROLLBACK` no deja filas.
- El semáforo solo evalúa solicitudes `PENDIENTE` y no ejecuta DML sobre
  PostgreSQL.
- Los casos C2 a C6 dan el resultado esperado y los invariantes del servidor no
  cambian (pedidos, líneas, stock e importe).
