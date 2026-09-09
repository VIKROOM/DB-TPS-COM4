-- TP4 Parte 1 - Cambios propuestos por IA (revisados linea a linea) - foodstore_tp3

-- QA: el plan hacia un Nested Loop pero pagaba un Parallel Seq Scan sobre
--     linea_pedido (Rows Removed by Filter: 199997 por worker). Un indice
--     sobre producto_id convierte ese scan en un Index Scan puntual de las
--     lineas de ESE producto. No cambia el algoritmo de join (sigue Nested
--     Loop) pero elimina el barrido de las 600.000 lineas.
CREATE INDEX idx_linea_pedido_producto ON linea_pedido (producto_id);

-- QB: el plan pagaba un Merge Join + GroupAggregate + Sort sobre las 600.002
--     lineas y las 200.001 filas de pedido para quedarse con 100. La
--     reescritura selecciona primero los 100 pedidos mas recientes (usando
--     idx_pedido_fecha) y solo agrega las lineas de esos 100 (Nested Loop por
--     la PK). No se crea indice nuevo: se reutilizan idx_pedido_fecha y
--     linea_pedido_pkey.