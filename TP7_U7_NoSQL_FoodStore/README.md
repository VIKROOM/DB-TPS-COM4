# TP Unidad 7 — NoSQL y nuevas formas de almacenamiento (Food Store)

**Asignatura:** Bases de Datos II · Comisión 4
**Integrante:** Facundo Chacón
**Repositorio:** <https://github.com/VIKROOM/DB-TPS-COM4>
**Motores:** PostgreSQL 17 (base `foodstore`) · MongoDB 7.0.14 Community + mongosh 2.3.1

Modelado y consulta del subconjunto **pedidos + detalle de pedidos** de Food Store
en MongoDB, con migración desde PostgreSQL y verificación cruzada de resultados.

## Estructura

```
TP7_U7_NoSQL_FoodStore/
├── consultas_mongodb.js              ENTREGABLE: consultas 4.a–4.d en mongosh
├── consultas_postgresql.sql          ENTREGABLE: equivalentes 5.b y 5.c + integridad
├── reproducir.ps1                    Extrae, crea, carga, verifica y consulta todo
├── verificar_entrega.ps1             Autoevaluación objetiva (26 comprobaciones)
├── AUTOEVALUACION.md                 Revisión por consigna e iteraciones
├── BITACORA_IA.md                    Prompt, respuesta y contraste de afirmaciones
├── README.md
├── sql/
│   ├── 01_exportar_pedidos_mongodb.sql   Genera el insertMany desde PostgreSQL
│   └── 02_explain_consultas.sql          Planes de ejecución de ambos filtros
├── mongodb/
│   ├── 01_crear_coleccion.js         Base, colección, validador e índices
│   ├── 02_datos_pedidos.js           GENERADO: 12 pedidos / 24 líneas
│   ├── 03_verificacion_integridad.js Comprueba coherencia del documento
│   ├── 05_resumen_comparacion.js     JSON para la comparación cruzada
│   └── 06_pruebas_afirmaciones_ia.js Pruebas de validador, transacción y explain
├── evidencia/                        Salidas reales de todas las ejecuciones
└── informe/
    ├── Informe_TP_U7_NoSQL_FoodStore.md
    ├── Informe_TP_U7_NoSQL_FoodStore.pdf   ENTREGABLE (2 páginas, límite 5)
    ├── Informe_TP_U7_Actividades.pdf       Informe ampliado: una sección por actividad
    ├── generar_informe.py
    └── generar_informe_actividades.py
```

## Informes

- `informe/Informe_TP_U7_NoSQL_FoodStore.pdf` — **entrega oficial**, 2 páginas (límite 5).
- `informe/Informe_TP_U7_Actividades.pdf` — informe ampliado de 3 páginas, con una sección
  por actividad (consigna, desarrollo, evidencia y verificación) y el enlace al repositorio.

## Modelo documental (resumen)

Base `foodstore_nosql`, colección `pedidos`:

```javascript
{
  pedido_id: 1,                       // id de origen conservado
  fecha: ISODate("2026-11-03T01:39:32.658Z"),
  estado: "PENDIENTE",                // regla derivada documentada
  forma_pago: "EFECTIVO",             // atributo real del modelo
  cliente: { cliente_id: 1, nombre: "Ana Gomez" },   // sin email/teléfono
  items: [
    { producto_id: 1, nombre: "Muzzarella", categoria: "Pizzas",
      cantidad: 2, precio_unitario: NumberDecimal("1000.00"),
      subtotal: NumberDecimal("2000.00") }
  ],
  items_count: 2,
  total: NumberDecimal("2800.00")
}
```

- **Embebido:** líneas (`items`) y datos mínimos del cliente. Se leen siempre con
  el pedido y el arreglo es acotado.
- **Referencia:** `cliente_id` y `producto_id` conservan trazabilidad al modelo
  relacional; no se copian catálogos completos.
- **Snapshot histórico:** nombre, categoría y precio unitario quedan congelados
  al momento de la venta (regla R4 del proyecto).
- **Importes:** `Decimal128` con dos decimales, equivalente a `NUMERIC(10,2)`.
- **Validación:** `$jsonSchema` con `validationAction: "error"` e índices por
  `pedido_id` (único), `estado`, `items.producto_id` y `total`.

### Regla de estado

El esquema real de Food Store **no tiene columna de estado de pedido**. Para
poder cumplir la consigna 4.b se definió una regla explícita y reproducible,
aplicada igual en MongoDB (al migrar) y en SQL (con `CASE`):

```
fecha_corte = max(fecha del lote) + 1 día
TERMINADO   si fecha <= fecha_corte - 30 días
PENDIENTE   en caso contrario
```

No depende del reloj, así que la extracción y la comparación son repetibles.
El resultado es 11 pedidos `TERMINADO` y 1 `PENDIENTE`. La limitación se
documenta en el informe y en `mongodb/01_crear_coleccion.js`.

## Requisitos

- PostgreSQL 16+ con la base `foodstore` poblada (`schema.sql` + datos del TP3).
- MongoDB Community 7.x (`mongod`) escuchando en `127.0.0.1:27017`.
- `mongosh` 2.x y `psql` en el PATH (o pasar sus rutas a los scripts).
- PowerShell 5.1+.

## Reproducción

```powershell
# 1) Iniciar MongoDB (ejemplo con binarios locales)
mongod --dbpath C:\ruta\mongo-data --port 27017 --bind_ip 127.0.0.1

# 2) Desde esta carpeta
$env:PGPASSWORD="tu_password"
.\reproducir.ps1 `
  -Psql "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -Mongosh "C:\ruta\mongosh.exe"

# 3) Autoevaluación objetiva
.\verificar_entrega.ps1 `
  -Psql "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -Mongosh "C:\ruta\mongosh.exe"
```

`reproducir.ps1` ejecuta, en orden: extracción SQL → creación de colección →
`insertMany()` → verificación de integridad → consultas MongoDB → consultas
PostgreSQL → resumen comparable. Cada paso deja su salida en `evidencia/`.

## Resultados verificados

| Consulta | PostgreSQL | MongoDB | ¿Coinciden? |
|---|---|---|---|
| b) estado `TERMINADO` | 11 pedidos: `2..12` | 11 pedidos: `2..12` | Sí |
| c) producto 1 (Muzzarella) | 2 pedidos: `1,2` | 2 pedidos: `1,2` | Sí |
| Importe b) | 558.179,00 | 558.179,00 | Sí |
| Importe c) | 79.810,00 | 79.810,00 | Sí |
| Importe total de la muestra | 560.979,00 | 560.979,00 | Sí |

Sin diferencias: se migró el mismo subconjunto (ids 1–12), se aplicó la misma
regla de estado y se usó la misma precisión decimal. La comparación se
recalcula en cada ejecución de `verificar_entrega.ps1`.

## Decisiones y límites

- No se migró la base completa: solo 12 pedidos y 24 líneas, con procedencia
  indicada (`pedido.id BETWEEN 1 AND 12`).
- No se copiaron email ni teléfono del cliente (minimización de datos).
- El `mongod` de laboratorio es *standalone*: no admite transacciones
  multidocumento. El diseño no las requiere porque pedido y líneas forman un
  único documento; se documenta la limitación en `BITACORA_IA.md`.
- La ventaja observada de MongoDB es de **número de operaciones** (un documento
  frente a tres tablas), no una superioridad de rendimiento medida.
- El estado es derivado, no un dato nativo del esquema relacional.
