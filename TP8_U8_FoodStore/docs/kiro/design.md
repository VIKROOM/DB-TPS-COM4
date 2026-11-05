# Kiro · Design — TP Unidad 8 (Food Store en la feria)

## Objetivo

Construir la base de la tablet en SQLite, importar una instantánea del catálogo
de PostgreSQL y resolver los borradores con un semáforo que clasifica cada
solicitud en verde, amarillo o rojo, sin modificar el servidor.

## Decisión de arquitectura

```
PostgreSQL (fuente de verdad)
   │  v_snapshot_movil → CSV (solo catálogo)
   ▼
SQLite en la tablet
   ├── producto_cache       copia de solo lectura del catálogo
   ├── pedido_borrador      cabecera local (UUID)
   ├── item_borrador        líneas del borrador
   └── cola_sync            solicitudes y resultado del semáforo
   │
   ▼
Semáforo (SQLite): PENDIENTE → CONFLICTO | RECHAZADO | SIMULADO_APROBADO
   │
   ▼
Revisión humana / futuro envío al servidor (fuera de este TP)
```

La tablet nunca ejecuta `INSERT`, `UPDATE` ni `DELETE` sobre PostgreSQL. El
único flujo permitido es recibir una instantánea y proponer borradores.

## Esquema SQLite

| Tabla | Rol | Reglas principales |
|---|---|---|
| `producto_cache` | catálogo offline | precio en centavos ≥ 0; `stock_visto` ≥ 0; `disponible` y `eliminado` en {0,1}; `fecha_copia` |
| `pedido_borrador` | cabecera local | `id_local` UUID como PK; `forma_pago` en {EFECTIVO, TARJETA, TRANSFERENCIA} |
| `item_borrador` | líneas | FK a `pedido_borrador` y `producto_cache`; `cantidad > 0`; precio visto ≥ 0 |
| `cola_sync` | cola de sincronización | `solicitud_uuid` PK; estado acotado; motivo y `evaluado_en` |

Todas las tablas son `STRICT`; se activa `PRAGMA foreign_keys = ON` al inicio.

## Instantánea (consigna 2.a)

`v_snapshot_movil` proyecta solo lo necesario:

- `precio_centavos = round(precio * 100)`: entero, sin punto flotante.
- `disponible = activo AND stock > 0`.
- `eliminado = NOT activo`: la lápida de la baja lógica también viaja.
- `fecha_copia = now()`: permite saber la antigüedad de la copia.

El CSV se importa en `snapshot_servidor` y se refresca `producto_cache` con un
UPSERT (`ON CONFLICT(id) DO UPDATE`). Las filas que ya no vienen no se borran:
así un borrador viejo conserva su referencia y la lápida se actualiza.

## Semáforo (consigna 2.b)

Se agrupa por solicitud y se cuentan los ítems con problemas:

1. Sin ítems → `RECHAZADO` / `SIN_ITEMS`.
2. Producto inexistente, dado de baja, no disponible o sin stock → `RECHAZADO`.
3. Sin rojo pero con precio distinto → `CONFLICTO`.
4. Todo coincide → `SIMULADO_APROBADO`.

La prioridad es rojo > amarillo > verde. Solo se actualizan filas `PENDIENTE`,
de modo que repetir la simulación no reevalúa lo resuelto.

## Idempotencia y transacciones

- La solicitud se identifica con un UUID generado en la tablet.
- `solicitud_uuid` es clave primaria en `cola_sync`: el reenvío local falla.
- En un sistema real la protección debe estar en el servidor: clave única de
  idempotencia y confirmación transaccional. La PK local no alcanza porque cada
  tablet tiene su propia base.
- El borrador se guarda con `BEGIN … COMMIT`; si una línea viola un `CHECK` o
  una FK, el `ROLLBACK` deja la base sin filas nuevas.

## Datos que no viajan

No viajan clientes, usuarios, contraseñas, ventas, logs ni datos personales.
La tablet usa un identificador de vendedor inventado (`vendedor-demo`) y no
necesita saber quién es el cliente para armar el borrador.

## Verificación

- `movil/pruebas_sqlite.sql`: transacción confirmada, rollback, catálogo offline
  y casos C7 (cantidad 0 y producto inexistente).
- `scripts/simular_tp8.py`: reproduce los casos C2 a C6, exporta evidencias y
  comprueba que los invariantes de PostgreSQL no cambiaron.
- `scripts/revision_codigo.py`: ejecuta los scripts reales de U3 y U5 en un
  PostgreSQL temporal para comprobar los hallazgos del code review.
