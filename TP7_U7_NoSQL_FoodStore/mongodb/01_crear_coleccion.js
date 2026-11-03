// ============================================================================
// TP Unidad 7 - Food Store NoSQL
// Consigna 2: crear la base foodstore_nosql, la coleccion pedidos, sus
// indices y las validaciones de esquema del dominio.
//
// Uso:
//   mongosh "mongodb://127.0.0.1:27017/foodstore_nosql" mongodb/01_crear_coleccion.js
//
// El script es idempotente: elimina la coleccion si existe y la vuelve a
// crear. Ejecutar DESPUES mongodb/02_datos_pedidos.js.
// ============================================================================

const nombreBase = "foodstore_nosql";
const nombreColeccion = "pedidos";

if (db.getName() !== nombreBase) {
  throw new Error(`Base inesperada: ${db.getName()}. Usar la URI ${nombreBase}.`);
}

// ---------------------------------------------------------------------------
// 1. Coleccion con validacion de esquema ($jsonSchema)
//    Reglas verificables en el motor (ademas de las validaciones de negocio
//    que se comprueban en mongodb/03_verificacion_integridad.js):
//      - campos obligatorios y tipos BSON;
//      - estado y forma_pago dentro del dominio cerrado;
//      - cantidad entera >= 1 y precios/subtotales decimales >= 0;
//      - items no vacio;
//      - additionalProperties: false para detectar campos mal escritos.
// ---------------------------------------------------------------------------
db.pedidos.drop();

db.createCollection(nombreColeccion, {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "pedido_id", "fecha", "estado", "forma_pago",
        "cliente", "items", "items_count", "total",
      ],
      additionalProperties: false,
      properties: {
        _id: {},
        pedido_id: { bsonType: "int", minimum: 1 },
        fecha: { bsonType: "date" },
        estado: { enum: ["PENDIENTE", "TERMINADO"] },
        forma_pago: { enum: ["EFECTIVO", "TARJETA", "TRANSFERENCIA"] },
        cliente: {
          bsonType: "object",
          required: ["cliente_id", "nombre"],
          additionalProperties: false,
          properties: {
            cliente_id: { bsonType: "int", minimum: 1 },
            nombre: { bsonType: "string", minLength: 1 },
          },
        },
        items: {
          bsonType: "array",
          minItems: 1,
          items: {
            bsonType: "object",
            required: [
              "producto_id", "nombre", "categoria",
              "cantidad", "precio_unitario", "subtotal",
            ],
            additionalProperties: false,
            properties: {
              producto_id: { bsonType: "int", minimum: 1 },
              nombre: { bsonType: "string", minLength: 1 },
              categoria: { bsonType: "string", minLength: 1 },
              cantidad: { bsonType: "int", minimum: 1 },
              precio_unitario: { bsonType: "decimal", minimum: 0 },
              subtotal: { bsonType: "decimal", minimum: 0 },
            },
          },
        },
        items_count: { bsonType: "int", minimum: 1 },
        total: { bsonType: "decimal", minimum: 0 },
      },
    },
  },
  validationLevel: "strict",
  validationAction: "error",
});

// ---------------------------------------------------------------------------
// 2. Indices alineados a las consultas del TP
// ---------------------------------------------------------------------------
// pedido_id: identificador de origen, unico (regla de integridad 1).
db.pedidos.createIndex({ pedido_id: 1 }, { unique: true });
// Consulta 4.b: filtrar por estado.
db.pedidos.createIndex({ estado: 1 });
// Consulta 4.c: buscar un producto dentro del arreglo de lineas (multikey).
db.pedidos.createIndex({ "items.producto_id": 1 });
// Consulta 4.d y ordenamientos por importe.
db.pedidos.createIndex({ total: -1 });

// ---------------------------------------------------------------------------
// 3. Metadatos de la migracion (procedencia y reglas aplicadas)
// ---------------------------------------------------------------------------
db.meta_migracion.drop();
db.meta_migracion.insertOne({
  proyecto: "Food Store - Bases de Datos II - Comision 4",
  trabajo: "TP Unidad 7 - NoSQL",
  origen: {
    motor: "PostgreSQL 17",
    base: "foodstore",
    tablas: ["pedido", "linea_pedido", "cliente", "producto", "categoria"],
    filtro: "pedido.id BETWEEN 1 AND 12",
    pedidos_origen: 12,
    lineas_origen: 24,
  },
  destino: {
    motor: "MongoDB 7.0.14",
    base: nombreBase,
    coleccion: nombreColeccion,
  },
  decision_embebido:
    "Las lineas se embeben en el pedido porque siempre se leen juntas y son un arreglo acotado; " +
    "el cliente y el producto conservan su id de origen como referencia y se copia solo la " +
    "instantanea necesaria para mostrar el pedido historico (nombre, categoria y precio unitario).",
  regla_estado:
    "El esquema relacional real no tiene columna de estado de pedido. Para la consigna 4.b se " +
    "deriva estado con una regla reproducible: fecha_corte = max(fecha del lote) + 1 dia; " +
    "TERMINADO si fecha <= fecha_corte - 30 dias; PENDIENTE en caso contrario. La misma regla " +
    "se aplica en SQL (CASE) para comparar resultados.",
  regla_importes:
    "precio_unitario y total se guardan como Decimal128 con dos decimales, equivalentes a " +
    "NUMERIC(10,2) de PostgreSQL. subtotal = cantidad * precio_unitario y total = suma de subtotales.",
  fecha_extraccion: new Date(),
});

print("Coleccion creada:", nombreColeccion);
print("Documentos actuales:", db.pedidos.countDocuments());
printjson(db.pedidos.getIndexes());
