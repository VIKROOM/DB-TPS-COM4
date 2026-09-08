# Declaración de Uso de IA (DUIA) — Parte 3 · Lectura crítica

**TP:** 2 · Concurrencia e IA (Parte 3)
**Regla de fondo:** ningún script generado por IA se ejecuta sin leerse antes.

---

| Campo | Completar |
|---|---|
| **Herramienta** | OpenCode (modelo de línea big-pickle) |
| **Spec o prompt utilizado** | "Enunciado Parte 3 de la consigna: para cada uno de estos dos scripts 'generados para dar de baja registros vencidos', identificá qué filas afectaría realmente tal como está escrito, por qué eso no coincide con la consigna que dice cumplir, y reescribilo corregido (con su WHERE, o con el manejo correcto de NULL en la subconsulta, según corresponda)." |
| **Qué generó** | El análisis de los dos scripts (`UPDATE funcion SET activa = FALSE;` sin WHERE y `DELETE FROM categoria WHERE id NOT IN (...)`), la explicación del efecto real de cada uno y sus versiones corregidas, incluidas en `ejercicio_lectura_critica.md`. |
| **Qué se aceptó** | El diagnóstico en ambos casos: (1) el `UPDATE` sin `WHERE` afecta el 100 % de las filas y se corrige con un `WHERE` que identifique el subconjunto pedido; (2) el `NOT IN` es peligroso con `NULL` (si la subconsulta devuelve un `NULL`, la condición nunca es verdadera y el `DELETE` no borra nada), y se corrige con `NOT EXISTS`. |
| **Qué se modificó o descartado, y por qué** | La corrección se adaptó al dominio del proyecto FoodStore: como FoodStore usa **baja lógica** (`activo`), el equivalente real de "dar de baja" no es `DELETE` sino `UPDATE ... SET activo = FALSE`. Además se dejó el análisis sobre el esquema genérico de cátedra (donde `producto.categoria_id` puede ser nullable) y se aclaró que en `schema.sql` la FK es `NOT NULL`, pero que por defensa del código conviene `NOT EXISTS` igual. |
| **Verificación realizada** | Se trazó el efecto de cada script contra el esquema (`schema.sql`): el `UPDATE` sin `WHERE` recorre toda la tabla; el `NOT IN` depende de la presencia de `NULL` en `producto.categoria_id`, que la FK `NOT NULL` de FoodStore excluye pero el esquema genérico no. Con `NOT EXISTS` la semántica es correcta en ambos escenarios. La conclusión coincide con el patrón común de los incidentes documentados (Replit, Gemini CLI, PocketOS, confusión de entorno). |

## Verificación humana

- El análisis fue revisado y entendido línea por línea ANTES de considerarlo correcto (política de la cátedra).
- La guía de la consigna pide entregar "qué filas afectaría realmente cada uno, por qué no coincide y la versión corregida"; el archivo `ejercicio_lectura_critica.md` cubre los tres campos para ambos scripts.
- Ninguno de estos scripts se ejecutó jamás contra la base: se analizaron como ejercicio de lectura crítica, sin tocar `foodstore` ni `foodstore_tp2`.