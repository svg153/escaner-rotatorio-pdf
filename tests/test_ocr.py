import types

import pytest
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter

import utils.ocr as ocr


@pytest.fixture(autouse=True)
def enable_ocr(monkeypatch):
    monkeypatch.setattr(ocr, "OCR_AVAILABLE", True)

    dummy = types.SimpleNamespace(
        image_to_string=lambda *a, **k: "texto",
        get_languages=lambda: ["spa", "eng"],
    )
    monkeypatch.setattr(ocr, "pytesseract", dummy, raising=False)


def create_pdf(tmp_path, name="input.pdf"):
    path = tmp_path / name
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as fh:
        writer.write(fh)
    return path


def test_perform_ocr_on_image_returns_text():
    img = Image.new("RGB", (10, 10), color="white")
    text = ocr.perform_ocr_on_image(img, lang="spa")
    assert text == "texto"


def test_perform_ocr_handles_exception(monkeypatch):
    img = Image.new("RGB", (10, 10), color="white")

    def boom(*_a, **_k):
        raise RuntimeError("fail")

    monkeypatch.setattr(ocr.pytesseract, "image_to_string", boom)
    assert ocr.perform_ocr_on_image(img, lang="spa") == ""


def test_check_ocr_availability_flag(monkeypatch):
    monkeypatch.setattr(ocr, "OCR_AVAILABLE", False)
    assert ocr.check_ocr_availability() is False


def test_add_ocr_layer_processes_pages(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path)
    output_pdf = tmp_path / "ocr.pdf"

    monkeypatch.setattr(
        ocr,
        "convert_from_path",
        lambda *_args, **_kwargs: [Image.new("RGB", (10, 10), color="white")],
        raising=False,
    )
    monkeypatch.setattr(ocr, "perform_ocr_on_image", lambda *_a, **_k: "text")

    success = ocr.add_ocr_layer_to_pdf(
        str(input_pdf), str(output_pdf), lang="spa", verbose=True
    )
    assert success is True
    assert PdfReader(str(output_pdf))


def test_add_ocr_layer_handles_missing_dependencies(monkeypatch, tmp_path):
    monkeypatch.setattr(ocr, "OCR_AVAILABLE", False)
    input_pdf = create_pdf(tmp_path, "input.pdf")
    result = ocr.add_ocr_layer_to_pdf(
        str(input_pdf), str(tmp_path / "out.pdf"), verbose=True
    )
    assert result is False


def test_add_ocr_layer_handles_exception(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path, "input.pdf")

    def boom(*_a, **_k):
        raise RuntimeError("fail")

    monkeypatch.setattr(ocr, "convert_from_path", boom, raising=False)
    assert (
        ocr.add_ocr_layer_to_pdf(
            str(input_pdf), str(tmp_path / "out.pdf"), verbose=True
        )
        is False
    )


def test_get_available_languages_falls_back(monkeypatch):
    def boom():
        raise RuntimeError("failure")

    monkeypatch.setattr(ocr.pytesseract, "get_languages", boom)
    langs = ocr.get_available_languages()
    assert set(langs) == {"spa", "eng"}
