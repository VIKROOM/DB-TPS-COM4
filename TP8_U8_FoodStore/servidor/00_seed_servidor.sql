-- ============================================================================
-- TP8 · Unidad 8 · Consigna 2.a (preparacion del servidor de PRUEBAS)
-- Copia controlada de Food Store en PostgreSQL, con datos inventados.
--
-- Este script NO es la base real: es una copia de laboratorio para simular
-- la sincronizacion. Se puede volver a ejecutar desde cero.
-- ============================================================================

DROP TABLE IF EXISTS linea_pedido CASCADE;
DROP TABLE IF EXISTS pedido        CASCADE;
DROP TABLE IF EXISTS producto      CASCADE;
DROP TABLE IF EXISTS cliente       CASCADE;
DROP TABLE IF EXISTS categoria     CASCADE;
DROP TYPE  IF EXISTS forma_pago    CASCADE;

CREATE TYPE forma_pago AS ENUM ('EFECTIVO', 'TARJETA', 'TRANSFERENCIA');

CREATE TABLE categoria (
    id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE producto (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    categoria_id BIGINT NOT NULL REFERENCES categoria(id) ON DELETE RESTRICT,
    nombre       VARCHAR(120) NOT NULL,
    precio       NUMERIC(10,2) NOT NULL CHECK (precio >= 0),
    stock        INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    activo       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE cliente (
    id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL,
    email  VARCHAR(160) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE pedido (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente_id BIGINT NOT NULL REFERENCES cliente(id) ON DELETE RESTRICT,
    fecha      TIMESTAMPTZ NOT NULL DEFAULT now(),
    forma_pago forma_pago NOT NULL
);

CREATE TABLE linea_pedido (
    pedido_id       BIGINT NOT NULL REFERENCES pedido(id) ON DELETE CASCADE,
    producto_id     BIGINT NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario >= 0),
    PRIMARY KEY (pedido_id, producto_id)
);

-- ----------------------------------------------------------------------------
-- Datos inventados (sin mails ni datos personales reales).
-- ----------------------------------------------------------------------------
INSERT INTO categoria (nombre) VALUES
    ('Pizzas'),
    ('Bebidas'),
    ('Postres');

INSERT INTO producto (categoria_id, nombre, precio, stock, activo) VALUES
    (1, 'Muzzarella',        1050.00, 20, TRUE),
    (2, 'Coca 1.5L',          800.00, 50, TRUE),
    (1, 'Empanada de carne',  450.00, 30, TRUE),
    (2, 'Agua 500ml',         300.00, 10, TRUE),
    (3, 'Flan casero',        600.00,  5, TRUE);

INSERT INTO cliente (nombre, email, activo) VALUES
    ('Cliente Demo 1', 'demo1@example.test', TRUE),
    ('Cliente Demo 2', 'demo2@example.test', TRUE),
    ('Cliente Demo 3', 'demo3@example.test', TRUE);

INSERT INTO pedido (cliente_id, fecha, forma_pago) VALUES
    (1, '2026-11-01T12:00:00Z', 'EFECTIVO'),
    (2, '2026-11-02T13:30:00Z', 'TARJETA'),
    (3, '2026-11-03T20:15:00Z', 'TRANSFERENCIA');

INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario) VALUES
    (1, 1, 2, 1050.00),
    (1, 2, 1,  800.00),
    (2, 3, 3,  450.00),
    (3, 4, 1,  300.00),
    (3, 5, 2,  600.00);

-- Verificacion del seed.
SELECT 'seed_producto' AS tabla, count(*) AS filas FROM producto
UNION ALL SELECT 'seed_pedido', count(*) FROM pedido
UNION ALL SELECT 'seed_linea_pedido', count(*) FROM linea_pedido;
