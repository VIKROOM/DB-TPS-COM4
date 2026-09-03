# Protocolo de Seguridad — TP2 Laboratorio de Concurrencia e IA

**Materia:** Base de Datos II — Tecnicatura Universitaria en Programación (UTN)
**TP:** 2 · Concurrencia e IA como motor primario (Unidad 1, Semana 2)
**Motor:** PostgreSQL 17.10 · **Cliente:** DBeaver / psql
**Integrantes:** Guillot Tiago, Monardez Maximo, Ruiz Matias, Mendez Joaquin, Oviedo Thiago y Chacon Facundo
**Proyecto integrador:** Food Store (`schema.sql` de la Semana 1)

---

## Regla de fondo

> Se delega la escritura, nunca la decisión.

Todo script —propio o generado por una IA— que toque la base se aplica **siempre** siguiendo este protocolo de tres pasos. No es una excepción que se salta cuando el cambio "parece trivial": un `UPDATE` sin `WHERE` no parece riesgoso hasta que borra todo.

Este documento adapta los tres pasos de la cátedra al entorno real del proyecto (PostgreSQL 17 local, base `foodstore`, respaldo con `pg_dump`).

---

## Los tres pasos: copia → transacción → respaldo

### Paso 1 — Copia (siempre sobre una base de desarrollo)

Nunca se trabaja sobre la base que contiene datos que importan. La base real de trabajo de Semana 1 es `foodstore`; para el TP2 se trabaja sobre una **copia** creada a partir de una plantilla.

```bash
# 1. Crear la copia de trabajo usando la base real como plantilla
createdb -U postgres -h localhost -T foodstore foodstore_tp2

# 2. Verificar que la copia tiene el mismo esquema y los mismos datos
psql -U postgres -h localhost -d foodstore_tp2 -c "\dt"
```

> **Cuándo se salta:** no aplica. Siempre hay copia. Si no existiera la base plantilla, se carga `schema.sql` en una base vacía nueva.

> **Nota de entorno:** `createdb -T` con copia template necesita que nadie esté conectado a la base origen al momento de copiarla (`foodstore` debe estar sin conexiones activas). Si está en uso, usar `pg_dump` + `pg_restore` como alternativa de copia.

---

### Paso 2 — Transacción (todo script de escritura empieza con BEGIN)

Todo script que escribe corre primero dentro de una transacción que se revierte, para **inspeccionar el efecto** (filas afectadas, mensajes de error) antes de confirmar nada.

```sql
BEGIN;

-- ... script de escritura (INSERT / UPDATE / DELETE / DDL) ...
-- ... prueba con casos válidos e inválidos ...

-- Inspeccionar el efecto ANTES de confirmar:
SELECT * FROM <tabla> WHERE ...;

-- Si algo salió mal, deshacer todo:
ROLLBACK;

-- Solo cuando se entiende y verifica el efecto:
COMMIT;
```

> **Cuándo se salta:** no aplica. Siempre `BEGIN` antes de escribir. El `ROLLBACK` es la red de seguridad que permite que un error propio —o de la IA— no toque nada real.

---

### Paso 3 — Respaldo (obligatorio antes de cualquier cambio estructural)

Antes de aplicar un cambio estructural (`ALTER TABLE`, `DROP`, una migración o un trigger nuevo), se hace un respaldo independiente. El `ROLLBACK` del Paso 2 alcanza para una transacción puntual, pero no para decisiones estructurales que conviene poder volver atrás sin depender de la transacción.

```bash
# Respaldo lógico completo de la copia de trabajo, con marca de fecha/hora
pg_dump -U postgres -h localhost -d foodstore_tp2 \
  --file="C:\UTN\3er semestre\Bases de Datos II\UNIDAD 1\backups\foodstore_tp2_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"

# Listar respaldos disponibles
Get-ChildItem "C:\UTN\3er semestre\Bases de Datos II\UNIDAD 1\backups"
```

> **Cuándo se salta:** no aplica. Siempre respaldo antes de DDL.

> **Lugar donde vive el respaldo:** carpeta `backups/` dentro del directorio del proyecto, que se conserva localmente (está excluida del repositorio Git por `.gitignore`, porque es un artefacto regenerable vía `pg_dump`). Se usa `pg_dump` (respaldo lógico) porque es portable y legible.

---

## Checklist que se repite en CADA operación

- [ ] Trabajo sobre la **copia** `foodstore_tp2`, nunca sobre `foodstore`.
- [ ] Respaldo `pg_dump` tomado antes de cualquier DDL.
- [ ] Script **leído línea por línea** antes de ejecutarlo (ningún script de IA se corre sin leerse).
- [ ] Script aplicado dentro de `BEGIN ... ROLLBACK` y verificado antes del `COMMIT`.
- [ ] Si era script de IA: `git diff` revisado línea a línea y DUIA completada.

---

## Dónde vive este protocolo

Este archivo (`protocolo_seguridad.md`) se commitea en la raíz del repo **antes** de avanzar a la Parte 1. Sin este archivo no se continúa.
