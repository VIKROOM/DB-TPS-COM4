# Declaración de Uso de IA (DUIA) — TP N.º 1

**Alumno:** [completar apellido, nombre]
**Legajo:** [completar]
**Fecha:** 21/08/2026

| # | Herramienta | Uso dado | Prompts / specs principales |
|---|---|---|---|
| 1 | OpenCode (CLI, modelo ox-alpha) | Motor primario para producir los entregables del TP: análisis del enunciado, diagrama ER (DBML/Mermaid), derivación al modelo relacional, desarrollo de la normalización paso a paso y generación de `schema.sql` | "Leé el enunciado del TP1 Food Store y resolvé las 4 partes: ER, modelo relacional, normalización hasta BCNF y DDL PostgreSQL. Estoy usando PostgreSQL y DBeaver." |
| 2 | DBeaver | Verificación: ejecución de `schema.sql` contra PostgreSQL 17 local y revisión visual del esquema generado | — |

## Verificación humana

- Cada script fue leído y revisado antes de ejecutarse (ningún script se ejecuta sin leerse).
- `schema.sql` se probó completo sobre una base vacía; la salida se verificó en DBeaver.
- Las decisiones de diseño (PK compuesta en `linea_pedido`, `ON DELETE RESTRICT/CASCADE`, no almacenar `subtotal`) fueron entendidas y defendidas por el alumno.
