from pathlib import Path

import pytest
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter

import utils.blank_detection as bd


@pytest.fixture(autouse=True)
def ensure_dependencies(monkeypatch):
    monkeypatch.setattr(bd, "BLANK_DETECTION_AVAILABLE", True)
    monkeypatch.setattr(bd, "PDF_AVAILABLE", True)
    monkeypatch.setattr(bd, "PdfReader", PdfReader, raising=False)
    monkeypatch.setattr(bd, "PdfWriter", PdfWriter, raising=False)


def create_pdf(tmp_path: Path, name: str, pages: int = 2) -> Path:
    path = tmp_path / name
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    with path.open("wb") as fh:
        writer.write(fh)
    return path


def test_is_blank_image_detects_white_image():
    img = Image.new("RGB", (10, 10), color="white")
    assert bool(bd.is_blank_image(img, threshold=0.95)) is True

    img2 = Image.new("RGB", (10, 10), color="black")
    assert bool(bd.is_blank_image(img2, threshold=0.95)) is False


def test_detect_blank_pages_identifies_indexes(monkeypatch, tmp_path):
    white = Image.new("RGB", (10, 10), color="white")
    gray = Image.new("RGB", (10, 10), color="gray")

    monkeypatch.setattr(
        bd,
        "convert_from_path",
        lambda *_, **__: [white, gray, white],
        raising=False,
    )

    blanks = bd.detect_blank_pages(
        str(tmp_path / "dummy.pdf"), threshold=0.9, verbose=True
    )
    assert blanks == [0, 2]


def test_remove_blank_pages_copies_when_none(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path, "in.pdf", pages=1)
    output_pdf = tmp_path / "out.pdf"

    monkeypatch.setattr(bd, "detect_blank_pages", lambda *_, **__: [])

    success, removed = bd.remove_blank_pages(
        str(input_pdf), str(output_pdf), threshold=0.9, verbose=False
    )

    assert success is True
    assert removed == []
    assert output_pdf.exists()


def test_remove_blank_pages_drops_pages(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path, "input.pdf", pages=2)
    output_pdf = tmp_path / "output.pdf"

    monkeypatch.setattr(bd, "detect_blank_pages", lambda *_, **__: [0])

    success, removed = bd.remove_blank_pages(
        str(input_pdf), str(output_pdf), threshold=0.9, verbose=False
    )

    assert success is True
    assert removed == [0]

    reader = PdfReader(str(output_pdf))
    assert len(reader.pages) == 1


def test_detect_blank_pages_handles_missing_dependencies(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "BLANK_DETECTION_AVAILABLE", False)
    blanks = bd.detect_blank_pages(str(tmp_path / "dummy.pdf"), verbose=True)
    assert blanks == []


def test_remove_blank_pages_handles_missing_dependencies(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "BLANK_DETECTION_AVAILABLE", False)
    ok, removed = bd.remove_blank_pages("a.pdf", "b.pdf", verbose=True)
    assert ok is False
    assert removed == []


def test_is_blank_image_returns_false_when_unavailable(monkeypatch):
    monkeypatch.setattr(bd, "BLANK_DETECTION_AVAILABLE", False)
    img = Image.new("RGB", (5, 5), color="white")
    assert bd.is_blank_image(img) is False


def test_detect_blank_pages_handles_exception(monkeypatch, tmp_path):
    def boom(*_a, **_k):
        raise RuntimeError("convert error")

    monkeypatch.setattr(bd, "convert_from_path", boom, raising=False)
    blanks = bd.detect_blank_pages(str(tmp_path / "dummy.pdf"), verbose=True)
    assert blanks == []


def test_remove_blank_pages_reports_no_blanks(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path, "src.pdf", pages=1)
    output_pdf = tmp_path / "dst.pdf"
    monkeypatch.setattr(bd, "detect_blank_pages", lambda *_, **__: [])
    ok, removed = bd.remove_blank_pages(str(input_pdf), str(output_pdf), verbose=True)
    assert ok is True and removed == []


def test_remove_blank_pages_reports_errors(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path, "src.pdf", pages=1)
    monkeypatch.setattr(bd, "detect_blank_pages", lambda *_, **__: [0])

    def reader(*_a, **_k):
        raise RuntimeError("reader error")

    monkeypatch.setattr(bd, "PdfReader", reader, raising=False)
    ok, removed = bd.remove_blank_pages(
        str(input_pdf), str(tmp_path / "dst.pdf"), verbose=True
    )
    assert ok is False
    assert removed == []
