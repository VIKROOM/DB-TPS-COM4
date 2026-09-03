-- ============================================================================
-- Food Store - Proyecto integrador, Semana 1
-- TP N.1: DDL del esquema definitivo (Partes 2 y 3 conciliadas)
-- Motor: PostgreSQL 17 | Cliente: DBeaver
-- Ejecutar sobre una base vacia:  psql -U postgres -d foodstore -f schema.sql
-- ============================================================================

-- Dominio cerrado para la forma de pago del pedido (regla de negocio fija).

CREATE TYPE forma_pago AS ENUM ('EFECTIVO', 'TARJETA', 'TRANSFERENCIA');

-- ----------------------------------------------------------------------------
-- CATEGORIA
-- R7: baja logica, no se elimina fisicamente.
-- ----------------------------------------------------------------------------
CREATE TABLE categoria (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre     VARCHAR(80)  NOT NULL UNIQUE,
    activo     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- PRODUCTO
-- R1: todo producto pertenece exactamente a una categoria (FK NOT NULL).
-- R5: precio y stock no negativos (CHECK).
-- R7: baja logica con activo.
-- ----------------------------------------------------------------------------
CREATE TABLE producto (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    categoria_id BIGINT       NOT NULL REFERENCES categoria(id) ON DELETE RESTRICT,
    nombre       VARCHAR(120) NOT NULL,
    descripcion  TEXT,
    precio       NUMERIC(10,2) NOT NULL CHECK (precio >= 0),
    stock        INTEGER      NOT NULL DEFAULT 0 CHECK (stock >= 0),
    activo       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    -- El nombre del producto es unico dentro de su categoria (clave candidata).
    UNIQUE (categoria_id, nombre)
);

-- ----------------------------------------------------------------------------
-- CLIENTE
-- R6: el email identifica de forma unica al cliente (clave candidata -> UNIQUE).
-- ----------------------------------------------------------------------------
CREATE TABLE cliente (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre     VARCHAR(80)  NOT NULL,
    apellido   VARCHAR(80)  NOT NULL,
    email      VARCHAR(160) NOT NULL UNIQUE,
    telefono   VARCHAR(30),
    activo     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- PEDIDO
-- R2: todo pedido pertenece exactamente a un cliente registrado (FK NOT NULL).
-- ON DELETE RESTRICT: no se borra un cliente si tiene pedidos, para conservar
-- el historial de ventas (misma filosofia que R7).
-- ----------------------------------------------------------------------------
CREATE TABLE pedido (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente_id  BIGINT      NOT NULL REFERENCES cliente(id) ON DELETE RESTRICT,
    fecha       TIMESTAMPTZ NOT NULL DEFAULT now(),
    forma_pago  forma_pago  NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- LINEA_PEDIDO (tabla intermedia de la relacion N:M pedido-producto)
-- R3: un pedido incluye varios productos y un producto aparece en muchos pedidos.
-- R4: cantidad y precio_unitario viven aqui; el precio queda congelado al
--     momento de la venta aunque el precio de lista del producto cambie.
-- PK compuesta (pedido_id, producto_id): garantiza que un producto no se
-- repita en dos lineas del mismo pedido sin necesitar constraints extra.
-- ON DELETE CASCADE en pedido: si algun dia se elimina un pedido, sus lineas
-- se van con el (no tienen sentido sueltas). En producto va RESTRICT porque
-- las lineas son el historial facturado que R7 busca preservar.
-- ----------------------------------------------------------------------------
CREATE TABLE linea_pedido (
    pedido_id       BIGINT        NOT NULL REFERENCES pedido(id)   ON DELETE CASCADE,
    producto_id     BIGINT        NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
    cantidad        INTEGER       NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario >= 0),
    PRIMARY KEY (pedido_id, producto_id)
);

-- ----------------------------------------------------------------------------
-- INDICES
-- ----------------------------------------------------------------------------

-- Acelera "listar todos los pedidos de un cliente" (filtro por cliente_id),
-- consulta tipica desde la pantalla del cliente.
CREATE INDEX idx_pedido_cliente ON pedido (cliente_id);

-- Acelera "listar los productos vigentes de una categoria" (JOIN/FILTER por
-- categoria_id), consulta principal del menu/cartilla.
CREATE INDEX idx_producto_categoria ON producto (categoria_id);

-- Acelera reportes de ventas por rango de fechas (BETWEEN sobre pedido.fecha).
CREATE INDEX idx_pedido_fecha ON pedido (fecha);
