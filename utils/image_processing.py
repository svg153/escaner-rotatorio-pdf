"""
Utilidades para mejorar la calidad de imágenes en PDFs.
"""

from pathlib import Path
from typing import Optional, Tuple
import io

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import numpy as np
    import cv2
    from skimage import filters, exposure
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    import img2pdf
    PDF_IMAGE_AVAILABLE = True
except ImportError:
    PDF_IMAGE_AVAILABLE = False


def check_image_processing_availability() -> bool:
    """Verifica si las dependencias de procesamiento de imagen están disponibles."""
    return IMAGE_PROCESSING_AVAILABLE


def enhance_image(image: 'Image.Image', contrast: float = 1.5, 
                 brightness: float = 1.1, sharpness: float = 1.3) -> 'Image.Image':
    """
    Mejora la calidad de una imagen.
    
    Args:
        image: Imagen PIL
        contrast: Factor de contraste (1.0 = sin cambio)
        brightness: Factor de brillo
        sharpness: Factor de nitidez
    
    Returns:
        Imagen mejorada
    """
    if not IMAGE_PROCESSING_AVAILABLE:
        return image
    
    # Contraste
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(contrast)
    
    # Brillo
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(brightness)
    
    # Nitidez
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(sharpness)
    
    return image


def denoise_image(image: 'Image.Image', strength: int = 10) -> 'Image.Image':
    """
    Elimina ruido de una imagen.
    
    Args:
        image: Imagen PIL
        strength: Fuerza del denoise
    
    Returns:
        Imagen sin ruido
    """
    if not IMAGE_PROCESSING_AVAILABLE:
        return image
    
    # Convertir a array numpy
    img_array = np.array(image)
    
    # Aplicar fastNlMeansDenoisingColored si es color, sino el normal
    if len(img_array.shape) == 3:
        denoised = cv2.fastNlMeansDenoisingColored(img_array, None, strength, strength, 7, 21)
    else:
        denoised = cv2.fastNlMeansDenoising(img_array, None, strength, 7, 21)
    
    return Image.fromarray(denoised)


def binarize_image(image: 'Image.Image', threshold: Optional[int] = None) -> 'Image.Image':
    """
    Convierte una imagen a blanco y negro puro (binarización).
    
    Args:
        image: Imagen PIL
        threshold: Umbral de binarización (None = automático)
    
    Returns:
        Imagen binarizada
    """
    if not IMAGE_PROCESSING_AVAILABLE:
        # Fallback simple
        return image.convert('1')
    
    # Convertir a escala de grises
    gray = image.convert('L')
    img_array = np.array(gray)
    
    if threshold is None:
        # Usar método de Otsu para threshold automático
        threshold = filters.threshold_otsu(img_array)
    
    # Binarizar
    binary = img_array > threshold
    binary_image = Image.fromarray((binary * 255).astype(np.uint8))
    
    return binary_image


def sharpen_image(image: 'Image.Image') -> 'Image.Image':
    """
    Mejora la nitidez de una imagen.
    
    Args:
        image: Imagen PIL
    
    Returns:
        Imagen más nítida
    """
    return image.filter(ImageFilter.SHARPEN)


def despeckle_image(image: 'Image.Image') -> 'Image.Image':
    """
    Elimina manchas y artefactos pequeños.
    
    Args:
        image: Imagen PIL
    
    Returns:
        Imagen sin manchas
    """
    if not IMAGE_PROCESSING_AVAILABLE:
        return image
    
    # Aplicar filtro de mediana
    img_array = np.array(image)
    
    if len(img_array.shape) == 3:
        despeckled = cv2.medianBlur(img_array, 3)
    else:
        despeckled = cv2.medianBlur(img_array, 3)
    
    return Image.fromarray(despeckled)


def autocrop_image(image: 'Image.Image', margin: int = 10) -> 'Image.Image':
    """
    Recorta automáticamente los bordes blancos de una imagen.
    
    Args:
        image: Imagen PIL
        margin: Margen a dejar (en píxeles)
    
    Returns:
        Imagen recortada
    """
    if not IMAGE_PROCESSING_AVAILABLE:
        return image
    
    # Convertir a escala de grises
    gray = np.array(image.convert('L'))
    
    # Encontrar límites del contenido
    # Invertir para que el contenido sea blanco
    inverted = 255 - gray
    
    # Encontrar coordenadas donde hay contenido
    coords = np.column_stack(np.where(inverted > 30))
    
    if len(coords) == 0:
        return image
    
    # Obtener bounding box
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    
    # Añadir margen
    h, w = gray.shape
    y_min = max(0, y_min - margin)
    x_min = max(0, x_min - margin)
    y_max = min(h, y_max + margin)
    x_max = min(w, x_max + margin)
    
    # Recortar
    return image.crop((x_min, y_min, x_max, y_max))


def adjust_dpi(image: 'Image.Image', target_dpi: int = 300) -> 'Image.Image':
    """
    Ajusta el DPI de una imagen.
    
    Args:
        image: Imagen PIL
        target_dpi: DPI objetivo
    
    Returns:
        Imagen con DPI ajustado
    """
    # Obtener DPI actual
    current_dpi = image.info.get('dpi', (72, 72))
    
    if isinstance(current_dpi, tuple):
        current_dpi = current_dpi[0]
    
    if current_dpi == target_dpi:
        return image
    
    # Calcular nuevo tamaño
    scale = target_dpi / current_dpi
    new_size = (int(image.width * scale), int(image.height * scale))
    
    # Redimensionar
    resized = image.resize(new_size, Image.Resampling.LANCZOS)
    
    return resized


def process_pdf_images(input_pdf: str, output_pdf: str, 
                      enhance: bool = False,
                      denoise: bool = False,
                      binarize: bool = False,
                      sharpen: bool = False,
                      despeckle: bool = False,
                      autocrop: bool = False,
                      max_dpi: Optional[int] = None,
                      verbose: bool = True) -> bool:
    """
    Procesa las imágenes de un PDF aplicando varias mejoras.
    
    Args:
        input_pdf: PDF de entrada
        output_pdf: PDF de salida
        enhance: Mejorar contraste y brillo
        denoise: Eliminar ruido
        binarize: Convertir a blanco y negro
        sharpen: Mejorar nitidez
        despeckle: Eliminar manchas
        autocrop: Recortar bordes blancos
        max_dpi: DPI máximo (None = sin límite)
        verbose: Mostrar progreso
    
    Returns:
        True si tuvo éxito
    """
    if not IMAGE_PROCESSING_AVAILABLE or not PDF_IMAGE_AVAILABLE:
        if verbose:
            print("⚠ Dependencias de procesamiento de imagen no disponibles")
        return False
    
    try:
        if verbose:
            print("Procesando imágenes del PDF...")
        
        # Convertir PDF a imágenes
        images = convert_from_path(input_pdf, dpi=300)
        processed_images = []
        
        for i, img in enumerate(images, 1):
            if verbose:
                print(f"  Procesando imagen {i}/{len(images)}...")
            
            # Aplicar procesos en orden
            if autocrop:
                img = autocrop_image(img)
            
            if denoise:
                img = denoise_image(img)
            
            if despeckle:
                img = despeckle_image(img)
            
            if enhance:
                img = enhance_image(img)
            
            if sharpen:
                img = sharpen_image(img)
            
            if binarize:
                img = binarize_image(img)
            
            if max_dpi:
                img = adjust_dpi(img, max_dpi)
            
            processed_images.append(img)
        
        # Convertir imágenes de vuelta a PDF
        if verbose:
            print("Generando PDF desde imágenes procesadas...")
        
        # Guardar imágenes temporales
        image_bytes = []
        for img in processed_images:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            image_bytes.append(img_byte_arr.getvalue())
        
        # Crear PDF
        with open(output_pdf, 'wb') as f:
            f.write(img2pdf.convert(image_bytes))
        
        if verbose:
            print("✓ Procesamiento de imágenes completado")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"⚠ Error al procesar imágenes: {e}")
        return False
