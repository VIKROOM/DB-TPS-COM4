-- ============================================================================
-- TP8 · Unidad 8 · Consigna 1.b
-- Base de la tablet Food Store (SQLite 3.37+)
--
-- Regla de oro del TP: el movil propone, el servidor dispone.
-- Esta base NO decide precio, stock ni ventas: solo guarda un cache de
-- catalogo y borradores locales que luego se simulan contra el servidor.
--
-- Ejecutar con:  sqlite3 foodstore_movil.db < schema_sqlite.sql
-- ============================================================================

PRAGMA foreign_keys = ON;

-- Se recrea desde cero. El orden respeta las claves foraneas.
DROP TABLE IF EXISTS cola_sync;
DROP TABLE IF EXISTS item_borrador;
DROP TABLE IF EXISTS pedido_borrador;
DROP TABLE IF EXISTS producto_cache;

-- ----------------------------------------------------------------------------
-- producto_cache: copia de solo lectura del catalogo del servidor.
-- precio_centavos: entero, nunca negativo (se evita el punto flotante).
-- disponible / eliminado: banderas 0/1. "eliminado" es la lapida de la baja
-- logica del servidor; la fila se conserva para no romper borradores viejos.
-- ----------------------------------------------------------------------------
CREATE TABLE producto_cache (
    id              INTEGER PRIMARY KEY,
    nombre          TEXT    NOT NULL,
    precio_centavos INTEGER NOT NULL CHECK (precio_centavos >= 0),
    stock_visto     INTEGER NOT NULL CHECK (stock_visto >= 0),
    disponible      INTEGER NOT NULL CHECK (disponible IN (0, 1)),
    eliminado       INTEGER NOT NULL DEFAULT 0 CHECK (eliminado IN (0, 1)),
    fecha_copia     TEXT    NOT NULL
) STRICT;

-- ----------------------------------------------------------------------------
-- pedido_borrador: cabecera de un borrador local, identificada por UUID.
-- No hay FK al servidor: el borrador nace y vive en la tablet.
-- usuario es un identificador inventado de vendedor, sin datos personales.
-- ----------------------------------------------------------------------------
CREATE TABLE pedido_borrador (
    id_local   TEXT PRIMARY KEY,
    usuario    TEXT NOT NULL,
    forma_pago TEXT NOT NULL CHECK (forma_pago IN ('EFECTIVO', 'TARJETA', 'TRANSFERENCIA')),
    fecha      TEXT NOT NULL
) STRICT;

-- ----------------------------------------------------------------------------
-- item_borrador: lineas del borrador.
-- FK a producto_cache para que no se pueda cargar un producto inexistente.
-- cantidad > 0 y precio visto no negativo.
-- ----------------------------------------------------------------------------
CREATE TABLE item_borrador (
    id_local              TEXT    NOT NULL REFERENCES pedido_borrador(id_local) ON DELETE CASCADE,
    producto_id           INTEGER NOT NULL REFERENCES producto_cache(id) ON DELETE RESTRICT,
    cantidad              INTEGER NOT NULL CHECK (cantidad > 0),
    precio_centavos_visto INTEGER NOT NULL CHECK (precio_centavos_visto >= 0),
    PRIMARY KEY (id_local, producto_id)
) STRICT;

-- ----------------------------------------------------------------------------
-- cola_sync: solicitudes de sincronizacion pendientes de simulacion.
-- solicitud_uuid es la clave de idempotencia local: reenviar el mismo UUID
-- falla por clave primaria (caso C6).
-- Solo el semaforo cambia el estado de las solicitudes PENDIENTE.
-- ----------------------------------------------------------------------------
CREATE TABLE cola_sync (
    solicitud_uuid TEXT PRIMARY KEY,
    id_local       TEXT NOT NULL REFERENCES pedido_borrador(id_local) ON DELETE CASCADE,
    estado         TEXT NOT NULL DEFAULT 'PENDIENTE'
                   CHECK (estado IN ('PENDIENTE', 'CONFLICTO', 'RECHAZADO', 'SIMULADO_APROBADO')),
    motivo         TEXT,
    creado_en      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    evaluado_en    TEXT
) STRICT;

-- ----------------------------------------------------------------------------
-- Verificacion de que las cuatro tablas quedaron creadas.
-- ----------------------------------------------------------------------------
SELECT name AS tabla
FROM sqlite_master
WHERE type = 'table' AND name IN ('producto_cache', 'pedido_borrador', 'item_borrador', 'cola_sync')
ORDER BY name;
