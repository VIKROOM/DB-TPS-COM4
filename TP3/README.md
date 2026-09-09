# TP3 — Optimización asistida por IA sobre Food Store

**Base de Datos II · Unidad 2 · Semana 3** — filtros, planes de ejecución e
índices. Proyecto integrador Food Store.

- **Motor:** PostgreSQL 17.10 · **Cliente:** psql
- **Base de trabajo:** `foodstore_tp3` (copia según protocolo de seguridad;
  producción `foodstore` intacta)
- **Volumen de la base masiva:** 50.003 productos · 20.003 usuarios · 200.001
  pedidos · 500.365 líneas de detalle · 6 categorías
- **Herramienta de IA:** OpenCode (la IA propone, el estudiante verifica)

## Estructura de la entrega

```
TP3/
├── README.md                        ← este índice
├── DUIA.md                          ← Declaración de Uso de IA (todas las partes)
├── parte1_carga_masiva/
│   ├── Genera_registros.sql         ← script de carga provisto por la cátedra (sin modificar)
│   ├── verificacion_carga.sql       ← verificación de la carga (restricciones + distribución)
│   ├── correccion_distribucion.sql  ← corrección del defecto de distribución detectado
│   ├── informe_carga.md             ← protocolo, lectura línea a línea, defecto, evidencia
│   ├── salida_carga.txt             ← ejecución real con \timing
│   ├── salida_correccion.txt        ← ejecución real de la corrección
│   ├── salida_verificacion_inicial.txt ← verificación post-carga (detecta el defecto)
│   └── salida_verificacion_final.txt   ← verificación post-corrección (todo ✓)
├── parte2_laboratorio/
│   ├── consultas.sql                ← C1, C2, C3 (variantes propias sobre el modelo)
│   ├── indices.sql                  ← I1, I2, I3 aceptados + descartes documentados
│   ├── tabla_comparativa.md         ← tabla 2.2 de la consigna + análisis honesto
│   └── planes/                      ← EXPLAIN (ANALYZE, BUFFERS) reales
│       ├── C1_antes.txt  C1_despues.txt  C1_despues_include.txt (variante descartada)
│       ├── C2_antes.txt  C2_despues.txt
│       └── C3_antes.txt  C3_despues.txt
├── parte3_lectura_critica/
│   ├── plan_analizado.txt           ← plan real (C2 después) dado a la IA sin contexto
│   ├── explicacion_ia.md            ← explicación generada por la IA, textual
│   └── lectura_critica.md           ← contraste frase por frase (13 afirmaciones, 6 ❌)
├── parte4_specs/
│   ├── specs.md                     ← las 2 especificaciones precisas (resumen + subconsulta)
│   ├── consulta_A_generada_ia.sql   ← versión IA (LEFT JOIN + GROUP BY)
│   ├── consulta_A_alternativa_propia.sql ← versión propia (subconsulta escalar)
│   ├── consulta_B_generada_ia.sql   ← versión IA (subconsulta IN)
│   ├── consulta_B_alternativa_propia.sql ← versión propia (EXISTS correlacionado)
│   ├── verificacion_equivalencia.sql ← EXCEPT ambos sentidos + conteos + caso borde
│   └── salida_verificacion.txt      ← ejecución real: 0 filas en todos los EXCEPT
└── parte5_competencia/
    ├── consulta_comun.sql           ← la consulta fijada por la cátedra
    ├── registro_competencia.md      ← estrategia, tiempos reales, bitácora de descartes
    └── planes/
        ├── competencia_antes.txt        ← 13.580 ms (sin índice)
        ├── competencia_despues.txt      ← 4.941 ms (I1)
        └── competencia_despues_include.txt ← variante INCLUDE descartada (4.798 ms, ruido)
```

## Entregables de la consigna → dónde están

| Entregable pedido | Archivo |
|---|---|
| Script de carga masiva (leído, probado y ejecutado bajo protocolo) | `parte1_carga_masiva/` (script provisto + informe + salidas reales) |
| Tabla comparativa Parte 2 con planes antes/después | `parte2_laboratorio/tabla_comparativa.md` + `planes/` |
| Tabla de lectura crítica Parte 3 | `parte3_lectura_critica/lectura_critica.md` |
| Dos consultas Parte 4 (spec + SQL generado + verificación de equivalencia) | `parte4_specs/` |
| Registro de la competencia Parte 5 | `parte5_competencia/registro_competencia.md` |
| DUIA completa | `DUIA.md` |
| Defensa oral | cada decisión está justificada en su documento; resumen de puntos a defender en `DUIA.md` ("Verificación humana") |

## Resultados principales (medidos en real, segunda corrida con caché caliente)

| Consulta | Antes | Después | Mejora | Cambio |
|---|---|---|---|---|
| C1 productos por categoría + orden | 10.486 ms | 7.726 ms | 1.36× | I1 `(categoria_id, eliminado, precio)` |
| C2 historial de pedidos por usuario | 36.934 ms | 0.164 ms | **225×** | I2 `(usuario_id, eliminado, fecha)` |
| C3 top 10 productos vendidos | 150.645 ms | 62.328 ms | 2.42× | I3 `(producto_id, cantidad)` cubriente |
| Competencia (Parte 5) | 13.580 ms | 4.941 ms | 2.75× | I1 |

## Reproducción

```powershell
# entorno usado (Windows / PowerShell)
$env:PGPASSWORD = '<contraseña de postgres>'
psql -U postgres -h localhost -d postgres -c "CREATE DATABASE foodstore_tp3 TEMPLATE foodstore;"

# Parte 1 (el script trae BEGIN/COMMIT y ANALYZE propios)
psql -U postgres -h localhost -d foodstore_tp3 -X -v ON_ERROR_STOP=1 -f parte1_carga_masiva/Genera_registros.sql
psql -U postgres -h localhost -d foodstore_tp3 -X -f parte1_carga_masiva/verificacion_carga.sql
psql -U postgres -h localhost -d foodstore_tp3 -X -f parte1_carga_masiva/correccion_distribucion.sql
psql -U postgres -h localhost -d foodstore_tp3 -X -c "VACUUM ANALYZE;"

# Parte 2: medir "antes" con consultas.sql, aplicar indices.sql, medir "después"
# Parte 4: psql ... -f parte4_specs/verificacion_equivalencia.sql
```

> Los `.txt` de planes y salidas son evidencia capturada directamente de psql
> sobre la base masiva real (no son simulaciones).
