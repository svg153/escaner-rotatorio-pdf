from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from PyPDF2 import PdfReader, PdfWriter

from models.pdf_processor import PDFInput, PDFMergerCore, ProcessingOptions

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))


class PDFProcessorTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _create_pdf(self, name: str, page_widths):
        path = self.tmp_path / name
        writer = PdfWriter()
        for width in page_widths:
            writer.add_blank_page(width=width, height=842)
        with path.open("wb") as f:
            writer.write(f)
        return path

    def _page_widths(self, pdf_path: Path):
        reader = PdfReader(str(pdf_path))
        return [float(page.mediabox.width) for page in reader.pages]

    def test_pdf_input_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            PDFInput(str(self.tmp_path / "missing.pdf"))

    def test_merge_pdfs_respects_reverse_flags(self):
        pdf1 = self._create_pdf("one.pdf", [100, 200])
        pdf2 = self._create_pdf("two.pdf", [300, 400])
        output = self.tmp_path / "merged.pdf"

        inputs = [PDFInput(str(pdf1)), PDFInput(str(pdf2), reverse=True)]
        core = PDFMergerCore(ProcessingOptions(verbose=False))

        self.assertTrue(core.merge_pdfs(inputs, str(output)))
        self.assertEqual(self._page_widths(output), [100.0, 200.0, 400.0, 300.0])

    def test_interleave_pdfs_alternates_pages(self):
        pdf1 = self._create_pdf("front.pdf", [100, 200])
        pdf2 = self._create_pdf("back.pdf", [300, 400])
        output = self.tmp_path / "interleaved.pdf"

        inputs = [PDFInput(str(pdf1)), PDFInput(str(pdf2), reverse=True)]
        core = PDFMergerCore(ProcessingOptions(verbose=False))

        self.assertTrue(core.interleave_pdfs(inputs, str(output)))
        self.assertEqual(self._page_widths(output), [100.0, 400.0, 200.0, 300.0])

    def test_merge_and_process_uses_interleave_when_requested(self):
        pdf1 = self._create_pdf("front.pdf", [100])
        pdf2 = self._create_pdf("back.pdf", [200])
        output = self.tmp_path / "final.pdf"
        inputs = [PDFInput(str(pdf1)), PDFInput(str(pdf2))]

        core = PDFMergerCore(ProcessingOptions(verbose=False))

        with (
            patch.object(core, "interleave_pdfs", return_value=True) as mock_interleave,
            patch.object(core, "merge_pdfs", return_value=True) as mock_merge,
            patch.object(core, "process_pdf", return_value=True) as mock_process,
        ):
            self.assertTrue(
                core.merge_and_process(inputs, str(output), interleave=True)
            )

        mock_interleave.assert_called_once()
        mock_merge.assert_not_called()
        mock_process.assert_called_once()

    def test_process_pdf_executes_all_stages_when_available(self):
        source = self._create_pdf("source.pdf", [100])
        output = self.tmp_path / "processed.pdf"

        options = ProcessingOptions(
            remove_blank=True,
            auto_deskew=True,
            enhance=True,
            denoise=True,
            binarize=True,
            sharpen=True,
            despeckle=True,
            autocrop=True,
            max_dpi=200,
            lossy=True,
            ocr=True,
            optimize=True,
            watermark="CONFIDENCIAL",
            page_numbers=True,
            title="Doc",
            author="Autor",
            verbose=False,
        )
        core = PDFMergerCore(options)

        def _copy(src, dst, *args, **kwargs):
            shutil.copy2(src, dst)
            return True

        def _copy_with_tuple(src, dst, *args, **kwargs):
            shutil.copy2(src, dst)
            return True, []

        with (
            patch(
                "utils.blank_detection.check_blank_detection_availability",
                return_value=True,
            ),
            patch(
                "utils.blank_detection.remove_blank_pages",
                side_effect=_copy_with_tuple,
            ) as mock_blank,
            patch("utils.deskew.check_deskew_availability", return_value=True),
            patch(
                "utils.deskew.auto_deskew_pdf",
                side_effect=lambda s, d, *a, **k: _copy(s, d),
            ),
            patch(
                "utils.image_processing.check_image_processing_availability",
                return_value=True,
            ),
            patch(
                "utils.image_processing.process_pdf_images",
                side_effect=lambda s, d, **_: _copy(s, d),
            ),
            patch.object(
                core, "_lossy_reencode", side_effect=lambda s, d, **_: _copy(s, d)
            ) as mock_lossy,
            patch("utils.ocr.check_ocr_availability", return_value=True),
            patch(
                "utils.ocr.add_ocr_layer_to_pdf",
                side_effect=lambda s, d, *a, **k: _copy(s, d),
            ),
            patch.object(
                core, "_optimize_pdf", side_effect=lambda s, d, *_: _copy(s, d)
            ) as mock_opt,
            patch("utils.metadata.check_metadata_availability", return_value=True),
            patch(
                "utils.metadata.add_text_watermark",
                side_effect=lambda s, d, *a, **k: _copy(s, d),
            ) as mock_wm,
            patch(
                "utils.metadata.add_page_numbers",
                side_effect=lambda s, d, *a, **k: _copy(s, d),
            ) as mock_pn,
            patch(
                "utils.metadata.add_metadata",
                side_effect=lambda s, d, *a, **k: _copy(s, d),
            ) as mock_meta,
        ):
            self.assertTrue(core.process_pdf(str(source), str(output)))

        self.assertTrue(output.exists())
        self.assertGreater(output.stat().st_size, 0)
        mock_blank.assert_called_once()
        mock_lossy.assert_called_once()
        mock_opt.assert_called_once()
        mock_wm.assert_called_once()
        mock_pn.assert_called_once()
        mock_meta.assert_called_once()


if __name__ == "__main__":
    unittest.main()
