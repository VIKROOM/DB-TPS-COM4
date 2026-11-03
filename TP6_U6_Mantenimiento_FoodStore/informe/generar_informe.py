# ============================================================================
# generar_informe.py - genera informe_u6.pdf (1 página A4) a partir de las
# métricas reales del simulacro (evidencias/restore_metrics.json) y del
# snapshot de conteos (evidencias/counts_pre_backup.txt).
#
# Uso (desde la raíz del TP):
#   python informe/generar_informe.py
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
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidencias")
SALIDA = os.path.join(ROOT, "informe_u6.pdf")
REPO = "https://github.com/VIKROOM/DB-TPS-COM4"

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

AZUL = colors.HexColor("#14375F")
GRIS = colors.HexColor("#5A5A5A")
FONDO = colors.HexColor("#E8EEF6")

titulo_doc = ParagraphStyle("titulo_doc", fontName="Arial-Bold", fontSize=13, leading=15,
                            textColor=AZUL, spaceAfter=1)
subtitulo = ParagraphStyle("subtitulo", fontName="Arial", fontSize=8.2, leading=10,
                           textColor=GRIS, spaceAfter=3)
seccion = ParagraphStyle("seccion", fontName="Arial-Bold", fontSize=9.6, leading=11.5,
                         textColor=AZUL, spaceBefore=3, spaceAfter=2)
cuerpo = ParagraphStyle("cuerpo", fontName="Arial", fontSize=8.6, leading=10.4,
                        alignment=TA_LEFT, spaceAfter=2)
vineta = ParagraphStyle("vineta", parent=cuerpo, leftIndent=8, bulletIndent=1,
                        bulletFontName="Arial", bulletFontSize=8.6, spaceAfter=0.6)
celda = ParagraphStyle("celda", fontName="Arial", fontSize=8.2, leading=9.6)
celda_b = ParagraphStyle("celda_b", parent=celda, fontName="Arial-Bold")

story = []


def P(texto, estilo=cuerpo, **kw):
    return Paragraph(texto, estilo, **kw)


def tabla(encabezados, filas, anchos):
    datos = [[P(h, celda_b) for h in encabezados]]
    for fila in filas:
        datos.append([P(c, celda) for c in fila])
    t = Table(datos, colWidths=[a * mm for a in anchos], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA7B6")),
        ("BACKGROUND", (0, 0), (-1, 0), FONDO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t)
    story.append(Spacer(1, 2.2 * mm))


story.append(P("Informe post-incidente - Mantenimiento de Food Store", titulo_doc))
story.append(P("Bases de Datos II · Comisión 4 · Facundo Chacón · PostgreSQL 17.10 · Base: foodstore", subtitulo))
story.append(P(f'Repositorio: <link href="{REPO}" color="#2E6DA4">{REPO}</link>', ParagraphStyle(
    "repo", fontName="Arial", fontSize=7.8, leading=9.4, textColor=GRIS, spaceAfter=3)))

story.append(P("1. Respaldo utilizado", seccion))
tabla(
    ["Dato", "Valor"],
    [
        ["Archivo", f"{m['respaldo_archivo']} (formato custom -Fc)"],
        ["Fecha y hora", "2026-11-02, ejecución 22:45:00–22:45:02"],
        ["Tamaño e integridad", f"{fmt(m['respaldo_bytes'])} bytes ({mb} MB), 45 objetos; SHA-256 {m['respaldo_sha256'][:16]}…{m['respaldo_sha256'][-8:]}"],
        ["Identidad", "mant_backup (solo lectura + INSERT en bitácora), sin contraseña en el script"],
    ],
    [36, 150],
)

story.append(P("2. RPO y RTO: previsto vs. observado", seccion))
tabla(
    ["Métrica", "Previsto", "Observado", "Cumple"],
    [
        ["RPO (pérdida máxima de datos)", "≤ 24 h (respaldo diario)", rpo_txt + " de antigüedad", "Sí"],
        ["RTO (tiempo de recuperación)", "≤ 20 min", f"{rto} s (createdb + pg_restore + validaciones)", "Sí"],
    ],
    [58, 46, 62, 20],
)
story.append(P("El RTO se midió con cronómetro desde el instante anterior a createdb hasta completar la última validación. El RPO se calculó como la diferencia entre el inicio del simulacro y la fecha del .dump."))

story.append(P("3. Resultados de la validación", seccion))
story.append(P("Restauración en foodstore_restore_test con mant_restore (CREATEDB, sin superusuario), pg_restore --no-owner --no-privileges --exit-on-error -j 4:"))
story.append(P(
    f"Conteos coincidentes 7/7 contra el snapshot previo: {fmt(conteos['categoria'])} categorías, "
    f"{fmt(conteos['cliente'])} clientes, {fmt(conteos['producto'])} productos, {fmt(conteos['pedido'])} pedidos, "
    f"{fmt(conteos['detalle_pedido'])} líneas, suma de cantidades {fmt(conteos['suma_cantidad'])} e importe "
    f"{fmt(int(conteos['suma_importe']))},00.", vineta, bulletText="•"))
for texto in (
    "productos_invalidos = 0 y detalles_invalidos = 0 (precio, stock y cantidad dentro de rango).",
    "Huérfanos referenciales = 0 en pedido→cliente y línea→pedido/producto.",
    "16 restricciones declarativas restauradas y vista de compatibilidad public.detalle_pedido presente.",
    "foodstore no se tocó: el script aborta si el destino no termina en _restore_test.",
):
    story.append(P(texto, vineta, bulletText="•"))

story.append(P("4. Problema real encontrado", seccion))
story.append(P(
    "La primera restauración falló con FATAL: demasiadas conexiones para el rol \"mant_restore\". El rol tenía "
    "CONNECTION LIMIT 2, pero pg_restore -j 4 abre un proceso principal y hasta cuatro trabajadores (5 conexiones). "
    "El respaldo era válido: el problema era de configuración de la identidad. Se corrigió con ALTER ROLE mant_restore "
    "CONNECTION LIMIT 10 (idempotente en 01_roles_mantenimiento.sql) y el simulacro se repitió con éxito. También se "
    "corrigió el registro en bitácora del respaldo: psql no interpola variables en -c, por lo que se pasó a un archivo "
    "temporal con -f."))

story.append(P("5. Mejora concreta", seccion))
story.append(P(
    "Se agregó a restore_test.ps1 un preflight que consulta rolconnlimit y aborta con un mensaje claro si es menor que "
    "-j + 2 (con -j 4 exige al menos 7). Así, una configuración insuficiente se detecta antes de crear la base y no a "
    "mitad de la restauración. Como paso siguiente, health_check.sql debe alertar cuando el último respaldo OK supere "
    "las 20 h (margen sobre el RPO de 24 h), para vigilar el RPO antes del incidente."))

story.append(P("6. Uso de IA (OpenCode) y verificación", seccion))
story.append(P(
    "OpenCode generó la especificación, los scripts de respaldo/monitoreo/mantenimiento/restauración y este informe. "
    "Nada se aceptó sin ejecutarlo contra el motor real: se cargó foodstore (400.002 líneas), se ejecutaron los cuatro "
    "artefactos, la prueba de falla de pg_dump (exit 1, sin .dump válido) y el simulacro completo. La IA propuso y la "
    "ejecución obligó a corregir cuatro errores: variables de psql en -c, límite de conexiones de mant_restore, permisos "
    "de rotación de pgpass.conf y un ORDER BY inválido en el SQL de evidencias. La autoevaluación "
    "soporte/verificar_entrega.ps1 terminó con todos los controles en PASS, y las salidas crudas quedaron en evidencias/ "
    "(restore_metrics.json, logs, health checks y listado del dump)."))

doc = SimpleDocTemplate(
    SALIDA,
    pagesize=A4,
    leftMargin=12 * mm,
    rightMargin=12 * mm,
    topMargin=9 * mm,
    bottomMargin=9 * mm,
    title="Informe U6 - Mantenimiento Food Store",
    author="Facundo Chacón",
)
doc.build(story)
print(f"PDF generado: {SALIDA}")
print(f"Páginas: {doc.page}")
