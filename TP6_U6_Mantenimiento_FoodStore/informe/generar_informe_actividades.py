# ============================================================================
# generar_informe_actividades.py - genera informe_u6_actividades.pdf, el
# informe del TP U6 organizado por las actividades (Partes 1 a 5) de la
# consigna oficial, con los resultados reales registrados en evidencias/.
#
# Uso (desde la raíz del TP):
#   python informe/generar_informe_actividades.py
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
SALIDA = os.path.join(ROOT, "informe_u6_actividades.pdf")
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
titulo_banner = ParagraphStyle("titulo_banner", fontName="Arial-Bold", fontSize=19.5,
                               leading=22.5, textColor=colors.white)
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


def encabezado_actividad(numero, titulo, parte):
    fila = Table(
        [[P(f"<font size=15>{numero}</font>", ParagraphStyle(
            "num", fontName="Arial-Bold", fontSize=15, leading=17,
            textColor=colors.white)),
          P(f"<b>{titulo}</b><br/><font size=7.6 color='#C9D8EA'>{parte}</font>",
            ParagraphStyle("tt", fontName="Arial-Bold", fontSize=11.3, leading=13.5,
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
    t = Table(
        [[P(f"<b>{etiqueta}</b>", ParagraphStyle(
            "call_lbl", fontName="Arial-Bold", fontSize=8.3, leading=10,
            textColor=AMBAR)),
          P(texto, ParagraphStyle(
              "call_txt", fontName="Arial", fontSize=8.6, leading=11,
              textColor=colors.HexColor("#4A3A22")))]],
        colWidths=[29 * mm, ANCHO - 29 * mm],
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


def bloque_actividad(numero, titulo, parte, consigna, hechos, extras=(),
                     problema=None, evid=None):
    partes = [Spacer(1, 5 * mm), encabezado_actividad(numero, titulo, parte),
              Spacer(1, 2.4 * mm)]
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
    canvas.setFillColor(AZUL_CLARO)
    canvas.drawString(MARGEN_IZQ, 5.4 * mm, REPO_TXT)
    canvas.restoreState()


def cabecera(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 7.4)
    canvas.setFillColor(GRIS_CLARO)
    canvas.drawString(MARGEN_IZQ, PAGINA_ALTO - 10.5 * mm,
                      "Informe por actividades · Facundo Chacón · Comisión 4")
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
     [P("Informe de lo realizado en cada actividad · PostgreSQL 17.10 · Base foodstore",
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

story.append(P("Resumen del trabajo", seccion))
story.append(P(
    "El TP se resolvió sobre una instancia real de PostgreSQL 17.10 siguiendo las cinco actividades de la "
    "consigna: primero la especificación y el plan, después el respaldo, luego el monitoreo y el mantenimiento, "
    "a continuación el simulacro de desastre contra reloj y, por último, el informe post-incidente con la "
    "verificación del trabajo asistido por OpenCode. Cada apartado de este documento indica qué pedía la "
    "actividad, qué se hizo, cuál fue el resultado medido y en qué archivo se puede auditar."))
story.append(Spacer(1, 3 * mm))

story.append(P("Las cinco actividades y su resultado", seccion))
story.append(tabla(
    ["#", "Actividad de la consigna", "Entregable", "Resultado"],
    [
        ["1", "Parte 1 · Especificación y plan de mantenimiento", "SPEC_U6.md",
         "Plan de 4 tareas con frecuencia y evidencia"],
        ["2", "Parte 2 · Respaldo automatizable", "backup_foodstore.ps1",
         "7,00 MB · 45 objetos · SHA-256 · prueba de falla"],
        ["3", "Parte 3 · Monitoreo y mantenimiento", "health_check.sql + maintenance.sql",
         "4 bloques de control · 5.000 tuplas recuperadas"],
        ["4", "Parte 4 · Simulacro de desastre contra reloj", "restore_test.ps1",
         "RTO 4,91 s · RPO 658 s · 7/7 conteos"],
        ["5", "Parte 5 · Informe post-incidente y uso de IA", "informe_u6.pdf + BITACORA_IA.md",
         "1 página · 102 PASS / 0 FAIL"],
    ],
    [8, 62, 58, 52], chica=True,
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
    "El repositorio con todos los archivos, scripts y evidencias es "
    f'<link href="{REPO}" color="#2E6DA4">{REPO}</link>. Las salidas crudas están en '
    "<b>evidencias/</b>; los scripts pueden volver a ejecutarse siguiendo el Anexo B."))
story.append(PageBreak())

# ---------------------------------------------------------- actividad 1 ------
plan = tabla(
    ["Tarea mínima", "Frecuencia", "Condición que confirma el éxito", "Evidencia"],
    [
        ["Respaldo de foodstore", "Diaria, 02:00",
         "pg_dump termina en 0, el dump se lista, se calcula SHA-256 y se registra en bitácora.",
         ".dump fechado + log + .sha256"],
        ["Chequeo de salud", "Diaria, inicio de jornada",
         "Devuelve tamaño, actividad de conexiones, estado de tablas y consultas activas.",
         "Salida de health_check.sql"],
        ["Revisión de mantenimiento", "Semanal",
         "Se observan tuplas muertas y autovacuum; solo se interviene si se supera el umbral.",
         "Salida antes/después + bitácora"],
        ["Restauración de prueba", "Semanal",
         "foodstore_restore_test se crea, restaura y supera conteos e invalid=0.",
         "Log + métricas RTO/RPO"],
    ],
    [30, 28, 78, 44], chica=True,
)

reglas = tabla(
    ["#", "Regla de seguridad no negociable"],
    [
        ["1", "foodstore no se elimina, reemplaza ni se restaura durante el simulacro."],
        ["2", "Toda operación destructiva se limita a foodstore_restore_test; el script aborta si el destino no termina en _restore_test."],
        ["3", "Ninguna contraseña se escribe en scripts, SQL, logs ni repositorio: se usa %APPDATA%\\postgresql\\pgpass.conf."],
        ["4", "Roles de mínimo privilegio: mant_backup (lectura), mant_monitor (pg_monitor) y mant_restore (CREATEDB + lectura)."],
        ["5", "VACUUM FULL queda prohibido como mantenimiento periódico; solo se admite VACUUM (ANALYZE) justificado."],
        ["6", "Todo script aborta ante el primer error y deja un log con fecha, operación, resultado y código de salida."],
        ["7", "Un respaldo no se considera válido hasta que se restaura y se validan cantidades y reglas lógicas."],
    ],
    [7, 173], chica=True,
)

story.extend(bloque_actividad(
    "1", "Especificación y plan de mantenimiento", "Parte 1 de la consigna",
    "Crear SPEC_U6.md (máximo una página) indicando qué se automatiza, con qué frecuencia y qué condición "
    "confirma que cada tarea terminó correctamente.",
    [
        "Se redactó <b>SPEC_U6.md</b> en 37 líneas con alcance, tabla de tareas, metas de RPO/RTO, reglas de "
        "seguridad y criterios de aceptación.",
        "Se definieron las cuatro tareas mínimas con frecuencia, identidad, condición de éxito y evidencia "
        "verificable; no se automatizan decisiones de intervención, solo la observación y la ejecución segura.",
        "Se fijaron las metas del laboratorio: <b>RPO ≤ 24 h</b> y <b>RTO ≤ 20 min</b>, con medición real y no "
        "estimada. Quedaron fuera de alcance el respaldo físico, PITR y la replicación.",
    ],
    extras=[
        plan,
        Spacer(1, 2 * mm),
        P("Reglas de seguridad que gobiernan todo el procedimiento", celda_b),
        Spacer(1, 1.2 * mm),
        reglas,
    ],
    problema=("Cómo se verificó",
             "La especificación se usó como contrato: soporte/verificar_entrega.ps1 comprueba automáticamente que "
             "mencione las frecuencias, RPO/RTO, la base descartable, pgpass.conf y la prohibición de VACUUM FULL. "
             "Los 7 controles de plan quedaron en PASS."),
    evid="SPEC_U6.md · evidencias/verificacion_entrega.txt (controles de plan).",
))

# ---------------------------------------------------------- actividad 2 ------
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

story.extend(bloque_actividad(
    "2", "Respaldo automatizable", "Parte 2 de la consigna",
    "Crear backup_foodstore.ps1 para generar un respaldo custom de foodstore, con fecha y hora en el nombre, "
    "registro en logs, error si pg_dump falla y sin contraseñas embebidas.",
    [
        "El script toma un <b>snapshot de conteos antes</b> del respaldo y ejecuta "
        "<b>pg_dump -Fc -Z 6 -w</b> con el rol <b>mant_backup</b>, escribiendo primero un archivo <b>.parcial</b>.",
        "Si pg_dump falla: aborta con código distinto de cero, elimina el <b>.parcial</b> y registra <b>ERROR</b> "
        "en el log y en la bitácora; nunca deja un archivo incompleto con nombre válido.",
        "Si termina bien: verifica el dump con <b>pg_restore --list</b>, lo renombra con fecha y hora, calcula "
        "<b>SHA-256</b> y aplica retención solo a sus propios archivos.",
        "Se ejecutó manualmente antes de considerarlo apto y se probó el camino de error con una tabla inexistente.",
    ],
    extras=[
        respaldo,
        Spacer(1, 1.6 * mm),
        P("<b>Prueba de falla ejecutada.</b> Con "
          "<font face='Courier'>-PgDumpExtra '--table=public.tabla_que_no_existe'</font>, pg_dump terminó con "
          "<b>exit 1</b>, el log quedó en <b>ERROR</b>, se eliminó el .parcial y no apareció ningún .dump válido.", cuerpo),
    ],
    problema=("Problema real corregido",
              "El registro en bitácora usaba variables de psql pasadas con -c, que psql no interpola: el INSERT "
              "fallaba y el respaldo quedaba sin trazabilidad. Se cambió a un archivo SQL temporal ejecutado con -f "
              "y se verificó la fila OK en la bitácora."),
    evid="evidencias/backup_ejecucion.log · evidencias/backup_listado.txt · evidencias/backup_sha256.txt · "
         "evidencias/fallo_pg_dump.log.",
))

# ---------------------------------------------------------- actividad 3 ------
story.append(PageBreak())
parametros = tabla(
    ["Parámetro observado", "Valor", "Lectura"],
    [
        ["autovacuum", "on", "El proceso automático está habilitado."],
        ["autovacuum_vacuum_scale_factor", "0,2", "Umbral relativo alto: con tablas grandes tarda en actuar."],
        ["autovacuum_analyze_scale_factor", "0,1", "Estadísticas se actualizan al 10 % de cambios."],
        ["autovacuum_vacuum_threshold", "50", "Margen fijo adicional de tuplas muertas."],
        ["autovacuum_naptime", "60 s", "Frecuencia de revisión del proceso."],
        ["autovacuum_max_workers", "3", "Cantidad de workers disponibles."],
    ],
    [46, 16, 118], chica=True,
)

salud = tabla(
    ["Indicador", "Antes", "Después"],
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

story.extend(bloque_actividad(
    "3", "Monitoreo y mantenimiento", "Parte 3 de la consigna",
    "Crear health_check.sql con al menos cuatro controles (tamaño, conexiones, estado de tablas y consultas "
    "activas) y maintenance.sql con revisión de autovacuum/ANALYZE más una acción segura y justificada, sin "
    "VACUUM FULL periódico.",
    [
        "<b>Monitoreo:</b> health_check.sql cubre tamaño de base y tablas; conexiones, commits/rollbacks, cache hit, "
        "deadlocks y temporales; tuplas vivas/muertas, vacuum y analyze; consultas activas, bloqueos y edad del XID. "
        "Además controla la antigüedad del último respaldo OK para vigilar el RPO.",
        "<b>Observación previa:</b> maintenance.sql revisa los parámetros de autovacuum, transacciones largas y "
        "estadísticas por tabla antes de decidir.",
        "<b>Umbral documentado:</b> se interviene si una tabla tiene ≥ 5 % de tuplas muertas y ≥ 1.000 filas, o "
        "≥ 10.000 tuplas muertas. Solo <b>producto</b> calificó, con 5.000 muertas sobre 50.002 (9,09 %).",
        "<b>Acción segura:</b> se ejecutó <b>VACUUM (ANALYZE)</b> solo sobre esa tabla mediante \\gexec: se eliminaron "
        "las 5.000 tuplas muertas, quedaron 50.002 vivas y 0 pendientes. No se usó VACUUM FULL.",
    ],
    extras=[
        parametros,
        Spacer(1, 1.6 * mm),
        salud,
    ],
    problema=("Corrección de criterio",
              "La primera propuesta de la IA fue un VACUUM FULL semanal para “recuperar espacio”. Se rechazó porque "
              "bloquea la tabla y la consigna lo prohíbe como mantenimiento periódico; se reemplazó por observación "
              "previa y VACUUM (ANALYZE) condicionado."),
    evid="health_check.sql · maintenance.sql · evidencias/health_check_antes.txt · "
         "evidencias/health_check_despues.txt · evidencias/maintenance_salida.txt.",
))

# ---------------------------------------------------------- actividad 4 ------
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

story.extend(bloque_actividad(
    "4", "Simulacro de desastre contra reloj", "Parte 4 de la consigna",
    "Restaurar el último respaldo en foodstore_restore_test, cronometrar desde antes de createdb hasta terminar "
    "las validaciones, comparar conteos con el snapshot previo y calcular RTO y RPO observados.",
    [
        "El script valida el dump con <b>pg_restore --list</b>, verifica el <b>SHA-256</b> y ejecuta un <b>preflight</b> "
        "de conexiones antes de crear la base. Aborta si el destino es foodstore o no termina en <b>_restore_test</b>.",
        "Arranca el cronómetro inmediatamente antes de <b>createdb</b> y restaura con "
        "<b>pg_restore --no-owner --no-privileges --exit-on-error -j 4</b> usando <b>mant_restore</b> "
        "(CREATEDB, sin superusuario).",
        "Detiene el cronómetro al terminar la última validación. El RPO se calcula como la antigüedad del .dump "
        "respecto del inicio del simulacro.",
        "foodstore nunca se toca: el simulacro corre de principio a fin sobre <b>foodstore_restore_test</b>, que "
        "queda conservada para inspección.",
    ],
    extras=[
        simulacro,
        Spacer(1, 1.6 * mm),
        P(f"<b>Conteos validados:</b> {fmt(conteos['categoria'])} categorías, {fmt(conteos['cliente'])} clientes, "
          f"{fmt(conteos['producto'])} productos, {fmt(conteos['pedido'])} pedidos, {fmt(conteos['detalle_pedido'])} "
          f"líneas, suma de cantidades {fmt(conteos['suma_cantidad'])} e importe "
          f"{fmt(int(conteos['suma_importe']))},00.", cuerpo),
    ],
    problema=("Problema real corregido",
              "La primera restauración falló con FATAL: demasiadas conexiones para el rol mant_restore. El rol tenía "
              "CONNECTION LIMIT 2 y pg_restore -j 4 necesita 5 conexiones. El respaldo era válido: se elevó el límite "
              "a 10 de forma idempotente y se agregó al script el preflight que exige al menos -j + 2 conexiones. "
              "El simulacro se repitió con éxito."),
    evid="evidencias/restore_ejecucion.log · evidencias/restore_metrics.json · "
         "evidencias/restore_validaciones.txt.",
))

# ---------------------------------------------------------- actividad 5 ------
story.append(PageBreak())
informe_check = tabla(
    ["Requisito del informe de una página", "Dónde se cumple"],
    [
        ["Fecha y hora del respaldo utilizado", "informe_u6.pdf §1: 2026-11-02 22:45:00–22:45:02"],
        ["Tiempo total de restauración y validación", "§2: RTO 4,91 s"],
        ["RPO y RTO previstos y observados", "§2: ≤ 24 h / 658 s y ≤ 20 min / 4,91 s"],
        ["Validaciones de tablas y restricciones lógicas", "§3: 7/7 conteos, invalid=0, huérfanos=0, 16 restricciones"],
        ["Problema real encontrado", "§4: límite de conexiones de mant_restore"],
        ["Mejora concreta para la siguiente ejecución", "§5: preflight de conexiones y alerta de antigüedad del respaldo"],
        ["Uso de OpenCode y verificación", "§6 y BITACORA_IA.md: 12 propuestas revisadas y probadas"],
    ],
    [66, 114], chica=True,
)

ia = tabla(
    ["Propuesta inicial de la IA", "Revisión humana y corrección aplicada"],
    [
        ["Contraseña embebida y usuario postgres", "Rechazada: se usó mant_backup y pgpass.conf, sin credenciales en el repo."],
        ["VACUUM FULL semanal", "Rechazada: bloquea la tabla; se reemplazó por VACUUM (ANALYZE) justificado."],
        ["Borrar foodstore_restore_test al finalizar", "Ajustada: no se borra automáticamente; la limpieza es manual."],
        ["Restaurar como superusuario", "Ajustada: mant_restore con CREATEDB y sin superusuario."],
        ["CONNECTION LIMIT 2 con -j 4", "Corregida en ejecución: límite 10 y preflight de conexiones."],
    ],
    [62, 118], chica=True,
)

story.extend(bloque_actividad(
    "5", "Informe post-incidente y uso de IA", "Parte 5 de la consigna",
    "Entregar un informe de una página con fecha y hora del respaldo, tiempo de restauración, RPO/RTO previstos "
    "y observados, validaciones, problema real, mejora concreta e indicación del trabajo asistido por OpenCode.",
    [
        "Se redactó <b>informe_u6.pdf</b>, de una página, con los siete puntos exigidos y el link del repositorio.",
        "Se documentó el uso de IA en <b>BITACORA_IA.md</b>: 12 propuestas de OpenCode con la revisión humana y la "
        "corrección aplicada a cada una, incluyendo los errores que aparecieron recién al ejecutar.",
        "Se ejecutó <b>soporte/verificar_entrega.ps1</b> contra la entrega completa: <b>102 PASS / 0 FAIL</b>, "
        "incluyendo archivos, ausencia de contraseñas, ausencia de VACUUM FULL, evidencias y métricas.",
    ],
    extras=[
        informe_check,
        Spacer(1, 2 * mm),
        P("Ejemplos de revisión humana sobre lo propuesto por la IA", celda_b),
        Spacer(1, 1.2 * mm),
        ia,
    ],
    problema=("Mejora aplicada",
              "Además del preflight de conexiones, se dejó como paso siguiente alertar cuando el último respaldo OK "
              "supere las 20 h (margen sobre el RPO de 24 h), para detectar el riesgo antes del incidente y no "
              "después."),
    evid="informe_u6.pdf · BITACORA_IA.md · evidencias/verificacion_entrega.txt.",
))

# ------------------------------------------------------- cierre/entrega ------
story.append(PageBreak())
entregables = tabla(
    ["Entregable de la consigna", "Estado", "Ubicación"],
    [
        ["SPEC_U6.md", "Completo", "SPEC_U6.md (37 líneas)"],
        ["backup_foodstore.ps1 o .sh", "Completo y probado", "backup_foodstore.ps1"],
        ["health_check.sql", "Completo (4+ controles)", "health_check.sql"],
        ["maintenance.sql", "Completo y justificado", "maintenance.sql"],
        ["restore_test.ps1 o .sh (opcional)", "Completo", "restore_test.ps1"],
        ["informe_u6.pdf", "Completo (1 página)", "informe_u6.pdf"],
        ["Evidencias y bitácora", "Completo", "evidencias/, logs/, BITACORA_IA.md"],
    ],
    [58, 42, 80], chica=True,
)

rubrica = tabla(
    ["Criterio de evaluación", "Peso", "Cómo se cubrió"],
    [
        ["Especificación clara y plan coherente", "2,0", "SPEC de 37 líneas con tareas, frecuencia, RPO/RTO y reglas."],
        ["Respaldo automatizable, seguro y probado", "2,0", "pg_dump -Fc, SHA-256, logs, bitácora y prueba de falla."],
        ["Monitoreo y mantenimiento correctos", "2,0", "Cuatro bloques de control y VACUUM (ANALYZE) justificado."],
        ["Restauración, validaciones y RPO/RTO", "3,0", "4,91 s y 658 s; 7/7 conteos; invalid=0 y huérfanos=0."],
        ["Informe breve, evidencias y verificación de IA", "1,0", "Informe de 1 página, BITACORA_IA y 102 PASS / 0 FAIL."],
    ],
    [72, 14, 94], chica=True,
)

story.append(Spacer(1, 5 * mm))
story.append(P("Cumplimiento de entregables y criterios", ParagraphStyle(
    "sec2", fontName="Arial-Bold", fontSize=11.5, leading=13.5, textColor=AZUL,
    spaceBefore=0, spaceAfter=2)))
story.append(P("La tabla siguiente contrasta lo pedido por la cátedra con lo efectivamente entregado y verificado."))
story.append(Spacer(1, 2 * mm))
story.append(entregables)
story.append(Spacer(1, 3 * mm))
story.append(P("Criterios de evaluación de la consigna", seccion))
story.append(rubrica)

story.append(Spacer(1, 5 * mm))
cierre = Table(
    [[P("<b>Conclusión.</b> Las cinco actividades quedaron completas y verificables: plan escrito, respaldo con "
        "integridad comprobada y prueba de falla, monitoreo con cuatro bloques, mantenimiento decidido por métricas, "
        "restauración real en 4,91 s con validación 7/7 y un informe de una página con la intervención de OpenCode "
        "documentada. La base foodstore nunca se tocó y ninguna credencial quedó en el repositorio. La autoevaluación "
        "cerró con 102 PASS / 0 FAIL.",
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
story.append(Spacer(1, 3 * mm))
story.append(P(f'<b>Repositorio:</b> <link href="{REPO}" color="#2E6DA4">{REPO}</link> · '
               "rama <b>master</b> · el informe de una página se mantiene como entrega oficial de la Parte 5.", cuerpo))

# ------------------------------------------------------------- anexo ---------
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
    "Informe oficial de la Parte 5: informe_u6.pdf (1 página).", nota))

# ---------------------------------------------------------------- build ------
doc = SimpleDocTemplate(
    SALIDA,
    pagesize=A4,
    leftMargin=MARGEN_IZQ,
    rightMargin=MARGEN_DER,
    topMargin=MARGEN_SUP,
    bottomMargin=MARGEN_INF,
    title="Informe por actividades - TP U6 Mantenimiento Food Store",
    author="Facundo Chacón",
    subject="Mantenimiento, respaldo y recuperación - PostgreSQL 17.10",
    keywords="PostgreSQL, pg_dump, pg_restore, RPO, RTO, VACUUM, Food Store, actividades",
)
doc.build(story, onFirstPage=portada, onLaterPages=cabecera)
print(f"PDF generado: {SALIDA}")
print(f"Páginas: {doc.page}")
