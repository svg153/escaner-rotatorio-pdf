#!/usr/bin/env python3
"""
CLI for PDF Merger Tool.
Command-line interface separated from core logic.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import yaml

from models.pdf_processor import PDFInput, PDFMergerCore, ProcessingOptions


def load_profile(profile_name: str) -> Optional[dict]:
    """Load a predefined profile from YAML."""
    profile_path = Path(__file__).parent / "config" / "profiles.yaml"

    if not profile_path.exists():
        return None

    try:
        with open(profile_path, "r") as f:
            profiles = yaml.safe_load(f)
            return profiles.get(profile_name)
    except Exception as e:
        print(f"⚠ Error al cargar perfil: {e}")
        return None


def parse_pdf_inputs(args) -> List[PDFInput]:
    """Parse PDF inputs from command line arguments."""
    pdf_inputs = []

    if args.pdfs:
        # Multiple PDFs provided
        for pdf_path in args.pdfs:
            pdf_inputs.append(PDFInput(path=pdf_path, reverse=False))

    # Apply reverse flags if specified
    if args.reverse_pdfs:
        for idx in args.reverse_pdfs:
            if 0 <= idx < len(pdf_inputs):
                pdf_inputs[idx].reverse = True

    return pdf_inputs


def create_processing_options(args) -> ProcessingOptions:
    """Create ProcessingOptions from command line arguments."""
    return ProcessingOptions(
        # OCR
        ocr=args.ocr,
        ocr_lang=args.ocr_lang,
        # Deskew
        deskew=args.deskew,
        auto_deskew=args.auto_deskew,
        deskew_threshold=args.deskew_threshold,
        # Image processing
        enhance=args.enhance,
        denoise=args.denoise,
        binarize=args.binarize,
        sharpen=args.sharpen,
        despeckle=args.despeckle,
        autocrop=args.autocrop,
        max_dpi=args.max_dpi,
        # Blank pages
        remove_blank=args.remove_blank,
        blank_threshold=args.blank_threshold,
        # Optimization
        optimize=args.optimize,
        compress_level=args.compress_level,
        lossy=args.lossy,
        lossy_dpi=args.lossy_dpi,
        lossy_quality=args.lossy_quality,
        # Metadata
        title=args.title,
        author=args.author,
        subject=args.subject,
        keywords=args.keywords,
        # Watermark
        watermark=args.watermark,
        watermark_opacity=args.watermark_opacity,
        watermark_size=args.watermark_size,
        watermark_rotation=args.watermark_rotation,
        # Page numbers
        page_numbers=args.page_numbers,
        page_number_position=args.page_number_position,
        page_number_size=args.page_number_size,
        page_number_margin=args.page_number_margin,
        # General
        verbose=not args.quiet,
    )


def apply_profile_to_args(args, profile: dict):
    """Apply profile settings to args (don't override explicit args)."""
    defaults = {
        "enhance": False,
        "denoise": False,
        "binarize": False,
        "sharpen": False,
        "despeckle": False,
        "autocrop": False,
        "remove_blank": False,
        "ocr": False,
        "optimize": False,
        "auto_deskew": False,
        "deskew": False,
    }

    for key, value in profile.items():
        attr_name = key.replace("-", "_")
        # Only apply if arg is at default value
        if hasattr(args, attr_name):
            current_value = getattr(args, attr_name)
            default_value = defaults.get(attr_name, None)
            if current_value == default_value or current_value is None:
                setattr(args, attr_name, value)


def main():
    parser = argparse.ArgumentParser(
        description="Herramienta avanzada para procesar y mezclar PDFs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Mezclar múltiples PDFs
  %(prog)s pdf1.pdf pdf2.pdf pdf3.pdf -o output.pdf

  # Intercalar dos PDFs (páginas impares y pares)
  %(prog)s impares.pdf pares.pdf -o output.pdf --interleave --reverse-pdfs 1

  # Procesar un solo PDF
  %(prog)s documento.pdf -o procesado.pdf --ocr --optimize

  # Usar perfil predefinido
  %(prog)s *.pdf -o resultado.pdf --profile document

  # Procesamiento completo
  %(prog)s impares.pdf pares.pdf -o resultado.pdf --interleave --reverse-pdfs 1 \\
    --ocr --ocr-lang spa --auto-deskew --enhance --optimize \\
    --remove-blank --watermark "CONFIDENCIAL" --page-numbers
        """,
    )

    # Input PDFs
    parser.add_argument("pdfs", nargs="*", help="Archivos PDF de entrada")
    parser.add_argument("-o", "--output", required=True, help="Archivo PDF de salida")

    # Merging options
    parser.add_argument(
        "--interleave",
        action="store_true",
        help="Intercalar páginas en lugar de concatenar",
    )
    parser.add_argument(
        "--reverse-pdfs",
        type=int,
        nargs="+",
        metavar="INDEX",
        help="Índices de PDFs a invertir (0-based). Ej: --reverse-pdfs 1 2",
    )

    # Profile
    parser.add_argument(
        "--profile",
        choices=["document", "photo", "ebook", "archive", "share", "fast"],
        help="Usar perfil de configuración predefinido",
    )

    # OCR
    parser.add_argument("--ocr", action="store_true", help="Añadir capa de texto OCR")
    parser.add_argument(
        "--ocr-lang", default="spa", help="Idioma para OCR (spa, eng, etc.)"
    )

    # Deskew
    parser.add_argument(
        "--deskew", action="store_true", help="Enderezar páginas (rotación básica)"
    )
    parser.add_argument(
        "--auto-deskew",
        action="store_true",
        help="Auto-detectar y corregir inclinación",
    )
    parser.add_argument(
        "--deskew-threshold",
        type=float,
        default=0.5,
        help="Umbral mínimo para auto-deskew (grados)",
    )

    # Image processing
    parser.add_argument(
        "--enhance", action="store_true", help="Mejorar contraste y brillo"
    )
    parser.add_argument("--denoise", action="store_true", help="Eliminar ruido")
    parser.add_argument(
        "--binarize", action="store_true", help="Convertir a blanco y negro"
    )
    parser.add_argument("--sharpen", action="store_true", help="Mejorar nitidez")
    parser.add_argument("--despeckle", action="store_true", help="Eliminar manchas")
    parser.add_argument(
        "--autocrop", action="store_true", help="Recortar bordes blancos"
    )
    parser.add_argument(
        "--max-dpi", type=int, help="DPI máximo (reducir para menor tamaño)"
    )

    # Blank pages
    parser.add_argument(
        "--remove-blank", action="store_true", help="Eliminar páginas en blanco"
    )
    parser.add_argument(
        "--blank-threshold", type=float, default=0.99, help="Umbral de blancura (0-1)"
    )

    # Optimization
    parser.add_argument(
        "--optimize", action="store_true", help="Optimizar y comprimir PDF"
    )
    parser.add_argument(
        "--compress-level",
        type=int,
        default=5,
        choices=range(0, 10),
        help="Nivel de compresión (0-9)",
    )
    parser.add_argument(
        "--lossy",
        action="store_true",
        help="Re-encode todas las páginas como JPEG (reduce tamaño, pierde fidelidad/OCR)",
    )
    parser.add_argument(
        "--lossy-dpi",
        type=int,
        default=150,
        help="DPI objetivo para re-render (recomendado 100-200)",
    )
    parser.add_argument(
        "--lossy-quality",
        type=int,
        default=70,
        help="Calidad JPEG 1-95 (por encima de 95 no aporta beneficio)",
    )

    # Metadata
    parser.add_argument("--title", help="Título del documento")
    parser.add_argument("--author", help="Autor del documento")
    parser.add_argument("--subject", help="Asunto del documento")
    parser.add_argument("--keywords", help="Palabras clave")

    # Watermark
    parser.add_argument("--watermark", help="Texto de marca de agua")
    parser.add_argument(
        "--watermark-opacity",
        type=float,
        default=0.3,
        help="Opacidad de marca de agua (0-1)",
    )
    parser.add_argument(
        "--watermark-size",
        type=int,
        default=60,
        help="Tamaño de fuente de marca de agua",
    )
    parser.add_argument(
        "--watermark-rotation",
        type=int,
        default=45,
        help="Rotación de marca de agua (grados)",
    )

    # Page numbers
    parser.add_argument(
        "--page-numbers", action="store_true", help="Añadir números de página"
    )
    parser.add_argument(
        "--page-number-position",
        default="bottom-center",
        choices=[
            "bottom-center",
            "bottom-right",
            "bottom-left",
            "top-center",
            "top-right",
            "top-left",
        ],
        help="Posición de números de página",
    )
    parser.add_argument(
        "--page-number-size", type=int, default=10, help="Tamaño de fuente de números"
    )
    parser.add_argument(
        "--page-number-margin", type=int, default=20, help="Margen desde el borde"
    )

    # Other
    parser.add_argument("-q", "--quiet", action="store_true", help="Modo silencioso")

    args = parser.parse_args()

    # Validate inputs
    if not args.pdfs:
        parser.print_help()
        sys.exit(1)

    # Load and apply profile
    if args.profile:
        profile = load_profile(args.profile)
        if profile:
            if not args.quiet:
                print(f"Cargando perfil: {args.profile}")
            apply_profile_to_args(args, profile)

    # Parse PDF inputs
    try:
        pdf_inputs = parse_pdf_inputs(args)
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create processing options
    options = create_processing_options(args)

    # Create processor
    processor = PDFMergerCore(options)

    # Process PDFs
    if len(pdf_inputs) == 1:
        # Single PDF - just process it
        success = processor.process_pdf(pdf_inputs[0].path, args.output)
    else:
        # Multiple PDFs - merge and process
        success = processor.merge_and_process(
            pdf_inputs, args.output, interleave=args.interleave
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
