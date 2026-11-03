// ============================================================================
// TP Unidad 7 - Food Store NoSQL
// Consultas de la Parte 2 (consigna 4) sobre la coleccion foodstore_nosql.pedidos
//
// Uso:
//   mongosh "mongodb://127.0.0.1:27017/foodstore_nosql" --quiet ^
//           --file consultas_mongodb.js
//
// Requiere haber ejecutado mongodb/01_crear_coleccion.js y
// mongodb/02_datos_pedidos.js.
// ============================================================================

const coll = db.getSiblingDB("foodstore_nosql").pedidos;
const proyeccion = { _id: 0, pedido_id: 1, estado: 1 };

function idsDe(cursor) {
  return cursor.toArray().map((d) => d.pedido_id).sort((a, b) => a - b);
}

print("============================================================");
print("BASE: foodstore_nosql | COLECCION: pedidos");
print("Documentos: " + coll.countDocuments());
print("============================================================");

// ---------------------------------------------------------------------------
// a) Mostrar todos los pedidos, incluyendo identificador y estado.
// ---------------------------------------------------------------------------
print("\n--- 4.a) Todos los pedidos (pedido_id, estado) ---");
const a = coll
  .find({}, proyeccion)
  .sort({ pedido_id: 1 })
  .toArray();
printjson(a);

// ---------------------------------------------------------------------------
// b) Filtrar por un estado existente en los datos migrados.
//    Se usa TERMINADO (11 de 12 documentos). El estado deriva de la regla
//    documentada: fecha <= now() - 30 dias.
// ---------------------------------------------------------------------------
print("\n--- 4.b) Pedidos con estado TERMINADO ---");
const b = coll
  .find({ estado: "TERMINADO" }, proyeccion)
  .sort({ pedido_id: 1 })
  .toArray();
printjson(b);
print("IDs TERMINADO: " + idsDe(coll.find({ estado: "TERMINADO" })).join(","));
print("Cantidad TERMINADO: " + b.length);
print("Cantidad PENDIENTE: " + coll.countDocuments({ estado: "PENDIENTE" }));

// ---------------------------------------------------------------------------
// c) Pedidos que contengan un producto determinado en el arreglo de lineas.
//    Producto 1 = Muzzarella (existe en los pedidos 1 y 2).
// ---------------------------------------------------------------------------
print("\n--- 4.c) Pedidos que contienen el producto 1 (Muzzarella) ---");
const c = coll
  .find(
    { "items.producto_id": 1 },
    { _id: 0, pedido_id: 1, "items.producto_id": 1, "items.nombre": 1, "items.cantidad": 1 }
  )
  .sort({ pedido_id: 1 })
  .toArray();
printjson(c);
print("IDs producto 1: " + idsDe(coll.find({ "items.producto_id": 1 })).join(","));
print("Cantidad: " + c.length);

// ---------------------------------------------------------------------------
// d) Pedidos con total superior a un importe elegido y justificacion.
//    Umbral: 50000.00. La muestra tiene promedio 46748.25 y mediana 49891.50;
//    el umbral separa 6 de 12 pedidos de alto valor sin ser trivial.
// ---------------------------------------------------------------------------
const UMBRAL = NumberDecimal("50000.00");
print(`\n--- 4.d) Pedidos con total > ${UMBRAL} (orden descendente) ---`);
const d = coll
  .find({ total: { $gt: UMBRAL } }, { _id: 0, pedido_id: 1, total: 1 })
  .sort({ total: -1 })
  .toArray();
printjson(d);
print("IDs total > 50000: " + idsDe(coll.find({ total: { $gt: UMBRAL } })).join(","));
print("Cantidad: " + d.length);

// ---------------------------------------------------------------------------
// Comprobaciones complementarias (no exigidas por 4.a-4.d, utiles para 5 y 7):
// distribucion por estado y suma de importes con la misma regla en ambos motores.
// ---------------------------------------------------------------------------
print("\n--- Extra: distribucion por estado (cantidad e importe) ---");
printjson(
  coll
    .aggregate([
      {
        $group: {
          _id: "$estado",
          pedidos: { $sum: 1 },
          importe: { $sum: "$total" },
        },
      },
      { $sort: { _id: 1 } },
    ])
    .toArray()
);

print("\n--- Extra: total general de la muestra ---");
printjson(
  coll
    .aggregate([{ $group: { _id: null, pedidos: { $sum: 1 }, importe: { $sum: "$total" } } }])
    .toArray()
);

print("\n--- Resumen ---");
printjson({
  a_pedidos: a.length,
  b_estado_TERMINADO: b.length,
  c_producto_1: c.length,
  d_total_mayor_50000: d.length,
  importe_muestra: coll
    .aggregate([{ $group: { _id: null, t: { $sum: "$total" } } }])
    .toArray()[0].t.toString(),
});
