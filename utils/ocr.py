"""
Utilidades para OCR (Reconocimiento Óptico de Caracteres).
"""

import io
from pathlib import Path
from typing import Optional, List
from PIL import Image

try:
    import pytesseract
    from pdf2image import convert_from_path, convert_from_bytes
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    pass


def check_ocr_availability() -> bool:
    """Verifica si las dependencias de OCR están disponibles."""
    return OCR_AVAILABLE


def perform_ocr_on_image(image: Image.Image, lang: str = 'spa') -> str:
    """
    Realiza OCR en una imagen.
    
    Args:
        image: Imagen PIL
        lang: Código de idioma (spa, eng, etc.)
    
    Returns:
        Texto extraído
    """
    if not OCR_AVAILABLE:
        raise ImportError("pytesseract y pdf2image son necesarios para OCR")
    
    try:
        text = pytesseract.image_to_string(image, lang=lang)
        return text
    except Exception as e:
        print(f"⚠ Error en OCR: {e}")
        return ""


def add_ocr_layer_to_pdf(input_pdf: str, output_pdf: str, lang: str = 'spa', 
                         verbose: bool = True) -> bool:
    """
    Añade una capa de texto OCR a un PDF escaneado.
    
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
            
            # Realizar OCR
            text = perform_ocr_on_image(image, lang=lang)
            
            # Añadir la página original
            writer.add_page(page)
            
            # TODO: Añadir capa de texto invisible sobre la página
            # Esto requiere coordenadas exactas, por ahora solo extraemos el texto
        
        # Guardar PDF
        with open(output_pdf, 'wb') as f:
            writer.write(f)
        
        if verbose:
            print("✓ OCR completado")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"⚠ Error al realizar OCR: {e}")
        return False


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
    except:
        return ['spa', 'eng']  # Valores por defecto
