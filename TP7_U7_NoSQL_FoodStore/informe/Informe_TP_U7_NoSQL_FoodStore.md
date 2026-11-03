# Trabajo Práctico — Unidad 7

## NoSQL y nuevas formas de almacenamiento — Food Store

**Tecnicatura Universitaria en Programación — Bases de Datos II — Comisión 4**

**Integrante:** Facundo Chacón
**Repositorio:** <https://github.com/VIKROOM/DB-TPS-COM4>
**Motores:** PostgreSQL 17 (base `foodstore`) · MongoDB 7.0.14 + mongosh 2.3.1
**Fecha:** 03/11/2026

---

## 1. Modelo documental y correspondencia con Food Store (consigna 1)

Se eligió el subconjunto **pedidos y detalle de pedidos**. En PostgreSQL
intervienen cuatro tablas:

| Tabla | Clave primaria | Claves foráneas / reglas |
|---|---|---|
| `pedido` | `id` | `cliente_id → cliente(id)` `ON DELETE RESTRICT`; `fecha`, `forma_pago` |
| `linea_pedido` | `(pedido_id, producto_id)` | `pedido_id → pedido(id)` `ON DELETE CASCADE`; `producto_id → producto(id)` `ON DELETE RESTRICT`; `cantidad > 0`; `precio_unitario >= 0` |
| `cliente` | `id` | `email` único |
| `producto` | `id` | `categoria_id → categoria(id)`; `precio >= 0` |

Cada pedido se representa como **un documento** con las líneas embebidas:

```javascript
{
  pedido_id: 1,
  fecha: ISODate("2026-11-03T01:39:32.658Z"),
  estado: "PENDIENTE",
  forma_pago: "EFECTIVO",
  cliente: { cliente_id: 1, nombre: "Ana Gomez" },
  items: [
    { producto_id: 1, nombre: "Muzzarella", categoria: "Pizzas",
      cantidad: 2, precio_unitario: NumberDecimal("1000.00"),
      subtotal: NumberDecimal("2000.00") },
    { producto_id: 2, nombre: "Coca 1.5L", categoria: "Bebidas",
      cantidad: 1, precio_unitario: NumberDecimal("800.00"),
      subtotal: NumberDecimal("800.00") }
  ],
  items_count: 2,
  total: NumberDecimal("2800.00")
}
```

**Correspondencia:** `pedido.id → pedido_id`; `pedido.fecha → fecha`;
`pedido.forma_pago → forma_pago`; `cliente.id → cliente.cliente_id`;
`cliente.nombre + apellido → cliente.nombre`; `linea_pedido + producto →
items[]` con `producto_id`, `nombre`, `categoria`, `cantidad`, `precio_unitario`;
`SUM(cantidad × precio_unitario) → total`. Se conservan los tres identificadores
de origen. No se copian `email` ni `teléfono` (minimización de datos).

**Decisión de agrupamiento.** Las líneas se embeben porque siempre se leen
juntas, son un arreglo acotado (2 líneas por pedido en la muestra) y permiten
actualizar el pedido completo en una escritura atómica. El cliente y el producto
quedan **referenciados por id**; solo se copia la instantánea necesaria para
mostrar el pedido histórico (nombre, categoría y precio unitario). Es un diseño
mixto: referencia estable + copia controlada.

## 2. Migración y reglas de integridad (consignas 2 y 3)

Se migraron los **12 pedidos** con `id` 1 a 12 y sus **24 líneas**, de 11
clientes, con fechas entre 2025-03-01 y 2026-11-02 e importe total de
**$560.979,00**. La extracción se hace con `sql/01_exportar_pedidos_mongodb.sql`:
PostgreSQL genera un `insertMany()` con `ISODate` y `NumberDecimal`, y el script
resultante (`mongodb/02_datos_pedidos.js`) se ejecuta en mongosh. Los documentos
incluyen fecha, estado, cliente, productos, cantidades y precios históricos.

La colección se crea con un validador `$jsonSchema`
(`validationLevel: "strict"`, `validationAction: "error"`) y cuatro índices:
`pedido_id` único, `estado`, `items.producto_id` (multikey) y `total`.

**Reglas de integridad conservadas:**

1. **Identidad y referencia.** `pedido_id` es obligatorio y único (índice
   `unique`), y cada `items.producto_id` debe existir en el catálogo de origen.
   El laboratorio verificó **0 líneas huérfanas** contra `producto` y **0
   duplicados** de `pedido_id`.
2. **Coherencia de cantidades e importes.** `cantidad` es entero ≥ 1,
   `precio_unitario ≥ 0`, `subtotal = cantidad × precio_unitario` y
   `total = Σ subtotales`. Las 24 líneas y los 12 totales coinciden; además,
   23 de 24 precios históricos difieren del precio actual del catálogo, lo que
   confirma que la instantánea no se sobrescribe.

La regla de estado se deriva porque el esquema real no tiene columna de estado:
`fecha_corte = max(fecha del lote) + 1 día`; `TERMINADO` si `fecha ≤
fecha_corte − 30 días`, `PENDIENTE` en caso contrario. Se aplica igual en SQL y
en la migración, y no depende del reloj.

## 3. Consultas y verificación con PostgreSQL (consignas 4 y 5)

| # | Consulta MongoDB | Resultado |
|---|---|---|
| a | `db.pedidos.find({}, {_id:0, pedido_id:1, estado:1}).sort({pedido_id:1})` | 12 pedidos |
| b | `db.pedidos.find({estado:"TERMINADO"})` | 11 pedidos: 2–12 |
| c | `db.pedidos.find({"items.producto_id": 1})` | 2 pedidos: 1, 2 |
| d | `db.pedidos.find({total: {$gt: NumberDecimal("50000.00")}})` | 6 pedidos: 2, 6, 8, 10, 11, 12 |

**Umbral de d):** $50.000,00. La muestra tiene promedio $46.748,25 y mediana
$49.891,50; el umbral separa 6 de 12 pedidos de alto valor, sin ser trivial
(no devuelve todos ni ninguno). El importe acumulado es $386.471,00.

**Comparación (misma regla de estado y mismo lote):**

| Consulta | Cantidad PostgreSQL | Cantidad MongoDB | IDs | ¿Coinciden? |
|---|---|---|---|---|
| b) estado `TERMINADO` | 11 | 11 | 2,3,4,5,6,7,8,9,10,11,12 | **Sí** |
| c) producto 1 | 2 | 2 | 1,2 | **Sí** |

También coinciden los importes: b) $558.179,00 y c) $79.810,00 en ambos
motores. **No se detectaron diferencias**: se migró exactamente el mismo
subconjunto, se aplicó la misma regla de estado y se usó la misma precisión
decimal (`NUMERIC(10,2)` ↔ `Decimal128`). La única diferencia es de sintaxis y
de modelo de datos: SQL usa `JOIN` y `CASE`; MongoDB usa notación de punto sobre
el arreglo y un campo materializado.

## 4. Evaluación de la tecnología y contraste de IA (consignas 6 y 7)

**Consulta a la IA.** Se pidió comparar ambos motores para el modelo actual,
el acceso frecuente al pedido completo y la necesidad de conservar coherencia
de cantidades y precios (prompt completo en `BITACORA_IA.md`). La respuesta
propuso embeber las líneas y afirmó, entre otras cosas, que MongoDB no soporta
transacciones multidocumento, que es más rápido por evitar JOIN, que no admite
reglas de integridad y que un documento puede crecer sin límite.

**Contraste de afirmaciones:**

| Afirmación | Documentación oficial / laboratorio | Veredicto |
|---|---|---|
| No hay transacciones ACID multidocumento | MongoDB las soporta en *replica sets*; un *standalone* no. En el laboratorio la sesión falló con `Transaction numbers are only allowed on a replica set member or mongos`. | Imprecisa: falsa en general, cierta en nuestro despliegue. El diseño no las necesita porque pedido y líneas son un solo documento. |
| Es más rápido porque evita JOIN | El embebido reduce operaciones, pero no garantiza superioridad. Consulta c): MongoDB examinó 2 documentos y 2 claves (1 ms); PostgreSQL usó *index-only scans* y *nested loop* (0,086 ms) para el mismo resultado. | No sostenible como absoluto. La ventaja comprobada es de número de operaciones, no de velocidad. |
| No se pueden imponer reglas de integridad | `$jsonSchema` con `validationAction:"error"` rechaza documentos inválidos. El intento con `cantidad: 0` devolvió `Document failed validation`. | Falsa. El esquema flexible admite validaciones estrictas. |
| El documento crece sin límite | Los documentos BSON tienen un máximo de 16 MiB; el embebido se recomienda para arreglos acotados. | Falsa. Los pedidos migrados tienen 2 líneas y ~1,5 KB. |

**Conclusión (≤ 200 palabras).** Para el subconjunto pedidos-detalle conviene una
arquitectura combinada, no un reemplazo. PostgreSQL debe seguir siendo la fuente
de verdad: el modelo normalizado garantiza con claves foráneas que cada pedido
tenga un cliente y productos existentes, impone cantidades positivas y conserva
el precio histórico en `linea_pedido`; además ofrece transacciones ACID en el
despliegue real del equipo. MongoDB aporta una proyección de lectura: un pedido
completo se recupera en un solo documento, sin JOIN, y el laboratorio mostró
resultados idénticos a SQL (11 pedidos `TERMINADO` y 2 con el producto 1, mismos
IDs e importes). Esa ventaja es de número de operaciones, no una superioridad de
rendimiento demostrada con 12 documentos. Los criterios que sostienen la decisión
son (1) patrón de acceso —lectura completa y repetida del pedido frente a
escrituras transaccionales— y (2) integridad —coherencia de cantidades, precios y
referencias—, más (3) costo operativo de mantener dos motores. Si el volumen de
lectura lo justifica, sincronizar por `pedido_id` una colección de solo lectura;
migrar el núcleo transaccional no se justifica con la evidencia obtenida.

## 5. Evidencias, reproducción y autoevaluación

- `consultas_mongodb.js` y `consultas_postgresql.sql`: instrucciones ejecutadas.
- `mongodb/01_crear_coleccion.js`: validador, índices y metadatos.
- `evidencia/mongo_02_carga.txt`: 12 documentos insertados.
- `evidencia/mongo_03_verificacion_integridad.txt`: 9 comprobaciones, todas OK.
- `evidencia/mongo_04_consultas.txt` y `evidencia/postgres_01_consultas.txt`:
  salidas de las consultas a–d y b–c.
- `evidencia/mongo_06_pruebas_ia.txt`: validador, transacción y `explain`.
- `verificar_entrega.ps1`: 26 comprobaciones automatizadas, incluida la
  comparación cruzada de IDs e importes y el límite de 5 páginas del PDF.

**Límites.** El estado es derivado (el esquema relacional no lo tiene); la
muestra es pequeña (12 pedidos) y no permite conclusiones de rendimiento; el
`mongod` local es *standalone*, por lo que no admite transacciones
multidocumento. El informe no afirma que MongoDB reemplace a PostgreSQL.

**Bibliografía.** MongoDB: [Transactions](https://www.mongodb.com/docs/manual/core/transactions/),
[Schema Validation](https://www.mongodb.com/docs/manual/core/schema-validation/),
[Embedded Data](https://www.mongodb.com/docs/manual/data-modeling/embedding/),
[db.collection.find()](https://www.mongodb.com/docs/manual/reference/method/db.collection.find/).
Apunte de la cátedra: «Unidad 7: NoSQL y nuevas formas de almacenamiento».
