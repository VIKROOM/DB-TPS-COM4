// ============================================================================
// TP Unidad 7 - Food Store NoSQL
// Pruebas de laboratorio para contrastar afirmaciones de la IA (consigna 7).
//
// Uso:
//   mongosh "mongodb://127.0.0.1:27017/foodstore_nosql" --quiet ^
//           --file mongodb/06_pruebas_afirmaciones_ia.js
//
// No modifica datos: el documento invalido es rechazado por el validador y
// la transaccion se aborta. Ejecutar sobre el servidor local (standalone).
// ============================================================================

const coll = db.getSiblingDB("foodstore_nosql").pedidos;

print("=== Prueba 1: el validador rechaza un documento con cantidad invalida ===");
try {
  coll.insertOne({
    pedido_id: 999,
    fecha: new Date(),
    estado: "PENDIENTE",
    forma_pago: "EFECTIVO",
    cliente: { cliente_id: 1, nombre: "Prueba" },
    items: [{
      producto_id: 1, nombre: "Muzzarella", categoria: "Pizzas",
      cantidad: 0,                       // viola minimum: 1
      precio_unitario: NumberDecimal("1000.00"),
      subtotal: NumberDecimal("0.00"),
    }],
    items_count: 1,
    total: NumberDecimal("0.00"),
  });
  print("RESULTADO: FALLO - el documento invalido fue aceptado");
} catch (e) {
  print("RESULTADO: RECHAZADO por validationAction=error");
  print("Mensaje: " + e.message.split("\n")[0]);
}

print("");
print("=== Prueba 2: transaccion multidocumento en el servidor standalone ===");
const sesion = db.getMongo().startSession();
try {
  sesion.startTransaction();
  sesion.getDatabase("foodstore_nosql").pedidos.insertOne({
    pedido_id: 998,
    fecha: new Date(),
    estado: "PENDIENTE",
    forma_pago: "EFECTIVO",
    cliente: { cliente_id: 1, nombre: "Prueba" },
    items: [{
      producto_id: 1, nombre: "Muzzarella", categoria: "Pizzas",
      cantidad: 1,
      precio_unitario: NumberDecimal("1000.00"),
      subtotal: NumberDecimal("1000.00"),
    }],
    items_count: 1,
    total: NumberDecimal("1000.00"),
  });
  sesion.commitTransaction();
  print("RESULTADO: transaccion confirmada (el servidor soporta multi-documento)");
} catch (e) {
  print("RESULTADO: la transaccion no esta disponible en este despliegue");
  print("Mensaje: " + e.message.split("\n")[0]);
  try { sesion.abortTransaction(); } catch (_) { /* ya abortada */ }
} finally {
  sesion.endSession();
}

print("");
print("=== Prueba 3: plan de ejecucion de la consulta c) (producto 1) ===");
const ex = coll.find({ "items.producto_id": 1 }).explain("executionStats");
printjson({
  etapa: ex.queryPlanner.winningPlan.stage,
  nReturned: ex.executionStats.nReturned,
  totalDocsExamined: ex.executionStats.totalDocsExamined,
  totalKeysExamined: ex.executionStats.totalKeysExamined,
  executionTimeMillis: ex.executionStats.executionTimeMillis,
});

print("");
print("=== Prueba 4: documento migrado completo (muestra legible) ===");
printjson(coll.findOne({ pedido_id: 1 }));
