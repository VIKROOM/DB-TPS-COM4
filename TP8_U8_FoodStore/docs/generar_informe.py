# -*- coding: utf-8 -*-
"""Genera docs/informe.pdf (maximo 6 paginas) para el TP8."""

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
SALIDA = RAIZ / "informe.pdf"

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
VERDE = colors.HexColor("#2E6B4F")
ROJO = colors.HexColor("#8B2E2E")

ss = getSampleStyleSheet()
st_titulo = ParagraphStyle("titulo", parent=ss["Title"], fontName=BOLD,
                           fontSize=16, leading=19, textColor=AZUL, spaceAfter=2)
st_sub = ParagraphStyle("sub", parent=ss["Normal"], fontName=BASE,
                        fontSize=9.5, leading=12, alignment=TA_CENTER,
                        textColor=GRIS, spaceAfter=1)
st_meta = ParagraphStyle("meta", parent=ss["Normal"], fontName=BASE,
                         fontSize=8.2, leading=10, alignment=TA_CENTER,
                         textColor=colors.black, spaceAfter=5)
st_h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName=BOLD, fontSize=11,
                       leading=13, textColor=AZUL, spaceBefore=6, spaceAfter=2)
st_h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName=BOLD, fontSize=9.2,
                       leading=11, textColor=AZUL, spaceBefore=4, spaceAfter=1)
st_body = ParagraphStyle("body", parent=ss["Normal"], fontName=BASE, fontSize=8.4,
                         leading=10.6, alignment=TA_JUSTIFY, spaceAfter=2.5)
st_li = ParagraphStyle("li", parent=st_body, leftIndent=9, bulletIndent=1,
                       spaceAfter=1.2)
st_code = ParagraphStyle("code", parent=ss["Code"], fontName=MONO, fontSize=6.4,
                         leading=7.5, textColor=colors.HexColor("#1B1B1B"))
st_celda = ParagraphStyle("celda", parent=ss["Normal"], fontName=BASE, fontSize=7.2,
                          leading=8.8)
st_celda_b = ParagraphStyle("celdab", parent=st_celda, fontName=BOLD)
st_pie = ParagraphStyle("pie", parent=ss["Normal"], fontName=BASE, fontSize=6.8,
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
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
    ]
    if header:
        est += [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), BOLD),
            ("FONTSIZE", (0, 0), (-1, 0), 7.2),
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
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, A4[1] - 11 * mm, A4[0] - doc.rightMargin, A4[1] - 11 * mm)
    canvas.setFont(BASE, 6.6)
    canvas.setFillColor(GRIS)
    canvas.drawString(doc.leftMargin, A4[1] - 9.4 * mm,
                      "Bases de Datos II · Comisión 4 · TP Unidad 8 — Food Store en la feria")
    canvas.drawRightString(A4[0] - doc.rightMargin, A4[1] - 9.4 * mm, "Facundo Chacón")
    canvas.line(doc.leftMargin, 11 * mm, A4[0] - doc.rightMargin, 11 * mm)
    canvas.drawString(doc.leftMargin, 7.6 * mm,
                      "Repositorio: github.com/VIKROOM/DB-TPS-COM4")
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
            self.setFont(BASE, 6.6)
            self.setFillColor(GRIS)
            self.drawRightString(A4[0] - 1.6 * cm, 7.6 * mm,
                                 f"Página {self._pageNumber} de {total}")
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)


doc = BaseDocTemplate(
    str(SALIDA), pagesize=A4,
    leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    topMargin=1.45 * cm, bottomMargin=1.5 * cm,
    title="TP Unidad 8 - Food Store en la feria",
    author="Facundo Chacón",
    subject="Bases de Datos II - Comisión 4",
)
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates([PageTemplate(id="pagina", frames=[frame], onPage=encabezado_pie)])

S = []

# ------------------------------------------------------------------ portada
S.append(P("Trabajo Práctico · Unidad 8", st_titulo))
S.append(P("Food Store en la feria: la base de la tablet y el cierre de la capa de datos", st_sub))
S.append(P(
    "Tecnicatura Universitaria en Programación · Bases de Datos II · Comisión 4<br/>"
    "Integrante: <b>Facundo Chacón</b> · Repositorio: github.com/VIKROOM/DB-TPS-COM4<br/>"
    "PostgreSQL 16 · SQLite 3.37 · MongoDB 7 (U7) · 04/11/2026",
    st_meta))

# ------------------------------------------------------------------ 1.a
S.append(P("1. Qué datos viajan a la tablet (consigna 1.a)", st_h1))
S.append(P(
    "La fuente de verdad es <b>PostgreSQL</b>. La tablet recibe solo una copia de "
    "lectura del catálogo mínimo para armar borradores sin señal. No viajan "
    "clientes, usuarios, contraseñas, ventas ni logs: no son necesarios para la "
    "venta offline y aumentarían el riesgo sobre datos personales. La tablet "
    "<b>propone</b>; el servidor <b>dispone</b> sobre precio, stock y ventas."))

S.append(tabla([
    [C("Campo que viaja", True), C("¿Viaja?", True), C("Por qué", True)],
    [C("<i>producto.id</i> / <i>nombre</i>"), C("Sí"), C("Identificar y mostrar el producto en el borrador.")],
    [C("<i>precio_centavos</i>"), C("Sí"), C("Precio visto para detectar cambios; entero, sin punto flotante.")],
    [C("<i>stock_visto</i>"), C("Sí"), C("Referencia para validar la cantidad; no descuenta stock.")],
    [C("<i>disponible</i> / <i>eliminado</i>"), C("Sí"), C("Semáforo y lápida de la baja lógica.")],
    [C("<i>fecha_copia</i>"), C("Sí"), C("Saber la antigüedad de la instantánea.")],
    [C("<i>categoria_id</i> / categoría"), C("No"), C("No se usa para armar el borrador.")],
    [C("<i>cliente</i> (id, nombre, email, teléfono)"), C("No"), C("Datos personales innecesarios en la tablet.")],
    [C("<i>usuario</i> / contraseña / roles"), C("No"), C("Seguridad: la tablet usa un vendedor inventado.")],
    [C("<i>pedido</i> / <i>linea_pedido</i> / ventas"), C("No"), C("Transaccional: lo decide PostgreSQL.")],
    [C("Logs / auditoría"), C("No"), C("No aportan a la operación offline.")],
], [5.0 * cm, 1.5 * cm, doc.width - 6.5 * cm]))
S.append(Spacer(1, 2))
S.append(P(
    "La instantánea se proyecta con <i>v_snapshot_movil</i>: "
    "<i>precio_centavos = round(precio × 100)</i>, "
    "<i>disponible = activo AND stock &gt; 0</i> y "
    "<i>eliminado = NOT activo</i>. El precio se convierte a centavos para que la "
    "comparación del semáforo sea exacta; la lápida de la baja lógica también "
    "viaja para que la tablet sepa que el producto existía y ya no está."))

# ------------------------------------------------------------------ 2.c
S.append(P("2. Sincronización y casos (consigna 2.c)", st_h1))
S.append(P(
    "El circuito es: PostgreSQL exporta el CSV de <i>v_snapshot_movil</i> → SQLite "
    "lo carga en <i>snapshot_servidor</i> → un UPSERT refresca "
    "<i>producto_cache</i> sin borrar lápidas → el semáforo evalúa solo las "
    "solicitudes <i>PENDIENTE</i>. Para cada caso se preparó la situación en la "
    "copia del servidor, se exportó una instantánea nueva y se corrió el semáforo. "
    "La evidencia completa está en <i>evidencias/04_semaforo_casos.txt</i>."))

S.append(tabla([
    [C("Caso", True), C("Qué se preparó", True), C("Resultado", True), C("Explicación", True)],
    [C("C2-A"), C("Borrador del producto 1 (2 × 105000). Se sube el precio a 1150,00 en el servidor."),
     C("CONFLICTO / PRECIO_CAMBIADO"),
     C("No hay rojo, pero el precio visto difiere del actual. La solicitud queda en amarillo para que el cliente decida.")],
    [C("C2-B"), C("Se acepta el precio (se actualiza a 115000) y se envía una solicitud nueva con otro UUID."),
     C("SIMULADO_APROBADO / TODO_COINCIDE"),
     C("Al coincidir todos los datos, el borrador queda aprobado para simulación; no se confirma la venta.")],
    [C("C3"), C("Borrador de 15 unidades del producto 4, con stock 10."),
     C("RECHAZADO / STOCK_INSUFICIENTE"),
     C("La cantidad supera el stock visto: rojo, aunque el precio coincida.")],
    [C("C4"), C("Borrador del producto 5 y luego <i>UPDATE producto SET activo = FALSE WHERE id = 5</i>."),
     C("RECHAZADO / PRODUCTO_DADO_DE_BAJA"),
     C("La lápida viaja en la instantánea. El producto 5 ya no está disponible, pero su fila y el ítem del borrador siguen existiendo.")],
    [C("C5"), C("Borrador del producto 2 (1 × 80000) sin cambios en el servidor."),
     C("SIMULADO_APROBADO / TODO_COINCIDE"),
     C("Producto disponible, stock suficiente y precio igual: verde.")],
    [C("C6"), C("Reenvío del mismo UUID y repetición del semáforo."),
     C("Error de PK; una sola fila"),
     C("La PK de <i>cola_sync</i> rechaza el duplicado y repetir la simulación no reevalúa: <i>evaluado_en</i> no cambia.")],
], [1.2 * cm, 5.6 * cm, 3.7 * cm, doc.width - 10.5 * cm]))
S.append(Spacer(1, 2))
S.append(P(
    "<b>Invariantes del servidor.</b> Antes y después de toda la simulación: "
    "<i>pedido</i> = 3, <i>linea_pedido</i> = 5, <i>producto</i> = 5, "
    "<i>cliente</i> = 3, <i>suma_stock</i> = 115 e <i>importe_lineas</i> = "
    "$5.750,00. El diff está vacío: la tablet no descontó stock ni confirmó "
    "ventas (<i>evidencias/05_verificacion_postgres_diff.txt</i>). Lo que sí "
    "cambió es el precio del producto 1 (C2) y el flag <i>activo</i> del "
    "producto 5 (C4), porque son las preparaciones deliberadas de los casos."))
S.append(P(
    "<b>Idempotencia en un sistema real (C6).</b> La PK de SQLite solo protege a "
    "esa tablet. La protección real debe estar en el servidor: una clave única "
    "de idempotencia por solicitud, el registro de la respuesta y la confirmación "
    "dentro de una transacción. Si la tablet reintenta, el servidor devuelve el "
    "resultado ya registrado en lugar de crear una segunda venta."))

# ------------------------------------------------------------------ 3.a
S.append(P("3. Mapa de la capa de datos (consigna 3.a)", st_h1))
S.append(tabla([
    [C("Motor", True), C("Qué guarda", True), C("Quién manda sobre esos datos", True)],
    [C("PostgreSQL 16"),
     C("Fuente de verdad: <i>categoria</i>, <i>producto</i> (precio, stock, activo), "
       "<i>cliente</i>, <i>pedido</i>, <i>linea_pedido</i>, usuarios/roles, "
       "auditoría, vistas y la vista materializada de facturación."),
     C("PostgreSQL manda sobre precio, stock, ventas, clientes y seguridad. "
       "Ningún otro motor confirma una venta.")],
    [C("MongoDB 7 (U7)"),
     C("Proyección documental de <i>pedidos</i> + detalle (12 pedidos / 24 líneas) "
       "para consultas de lectura. No guarda stock ni precios vigentes."),
     C("PostgreSQL manda. MongoDB es una copia de lectura; no acepta ventas ni "
       "modifica el catálogo.")],
    [C("SQLite 3.37+ (tablet)"),
     C("<i>producto_cache</i> (catálogo de solo lectura), <i>pedido_borrador</i>, "
       "<i>item_borrador</i> y <i>cola_sync</i> (borradores y su estado)."),
     C("La tablet no manda sobre nada: propone borradores. PostgreSQL dispone "
       "cuando confirma la venta.")],
], [2.6 * cm, 7.3 * cm, doc.width - 9.9 * cm]))
S.append(Spacer(1, 2))
S.append(P(
    "El flujo es de una sola dirección: PostgreSQL → CSV → SQLite. La vuelta "
    "(borrador → servidor) queda fuera de este TP y, cuando exista, deberá "
    "confirmarse en PostgreSQL con una transacción y una clave de idempotencia. "
    "MongoDB no participa del circuito de venta: es una proyección de lectura de "
    "los pedidos ya confirmados."))

# ------------------------------------------------------------------ 3.b
S.append(P("4. Plan de mantenimiento (consigna 3.b)", st_h1))
S.append(P(
    "<b>¿Qué se respalda y cómo se prueba la restauración?</b> Se respalda "
    "PostgreSQL completo con <i>pg_dump -Fc</i> (esquema + datos) y los roles con "
    "<i>pg_dumpall -g</i>. Se conservan 7 copias diarias y 4 semanales fuera del "
    "servidor, con <i>sha256</i> para detectar corrupción. La restauración se "
    "prueba mensualmente en una base temporal: <i>pg_restore --list</i>, "
    "restauración completa y comparación de conteos, stock, importes y una "
    "consulta de muestra contra el original. El RPO objetivo es 24 h y el RTO se "
    "mide en cada simulacro (base del TP6).", st_li))
S.append(P(
    "<b>Si se restaura un respaldo viejo de PostgreSQL, ¿qué hacen las tablets?</b> "
    "No se reutiliza el catálogo local como si fuera actual. Al reconectar, la "
    "tablet descarta su <i>snapshot_servidor</i> y recibe una instantánea nueva; "
    "las solicitudes pendientes se reevalúan contra el estado restaurado y las "
    "que queden en <i>CONFLICTO</i> o <i>RECHAZADO</i> se derivan a revisión. "
    "Nunca se reenvían borradores automáticamente como ventas: si una venta "
    "confirmada se perdió con el respaldo, se reconcilia con la auditoría y se "
    "resuelve manualmente. El UUID evita duplicar una solicitud que ya había "
    "llegado.", st_li))
S.append(P(
    "<b>¿Cada cuánto y quién revisa las solicitudes en CONFLICTO o RECHAZADO?</b> "
    "El encargado de operaciones (rol de soporte) revisa la cola al cierre de cada "
    "feria y, como máximo, dentro de las 24 h. Si un caso sigue abierto a las "
    "48 h, escala al responsable de datos. Cada decisión se registra en la "
    "auditoría y se resume semanalmente por causa (precio, stock, baja, "
    "producto inexistente) para corregir el origen.", st_li))

# ------------------------------------------------------------------ 3.c
S.append(P("5. Code review con IA (consigna 3.c)", st_h1))
S.append(P(
    "Se revisaron los scripts de la cursada con OpenCode. Cada hallazgo se "
    "comprobó ejecutando el script real sobre PostgreSQL temporal, no por "
    "inspección visual. La salida completa está en "
    "<i>evidencias/07_revision_codigo.txt</i>; el runner es "
    "<i>scripts/revision_codigo.py</i>."))

S.append(tabla([
    [C("ID", True), C("Unidad", True), C("Hallazgo", True), C("Decisión", True), C("Cómo se comprobó", True)],
    [C("H1"), C("U5"), C("Los grants de tabla sobre <i>usuario</i> dan SELECT de todas las columnas (mail, celular, contraseña); el mínimo por columna solo se aplicó a <i>rol_soporte</i>."),
     C("Aceptado"), C("<i>role_table_grants</i> vs. <i>column_privileges</i>: <i>rol_app_lectura</i> y <i>rol_app_escritura</i> tienen SELECT de tabla.")],
    [C("H2"), C("U5"), C("<i>usuario_anon</i> se crea con CTAS: no tiene PK ni NOT NULL y la verificación por <i>EXCEPT</i> no detecta duplicados."),
     C("Aceptado"), C("<i>pg_constraint</i> = 0; un <i>INSERT</i> duplicado de <i>id</i> pasó y <i>diff_total</i> siguió en 0.")],
    [C("H3"), C("U3"), C("<i>v_pedidos_cliente</i> filtra <i>c.activo = TRUE</i> y oculta los pedidos históricos de clientes inactivos."),
     C("Aceptado"), C("2 pedidos en la tabla vs. 1 en la vista; el pedido 2 (cliente inactivo) desaparece.")],
    [C("H4"), C("U3/U5"), C("U5 referencia <i>usuario</i>/<i>detalle_pedido</i>; el esquema real de U3 usa <i>cliente</i>/<i>linea_pedido</i>."),
     C("Aceptado"), C("<i>to_regclass</i> devuelve NULL para <i>usuario</i> y <i>detalle_pedido</i>; el <i>GRANT</i> falla con “relation does not exist”.")],
    [C("H5"), C("U3"), C("<i>registrar_pedido</i> consume un id de secuencia antes de validar los ítems; se sospechaban pedidos huérfanos."),
     C("Descartado"), C("Secuencia 2 → 3, pero <i>pedido</i> sigue en 2 y hay 0 huérfanos: <i>RAISE EXCEPTION</i> aborta la transacción. Los huecos de secuencia son normales.")],
    [C("H6"), C("U5"), C("<i>ALTER DEFAULT PRIVILEGES ... GRANT SELECT (columna)</i> no es válido y corta el script de U5."),
     C("Aceptado"), C("Error “default privileges cannot be set for columns”; <i>pg_default_acl</i> solo registra privilegios de tabla.")],
], [0.9 * cm, 1.3 * cm, 6.0 * cm, 1.6 * cm, doc.width - 9.8 * cm]))
S.append(Spacer(1, 2))
S.append(P("Desarrollo de los hallazgos principales", st_h2))
S.append(P(
    "<b>H3 (U3).</b> La vista <i>v_pedidos_cliente</i> agrega <i>WHERE c.activo = "
    "TRUE</i>, una decisión razonable para clientes vigentes pero incorrecta para "
    "un historial: un cliente que se dio de baja conserva sus pedidos. La prueba "
    "insertó 3 clientes (uno inactivo) y 2 pedidos; la vista devolvió 1 y ocultó "
    "el pedido 2. Decisión aceptada: el historial debe incluir a todos los "
    "clientes y, si se necesita el filtro, aplicarlo en otra vista o en la "
    "consulta, no en la fuente.", st_li))
S.append(P(
    "<b>H4 (U3/U5).</b> Los scripts de U5 se escribieron contra nombres que no "
    "existen en el esquema final: <i>usuario</i> y <i>detalle_pedido</i>. En U3 "
    "las tablas son <i>cliente</i> y <i>linea_pedido</i>. El <i>GRANT</i> de U5 "
    "falla al ejecutarse sobre U3, así que el script de seguridad no es "
    "reproducible tal cual. Decisión aceptada: unificar nombres o agregar una "
    "capa de vistas compatibles antes de aplicar los permisos.", st_li))
S.append(P(
    "<b>H5 (U3), descartado.</b> La sospecha era que <i>registrar_pedido</i> "
    "consumía la secuencia antes de validar y dejaba un pedido huérfano. La "
    "prueba con un producto inexistente mostró que la secuencia avanza de 2 a 3, "
    "pero la tabla <i>pedido</i> sigue con 2 filas y la consulta de huérfanos "
    "devuelve 0: la excepción aborta la transacción. Se descarta como defecto. "
    "Los huecos de secuencia no afectan integridad ni negocio y son esperables.", st_li))
S.append(P(
    "<b>H6 (U5).</b> PostgreSQL no permite <i>ALTER DEFAULT PRIVILEGES</i> con "
    "lista de columnas; el script se corta en esa línea. La consulta a "
    "<i>pg_default_acl</i> confirma que solo se registraron los privilegios de "
    "tabla. Decisión aceptada: quitar las columnas del default privilege y "
    "mantener el grant por columna sobre la tabla existente, o crear una vista "
    "<i>usuario_soporte</i> y otorgar SELECT sobre la vista.", st_li))

# ------------------------------------------------------------------ cierre
S.append(P("6. Evidencias y reproducción", st_h1))
S.append(P(
    "<i>python scripts/simular_tp8.py</i> reproduce las consignas 1 y 2 y "
    "escribe <i>evidencias/00</i> a <i>06</i>; <i>python "
    "scripts/revision_codigo.py</i> reproduce la consigna 3.c en "
    "<i>evidencias/07_revision_codigo.txt</i>. Los datos son inventados y la "
    "copia de PostgreSQL es de laboratorio. El detalle del orden de ejecución "
    "está en <i>README.md</i>; la especificación previa, en <i>docs/kiro/</i>; y "
    "el uso de IA, en <i>docs/bitacora_ia.md</i> y <i>docs/DUIA.md</i>."))

doc.build(S, canvasmaker=NumberedCanvas)
print(f"PDF generado: {SALIDA}")
