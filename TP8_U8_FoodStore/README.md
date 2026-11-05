# TP Unidad 8 — Food Store en la feria

**Asignatura:** Bases de Datos II · Comisión 4
**Integrante:** Facundo Chacón
**Repositorio:** <https://github.com/VIKROOM/DB-TPS-COM4>
**Motores:** PostgreSQL 16+ · SQLite 3.37+ · MongoDB 7 (proyección de la U7)
**Entrega:** carpeta `TP8_U8_FoodStore/` (el `.zip` o la etiqueta `tp8` del repositorio)

> **Regla de oro:** el móvil propone, el servidor dispone. La tablet solo
> consulta el catálogo y arma borradores. El precio, el stock y las ventas los
> decide PostgreSQL. `SIMULADO_APROBADO` **no es una venta**.

## Estructura

```
TP8_U8_FoodStore/
├── README.md                       este archivo
├── movil/
│   ├── schema_sqlite.sql           consigna 1.b: tablas de la tablet
│   ├── pruebas_sqlite.sql          consigna 1.c: COMMIT, ROLLBACK, C1 y C7
│   ├── semaforo.sql                consigna 2.b: clasificación de solicitudes
│   ├── importar_snapshot.sql       consigna 2.a: CSV → SQLite + UPSERT
│   ├── servidor_snapshot.csv       instantánea exportada de PostgreSQL
│   └── foodstore_movil.db          base SQLite lista para abrir
├── servidor/
│   ├── 00_seed_servidor.sql        copia de laboratorio con datos inventados
│   ├── 01_v_snapshot_movil.sql     vista de instantánea
│   ├── 02_exportar_snapshot.sql    exportación a CSV
│   ├── 03_verificacion_postgres.sql invariantes antes/después
│   └── 04_estado_productos.sql     precio/stock/activo antes/después
├── scripts/
│   ├── simular_tp8.py              reproduce todo y genera las evidencias
│   └── revision_codigo.py          consigna 3.c: code review comprobado
├── evidencias/                     salidas reales de las ejecuciones
└── docs/
    ├── informe.pdf                 consignas 1.a, 2.c, 3.a, 3.b y 3.c (≤ 6 páginas)
    ├── generar_informe.py          genera el PDF con ReportLab
    ├── kiro/
    │   ├── requirements.md         cuatro requisitos EARS con su caso
    │   ├── design.md               diseño de la base y del semáforo
    │   └── tasks.md                tareas y verificación
    ├── bitacora_ia.md              qué se pidió, qué se aceptó y qué se descartó
    └── DUIA.md                     Declaración de Uso de IA
```

## Requisitos

- PostgreSQL 16 o superior (servidor real de pruebas o `pgserver` portable).
- SQLite 3.37 o superior. Si no está el ejecutable `sqlite3`, se puede usar el
  módulo `sqlite3` de Python o el runner automático.
- Python 3.10+ con `pgserver`, `reportlab` y `pypdf`:

```powershell
python -m pip install pgserver reportlab pypdf
```

- PowerShell 5.1+ (Windows) para los comandos de ejemplo.

## Orden para crear todo desde cero

### 1. Servidor PostgreSQL de pruebas

Trabajar sobre una base de prueba, nunca sobre la base real. Desde
`TP8_U8_FoodStore/`:

```powershell
psql -f servidor/00_seed_servidor.sql
psql -f servidor/01_v_snapshot_movil.sql
```

El seed crea `categoria`, `producto`, `cliente`, `pedido` y `linea_pedido` con
datos inventados, y la vista `v_snapshot_movil` deja solo lo que viaja a la
tablet.

### 2. Exportar la instantánea

Con una ruta absoluta o relativa al directorio actual:

```powershell
psql -c "\copy (SELECT * FROM v_snapshot_movil) TO 'movil/servidor_snapshot.csv' CSV HEADER"
```

El CSV queda en `movil/servidor_snapshot.csv`. Los booleanos de psql viajan
como `t` / `f` y se normalizan a 0/1 al importar.

### 3. Crear la base de la tablet

Desde `TP8_U8_FoodStore/movil/`:

```powershell
sqlite3 foodstore_movil.db < schema_sqlite.sql
sqlite3 foodstore_movil.db < importar_snapshot.sql
```

`importar_snapshot.sql` usa el meta-comando `.import --csv --skip 1`; por eso
debe ejecutarse desde `movil/`, donde está el CSV.

### 4. Probar la tablet (consigna 1.c)

```powershell
sqlite3 foodstore_movil.db < pruebas_sqlite.sql
```

Se muestran: borrador completo con `COMMIT`, operación deshecha con `ROLLBACK`,
catálogo disponible sin servidor (C1) y los errores C7 (cantidad 0 y producto
inexistente) sin filas nuevas.

### 5. Correr el semáforo (consigna 2.b)

Con borradores cargados en `cola_sync`:

```powershell
sqlite3 foodstore_movil.db < semaforo.sql
```

Solo se evalúan solicitudes `PENDIENTE`. El resultado queda en `cola_sync` con
`estado`, `motivo` y `evaluado_en`.

### 6. Reproducción automática de los casos C2 a C6

El runner hace todo el circuito en un PostgreSQL temporal y deja las
evidencias:

```powershell
python scripts/simular_tp8.py
```

Pasos que ejecuta: levanta PostgreSQL portable, carga el seed y la vista,
exporta el CSV, crea SQLite, importa la instantánea, corre las pruebas de la
consigna 1.c, simula C2 a C6, verifica que pedidos/líneas/stock/importe no
cambiaron y escribe `evidencias/`.

### 7. Code review con IA (consigna 3.c)

```powershell
python scripts/revision_codigo.py
```

Lee los scripts de `food-store/` (U3) y `TP5_U5_Seguridad_FoodStore/` (U5), los
ejecuta en bases temporales y comprueba cada hallazgo con consultas al motor.
La salida completa queda en `evidencias/07_revision_codigo.txt`.

> Este script **solo lee** los archivos de otros TP. Las bases que crea viven en
> un clúster temporal en `%TEMP%` y se eliminan al terminar. No modifica
> archivos de U3, U5 ni de ningún otro trabajo práctico.

### 8. Generar el informe

```powershell
python docs/generar_informe.py
```

Genera `docs/informe.pdf` (máximo 6 páginas) a partir de las evidencias.

## Resultados verificados

| Caso | Preparación | Resultado obtenido |
|---|---|---|
| C2-A | Subir el precio del producto 1 en el servidor | `CONFLICTO` / `PRECIO_CAMBIADO` |
| C2-B | Aceptar el precio y enviar una solicitud nueva | `SIMULADO_APROBADO` / `TODO_COINCIDE` |
| C3 | Borrador por 15 unidades con stock 10 | `RECHAZADO` / `STOCK_INSUFICIENTE` |
| C4 | Baja lógica del producto 5 después del borrador | `RECHAZADO` / `PRODUCTO_DADO_DE_BAJA` |
| C5 | Borrador sin cambios | `SIMULADO_APROBADO` / `TODO_COINCIDE` |
| C6 | Reenviar el mismo UUID y repetir el semáforo | Error de PK; una sola fila y `evaluado_en` sin cambios |
| C7a | Cantidad 0 en SQLite | Error de `CHECK`; 0 filas nuevas |
| C7b | Producto inexistente en SQLite | Error de FK; 0 filas nuevas |

Invariantes de PostgreSQL antes/después: `pedido = 3`, `linea_pedido = 5`,
`producto = 5`, `cliente = 3`, `suma_stock = 115`, `importe_lineas = 5750.00`.
El diff está vacío (`evidencias/05_verificacion_postgres_diff.txt`).

## Evidencias principales

| Archivo | Contenido |
|---|---|
| `evidencias/00_resumen.txt` | Resumen de la ejecución y diff de invariantes |
| `evidencias/01_seed_y_vista.txt` | Seed del servidor y creación de la vista |
| `evidencias/02_pruebas_sqlite.txt` | Pruebas 1.c |
| `evidencias/03_snapshot_export.txt` | CSV exportado e importado |
| `evidencias/04_semaforo_casos.txt` | Casos C2 a C6 y estado final de `cola_sync` |
| `evidencias/05_verificacion_postgres_*.txt` | Invariantes antes/después y diff |
| `evidencias/06_estado_productos_*.txt` | Productos antes/después de C2 y C4 |
| `evidencias/07_revision_codigo.txt` | Hallazgos H1 a H6 comprobados en PostgreSQL |
| `evidencias/snapshot_v1.csv` a `v3.csv` | Instantáneas de cada momento |

## Decisiones y límites

- La tablet no escribe en PostgreSQL: solo recibe la instantánea y arma
  borradores.
- El precio viaja en centavos enteros para evitar errores de punto flotante.
- La baja lógica se representa con `eliminado = 1`; la fila no se borra para no
  romper borradores viejos.
- No viajan clientes, usuarios, contraseñas, mails, ventas ni logs.
- La simulación se hace sobre una copia de laboratorio con datos inventados.
- La protección real de idempotencia debe estar en el servidor (clave única de
  la solicitud + transacción); la PK de SQLite solo protege esa tablet.
- El orden de las tablas en el esquema respeta las claves foráneas: primero
  `producto_cache`, después `pedido_borrador`, `item_borrador` y `cola_sync`.
