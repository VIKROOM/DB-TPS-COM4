// ============================================================================
// TP Unidad 7 - Food Store NoSQL
// Verificacion de integridad sobre los documentos migrados.
//
// Uso:
//   mongosh "mongodb://127.0.0.1:27017/foodstore_nosql" --quiet ^
//           --file mongodb/03_verificacion_integridad.js
//
// Comprueba, con consultas al motor y no con inspeccion visual:
//   1) cantidad de documentos migrados;
//   2) unicidad de pedido_id;
//   3) items_count == cantidad de elementos de items;
//   4) subtotal == cantidad * precio_unitario en cada linea;
//   5) total == suma de subtotales del pedido;
//   6) estado dentro del dominio y fecha de tipo Date;
//   7) IDs de producto positivos (la existencia en el catalogo de origen se
//      contrasta en sql/02_consultas_postgresql.sql).
// Sale con codigo 1 si alguna comprobacion falla.
// ============================================================================

const esperados = 12;
const fallos = [];
const resultados = {};

function comprobar(nombre, obtenido, esperado) {
  const ok = JSON.stringify(obtenido) === JSON.stringify(esperado);
  resultados[nombre] = { ok, obtenido, esperado };
  if (!ok) {
    fallos.push(`${nombre}: obtenido=${JSON.stringify(obtenido)} esperado=${JSON.stringify(esperado)}`);
  }
}

// 1) Cantidad de documentos.
comprobar("documentos_migrados", db.pedidos.countDocuments(), esperados);

// 2) pedido_id unico (ademas del indice unique, se comprueba el dato).
const duplicados = db.pedidos
  .aggregate([
    { $group: { _id: "$pedido_id", n: { $sum: 1 } } },
    { $match: { n: { $gt: 1 } } },
  ])
  .toArray();
comprobar("pedido_id_sin_duplicados", duplicados.length, 0);

// 3) items_count coherente con el arreglo.
const itemsCountMal = db.pedidos
  .aggregate([
    { $project: { pedido_id: 1, items_count: 1, real: { $size: "$items" } } },
    { $match: { $expr: { $ne: ["$items_count", "$real"] } } },
    { $project: { _id: 0, pedido_id: 1 } },
  ])
  .toArray();
comprobar("items_count_coherente", itemsCountMal.length, 0);

// 4) subtotal == cantidad * precio_unitario (comparacion Decimal128).
const subtotalesMal = db.pedidos
  .aggregate([
    {
      $project: {
        pedido_id: 1,
        lineas: {
          $filter: {
            input: "$items",
            as: "i",
            cond: {
              $ne: [
                "$$i.subtotal",
                { $multiply: ["$$i.cantidad", "$$i.precio_unitario"] },
              ],
            },
          },
        },
      },
    },
    { $match: { "lineas.0": { $exists: true } } },
    { $project: { _id: 0, pedido_id: 1, lineas: 1 } },
  ])
  .toArray();
comprobar("subtotal_por_linea", subtotalesMal.length, 0);

// 5) total == suma de subtotales.
const totalesMal = db.pedidos
  .aggregate([
    {
      $project: {
        pedido_id: 1,
        total: 1,
        calculado: {
          $sum: {
            $map: { input: "$items", as: "i", in: "$$i.subtotal" },
          },
        },
      },
    },
    { $match: { $expr: { $ne: ["$total", "$calculado"] } } },
    { $project: { _id: 0, pedido_id: 1, total: 1, calculado: 1 } },
  ])
  .toArray();
comprobar("total_igual_suma_subtotales", totalesMal.length, 0);

// 6) Dominio de estado y tipo de fecha.
comprobar(
  "estados_fuera_de_dominio",
  db.pedidos.countDocuments({ estado: { $nin: ["PENDIENTE", "TERMINADO"] } }),
  0
);
comprobar(
  "fechas_no_date",
  db.pedidos.countDocuments({ fecha: { $not: { $type: "date" } } }),
  0
);

// 6.b) Tipos BSON previstos: identificadores int32 e importes Decimal128.
comprobar(
  "tipos_bson",
  db.pedidos
    .aggregate([
      {
        $project: {
          _id: 0,
          pedido_id: { $type: "$pedido_id" },
          total: { $type: "$total" },
          cantidad: { $type: { $arrayElemAt: ["$items.cantidad", 0] } },
          precio: { $type: { $arrayElemAt: ["$items.precio_unitario", 0] } },
        },
      },
      { $match: { $or: [
        { pedido_id: { $ne: "int" } },
        { total: { $ne: "decimal" } },
        { cantidad: { $ne: "int" } },
        { precio: { $ne: "decimal" } },
      ] } },
    ])
    .toArray().length,
  0
);

// 7) IDs de producto positivos y nombres no vacios.
comprobar(
  "productos_id_invalidos",
  db.pedidos.countDocuments({
    $or: [
      { "items.producto_id": { $lte: 0 } },
      { "items.nombre": "" },
      { "items.categoria": "" },
    ],
  }),
  0
);

// Detalle util para el informe.
resultados.documentos = db.pedidos
  .find({}, { _id: 0, pedido_id: 1, estado: 1, items_count: 1, total: 1 })
  .sort({ pedido_id: 1 })
  .toArray();

resultados.producto_ids_distintos = db.pedidos
  .distinct("items.producto_id")
  .sort((a, b) => a - b);

printjson(resultados);

if (fallos.length > 0) {
  print(`RESULTADO: FALLO (${fallos.length} comprobaciones)`);
  fallos.forEach((f) => print(" - " + f));
  quit(1);
}
print("RESULTADO: OK - integridad del subconjunto migrado verificada");
