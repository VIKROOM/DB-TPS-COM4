// ============================================================================
// TP Unidad 7 - Food Store NoSQL
// Resumen en JSON puro para la verificacion cruzada con PostgreSQL.
// Lo consume verificar_entrega.ps1; no es un entregable de la catedra.
//
// Uso:
//   mongosh "mongodb://127.0.0.1:27017/foodstore_nosql" --quiet ^
//           --file mongodb/05_resumen_comparacion.js
// ============================================================================

const coll = db.getSiblingDB("foodstore_nosql").pedidos;

function ids(filtro) {
  return coll
    .find(filtro, { _id: 0, pedido_id: 1 })
    .toArray()
    .map((d) => d.pedido_id)
    .sort((a, b) => a - b);
}

function cantidad(filtro) {
  return coll.countDocuments(filtro);
}

function importe(filtro) {
  const r = coll
    .aggregate([{ $match: filtro }, { $group: { _id: null, t: { $sum: "$total" } } }])
    .toArray();
  return r.length ? r[0].t.toString() : "0.00";
}

const resumen = {
  total_documentos: coll.countDocuments(),
  a: { cantidad: cantidad({}) },
  b: {
    estado: "TERMINADO",
    cantidad: cantidad({ estado: "TERMINADO" }),
    ids: ids({ estado: "TERMINADO" }),
    importe: importe({ estado: "TERMINADO" }),
  },
  pendiente: {
    cantidad: cantidad({ estado: "PENDIENTE" }),
    ids: ids({ estado: "PENDIENTE" }),
    importe: importe({ estado: "PENDIENTE" }),
  },
  c: {
    producto_id: 1,
    cantidad: cantidad({ "items.producto_id": 1 }),
    ids: ids({ "items.producto_id": 1 }),
    importe: importe({ "items.producto_id": 1 }),
  },
  d: {
    umbral: "50000.00",
    cantidad: cantidad({ total: { $gt: NumberDecimal("50000.00") } }),
    ids: ids({ total: { $gt: NumberDecimal("50000.00") } }),
    importe: importe({ total: { $gt: NumberDecimal("50000.00") } }),
  },
  muestra: { importe: importe({}) },
};

print(JSON.stringify(resumen));
