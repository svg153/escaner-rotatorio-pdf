"""
Utilidades para detección y eliminación de páginas en blanco.
"""

from typing import List, Tuple

try:
    import numpy as np
    from PIL import Image

    BLANK_DETECTION_AVAILABLE = True
except ImportError:  # pragma: no cover
    BLANK_DETECTION_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    from PyPDF2 import PdfReader, PdfWriter

    PDF_AVAILABLE = True
except ImportError:  # pragma: no cover
    PDF_AVAILABLE = False


def check_blank_detection_availability() -> bool:
    """Verifica si las dependencias están disponibles."""
    return BLANK_DETECTION_AVAILABLE and PDF_AVAILABLE


def is_blank_image(image: "Image.Image", threshold: float = 0.99) -> bool:
    """
    Detecta si una imagen está en blanco o casi en blanco.

    Args:
        image: Imagen PIL
        threshold: Umbral de "blancura" (0-1, donde 1 = completamente blanco)

    Returns:
        True si la imagen está en blanco
    """
    if not BLANK_DETECTION_AVAILABLE:
        return False

    # Convertir a escala de grises
    gray = np.array(image.convert("L"))

    # Calcular el porcentaje de píxeles "blancos" (> 250)
    white_pixels = np.sum(gray > 250)
    total_pixels = gray.size
    white_ratio = white_pixels / total_pixels

    return white_ratio >= threshold


def detect_blank_pages(
    pdf_path: str, threshold: float = 0.99, verbose: bool = True
) -> List[int]:
    """
    Detecta las páginas en blanco de un PDF.

    Args:
        pdf_path: Ruta al PDF
        threshold: Umbral de "blancura"
        verbose: Mostrar progreso

    Returns:
        Lista de números de página en blanco (base 0)
    """
    if not check_blank_detection_availability():
        if verbose:
            print("⚠ Dependencias de detección de páginas en blanco no disponibles")
        return []

    try:
        if verbose:
            print("Detectando páginas en blanco...")

        # Convertir PDF a imágenes (baja resolución para velocidad)
        images = convert_from_path(pdf_path, dpi=100)

        blank_pages = []
        for i, img in enumerate(images):
            if is_blank_image(img, threshold):
                blank_pages.append(i)
                if verbose:
                    print(f"  Página {i + 1} detectada como blanca")

        if verbose and not blank_pages:
            print("  No se detectaron páginas en blanco")

        return blank_pages

    except Exception as e:
        if verbose:
            print(f"⚠ Error al detectar páginas en blanco: {e}")
        return []


def remove_blank_pages(
    input_pdf: str, output_pdf: str, threshold: float = 0.99, verbose: bool = True
) -> Tuple[bool, List[int]]:
    """
    Elimina las páginas en blanco de un PDF.

    Args:
        input_pdf: PDF de entrada
        output_pdf: PDF de salida
        threshold: Umbral de "blancura"
        verbose: Mostrar progreso

    Returns:
        Tupla (éxito, lista de páginas eliminadas)
    """
    if not check_blank_detection_availability():
        if verbose:
            print("⚠ Dependencias no disponibles")
        return False, []

    try:
        # Detectar páginas en blanco
        blank_pages = detect_blank_pages(input_pdf, threshold, verbose)

        if not blank_pages:
            if verbose:
                print("No hay páginas en blanco para eliminar")
            # Copiar el archivo original
            import shutil

            shutil.copy2(input_pdf, output_pdf)
            return True, []

        # Crear nuevo PDF sin las páginas en blanco
        reader = PdfReader(input_pdf)
        writer = PdfWriter()

        if verbose:
            print(f"Eliminando {len(blank_pages)} páginas en blanco...")

        for i, page in enumerate(reader.pages):
            if i not in blank_pages:
                writer.add_page(page)

        # Guardar
        with open(output_pdf, "wb") as f:
            writer.write(f)

        if verbose:
            original_pages = len(reader.pages)
            final_pages = len(writer.pages)
            print(f"✓ Páginas eliminadas: {len(blank_pages)}")
            print(f"  Páginas originales: {original_pages}")
            print(f"  Páginas finales: {final_pages}")

        return True, blank_pages

    except Exception as e:
        if verbose:
            print(f"⚠ Error al eliminar páginas en blanco: {e}")
        return False, []
