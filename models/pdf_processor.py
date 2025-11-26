"""
Core logic for PDF merging and processing.
Separated from CLI to allow web/GUI implementations.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from PyPDF2 import PdfReader, PdfWriter

try:
    import pikepdf

    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False


@dataclass
class PDFInput:
    """Represents a PDF input file with its configuration."""

    path: str
    reverse: bool = False

    def __post_init__(self):
        if not Path(self.path).exists():
            raise FileNotFoundError(f"PDF file not found: {self.path}")


@dataclass
class ProcessingOptions:
    """Configuration for PDF processing."""

    # OCR options
    ocr: bool = False
    ocr_lang: str = "spa"

    # Deskew options
    deskew: bool = False
    auto_deskew: bool = False
    deskew_threshold: float = 0.5

    # Image processing options
    enhance: bool = False
    denoise: bool = False
    binarize: bool = False
    sharpen: bool = False
    despeckle: bool = False
    autocrop: bool = False
    max_dpi: Optional[int] = None

    # Blank page detection
    remove_blank: bool = False
    blank_threshold: float = 0.99

    # Optimization
    optimize: bool = False
    compress_level: int = 5
    # Lossy recompression
    lossy: bool = False
    lossy_dpi: int = 150
    lossy_quality: int = 70  # JPEG quality 1-95 (Pillow typical range), we cap input

    # Metadata
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None

    # Watermark
    watermark: Optional[str] = None
    watermark_opacity: float = 0.3
    watermark_size: int = 60
    watermark_rotation: int = 45

    # Page numbers
    page_numbers: bool = False
    page_number_position: str = "bottom-center"
    page_number_size: int = 10
    page_number_margin: int = 20

    # General
    verbose: bool = True


class PDFMergerCore:
    """Core PDF merging and processing logic."""

    def __init__(self, options: Optional[ProcessingOptions] = None):
        """
        Initialize PDF merger core.

        Args:
            options: Processing options. If None, uses defaults.
        """
        self.options = options or ProcessingOptions()
        self.temp_files: List[str] = []

    def merge_pdfs(self, pdf_inputs: List[PDFInput], output_path: str) -> bool:
        """
        Merge multiple PDFs into one.

        Args:
            pdf_inputs: List of PDF inputs with configurations
            output_path: Output PDF path

        Returns:
            True if successful
        """
        try:
            if self.options.verbose:
                print(f"Mezclando {len(pdf_inputs)} PDFs...")

            writer = PdfWriter()

            for idx, pdf_input in enumerate(pdf_inputs, 1):
                reader = PdfReader(pdf_input.path)
                num_pages = len(reader.pages)

                if self.options.verbose:
                    reverse_text = " (invertido)" if pdf_input.reverse else ""
                    print(f"  PDF {idx}: {num_pages} páginas{reverse_text}")

                # Get pages in correct order
                pages = (
                    list(reversed(reader.pages))
                    if pdf_input.reverse
                    else list(reader.pages)
                )

                # Add all pages
                for page in pages:
                    writer.add_page(page)

            # Save merged PDF
            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            if self.options.verbose:
                print(f"✓ PDFs mezclados: {len(writer.pages)} páginas totales")

            return True

        except Exception as e:
            if self.options.verbose:
                print(f"✗ Error al mezclar PDFs: {e}")
            return False

    def interleave_pdfs(self, pdf_inputs: List[PDFInput], output_path: str) -> bool:
        """
        Interleave multiple PDFs (alternate pages).
        Useful for scanning both sides of documents.

        Args:
            pdf_inputs: List of PDF inputs (typically 2 for front/back)
            output_path: Output PDF path

        Returns:
            True if successful
        """
        try:
            if len(pdf_inputs) < 2:
                return self.merge_pdfs(pdf_inputs, output_path)

            if self.options.verbose:
                print(f"Intercalando {len(pdf_inputs)} PDFs...")

            readers = []
            for pdf_input in pdf_inputs:
                reader = PdfReader(pdf_input.path)
                pages = (
                    list(reversed(reader.pages))
                    if pdf_input.reverse
                    else list(reader.pages)
                )
                readers.append(pages)

            writer = PdfWriter()

            # Find max pages
            max_pages = max(len(pages) for pages in readers)

            # Interleave pages
            for i in range(max_pages):
                for pages in readers:
                    if i < len(pages):
                        writer.add_page(pages[i])

            # Save
            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            if self.options.verbose:
                print(f"✓ PDFs intercalados: {len(writer.pages)} páginas totales")

            return True

        except Exception as e:
            if self.options.verbose:
                print(f"✗ Error al intercalar PDFs: {e}")
            return False

    def process_pdf(self, input_pdf: str, output_pdf: str) -> bool:
        """
        Process a single PDF with all configured options.

        Args:
            input_pdf: Input PDF path
            output_pdf: Output PDF path

        Returns:
            True if successful
        """
        current_file = input_pdf

        try:
            # Import utilities only when needed
            from utils.blank_detection import (
                check_blank_detection_availability,
                remove_blank_pages,
            )
            from utils.deskew import auto_deskew_pdf, check_deskew_availability
            from utils.image_processing import (
                check_image_processing_availability,
                process_pdf_images,
            )
            from utils.metadata import (
                add_metadata,
                add_page_numbers,
                add_text_watermark,
                check_metadata_availability,
            )
            from utils.ocr import add_ocr_layer_to_pdf, check_ocr_availability

            # 1. Remove blank pages
            if self.options.remove_blank:
                if check_blank_detection_availability():
                    temp_blank = self._create_temp_file()
                    success, removed = remove_blank_pages(
                        current_file,
                        temp_blank,
                        self.options.blank_threshold,
                        self.options.verbose,
                    )
                    if success:
                        current_file = temp_blank
                else:
                    if self.options.verbose:
                        print(
                            "⚠ Omitiendo eliminación de páginas en blanco (dependencias no disponibles)"
                        )

            # 2. Auto-deskew
            if self.options.auto_deskew:
                if check_deskew_availability():
                    temp_deskew = self._create_temp_file()
                    success = auto_deskew_pdf(
                        current_file,
                        temp_deskew,
                        self.options.deskew_threshold,
                        self.options.verbose,
                    )
                    if success:
                        current_file = temp_deskew
                else:
                    if self.options.verbose:
                        print("⚠ Omitiendo auto-deskew (dependencias no disponibles)")

            # 3. Basic deskew
            elif self.options.deskew:
                temp_deskew = self._create_temp_file()
                success = self._deskew_pdf_basic(current_file, temp_deskew)
                if success:
                    current_file = temp_deskew

            # 4. Image processing
            if any(
                [
                    self.options.enhance,
                    self.options.denoise,
                    self.options.binarize,
                    self.options.sharpen,
                    self.options.despeckle,
                    self.options.autocrop,
                    self.options.max_dpi,
                ]
            ):
                if check_image_processing_availability():
                    temp_img = self._create_temp_file()
                    success = process_pdf_images(
                        current_file,
                        temp_img,
                        enhance=self.options.enhance,
                        denoise=self.options.denoise,
                        binarize=self.options.binarize,
                        sharpen=self.options.sharpen,
                        despeckle=self.options.despeckle,
                        autocrop=self.options.autocrop,
                        max_dpi=self.options.max_dpi,
                        verbose=self.options.verbose,
                    )
                    if success:
                        current_file = temp_img
                else:
                    if self.options.verbose:
                        print(
                            "⚠ Omitiendo procesamiento de imágenes (dependencias no disponibles)"
                        )

            # 4b. Lossy recompression (convert pages to JPEG images at target DPI)
            if self.options.lossy:
                temp_lossy = self._create_temp_file()
                success = self._lossy_reencode(
                    current_file,
                    temp_lossy,
                    dpi=self.options.lossy_dpi,
                    quality=self.options.lossy_quality,
                )
                if success:
                    current_file = temp_lossy
                else:
                    if self.options.verbose:
                        print("⚠ Omitiendo compresión lossy (dependencias o error)")

            # 5. OCR
            if self.options.ocr:
                if check_ocr_availability():
                    temp_ocr = self._create_temp_file()
                    success = add_ocr_layer_to_pdf(
                        current_file,
                        temp_ocr,
                        self.options.ocr_lang,
                        self.options.verbose,
                    )
                    if success:
                        current_file = temp_ocr
                else:
                    if self.options.verbose:
                        print("⚠ Omitiendo OCR (dependencias no disponibles)")

            # 6. Optimize
            if self.options.optimize:
                temp_opt = self._create_temp_file()
                success = self._optimize_pdf(
                    current_file, temp_opt, self.options.compress_level
                )
                if success:
                    current_file = temp_opt

            # 7. Watermark
            if self.options.watermark:
                if check_metadata_availability():
                    temp_wm = self._create_temp_file()
                    success = add_text_watermark(
                        current_file,
                        temp_wm,
                        self.options.watermark,
                        self.options.watermark_opacity,
                        self.options.watermark_size,
                        self.options.watermark_rotation,
                        self.options.verbose,
                    )
                    if success:
                        current_file = temp_wm
                else:
                    if self.options.verbose:
                        print("⚠ Omitiendo marca de agua (dependencias no disponibles)")

            # 8. Page numbers
            if self.options.page_numbers:
                if check_metadata_availability():
                    temp_pn = self._create_temp_file()
                    success = add_page_numbers(
                        current_file,
                        temp_pn,
                        self.options.page_number_position,
                        self.options.page_number_size,
                        self.options.page_number_margin,
                        self.options.verbose,
                    )
                    if success:
                        current_file = temp_pn
                else:
                    if self.options.verbose:
                        print(
                            "⚠ Omitiendo números de página (dependencias no disponibles)"
                        )

            # 9. Metadata
            if any(
                [
                    self.options.title,
                    self.options.author,
                    self.options.subject,
                    self.options.keywords,
                ]
            ):
                if check_metadata_availability():
                    temp_meta = self._create_temp_file()
                    success = add_metadata(
                        current_file,
                        temp_meta,
                        title=self.options.title,
                        author=self.options.author,
                        subject=self.options.subject,
                        keywords=self.options.keywords,
                        verbose=self.options.verbose,
                    )
                    if success:
                        current_file = temp_meta
                else:
                    if self.options.verbose:
                        print("⚠ Omitiendo metadata (dependencias no disponibles)")

            # Copy final result
            import shutil

            shutil.copy2(current_file, output_pdf)

            # Cleanup
            self._cleanup_temp_files()

            return True

        except Exception as e:
            if self.options.verbose:
                print(f"✗ Error en procesamiento: {e}")
            self._cleanup_temp_files()
            return False

    def merge_and_process(
        self, pdf_inputs: List[PDFInput], output_path: str, interleave: bool = False
    ) -> bool:
        """
        Merge multiple PDFs and apply processing in one operation.

        Args:
            pdf_inputs: List of PDF inputs
            output_path: Final output path
            interleave: If True, interleave pages instead of concatenating

        Returns:
            True if successful
        """
        try:
            # Create temporary merged file
            temp_merged = self._create_temp_file()

            # Merge PDFs
            if interleave:
                success = self.interleave_pdfs(pdf_inputs, temp_merged)
            else:
                success = self.merge_pdfs(pdf_inputs, temp_merged)

            if not success:
                return False

            # Process merged PDF
            success = self.process_pdf(temp_merged, output_path)

            # Cleanup
            self._cleanup_temp_files()

            if success and self.options.verbose:
                print(f"\n✓ PDF final generado: {output_path}")

            return success

        except Exception as e:
            if self.options.verbose:
                print(f"✗ Error: {e}")
            self._cleanup_temp_files()
            return False

    def _create_temp_file(self) -> str:
        """Create a temporary file and track it."""
        temp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp.close()
        self.temp_files.append(temp.name)
        return temp.name

    def _cleanup_temp_files(self):
        """Clean up all temporary files."""
        for temp_file in self.temp_files:
            try:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
            except OSError:
                pass
        self.temp_files.clear()

    def _deskew_pdf_basic(self, input_pdf: str, output_pdf: str) -> bool:
        """Basic deskew (rotation correction)."""
        if not PIKEPDF_AVAILABLE:
            if self.options.verbose:
                print("⚠ pikepdf no disponible para deskew básico")
            return False

        try:
            if self.options.verbose:
                print("Enderezando páginas...")

            with pikepdf.open(input_pdf) as pdf:
                for i, page in enumerate(pdf.pages):
                    rotate = page.get("/Rotate", 0)
                    if rotate != 0:
                        if self.options.verbose:
                            print(
                                f"  Corrigiendo rotación de página {i + 1}: {rotate}° → 0°"
                            )
                        page.Rotate = 0

                pdf.save(output_pdf)

            if self.options.verbose:
                print("✓ Enderezado completado")
            return True
        except Exception as e:
            if self.options.verbose:
                print(f"⚠ Error al enderezar: {e}")
            return False

    def _optimize_pdf(
        self, input_pdf: str, output_pdf: str, compress_level: int = 5
    ) -> bool:
        """Optimize PDF size."""
        if not PIKEPDF_AVAILABLE:
            if self.options.verbose:
                print("⚠ pikepdf no disponible para optimización")
            return False

        try:
            if self.options.verbose:
                original_size = Path(input_pdf).stat().st_size / (1024 * 1024)
                print(f"Optimizando PDF (tamaño original: {original_size:.2f} MB)...")

            # Map compression level
            stream_decode_level = pikepdf.StreamDecodeLevel.generalized
            if compress_level >= 7:
                stream_decode_level = pikepdf.StreamDecodeLevel.all
            elif compress_level <= 3:
                stream_decode_level = pikepdf.StreamDecodeLevel.none

            with pikepdf.open(input_pdf) as pdf:
                pdf.save(
                    output_pdf,
                    compress_streams=True,
                    stream_decode_level=stream_decode_level,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                    recompress_flate=True,
                )

            if self.options.verbose:
                optimized_size = Path(output_pdf).stat().st_size / (1024 * 1024)
                reduction = (
                    ((original_size - optimized_size) / original_size) * 100
                    if original_size > 0
                    else 0
                )
                print(
                    f"✓ Optimización completada (nuevo tamaño: {optimized_size:.2f} MB, reducción: {reduction:.1f}%)"
                )
            return True
        except Exception as e:
            if self.options.verbose:
                print(f"⚠ Error al optimizar: {e}")
            return False

    def _lossy_reencode(
        self, input_pdf: str, output_pdf: str, dpi: int = 150, quality: int = 70
    ) -> bool:
        """Lossy re-encode all pages as JPEG images to reduce size.

        Args:
            input_pdf: Source PDF path
            output_pdf: Destination PDF path
            dpi: Target DPI for rendering (typical 100-200 for documents)
            quality: JPEG quality (1-95)
        Returns:
            True if successful.
        """
        try:
            if quality < 1:
                quality = 1
            if quality > 95:
                quality = 95  # Pillow advises <=95
            import io

            import img2pdf
            import pypdfium2 as pdfium

            if self.options.verbose:
                print(
                    f"Re-encodificando en modo lossy (dpi={dpi}, calidad={quality})..."
                )
            pdf = pdfium.PdfDocument(input_pdf)
            page_images_bytes = []
            scale = dpi / 72.0  # PDF points to target DPI
            for i in range(len(pdf)):
                page = pdf[i]
                bitmap = page.render(scale=scale).to_pil()
                rgb = bitmap.convert("RGB")  # Ensure RGB for JPEG
                buf = io.BytesIO()
                rgb.save(buf, format="JPEG", quality=quality, optimize=True)
                page_images_bytes.append(buf.getvalue())
                buf.close()
                if self.options.verbose:
                    orig_w, orig_h = bitmap.size
                    print(f"  Página {i + 1}: {orig_w}x{orig_h} px re-encodificada")
            # Combine into single PDF
            with open(output_pdf, "wb") as f_out:
                f_out.write(img2pdf.convert(page_images_bytes))
            if self.options.verbose:
                new_size = Path(output_pdf).stat().st_size / (1024 * 1024)
                print(
                    f"✓ Re-encoding lossy completado (nuevo tamaño: {new_size:.2f} MB)"
                )
            return True
        except Exception as e:
            if self.options.verbose:
                print(f"⚠ Error en lossy reencode: {e}")
            return False
