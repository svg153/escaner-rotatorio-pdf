import sys
import types
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
from PyPDF2 import PdfWriter

from models import pdf_processor as pp


def make_pdf(tmp_path: Path, name: str, pages: int = 1) -> Path:
    path = tmp_path / name
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    with path.open("wb") as fh:
        writer.write(fh)
    return path


def test_merge_pdfs_handles_exception(monkeypatch, tmp_path):
    pdf_path = make_pdf(tmp_path, "one.pdf")
    inputs = [pp.PDFInput(str(pdf_path))]
    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))

    def boom(path):
        raise ValueError("bad pdf")

    monkeypatch.setattr(pp, "PdfReader", boom)

    assert core.merge_pdfs(inputs, str(tmp_path / "out.pdf")) is False


def test_interleave_single_pdf_falls_back_to_merge(monkeypatch, tmp_path):
    pdf_path = make_pdf(tmp_path, "single.pdf")
    inputs = [pp.PDFInput(str(pdf_path))]
    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))

    called = {}

    def fake_merge(pdf_inputs, output_path):
        called["merge"] = True
        return True

    monkeypatch.setattr(core, "merge_pdfs", fake_merge)

    assert core.interleave_pdfs(inputs, str(tmp_path / "out.pdf")) is True
    assert called["merge"] is True


def test_interleave_pdfs_handles_exception(monkeypatch, tmp_path):
    pdf_path = make_pdf(tmp_path, "one.pdf")
    inputs = [pp.PDFInput(str(pdf_path)), pp.PDFInput(str(pdf_path))]
    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))

    def boom(path):
        raise RuntimeError("read error")

    monkeypatch.setattr(pp, "PdfReader", boom)
    assert core.interleave_pdfs(inputs, str(tmp_path / "out.pdf")) is False


def test_process_pdf_skips_when_dependencies_missing(monkeypatch, tmp_path):
    pdf_path = make_pdf(tmp_path, "input.pdf")
    core = pp.PDFMergerCore(
        pp.ProcessingOptions(
            remove_blank=True,
            auto_deskew=True,
            enhance=True,
            ocr=True,
            watermark="W",
            page_numbers=True,
            title="T",
            verbose=True,
        )
    )

    monkeypatch.setattr(
        "utils.blank_detection.check_blank_detection_availability",
        lambda: False,
    )
    monkeypatch.setattr(
        "utils.deskew.check_deskew_availability",
        lambda: False,
    )
    monkeypatch.setattr(
        "utils.image_processing.check_image_processing_availability",
        lambda: False,
    )
    monkeypatch.setattr("utils.ocr.check_ocr_availability", lambda: False)
    monkeypatch.setattr("utils.metadata.check_metadata_availability", lambda: False)

    assert core.process_pdf(str(pdf_path), str(tmp_path / "output.pdf")) is True


def configure_fake_pikepdf(monkeypatch, tmp_path):
    class FakePage(dict):
        def __init__(self, rotate=90):
            super().__init__()
            self.Rotate = rotate

        def get(self, key, default=None):
            if key == "/Rotate":
                return self.Rotate
            return default

    class FakePdf:
        def __init__(self):
            self.pages = [FakePage(90), FakePage(0)]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def save(self, path, **_kwargs):
            Path(path).write_bytes(b"pdf")

    class FakeStreamDecodeLevel:
        generalized = object()
        all = object()
        none = object()

    class FakeObjectStreamMode:
        generate = object()

    fake_module = SimpleNamespace(
        open=lambda *_: FakePdf(),
        StreamDecodeLevel=FakeStreamDecodeLevel,
        ObjectStreamMode=FakeObjectStreamMode,
    )

    monkeypatch.setattr(pp, "pikepdf", fake_module, raising=False)
    monkeypatch.setattr(pp, "PIKEPDF_AVAILABLE", True)


def test_deskew_pdf_basic_resets_rotation(monkeypatch, tmp_path):
    input_pdf = make_pdf(tmp_path, "input.pdf")
    output_pdf = tmp_path / "deskew.pdf"
    configure_fake_pikepdf(monkeypatch, tmp_path)
    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))

    assert core._deskew_pdf_basic(str(input_pdf), str(output_pdf)) is True
    assert output_pdf.exists()


def test_optimize_pdf_uses_compression_levels(monkeypatch, tmp_path):
    input_pdf = make_pdf(tmp_path, "input.pdf")
    output_pdf = tmp_path / "opt.pdf"
    configure_fake_pikepdf(monkeypatch, tmp_path)
    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))

    assert core._optimize_pdf(str(input_pdf), str(output_pdf), compress_level=8)
    assert output_pdf.exists()


def test_lossy_reencode_creates_output(monkeypatch, tmp_path):
    input_pdf = make_pdf(tmp_path, "input.pdf")
    output_pdf = tmp_path / "lossy.pdf"

    img2pdf_module = types.ModuleType("img2pdf")

    def convert(images):
        return b"PDF" + b"".join(images)

    img2pdf_module.convert = convert

    class DummyBitmap:
        def __init__(self):
            self.size = (10, 10)

        def to_pil(self):
            return Image.new("RGB", self.size, color="white")

    class DummyPage:
        def render(self, scale):
            return DummyBitmap()

    class DummyPdfDocument:
        def __init__(self, _path):
            self.pages = [DummyPage(), DummyPage()]

        def __len__(self):
            return len(self.pages)

        def __getitem__(self, idx):
            return self.pages[idx]

    pdfium_module = SimpleNamespace(PdfDocument=DummyPdfDocument)

    monkeypatch.setitem(sys.modules, "img2pdf", img2pdf_module)
    monkeypatch.setitem(sys.modules, "pypdfium2", pdfium_module)

    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))

    assert core._lossy_reencode(str(input_pdf), str(output_pdf), dpi=120, quality=120)
    assert output_pdf.exists()


def test_process_pdf_uses_basic_deskew(monkeypatch, tmp_path):
    input_pdf = make_pdf(tmp_path, "doc.pdf", pages=1)
    output_pdf = tmp_path / "out.pdf"

    core = pp.PDFMergerCore(pp.ProcessingOptions(deskew=True, verbose=True))

    monkeypatch.setattr(pp, "PIKEPDF_AVAILABLE", True)
    monkeypatch.setattr(core, "_deskew_pdf_basic", lambda src, dst: True)
    monkeypatch.setattr(
        "utils.blank_detection.check_blank_detection_availability", lambda: False
    )
    monkeypatch.setattr(
        "utils.image_processing.check_image_processing_availability", lambda: False
    )
    monkeypatch.setattr("utils.ocr.check_ocr_availability", lambda: False)
    monkeypatch.setattr("utils.metadata.check_metadata_availability", lambda: False)

    assert core.process_pdf(str(input_pdf), str(output_pdf)) is True


def test_process_pdf_handles_exception(monkeypatch, tmp_path):
    input_pdf = make_pdf(tmp_path, "doc.pdf", pages=1)
    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))

    monkeypatch.setattr(
        "utils.blank_detection.check_blank_detection_availability", lambda: False
    )
    monkeypatch.setattr(
        "utils.image_processing.check_image_processing_availability", lambda: False
    )
    monkeypatch.setattr("utils.ocr.check_ocr_availability", lambda: False)
    monkeypatch.setattr("utils.metadata.check_metadata_availability", lambda: False)

    def boom(*_a, **_k):
        raise RuntimeError("copy")

    monkeypatch.setattr("shutil.copy2", boom)
    assert core.process_pdf(str(input_pdf), str(tmp_path / "out.pdf")) is False


def test_process_pdf_reports_lossy_skip(monkeypatch, tmp_path):
    input_pdf = make_pdf(tmp_path, "doc.pdf", pages=1)
    output_pdf = tmp_path / "lossy.pdf"

    options = pp.ProcessingOptions(lossy=True, verbose=True)
    core = pp.PDFMergerCore(options)

    monkeypatch.setattr(
        "utils.blank_detection.check_blank_detection_availability", lambda: False
    )
    monkeypatch.setattr(
        "utils.image_processing.check_image_processing_availability", lambda: False
    )
    monkeypatch.setattr("utils.ocr.check_ocr_availability", lambda: False)
    monkeypatch.setattr("utils.metadata.check_metadata_availability", lambda: False)
    monkeypatch.setattr(core, "_lossy_reencode", lambda *_a, **_k: False)

    assert core.process_pdf(str(input_pdf), str(output_pdf)) is True


def test_merge_and_process_handles_failures(monkeypatch, tmp_path):
    pdf_path = make_pdf(tmp_path, "one.pdf")
    inputs = [pp.PDFInput(str(pdf_path))]
    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))

    monkeypatch.setattr(core, "merge_pdfs", lambda *_a, **_k: False)
    assert core.merge_and_process(inputs, str(tmp_path / "out.pdf")) is False

    def boom(*_a, **_k):
        raise RuntimeError("merge error")

    monkeypatch.setattr(core, "merge_pdfs", boom)
    assert core.merge_and_process(inputs, str(tmp_path / "out.pdf")) is False


def test_cleanup_temp_files_removes_files(tmp_path):
    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))
    temp = core._create_temp_file()
    Path(temp).write_text("temp")
    core._cleanup_temp_files()
    assert not Path(temp).exists()


def test_deskew_basic_warns_without_pikepdf(monkeypatch, tmp_path):
    input_pdf = make_pdf(tmp_path, "input.pdf")
    output_pdf = tmp_path / "out.pdf"
    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))
    monkeypatch.setattr(pp, "PIKEPDF_AVAILABLE", False)
    assert core._deskew_pdf_basic(str(input_pdf), str(output_pdf)) is False
    monkeypatch.setattr(pp, "PIKEPDF_AVAILABLE", True)


def test_optimize_pdf_guard(monkeypatch, tmp_path):
    input_pdf = make_pdf(tmp_path, "input.pdf")
    output_pdf = tmp_path / "out.pdf"
    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))
    monkeypatch.setattr(pp, "PIKEPDF_AVAILABLE", False)
    assert core._optimize_pdf(str(input_pdf), str(output_pdf)) is False
    monkeypatch.setattr(pp, "PIKEPDF_AVAILABLE", True)


def test_lossy_reencode_handles_errors(monkeypatch, tmp_path):
    input_pdf = make_pdf(tmp_path, "input.pdf")
    output_pdf = tmp_path / "out.pdf"

    img2pdf_module = types.ModuleType("img2pdf")

    def convert(*_a, **_k):
        raise RuntimeError("fail")

    img2pdf_module.convert = convert

    class ErrorPdfDocument:
        def __init__(self, *_a, **_k):
            raise RuntimeError("fail")

    pdfium_module = SimpleNamespace(PdfDocument=ErrorPdfDocument)

    monkeypatch.setitem(sys.modules, "img2pdf", img2pdf_module)
    monkeypatch.setitem(sys.modules, "pypdfium2", pdfium_module)

    core = pp.PDFMergerCore(pp.ProcessingOptions(verbose=True))
    assert core._lossy_reencode(str(input_pdf), str(output_pdf)) is False
