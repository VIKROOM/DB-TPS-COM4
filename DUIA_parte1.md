# Declaración de Uso de IA (DUIA) — Parte 1 · Integridad versionada

**TP:** 2 · Concurrencia e IA como motor primario (Parte 1)
**Esquema:** Food Store (proyecto integrador)
**Motor:** PostgreSQL 17.10 · **Base de trabajo:** `foodstore_tp2` (copia según protocolo)

---

| Campo | Completar |
|---|---|
| **Herramienta** | OpenCode (modelo/proveedor configurado: modelo de línea big-pickle) |
| **Spec o prompt utilizado** | "Generá restricciones de integridad (triggers declarativos) para las 3 reglas de negocio de la spec_restricciones.md: (R1) cliente inactivo no genera pedidos, (R2) producto inactivo no se vende en líneas nuevas, (R3) cantidad vendida <= stock. Motor PostgreSQL 17, sobre el esquema FoodStore. Usá triggers BEFORE INSERT/UPDATE y RAISE EXCEPTION con mensajes descriptivos." |
| **Qué generó** | `spec_restricciones.md` (spec), `restricciones_integridad.sql` (3 funciones + 3 triggers: `chk_activo_cliente_pedido`, `chk_activo_producto_linea`, `chk_stock_linea`), `pruebas_restricciones.sql` (script de verificación) |
| **Qué se aceptó** | Las 3 funciones y los 3 triggers tal como se generaron, tras revisar el diff. La lógica de cada regla y los nombres de los objetos se mantuvieron. |
| **Qué se modificó o descartado, y por qué** | 1) En `pruebas_restricciones.sql`, el caso válido de la R3 usaba inicialmente `producto_id = 1` (Muzzarella), pero ese producto ya tenía una línea en el mismo pedido, lo que violaba la PK compuesta `(pedido_id, producto_id)` antes de llegar al trigger de stock. Se cambió a `producto_id = 2` (Coca) para aislar la prueba del control de stock. 2) Los mensajes de error se ajustaron para incluir los valores concretos (id de cliente/producto, cantidades) para facilitar el diagnóstico. |
| **Verificación realizada** | Sobre la copia `foodstore_tp2`, dentro de `BEGIN ... ROLLBACK` primero (inspección) y luego con `COMMIT` definitivo: — R1: pedido para cliente inactivo → rechazado ("No se puede crear un pedido para el cliente 1"); cliente activo → aceptado. — R2: línea con producto inactivo → rechazada ("No se puede vender el producto 2"); activo → aceptada. — R3: cantidad 5000 > stock 20 → rechazada ("Stock insuficiente ... pide 5000 pero hay 20"); cantidad 3 ≤ stock 50 → aceptada. Se comprobó además que los 3 triggers quedaron registrados en `pg_trigger`. |

## Verificación humana

- Cada línea del diff de `restricciones_integridad.sql` fue leída y entendida antes de aplicarse (política: ningún script se ejecuta sin leerse).
- El DDL se aplicó primero en una transacción que se revirtió para inspeccionar, y recién después se confirmó con `COMMIT` sobre la copia.
- Las decisiones de diseño (usar triggers en vez de CHECK porque involucran dos tablas; `FOR EACH ROW`; `BEFORE INSERT`/`UPDATE OF cantidad`) fueron entendidas.
