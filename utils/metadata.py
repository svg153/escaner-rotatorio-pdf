"""
Utilidades para añadir metadata y marcas de agua a PDFs.
"""

from datetime import datetime
from typing import Optional

try:
    import io

    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    METADATA_AVAILABLE = True
except ImportError:  # pragma: no cover
    METADATA_AVAILABLE = False

DEFAULT_PAGE_SIZE = (595.27, 841.89)
if "A4" in globals():
    DEFAULT_PAGE_SIZE = A4


def check_metadata_availability() -> bool:
    """Verifica si las dependencias están disponibles."""
    return METADATA_AVAILABLE


def add_metadata(
    input_pdf: str,
    output_pdf: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    subject: Optional[str] = None,
    keywords: Optional[str] = None,
    creator: Optional[str] = None,
    verbose: bool = True,
) -> bool:
    """
    Añade metadata a un PDF.

    Args:
        input_pdf: PDF de entrada
        output_pdf: PDF de salida
        title: Título del documento
        author: Autor
        subject: Asunto
        keywords: Palabras clave
        creator: Creador
        verbose: Mostrar información

    Returns:
        True si tuvo éxito
    """
    if not METADATA_AVAILABLE:
        if verbose:
            print("⚠ PyPDF2 no disponible para metadata")
        return False

    try:
        reader = PdfReader(input_pdf)
        writer = PdfWriter()

        # Copiar todas las páginas
        for page in reader.pages:
            writer.add_page(page)

        # Añadir metadata
        metadata = {}
        if title:
            metadata["/Title"] = title
        if author:
            metadata["/Author"] = author
        if subject:
            metadata["/Subject"] = subject
        if keywords:
            metadata["/Keywords"] = keywords
        if creator:
            metadata["/Creator"] = creator
        else:
            metadata["/Creator"] = "PDF Merger Tool"

        metadata["/Producer"] = "PDF Merger Tool"
        metadata["/CreationDate"] = datetime.now().strftime("D:%Y%m%d%H%M%S")

        writer.add_metadata(metadata)

        # Guardar
        with open(output_pdf, "wb") as f:
            writer.write(f)

        if verbose:
            print("✓ Metadata añadida")

        return True

    except Exception as e:
        if verbose:
            print(f"⚠ Error al añadir metadata: {e}")
        return False


def create_watermark_page(
    text: str,
    page_size: tuple | None = None,
    opacity: float = 0.3,
    font_size: int = 60,
    rotation: int = 45,
) -> bytes:
    """
    Crea una página con marca de agua.

    Args:
        text: Texto de la marca de agua
        page_size: Tamaño de página
        opacity: Opacidad (0-1)
        font_size: Tamaño de fuente
        rotation: Rotación en grados

    Returns:
        PDF bytes con la marca de agua
    """
    page_size = page_size or DEFAULT_PAGE_SIZE

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=page_size)

    # Configurar opacidad y color
    can.setFillColorRGB(0.5, 0.5, 0.5, alpha=opacity)

    # Posicionar en el centro
    width, height = page_size
    can.translate(width / 2, height / 2)
    can.rotate(rotation)

    # Dibujar texto
    can.setFont("Helvetica-Bold", font_size)
    text_width = can.stringWidth(text, "Helvetica-Bold", font_size)
    can.drawString(-text_width / 2, 0, text)

    can.save()
    packet.seek(0)

    return packet.read()


def add_text_watermark(
    input_pdf: str,
    output_pdf: str,
    watermark_text: str,
    opacity: float = 0.3,
    font_size: int = 60,
    rotation: int = 45,
    verbose: bool = True,
) -> bool:
    """
    Añade una marca de agua de texto a todas las páginas.

    Args:
        input_pdf: PDF de entrada
        output_pdf: PDF de salida
        watermark_text: Texto de la marca de agua
        opacity: Opacidad (0-1)
        font_size: Tamaño de fuente
        rotation: Rotación en grados
        verbose: Mostrar información

    Returns:
        True si tuvo éxito
    """
    if not METADATA_AVAILABLE:
        if verbose:
            print("⚠ Dependencias no disponibles para marca de agua")
        return False

    try:
        if verbose:
            print(f"Añadiendo marca de agua: '{watermark_text}'...")

        reader = PdfReader(input_pdf)
        writer = PdfWriter()

        # Obtener tamaño de la primera página
        first_page = reader.pages[0]
        page_size = (
            float(first_page.mediabox.width),
            float(first_page.mediabox.height),
        )

        # Crear marca de agua
        watermark_bytes = create_watermark_page(
            watermark_text, page_size, opacity, font_size, rotation
        )

        watermark_pdf = PdfReader(io.BytesIO(watermark_bytes))
        watermark_page = watermark_pdf.pages[0]

        # Aplicar a todas las páginas
        for i, page in enumerate(reader.pages, 1):
            page.merge_page(watermark_page)
            writer.add_page(page)

            if verbose and i % 10 == 0:
                print(f"  Procesadas {i}/{len(reader.pages)} páginas...")

        # Guardar
        with open(output_pdf, "wb") as f:
            writer.write(f)

        if verbose:
            print("✓ Marca de agua añadida")

        return True

    except Exception as e:
        if verbose:
            print(f"⚠ Error al añadir marca de agua: {e}")
        return False


def add_page_numbers(
    input_pdf: str,
    output_pdf: str,
    position: str = "bottom-center",
    font_size: int = 10,
    margin: int = 20,
    verbose: bool = True,
) -> bool:
    """
    Añade números de página al PDF.

    Args:
        input_pdf: PDF de entrada
        output_pdf: PDF de salida
        position: Posición ('bottom-center', 'bottom-right', 'top-center', etc.)
        font_size: Tamaño de fuente
        margin: Margen desde el borde
        verbose: Mostrar información

    Returns:
        True si tuvo éxito
    """
    if not METADATA_AVAILABLE:
        if verbose:
            print("⚠ Dependencias no disponibles")
        return False

    try:
        if verbose:
            print("Añadiendo números de página...")

        reader = PdfReader(input_pdf)
        writer = PdfWriter()

        total_pages = len(reader.pages)

        for page_num, page in enumerate(reader.pages, 1):
            # Crear página con número
            packet = io.BytesIO()
            page_size = (float(page.mediabox.width), float(page.mediabox.height))
            can = canvas.Canvas(packet, pagesize=page_size)

            # Calcular posición
            width, height = page_size
            if "bottom" in position:
                y = margin
            else:  # top
                y = height - margin

            if "center" in position:
                x = width / 2
                can.drawCentredString(x, y, f"{page_num}")
            elif "right" in position:
                x = width - margin
                can.drawRightString(x, y, f"{page_num}")
            else:  # left
                x = margin
                can.drawString(x, y, f"{page_num}")

            can.setFont("Helvetica", font_size)
            can.save()

            # Merge con página original
            packet.seek(0)
            number_pdf = PdfReader(packet)
            page.merge_page(number_pdf.pages[0])
            writer.add_page(page)

        # Guardar
        with open(output_pdf, "wb") as f:
            writer.write(f)

        if verbose:
            print(f"✓ Números de página añadidos (1-{total_pages})")

        return True

    except Exception as e:
        if verbose:
            print(f"⚠ Error al añadir números de página: {e}")
        return False
