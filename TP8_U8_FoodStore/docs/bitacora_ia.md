# Bitácora de uso de IA — TP Unidad 8 (Food Store en la feria)

**Herramienta:** OpenCode (agente de IA en CLI)
**Fecha de trabajo:** 04/11/2026
**Alcance:** base SQLite de la tablet, semáforo de sincronización y code review
de los scripts de las unidades 3 y 5.
**Datos:** todos los datos usados son inventados. No se enviaron contraseñas,
mails ni datos personales reales.

---

## Entrada 1 — Esquema de la tablet (consigna 1.b)

**Qué se le pidió.** Diseñar las cuatro tablas SQLite (`producto_cache`,
`pedido_borrador`, `item_borrador`, `cola_sync`) para una tablet que trabaja sin
señal, con claves foráneas, precios en centavos y estados acotados.

**Qué se aceptó.**
- Las cuatro tablas `STRICT` y `PRAGMA foreign_keys = ON`.
- `precio_centavos` entero y `CHECK (precio_centavos >= 0)`.
- `disponible` y `eliminado` como enteros 0/1 con `CHECK`.
- `solicitud_uuid` como clave primaria de `cola_sync`.

**Qué se descartó y por qué.**
- Se descartó guardar el precio como `REAL`: el punto flotante puede producir
  diferencias de centavos al comparar. Se reemplazó por centavos enteros.
- Se descartó una tabla de clientes en la tablet: no se necesita para armar un
  borrador y agregaría datos personales innecesarios.

**Verificación humana.** El script se ejecutó desde cero y las pruebas
`evidencias/02_pruebas_sqlite.txt` muestran el borrador confirmado con
`COMMIT`, el `ROLLBACK` sin filas y los errores C7.

---

## Entrada 2 — Semáforo de sincronización (consigna 2.b)

**Qué se le pidió.** Escribir una consulta SQLite que compare cada solicitud
`PENDIENTE` contra `snapshot_servidor` y guarde estado y motivo, con prioridad
rojo > amarillo > verde.

**Qué se aceptó.**
- Agrupar por `solicitud_uuid` y contar ítems con problemas mediante `SUM(CASE ...)`.
- Actualizar solo las filas `PENDIENTE`.
- No escribir nada en PostgreSQL: `SIMULADO_APROBADO` no es una venta.

**Qué se descartó y por qué.**
- Se descartó una versión que solo comparaba precios: no detectaba stock
  insuficiente ni bajas lógicas. Se agregaron las condiciones de producto
  inexistente, `eliminado = 1`, `disponible = 0` y `cantidad > stock_visto`.
- Se descartó evaluar todas las filas de `cola_sync`: repetir la simulación
  habría cambiado `evaluado_en` y roto la idempotencia de C6.

**Verificación humana.** Los casos C2 a C6 se ejecutaron contra PostgreSQL
temporal y SQLite real; el detalle está en
`evidencias/04_semaforo_casos.txt` y el diff de invariantes en
`evidencias/05_verificacion_postgres_diff.txt`.

---

## Entrada 3 — Code review de los scripts de U3 y U5 (consigna 3.c)

**Qué se le pidió.** Revisar todos los scripts de la cursada y proponer
hallazgos con decisión (aceptado, corregido o descartado), indicando cómo se
comprueba cada uno en la base.

**Qué se aceptó.**
- H1: los grants de tabla sobre `usuario` exponen columnas sensibles.
- H2: `usuario_anon` creado con CTAS no tiene PK ni `NOT NULL`.
- H3: `v_pedidos_cliente` filtra clientes inactivos y pierde historial.
- H4: U5 referencia `usuario`/`detalle_pedido`, pero el esquema de U3 usa
  `cliente`/`linea_pedido`.
- H6: `ALTER DEFAULT PRIVILEGES ... GRANT SELECT (columna)` no es válido en
  PostgreSQL y corta el script de U5.

**Qué se descartó y por qué.**
- H5: se sospechó que `registrar_pedido` dejaba pedidos huérfanos al consumir
  la secuencia antes de validar. Se descartó: la prueba mostró que la secuencia
  avanza de 2 a 3, pero `pedido` sigue con 2 filas y hay 0 huérfanos porque
  `RAISE EXCEPTION` aborta la transacción. Los huecos de secuencia son normales.

**Verificación humana.** `scripts/revision_codigo.py` ejecuta los scripts reales
de U3 y U5 en un PostgreSQL temporal y deja la salida completa en
`evidencias/07_revision_codigo.txt`. Los archivos de otros TP se leen, no se
modifican.

---

## Entrada 4 — Informe y documentación

**Qué se le pidió.** Redactar el informe de las consignas 1.a, 2.c, 3.a, 3.b y
3.c, y ordenar el README de reproducción.

**Qué se aceptó.** La estructura por consigna y las tablas de casos, mapa de
motores y hallazgos.

**Qué se descartó y por qué.** Se descartaron afirmaciones sin evidencia (por
ejemplo, “la tablet es más rápida”): el TP no mide rendimiento y no corresponde
afirmarlo. También se descartó presentar `SIMULADO_APROBADO` como una venta.

**Verificación humana.** Cada número del informe se contrastó con las evidencias
`00_resumen.txt`, `04_semaforo_casos.txt`, `05_verificacion_postgres_*.txt`,
`06_estado_productos_*.txt` y `07_revision_codigo.txt`.
