# -*- coding: utf-8 -*-
"""Genera el PDF unico del TP U7 (<= 5 paginas) con ReportLab."""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, Preformatted, HRFlowable, KeepTogether,
)

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "Informe_TP_U7_NoSQL_FoodStore.pdf"

# Tipografias con soporte de acentos y simbolos.
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
ROJO = colors.HexColor("#8B2E2E")

ss = getSampleStyleSheet()
st_titulo = ParagraphStyle("titulo", parent=ss["Title"], fontName=BOLD,
                           fontSize=17, leading=20, textColor=AZUL, spaceAfter=2)
st_sub = ParagraphStyle("sub", parent=ss["Normal"], fontName=BASE,
                        fontSize=10.5, leading=13, alignment=TA_CENTER,
                        textColor=GRIS, spaceAfter=2)
st_autor = ParagraphStyle("autor", parent=ss["Normal"], fontName=BASE,
                          fontSize=8.8, leading=11, alignment=TA_CENTER,
                          textColor=colors.black, spaceAfter=8)
st_h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName=BOLD, fontSize=11.5,
                       leading=13.5, textColor=AZUL, spaceBefore=7, spaceAfter=3)
st_h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName=BOLD, fontSize=9.8,
                       leading=12, textColor=AZUL, spaceBefore=5, spaceAfter=2)
st_body = ParagraphStyle("body", parent=ss["Normal"], fontName=BASE, fontSize=8.7,
                         leading=11.3, alignment=TA_JUSTIFY, spaceAfter=3)
st_li = ParagraphStyle("li", parent=st_body, leftIndent=10, bulletIndent=2,
                       spaceAfter=1.5)
st_code = ParagraphStyle("code", parent=ss["Code"], fontName=MONO, fontSize=6.6,
                         leading=7.8, textColor=colors.HexColor("#1B1B1B"))
st_celda = ParagraphStyle("celda", parent=ss["Normal"], fontName=BASE, fontSize=7.5,
                          leading=9.2)
st_celda_b = ParagraphStyle("celdab", parent=st_celda, fontName=BOLD)
st_pie = ParagraphStyle("pie", parent=ss["Normal"], fontName=BASE, fontSize=7,
                        textColor=GRIS, alignment=TA_CENTER)


def P(texto, estilo=st_body):
    return Paragraph(texto, estilo)


def C(texto, negrita=False):
    return Paragraph(texto, st_celda_b if negrita else st_celda)


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
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ]
    if zebra:
        for i in range(1 if header else 0, len(data)):
            if i % 2 == 0:
                est.append(("BACKGROUND", (0, i), (-1, i), GRIS_CLARO))
    t.setStyle(TableStyle(est))
    return t


def encabezado_pie(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(AZUL)
    canvas.setLineWidth(0.6)
    canvas.line(doc.leftMargin, A4[1] - 12 * mm, A4[0] - doc.rightMargin, A4[1] - 12 * mm)
    canvas.setFont(BASE, 6.8)
    canvas.setFillColor(GRIS)
    canvas.drawString(doc.leftMargin, A4[1] - 10.2 * mm,
                      "Bases de Datos II · Comisión 4 · TP Unidad 7 — Food Store NoSQL")
    canvas.drawRightString(A4[0] - doc.rightMargin, A4[1] - 10.2 * mm, "Facundo Chacón")
    canvas.line(doc.leftMargin, 12 * mm, A4[0] - doc.rightMargin, 12 * mm)
    canvas.drawString(doc.leftMargin, 8.5 * mm,
                      "Repositorio: github.com/VIKROOM/DB-TPS-COM4")
    canvas.restoreState()


class NumberedCanvas(pdfcanvas.Canvas):
    """Dibuja 'Pagina X de Y' con el total real de paginas del PDF."""

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
    title="TP Unidad 7 - Food Store NoSQL",
    author="Facundo Chacón",
    subject="Bases de Datos II - Comisión 4",
)
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates([PageTemplate(id="pagina", frames=[frame], onPage=encabezado_pie)])

S = []

# ---------------------------------------------------------------- portada
S.append(P("Trabajo Práctico · Unidad 7", st_titulo))
S.append(P("NoSQL y nuevas formas de almacenamiento — Food Store", st_sub))
S.append(P(
    "Tecnicatura Universitaria en Programación · Bases de Datos II · Comisión 4<br/>"
    "Integrante: <b>Facundo Chacón</b> · Repositorio: github.com/VIKROOM/DB-TPS-COM4<br/>"
    "PostgreSQL 17 (base <i>foodstore</i>) · MongoDB 7.0.14 + mongosh 2.3.1 · 03/11/2026",
    st_autor))

# ---------------------------------------------------------------- 1
S.append(P("1. Modelo documental y correspondencia con Food Store (consigna 1)", st_h1))
S.append(P(
    "Se eligió el subconjunto <b>pedidos y detalle de pedidos</b>. En PostgreSQL "
    "intervienen <i>pedido</i> (PK <i>id</i>), <i>linea_pedido</i> (PK compuesta "
    "<i>pedido_id, producto_id</i>), <i>cliente</i> (PK <i>id</i>, email único) y "
    "<i>producto</i> (PK <i>id</i>). Las claves foráneas de <i>linea_pedido</i> "
    "referencian al pedido (CASCADE) y al producto (RESTRICT); <i>pedido.cliente_id</i> "
    "referencia al cliente (RESTRICT). Cada pedido se representa como un documento "
    "con las líneas embebidas:"))

codigo = r"""{
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
}"""
caja = Table([[Preformatted(codigo, st_code)]], colWidths=[doc.width])
caja.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F6F8FA")),
    ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D2DB")),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
S.append(caja)
S.append(Spacer(1, 2))

S.append(P(
    "<b>Correspondencia.</b> <i>pedido.id → pedido_id</i>; <i>pedido.fecha → fecha</i>; "
    "<i>pedido.forma_pago → forma_pago</i>; <i>cliente.id → cliente.cliente_id</i>; "
    "<i>cliente.nombre + apellido → cliente.nombre</i>; <i>linea_pedido + producto → "
    "items[]</i> con <i>producto_id, nombre, categoria, cantidad, precio_unitario</i>; "
    "<i>SUM(cantidad × precio_unitario) → total</i>. Se conservan los tres "
    "identificadores de origen y no se copian email ni teléfono (minimización de datos)."))
S.append(P(
    "<b>Decisión de agrupamiento.</b> Las líneas se embeben porque siempre se leen "
    "juntas, son un arreglo acotado (2 líneas por pedido en la muestra) y permiten "
    "actualizar el pedido completo en una escritura atómica. Cliente y producto quedan "
    "referenciados por id; solo se copia la instantánea necesaria para mostrar el pedido "
    "histórico (nombre, categoría y precio unitario). Es un diseño mixto: referencia "
    "estable + copia controlada."))

# ---------------------------------------------------------------- 2
S.append(P("2. Migración y reglas de integridad (consignas 2 y 3)", st_h1))
S.append(P(
    "Se migraron los <b>12 pedidos</b> con <i>id</i> 1 a 12 y sus <b>24 líneas</b>, de 11 "
    "clientes, con fechas entre 2025-03-01 y 2026-11-02 e importe total de "
    "<b>$560.979,00</b>. <i>sql/01_exportar_pedidos_mongodb.sql</i> hace que PostgreSQL "
    "genere un <i>insertMany()</i> con <i>ISODate</i> y <i>NumberDecimal</i>; el script "
    "<i>mongodb/02_datos_pedidos.js</i> se ejecuta en mongosh. Los documentos incluyen "
    "fecha, estado, cliente, productos, cantidades y precios históricos. La colección "
    "se crea con <i>$jsonSchema</i> (<i>strict</i>, <i>validationAction: \"error\"</i>) "
    "e índices por <i>pedido_id</i> (único), <i>estado</i>, <i>items.producto_id</i> y "
    "<i>total</i>."))

S.append(P(
    "<b>Regla 1 — identidad y referencia.</b> <i>pedido_id</i> es obligatorio y único; "
    "cada <i>items.producto_id</i> debe existir en el catálogo de origen. Verificado: "
    "0 duplicados y 0 líneas huérfanas contra <i>producto</i>.", st_li))
S.append(P(
    "<b>Regla 2 — coherencia de cantidades e importes.</b> <i>cantidad</i> entero ≥ 1, "
    "<i>precio_unitario ≥ 0</i>, <i>subtotal = cantidad × precio_unitario</i> y "
    "<i>total = Σ subtotales</i>. Las 24 líneas y los 12 totales coinciden; 23 de 24 "
    "precios históricos difieren del precio actual, lo que confirma que la instantánea "
    "no se sobrescribe.", st_li))
S.append(P(
    "<b>Estado.</b> El esquema real no tiene columna de estado. Para la consigna 4.b se "
    "deriva con una regla reproducible: <i>fecha_corte = max(fecha del lote) + 1 día</i>; "
    "<i>TERMINADO</i> si <i>fecha ≤ fecha_corte − 30 días</i>, <i>PENDIENTE</i> en caso "
    "contrario. Se aplica igual en SQL y al migrar; no depende del reloj. Resultado: "
    "11 TERMINADO y 1 PENDIENTE."))

# ---------------------------------------------------------------- 3
S.append(P("3. Consultas y verificación con PostgreSQL (consignas 4 y 5)", st_h1))
S.append(tabla([
    [C("#", True), C("Consulta MongoDB", True), C("Resultado", True)],
    [C("a"), C("db.pedidos.find({}, {_id:0, pedido_id:1, estado:1}).sort({pedido_id:1})"), C("12 pedidos")],
    [C("b"), C("db.pedidos.find({estado:\"TERMINADO\"}, {_id:0, pedido_id:1})"), C("11 pedidos: 2–12")],
    [C("c"), C("db.pedidos.find({\"items.producto_id\": 1}, {_id:0, pedido_id:1})"), C("2 pedidos: 1, 2")],
    [C("d"), C("db.pedidos.find({total: {$gt: NumberDecimal(\"50000.00\")}})"), C("6 pedidos: 2, 6, 8, 10, 11, 12")],
], [0.8 * cm, 11.2 * cm, doc.width - 12 * cm]))
S.append(Spacer(1, 3))
S.append(P(
    "<b>Umbral de d): $50.000,00.</b> La muestra tiene promedio $46.748,25 y mediana "
    "$49.891,50; el umbral separa 6 de 12 pedidos de alto valor, sin ser trivial (no "
    "devuelve todos ni ninguno). El importe acumulado es $386.471,00."))

S.append(tabla([
    [C("Consulta", True), C("Cantidad PostgreSQL", True), C("Cantidad MongoDB", True),
     C("IDs en ambos motores", True), C("¿Coinciden?", True)],
    [C("b) estado TERMINADO"), C("11"), C("11"), C("2,3,4,5,6,7,8,9,10,11,12"), C("Sí", True)],
    [C("c) producto 1 (Muzzarella)"), C("2"), C("2"), C("1,2"), C("Sí", True)],
], [4.7 * cm, 2.6 * cm, 2.6 * cm, doc.width - 12.4 * cm, 2.5 * cm]))
S.append(Spacer(1, 3))
S.append(P(
    "También coinciden los importes: b) $558.179,00 y c) $79.810,00 en ambos motores. "
    "<b>No se detectaron diferencias</b>: se migró el mismo subconjunto, se aplicó la "
    "misma regla de estado y la misma precisión (<i>NUMERIC(10,2)</i> ↔ <i>Decimal128</i>). "
    "La única diferencia es de sintaxis y modelo: SQL usa <i>JOIN</i> y <i>CASE</i>; "
    "MongoDB usa notación de punto sobre el arreglo y un campo materializado."))

# ---------------------------------------------------------------- 4
S.append(P("4. Evaluación de la tecnología y contraste de IA (consignas 6 y 7)", st_h1))
S.append(P(
    "<b>Consulta a la IA.</b> Se pidió comparar ambos motores para el modelo actual, el "
    "acceso frecuente al pedido completo y la necesidad de conservar coherencia de "
    "cantidades y precios (prompt completo en <i>BITACORA_IA.md</i>). La respuesta propuso "
    "embeber las líneas y afirmó que MongoDB no soporta transacciones multidocumento, que "
    "es más rápido por evitar JOIN, que no admite reglas de integridad y que un documento "
    "puede crecer sin límite. Se contrastaron las cuatro afirmaciones:"))

S.append(tabla([
    [C("Afirmación de la IA", True), C("Documentación oficial / laboratorio", True), C("Veredicto", True)],
    [C("No hay transacciones ACID multidocumento"),
     C("Las hay en <i>replica sets</i>; un <i>standalone</i> no las soporta. En el laboratorio: "
       "<i>Transaction numbers are only allowed on a replica set member or mongos</i>."),
     C("Imprecisa: falsa en general, cierta en nuestro despliegue. El diseño no las necesita: pedido y líneas son un documento.")],
    [C("Es más rápido porque evita JOIN"),
     C("El embebido reduce operaciones, no garantiza superioridad. Consulta c): MongoDB examinó "
       "2 documentos y 2 claves (1 ms); PostgreSQL usó <i>index-only scans</i> y <i>nested loop</i> (0,086 ms)."),
     C("No sostenible como absoluto: la ventaja comprobada es de número de operaciones, no de velocidad.")],
    [C("No se pueden imponer reglas de integridad"),
     C("<i>$jsonSchema</i> con <i>validationAction:\"error\"</i> rechaza documentos inválidos. "
       "El intento con <i>cantidad: 0</i> devolvió <i>Document failed validation</i>."),
     C("Falsa: el esquema flexible admite validaciones estrictas.")],
    [C("El documento crece sin límite"),
     C("Los documentos BSON tienen un máximo de 16 MiB; el embebido se recomienda para arreglos acotados."),
     C("Falsa: los pedidos migrados tienen 2 líneas y ~1,5 KB.")],
], [3.4 * cm, 8.2 * cm, doc.width - 11.6 * cm]))

S.append(Spacer(1, 4))
S.append(P("Conclusión (≤ 200 palabras)", st_h2))
S.append(P(
    "Para el subconjunto pedidos-detalle conviene una arquitectura combinada, no un "
    "reemplazo. PostgreSQL debe seguir siendo la fuente de verdad: el modelo normalizado "
    "garantiza con claves foráneas que cada pedido tenga un cliente y productos existentes, "
    "impone cantidades positivas y conserva el precio histórico en <i>linea_pedido</i>; "
    "además ofrece transacciones ACID en el despliegue real del equipo. MongoDB aporta una "
    "proyección de lectura: un pedido completo se recupera en un solo documento, sin JOIN, "
    "y el laboratorio mostró resultados idénticos a SQL (11 pedidos TERMINADO y 2 con el "
    "producto 1, mismos IDs e importes). Esa ventaja es de número de operaciones, no una "
    "superioridad de rendimiento demostrada con 12 documentos. Los criterios que sostienen "
    "la decisión son (1) patrón de acceso —lectura completa y repetida del pedido frente a "
    "escrituras transaccionales— y (2) integridad —coherencia de cantidades, precios y "
    "referencias—, más (3) costo operativo de mantener dos motores. Si el volumen de lectura "
    "lo justifica, sincronizar por <i>pedido_id</i> una colección de solo lectura; migrar el "
    "núcleo transaccional no se justifica con la evidencia obtenida."))

# ---------------------------------------------------------------- 5
S.append(P("5. Evidencias, reproducción y límites", st_h1))
S.append(P(
    "<b>Archivos entregados:</b> <i>consultas_mongodb.js</i> y "
    "<i>consultas_postgresql.sql</i> (instrucciones ejecutadas); "
    "<i>mongodb/01_crear_coleccion.js</i> (validador, índices y metadatos); "
    "<i>mongodb/02_datos_pedidos.js</i> (12 documentos generados desde PostgreSQL)."))
S.append(P(
    "<b>Evidencias:</b> <i>evidencia/mongo_02_carga.txt</i> (12 documentos); "
    "<i>mongo_03_verificacion_integridad.txt</i> (9 comprobaciones, todas OK); "
    "<i>mongo_04_consultas.txt</i> y <i>postgres_01_consultas.txt</i> (salidas a–d y b–c); "
    "<i>mongo_06_pruebas_ia.txt</i> (validador, transacción y <i>explain</i>)."))
S.append(P(
    "<b>Autoevaluación:</b> <i>verificar_entrega.ps1</i> ejecuta 26 comprobaciones: archivos "
    "exigidos, integridad del modelo, comparación cruzada de IDs e importes entre motores y "
    "límite de 5 páginas. Resultado final: <b>26/26 OK</b> "
    "(<i>evidencia/verificacion_entrega.txt</i>)."))
S.append(P(
    "<b>Límites:</b> el estado es derivado (el esquema relacional no lo tiene); la muestra es "
    "pequeña (12 pedidos) y no permite conclusiones de rendimiento; el <i>mongod</i> local es "
    "<i>standalone</i>, por lo que no admite transacciones multidocumento. No se afirma que "
    "MongoDB reemplace a PostgreSQL."))
S.append(P(
    "<b>Bibliografía.</b> MongoDB: Transactions, Schema Validation, Embedded Data y "
    "db.collection.find() (documentación oficial). Apunte de la cátedra: «Unidad 7: NoSQL y "
    "nuevas formas de almacenamiento»."))

doc.build(S, canvasmaker=NumberedCanvas)
print(f"PDF generado: {SALIDA}")
