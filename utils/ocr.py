"""
Utilidades para OCR (Reconocimiento Óptico de Caracteres).
"""

import io
import logging
from typing import List, Optional

from PIL import Image

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from pdf2image import convert_from_path

    OCR_AVAILABLE = True
except ImportError:  # pragma: no cover
    OCR_AVAILABLE = False
    convert_from_path = None  # type: ignore[assignment,misc]

try:
    from PyPDF2 import PdfReader, PdfWriter
    from PyPDF2.generic import BooleanObject, NameObject, NumberObject, StreamObject

    PDF_WRITER_AVAILABLE = True
except ImportError:
    PDF_WRITER_AVAILABLE = False


def check_ocr_availability() -> bool:
    """Verifica si las dependencias de OCR están disponibles."""
    return OCR_AVAILABLE


def perform_ocr_on_image(image: Image.Image, lang: str = "spa") -> str:
    """
    Realiza OCR en una imagen.

    Args:
        image: Imagen PIL
        lang: Código de idioma (spa, eng, etc.)

    Returns:
        Texto extraído
    """
    if not OCR_AVAILABLE:
        raise ImportError(
            "pytesseract y pdf2image son necesarios para OCR"
        )  # pragma: no cover

    try:
        text = pytesseract.image_to_string(image, lang=lang)
        return text
    except Exception as e:
        logger.warning("Error en OCR: %s", e)
        return ""


def perform_ocr_with_confidence(image: Image.Image, lang: str = "spa") -> dict:
    """
    Realiza OCR en una imagen y devuelve texto + confianza + bounding boxes.

    Args:
        image: Imagen PIL
        lang: Código de idioma

    Returns:
        Dict con 'text', 'confidence', 'blocks'
    """
    if not OCR_AVAILABLE:
        return {"text": "", "confidence": 0, "blocks": []}  # pragma: no cover

    try:
        data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(image, lang=lang)

        # Calcular confianza media
        confidences = [c for c in data["conf"] if c > 0]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        # Extraer bloques de texto con posición
        blocks = []
        for i in range(len(data["text"])):
            if data["conf"][i] > 0 and data["text"][i].strip():
                blocks.append({
                    "text": data["text"][i].strip(),
                    "confidence": data["conf"][i],
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                })

        return {
            "text": text.strip(),
            "confidence": avg_conf,
            "blocks": blocks,
        }
    except Exception as e:
        logger.warning("Error en OCR con confianza: %s", e)
        return {"text": "", "confidence": 0, "blocks": []}


def add_ocr_layer_to_pdf(
    input_pdf: str, output_pdf: str, lang: str = "spa", verbose: bool = True
) -> bool:
    """
    Añade una capa de texto OCR invisible a un PDF escaneado.

    Usa pdf2image para convertir páginas a imágenes, realiza OCR con
    pytesseract, y añade el texto como capa invisible usando PyPDF2.

    Args:
        input_pdf: Ruta al PDF de entrada
        output_pdf: Ruta al PDF de salida
        lang: Código de idioma para OCR
        verbose: Mostrar progreso

    Returns:
        True si tuvo éxito
    """
    if not OCR_AVAILABLE:
        if verbose:
            print("⚠ pytesseract y pdf2image no están instalados")
        return False

    if not PDF_WRITER_AVAILABLE:
        if verbose:
            print("⚠ PyPDF2 no disponible para añadir capa OCR")
        return False

    try:
        if verbose:
            print(f"Realizando OCR en PDF (idioma: {lang})...")

        # Convertir páginas PDF a imágenes
        images = convert_from_path(input_pdf, dpi=300)

        reader = PdfReader(input_pdf)
        writer = PdfWriter()

        for i, (page, image) in enumerate(zip(reader.pages, images), 1):
            if verbose:
                print(f"  Procesando página {i}/{len(images)}...")

            # Realizar OCR con información de bloques
            result = perform_ocr_with_confidence(image, lang=lang)

            if result["text"] and verbose:
                # Mostrar primera línea como preview
                first_line = result["text"].split("\n")[0][:80]
                print(f"    Texto detectado: \"{first_line}...\" (confianza: {result['confidence']:.1f}%)")

            # Añadir la página original
            writer.add_page(page)

            # Añadir capa de texto invisible
            _add_invisible_text_layer(writer, page, result, image)

        # Guardar PDF
        with open(output_pdf, "wb") as f:
            writer.write(f)

        if verbose:
            print("✓ OCR completado")

        return True

    except Exception as e:
        if verbose:
            print(f"⚠ Error al realizar OCR: {e}")
        return False


def _add_invisible_text_layer(
    writer: "PdfWriter",
    page: "PdfReader.pages[0]",
    ocr_result: dict,
    image: Image.Image,
) -> None:
    """
    Añade una capa de texto invisible sobre la página.
    """
    if not ocr_result["blocks"]:
        return

    lines = ["0 g\n"]

    for block in ocr_result["blocks"]:
        text = block["text"].replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        scale = 72.0 / 300.0
        x = block["left"] * scale
        y = image.height - block["top"] - block["height"]
        y = y * scale
        font_size = max(4, block["height"] * scale * 0.8)
        lines.append(f"BT /F1 {font_size:.2f} Tf {x:.2f} {y:.2f} Td ({text}) Tj ET\n")

    content_stream = "\n".join(lines) + "\n"
    content_bytes = content_stream.encode("utf-8")

    page_obj = writer.pages[-1]

    from PyPDF2.generic import NameObject, StreamObject, DictionaryObject, NumberObject

    # Añadir fuente Helvetica al recurso de fuentes de la página
    if "/Resources" not in page_obj:
        page_obj[NameObject("/Resources")] = DictionaryObject()
    resources = page_obj["/Resources"]
    if isinstance(resources, dict):
        if "/Font" not in resources:
            font_dict = DictionaryObject()
            resources[NameObject("/Font")] = font_dict
        font_dict = resources.get("/Font", {})
        if isinstance(font_dict, dict) and "/F1" not in font_dict:
            font_entry = DictionaryObject()
            font_entry[NameObject("/Type")] = NameObject("/Font")
            font_entry[NameObject("/Subtype")] = NameObject("/Type1")
            font_entry[NameObject("/BaseFont")] = NameObject("/Helvetica")
            font_entry[NameObject("/Encoding")] = NameObject("/WinAnsiEncoding")
            font_dict[NameObject("/F1")] = font_entry

    # Crear StreamObject con el contenido invisible
    stream_obj = StreamObject()
    stream_obj._data = content_bytes
    stream_obj[NameObject("/Length")] = NumberObject(len(content_bytes))

    # Asignar como /Contents de la página
    page_obj[NameObject("/Contents")] = stream_obj


def get_available_languages() -> List[str]:
    """
    Obtiene los idiomas disponibles en Tesseract.

    Returns:
        Lista de códigos de idioma
    """
    if not OCR_AVAILABLE:
        return []

    try:
        langs = pytesseract.get_languages()
        return langs
    except Exception:
        return ["spa", "eng"]  # Valores por defecto


def extract_text_from_pdf(pdf_path: str, lang: str = "spa") -> str:
    """
    Extrae todo el texto de un PDF mediante OCR.

    Args:
        pdf_path: Ruta al PDF
        lang: Código de idioma

    Returns:
        Texto completo extraído
    """
    if not OCR_AVAILABLE:
        return ""  # pragma: no cover

    try:
        images = convert_from_path(pdf_path, dpi=300)
        texts = []
        for i, image in enumerate(images, 1):
            text = perform_ocr_on_image(image, lang=lang)
            if text:
                texts.append(f"--- Página {i} ---\n{text}")

        return "\n\n".join(texts)
    except Exception as e:
        logger.warning("Error al extraer texto de PDF: %s", e)
        return ""
