# Kiro · Tasks — TP Unidad 8 (Food Store en la feria)

## Tareas de implementación

| # | Tarea | Archivo | Verificación |
|---|---|---|---|
| 1 | Definir qué datos viajan a la tablet y por qué | `docs/informe.pdf` (1.a) | Tabla de campos y fuente de verdad |
| 2 | Crear las cuatro tablas SQLite con FK, CHECK y STRICT | `movil/schema_sqlite.sql` | Ejecutar desde cero; `PRAGMA foreign_keys = ON`; `sqlite_master` |
| 3 | Probar borrador con COMMIT, ROLLBACK, catálogo offline y C7 | `movil/pruebas_sqlite.sql` | `evidencias/02_pruebas_sqlite.txt` |
| 4 | Crear la vista de instantánea y exportarla a CSV | `servidor/01_v_snapshot_movil.sql`, `servidor/02_exportar_snapshot.sql` | `evidencias/01_seed_y_vista.txt`, `evidencias/03_snapshot_export.txt` |
| 5 | Importar el CSV y refrescar `producto_cache` con UPSERT | `movil/importar_snapshot.sql`, `movil/servidor_snapshot.csv` | `evidencias/03_snapshot_export.txt` |
| 6 | Implementar el semáforo con prioridad rojo > amarillo > verde | `movil/semaforo.sql` | `evidencias/04_semaforo_casos.txt` |
| 7 | Reproducir los casos C2 a C6 | `scripts/simular_tp8.py` | `evidencias/04_semaforo_casos.txt` |
| 8 | Comprobar que PostgreSQL no cambió | `servidor/03_verificacion_postgres.sql` | `evidencias/05_verificacion_postgres_diff.txt` |
| 9 | Revisar los scripts de U3 y U5 con IA y comprobar hallazgos | `scripts/revision_codigo.py` | `evidencias/07_revision_codigo.txt` |
| 10 | Documentar el mapa de los tres motores y el mantenimiento | `docs/informe.pdf` (3.a y 3.b) | Tabla de motores y respuestas del plan |
| 11 | Registrar el uso de IA y la DUIA | `docs/bitacora_ia.md`, `docs/DUIA.md` | Al menos tres entradas y verificación humana |
| 12 | Generar el PDF del informe (≤ 6 páginas) | `docs/generar_informe.py`, `docs/informe.pdf` | Contar páginas con `pypdf` |
| 13 | Documentar el orden de reproducción desde cero | `README.md` | Seguir los pasos en una carpeta limpia |

## Orden sugerido

1. Tareas 2, 3 y 4–5: base de la tablet e instantánea.
2. Tareas 6–8: semáforo y casos.
3. Tareas 9–11: revisión, bitácora y DUIA.
4. Tareas 12–13: informe y README.

## Criterio de terminado

- Todos los scripts se ejecutan sin errores no intencionales.
- Los casos C2 a C6 coinciden con el resultado esperado.
- Los invariantes del servidor no cambian.
- El PDF tiene como máximo 6 páginas.
- El README permite recrear la entrega desde cero.
