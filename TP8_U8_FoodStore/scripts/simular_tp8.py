"""
TP8 · Unidad 8 · Food Store
Runner reproducible de la simulacion completa.

Hace, en un solo proceso:
  1. Levanta un PostgreSQL 16 portable (pgserver) en un cluster temporal.
  2. Carga el seed de pruebas y crea v_snapshot_movil.
  3. Exporta la instantanea a movil/servidor_snapshot.csv.
  4. Crea foodstore_movil.db con schema_sqlite.sql e importa la instantanea.
  5. Ejecuta pruebas_sqlite.sql (consigna 1.c).
  6. Ejecuta los casos C2 a C6 con el semaforo (consigna 2.b y 2.c).
  7. Verifica que PostgreSQL no cambio (pedidos y stock).
  8. Deja toda la evidencia en evidencias/.

Uso:
    python scripts/simular_tp8.py

Requiere: pip install pgserver
"""

import csv
import difflib
import shutil
import sqlite3
import time
from pathlib import Path

import pgserver

BASE = Path(__file__).resolve().parent.parent
MOVIL = BASE / "movil"
SERVIDOR = BASE / "servidor"
EVID = BASE / "evidencias"
DB = MOVIL / "foodstore_movil.db"
PGDATA = Path(r"C:\Users\tiago\AppData\Local\Temp\opencode\pgdata_tp8_run")

# ---------------------------------------------------------------------------
# UUIDs de los borradores y solicitudes (inventados, formato v4 valido).
# ---------------------------------------------------------------------------
C2_DRAFT = "5a5a5a5a-5a5a-4a5a-8a5a-5a5a5a5a5a5a"
C2_SOL_A = "a2a2a2a2-a2a2-4a2a-8a2a-a2a2a2a2a2a2"
C2_SOL_B = "b2b2b2b2-b2b2-4b2b-8b2b-b2b2b2b2b2b2"
C3_DRAFT = "3c3c3c3c-3c3c-4c3c-8c3c-3c3c3c3c3c3c"
C3_SOL = "c3c3c3c3-c3c3-4c3c-8c3c-c3c3c3c3c3c3"
C4_DRAFT = "4d4d4d4d-4d4d-4d4d-8d4d-4d4d4d4d4d4d"
C4_SOL = "d4d4d4d4-d4d4-4d4d-8d4d-d4d4d4d4d4d4"
C5_DRAFT = "5e5e5e5e-5e5e-4e5e-8e5e-5e5e5e5e5e5e"
C5_SOL = "e5e5e5e5-e5e5-4e5e-8e5e-e5e5e5e5e5e5"
C6_DRAFT = "6f6f6f6f-6f6f-4f6f-8f6f-6f6f6f6f6f6f"
C6_SOL = "f6f6f6f6-f6f6-4f6f-8f6f-f6f6f6f6f6f6"


def escribir(nombre, texto):
    (EVID / nombre).write_text(texto, encoding="utf-8")


def split_sql(texto):
    """Separa sentencias por ';' respetando comentarios y comillas."""
    sentencias, buf = [], []
    i, n = 0, len(texto)
    en_comilla = en_doble = en_linea = en_bloque = False
    while i < n:
        c = texto[i]
        nxt = texto[i + 1] if i + 1 < n else ""
        if en_linea:
            buf.append(c)
            if c == "\n":
                en_linea = False
            i += 1
            continue
        if en_bloque:
            buf.append(c)
            if c == "*" and nxt == "/":
                buf.append(nxt)
                i += 2
                en_bloque = False
                continue
            i += 1
            continue
        if en_comilla:
            buf.append(c)
            if c == "'":
                if nxt == "'":
                    buf.append(nxt)
                    i += 2
                    continue
                en_comilla = False
            i += 1
            continue
        if en_doble:
            buf.append(c)
            if c == '"':
                if nxt == '"':
                    buf.append(nxt)
                    i += 2
                    continue
                en_doble = False
            i += 1
            continue
        if c == "-" and nxt == "-":
            buf.extend([c, nxt])
            i += 2
            en_linea = True
            continue
        if c == "/" and nxt == "*":
            buf.extend([c, nxt])
            i += 2
            en_bloque = True
            continue
        if c == "'":
            buf.append(c)
            en_comilla = True
            i += 1
            continue
        if c == '"':
            buf.append(c)
            en_doble = True
            i += 1
            continue
        if c == ";":
            stmt = "".join(buf).strip()
            if stmt:
                sentencias.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    stmt = "".join(buf).strip()
    if stmt:
        sentencias.append(stmt)
    return sentencias


def ejecutar_sqlite(conn, texto, lines):
    resultados = []
    for stmt in split_sql(texto):
        plano = " ".join(stmt.split())
        lines.append("")
        lines.append(">>> " + plano)
        try:
            cur = conn.execute(stmt)
            if cur.description:
                cols = [d[0] for d in cur.description]
                filas = cur.fetchall()
                lines.append("    " + " | ".join(cols))
                for fila in filas:
                    lines.append("    " + " | ".join("" if v is None else str(v) for v in fila))
                resultados.append((plano, cols, filas, None))
            else:
                lines.append("    OK")
                resultados.append((plano, None, None, None))
        except sqlite3.Error as exc:
            lines.append("    ERROR: " + str(exc))
            resultados.append((plano, None, None, str(exc)))
    return resultados


def _booleano_a_entero(valor):
    return 1 if str(valor).strip().lower() in ("t", "true", "1") else 0


def importar_snapshot(conn, csv_path):
    """Carga el CSV en snapshot_servidor y refresca producto_cache (UPSERT)."""
    conn.execute("DROP TABLE IF EXISTS snapshot_servidor")
    conn.execute(
        """
        CREATE TABLE snapshot_servidor (
            producto_id     INTEGER,
            nombre          TEXT,
            precio_centavos INTEGER,
            stock_visto     INTEGER,
            disponible      INTEGER,
            eliminado       INTEGER,
            fecha_copia     TEXT
        )
        """
    )
    with open(csv_path, newline="", encoding="utf-8") as archivo:
        lector = csv.reader(archivo)
        next(lector)  # cabecera
        filas = []
        for fila in lector:
            producto_id, nombre, precio, stock, disponible, eliminado, fecha = fila
            filas.append((
                int(producto_id),
                nombre,
                int(precio),
                int(stock),
                _booleano_a_entero(disponible),
                _booleano_a_entero(eliminado),
                fecha,
            ))

    conn.execute("BEGIN")
    conn.executemany(
        "INSERT INTO snapshot_servidor VALUES (?, ?, ?, ?, ?, ?, ?)", filas
    )
    conn.execute(
        """
        INSERT INTO producto_cache
            (id, nombre, precio_centavos, stock_visto, disponible, eliminado, fecha_copia)
        SELECT CAST(producto_id AS INTEGER),
               nombre,
               CAST(precio_centavos AS INTEGER),
               CAST(stock_visto AS INTEGER),
               CASE lower(trim(disponible))
                    WHEN 't' THEN 1 WHEN 'true' THEN 1 WHEN '1' THEN 1 ELSE 0 END,
               CASE lower(trim(eliminado))
                    WHEN 't' THEN 1 WHEN 'true' THEN 1 WHEN '1' THEN 1 ELSE 0 END,
               fecha_copia
        FROM snapshot_servidor
        WHERE 1
        ON CONFLICT(id) DO UPDATE SET
            nombre          = excluded.nombre,
            precio_centavos = excluded.precio_centavos,
            stock_visto     = excluded.stock_visto,
            disponible      = excluded.disponible,
            eliminado       = excluded.eliminado,
            fecha_copia     = excluded.fecha_copia
        """
    )
    conn.execute("COMMIT")
    return len(filas)


def crear_borrador(conn, id_local, items, solicitud_uuid,
                   usuario="vendedor-demo", forma_pago="EFECTIVO",
                   fecha="2026-11-04T11:00:00Z"):
    conn.execute("BEGIN")
    try:
        conn.execute(
            "INSERT INTO pedido_borrador (id_local, usuario, forma_pago, fecha) VALUES (?, ?, ?, ?)",
            (id_local, usuario, forma_pago, fecha),
        )
        for producto_id, cantidad, precio in items:
            conn.execute(
                "INSERT INTO item_borrador (id_local, producto_id, cantidad, precio_centavos_visto)"
                " VALUES (?, ?, ?, ?)",
                (id_local, producto_id, cantidad, precio),
            )
        conn.execute(
            "INSERT INTO cola_sync (solicitud_uuid, id_local, estado) VALUES (?, ?, 'PENDIENTE')",
            (solicitud_uuid, id_local),
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def estado(conn, uuid):
    return conn.execute(
        "SELECT estado, motivo, evaluado_en FROM cola_sync WHERE solicitud_uuid = ?",
        (uuid,),
    ).fetchone()


def correr_semaforo(conn, lines, titulo):
    lines.append("")
    lines.append("=" * 74)
    lines.append("SEMAFORO · " + titulo)
    lines.append("=" * 74)
    res = ejecutar_sqlite(conn, (MOVIL / "semaforo.sql").read_text(encoding="utf-8"), lines)
    detalle = []
    for _stmt, cols, filas, _err in res:
        if cols and "solicitud_uuid" in cols:
            detalle = filas
    return detalle


def esperar(condicion, mensaje, lines):
    if condicion:
        lines.append("  [OK]    " + mensaje)
    else:
        lines.append("  [FALLA] " + mensaje)
        raise AssertionError(mensaje)


def main():
    EVID.mkdir(exist_ok=True)
    if PGDATA.exists():
        shutil.rmtree(PGDATA, ignore_errors=True)
    if DB.exists():
        DB.unlink()

    resumen = []
    casos = []
    resultados = []

    print("Levantando PostgreSQL portable...")
    srv = pgserver.get_server(str(PGDATA), cleanup_mode="stop")
    try:
        # ------------------------------------------------------------------
        # Servidor: seed + vista
        # ------------------------------------------------------------------
        seed_sql = (SERVIDOR / "00_seed_servidor.sql").read_text(encoding="utf-8")
        vista_sql = (SERVIDOR / "01_v_snapshot_movil.sql").read_text(encoding="utf-8")
        salida_seed = srv.psql("\\set ON_ERROR_STOP on\n" + seed_sql)
        salida_vista = srv.psql("\\set ON_ERROR_STOP on\n" + vista_sql)
        escribir("01_seed_y_vista.txt", salida_seed + "\n" + salida_vista)

        # Invariantes y estado ANTES de simular.
        invariantes_antes = srv.psql(
            "\\set ON_ERROR_STOP on\n"
            + (SERVIDOR / "03_verificacion_postgres.sql").read_text(encoding="utf-8")
        )
        estado_antes = srv.psql(
            "\\set ON_ERROR_STOP on\n"
            + (SERVIDOR / "04_estado_productos.sql").read_text(encoding="utf-8")
        )
        escribir("05_verificacion_postgres_antes.txt", invariantes_antes)
        escribir("06_estado_productos_antes.txt", estado_antes)

        # ------------------------------------------------------------------
        # Instantanea inicial (consigna 2.a)
        # ------------------------------------------------------------------
        csv_inicial = MOVIL / "servidor_snapshot.csv"
        ruta_pg = str(csv_inicial).replace("\\", "/")
        srv.psql(
            "\\set ON_ERROR_STOP on\n"
            f"\\copy (SELECT * FROM v_snapshot_movil) TO '{ruta_pg}' CSV HEADER\n"
        )
        shutil.copyfile(csv_inicial, EVID / "snapshot_v1.csv")
        contenido_csv = csv_inicial.read_text(encoding="utf-8")
        fecha_copia = contenido_csv.splitlines()[1].split(",")[-1]
        escribir(
            "03_snapshot_export.txt",
            "CSV exportado desde v_snapshot_movil (v1):\n\n"
            + contenido_csv
            + "\n\nFecha de copia anotada: " + fecha_copia + "\n",
        )

        # ------------------------------------------------------------------
        # SQLite: schema + importacion
        # ------------------------------------------------------------------
        conn = sqlite3.connect(DB)
        conn.isolation_level = None  # transacciones explicitas (BEGIN/COMMIT)
        conn.execute("PRAGMA foreign_keys = ON")

        schema_lines = []
        ejecutar_sqlite(
            conn,
            (MOVIL / "schema_sqlite.sql").read_text(encoding="utf-8"),
            schema_lines,
        )
        importadas = importar_snapshot(conn, csv_inicial)
        escribir(
            "03_snapshot_export.txt",
            (EVID / "03_snapshot_export.txt").read_text(encoding="utf-8")
            + f"\nImportadas {importadas} filas en snapshot_servidor y refrescado producto_cache.\n",
        )

        # ------------------------------------------------------------------
        # Consigna 1.c: pruebas de la base de la tablet
        # ------------------------------------------------------------------
        pruebas_lines = ["PRUEBAS SQLITE · consigna 1.c", "=" * 74]
        ejecutar_sqlite(
            conn,
            (MOVIL / "pruebas_sqlite.sql").read_text(encoding="utf-8"),
            pruebas_lines,
        )
        escribir("02_pruebas_sqlite.txt", "\n".join(pruebas_lines))

        # Limpieza de los borradores de prueba: los casos arrancan limpios.
        conn.execute("DELETE FROM cola_sync")
        conn.execute("DELETE FROM item_borrador")
        conn.execute("DELETE FROM pedido_borrador")

        # ------------------------------------------------------------------
        # Caso C2: cambio de precio -> CONFLICTO; cliente acepta -> verde
        # ------------------------------------------------------------------
        casos.append("C2 · precio cambiado")
        crear_borrador(conn, C2_DRAFT, [(1, 2, 105000)], C2_SOL_A)
        srv.psql("\\set ON_ERROR_STOP on\nUPDATE producto SET precio = 1150.00 WHERE id = 1;")
        csv_v2 = EVID / "snapshot_v2.csv"
        srv.psql(
            "\\set ON_ERROR_STOP on\n"
            f"\\copy (SELECT * FROM v_snapshot_movil) TO '{str(csv_v2).replace(chr(92), '/')}' CSV HEADER\n"
        )
        importar_snapshot(conn, csv_v2)
        correr_semaforo(conn, casos, "C2 tras subir el precio en el servidor")
        est = estado(conn, C2_SOL_A)
        esperar(est[0] == "CONFLICTO" and est[1] == "PRECIO_CAMBIADO",
                f"C2-A debe ser CONFLICTO/PRECIO_CAMBIADO (obtenido {est})", casos)
        casos.append("C2-A estado: " + str(est))
        resultados.append("C2-A " + str(est))

        conn.execute(
            "UPDATE item_borrador SET precio_centavos_visto = 115000"
            " WHERE id_local = ? AND producto_id = 1",
            (C2_DRAFT,),
        )
        conn.execute(
            "INSERT INTO cola_sync (solicitud_uuid, id_local, estado) VALUES (?, ?, 'PENDIENTE')",
            (C2_SOL_B, C2_DRAFT),
        )
        correr_semaforo(conn, casos, "C2 tras aceptar el precio (solicitud nueva)")
        est_b = estado(conn, C2_SOL_B)
        esperar(est_b[0] == "SIMULADO_APROBADO" and est_b[1] == "TODO_COINCIDE",
                f"C2-B debe ser SIMULADO_APROBADO/TODO_COINCIDE (obtenido {est_b})", casos)
        casos.append("C2-B estado: " + str(est_b))
        resultados.append("C2-B " + str(est_b))

        # ------------------------------------------------------------------
        # Caso C3: mas unidades que el stock -> RECHAZADO
        # ------------------------------------------------------------------
        casos.append("C3 · stock insuficiente")
        crear_borrador(conn, C3_DRAFT, [(4, 15, 30000)], C3_SOL)
        correr_semaforo(conn, casos, "C3 con cantidad 15 y stock 10")
        est = estado(conn, C3_SOL)
        esperar(est[0] == "RECHAZADO" and est[1] == "STOCK_INSUFICIENTE",
                f"C3 debe ser RECHAZADO/STOCK_INSUFICIENTE (obtenido {est})", casos)
        casos.append("C3 estado: " + str(est))
        resultados.append("C3 " + str(est))

        # ------------------------------------------------------------------
        # Caso C4: baja logica -> RECHAZADO; la fila del borrador queda
        # ------------------------------------------------------------------
        casos.append("C4 · producto dado de baja")
        crear_borrador(conn, C4_DRAFT, [(5, 1, 60000)], C4_SOL)
        srv.psql("\\set ON_ERROR_STOP on\nUPDATE producto SET activo = FALSE WHERE id = 5;")
        csv_v3 = EVID / "snapshot_v3.csv"
        srv.psql(
            "\\set ON_ERROR_STOP on\n"
            f"\\copy (SELECT * FROM v_snapshot_movil) TO '{str(csv_v3).replace(chr(92), '/')}' CSV HEADER\n"
        )
        importar_snapshot(conn, csv_v3)
        correr_semaforo(conn, casos, "C4 tras la baja logica del producto 5")
        est = estado(conn, C4_SOL)
        esperar(est[0] == "RECHAZADO" and est[1] == "PRODUCTO_DADO_DE_BAJA",
                f"C4 debe ser RECHAZADO/PRODUCTO_DADO_DE_BAJA (obtenido {est})", casos)
        casos.append("C4 estado: " + str(est))
        resultados.append("C4 " + str(est))

        disponibles = [r[0] for r in conn.execute(
            "SELECT id FROM producto_cache WHERE disponible = 1 AND eliminado = 0 ORDER BY id"
        ).fetchall()]
        fila5 = conn.execute(
            "SELECT id, disponible, eliminado FROM producto_cache WHERE id = 5"
        ).fetchone()
        item5 = conn.execute(
            "SELECT count(*) FROM item_borrador WHERE id_local = ?", (C4_DRAFT,)
        ).fetchone()[0]
        esperar(5 not in disponibles, "C4: el producto 5 ya no aparece en el catalogo disponible", casos)
        esperar(fila5 == (5, 0, 1), "C4: la fila del producto 5 queda como lapida (disponible=0, eliminado=1)", casos)
        esperar(item5 == 1, "C4: el item del borrador sigue existiendo", casos)
        casos.append("C4 catalogo disponible: " + str(disponibles))
        casos.append("C4 fila producto 5: " + str(fila5))
        casos.append("C4 items del borrador: " + str(item5))

        # ------------------------------------------------------------------
        # Caso C5: sin cambios -> SIMULADO_APROBADO
        # ------------------------------------------------------------------
        casos.append("C5 · sin cambios")
        crear_borrador(conn, C5_DRAFT, [(2, 1, 80000)], C5_SOL)
        correr_semaforo(conn, casos, "C5 sin cambios")
        est = estado(conn, C5_SOL)
        esperar(est[0] == "SIMULADO_APROBADO" and est[1] == "TODO_COINCIDE",
                f"C5 debe ser SIMULADO_APROBADO/TODO_COINCIDE (obtenido {est})", casos)
        casos.append("C5 estado: " + str(est))
        resultados.append("C5 " + str(est))

        # ------------------------------------------------------------------
        # Caso C6: reenvio del mismo UUID + repeticion de la simulacion
        # ------------------------------------------------------------------
        casos.append("C6 · idempotencia")
        crear_borrador(conn, C6_DRAFT, [(3, 2, 45000)], C6_SOL)
        correr_semaforo(conn, casos, "C6 primera simulacion")
        est = estado(conn, C6_SOL)
        esperar(est[0] == "SIMULADO_APROBADO" and est[1] == "TODO_COINCIDE",
                f"C6 primera evaluacion debe ser SIMULADO_APROBADO (obtenido {est})", casos)
        antes_c6 = est

        try:
            conn.execute(
                "INSERT INTO cola_sync (solicitud_uuid, id_local, estado) VALUES (?, ?, 'PENDIENTE')",
                (C6_SOL, C6_DRAFT),
            )
            casos.append("  [FALLA] C6: se esperaba violacion de clave primaria")
            raise AssertionError("C6: el UUID repetido no fallo")
        except sqlite3.IntegrityError as exc:
            casos.append("  [OK]    C6: UUID repetido rechazado por clave primaria -> " + str(exc))

        time.sleep(1.1)
        correr_semaforo(conn, casos, "C6 repeticion de la simulacion")
        despues_c6 = estado(conn, C6_SOL)
        esperar(antes_c6 == despues_c6,
                "C6: repetir la simulacion no reevalua la solicitud (evaluado_en igual)", casos)
        casos.append("C6 antes:   " + str(antes_c6))
        casos.append("C6 despues: " + str(despues_c6))
        casos.append("C6 filas con ese UUID: " + str(
            conn.execute("SELECT count(*) FROM cola_sync WHERE solicitud_uuid = ?", (C6_SOL,)).fetchone()[0]
        ))
        resultados.append("C6 " + str(despues_c6) + " (sin reevaluar)")

        # ------------------------------------------------------------------
        # Estado final de cola_sync
        # ------------------------------------------------------------------
        casos.append("")
        casos.append("ESTADO FINAL DE cola_sync")
        casos.append("-" * 74)
        for fila in conn.execute(
            "SELECT solicitud_uuid, id_local, estado, motivo, evaluado_en"
            " FROM cola_sync ORDER BY creado_en, solicitud_uuid"
        ).fetchall():
            casos.append(" | ".join("" if v is None else str(v) for v in fila))

        escribir("04_semaforo_casos.txt", "\n".join(casos))

        # ------------------------------------------------------------------
        # Verificacion final del servidor
        # ------------------------------------------------------------------
        invariantes_despues = srv.psql(
            "\\set ON_ERROR_STOP on\n"
            + (SERVIDOR / "03_verificacion_postgres.sql").read_text(encoding="utf-8")
        )
        estado_despues = srv.psql(
            "\\set ON_ERROR_STOP on\n"
            + (SERVIDOR / "04_estado_productos.sql").read_text(encoding="utf-8")
        )
        escribir("05_verificacion_postgres_despues.txt", invariantes_despues)
        escribir("06_estado_productos_despues.txt", estado_despues)

        diff = list(difflib.unified_diff(
            invariantes_antes.splitlines(),
            invariantes_despues.splitlines(),
            fromfile="antes",
            tofile="despues",
            lineterm="",
        ))
        texto_diff = "\n".join(diff) if diff else "SIN DIFERENCIAS: pedidos, lineas, stock e importe no cambiaron."
        escribir("05_verificacion_postgres_diff.txt", texto_diff)

        conn.close()

        # ------------------------------------------------------------------
        # Resumen
        # ------------------------------------------------------------------
        resumen.append("TP8 · Food Store · resumen de ejecucion")
        resumen.append("=" * 74)
        resumen.append("Fecha de copia inicial: " + fecha_copia)
        resumen.append("Filas importadas en snapshot_servidor: " + str(importadas))
        resumen.append("Casos: " + " | ".join(resultados))
        resumen.append("")
        resumen.append("Invariantes PostgreSQL:")
        resumen.append(invariantes_despues.strip())
        resumen.append("")
        resumen.append("Diff invariantes antes/despues:")
        resumen.append(texto_diff)
        resumen.append("")
        resumen.append("Archivos generados:")
        for ruta in sorted(EVID.glob("*")):
            resumen.append("  - " + ruta.name)
        escribir("00_resumen.txt", "\n".join(resumen) + "\n")

        print("\n".join(resumen))
    finally:
        if casos:
            escribir("04_semaforo_casos.txt", "\n".join(casos))
        srv.cleanup()


if __name__ == "__main__":
    main()
