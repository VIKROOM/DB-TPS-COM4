-- ============================================================================
-- TP8 · Unidad 8 · Consigna 2.a
-- Exportacion de la instantanea a CSV.
--
-- Ejecutar desde psql (PostgreSQL de PRUEBAS), con una ruta absoluta:
--
--   \copy (SELECT * FROM v_snapshot_movil) TO 'servidor_snapshot.csv' CSV HEADER
--
-- El script reproducible (scripts/simular_tp8.py) hace exactamente esto y
-- deja el CSV en movil/servidor_snapshot.csv. En el CSV, psql exporta los
-- booleanos como 't' / 'f'.
-- ============================================================================

\copy (SELECT * FROM v_snapshot_movil) TO 'servidor_snapshot.csv' CSV HEADER
