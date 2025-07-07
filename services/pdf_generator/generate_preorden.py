from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import PyPDF2
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from datetime import datetime
import os
from textwrap import wrap
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

# ----------------------------------------------------------------------
# Utilidad para “wrappear” texto
# ----------------------------------------------------------------------
def wrapped_draw_string(c, text, x, y, fontName, fontSize, max_width, leading=12):
    words = text.split()
    line, y_offset = "", 0
    for word in words:
        test_line = f"{line} {word}".strip()
        if stringWidth(test_line, fontName, fontSize) <= max_width:
            line = test_line
        else:
            c.drawString(x, y - y_offset, line)
            y_offset += leading
            line = word
    if line:
        c.drawString(x, y - y_offset, line)
    return y_offset

# ----------------------------------------------------------------------
# Registro de fuentes (sobrescribe las advertencias originales)
# ----------------------------------------------------------------------
FONT_REGULAR = "OpenSauce"
FONT_BOLD    = "OpenSauceBold"

def _register_fonts():
    font_path = "resources/fonts/OpenSauceSans-Regular.ttf"
    font_bold = "resources/fonts/OpenSauceSans-Bold.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, font_path))
    if os.path.exists(font_bold):
        pdfmetrics.registerFont(TTFont(FONT_BOLD,   font_bold))

_register_fonts()

# ----------------------------------------------------------------------
# Capa de datos (overlay)
# ----------------------------------------------------------------------
def create_overlay(data: dict, overlay_path: str, surcharge_key: str = "sales_surcharges") -> None:
    c = canvas.Canvas(overlay_path, pagesize=letter)
    current_date = datetime.today().strftime("%d/%m/%Y")

    c.setFont(FONT_REGULAR, 6)
    c.drawString(282, 470, data.get("no_solicitud", "").upper())

    c.setFont(FONT_BOLD, 7)
    c.drawString(500, 669, current_date)

    c.setFont(FONT_REGULAR, 7)
    c.drawString(115, 583, data.get("client", "").upper())
    c.drawString(95, 573, data.get("customer_phone", "").upper())
    c.drawString(125, 563, data.get("customer_address", "").upper())
    c.drawString(170, 553, data.get("customer_account", "").upper())
    c.drawString(95, 543, data.get("customer_nit", "").upper())
    c.drawString(120, 533, data.get("customer_contact", "").upper())
    c.drawString(105, 523, data.get("customer_email", "").upper())

    # ----------------------- datos transporte / referencia --------------------
    c.setFont(FONT_REGULAR, 6)
    c.drawString(282, 586, data.get("bl_awb", "").upper())
    c.drawString(282, 546, data.get("pol_aol", "").upper())
    c.drawString(282, 506, data.get("pod_aod", "").upper())

    c.drawString(442, 586, data.get("shipper", "").upper())
    c.drawString(442, 546, data.get("consignee", "").upper())
    ref_text     = data.get("reference", "").upper()
    max_chars    = 20            # ~ ancho de unos 120 pt a font-size 7 (ajústalo)
    line_height  = 11           # puntos de separación vertical
    x_ref        = 442
    y_ref_start  = 506           # coordenada de la 1.ª línea

    c.setFont(FONT_REGULAR, 6)

    for i, line in enumerate(wrap(ref_text, max_chars)):
        y = y_ref_start - i * line_height
        c.drawString(x_ref, y, line)

    # ────────────────── Nombres de contenedor uno debajo de otro ──────────────────
    c.setFont(FONT_REGULAR, 6)

    x_pos       = 75          # columna izquierda
    y_start     = 470         # coordenada Y inicial
    line_height = 11          # separación vertical

    cargo_type = (data.get("cargo_type") or "").strip().lower()
    container_details = data.get("container_details") or {}

    if cargo_type == "carga suelta" or not container_details:
        unidad = str(data.get("unidad_medida", "")).upper()
        cantidad = data.get("cantidad_suelta", "")
        
        c.drawString(x_pos, y_start,  f"{cantidad} {unidad}")
    else:
        #   ► Caso contenedores
        for ctype, details in container_details.items():
            for name in details.get("names", []):
                c.drawString(x_pos, y_start, name.upper())
                y_start -= line_height


    # ------------------------------ tabla costos ------------------------------
    table_data = []

    for surcharge in data.get(surcharge_key, []):
        concept   = surcharge.get("concept", "")
        quantity  = surcharge.get("quantity", 0)
        rate      = surcharge.get("rate", 0)
        total     = surcharge.get("total", rate * quantity)  # en caso de que 'total' no venga
        currency  = surcharge.get("currency", "")

        table_data.append([
            concept,                  # Concepto
            str(quantity),            # Cantidad
            f"${rate:,.2f}",   # Tarifa / Rate
            f"${total:,.2f}",  # Total
            currency                  # Moneda (columna opcional, si tu tabla la usa)
        ])

    # Dimensiones de columna
    col_widths = [180, 150, 20, 130, 50]
    table      = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
        ("FONTSIZE", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0.3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0.3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 1),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 1),
    ]))

    totales = defaultdict(Decimal)

    for s in data.get("sales_surcharges", []):
        currency = s.get("currency", "").upper()
        total    = Decimal(s.get("total", 0)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        totales[currency] += total

    x, y = 10, 358 
    table.wrapOn(c, 0, 0)
    table.drawOn(c, x, y - table._height)

    label_font   = FONT_BOLD   
    value_font   = FONT_BOLD
    font_size    = 8
    x_label      = 450    
    x_value      = 510    
    y_start      = 210        
    line_height  = 13        

    # ── Dibujo ────────────────────────────────────────────────────────────────────
    c.setFont(label_font, font_size)

    for i, (curr, total) in enumerate(totales.items()):
        y = y_start - i * line_height

        c.drawString(x_label, y, f"TOTAL {curr}")

        c.setFont(value_font, font_size)
        formatted = f"${total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        c.drawString(x_value, y, formatted)   
        c.setFont(label_font, font_size)        
    
    #Notas finales-----------------
    comments     = data.get("final_comments", "").upper()
    max_chars    = 110            # ajusta al ancho de tu columna ↔
    line_height  = 11            # separación vertical
    x_comments   = 60            # coordenada X donde empiezan las notas
    y_start      = 120           # coordenada Y de la primera línea

    c.setFont(FONT_REGULAR, 6)

    for i, line in enumerate(wrap(comments, max_chars)):
        y = y_start - i * line_height
        c.drawString(x_comments, y, line)

    c.save()

# ----------------------------------------------------------------------
# Combinar plantilla + overlay
# ----------------------------------------------------------------------

def merge_pdfs(template_path, overlay_path, output_path):
    template_pdf = PyPDF2.PdfReader(template_path)
    overlay_pdf  = PyPDF2.PdfReader(overlay_path)
    writer       = PyPDF2.PdfWriter()

    for idx, template_page in enumerate(template_pdf.pages):
        if idx < len(overlay_pdf.pages):
            template_page.merge_page(overlay_pdf.pages[idx])
        writer.add_page(template_page)

    with open(output_path, "wb") as f_out:
        writer.write(f_out)

# ----------------------------------------------------------------------
# Función pública que genera el PDF
# ----------------------------------------------------------------------
def generate_pdf(
    quotation_data: dict,
    template_path="resources/templates/PRE ORDEN COSTOS 1.pdf",
    output_path="resources/output/pre_orden_ventas.pdf",
    overlay_path="resources/templates/overlay.pdf",
):
    create_overlay(quotation_data, overlay_path)
    merge_pdfs(template_path, overlay_path, output_path)
    return output_path

def generate_archives(quotation_data: dict, variant: str = "ventas"):

    config = {
        "ventas": {
            "surcharge_key": "sales_surcharges",
            "template":      "resources/templates/ORDER VENTAS SHADIA 1.pdf",
            "output":        "resources/output/pre_orden_ventas.pdf",
        },
        "costos": {
            "surcharge_key": "cost_surcharges",
            "template":      "resources/templates/PRE ORDEN COSTOS SHADIA 1.pdf",
            "output":        "resources/output/pre_orden_costos.pdf",
        },
    }

    if variant not in config:
        raise ValueError(f"Variant desconocida: {variant}")

    cfg          = config[variant]
    overlay_path = f"resources/temp/overlay_{variant}.pdf"
    os.makedirs(os.path.dirname(overlay_path), exist_ok=True)

    create_overlay(quotation_data, overlay_path, cfg["surcharge_key"])
    merge_pdfs(cfg["template"], overlay_path, cfg["output"])

    return cfg["output"]