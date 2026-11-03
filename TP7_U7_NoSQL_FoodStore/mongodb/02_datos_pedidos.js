// ============================================================================
// ARCHIVO GENERADO AUTOMATICAMENTE POR sql/01_exportar_pedidos_mongodb.sql
// Fuente: PostgreSQL 17 / base foodstore / pedidos 1 a 12
// No editar a mano: volver a ejecutar la extraccion.
// ============================================================================

db.pedidos.insertMany([
  {
    pedido_id: 1,
    fecha: ISODate("2026-11-03T01:39:32.658Z"),
    estado: "PENDIENTE",
    forma_pago: "EFECTIVO",
    cliente: { cliente_id: 1, nombre: "Ana Gomez" },
    items: [
      { producto_id: 1, nombre: "Muzzarella", categoria: "Pizzas", cantidad: 2, precio_unitario: NumberDecimal("1000.00"), subtotal: NumberDecimal("2000.00") },
      { producto_id: 2, nombre: "Coca 1.5L", categoria: "Bebidas", cantidad: 1, precio_unitario: NumberDecimal("800.00"), subtotal: NumberDecimal("800.00") }
    ],
    items_count: 2,
    total: NumberDecimal("2800.00")
  },
  {
    pedido_id: 2,
    fecha: ISODate("2025-04-24T10:27:16.923Z"),
    estado: "TERMINADO",
    forma_pago: "TARJETA",
    cliente: { cliente_id: 1, nombre: "Ana Gomez" },
    items: [
      { producto_id: 1, nombre: "Muzzarella", categoria: "Pizzas", cantidad: 2, precio_unitario: NumberDecimal("3401.00"), subtotal: NumberDecimal("6802.00") },
      { producto_id: 2, nombre: "Coca 1.5L", categoria: "Bebidas", cantidad: 16, precio_unitario: NumberDecimal("4388.00"), subtotal: NumberDecimal("70208.00") }
    ],
    items_count: 2,
    total: NumberDecimal("77010.00")
  },
  {
    pedido_id: 3,
    fecha: ISODate("2025-10-23T01:17:23.847Z"),
    estado: "TERMINADO",
    forma_pago: "TRANSFERENCIA",
    cliente: { cliente_id: 2, nombre: "Nombre2 Apellido2" },
    items: [
      { producto_id: 6, nombre: "Bebida 4", categoria: "Pizzas", cantidad: 8, precio_unitario: NumberDecimal("2213.00"), subtotal: NumberDecimal("17704.00") },
      { producto_id: 7, nombre: "Pizza 5", categoria: "Bebidas", cantidad: 4, precio_unitario: NumberDecimal("4844.00"), subtotal: NumberDecimal("19376.00") }
    ],
    items_count: 2,
    total: NumberDecimal("37080.00")
  },
  {
    pedido_id: 4,
    fecha: ISODate("2025-12-22T18:11:28.968Z"),
    estado: "TERMINADO",
    forma_pago: "TARJETA",
    cliente: { cliente_id: 3, nombre: "Nombre3 Apellido3" },
    items: [
      { producto_id: 11, nombre: "Pizza 9", categoria: "Bebidas", cantidad: 2, precio_unitario: NumberDecimal("1356.00"), subtotal: NumberDecimal("2712.00") },
      { producto_id: 12, nombre: "Bebida 10", categoria: "Pizzas", cantidad: 6, precio_unitario: NumberDecimal("3961.00"), subtotal: NumberDecimal("23766.00") }
    ],
    items_count: 2,
    total: NumberDecimal("26478.00")
  },
  {
    pedido_id: 5,
    fecha: ISODate("2025-11-10T22:32:21.395Z"),
    estado: "TERMINADO",
    forma_pago: "TRANSFERENCIA",
    cliente: { cliente_id: 4, nombre: "Nombre4 Apellido4" },
    items: [
      { producto_id: 16, nombre: "Bebida 14", categoria: "Pizzas", cantidad: 11, precio_unitario: NumberDecimal("1983.00"), subtotal: NumberDecimal("21813.00") },
      { producto_id: 17, nombre: "Pizza 15", categoria: "Bebidas", cantidad: 17, precio_unitario: NumberDecimal("907.00"), subtotal: NumberDecimal("15419.00") }
    ],
    items_count: 2,
    total: NumberDecimal("37232.00")
  },
  {
    pedido_id: 6,
    fecha: ISODate("2025-03-24T05:17:28.751Z"),
    estado: "TERMINADO",
    forma_pago: "TRANSFERENCIA",
    cliente: { cliente_id: 5, nombre: "Nombre5 Apellido5" },
    items: [
      { producto_id: 21, nombre: "Pizza 19", categoria: "Bebidas", cantidad: 7, precio_unitario: NumberDecimal("4267.00"), subtotal: NumberDecimal("29869.00") },
      { producto_id: 22, nombre: "Bebida 20", categoria: "Pizzas", cantidad: 11, precio_unitario: NumberDecimal("4333.00"), subtotal: NumberDecimal("47663.00") }
    ],
    items_count: 2,
    total: NumberDecimal("77532.00")
  },
  {
    pedido_id: 7,
    fecha: ISODate("2025-10-24T15:39:24.466Z"),
    estado: "TERMINADO",
    forma_pago: "TARJETA",
    cliente: { cliente_id: 6, nombre: "Nombre6 Apellido6" },
    items: [
      { producto_id: 26, nombre: "Bebida 24", categoria: "Pizzas", cantidad: 11, precio_unitario: NumberDecimal("1519.00"), subtotal: NumberDecimal("16709.00") },
      { producto_id: 27, nombre: "Pizza 25", categoria: "Bebidas", cantidad: 6, precio_unitario: NumberDecimal("1144.00"), subtotal: NumberDecimal("6864.00") }
    ],
    items_count: 2,
    total: NumberDecimal("23573.00")
  },
  {
    pedido_id: 8,
    fecha: ISODate("2025-06-09T15:46:37.141Z"),
    estado: "TERMINADO",
    forma_pago: "TRANSFERENCIA",
    cliente: { cliente_id: 7, nombre: "Nombre7 Apellido7" },
    items: [
      { producto_id: 31, nombre: "Pizza 29", categoria: "Bebidas", cantidad: 8, precio_unitario: NumberDecimal("1710.00"), subtotal: NumberDecimal("13680.00") },
      { producto_id: 32, nombre: "Bebida 30", categoria: "Pizzas", cantidad: 13, precio_unitario: NumberDecimal("3797.00"), subtotal: NumberDecimal("49361.00") }
    ],
    items_count: 2,
    total: NumberDecimal("63041.00")
  },
  {
    pedido_id: 9,
    fecha: ISODate("2025-04-22T20:10:59.003Z"),
    estado: "TERMINADO",
    forma_pago: "TARJETA",
    cliente: { cliente_id: 8, nombre: "Nombre8 Apellido8" },
    items: [
      { producto_id: 36, nombre: "Bebida 34", categoria: "Pizzas", cantidad: 19, precio_unitario: NumberDecimal("2000.00"), subtotal: NumberDecimal("38000.00") },
      { producto_id: 37, nombre: "Pizza 35", categoria: "Bebidas", cantidad: 3, precio_unitario: NumberDecimal("3115.00"), subtotal: NumberDecimal("9345.00") }
    ],
    items_count: 2,
    total: NumberDecimal("47345.00")
  },
  {
    pedido_id: 10,
    fecha: ISODate("2025-12-06T18:59:50.548Z"),
    estado: "TERMINADO",
    forma_pago: "EFECTIVO",
    cliente: { cliente_id: 9, nombre: "Nombre9 Apellido9" },
    items: [
      { producto_id: 41, nombre: "Pizza 39", categoria: "Bebidas", cantidad: 18, precio_unitario: NumberDecimal("2020.00"), subtotal: NumberDecimal("36360.00") },
      { producto_id: 42, nombre: "Bebida 40", categoria: "Pizzas", cantidad: 20, precio_unitario: NumberDecimal("910.00"), subtotal: NumberDecimal("18200.00") }
    ],
    items_count: 2,
    total: NumberDecimal("54560.00")
  },
  {
    pedido_id: 11,
    fecha: ISODate("2025-11-01T18:25:57.603Z"),
    estado: "TERMINADO",
    forma_pago: "TARJETA",
    cliente: { cliente_id: 10, nombre: "Nombre10 Apellido10" },
    items: [
      { producto_id: 46, nombre: "Bebida 44", categoria: "Pizzas", cantidad: 7, precio_unitario: NumberDecimal("1460.00"), subtotal: NumberDecimal("10220.00") },
      { producto_id: 47, nombre: "Pizza 45", categoria: "Bebidas", cantidad: 19, precio_unitario: NumberDecimal("2222.00"), subtotal: NumberDecimal("42218.00") }
    ],
    items_count: 2,
    total: NumberDecimal("52438.00")
  },
  {
    pedido_id: 12,
    fecha: ISODate("2025-03-01T12:34:33.284Z"),
    estado: "TERMINADO",
    forma_pago: "TRANSFERENCIA",
    cliente: { cliente_id: 11, nombre: "Nombre11 Apellido11" },
    items: [
      { producto_id: 51, nombre: "Pizza 49", categoria: "Bebidas", cantidad: 6, precio_unitario: NumberDecimal("4264.00"), subtotal: NumberDecimal("25584.00") },
      { producto_id: 52, nombre: "Bebida 50", categoria: "Pizzas", cantidad: 9, precio_unitario: NumberDecimal("4034.00"), subtotal: NumberDecimal("36306.00") }
    ],
    items_count: 2,
    total: NumberDecimal("61890.00")
  }
]);
print("Documentos en pedidos: " + db.pedidos.countDocuments());
