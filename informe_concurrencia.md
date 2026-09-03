# Informe de Concurrencia — Parte 2

**TP:** 2 · Laboratorio de Concurrencia e IA (Unidad 1, Semana 2)
**Proyecto:** Food Store · **Motor:** PostgreSQL 17.10 · **Base de trabajo:** `foodstore_tp2` (copia según protocolo)
**Sesiones:** dos conexiones concurrentes de `psql` (Sesión A y Sesión B) sobre la misma base, según la consigna del TP.

> Método (regla de la cátedra): cada escenario se reprodujo → se pidió una explicación a la IA → se **verificó en el motor real** repitiendo el experimento con el nivel de aislamiento propuesto → se registró si la IA acertó. La que vale es la que confirma el motor, no la que da el modelo.

---

## Escenario 1 — Lectura no repetible

### Cómo se reprodujo
Tabla objetivo: `producto` (fila `id = 2`, Coca, precio base **800.00**).

- **Sesión A** (`concurrencia/escenario1_no_repetible/sA_rc.sql`): inicia transacción con `SET TRANSACTION ISOLATION LEVEL READ COMMITTED`, lee `precio`, duerme 5 s, y vuelve a leer `precio` en la misma transacción.
- **Sesión B** (`sB1.sql`): tras 2 s, actualiza `precio = 850.00` y hace `COMMIT` mientras A duerme.

### Qué se observó (salida real en el motor)
```
SESION A (READ COMMITTED)
>>> Lectura 1: precio = 800.00
>>> A espera 5 segundos mientras B actualiza y confirma...
>>> Lectura 2: precio = 850.00     <-- CAMBIO el valor en la misma transaccion
SESION B: UPDATE 1 / COMMIT / precio ahora es 850.00
```

### Explicación de la IA
> "Bajo `READ COMMITTED`, PostgreSQL toma un snapshot **nuevo por cada sentencia**. Los dos `SELECT` de la Sesión A son dos sentencias distintas y cada una ve una 'foto' distinta: la primera ve la versión con precio 800 y la segunda ve la versión posterior con precio 850 confirmada por B. Por eso el valor cambia dentro de la misma transacción: es una **lectura no repetible**. Con `REPEATABLE READ`, en cambio, la transacción toma **un único snapshot al inicio** y lo conserva hasta el `COMMIT`, por lo que ambas lecturas deberían ver el mismo 800 sin importar que B confirme el 850."

### Verificación en el motor
Se repitió el experimento con `SESION A` en `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` (`sA_rr.sql`), con B haciendo la misma actualización a 850 + `COMMIT`:

```
SESION A (REPEATABLE READ)
>>> Lectura 1: precio = 800.00
>>> Lectura 2: precio = 800.00     <-- NO cambia (mismo snapshot)
SESION B: UPDATE 1 / COMMIT / precio ahora es 850.00
```
(Registrado en `salida_A_rr.txt`.)

### Conclusión
La IA **acertó**. Bajo `READ COMMITTED` el valor cambió de 800 a 850 (lectura no repetible); bajo `REPEATABLE READ` se mantuvo en 800. El mecanismo es el **MVCC** y el nivel de aislamiento que resuelve el problema es `REPEATABLE READ` (snapshot único por transacción).

---

## Escenario 2 — Lectura fantasma

### Cómo se reprodujo
Tabla objetivo: `producto` filtrado por `categoria_id = 1` (Pizzas, estado base con **1** producto).

- **Sesión A** (`escenario2_fantasma/sA_rc.sql`): `BEGIN; SELECT count(*) FROM producto WHERE categoria_id = 1;` → duerme 5 s → repite el mismo `count(*)`.
- **Sesión B** (`sB2.sql`): tras 2 s, `INSERT INTO producto (categoria_id=1, nombre='Fugazzeta', ...)` y confirma.

### Qué se observó (salida real del motor)
```
SESION A (READ COMMITTED)
>>> COUNT 1: 1
>>> A espera 5 s mientras B inserta una pizza nueva y confirma...
>>> COUNT 2: 2        <-- aparecio una fila NUEVA que cumple el WHERE
SESION B: INSERT 0 1 / SESION B confirmo insercion de Fugazzeta
```

### Explicación de la IA
> "Una **lectura fantasma** es una fila nueva que aparece en el resultado de una consulta repetida dentro de la misma transacción, porque otra sesión la insertó y confirmó en el medio. En `READ COMMITTED`, cada sentencia ve un snapshot distinto, así que el segundo `count(*)` incluye la 'Fugazzeta' y cambia de 1 a 2. El nivel `REPEATABLE READ` de PostgreSQL sí resuelve los fantasmas (su snapshot único cubre también los `INSERT`), a diferencia del estándar SQL."

### Verificación en el motor
Se repitió con `SESION A` en `REPEATABLE READ` (`sA_rr.sql`), B insertando la misma fila:

```
SESION A (REPEATABLE READ)
>>> COUNT 1: 1
>>> COUNT 2: 1        <-- NO ve la fila insertada por B (sin fantasma)
SESION B: INSERT 0 1 / confirmo
```
(Registrado en `salida_A_rr.txt`; la corrida READ COMMITTED quedó en `salida_A_rc.txt`, ambas en el directorio del escenario 2.)

### Conclusión
La IA **acertó**. Bajo `READ COMMITTED` el `count` cambió de 1 a 2 (fantasma); bajo `REPEATABLE READ` se mantuvo en 1. En PostgreSQL, `REPEATABLE READ` elimina también los fantasmas; la anomalía aparece en `READ COMMITTED`.

---

## Escenario 3 — Espera por bloqueo (FOR UPDATE)

### Cómo se reprodujo
Tabla objetivo: `producto` (fila `id = 1`, Muzzarella).

- **Sesión A** (`escenario3_bloqueo/sA.sql`): `BEGIN; SELECT ... FROM producto WHERE id = 1 FOR UPDATE;` (toma bloqueo de fila), duerme 5 s, `COMMIT`.
- **Sesión B** (`sB.sql`): tras 2 s, `SELECT ... FROM producto WHERE id = 1 FOR UPDATE;` — debe quedar esperando hasta el `COMMIT` de A.

### Qué se observó (salida real del motor, con timestamps)
```
SESION A: bloquea fila 1, duerme, COMMIT (libera el bloqueo)
SESION B:
  inicio_intento: 18:05:25
  >>> B pide FOR UPDATE sobre fila 1 (debe esperar)
  antes   : 18:05:25
  (obtiene la fila DESPUES de que A hizo COMMIT)
  despues : 18:05:28     <-- espero 3 s hasta el COMMIT de A
  >>> B obtuvo el bloqueo SOLO despues del COMMIT de A
```

### Explicación de la IA
> "Cuando una sesión ejecuta `SELECT ... FOR UPDATE`, obtiene un **bloqueo de fila exclusivo** y lo mantiene hasta el `COMMIT`/`ROLLBACK`. Si otra sesión pide `FOR UPDATE` sobre la misma fila, no recibe un error: queda **esperando** (en `wait_event = Lock`) hasta que la primera confirme y libere el bloqueo. Por defecto no hay timeout de espera de bloqueo de fila, así que la espera puede ser indefinida si la primera nunca confirma. Es el clásico bloqueo de fila de la Semana 2."

### Verificación en el motor
La Sesión B pidió a las **18:05:25** y recién obtuvo el bloqueo a las **18:05:28**, justo después del `COMMIT` de A. La espera de 3 s es evidencia directa del bloqueo de fila.

### Conclusión
La IA **acertó**. La Sesión B quedó en espera por el bloqueo de fila `FOR UPDATE` de A y continuó solo después del `COMMIT`. No requiere cambiar nivel de aislamiento: es espera por bloqueo, y se resuelve cuando la sesión bloqueante confirma.

---

## Escenario 4 — Interbloqueo real (opcional, nota adicional)

### Cómo se reprodujo
Dos sesiones tomando filas en **orden cruzado** sobre `producto`, con sincronización para garantizar el ciclo:

- **Sesión A** (`escenario4_interbloqueo/sA.sql`): bloquea `producto 1`, espera la señal de B, e intenta bloquear `producto 2`.
- **Sesión B** (`sB.sql`): bloquea `producto 2`, avisa a A, e intenta bloquear `producto 1`.

### Qué se observó (salida real del motor)
```
SESION A (victima):
  psql:...sA.sql:21: ERROR:  se ha detectado un deadlock
  DETALLE:  El proceso 18788 espera ShareLock en transaccion 807; bloqueado por proceso 9536.
  El proceso 9536 espera ShareLock en transaccion 806; bloqueado por proceso 18788.
  CONTEXTO:  mientras se bloqueaba la tupla (0,15) de la relacion "producto"
  ROLLBACK (la transaccion de A se aborta con el error 40P01)
SESION B:
  (completo su COMMIT sin error, su transaccion sobrevive al deadlock)
```

### Explicación de la IA
> "Un **interbloqueo** ocurre cuando dos transacciones se bloquean mutuamente: A tiene la fila 1 y pide la 2 mientras B tiene la 2 y pide la 1. Ninguna puede avanzar sola, así que se forma un **ciclo en el grafo de espera**. PostgreSQL detecta el ciclo (cada 1 s por defecto, `deadlock_timeout`) y **aborta a una de las dos** como víctima con el error SQLSTATE `40P01`, liberando sus bloqueos para que la otra continúe. La prevención estándar es acceder siempre a los recursos en el **mismo orden** y mantener transacciones cortas."

### Verificación en el motor
PostgreSQL abortó a la Sesión A con el error `40P01` ("se ha detectado un deadlock"), mostrando en el DETALLE el ciclo exacto (el proceso 18788 espera a 9536, y este a su vez espera a 18788). La Sesión B continuó y confirmó.

### Conclusión
La IA **acertó**. El ciclo se formó con el orden cruzado de acceso y el motor lo resolvió abortando a una víctima (A). La solución de diseño es acceder a los recursos en un **orden consistente** (evitar el cruce) y mantener transacciones cortas.

---

## Resumen

| Escenario | Anomalía / fenómeno | Nivel en el que aparece | Nivel/mecanismo que lo resuelve | ¿La IA acertó? |
|---|---|---|---|---|
| 1 | Lectura no repetible | `READ COMMITTED` | `REPEATABLE READ` (snapshot único) / MVCC | Sí |
| 2 | Lectura fantasma | `READ COMMITTED` | `REPEATABLE READ` | Sí |
| 3 | Espera por bloqueo (`FOR UPDATE`) | cualquier nivel (bloqueo de fila) | `COMMIT` de la sesión bloqueante | Sí |
| 4 | Interbloqueo (40P01) | orden cruzado de bloqueos | orden consistente de acceso + transacciones cortas | Sí |

**Observación:** en los cuatro escenarios la explicación de la IA se confirmó exactamente en el motor real. No hubo discrepancias que documentar, pero el método aplicado fue el de la cátedra: reproducir, pedir explicación, verificar en el motor y registrar el resultado.