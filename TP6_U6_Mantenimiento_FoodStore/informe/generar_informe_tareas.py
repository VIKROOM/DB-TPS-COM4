# ============================================================================
# generar_informe_tareas.py - genera informe_u6_tareas.pdf, el informe del TP
# U6 organizado por las tareas efectivamente ejecutadas, con resultados reales
# tomados de evidencias/ (métricas del simulacro, conteos y logs).
#
# Uso (desde la raíz del TP):
#   python informe/generar_informe_tareas.py
# Requiere reportlab:  python -m pip install reportlab
# ============================================================================
import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidencias")
SALIDA = os.path.join(ROOT, "informe_u6_tareas.pdf")
REPO = "https://github.com/VIKROOM/DB-TPS-COM4"
REPO_TXT = "github.com/VIKROOM/DB-TPS-COM4"

with open(os.path.join(EVID, "restore_metrics.json"), encoding="utf-8") as fh:
    m = json.load(fh)

conteos = {}
with open(os.path.join(EVID, "counts_pre_backup.txt"), encoding="utf-8") as fh:
    for linea in fh:
        if "|" in linea:
            k, v = linea.strip().split("|", 1)
            conteos[k] = int(float(v))

fmt = lambda n: f"{n:,}".replace(",", ".")
rto = f"{m['rto_segundos']:.2f}".replace(".", ",")
rpo = int(m["rpo_segundos"])
rpo_txt = f"{rpo} s ({rpo // 60} min {rpo % 60} s)"
mb = f"{m['respaldo_bytes'] / 1_048_576:.2f}".replace(".", ",")

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                              italic="Arial", boldItalic="Arial-Bold")

AZUL = colors.HexColor("#14375F")
AZUL_CLARO = colors.HexColor("#2E6DA4")
GRIS = colors.HexColor("#5A5A5A")
GRIS_CLARO = colors.HexColor("#8A8A8A")
FONDO = colors.HexColor("#E8EEF6")
FONDO_SUAVE = colors.HexColor("#F4F7FB")
VERDE = colors.HexColor("#1B7A43")
AMBAR = colors.HexColor("#9A5B00")
AMBAR_FONDO = colors.HexColor("#FDF3E2")
BORDE = colors.HexColor("#9AA7B6")

PAGINA_ANCHO, PAGINA_ALTO = A4
MARGEN_IZQ = MARGEN_DER = 14 * mm
MARGEN_SUP = 18 * mm
MARGEN_INF = 17 * mm
ANCHO = PAGINA_ANCHO - MARGEN_IZQ - MARGEN_DER

# ---------------------------------------------------------------- estilos ----
titulo_banner = ParagraphStyle("titulo_banner", fontName="Arial-Bold", fontSize=20,
                               leading=23, textColor=colors.white)
sub_banner = ParagraphStyle("sub_banner", fontName="Arial", fontSize=9.6, leading=12,
                            textColor=colors.HexColor("#D6E4F2"))
meta_celda = ParagraphStyle("meta_celda", fontName="Arial", fontSize=8.3, leading=10.2)
meta_b = ParagraphStyle("meta_b", parent=meta_celda, fontName="Arial-Bold", textColor=AZUL)

seccion = ParagraphStyle("seccion", fontName="Arial-Bold", fontSize=11.5, leading=13.5,
                         textColor=AZUL, spaceBefore=1, spaceAfter=2)
cuerpo = ParagraphStyle("cuerpo", fontName="Arial", fontSize=9.1, leading=12,
                        alignment=TA_LEFT, spaceAfter=2.6)
vineta = ParagraphStyle("vineta", parent=cuerpo, leftIndent=9, bulletIndent=1.5,
                        bulletFontName="Arial", bulletFontSize=8, spaceAfter=1.6)
nota = ParagraphStyle("nota", fontName="Arial", fontSize=7.9, leading=9.8,
                      textColor=GRIS)
celda = ParagraphStyle("celda", fontName="Arial", fontSize=8.4, leading=10.4)
celda_b = ParagraphStyle("celda_b", parent=celda, fontName="Arial-Bold")
celda_chica = ParagraphStyle("celda_chica", fontName="Arial", fontSize=8.0, leading=9.8)
celda_chica_b = ParagraphStyle("celda_chica_b", parent=celda_chica, fontName="Arial-Bold")
chip_ok = ParagraphStyle("chip_ok", fontName="Arial-Bold", fontSize=7.2, leading=8.6,
                         textColor=colors.white)


def P(texto, estilo=cuerpo, **kw):
    return Paragraph(texto, estilo, **kw)


def bullets(items, estilo=vineta):
    return [P(t, estilo, bulletText="•") for t in items]


def tabla(encabezados, filas, anchos, chica=False, repeat=True):
    est_c = celda_chica if chica else celda
    est_b = celda_chica_b if chica else celda_b
    datos = [[P(h, est_b) for h in encabezados]]
    for fila in filas:
        datos.append([P(str(c), est_c) for c in fila])
    t = Table(datos, colWidths=[a * mm for a in anchos], hAlign="LEFT",
              repeatRows=1 if repeat else 0)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, BORDE),
        ("BACKGROUND", (0, 0), (-1, 0), FONDO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.2),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
    ]))
    return t


def encabezado_tarea(numero, titulo):
    """Banda con número, título y estado."""
    fila = Table(
        [[P(f"<font size=15>{numero}</font>", ParagraphStyle(
            "num", fontName="Arial-Bold", fontSize=15, leading=17,
            textColor=colors.white)),
          P(f"<b>{titulo}</b>", ParagraphStyle(
              "tt", fontName="Arial-Bold", fontSize=11.3, leading=13.5,
              textColor=colors.white)),
          P("COMPLETADA", chip_ok)]],
        colWidths=[10 * mm, ANCHO - 34 * mm, 24 * mm],
        hAlign="LEFT",
    )
    fila.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL),
        ("BACKGROUND", (2, 0), (2, 0), VERDE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (0, 0), 5),
        ("LEFTPADDING", (1, 0), (1, 0), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 4.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.6),
        ("RIGHTPADDING", (2, 0), (2, 0), 5),
    ]))
    return fila


def callout(etiqueta, texto):
    """Recuadro ámbar para problemas reales y correcciones."""
    t = Table(
        [[P(f"<b>{etiqueta}</b>", ParagraphStyle(
            "call_lbl", fontName="Arial-Bold", fontSize=8.3, leading=10,
            textColor=AMBAR)),
          P(texto, ParagraphStyle(
              "call_txt", fontName="Arial", fontSize=8.6, leading=11,
              textColor=colors.HexColor("#4A3A22")))]],
        colWidths=[27 * mm, ANCHO - 27 * mm],
        hAlign="LEFT",
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AMBAR_FONDO),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, AMBAR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def evidencia(texto):
    return P(f"<b>Evidencias:</b> {texto}", ParagraphStyle(
        "evid", fontName="Arial", fontSize=7.8, leading=9.6, textColor=GRIS,
        spaceBefore=1))


def bloque_tarea(numero, titulo, consigna, hechos, extras=(), problema=None,
                 evid=None):
    """Arma una tarea completa y evita cortar el encabezado de su cuerpo."""
    partes = [Spacer(1, 5 * mm), encabezado_tarea(numero, titulo), Spacer(1, 2.4 * mm)]
    partes.append(P(f"<b>Consigna.</b> {consigna}"))
    partes.append(P("<b>Qué se hizo.</b>"))
    partes.extend(bullets(hechos))
    for extra in extras:
        partes.append(Spacer(1, 1.6 * mm))
        partes.append(extra)
    if problema:
        partes.append(Spacer(1, 2 * mm))
        partes.append(callout(*problema))
    if evid:
        partes.append(Spacer(1, 1.4 * mm))
        partes.append(evidencia(evid))
    return partes


# ---------------------------------------------------------- header/footer ----
def pie(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#C9D3DF"))
    canvas.setLineWidth(0.5)
    canvas.line(MARGEN_IZQ, 12.5 * mm, PAGINA_ANCHO - MARGEN_DER, 12.5 * mm)
    canvas.setFont("Arial", 7.3)
    canvas.setFillColor(GRIS_CLARO)
    canvas.drawString(MARGEN_IZQ, 8.6 * mm,
                      "TP Unidad 6 · Mantenimiento, respaldo y recuperación · Food Store")
    canvas.drawRightString(PAGINA_ANCHO - MARGEN_DER, 8.6 * mm,
                           f"Página {canvas.getPageNumber()}")
    canvas.setFont("Arial", 7.3)
    canvas.setFillColor(AZUL_CLARO)
    canvas.drawString(MARGEN_IZQ, 5.4 * mm, REPO_TXT)
    canvas.restoreState()


def cabecera(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 7.4)
    canvas.setFillColor(GRIS_CLARO)
    canvas.drawString(MARGEN_IZQ, PAGINA_ALTO - 10.5 * mm,
                      "Informe del TP U6 por tareas · Facundo Chacón · Comisión 4")
    canvas.setFillColor(AZUL)
    canvas.setFont("Arial-Bold", 7.4)
    canvas.drawRightString(PAGINA_ANCHO - MARGEN_DER, PAGINA_ALTO - 10.5 * mm,
                           "PostgreSQL 17.10 · foodstore")
    canvas.setStrokeColor(colors.HexColor("#C9D3DF"))
    canvas.setLineWidth(0.5)
    canvas.line(MARGEN_IZQ, PAGINA_ALTO - 12.3 * mm,
                PAGINA_ANCHO - MARGEN_DER, PAGINA_ALTO - 12.3 * mm)
    canvas.restoreState()
    pie(canvas, doc)


def portada(canvas, doc):
    pie(canvas, doc)


story = []

# ------------------------------------------------------------- portada -------
banner = Table(
    [[P("Trabajo Práctico Unidad 6", sub_banner)],
     [P("Mantenimiento, respaldo y recuperación de Food Store", titulo_banner)],
     [P("Informe de ejecución dividido por tareas · PostgreSQL 17.10 · Base foodstore",
        sub_banner)]],
    colWidths=[ANCHO], hAlign="LEFT",
)
banner.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), AZUL),
    ("LEFTPADDING", (0, 0), (-1, -1), 9 * mm),
    ("RIGHTPADDING", (0, 0), (-1, -1), 9 * mm),
    ("TOPPADDING", (0, 0), (0, 0), 9 * mm),
    ("BOTTOMPADDING", (0, 2), (0, 2), 9 * mm),
    ("TOPPADDING", (0, 1), (0, 1), 1.5 * mm),
    ("BOTTOMPADDING", (0, 1), (0, 1), 1.5 * mm),
    ("TOPPADDING", (0, 2), (0, 2), 0),
]))
story.append(banner)
story.append(Spacer(1, 4 * mm))

meta = Table(
    [[P("Alumno", meta_b), P("Facundo Chacón", meta_celda),
      P("Materia", meta_b), P("Bases de Datos II · Comisión 4", meta_celda)],
     [P("Motor", meta_b), P("PostgreSQL 17.10 (localhost:5432)", meta_celda),
      P("Base principal", meta_b), P("foodstore", meta_celda)],
     [P("Repositorio", meta_b),
      P(f'<link href="{REPO}" color="#2E6DA4">{REPO}</link>', meta_celda),
      P("Fecha", meta_b), P("2 de noviembre de 2026", meta_celda)]],
    colWidths=[22 * mm, 66 * mm, 24 * mm, 68 * mm], hAlign="LEFT",
)
meta.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), FONDO_SUAVE),
    ("BOX", (0, 0), (-1, -1), 0.4, BORDE),
    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D5DEE9")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
story.append(meta)
story.append(Spacer(1, 6 * mm))

story.append(P("Resumen ejecutivo", seccion))
story.append(P(
    "El trabajo se ejecutó de punta a punta sobre una instancia real de PostgreSQL 17.10. "
    "Se partió del análisis de la consigna y de una especificación escrita, se preparó el entorno con roles "
    "de mínimo privilegio, se respaldó la base con verificación de integridad, se monitoreó su salud, se "
    "ejecutó un mantenimiento justificado por métricas y se realizó un simulacro de desastre completo con "
    "medición de RPO y RTO. Todos los resultados de este informe salen de archivos de evidencia generados "
    "por las mismas corridas: no hay valores estimados ni copiados de una corrida ideal."))
story.append(Spacer(1, 3 * mm))

story.append(P("Mapa de tareas y resultado", seccion))
story.append(tabla(
    ["#", "Tarea", "Entregable principal", "Resultado"],
    [
        ["1", "Análisis de la consigna y especificación", "SPEC_U6.md", "Plan y reglas definidos"],
        ["2", "Preparación del entorno, roles y datos", "soporte/00 y 01, pgpass.conf", "3 roles + bitácora + vista"],
        ["3", "Respaldo lógico con control de falla", "backup_foodstore.ps1", "7,00 MB · 45 objetos · SHA-256"],
        ["4", "Monitoreo de salud", "health_check.sql", "Antes y después comparables"],
        ["5", "Mantenimiento justificado", "maintenance.sql", "5.000 tuplas muertas recuperadas"],
        ["6", "Simulacro de desastre (RPO/RTO)", "restore_test.ps1", "RTO 4,91 s · RPO 658 s · OK"],
        ["7", "Informe, autoevaluación y publicación", "informe_u6.pdf · verificación", "102 PASS / 0 FAIL"],
    ],
    [8, 55, 55, 62], chica=True,
))
story.append(Spacer(1, 3 * mm))
kpis = Table(
    [[P("4,91 s", ParagraphStyle("kpi", fontName="Arial-Bold", fontSize=17, leading=19,
                                 textColor=AZUL, alignment=1)),
      P("658 s", ParagraphStyle("kpi2", fontName="Arial-Bold", fontSize=17, leading=19,
                                textColor=AZUL, alignment=1)),
      P("7/7", ParagraphStyle("kpi3", fontName="Arial-Bold", fontSize=17, leading=19,
                              textColor=AZUL, alignment=1)),
      P("102 / 0", ParagraphStyle("kpi4", fontName="Arial-Bold", fontSize=17, leading=19,
                                  textColor=AZUL, alignment=1))],
     [P("RTO observado<br/>(meta ≤ 20 min)", ParagraphStyle("kl", fontName="Arial", fontSize=7.4,
                                                            leading=9, textColor=GRIS, alignment=1)),
      P("RPO observado<br/>(meta ≤ 24 h)", ParagraphStyle("kl2", fontName="Arial", fontSize=7.4,
                                                           leading=9, textColor=GRIS, alignment=1)),
      P("Conteos validados<br/>contra el snapshot", ParagraphStyle("kl3", fontName="Arial", fontSize=7.4,
                                                                   leading=9, textColor=GRIS, alignment=1)),
      P("Autoevaluación<br/>PASS / FAIL", ParagraphStyle("kl4", fontName="Arial", fontSize=7.4,
                                                         leading=9, textColor=GRIS, alignment=1))]],
    colWidths=[ANCHO / 4] * 4, hAlign="LEFT",
)
kpis.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), FONDO_SUAVE),
    ("LINEABOVE", (0, 0), (-1, 0), 2, AZUL_CLARO),
    ("LINEBEFORE", (0, 0), (0, -1), 0.4, colors.HexColor("#D5DEE9")),
    ("LINEAFTER", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DEE9")),
    ("LINEBELOW", (0, -1), (-1, -1), 0.4, colors.HexColor("#D5DEE9")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, 0), 5),
    ("BOTTOMPADDING", (0, 1), (-1, 1), 5),
    ("TOPPADDING", (0, 1), (-1, 1), 1),
]))
story.append(kpis)

story.append(Spacer(1, 3 * mm))
story.append(P(
    "Cada tarea se presenta con el mismo esquema: consigna, qué se hizo, resultado obtenido, problema real "
    "encontrado con su corrección y evidencias auditables. Los anexos finales concentran el índice de archivos "
    "y los comandos de reproducción."))
story.append(PageBreak())

# -------------------------------------------------------------- tarea 1 ------
story.extend(bloque_tarea(
    "1", "Análisis de la consigna y especificación",
    "Interpretar el escenario, definir el alcance, la frecuencia de cada tarea, las metas de RPO/RTO y las "
    "reglas de seguridad no negociables antes de escribir código.",
    [
        "Se redactó <b>SPEC_U6.md</b> (37 líneas) con alcance explícito: respaldo lógico diario, chequeo de salud, "
        "revisión semanal de mantenimiento y restauración de prueba; quedan fuera el respaldo físico, PITR y replicación.",
        "Se definió una tabla de tareas con frecuencia, herramienta, identidad, condición de éxito y evidencia "
        "verificable para cada una (diaria 02:00, diaria al inicio de jornada, semanal, semanal).",
        "Se fijaron las metas: <b>RPO ≤ 24 h</b> y <b>RTO ≤ 20 min</b>, medidas con datos reales y no con estimaciones.",
        "Se escribieron 7 reglas de seguridad: no tocar foodstore, operaciones destructivas solo en "
        "<b>foodstore_restore_test</b>, contraseñas únicamente en pgpass.conf, mínimo privilegio, prohibición de "
        "<b>VACUUM FULL</b> periódico, aborto ante el primer error y respaldo válido solo si se restaura y valida.",
    ],
    extras=[P(
        "La especificación funciona como contrato: la autoevaluación comprueba automáticamente que el plan mencione "
        "las frecuencias, RPO/RTO, la base descartable, pgpass.conf y la prohibición de VACUUM FULL.")],
    evid="SPEC_U6.md · evidencias/verificacion_entrega.txt (controles de plan, líneas 17 a 24).",
))

# -------------------------------------------------------------- tarea 2 ------
roles = tabla(
    ["Rol", "Privilegios", "Uso y límite"],
    [
        ["mant_backup", "pg_read_all_data + INSERT en mantenimiento.bitacora",
         "Respaldo y snapshot de conteos. Sin escritura sobre datos de negocio."],
        ["mant_monitor", "pg_monitor",
         "health_check.sql: estadísticas, actividad y bloqueos sin acceder a datos."],
        ["mant_restore", "CREATEDB + lectura; CONNECTION LIMIT 10",
         "Simulacro: crea foodstore_restore_test y restaura con -j 4."],
    ],
    [26, 63, 91], chica=True,
)

story.extend(bloque_tarea(
    "2", "Preparación del entorno, roles y datos",
    "Dejar una instancia reproducible: base poblada, identidades de mínimo privilegio, bitácora de operaciones, "
    "compatibilidad de nombres y credenciales fuera del repositorio.",
    [
        f"Se cargó <b>foodstore</b> desde <b>food-store/data.sql</b>: {fmt(conteos['categoria'])} categorías, "
        f"{fmt(conteos['cliente'])} clientes, {fmt(conteos['producto'])} productos, {fmt(conteos['pedido'])} pedidos y "
        f"{fmt(conteos['detalle_pedido'])} líneas de pedido.",
        "Se crearon tres roles de mínimo privilegio y el esquema <b>mantenimiento.bitacora</b> para dejar registro de "
        "cada respaldo, mantenimiento y restauración con fecha, operación, resultado y código de salida.",
        "El modelo real del equipo usa <b>linea_pedido</b> y la consigna nombra <b>detalle_pedido</b>. Se creó la vista "
        "de compatibilidad <b>public.detalle_pedido</b> sobre la tabla real, sin alterar el DDL del proyecto.",
        "Las contraseñas de los roles quedaron solo en <b>%APPDATA%\\postgresql\\pgpass.conf</b>; los scripts usan "
        "<b>pg_dump -w</b> y nunca piden ni imprimen credenciales.",
    ],
    extras=[
        roles,
        Spacer(1, 1.4 * mm),
        P("La preparación es idempotente: los scripts de roles y de entorno pueden volver a ejecutarse sin duplicar "
          "objetos ni romper permisos.", nota),
    ],
    problema=("Decisión de diseño",
             "Se optó por una vista de compatibilidad en lugar de renombrar la tabla del modelo integrador. Así las "
             "validaciones del enunciado funcionan literalmente con detalle_pedido y el esquema del equipo sigue intacto."),
    evid="soporte/00_preparacion_entorno.sql · soporte/01_roles_mantenimiento.sql · soporte/setup_pgpass.ps1 · "
         "evidencias/counts_pre_backup.txt.",
))

# -------------------------------------------------------------- tarea 3 ------
story.append(PageBreak())
respaldo = tabla(
    ["Control", "Valor observado"],
    [
        ["Archivo", f"{m['respaldo_archivo']} (formato custom -Fc, compresión -Z 6)"],
        ["Tamaño y objetos", f"{fmt(m['respaldo_bytes'])} bytes ({mb} MB) · 45 entradas en el TOC"],
        ["Duración", "1,9 s (22:45:00 a 22:45:02)"],
        ["Integridad", f"SHA-256 {m['respaldo_sha256'][:16]}…{m['respaldo_sha256'][-8:]}"],
        ["Bitácora", "Fila OK registrada en mantenimiento.bitacora"],
        ["Retención", "14 días; 0 archivos eliminados en esta corrida"],
    ],
    [40, 140], chica=True,
)

story.extend(bloque_tarea(
    "3", "Respaldo lógico con verificación de integridad",
    "Generar un respaldo restaurable, fechado, con log, sin contraseñas embebidas y con salida distinta de cero "
    "ante cualquier falla.",
    [
        "El script toma un <b>snapshot de conteos antes</b> del respaldo para poder comparar después de restaurar; "
        "ese snapshot es la referencia objetiva del RPO lógico.",
        "Ejecuta <b>pg_dump -Fc -Z 6 -w</b> con el rol <b>mant_backup</b> y escribe primero un archivo <b>.parcial</b>.",
        "Ante error: aborta con código distinto de cero, elimina el <b>.parcial</b> y registra <b>ERROR</b> en el log "
        "y en la bitácora. Nunca deja un archivo incompleto con nombre válido.",
        "Si termina bien: verifica el dump con <b>pg_restore --list</b>, lo renombra con fecha y hora, calcula "
        "<b>SHA-256</b> y aplica retención solo a sus propios archivos.",
    ],
    extras=[
        respaldo,
        Spacer(1, 1.6 * mm),
        P("<b>Prueba de falla ejecutada.</b> Se forzó un error con "
          "<font face='Courier'>-PgDumpExtra '--table=public.tabla_que_no_existe'</font>: pg_dump terminó con "
          "<b>exit 1</b>, el log quedó en <b>ERROR</b>, se eliminó el .parcial y no apareció ningún .dump válido.", cuerpo),
    ],
    problema=("Problema real corregido",
             "El registro en bitácora usaba variables de psql pasadas con -c, que psql no interpola: el INSERT fallaba "
             "y el respaldo quedaba sin trazabilidad. Se cambió a un archivo SQL temporal ejecutado con -f y se verificó "
             "la fila OK en la bitácora."),
    evid="evidencias/backup_ejecucion.log · evidencias/backup_listado.txt · evidencias/backup_sha256.txt · "
         "evidencias/fallo_pg_dump.log · logs/.",
))

# -------------------------------------------------------------- tarea 4 ------
story.append(PageBreak())
salud = tabla(
    ["Indicador", "Antes del mantenimiento", "Después del mantenimiento"],
    [
        ["Tuplas vivas en producto", "50.002", "50.002"],
        ["Tuplas muertas en producto", "5.000", "0"],
        ["Porcentaje de tuplas muertas", "9,09 %", "0,00 %"],
        ["last_vacuum", "(null)", "2026-11-02 22:44:04"],
        ["last_analyze", "2026-11-02 22:39:44", "2026-11-02 22:44:05"],
        ["Tamaño total de producto", "11 MB", "11 MB (sin reescritura)"],
    ],
    [62, 59, 59], chica=True,
)

story.extend(bloque_tarea(
    "4", "Monitoreo de salud de la base",
    "Contar con al menos cuatro controles que permitan detectar degradación antes de que se convierta en incidente.",
    [
        "<b>Tamaño:</b> tamaño de la base y de cada tabla, separando tabla, índices y filas vivas.",
        "<b>Actividad:</b> conexiones actuales contra max_connections, commits y rollbacks, cache hit, lecturas, "
        "deadlocks y uso de archivos temporales.",
        "<b>Estado de tablas:</b> tuplas vivas y muertas, porcentaje de muertas, fechas de vacuum y analyze, "
        "contadores de autovacuum y uso de índices.",
        "<b>Consultas y bloqueos:</b> sesiones activas, consultas lentas, bloqueos y edad del XID; además, antigüedad "
        "del último respaldo OK para vigilar el RPO antes del incidente.",
    ],
    extras=[salud],
    evid="health_check.sql · evidencias/health_check_antes.txt · evidencias/health_check_despues.txt.",
))

# -------------------------------------------------------------- tarea 5 ------
story.extend(bloque_tarea(
    "5", "Mantenimiento justificado por métricas",
    "Observar autovacuum y tuplas muertas, decidir con un umbral documentado y ejecutar solo la acción segura.",
    [
        "Primero se observan los parámetros de autovacuum (activo, scale factor 0,2 / 0,1, threshold 50, "
        "hasta 3 workers, naptime 60 s), las transacciones largas y las estadísticas de cada tabla.",
        "Umbral documentado: se interviene si una tabla tiene <b>≥ 5 % de tuplas muertas y ≥ 1.000 filas</b>, "
        "o <b>≥ 10.000 tuplas muertas</b>. Solo <b>producto</b> calificó, con 5.000 muertas sobre 50.002 (9,09 %).",
        "Se ejecutó <b>VACUUM (ANALYZE)</b> únicamente sobre esa tabla mediante \\gexec: se eliminaron las 5.000 "
        "tuplas muertas, quedaron 50.002 vivas y 0 pendientes. Luego se actualizaron estadísticas.",
        "No se usó <b>VACUUM FULL</b> en ningún momento: bloquearía la tabla y la consigna lo prohíbe como "
        "mantenimiento periódico. La acción y su resultado quedaron en la bitácora.",
    ],
    extras=[P(
        "Lectura del resultado: el espacio no se devuelve al sistema operativo, pero queda disponible para reutilización "
        "dentro de la tabla. Eso es exactamente lo que se busca en un mantenimiento rutinario: recuperar espacio interno "
        "sin bloquear la operación.", nota)],
    problema=("Corrección de criterio",
             "La primera propuesta de la IA fue un VACUUM FULL semanal para “recuperar espacio”. Se rechazó por bloquear "
             "la tabla y violar la consigna; se reemplazó por observación previa y VACUUM (ANALYZE) condicionado."),
    evid="maintenance.sql · evidencias/maintenance_salida.txt · evidencias/health_check_antes.txt y _despues.txt.",
))

# -------------------------------------------------------------- tarea 6 ------
story.append(PageBreak())
simulacro = tabla(
    ["Métrica / control", "Previsto", "Observado", "Cumple"],
    [
        ["RPO (pérdida máxima)", "≤ 24 h (86.400 s)", f"{rpo_txt} de antigüedad", "Sí"],
        ["RTO (recuperación)", "≤ 20 min (1.200 s)", f"{rto} s", "Sí"],
        ["Conteos vs. snapshot", "7/7 coincidentes", "7/7 coincidentes", "Sí"],
        ["Productos / detalles inválidos", "0 / 0", "0 / 0", "Sí"],
        ["Huérfanos referenciales", "0", "0", "Sí"],
        ["Restricciones restauradas", "16", "16", "Sí"],
        ["Vista detalle_pedido", "Presente", "400.002 filas", "Sí"],
    ],
    [55, 47, 58, 20], chica=True,
)

story.extend(bloque_tarea(
    "6", "Simulacro de desastre con RPO y RTO medidos",
    "Restaurar el respaldo en una base descartable, medir el tiempo real y demostrar que los datos y las reglas "
    "lógicas sobrevivieron.",
    [
        "El script valida el dump con <b>pg_restore --list</b>, verifica el <b>SHA-256</b> y ejecuta un <b>preflight</b> "
        "de conexiones antes de crear la base. Aborta si el destino es foodstore o no termina en <b>_restore_test</b>.",
        "Arranca el cronómetro inmediatamente antes de <b>createdb</b> y restaura con "
        "<b>pg_restore --no-owner --no-privileges --exit-on-error -j 4</b> usando <b>mant_restore</b> (CREATEDB, sin superusuario).",
        "Detiene el cronómetro al terminar la última validación. El RPO se calcula como la antigüedad del .dump "
        "respecto del inicio del simulacro.",
        "foodstore nunca se toca: el simulacro corre de principio a fin sobre <b>foodstore_restore_test</b>, que queda "
        "conservada para inspección.",
    ],
    extras=[simulacro, Spacer(1, 1.6 * mm),
            P(f"<b>Conteos validados:</b> {fmt(conteos['categoria'])} categorías, {fmt(conteos['cliente'])} clientes, "
              f"{fmt(conteos['producto'])} productos, {fmt(conteos['pedido'])} pedidos, {fmt(conteos['detalle_pedido'])} "
              f"líneas, suma de cantidades {fmt(conteos['suma_cantidad'])} e importe "
              f"{fmt(int(conteos['suma_importe']))},00.", cuerpo)],
    problema=("Problema real corregido",
             "La primera restauración falló con FATAL: demasiadas conexiones para el rol mant_restore. El rol tenía "
             "CONNECTION LIMIT 2 y pg_restore -j 4 necesita 5 conexiones. El respaldo era válido: se elevó el límite a 10 "
             "de forma idempotente y se agregó al script el preflight que exige al menos -j + 2 conexiones. El simulacro "
             "se repitió con éxito."),
    evid="evidencias/restore_ejecucion.log · evidencias/restore_metrics.json · evidencias/restore_validaciones.txt · "
         "logs/restore_metrics_20261102_225600.json.",
))

# -------------------------------------------------------------- tarea 7 ------
story.append(PageBreak())
commits = tabla(
    ["Commit", "Contenido"],
    [
        ["7dd18a0", "Especificación, roles, respaldo y mantenimiento de Food Store"],
        ["f8731dd", "Simulacro de restauración con RPO/RTO validado"],
        ["557bbc9", "Informe post-incidente, bitácora IA y autoevaluación 102/0"],
    ],
    [24, 156], chica=True,
)

story.extend(bloque_tarea(
    "7", "Informe, autoevaluación y publicación",
    "Documentar el procedimiento y los resultados, verificar la entrega contra la consigna y publicar todo en el "
    "repositorio del equipo.",
    [
        "Se redactó <b>informe_u6.pdf</b>, de una página, con respaldo utilizado, RPO/RTO previstos y observados, "
        "validación, problema real, mejora concreta y uso de IA.",
        "Se documentó el uso de IA en <b>BITACORA_IA.md</b>: 12 propuestas de OpenCode con la revisión humana y la "
        "corrección aplicada a cada una (seguridad, VACUUM FULL, borrado automático, nombres de tablas, rutas, "
        "paralelismo, credenciales y errores encontrados en ejecución).",
        "Se ejecutó <b>soporte/verificar_entrega.ps1</b> contra la entrega completa: <b>102 PASS / 0 FAIL</b>, "
        "incluyendo archivos, ausencia de contraseñas, ausencia de VACUUM FULL, evidencias y métricas del simulacro.",
        f"Todo quedó publicado en <b>{REPO_TXT}</b>, rama <b>master</b>, en tres commits descriptivos.",
    ],
    extras=[
        commits,
        Spacer(1, 2 * mm),
        P("<b>Repositorio:</b> " + f'<link href="{REPO}" color="#2E6DA4">{REPO}</link>', cuerpo),
        P("<b>Informe de una página:</b> TP6_U6_Mantenimiento_FoodStore/informe_u6.pdf", cuerpo),
        P("<b>Este informe por tareas:</b> TP6_U6_Mantenimiento_FoodStore/informe_u6_tareas.pdf", cuerpo),
    ],
    evid="informe_u6.pdf · BITACORA_IA.md · evidencias/verificacion_entrega.txt · git log (rama master).",
))

# ------------------------------------------------------------- cierre --------
story.append(Spacer(1, 6 * mm))
cierre = Table(
    [[P("<b>Conclusión.</b> El procedimiento quedó completo y verificable: respaldo con integridad comprobada, "
        "prueba de falla exitosa, monitoreo con cuatro bloques de control, mantenimiento decidido por métricas, "
        "restauración real en 4,91 s y validación 7/7 con cero inconsistencias. La base principal nunca se tocó y "
        "ninguna credencial quedó en el repositorio. El siguiente paso natural es programar el respaldo diario y el "
        "chequeo de salud con el Programador de tareas, y alertar cuando el último respaldo OK supere las 20 h.",
        ParagraphStyle("cierre_txt", fontName="Arial", fontSize=8.9, leading=11.6,
                       textColor=colors.HexColor("#22364D")))]],
    colWidths=[ANCHO], hAlign="LEFT",
)
cierre.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), FONDO),
    ("LINEBEFORE", (0, 0), (0, -1), 2.4, AZUL),
    ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(cierre)

# ------------------------------------------------------------- anexos --------
story.append(PageBreak())
story.append(P("Anexo A · Índice de evidencias", seccion))
story.append(P("Cada resultado del informe se puede auditar en el archivo correspondiente dentro de la entrega."))
story.append(Spacer(1, 1.5 * mm))
story.append(tabla(
    ["Archivo", "Qué demuestra"],
    [
        ["evidencias/backup_ejecucion.log", "Respaldo OK: 7.338.155 bytes, 45 objetos, SHA-256 y bitácora."],
        ["evidencias/backup_listado.txt", "El dump se puede leer con pg_restore --list."],
        ["evidencias/backup_sha256.txt", "Huella SHA-256 del archivo de respaldo."],
        ["evidencias/fallo_pg_dump.log", "Prueba de falla: exit 1, ERROR y sin .dump válido."],
        ["evidencias/health_check_antes.txt", "Estado previo: producto con 5.000 tuplas muertas (9,09 %)."],
        ["evidencias/health_check_despues.txt", "Estado posterior: 0 tuplas muertas y ANALYZE actualizado."],
        ["evidencias/maintenance_salida.txt", "Observación de autovacuum y VACUUM (ANALYZE) justificado."],
        ["evidencias/restore_ejecucion.log", "Simulacro completo con preflight y RTO/RPO observados."],
        ["evidencias/restore_metrics.json", "Métricas finales: RTO 4,91 s, RPO 658 s, validaciones OK."],
        ["evidencias/restore_validaciones.txt", "7/7 conteos, invalid=0, huérfanos=0, 16 restricciones y vista."],
        ["evidencias/counts_pre_backup.txt", "Snapshot de conteos previo al respaldo."],
        ["evidencias/verificacion_entrega.txt", "Autoevaluación: 102 PASS / 0 FAIL."],
    ],
    [66, 114], chica=True,
))
story.append(Spacer(1, 5 * mm))

story.append(P("Anexo B · Reproducción", seccion))
story.append(P("Los comandos se ejecutan desde la raíz de la carpeta del TP. Requieren PostgreSQL 16+ y pgpass.conf configurado."))
story.append(Spacer(1, 1.5 * mm))

comandos = [
    ("Respaldo diario", ".\\backup_foodstore.ps1"),
    ("Salud antes/después", "psql -h localhost -U mant_monitor -d foodstore -X -f .\\health_check.sql"),
    ("Mantenimiento", "psql -h localhost -U postgres -d foodstore -X -f .\\maintenance.sql"),
    ("Simulacro", ".\\restore_test.ps1 -Force"),
    ("Autoevaluación", ".\\soporte\\verificar_entrega.ps1"),
]
cmd = Table(
    [[P("<b>Paso</b>", celda_chica_b), P("<b>Comando</b>", celda_chica_b)]] +
    [[P(p, celda_chica), P(c, ParagraphStyle("mono", fontName="Courier", fontSize=7.6, leading=9.4))]
     for p, c in comandos],
    colWidths=[36 * mm, 144 * mm], hAlign="LEFT",
)
cmd.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.35, BORDE),
    ("BACKGROUND", (0, 0), (-1, 0), FONDO),
    ("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#F7F8FA")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
story.append(cmd)
story.append(Spacer(1, 4 * mm))
story.append(P(
    f"Repositorio: <link href='{REPO}' color='#2E6DA4'>{REPO}</link> · Rama master · "
    f"Último commit de la entrega: 557bbc9.", nota))

# ---------------------------------------------------------------- build ------
doc = SimpleDocTemplate(
    SALIDA,
    pagesize=A4,
    leftMargin=MARGEN_IZQ,
    rightMargin=MARGEN_DER,
    topMargin=MARGEN_SUP,
    bottomMargin=MARGEN_INF,
    title="Informe del TP U6 por tareas - Mantenimiento Food Store",
    author="Facundo Chacón",
    subject="Mantenimiento, respaldo y recuperación - PostgreSQL 17.10",
    keywords="PostgreSQL, pg_dump, pg_restore, RPO, RTO, VACUUM, Food Store",
)
doc.build(story, onFirstPage=portada, onLaterPages=cabecera)
print(f"PDF generado: {SALIDA}")
print(f"Páginas: {doc.page}")
