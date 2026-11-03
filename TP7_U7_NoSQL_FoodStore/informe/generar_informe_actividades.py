# -*- coding: utf-8 -*-
"""Genera el informe PDF por actividades del TP U7 (complementario al PDF unico)."""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, Preformatted,
)

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "Informe_TP_U7_Actividades.pdf"
REPO = "https://github.com/VIKROOM/DB-TPS-COM4"
REPO_TXT = "github.com/VIKROOM/DB-TPS-COM4"

FUENTES = {
    "Arial": r"C:\Windows\Fonts\arial.ttf",
    "Arial-Bold": r"C:\Windows\Fonts\arialbd.ttf",
    "Arial-Italic": r"C:\Windows\Fonts\ariali.ttf",
    "Consola": r"C:\Windows\Fonts\consola.ttf",
}
for nombre, ruta in FUENTES.items():
    if Path(ruta).exists():
        pdfmetrics.registerFont(TTFont(nombre, ruta))
BASE = "Arial" if "Arial" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
BOLD = "Arial-Bold" if "Arial-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
ITAL = "Arial-Italic" if "Arial-Italic" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Oblique"
MONO = "Consola" if "Consola" in pdfmetrics.getRegisteredFontNames() else "Courier"

AZUL = colors.HexColor("#1F3A5F")
GRIS = colors.HexColor("#5B6770")
GRIS_CLARO = colors.HexColor("#EDF1F5")
VERDE = colors.HexColor("#1E6B45")

ss = getSampleStyleSheet()
st_titulo = ParagraphStyle("titulo", parent=ss["Title"], fontName=BOLD,
                           fontSize=17, leading=20, textColor=AZUL, spaceAfter=2)
st_sub = ParagraphStyle("sub", parent=ss["Normal"], fontName=BASE,
                        fontSize=10.5, leading=13, alignment=TA_CENTER,
                        textColor=GRIS, spaceAfter=2)
st_autor = ParagraphStyle("autor", parent=ss["Normal"], fontName=BASE,
                          fontSize=8.6, leading=11, alignment=TA_CENTER,
                          textColor=colors.black, spaceAfter=7)
st_h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName=BOLD, fontSize=11.2,
                       leading=13.5, textColor=AZUL, spaceBefore=7, spaceAfter=3,
                       keepWithNext=1)
st_h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName=BOLD, fontSize=9.4,
                       leading=11.5, textColor=AZUL, spaceBefore=5, spaceAfter=2,
                       keepWithNext=1)
st_body = ParagraphStyle("body", parent=ss["Normal"], fontName=BASE, fontSize=8.5,
                         leading=10.8, alignment=TA_JUSTIFY, spaceAfter=2.5)
st_li = ParagraphStyle("li", parent=st_body, leftIndent=10, bulletIndent=2,
                       spaceAfter=1.2)
st_consigna = ParagraphStyle("consigna", parent=st_body, fontName=ITAL,
                             textColor=GRIS, leftIndent=6, spaceAfter=4)
st_code = ParagraphStyle("code", parent=ss["Code"], fontName=MONO, fontSize=6.5,
                         leading=7.5, textColor=colors.HexColor("#1B1B1B"))
st_celda = ParagraphStyle("celda", parent=ss["Normal"], fontName=BASE, fontSize=7.4,
                          leading=9.1)
st_celda_b = ParagraphStyle("celdab", parent=st_celda, fontName=BOLD)
st_chico = ParagraphStyle("chico", parent=st_celda, fontSize=7.0, leading=8.6)


def P(texto, estilo=st_body):
    return Paragraph(texto, estilo)


def C(texto, negrita=False, estilo=None):
    return Paragraph(texto, estilo or (st_celda_b if negrita else st_celda))


def tabla(data, anchos, header=True, zebra=True):
    t = Table(data, colWidths=anchos, repeatRows=1 if header else 0)
    est = [
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C2CC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if header:
        est += [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), BOLD),
            ("FONTSIZE", (0, 0), (-1, 0), 7.4),
        ]
    if zebra:
        for i in range(1 if header else 0, len(data)):
            if i % 2 == 0:
                est.append(("BACKGROUND", (0, i), (-1, i), GRIS_CLARO))
    t.setStyle(TableStyle(est))
    return t


def caja_codigo(texto, tam=None):
    caja = Table([[Preformatted(texto, st_code)]], colWidths=[doc.width])
    caja.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F6F8FA")),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D2DB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return caja


def encabezado_pie(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(AZUL)
    canvas.setLineWidth(0.6)
    canvas.line(doc.leftMargin, A4[1] - 12 * mm, A4[0] - doc.rightMargin, A4[1] - 12 * mm)
    canvas.setFont(BASE, 6.8)
    canvas.setFillColor(GRIS)
    canvas.drawString(doc.leftMargin, A4[1] - 10.2 * mm,
                      "Bases de Datos II · Comisión 4 · TP Unidad 7 — Informe por actividades")
    canvas.drawRightString(A4[0] - doc.rightMargin, A4[1] - 10.2 * mm, "Facundo Chacón")
    canvas.line(doc.leftMargin, 12 * mm, A4[0] - doc.rightMargin, 12 * mm)
    canvas.drawString(doc.leftMargin, 8.5 * mm, f"Repositorio: {REPO_TXT}")
    canvas.restoreState()


class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._estados = []

    def showPage(self):
        self._estados.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._estados)
        for estado in self._estados:
            self.__dict__.update(estado)
            self.setFont(BASE, 6.8)
            self.setFillColor(GRIS)
            self.drawRightString(A4[0] - 1.6 * cm, 8.5 * mm,
                                 f"Página {self._pageNumber} de {total}")
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)


doc = BaseDocTemplate(
    str(SALIDA), pagesize=A4,
    leftMargin=1.6 * cm, rightMargin=1.6 * cm,
    topMargin=1.55 * cm, bottomMargin=1.6 * cm,
    title="TP Unidad 7 - Informe por actividades",
    author="Facundo Chacón",
    subject="Bases de Datos II - Comisión 4",
)
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates([PageTemplate(id="pagina", frames=[frame], onPage=encabezado_pie)])

S = []

# ------------------------------------------------------------------ portada
S.append(P("Informe por actividades · Unidad 7", st_titulo))
S.append(P("NoSQL y nuevas formas de almacenamiento — Food Store", st_sub))
S.append(P(
    "Tecnicatura Universitaria en Programación · Bases de Datos II · Comisión 4<br/>"
    "Integrante: <b>Facundo Chacón</b> · Fecha: 03/11/2026<br/>"
    f"Repositorio: <link href=\"{REPO}\"><font color=\"#1F3A5F\">{REPO_TXT}</font></link><br/>"
    "PostgreSQL 17 (base <i>foodstore</i>) · MongoDB 7.0.14 + mongosh 2.3.1",
    st_autor))

S.append(P(
    "Este documento desglosa el trabajo en las <b>siete actividades</b> que se derivan de las "
    "consignas 1 a 7 y de la entrega. Para cada actividad se indica qué pedía la consigna, qué "
    "se hizo, con qué evidencia se comprobó y cuál fue el resultado. El PDF de entrega de 2 "
    "páginas es el resumen exigido; este informe es el detalle operativo de cada paso."))

S.append(P("Mapa de actividades", st_h2))
S.append(tabla([
    [C("#", True), C("Actividad", True), C("Consigna", True), C("Evidencia principal", True), C("Estado", True)],
    [C("A1"), C("Modelo documental y correspondencia"), C("1"), C("Sección 1 del informe; documento de ejemplo"), C("OK", True)],
    [C("A2"), C("Base, colección y migración"), C("2"), C("<i>01_crear_coleccion.js</i>, <i>02_datos_pedidos.js</i>"), C("OK", True)],
    [C("A3"), C("Reglas de integridad y embebido"), C("3"), C("<i>03_verificacion_integridad.js</i> (9 controles)"), C("OK", True)],
    [C("A4"), C("Consultas a–d en MongoDB"), C("4"), C("<i>consultas_mongodb.js</i> y salida real"), C("OK", True)],
    [C("A5"), C("Equivalentes en PostgreSQL"), C("5"), C("<i>consultas_postgresql.sql</i> y tabla comparativa"), C("OK", True)],
    [C("A6"), C("IA y contraste de afirmaciones"), C("6 y 7"), C("<i>BITACORA_IA.md</i> y pruebas de laboratorio"), C("OK", True)],
    [C("A7"), C("Conclusión, PDF y entrega"), C("7 y Entrega"), C("PDF de 2 páginas y 26/26 comprobaciones"), C("OK", True)],
], [0.8 * cm, 4.4 * cm, 1.5 * cm, doc.width - 8.4 * cm, 1.7 * cm]))
S.append(Spacer(1, 3))

# ------------------------------------------------------------------ A1
S.append(P("Actividad 1 · Modelo documental y correspondencia (consigna 1)", st_h1))
S.append(P(
    "<b>Consigna.</b> Seleccionar el subconjunto «pedidos y detalle de pedidos», identificar las "
    "tablas y claves de PostgreSQL y elaborar un esquema breve de la colección documental.",
    st_consigna))

S.append(P(
    "El subconjunto elegido son los <b>pedidos con sus líneas y los datos esenciales del "
    "cliente</b>. En PostgreSQL intervienen cuatro tablas: <i>pedido</i> (PK <i>id</i>, FK "
    "<i>cliente_id</i>, <i>fecha</i>, <i>forma_pago</i>), <i>linea_pedido</i> (PK compuesta "
    "<i>pedido_id, producto_id</i>, <i>cantidad</i>, <i>precio_unitario</i>), <i>cliente</i> "
    "(PK <i>id</i>, <i>nombre</i>, <i>apellido</i>) y <i>producto</i> (PK <i>id</i>, FK "
    "<i>categoria_id</i>, <i>nombre</i>, <i>precio</i>). Las FK de <i>linea_pedido</i> usan "
    "CASCADE hacia el pedido y RESTRICT hacia el producto; <i>pedido.cliente_id</i> usa RESTRICT."))
S.append(P("Cada pedido se representa como un único documento con las líneas embebidas:"))
S.append(caja_codigo(r"""{
  pedido_id: 1,  fecha: ISODate("2026-11-03T01:39:32.658Z"),
  estado: "PENDIENTE",  forma_pago: "EFECTIVO",
  cliente: { cliente_id: 1, nombre: "Ana Gomez" },
  items: [
    { producto_id: 1, nombre: "Muzzarella", categoria: "Pizzas",
      cantidad: 2, precio_unitario: NumberDecimal("1000.00"),
      subtotal: NumberDecimal("2000.00") },
    { producto_id: 2, nombre: "Coca 1.5L", categoria: "Bebidas",
      cantidad: 1, precio_unitario: NumberDecimal("800.00"),
      subtotal: NumberDecimal("800.00") } ],
  items_count: 2,  total: NumberDecimal("2800.00")
}"""))
S.append(Spacer(1, 2))
S.append(P(
    "<b>Correspondencia.</b> <i>pedido.id → pedido_id</i>; <i>fecha → fecha</i>; "
    "<i>forma_pago → forma_pago</i>; <i>cliente.id → cliente.cliente_id</i>; <i>nombre + "
    "apellido → cliente.nombre</i>; <i>linea_pedido + producto → items[]</i>; "
    "<i>SUM(cantidad × precio_unitario) → total</i>. Se conservan <b>pedido_id, cliente_id y "
    "producto_id</b>; no se copian email ni teléfono (minimización de datos)."))
S.append(P(
    "<b>Decisión de agrupamiento.</b> Las líneas se embeben porque siempre se leen junto con el "
    "pedido, el arreglo es acotado (2 líneas por pedido en la muestra) y la escritura del pedido "
    "completo queda atómica. Cliente y producto se referencian por id y solo se copia la "
    "instantánea histórica necesaria (nombre, categoría y precio unitario)."))
S.append(P(
    "<b>Evidencia y verificación.</b> El documento de ejemplo se reproduce en la sección 1 del "
    "informe de entrega y en <i>evidencia/mongo_06_pruebas_ia.txt</i>. Los 12 documentos "
    "migrados conservan los tres identificadores de origen y ninguno incluye email o teléfono."))

# ------------------------------------------------------------------ A2
S.append(P("Actividad 2 · Base, colección y migración (consigna 2)", st_h1))
S.append(P(
    "<b>Consigna.</b> Crear la base y la colección en MongoDB y migrar un mínimo de cinco pedidos "
    "con sus líneas y datos esenciales del cliente mediante <i>insertMany()</i> o equivalente.",
    st_consigna))

S.append(P(
    "La migración se resolvió en tres pasos reproducibles: <b>(1)</b> "
    "<i>sql/01_exportar_pedidos_mongodb.sql</i> consulta PostgreSQL y genera un script "
    "JavaScript con <i>ISODate</i> y <i>NumberDecimal</i>; <b>(2)</b> "
    "<i>mongodb/01_crear_coleccion.js</i> crea <i>foodstore_nosql.pedidos</i> con validador "
    "<i>$jsonSchema</i>, índices y metadatos de procedencia; <b>(3)</b> "
    "<i>mongodb/02_datos_pedidos.js</i> ejecuta el <i>insertMany()</i>."))

S.append(tabla([
    [C("Dato migrado", True), C("Valor verificado", True)],
    [C("Volumen migrado"), C("12 pedidos · 24 líneas · 11 clientes (mínimo exigido: 5 pedidos)")],
    [C("Rango de fechas"), C("2025-03-01 a 2026-11-02")],
    [C("Importe total"), C("$560.979,00 (idéntico a PostgreSQL)")],
    [C("Campos por documento"), C("pedido_id, fecha, estado, forma_pago, cliente, items, items_count, total")],
], [4.6 * cm, doc.width - 4.6 * cm]))
S.append(Spacer(1, 3))

S.append(P(
    "<b>Validador e índices.</b> El validador exige los ocho campos, tipos BSON correctos, "
    "<i>estado</i> y <i>forma_pago</i> dentro de su dominio, <i>cantidad</i> entero ≥ 1, "
    "importes decimales ≥ 0, <i>items</i> no vacío y <i>additionalProperties: false</i>. "
    "Se crearon índices por <i>pedido_id</i> (único), <i>estado</i>, "
    "<i>items.producto_id</i> (multikey) y <i>total</i> (descendente). Los metadatos quedan en "
    "<i>meta_migracion</i> con origen, reglas y fecha de extracción."))
S.append(P(
    "<b>Evidencia y verificación.</b> <i>evidencia/mongo_02_carga.txt</i> registra "
    "<i>Documentos en pedidos: 12</i>; <i>evidencia/mongo_01_crear_coleccion.txt</i> muestra "
    "los cuatro índices creados. Los 12 documentos contienen fecha, estado, cliente, productos, "
    "cantidades y precios históricos."))

# ------------------------------------------------------------------ A3
S.append(P("Actividad 3 · Reglas de integridad y justificación del embebido (consigna 3)", st_h1))
S.append(P(
    "<b>Consigna.</b> Indicar dos reglas de integridad que deben conservarse en la migración y "
    "justificar qué datos se incluyeron dentro del documento en lugar de colecciones separadas.",
    st_consigna))

S.append(tabla([
    [C("Regla", True), C("Implementación", True), C("Resultado medido", True)],
    [C("1. Identidad y referencia", True),
     C("<i>pedido_id</i> obligatorio y único; cada <i>items.producto_id</i> debe existir en "
       "<i>producto</i> del origen."),
     C("0 duplicados de <i>pedido_id</i>; 0 líneas huérfanas sobre 24 líneas.")],
    [C("2. Coherencia de cantidades e importes", True),
     C("<i>cantidad</i> entero ≥ 1; <i>precio_unitario ≥ 0</i>; "
       "<i>subtotal = cantidad × precio_unitario</i>; <i>total = Σ subtotales</i>."),
     C("0 subtotales incorrectos en 24 líneas; 0 totales incorrectos en 12 pedidos.")],
], [3.5 * cm, 7.2 * cm, doc.width - 10.7 * cm]))
S.append(Spacer(1, 3))
S.append(P(
    "<b>Por qué se embebe.</b> Las líneas se leen siempre junto con el pedido, son un arreglo "
    "acotado y permiten recuperar el pedido completo en una sola lectura, sin JOIN. El cliente y "
    "el producto quedan como referencia por id: no se duplica el catálogo ni los datos "
    "personales, y se conserva la trazabilidad al modelo relacional. La copia de nombre, "
    "categoría y precio unitario es una <b>instantánea histórica</b>: 23 de 24 precios "
    "históricos difieren del precio actual del catálogo, lo que confirma que no se sobrescriben."))
S.append(P(
    "<b>Límite asumido.</b> El embebido es válido para arreglos acotados; un documento BSON "
    "tiene un máximo de 16 MiB. Para un histórico ilimitado de líneas correspondería una "
    "colección separada con referencia al pedido. En esta muestra cada pedido tiene 2 líneas."))
S.append(P(
    "<b>Evidencia y verificación.</b> <i>mongodb/03_verificacion_integridad.js</i> ejecuta "
    "<b>9 controles</b> en el motor (documentos, duplicados, <i>items_count</i>, subtotales, "
    "totales, dominio de estado, tipo de fecha, tipos BSON e ids de producto). Salida: "
    "<i>RESULTADO: OK</i> en <i>evidencia/mongo_03_verificacion_integridad.txt</i>."))

# ------------------------------------------------------------------ A4
S.append(P("Actividad 4 · Consultas a–d en MongoDB (consigna 4)", st_h1))
S.append(P(
    "<b>Consigna.</b> Ejecutar cuatro consultas adaptadas al modelo: todos los pedidos con "
    "identificador y estado; filtrar por un estado existente; buscar un producto dentro del "
    "arreglo de líneas; y buscar totales superiores a un importe elegido, justificando el umbral.",
    st_consigna))

S.append(tabla([
    [C("#", True), C("Consulta ejecutada (resumen)", True), C("Resultado sobre los 12 documentos", True)],
    [C("a"), C("<i>find({}, {_id:0, pedido_id:1, estado:1}).sort({pedido_id:1})</i>"),
     C("12 pedidos, con <i>pedido_id</i> y <i>estado</i>")],
    [C("b"), C("<i>find({estado:\"TERMINADO\"}, {_id:0, pedido_id:1})</i>"),
     C("11 pedidos: ids 2 a 12")],
    [C("c"), C("<i>find({\"items.producto_id\": 1}, {_id:0, pedido_id:1})</i>"),
     C("2 pedidos: ids 1 y 2 (Muzzarella)")],
    [C("d"), C("<i>find({total: {$gt: NumberDecimal(\"50000.00\")}})</i>"),
     C("6 pedidos: 2, 6, 8, 10, 11 y 12 · $386.471,00")],
], [0.8 * cm, 10.4 * cm, doc.width - 11.2 * cm]))
S.append(Spacer(1, 3))
S.append(P(
    "<b>Justificación del umbral de d): $50.000,00.</b> Sobre los 12 pedidos, el total promedio "
    "es <b>$46.748,25</b> y la mediana <b>$49.891,50</b>. El umbral elegido queda en el orden de "
    "la mediana y separa <b>6 de 12</b> pedidos de alto valor: no devuelve todos ni ninguno, así "
    "que la consulta discrimina. El importe acumulado de esos 6 pedidos es <b>$386.471,00</b>."))
S.append(P(
    "La distribución por estado de la muestra es 11 pedidos <i>TERMINADO</i> ($558.179,00) y 1 "
    "<i>PENDIENTE</i> ($2.800,00). La regla de estado se deriva de los datos porque el esquema "
    "real no tiene columna de estado: <i>fecha_corte = max(fecha del lote) + 1 día</i>; "
    "<i>TERMINADO</i> si <i>fecha ≤ fecha_corte − 30 días</i>. No depende del reloj."))
S.append(P(
    "<b>Evidencia y verificación.</b> <i>consultas_mongodb.js</i> contiene las cuatro consultas "
    "y las comprobaciones complementarias; la salida completa está en "
    "<i>evidencia/mongo_04_consultas.txt</i>."))

# ------------------------------------------------------------------ A5
S.append(P("Actividad 5 · Equivalentes en PostgreSQL y comparación (consigna 5)", st_h1))
S.append(P(
    "<b>Consigna.</b> Resolver en PostgreSQL las consultas equivalentes a b) y c), comparar en "
    "una tabla la cantidad y los identificadores recuperados en ambos motores y explicar "
    "cualquier diferencia.",
    st_consigna))

S.append(P(
    "En SQL, b) se resuelve con un <i>CASE</i> que aplica exactamente la misma regla de estado y "
    "c) con un <i>JOIN</i> a <i>linea_pedido</i> más <i>DISTINCT</i>. Ambos motores trabajan "
    "sobre el mismo lote (<i>pedido.id BETWEEN 1 AND 12</i>) y la misma precisión decimal "
    "(<i>NUMERIC(10,2)</i> ↔ <i>Decimal128</i>)."))

S.append(tabla([
    [C("Consulta", True), C("Cant. PostgreSQL", True), C("Cant. MongoDB", True),
     C("IDs en ambos motores", True), C("Importe", True), C("¿Coinciden?", True)],
    [C("b) estado TERMINADO"), C("11"), C("11"), C("2,3,4,5,6,7,8,9,10,11,12"),
     C("$558.179,00"), C("Sí", True)],
    [C("c) producto 1"), C("2"), C("2"), C("1,2"), C("$79.810,00"), C("Sí", True)],
], [3.6 * cm, 2.2 * cm, 2.2 * cm, 5.0 * cm, 2.3 * cm, doc.width - 15.3 * cm]))
S.append(Spacer(1, 3))
S.append(P(
    "<b>Diferencias detectadas: ninguna en los datos.</b> Cantidades, IDs e importes coinciden "
    "exactamente. La única diferencia es de <b>sintaxis y modelo</b>: SQL usa <i>JOIN</i>, "
    "<i>CASE</i> y agregación; MongoDB usa notación de punto sobre el arreglo y un campo "
    "<i>estado</i> materializado al migrar. El total general también coincide: "
    "<b>$560.979,00</b> en ambos motores."))
S.append(P(
    "<b>Evidencia y verificación.</b> <i>consultas_postgresql.sql</i> incluye los equivalentes, "
    "la tabla de verificación y cuatro controles de integridad del origen; la salida está en "
    "<i>evidencia/postgres_01_consultas.txt</i>. La comparación de cantidad, IDs e importes se "
    "recalcula automáticamente en <i>verificar_entrega.ps1</i> (8 comprobaciones cruzadas)."))

# ------------------------------------------------------------------ A6
S.append(P("Actividad 6 · Consulta a IA y contraste de afirmaciones (consignas 6 y 7)", st_h1))
S.append(P(
    "<b>Consigna.</b> Consultar a una herramienta de IA comparando PostgreSQL y MongoDB para el "
    "modelo actual, el acceso frecuente a pedidos completos y la coherencia de cantidades y "
    "precios; contrastar dos afirmaciones con documentación oficial o laboratorio y concluir en "
    "hasta 200 palabras con al menos dos criterios técnicos.",
    st_consigna))

S.append(P(
    "El prompt completo está transcripto en <i>BITACORA_IA.md</i>. La IA propuso embeber las "
    "líneas y formuló cuatro afirmaciones que se contrastaron con documentación oficial y con "
    "pruebas ejecutadas en el laboratorio:"))
S.append(tabla([
    [C("Afirmación de la IA", True), C("Contraste", True), C("Veredicto", True)],
    [C("«No hay transacciones ACID multidocumento»"),
     C("MongoDB las soporta en <i>replica sets</i>; un <i>standalone</i> no. En el laboratorio "
       "la sesión falló con <i>Transaction numbers are only allowed on a replica set member or "
       "mongos</i>."),
     C("Imprecisa: falsa en general, cierta en este despliegue. El diseño no las necesita.")],
    [C("«Es más rápido porque evita JOIN»"),
     C("El embebido reduce operaciones, no garantiza superioridad. Consulta c): MongoDB examinó "
       "2 documentos y 2 claves (1 ms); PostgreSQL usó <i>index-only scans</i> (0,086 ms)."),
     C("No sostenible como absoluto: la ventaja es de número de operaciones.")],
    [C("«No se pueden imponer reglas de integridad»"),
     C("El validador <i>$jsonSchema</i> con <i>validationAction:\"error\"</i> rechazó un "
       "documento con <i>cantidad: 0</i>: <i>Document failed validation</i>."),
     C("Falsa: el esquema flexible admite validaciones estrictas.")],
    [C("«El documento puede crecer sin límite»"),
     C("El máximo BSON es 16 MiB; el embebido se recomienda para arreglos acotados."),
     C("Falsa: los pedidos migrados tienen 2 líneas y ~1,5 KB.")],
], [3.9 * cm, 8.0 * cm, doc.width - 11.9 * cm]))
S.append(Spacer(1, 3))
S.append(P(
    "<b>Conclusión (196 palabras).</b> Conviene una <b>arquitectura combinada</b>, no un "
    "reemplazo. PostgreSQL debe seguir siendo la fuente de verdad: las claves foráneas garantizan "
    "que cada pedido tenga un cliente y productos existentes, impone cantidades positivas y "
    "conserva el precio histórico; además ofrece transacciones ACID en el despliegue real. "
    "MongoDB aporta una proyección de lectura: el pedido completo se recupera en un solo "
    "documento, sin JOIN, y el laboratorio mostró resultados idénticos a SQL. Esa ventaja es de "
    "número de operaciones, no de rendimiento demostrado con 12 documentos. Los criterios son "
    "(1) patrón de acceso —lectura completa y repetida frente a escrituras transaccionales—, "
    "(2) integridad —coherencia de cantidades, precios y referencias— y (3) costo operativo de "
    "mantener dos motores. Si el volumen de lectura lo justifica, sincronizar por <i>pedido_id</i> "
    "una colección de solo lectura."))
S.append(P(
    "<b>Evidencia y verificación.</b> <i>BITACORA_IA.md</i> documenta el prompt, la respuesta y "
    "la tabla de contraste; <i>mongodb/06_pruebas_afirmaciones_ia.js</i> ejecuta las pruebas de "
    "validador, transacción y <i>explain</i> (<i>evidencia/mongo_06_pruebas_ia.txt</i>)."))

# ------------------------------------------------------------------ A7
S.append(P("Actividad 7 · Conclusión, PDF y entrega (consigna 7 y Entrega)", st_h1))
S.append(P(
    "<b>Consigna.</b> Presentar un único PDF de hasta cinco páginas, sin contar el código, con "
    "modelo, evidencias, tabla de verificación, contraste de IA y conclusión; adjuntar "
    "<i>consultas_mongodb.js</i> y <i>consultas_postgresql.sql</i>.",
    st_consigna))

S.append(tabla([
    [C("Entregable", True), C("Archivo", True), C("Verificación", True)],
    [C("Informe de entrega"), C("<i>informe/Informe_TP_U7_NoSQL_FoodStore.pdf</i>"),
     C("2 páginas (límite 5), con las cinco secciones")],
    [C("Consultas MongoDB"), C("<i>consultas_mongodb.js</i>"), C("Ejecuta a–d y comprobaciones extra")],
    [C("Consultas PostgreSQL"), C("<i>consultas_postgresql.sql</i>"), C("Ejecuta b–c y controles de integridad")],
    [C("Informe por actividades"), C("<i>informe/Informe_TP_U7_Actividades.pdf</i>"), C("Este documento")],
    [C("Evidencias"), C("<i>evidencia/</i>"), C("Salidas reales de ambos motores y del verificador")],
], [3.6 * cm, 8.3 * cm, doc.width - 11.9 * cm]))
S.append(Spacer(1, 3))
S.append(P(
    "<b>Autoevaluación.</b> <i>verificar_entrega.ps1</i> ejecuta <b>26 comprobaciones</b>: "
    "presencia de los 10 archivos exigidos, 12 pedidos y 24 líneas de origen, 0 huérfanas, "
    "0 líneas inválidas, 12 documentos migrados, comparación cruzada de cantidad, IDs, importes y "
    "productos entre ambos motores, integridad del modelo documental y límite de páginas del PDF. "
    "Resultado final: <b>26/26 OK, 0 fallas</b> (<i>evidencia/verificacion_entrega.txt</i>)."))
S.append(P("Reproducción completa desde la raíz del TP:"))
S.append(caja_codigo(r"""$env:PGPASSWORD="***"
.\reproducir.ps1 `
  -Psql    "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -Mongosh "C:\...\mongosh.exe"

.\verificar_entrega.ps1 `
  -Psql    "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -Mongosh "C:\...\mongosh.exe"    # 26/26 OK"""))
S.append(Spacer(1, 3))

S.append(P("Cierre y enlaces", st_h2))
S.append(P(
    f"<b>Repositorio del trabajo:</b> <link href=\"{REPO}\"><font color=\"#1F3A5F\">"
    f"{REPO}</font></link><br/>"
    "El TP completo (código, evidencias, informes y scripts de reproducción) está en la carpeta "
    "<i>TP7_U7_NoSQL_FoodStore/</i> de ese repositorio. Las evidencias se regeneran con "
    "<i>reproducir.ps1</i> y se validan con <i>verificar_entrega.ps1</i>."))
S.append(P(
    "<b>Límites declarados.</b> El estado es derivado porque el esquema relacional no lo tiene; "
    "la muestra es de 12 pedidos y no permite conclusiones de rendimiento; el <i>mongod</i> local "
    "es <i>standalone</i>, por lo que no admite transacciones multidocumento. El informe no "
    "afirma que MongoDB reemplace a PostgreSQL: propone combinar ambos motores según el patrón "
    "de acceso y el volumen."))

doc.build(S, canvasmaker=NumberedCanvas)
print(f"PDF generado: {SALIDA}")
