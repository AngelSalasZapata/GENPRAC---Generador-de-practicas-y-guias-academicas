import io
from typing import List
from fpdf import FPDF
from src.core.database import obtener_ejercicio_por_id
from src.core.models import ConfiguracionDocumento

TITULO_POR_DEFECTO = "Guía de Prácticas Académicas"
AUTOR_POR_DEFECTO = "Angel Fabiano Salas Zapata"
ETIQUETA_POR_DEFECTO = "Ejercicio"


def _texto_seguro(texto: str) -> str:
    """Convierte el texto a codificación segura para las fuentes del PDF."""
    return texto.encode("cp1252", errors="replace").decode("cp1252")


class PDFEjercicios(FPDF):
    def __init__(self, documento: ConfiguracionDocumento):
        super().__init__('P', 'mm', 'A4')
        self.titulo = _texto_seguro(documento.titulo)
        self.autor = _texto_seguro(documento.autor)

    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, self.titulo, 0, 1, 'C')

        self.set_font('Arial', '', 10)
        self.cell(0, 6, f'Por: {self.autor}', 0, 1, 'C')

        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')


def generar_pdf_ejercicios(
    ejercicios_ids: List[int],
    filename: str = "ejercicios.pdf",
    documento: ConfiguracionDocumento = None,
) -> str:
    """Genera un PDF con los ejercicios en 2 columnas usando los datos personalizados."""
    if documento is None:
        documento = ConfiguracionDocumento()

    etiqueta = _texto_seguro(documento.etiqueta)
    espacio_extra_mm = max(0.0, float(documento.espacio_cm) * 10.0)

    pdf = PDFEjercicios(documento)
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    col_width = 90
    col_spacing = 10
    img_height = 60
    margin_left = 10
    margin_top = 35
    margin_bottom = 20

    x_positions = [margin_left, margin_left + col_width + col_spacing]
    current_col = 0
    current_y = margin_top

    for idx, ej_id in enumerate(ejercicios_ids):
        imagen_bytes = obtener_ejercicio_por_id(ej_id)
        if not imagen_bytes:
            continue

        img_stream = io.BytesIO(imagen_bytes)

        x_pos = x_positions[current_col]

        espacio_celda = img_height + 10 + espacio_extra_mm
        if current_y + espacio_celda > pdf.h - margin_bottom:
            pdf.add_page()
            current_y = margin_top
            current_col = 0
            x_pos = x_positions[current_col]

        pdf.set_xy(x_pos, current_y)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(col_width, 5, f'{etiqueta} {idx + 1}', 0, 0, 'L')

        pdf.image(img_stream, x=x_pos, y=current_y + 5, w=col_width)

        if current_col == 0:
            current_col = 1
        else:
            current_col = 0
            current_y += espacio_celda

    pdf.output(filename)
    return filename