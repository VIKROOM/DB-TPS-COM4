# Declaración de Uso de IA (DUIA) — Parte 2 · Concurrencia con dos sesiones

**TP:** 2 · Concurrencia e IA (Parte 2)
**Motor:** PostgreSQL 17.10 · **Base de trabajo:** `foodstore_tp2` (copia)

---

| Campo | Completar |
|---|---|
| **Herramienta** | OpenCode (modelo de línea big-pickle) |
| **Spec o prompt utilizado** | "Generá y ejecutá, sobre el esquema FoodStore con dos sesiones concurrentes de psql, la reproducción de: (1) lectura no repetible en READ COMMITTED y su eliminación en REPEATABLE READ; (2) lectura fantasma en READ COMMITTED y su eliminación en REPEATABLE READ; (3) espera por bloqueo con SELECT FOR UPDATE; y (4, opcional) interbloqueo real con orden cruzado (error 40P01). Para cada escenario, guardá la explicación que darías y verificala en el motor." |
| **Qué generó** | Los scripts por sesión en `concurrencia/escenarioN/` (sA_rc.sql, sA_rr.sql, sB*.sql, sA.sql, sB.sql), los orquestadores `runN.ps1` que lanzan las dos sesiones en paralelo, y el archivo `informe_concurrencia.md`. |
| **Qué se aceptó** | El enfoque de simular dos sesiones con dos procesos `psql` lanzados en paralelo vía `Start-Process`, con `pg_sleep()` y una señal (`sync_deadlock`) para coordinar el interbloqueo. Los 4 scripts de sesión y el informe tal como se generaron. |
| **Qué se modificó o descartado, y por qué** | 1) El interbloqueo se intentó primero sin sincronización y no se formaba el ciclo por timing; se agregó una tabla `sync_deadlock` y un bucle de espera en la Sesión A para garantizar que B ya tuviera la fila 2 antes del cruce. 2) En el escenario 2, las corridas coincidentes se aislaron borrando la fila 'Fugazzeta' entre repeticiones para no contaminar el `count`. 3) En el escenario 1/2 se restauró `precio = 800` entre corridas para mantener el estado base reproducible. |
| **Verificación realizada** | Cada escenario se ejecutó realmente y se capturó la salida del motor en `salida_*.txt`: RC mostró 800→850 y count 1→2; RR mantuvo 800 y 1; el bloqueo B esperó de 18:05:25 a 18:05:28; el interbloqueo abortó a la sesión A con error 40P01. Todas las explicaciones de la IA se confirmaron en el motor (ver informe). |

## Verificación humana

- Los scripts se leyeron antes de ejecutarse (política de la cátedra).
- Las salidas reales del motor (`salida_*.txt`) respaldan cada afirmación del `informe_concurrencia.md`.
- Se aplicó la regla: la explicación que vale es la que confirma el motor, no la que da el modelo.