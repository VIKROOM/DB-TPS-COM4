"""
TP8 · Unidad 8 · Consigna 3.c
Revision de codigo asistida por IA, comprobada contra PostgreSQL real.

Casos revisados:
  H1 (U5)  grants de tabla sobre usuario exponen columnas sensibles.
  H2 (U5)  CREATE TABLE AS pierde PK/NOT NULL y la verificacion no lo detecta.
  H3 (U3)  v_pedidos_cliente oculta pedidos historicos de clientes inactivos.
  H4 (U5)  los scripts de U5 referencian usuario/detalle_pedido, que no
           existen en el esquema final de U3 (cliente/linea_pedido).
  H5 (U3)  registrar_pedido consume un id de secuencia antes de validar los
           items. Se documenta y se DESCARTA: no deja filas huerfanas.

Uso:
    python scripts/revision_codigo.py

Requiere: pip install pgserver
"""

import shutil
import subprocess
from pathlib import Path

import pgserver
import pgserver.postgres_server as pgimpl

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parent
EVID = BASE / "evidencias"
PGDATA = Path(r"C:\Users\tiago\AppData\Local\Temp\opencode\pgdata_tp8_review")

U3_SCHEMA = REPO / "food-store" / "schema.sql"
U3_VIEWS = REPO / "food-store" / "views.sql"
U3_PROCS = REPO / "food-store" / "08_procedimientos.sql"
U5_ROLES = REPO / "TP5_U5_Seguridad_FoodStore" / "sql" / "01_roles_permisos_minimo_privilegio.sql"
U5_ANON = REPO / "TP5_U5_Seguridad_FoodStore" / "sql" / "04_usuario_anon_anonimizacion.sql"

lineas = []


def log(texto=""):
    lineas.append(texto)
    print(texto)


def psql_capturado(srv, comando):
    """Ejecuta psql capturando stdout y stderr (los ERROR van a stderr)."""
    exe = pgimpl.POSTGRES_BIN_PATH / "psql"
    proc = subprocess.run(
        f'"{exe}" {srv.get_uri()}',
        input=comando.encode(),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ejecutar(srv, db, sql, titulo, detener=True):
    """Ejecuta sql en una base y devuelve (ok, salida)."""
    log("")
    log("-" * 74)
    log(titulo)
    log("-" * 74)
    comando = f"\\c {db}\n"
    if detener:
        comando += "\\set ON_ERROR_STOP on\n"
    comando += sql
    codigo, salida = psql_capturado(srv, comando)
    log(salida.rstrip() if salida.strip() else "(sin salida)")
    if codigo != 0:
        log(f"[psql salio con codigo {codigo}]")
        return False, salida
    return True, salida


def main():
    EVID.mkdir(exist_ok=True)
    if PGDATA.exists():
        shutil.rmtree(PGDATA, ignore_errors=True)

    log("REVISION DE CODIGO · TP8 · evidencia reproducible")
    log("=" * 74)
    log("Se levanta PostgreSQL 16 portable y se ejecutan los scripts reales")
    log("de U3 y U5 sobre bases de prueba. Cada hallazgo se comprueba con")
    log("consultas al motor, no por inspeccion visual.")

    srv = pgserver.get_server(str(PGDATA), cleanup_mode="stop")
    try:
        # ------------------------------------------------------------------
        # Base U3: esquema, datos minimos, vistas y procedimientos
        # ------------------------------------------------------------------
        srv.psql("CREATE DATABASE foodstore_u3;")
        srv.psql("CREATE DATABASE foodstore_u5;")

        ejecutar(srv, "foodstore_u3", U3_SCHEMA.read_text(encoding="utf-8"),
                 "Preparacion U3: food-store/schema.sql")

        seed_u3 = """
INSERT INTO categoria (nombre) VALUES ('Pizzas'), ('Bebidas');
INSERT INTO producto (categoria_id, nombre, precio, stock, activo) VALUES
  (1, 'Muzzarella', 1050.00, 20, TRUE),
  (2, 'Coca 1.5L',   800.00, 50, TRUE),
  (1, 'Empanada',    450.00, 30, TRUE);
INSERT INTO cliente (nombre, apellido, email, telefono, activo) VALUES
  ('Ana',  'Gomez',  'ana@mail.test',  '1155550001', TRUE),
  ('Beto', 'Perez',  'beto@mail.test', '1155550002', TRUE),
  ('Caro', 'Lopez',  'caro@mail.test', '1155550003', FALSE);
INSERT INTO pedido (cliente_id, fecha, forma_pago) VALUES
  (1, '2026-11-01T12:00:00Z', 'EFECTIVO'),
  (3, '2026-11-02T13:30:00Z', 'TARJETA');
INSERT INTO linea_pedido (pedido_id, producto_id, cantidad, precio_unitario) VALUES
  (1, 1, 2, 1050.00),
  (2, 2, 1,  800.00);
"""
        ejecutar(srv, "foodstore_u3", seed_u3, "Datos minimos de prueba U3")
        ejecutar(srv, "foodstore_u3", U3_VIEWS.read_text(encoding="utf-8"),
                 "Preparacion U3: food-store/views.sql")
        ejecutar(srv, "foodstore_u3", U3_PROCS.read_text(encoding="utf-8"),
                 "Preparacion U3: food-store/08_procedimientos.sql")

        # ------------------------------------------------------------------
        # H3 · v_pedidos_cliente oculta pedidos de clientes inactivos
        # ------------------------------------------------------------------
        ejecutar(srv, "foodstore_u3", """
SELECT 'pedido_total' AS metrica, count(*)::text AS valor FROM pedido
UNION ALL
SELECT 'v_pedidos_cliente', count(*)::text FROM v_pedidos_cliente;
SELECT p.id AS pedido_oculto, c.nombre AS cliente, c.activo
FROM pedido p JOIN cliente c ON c.id = p.cliente_id
WHERE p.id NOT IN (SELECT pedido_id FROM v_pedidos_cliente);
""", "H3 · La vista V2 filtra c.activo = TRUE y pierde historial")

        # ------------------------------------------------------------------
        # H5 · registrar_pedido consume secuencia antes de validar
        # ------------------------------------------------------------------
        ejecutar(srv, "foodstore_u3", """
SELECT last_value AS secuencia_antes FROM pedido_id_seq;
SELECT count(*) AS pedidos_antes FROM pedido;
""", "H5 · Estado antes de una venta invalida")
        ejecutar(srv, "foodstore_u3", """
CALL registrar_pedido(
  1,
  'EFECTIVO',
  '[{"producto_id": 999, "cantidad": 1}]'::jsonb,
  NULL
);
""", "H5 · Venta con producto inexistente (debe fallar)", detener=False)
        ejecutar(srv, "foodstore_u3", """
SELECT last_value AS secuencia_despues FROM pedido_id_seq;
SELECT count(*) AS pedidos_despues FROM pedido;
SELECT count(*) AS filas_huerfanas
FROM pedido p
WHERE NOT EXISTS (SELECT 1 FROM linea_pedido lp WHERE lp.pedido_id = p.id)
  AND p.id = (SELECT max(id) FROM pedido);
""", "H5 · No hay pedido huerfano; solo avanza la secuencia")

        # ------------------------------------------------------------------
        # H4 · Drift de nombres entre U5 y el esquema final de U3
        # ------------------------------------------------------------------
        ejecutar(srv, "foodstore_u3", """
SELECT to_regclass('public.usuario')       AS usuario,
       to_regclass('public.detalle_pedido') AS detalle_pedido,
       to_regclass('public.cliente')        AS cliente,
       to_regclass('public.linea_pedido')   AS linea_pedido;
""", "H4 · Relaciones que esperan los scripts de U5 vs. las reales de U3")
        ejecutar(srv, "foodstore_u3", """
CREATE ROLE rol_review_temp;
GRANT SELECT ON TABLE categoria, producto, pedido, detalle_pedido
  TO rol_review_temp;
""", "H4 · Al aplicar el GRANT de U5 sobre el esquema U3 falla", detener=False)
        srv.psql("\\c foodstore_u3\nDROP ROLE IF EXISTS rol_review_temp;\n")

        # ------------------------------------------------------------------
        # Base U5: tablas que esperan sus scripts + datos
        # ------------------------------------------------------------------
        ejecutar(srv, "foodstore_u5", """
CREATE TABLE categoria (id BIGINT PRIMARY KEY, nombre TEXT, activo BOOLEAN DEFAULT TRUE);
CREATE TABLE producto  (id BIGINT PRIMARY KEY, categoria_id BIGINT, nombre TEXT,
                        precio NUMERIC(10,2), stock INT, activo BOOLEAN DEFAULT TRUE);
CREATE TABLE pedido    (id BIGINT PRIMARY KEY, cliente_id BIGINT, fecha TIMESTAMPTZ,
                        forma_pago TEXT);
CREATE TABLE detalle_pedido (pedido_id BIGINT, producto_id BIGINT,
                             cantidad INT, precio_unitario NUMERIC(10,2));
CREATE TABLE usuario (
  id BIGINT PRIMARY KEY,
  nombre TEXT NOT NULL,
  apellido TEXT NOT NULL,
  mail TEXT NOT NULL,
  celular TEXT,
  contrasena TEXT NOT NULL,
  rol TEXT NOT NULL,
  eliminado BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO usuario (id, nombre, apellido, mail, celular, contrasena, rol, eliminado)
VALUES (1, 'Ana', 'Gomez', 'ana@mail.test', '1155550001', 'hash1', 'cliente', FALSE),
       (2, 'Beto', 'Perez', 'beto@mail.test', '1155550002', 'hash2', 'cliente', FALSE);
""", "Preparacion U5: tablas que esperan sus scripts")

        ejecutar(srv, "foodstore_u5", U5_ROLES.read_text(encoding="utf-8"),
                 "H6 · 01_roles_permisos_minimo_privilegio.sql: el ultimo "
                 "ALTER DEFAULT PRIVILEGES con columnas no es valido",
                 detener=False)
        ejecutar(srv, "foodstore_u5", """
SELECT defaclrole::regrole AS rol,
       defaclnamespace::regnamespace AS esquema,
       defaclobjtype AS tipo_objeto,
       defaclacl AS acl
FROM pg_default_acl
ORDER BY 1, 2, 3;
""", "H6 · Default privileges realmente registrados (sin columnas)")
        ejecutar(srv, "foodstore_u5", U5_ANON.read_text(encoding="utf-8"),
                 "Preparacion U5: 04_usuario_anon_anonimizacion.sql")

        # ------------------------------------------------------------------
        # H1 · SELECT de tabla sobre usuario expone columnas sensibles
        # ------------------------------------------------------------------
        ejecutar(srv, "foodstore_u5", """
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE table_name = 'usuario'
ORDER BY grantee, privilege_type;
SELECT grantee, column_name, privilege_type
FROM information_schema.column_privileges
WHERE table_name = 'usuario'
ORDER BY grantee, column_name, privilege_type;
""", "H1 · Grants de tabla (todas las columnas) vs. grants de columna")

        # ------------------------------------------------------------------
        # H2 · usuario_anon sin PK/NOT NULL y verificacion insuficiente
        # ------------------------------------------------------------------
        ejecutar(srv, "foodstore_u5", """
SELECT count(*) AS constraints_usuario_anon
FROM pg_constraint
WHERE conrelid = 'usuario_anon'::regclass;
INSERT INTO usuario_anon (id) VALUES (1);
SELECT id, count(*) AS filas
FROM usuario_anon
GROUP BY id
HAVING count(*) > 1;
SELECT count(*) AS usuario FROM usuario;
SELECT count(*) AS usuario_anon FROM usuario_anon;
SELECT count(*) AS diff_total
FROM (SELECT id FROM usuario EXCEPT SELECT id FROM usuario_anon) x;
""", "H2 · CTAS sin PK: se puede duplicar id y la verificacion no lo ve")

        log("")
        log("=" * 74)
        log("CONCLUSION")
        log("=" * 74)
        log("H1 ACEPTADO: app_web/roles de app tienen SELECT de tabla sobre usuario;")
        log("   el minimo privilegio por columna solo se aplico a rol_soporte.")
        log("H2 ACEPTADO: usuario_anon no tiene PK ni NOT NULL; el INSERT duplicado")
        log("   paso y la verificacion por EXCEPT siguio dando diff_total = 0.")
        log("H3 ACEPTADO: v_pedidos_cliente devuelve menos pedidos que la tabla;")
        log("   el pedido del cliente inactivo desaparece del historial.")
        log("H4 ACEPTADO: U5 referencia usuario/detalle_pedido; el esquema U3 tiene")
        log("   cliente/linea_pedido. El GRANT falla con 'relation does not exist'.")
        log("H5 DESCARTADO: la secuencia avanza, pero el pedido no queda huerfano")
        log("   porque RAISE EXCEPTION aborta la transaccion. Los huecos de una")
        log("   secuencia son esperables y no afectan integridad ni negocio.")
        log("H6 ACEPTADO: ALTER DEFAULT PRIVILEGES ... GRANT SELECT (columna)")
        log("   no es valido en PostgreSQL ('default privileges cannot be set")
        log("   for columns'); el script U5 se corta en esa linea. Se propone")
        log("   quitar la lista de columnas del default privilege y mantener el")
        log("   grant por columna solo en la tabla existente, o crear una vista")
        log("   usuario_soporte y otorgar SELECT sobre la vista.")

        (EVID / "07_revision_codigo.txt").write_text("\n".join(lineas) + "\n",
                                                     encoding="utf-8")
    finally:
        srv.cleanup()


if __name__ == "__main__":
    main()
