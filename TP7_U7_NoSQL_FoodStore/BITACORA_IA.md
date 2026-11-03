# Bitácora de uso de IA — TP Unidad 7 (NoSQL / Food Store)

**Herramienta:** OpenCode (agente de IA en CLI)
**Fecha de la consulta:** 03/11/2026
**Alcance:** exploración del diseño documental y comparación PostgreSQL/MongoDB (consignas 6 y 7).

## 1. Consulta realizada

Prompt enviado, con el caso, el modelo actual y las restricciones del dominio:

> En Food Store el modelo actual es PostgreSQL normalizado: `cliente`, `pedido`,
> `linea_pedido` y `producto`. `pedido` guarda `cliente_id`, `fecha` y
> `forma_pago`; `linea_pedido` guarda `cantidad` y `precio_unitario` histórico.
> La aplicación lee con frecuencia el pedido completo (cabecera, líneas y nombre
> del cliente) para mostrarlo y auditar ventas, y necesita conservar la coherencia
> entre cantidades, precios históricos y total. Compará PostgreSQL y MongoDB para
> almacenar y consultar ese subconjunto. Dame ventajas, riesgos y una
> recomendación, con afirmaciones concretas que pueda verificar.

## 2. Respuesta obtenida (resumen fiel)

La herramienta propuso embeber las líneas dentro del pedido y formuló estas
afirmaciones:

1. «MongoDB no soporta transacciones ACID multidocumento; solo garantiza
   atomicidad por documento.»
2. «MongoDB es más rápido que PostgreSQL para leer pedidos completos porque
   evita los JOIN.»
3. «El esquema flexible permite guardar cualquier documento, así que no se
   pueden imponer reglas de integridad.»
4. «Un pedido con todas sus líneas puede crecer sin un límite práctico.»

Recomendó migrar el subconjunto a MongoDB y mantener PostgreSQL solo como
respaldo histórico.

## 3. Contraste con documentación oficial y laboratorio

| # | Afirmación de la IA | Documentación oficial | Resultado en el laboratorio | Veredicto |
|---|---|---|---|---|
| 1 | «No hay transacciones ACID multidocumento.» | MongoDB soporta transacciones multidocumento en *replica sets* y clústeres fragmentados; los despliegues *standalone* **no** las soportan ([Transactions](https://www.mongodb.com/docs/manual/core/transactions/)). | `mongodb/06_pruebas_afirmaciones_ia.js`: en el `mongod` local (standalone) la sesión falla con `Transaction numbers are only allowed on a replica set member or mongos`. | **Imprecisa.** Es falsa como afirmación general y verdadera solo para nuestro despliegue. El diseño no necesita transacciones multidocumento porque el pedido y sus líneas viven en un único documento (escritura atómica). |
| 2 | «MongoDB es más rápido porque evita JOIN.» | El embebido reduce operaciones y permite recuperar datos relacionados en una sola operación, pero no garantiza superioridad de rendimiento ([Embedded Data](https://www.mongodb.com/docs/manual/data-modeling/embedding/)). | Consulta c): MongoDB examina 2 documentos y 2 claves de índice (1 ms); PostgreSQL resuelve con *index-only scans* y *nested loop* en 0,086 ms para el mismo resultado (2 pedidos). La muestra es demasiado chica para un benchmark. | **No sostenible como afirmación absoluta.** La ventaja comprobada es de **número de operaciones** (un documento frente a tres tablas), no de velocidad. |
| 3 | «No se pueden imponer reglas de integridad.» | MongoDB permite validación de esquema con `$jsonSchema`; `validationAction: "error"` rechaza inserciones y actualizaciones inválidas ([Schema Validation](https://www.mongodb.com/docs/manual/core/schema-validation/)). | El validador de `mongodb/01_crear_coleccion.js` rechazó el documento de prueba con `cantidad: 0`: `Document failed validation` (`mongo_06_pruebas_ia.txt`). | **Falsa.** El esquema flexible no impide validar tipos, campos obligatorios, dominios y rangos. |
| 4 | «El documento puede crecer sin límite.» | Los documentos BSON tienen un tamaño máximo de 16 MiB ([Embedding](https://www.mongodb.com/docs/manual/data-modeling/embedding/)). | Los pedidos migrados tienen 2 líneas y 1,5 KB promedio; el arreglo es acotado por la operación. | **Falsa.** El embebido es adecuado solo para arreglos acotados; para históricos ilimitados correspondería referenciar. |

## 4. Correcciones aplicadas a la propuesta de la IA

- Se mantuvo el embebido de líneas, pero **no** se migró el núcleo transaccional:
  PostgreSQL conserva claves foráneas, *checks* y el precio histórico.
- Se agregó un **validador `$jsonSchema`** y una verificación de integridad
  ejecutable (`mongodb/03_verificacion_integridad.js`), en lugar de confiar en
  la flexibilidad del esquema.
- No se afirmó una mejora de rendimiento: solo se documentó el número de
  documentos/operaciones y se midió el plan de ejecución de ambos motores.
- La recomendación final se corrigió a **arquitectura combinada**: PostgreSQL
  como fuente de verdad y MongoDB como proyección de lectura si el volumen lo
  justifica.

## 5. Verificación humana

- Cada script fue leído antes de ejecutarse y se ejecutó sobre datos reales de
  `foodstore` (12 pedidos, 24 líneas) y MongoDB 7.0.14 local.
- Las salidas completas quedaron en `evidencia/` y la comparación cruzada se
  automatizó en `verificar_entrega.ps1` (26 comprobaciones).
- Las afirmaciones 1 a 4 se contrastaron con las páginas oficiales citadas y con
  resultados reproducibles, no con la respuesta de la IA.
