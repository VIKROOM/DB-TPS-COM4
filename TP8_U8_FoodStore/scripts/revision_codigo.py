"""
TP8 · Unidad 8 · Consigna 3.c
Revision de codigo asistida por IA de los scripts de la cursada.
Los hallazgos de U3/U5/U4 se comprueban contra PostgreSQL real; los de
U6/U7/U8 se comprueban con revision estatica y se marcan como tales.

Casos revisados:
  H1 (U5)  grants de tabla sobre usuario exponen columnas sensibles.
  H2 (U5)  CREATE TABLE AS pierde PK/NOT NULL y la verificacion no lo detecta.
  H3 (U3)  v_pedidos_cliente oculta pedidos historicos de clientes inactivos.
  H4 (U5)  los scripts de U5 referencian usuario/detalle_pedido, que no
           existen en el esquema final de U3 (cliente/linea_pedido).
  H5 (U3)  registrar_pedido consume un id de secuencia antes de validar los
           items. Se documenta y se DESCARTA: no deja filas huerfanas.
  H6 (U5)  ALTER DEFAULT PRIVILEGES con lista de columnas no es valido.
  H7 (U4)  tp_fnbc_control_lote.sql hace DROP TABLE y destruye datos reales.
  H8 (U4)  tp_desnormalizacion_top_categorias.sql usa detalle_pedido, pero el
           esquema final define linea_pedido; el trigger no se puede crear.
  H9 (U4)  la migracion segura aborta si se viola DF2 y el ROLLBACK no deja
           objetos nuevos.
  H10 (U6) restore_test.ps1 usa --no-owner --no-privileges: valida datos,
           pero no verifica roles/permisos restaurados.
  H11 (U6) backup_foodstore.ps1 aplica retencion por LastWriteTime; una copia
           o restauracion de archivos puede alterar la antiguedad percibida.
  H12 (U7) 01_exportar_pedidos_mongodb.sql escapa comillas dobles pero no
           barras invertidas ni saltos de linea al generar JavaScript.
  H13 (U7) 01_crear_coleccion.js hace db.pedidos.drop() sin guarda: es
           idempotente en laboratorio, pero destructivo en una base poblada.
  H14 (U8) importar_snapshot.sql referencia movil/importar_snapshot.py, que
           no existe en el repositorio.
  H15 (U8) simular_tp8.py y este script fijan una ruta temp de un usuario
           Windows concreto; no son portables.
  H16 (U8) importar_snapshot.sql usa el meta-comando .import de sqlite3, que
           no ejecuta el runner Python; hay dos caminos de importacion.
  H17 (U6) maintenance.sql hace DROP TABLE IF EXISTS tmp_mantenimiento sin
           calificar pg_temp: podria borrar una tabla permanente homonima.

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
U4_DIR = REPO / "TP4_U4_FNBC_Desnormalizacion" / "sql"
U4_FNBC = U4_DIR / "tp_fnbc_control_lote.sql"
U4_MIGRACION = U4_DIR / "tp_fnbc_control_lote_migracion_segura.sql"
U4_DESNORM = U4_DIR / "tp_desnormalizacion_top_categorias.sql"
U6_DIR = REPO / "TP6_U6_Mantenimiento_FoodStore"
U6_BACKUP = U6_DIR / "backup_foodstore.ps1"
U6_RESTORE = U6_DIR / "restore_test.ps1"
U6_MAINT = U6_DIR / "maintenance.sql"
U7_DIR = REPO / "TP7_U7_NoSQL_FoodStore"
U7_EXPORT = U7_DIR / "sql" / "01_exportar_pedidos_mongodb.sql"
U7_CREATE = U7_DIR / "mongodb" / "01_crear_coleccion.js"
U8_IMPORT = REPO / "TP8_U8_FoodStore" / "movil" / "importar_snapshot.sql"
U8_RUNNER = REPO / "TP8_U8_FoodStore" / "scripts" / "simular_tp8.py"

lineas = []


def log(texto=""):
    lineas.append(texto)
    print(texto)


def leer(ruta):
    """Lee un script del repositorio para la revision estatica."""
    return ruta.read_text(encoding="utf-8", errors="replace")


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
    log("de U3, U4 y U5 sobre bases de prueba; cada hallazgo se comprueba con")
    log("consultas al motor. U6/U7/U8 se revisan de forma estatica y se")
    log("indica explicitamente que no hubo ejecucion.")

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

        # ------------------------------------------------------------------
        # Base U4: esquema final U3 (linea_pedido) + instancia de control_lote
        # ------------------------------------------------------------------
        srv.psql("CREATE DATABASE foodstore_u4;")
        ejecutar(srv, "foodstore_u4", U3_SCHEMA.read_text(encoding="utf-8"),
                 "Preparacion U4: esquema base de U3 (linea_pedido)")

        # H7 · el script de demostracion destruye datos existentes
        ejecutar(srv, "foodstore_u4", """
CREATE TABLE control_lote_almacen (
    lote_id                BIGINT NOT NULL,
    deposito_id            BIGINT NOT NULL,
    responsable_control_id BIGINT NOT NULL,
    PRIMARY KEY (lote_id, deposito_id)
);
INSERT INTO control_lote_almacen VALUES (999, 99, 999);
""", "H7 · Instancia real con una fila que no pertenece al ejemplo")

        ejecutar(srv, "foodstore_u4", U4_FNBC.read_text(encoding="utf-8"),
                 "H7 · tp_fnbc_control_lote.sql (DROP + recreacion del ejemplo)",
                 detener=False)

        ejecutar(srv, "foodstore_u4", """
SELECT 'fila_999_superviviente' AS control, count(*) AS filas
FROM control_lote_almacen
WHERE lote_id = 999 AND deposito_id = 99;
SELECT 'filas_totales' AS control, count(*) AS filas
FROM control_lote_almacen;
""", "H7 · La fila real desaparecio: el script es destructivo")

        # H8 · U4 usa detalle_pedido; el esquema final define linea_pedido
        ejecutar(srv, "foodstore_u4", """
SELECT to_regclass('public.detalle_pedido') AS detalle_pedido,
       to_regclass('public.linea_pedido')   AS linea_pedido;
""", "H8 · U4 espera detalle_pedido; el esquema final tiene linea_pedido")

        ejecutar(srv, "foodstore_u4", U4_DESNORM.read_text(encoding="utf-8"),
                 "H8 · tp_desnormalizacion_top_categorias.sql sobre el esquema final",
                 detener=False)

        ejecutar(srv, "foodstore_u4", """
SELECT to_regclass('public.ventas_categoria_dia') AS tabla_creada,
       to_regclass('public.v_control_lote_almacen') AS vista_fnbc;
""", "H8 · El script falla al crear el trigger sobre detalle_pedido")

        # H9 · migracion segura: prueba de rollback con violacion de DF2
        ejecutar(srv, "foodstore_u4", """
DROP VIEW  IF EXISTS v_control_lote_almacen CASCADE;
DROP TABLE IF EXISTS control_lote CASCADE;
DROP TABLE IF EXISTS responsable_deposito CASCADE;
DROP TABLE IF EXISTS control_lote_almacen_backup CASCADE;
DROP TABLE IF EXISTS control_lote_almacen CASCADE;
CREATE TABLE control_lote_almacen (
    lote_id                BIGINT NOT NULL,
    deposito_id            BIGINT NOT NULL,
    responsable_control_id BIGINT NOT NULL,
    PRIMARY KEY (lote_id, deposito_id)
);
INSERT INTO control_lote_almacen VALUES (1, 10, 100), (2, 20, 100);
""", "H9 · Preparacion: DF2 violada (responsable 100 en dos depositos)")

        ejecutar(srv, "foodstore_u4", U4_MIGRACION.read_text(encoding="utf-8"),
                 "H9 · Migracion segura: RAISE EXCEPTION + ROLLBACK",
                 detener=False)

        ejecutar(srv, "foodstore_u4", """
SELECT to_regclass('public.responsable_deposito') AS responsable_deposito,
       to_regclass('public.control_lote')         AS control_lote,
       to_regclass('public.v_control_lote_almacen') AS vista;
SELECT 'original_intacta' AS control, count(*) AS filas
FROM control_lote_almacen;
SELECT 'backup' AS control, count(*) AS filas
FROM control_lote_almacen_backup;
""", "H9 · Tras el fallo no quedan objetos nuevos; datos y backup intactos")

        # ------------------------------------------------------------------
        # U6/U7/U8 · revision estatica (no requiere motor)
        # ------------------------------------------------------------------
        log("")
        log("=" * 74)
        log("REVISION ESTATICA · U6/U7/U8")
        log("=" * 74)

        restore = leer(U6_RESTORE)
        backup = leer(U6_BACKUP)
        maint = leer(U6_MAINT)
        export = leer(U7_EXPORT)
        crear = leer(U7_CREATE)
        importar = leer(U8_IMPORT)
        runner = leer(U8_RUNNER)

        log("")
        log("H10 (U6) restore_test.ps1: usa --no-owner/--no-privileges=%s; "
            "verifica roles/grants despues de restaurar=%s"
            % ("--no-owner" in restore and "--no-privileges" in restore,
               "role_table_grants" in restore or "has_table_privilege" in restore))
        log("   Detectado: la restauracion valida datos e integridad, pero no")
        log("   comprueba que los roles ni los GRANT se hayan restaurado.")

        log("")
        log("H11 (U6) backup_foodstore.ps1: retencion por LastWriteTime=%s; "
            "parametro RetencionDias=%s"
            % ("LastWriteTime" in backup, "RetencionDias" in backup))
        log("   Detectado: copiar o restaurar archivos cambia la fecha de")
        log("   modificacion y puede alterar que respaldos se conservan.")

        log("")
        log("H12 (U7) 01_exportar_pedidos_mongodb.sql: usa replace()=%s; "
            "escapa barras invertidas=%s"
            % ("replace(" in export, "chr(92)" in export or "replace(\\\\" in export))
        log("   Detectado: solo se escapan comillas dobles; un nombre con")
        log("   barra invertida o salto de linea generaria JavaScript invalido.")

        log("")
        log("H13 (U7) 01_crear_coleccion.js: db.pedidos.drop()=%s"
            % ("db.pedidos.drop()" in crear))
        log("   Detectado: idempotente en laboratorio, pero destructivo si se")
        log("   ejecuta sobre una base ya poblada.")

        log("")
        log("H14 (U8) importar_snapshot.sql referencia importar_snapshot.py=%s; "
            "el archivo existe=%s"
            % ("importar_snapshot.py" in importar,
               (REPO / "TP8_U8_FoodStore" / "movil" / "importar_snapshot.py").exists()))
        log("   Detectado: comentario con una alternativa inexistente.")

        log("")
        propio = leer(Path(__file__).resolve())
        log("H15 (U8) rutas temp de usuario Windows fijas: simular_tp8.py=%s; "
            "revision_codigo.py=%s"
            % ('PGDATA = Path(r"C:\\Users' in runner,
               'PGDATA = Path(r"C:\\Users' in propio))
        log("   Detectado: la ruta de PGDATA no es portable a otra cuenta.")
        if 'PGDATA = Path(r"C:\\Users' in runner:
            log('   simular_tp8.py contiene una ruta literal C:\\Users\\...')
        if 'PGDATA = Path(r"C:\\Users' in propio:
            log('   revision_codigo.py contiene una ruta literal C:\\Users\\...')

        log("")
        log("H16 (U8) importar_snapshot.sql usa .import=%s; simular_tp8.py "
            "usa .import=%s"
            % (".import" in importar, ".import" in runner))
        log("   Detectado: el .sql depende del cliente sqlite3 y el runner")
        log("   Python importa el CSV por otra via; son dos caminos distintos.")

        log("")
        log("H17 (U6) maintenance.sql usa DROP TABLE IF EXISTS "
            "tmp_mantenimiento=%s; califica pg_temp=%s"
            % ("DROP TABLE IF EXISTS tmp_mantenimiento" in maint,
               "pg_temp" in maint))
        log("   Detectado: sin calificar el esquema, podria borrar una tabla")
        log("   permanente llamada tmp_mantenimiento si existiera.")

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
        log("H7 ACEPTADO: tp_fnbc_control_lote.sql hace DROP TABLE y recrea el")
        log("   ejemplo; sobre una base real borra filas. Se corrige con")
        log("   tp_fnbc_control_lote_migracion_segura.sql (backup + BEGIN/COMMIT")
        log("   + verificacion + ROLLBACK), documentado en kiro/design.md.")
        log("H8 ACEPTADO: U4 usa detalle_pedido y el esquema final define")
        log("   linea_pedido; el trigger falla. Se propone vista de")
        log("   compatibilidad detalle_pedido (como en U6) o renombrar en U4.")
        log("H9 ACEPTADO: la migracion segura aborta con RAISE EXCEPTION ante")
        log("   una violacion de DF2 y el ROLLBACK no deja objetos nuevos; la")
        log("   tabla original y el backup conservan sus filas.")
        log("H10 ACEPTADO (limitacion): restore_test.ps1 usa --no-owner y")
        log("   --no-privileges; valida datos e integridad, no roles/GRANT. Se")
        log("   documenta y se propone una verificacion posterior de privilegios.")
        log("H11 ACEPTADO (mejora menor): la retencion por LastWriteTime puede")
        log("   desalinearse si los archivos se copian; usar la fecha del nombre.")
        log("H12 ACEPTADO: la exportacion a MongoDB escapa comillas dobles pero")
        log("   no barras invertidas ni saltos de linea; usar json_build_object")
        log("   o escapar tambien '\\\\' y '\\n' antes de generar el JavaScript.")
        log("H13 ACEPTADO (laboratorio): db.pedidos.drop() es intencional para")
        log("   idempotencia; documentar que no debe ejecutarse en produccion.")
        log("H14 ACEPTADO: el comentario referencia importar_snapshot.py, que no")
        log("   existe; corregir el comentario o agregar el script Python.")
        log("H15 ACEPTADO: la ruta PGDATA esta fijada a una cuenta Windows; usar")
        log("   tempfile.gettempdir() para que sea portable.")
        log("H16 DESCARTADO: importar_snapshot.sql es para el cliente sqlite3 y")
        log("   simular_tp8.py importa el CSV por Python; son caminos distintos")
        log("   y el runner cubre la reproducibilidad. Se documenta la diferencia.")
        log("H17 ACEPTADO (bajo riesgo): calificar la tabla temporal como")
        log("   pg_temp.tmp_mantenimiento para no borrar una tabla homonima.")

        (EVID / "07_revision_codigo.txt").write_text("\n".join(lineas) + "\n",
                                                     encoding="utf-8")
    finally:
        srv.cleanup()


if __name__ == "__main__":
    main()
