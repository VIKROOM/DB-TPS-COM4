# Autoevaluación — TP Unidad 7 (NoSQL / Food Store)

**Trabajo:** modelado y consulta del subconjunto «pedidos y detalle de pedidos» en
MongoDB, con migración desde PostgreSQL y verificación cruzada.
**Integrante:** Facundo Chacón · **Repositorio:** <https://github.com/VIKROOM/DB-TPS-COM4>
**Motores:** PostgreSQL 17 (`foodstore`) · MongoDB 7.0.14 Community + mongosh 2.3.1
**Método:** el trabajo se dividió en 7 actividades (una por consigna). Cada actividad
se cerró con una lista de control verificable; cuando una comprobación falló, se
corrigió el artefacto y se volvió a ejecutar. Al final se corre
`verificar_entrega.ps1`, que automatiza 26 comprobaciones sobre los entregables
reales (no sobre el texto del informe).

---

## 1. División en actividades

| # | Actividad | Consigna | Entregable principal |
|---|---|---|---|
| A1 | Modelo documental y correspondencia | 1 | Sección 1 del informe + documento de ejemplo |
| A2 | Creación de base/colección y migración | 2 | `sql/01_exportar_pedidos_mongodb.sql`, `mongodb/01_crear_coleccion.js`, `mongodb/02_datos_pedidos.js` |
| A3 | Reglas de integridad y justificación del embebido | 3 | Sección 2 del informe + `mongodb/03_verificacion_integridad.js` |
| A4 | Consultas a–d en MongoDB | 4 | `consultas_mongodb.js` + `evidencia/mongo_04_consultas.txt` |
| A5 | Equivalentes en PostgreSQL y tabla comparativa | 5 | `consultas_postgresql.sql` + tabla de la sección 3 |
| A6 | Consulta a IA y contraste de afirmaciones | 6 y 7 | `BITACORA_IA.md` + `mongodb/06_pruebas_afirmaciones_ia.js` |
| A7 | Conclusión, PDF único y presentación | 7 y Entrega | `informe/Informe_TP_U7_NoSQL_FoodStore.pdf` (2 páginas) |

---

## 2. Lista de control por actividad

### A1 — Modelo documental (consigna 1)

| Criterio | Verificación | Estado |
|---|---|---|
| Subconjunto elegido y acotado | «pedidos y detalle de pedidos», ids 1–12 | OK |
| Tablas y claves de PostgreSQL identificadas | `pedido(id)`, `linea_pedido(pedido_id, producto_id)`, `cliente(id)`, `producto(id)` con sus FK y reglas | OK |
| Esquema documental breve con campos, embebidos y arreglos | Documento de ejemplo con `cliente{}` e `items[]` en la sección 1 | OK |
| Identificadores de origen conservados | `pedido_id`, `cliente_id`, `producto_id` presentes en los 12 documentos | OK |
| Decisión de agrupamiento justificada | Líneas embebidas (se leen juntas, arreglo acotado); cliente/producto referenciados por id | OK |

### A2 — Creación y migración (consigna 2)

| Criterio | Verificación | Estado |
|---|---|---|
| Base y colección creadas en MongoDB | `foodstore_nosql.pedidos`, creada por `mongodb/01_crear_coleccion.js` | OK |
| Mínimo cinco pedidos migrados | **12** pedidos y **24** líneas (mínimo exigido: 5) | OK |
| Migración por `insertMany()` | Script generado por PostgreSQL y ejecutado en mongosh | OK |
| Fecha, estado, cliente, productos, cantidades y precios históricos | Los 12 documentos tienen los 8 campos obligatorios | OK |
| Importes y cantidades respetados | Total migrado $560.979,00 = total en PostgreSQL | OK |

### A3 — Integridad (consigna 3)

| Criterio | Verificación | Estado |
|---|---|---|
| Dos reglas de integridad explícitas | (1) identidad/referencia; (2) coherencia de cantidades e importes | OK |
| Regla 1 comprobada en el motor | 0 `pedido_id` duplicados; 0 líneas huérfanas contra `producto` | OK |
| Regla 2 comprobada en el motor | 0 subtotales incorrectos; 0 totales incorrectos en 12 documentos / 24 líneas | OK |
| Justificación del embebido vs. colecciones separadas | Sección 1 y metadatos de la migración | OK |
| Regla de estado documentada y reproducible | `fecha_corte = max(fecha lote) + 1 día`; 11 TERMINADO / 1 PENDIENTE | OK |

### A4 — Consultas MongoDB (consigna 4)

| Criterio | Verificación | Estado |
|---|---|---|
| a) Todos los pedidos con identificador y estado | 12 documentos `{pedido_id, estado}` | OK |
| b) Filtro por un estado existente | `estado: "TERMINADO"` → 11 pedidos (2–12) | OK |
| c) Producto dentro del arreglo de líneas | `items.producto_id: 1` → 2 pedidos (1, 2) | OK |
| d) Total superior a un importe elegido | `total > 50000.00` → 6 pedidos, $386.471,00 | OK |
| Umbral justificado | Promedio $46.748,25 y mediana $49.891,50: separa 6/12 sin ser trivial | OK |
| Consultas guardadas en el entregable | `consultas_mongodb.js` ejecutable de punta a punta | OK |

### A5 — Equivalentes en PostgreSQL (consigna 5)

| Criterio | Verificación | Estado |
|---|---|---|
| Equivalente de b) en SQL | `CASE` con la misma regla de estado, mismo lote | OK |
| Equivalente de c) en SQL | `JOIN linea_pedido` + `DISTINCT` | OK |
| Tabla con cantidad e IDs de ambos motores | Sección 3 del informe | OK |
| Diferencias explicadas o corregidas | Sin diferencias de datos; se explica la diferencia de sintaxis/modelo | OK |
| Comparación automatizada | 8 comprobaciones cruzadas dentro de `verificar_entrega.ps1` | OK |

### A6 — IA y contraste (consignas 6 y 7)

| Criterio | Verificación | Estado |
|---|---|---|
| Prompt menciona modelo actual, acceso a pedidos completos y coherencia | Prompt transcripto en `BITACORA_IA.md` | OK |
| Al menos dos afirmaciones contrastadas | Se contrastaron **4** afirmaciones | OK |
| Contraste con documentación oficial | 4 referencias a docs de MongoDB (transacciones, validación, embebido, límite 16 MiB) | OK |
| Contraste con el laboratorio | Validador rechaza documento inválido; transacción falla en standalone; `explain` de ambos motores | OK |
| Conclusión ≤ 200 palabras con ≥ 2 criterios técnicos | 196 palabras; criterios: patrón de acceso, integridad y costo operativo | OK |

### A7 — Entrega (PDF único)

| Criterio | Verificación | Estado |
|---|---|---|
| PDF único de hasta 5 páginas sin contar código | **2 páginas** verificadas con `pypdf` | OK |
| Modelo, evidencias, tabla de verificación, contraste y conclusión | Las 5 secciones están en el PDF | OK |
| `consultas_mongodb.js` y `consultas_postgresql.sql` adjuntos | Ambos en la raíz del TP | OK |
| Integrante y repositorio identificados | Portada del PDF y README | OK |
| Sin imágenes decorativas ni datos personales reales | Solo tablas, código y salidas; cliente de prueba sin email/teléfono | OK |

---

## 3. Bitácora real de iteraciones

### Iteración 0 — construcción (fallas detectadas y corregidas antes de la primera medición)

| Falla observada | Causa | Corrección aplicada | Reprueba |
|---|---|---|---|
| `mongodb/02_datos_pedidos.js` salía sin encabezado y con formato de tabla de psql | `\o` redirigía la salida pero `\echo` la seguía enviando a consola, y el formato `aligned` agregaba relleno | Se quitó el `\echo` del archivo, se agregó `\pset format unaligned` + `tuples_only on` y el encabezado se emite dentro del `SELECT` | Archivo con encabezado y `insertMany()` válido |
| `ERROR: in an aggregate with DISTINCT, ORDER BY expressions must appear in argument list` | `string_agg(DISTINCT id, ',' ORDER BY id)` no es válido en PostgreSQL | Se reemplazó por subconsulta `SELECT DISTINCT` + `string_agg(... ORDER BY ...)` | Consultas 5.b/5.c ejecutan sin error |
| El estado cambiaba según el día en que se ejecutara la extracción | La regla original usaba `now()` | Se cambió a `fecha_corte = max(fecha del lote) + 1 día`, dependiente solo de los datos | Misma salida en ejecuciones distintas |
| `verificar_entrega.ps1` abortaba con `No se encuentra ningún parámetro ... 'FilePath'` | `Set-Content` no tiene parámetro `-FilePath` | Se cambió a `-Path` | Script completa y escribe la evidencia |
| La consulta c) devolvía el importe inflado por el JOIN con líneas repetidas | `sum(DISTINCT total)` no deduplica correctamente el importe | Subconsulta con `SELECT DISTINCT l.id, t.total` y luego `sum(total)` | Importe c) = $79.810,00 en ambos motores |

### Iteración 1 — primera medición objetiva

Evidencia: `evidencia/autoevaluacion_iter1.txt` (26 comprobaciones, **21 OK / 5 fallas**).

| Falla | Esperado | Obtenido | Corrección |
|---|---|---|---|
| Archivo `informe/Informe_TP_U7_NoSQL_FoodStore.pdf` | SI | NO | Se escribió `informe/generar_informe.py` y se generó el PDF |
| Archivo `BITACORA_IA.md` | SI | NO | Se redactó con prompt, respuesta resumida y tabla de contraste |
| Archivo `README.md` | SI | NO | Se redactó con estructura, modelo, reproducción y resultados |
| Archivo `AUTOEVALUACION.md` | SI | NO | Este documento |
| Páginas del PDF (máximo 5) | ≤5 | PDF ausente | PDF de 2 páginas, verificado con `pypdf` |

Las 21 comprobaciones de datos ya pasaban en la iteración 1: 12 pedidos, 24 líneas,
0 huérfanas, 0 líneas inválidas, 12 documentos, y coincidencia exacta de cantidad,
IDs e importes en b) y c).

### Iteración 2 — verificación final

Ver `evidencia/verificacion_entrega.txt`. Resultado: **26/26 OK** (0 fallas),
incluido el límite de páginas del PDF. La ejecución se hace con:

```powershell
$env:PGPASSWORD="***"
.\verificar_entrega.ps1 `
  -Psql    "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -Mongosh "C:\...\mongosh.exe"
```

Antes de llegar a 26/26 se corrigieron dos detalles de la propia autoevaluación:

| Falla observada | Causa | Corrección aplicada |
|---|---|---|
| La comprobación de páginas marcaba FALLA con PDF de 2 páginas | Comparaba por igualdad de texto contra el literal `<=5` | El criterio ahora incluye el número obtenido y se compara `SI`, igual que el resto |
| El pie del PDF decía «Página 1 de 5» con un PDF de 2 páginas | El total estaba fijo en el generador | Se implementó `NumberedCanvas` para escribir «Página X de Y» con el total real |

---

## 4. Resultado consolidado

| Consulta | PostgreSQL | MongoDB | Coinciden |
|---|---|---|---|
| b) estado `TERMINADO` | 11 pedidos (2–12), $558.179,00 | 11 pedidos (2–12), $558.179,00 | Sí |
| c) producto 1 | 2 pedidos (1, 2), $79.810,00 | 2 pedidos (1, 2), $79.810,00 | Sí |
| d) total > $50.000,00 | — (no exigida en SQL) | 6 pedidos, $386.471,00 | N/A |
| Total de la muestra | $560.979,00 | $560.979,00 | Sí |

**Comprobaciones automatizadas:** 26 · **Fallas:** 0 · **Páginas del PDF:** 2 de 5.

---

## 5. Límites declarados

- El esquema real de Food Store **no tiene** columna de estado de pedido: el estado
  usado en 4.b es derivado con una regla documentada, no un dato nativo.
- La muestra es de 12 pedidos: alcanza para verificar equivalencia lógica, **no**
  para afirmar superioridad de rendimiento.
- El `mongod` de laboratorio es *standalone*: no admite transacciones
  multidocumento. El diseño no las requiere porque pedido y líneas forman un único
  documento.
- No se copiaron `email` ni `teléfono` del cliente (minimización de datos); los
  nombres de clientes de la base de desarrollo son de prueba.
