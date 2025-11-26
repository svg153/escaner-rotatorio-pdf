"""
Utilidades para detección y corrección de inclinación (deskew).
"""

from typing import Tuple
import math

try:
    from PIL import Image
    import numpy as np
    import cv2

    DESKEW_AVAILABLE = True
except ImportError:
    DESKEW_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    import img2pdf

    PDF_IMAGE_AVAILABLE = True
except ImportError:
    PDF_IMAGE_AVAILABLE = False


def check_deskew_availability() -> bool:
    """Verifica si las dependencias de deskew están disponibles."""
    return DESKEW_AVAILABLE


def detect_skew_angle(image: "Image.Image") -> float:
    """
    Detecta el ángulo de inclinación de una imagen.

    Args:
        image: Imagen PIL

    Returns:
        Ángulo en grados (positivo = sentido horario)
    """
    if not DESKEW_AVAILABLE:
        return 0.0

    # Convertir a escala de grises
    gray = np.array(image.convert("L"))

    # Invertir colores (texto negro sobre fondo blanco)
    gray = 255 - gray

    # Aplicar threshold
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Detectar bordes
    edges = cv2.Canny(binary, 50, 150, apertureSize=3)

    # Detectar líneas con transformada de Hough
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10
    )

    if lines is None or len(lines) == 0:
        return 0.0

    # Calcular ángulos de todas las líneas
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))

        # Normalizar ángulo entre -45 y 45
        if angle < -45:
            angle += 90
        elif angle > 45:
            angle -= 90

        angles.append(angle)

    # Calcular mediana de ángulos (más robusto que la media)
    if not angles:
        return 0.0

    median_angle = np.median(angles)

    return median_angle


def rotate_image(
    image: "Image.Image",
    angle: float,
    fill_color: Tuple[int, int, int] = (255, 255, 255),
) -> "Image.Image":
    """
    Rota una imagen por el ángulo especificado.

    Args:
        image: Imagen PIL
        angle: Ángulo en grados (positivo = sentido anti-horario)
        fill_color: Color de relleno para áreas vacías

    Returns:
        Imagen rotada
    """
    # Rotar con expand=True para no cortar contenido
    rotated = image.rotate(angle, expand=True, fillcolor=fill_color)
    return rotated


def auto_deskew_image(
    image: "Image.Image", threshold: float = 0.5, verbose: bool = False
) -> Tuple["Image.Image", float]:
    """
    Detecta y corrige automáticamente la inclinación de una imagen.

    Args:
        image: Imagen PIL
        threshold: Umbral mínimo de ángulo para corregir (grados)
        verbose: Mostrar información

    Returns:
        Tupla (imagen corregida, ángulo detectado)
    """
    if not DESKEW_AVAILABLE:
        return image, 0.0

    # Detectar ángulo
    angle = detect_skew_angle(image)

    if verbose and abs(angle) > threshold:
        print(f"    Detectado ángulo de inclinación: {angle:.2f}°")

    # Solo corregir si el ángulo supera el umbral
    if abs(angle) < threshold:
        return image, angle

    # Corregir inclinación
    corrected = rotate_image(image, -angle)  # Negativo porque queremos corregir

    if verbose:
        print(f"    Corregida inclinación de {angle:.2f}°")

    return corrected, angle


def auto_deskew_pdf(
    input_pdf: str, output_pdf: str, threshold: float = 0.5, verbose: bool = True
) -> bool:
    """
    Detecta y corrige automáticamente la inclinación de todas las páginas de un PDF.

    Args:
        input_pdf: PDF de entrada
        output_pdf: PDF de salida
        threshold: Umbral mínimo de ángulo para corregir (grados)
        verbose: Mostrar progreso

    Returns:
        True si tuvo éxito
    """
    if not DESKEW_AVAILABLE or not PDF_IMAGE_AVAILABLE:
        if verbose:
            print("⚠ Dependencias de auto-deskew no disponibles")
        return False

    try:
        if verbose:
            print("Detectando y corrigiendo inclinación automáticamente...")

        # Convertir PDF a imágenes
        images = convert_from_path(input_pdf, dpi=300)
        corrected_images = []

        for i, img in enumerate(images, 1):
            if verbose:
                print(f"  Analizando página {i}/{len(images)}...")

            corrected, angle = auto_deskew_image(
                img, threshold=threshold, verbose=verbose
            )
            corrected_images.append(corrected)

        # Convertir imágenes de vuelta a PDF
        if verbose:
            print("Generando PDF corregido...")

        import io

        image_bytes = []
        for img in corrected_images:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            image_bytes.append(img_byte_arr.getvalue())

        with open(output_pdf, "wb") as f:
            f.write(img2pdf.convert(image_bytes))

        if verbose:
            print("✓ Auto-deskew completado")

        return True

    except Exception as e:
        if verbose:
            print(f"⚠ Error en auto-deskew: {e}")
        return False
