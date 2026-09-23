# Food Store — Unidad 3 · Semana 1 · Índices, vistas y vistas materializadas

Trabajo Práctico sobre el proyecto integrador Food Store. Se agregan
**índices, vistas y una vista materializada** SIN modificar el modelo de datos
(los archivos heredados `schema.sql`, `data.sql` y `queries.sql` solo se
amplían/adaptan al esquema real, nunca se altera el DDL de las tablas).

## Estructura

```
food-store/
├── schema.sql              (heredado, sin modificar)
├── data.sql                (heredado, ampliado a volumen masivo reproducible)
├── queries.sql             (heredado — carga de trabajo real de Semanas 3-4)
├── indices.sql             (nuevo — Parte A)
├── views.sql               (nuevo — Partes B y C: vistas + vista materializada)
├── specs/                  (especificaciones de Kiro para cada pieza)
├── duia.md                 (bitácora de uso de IA)
├── informe_mediciones.md   (EXPLAIN ANALYZE antes/después, lectura y escritura)
├── README.md               (este archivo)
├── 01_explain_antes.sql    (planes ANTES de indexar — Parte A)
├── 02_diagnostico_candidatos.sql (identificación de Seq Scan)
├── 03_escritura_antes.sql  (costo de escritura ANTES, BEGIN...ROLLBACK)
├── 04_explain_despues.sql  (planes DESPUÉS de indexar)
├── 05_escritura_despues.sql(costo de escritura DESPUÉS, BEGIN...ROLLBACK)
├── 06_verificacion_vistas.sql (equivalencia vista vs consulta manual, EXCEPT)
├── 07_vista_materializada.sql (creación + índice único + mediciones)
└── planes/                 (salidas de EXPLAIN ANALYZE y \timing)
```

## Requisitos

- PostgreSQL 16+ con extensiones `pg_trgm` (indices trigram).
- Usuario `postgres` (o uno con permisos de creación de objetos).

## Cómo reproducir las pruebas

```powershell
$env:PGPASSWORD = '<password de postgres>'

# 1. Crear la base de trabajo (copia, según protocolo de seguridad)
psql -U postgres -h localhost -d postgres -c "CREATE DATABASE foodstore_u3;"

# 2. Cargar esquema + datos (volumen masivo reproducible)
psql -U postgres -h localhost -d foodstore_u3 -X -v ON_ERROR_STOP=1 -f schema.sql
psql -U postgres -h localhost -d foodstore_u3 -X -v ON_ERROR_STOP=1 -f data.sql

# 3. Medir ANTES (planes Seq Scan + costo de escritura)
psql -U postgres -h localhost -d foodstore_u3 -X -f 01_explain_antes.sql
psql -U postgres -h localhost -d foodstore_u3 -X -f 02_diagnostico_candidatos.sql
psql -U postgres -h localhost -d foodstore_u3 -X -f 03_escritura_antes.sql

# 4. Crear los índices (Parte A)
psql -U postgres -h localhost -d foodstore_u3 -X -v ON_ERROR_STOP=1 -f indices.sql

# 5. Medir DESPUÉS
psql -U postgres -h localhost -d foodstore_u3 -X -f 04_explain_despues.sql
psql -U postgres -h localhost -d foodstore_u3 -X -f 05_escritura_despues.sql

# 6. Vistas y verificación de equivalencia (Parte B)
psql -U postgres -h localhost -d foodstore_u3 -X -v ON_ERROR_STOP=1 -f views.sql
psql -U postgres -h localhost -d foodstore_u3 -X -f 06_verificacion_vistas.sql

# 7. Vista materializada + mediciones (Parte C)
psql -U postgres -h localhost -d foodstore_u3 -X -f 07_vista_materializada.sql
```

Todas las cargas de escritura (03/05) corren dentro de `BEGIN...ROLLBACK`:
no modifican la tabla base de forma permanente.

## Resultados principales

| Pieza | Métrica | Antes → Después |
|-------|---------|-----------------|
| C1 · Ventas de un producto | plan / tiempo | Seq Scan 400k → Index Scanne · 36,6 → 0,3 ms |
| C2 · Búsqueda por nombre | plan / tiempo | Seq Scan → Bitmap trigram · 31,6 → 1,2 ms |
| C3 · Reposición de stock | plan / tiempo | Seq Scan → Bitmap parcial · 7,0 → 4,5 ms |
| Escritura (Parte A) | 5.000 INSERTs | 84,4 → 107,6 ms (+28%) |
| Vista materializada | consulta | 484,9 → 0,026 ms (~18.600×) |

Índice descartado por sobreindexación: `pedido(forma_pago)` (baja cardinalidad)
y `producto(categoria_id, nombre)` (duplicado del UNIQUE existente). Detalle y
justificación en `informe_mediciones.md` y `duia.md`.

## Nota de equivalencia con el enunciado

El enunciado genérico menciona tablas `usuario`/`detalle_pedido`. El esquema
real del proyecto (Semanas 1-4) usa `cliente`/`linea_pedido` para los mismos
roles. Se trabaja sobre los objetos realmente existentes y la correspondencia
queda documentada (ver `informe_mediciones.md` y `duia.md`).