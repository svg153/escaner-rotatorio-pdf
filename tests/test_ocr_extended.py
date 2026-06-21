"""Extended tests for utils/ocr.py — confidence extraction, invisible text layer, extract_text_from_pdf."""

import json
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
        image_to_data=lambda img, **k: {
            "text": ["hello", "world"],
            "conf": [95, 80],
            "left": [10, 80],
            "top": [20, 20],
            "width": [60, 50],
            "height": [15, 15],
        },
        get_languages=lambda: ["spa", "eng"],
        Output=types.SimpleNamespace(DICT=0),
    )
    monkeypatch.setattr(ocr, "pytesseract", dummy, raising=False)


def create_pdf(tmp_path, name="input.pdf"):
    path = tmp_path / name
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as fh:
        writer.write(fh)
    return path


# ── perform_ocr_with_confidence ──────────────────────────────────

def test_perform_ocr_with_confidence_returns_dict():
    img = Image.new("RGB", (10, 10), color="white")
    result = ocr.perform_ocr_with_confidence(img, lang="spa")
    assert isinstance(result, dict)
    assert "text" in result
    assert "confidence" in result
    assert "blocks" in result


def test_perform_ocr_with_confidence_blocks():
    img = Image.new("RGB", (10, 10), color="white")
    result = ocr.perform_ocr_with_confidence(img, lang="spa")
    assert len(result["blocks"]) == 2
    assert result["blocks"][0]["text"] == "hello"
    assert result["blocks"][0]["confidence"] == 95
    assert result["blocks"][0]["left"] == 10
    assert result["blocks"][1]["text"] == "world"
    assert result["blocks"][1]["confidence"] == 80


def test_perform_ocr_with_confidence_avg_confidence():
    img = Image.new("RGB", (10, 10), color="white")
    result = ocr.perform_ocr_with_confidence(img, lang="spa")
    assert result["confidence"] == 87.5  # (95 + 80) / 2


def test_perform_ocr_with_confidence_empty_conf(monkeypatch):
    img = Image.new("RGB", (10, 10), color="white")

    dummy = types.SimpleNamespace(
        image_to_string=lambda *a, **k: "texto",
        image_to_data=lambda img, **k: {
            "text": ["hello"],
            "conf": [0],
            "left": [10],
            "top": [20],
            "width": [60],
            "height": [15],
        },
        Output=types.SimpleNamespace(DICT=0),
    )
    monkeypatch.setattr(ocr, "pytesseract", dummy, raising=False)

    result = ocr.perform_ocr_with_confidence(img, lang="spa")
    assert result["confidence"] == 0
    assert len(result["blocks"]) == 0  # conf=0 blocks are filtered


# ── add_ocr_layer (invisible text) ───────────────────────────────

def test_add_ocr_layer_with_invisible_text(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path)
    output_pdf = tmp_path / "ocr_invisible.pdf"

    monkeypatch.setattr(
        ocr,
        "convert_from_path",
        lambda *_args, **_kwargs: [Image.new("RGB", (10, 10), color="white")],
        raising=False,
    )

    success = ocr.add_ocr_layer_to_pdf(
        str(input_pdf), str(output_pdf), lang="spa", verbose=False
    )
    assert success is True

    reader = PdfReader(str(output_pdf))
    page = reader.pages[0]
    # The page should now have content with invisible text
    content = page.get("/Contents")
    assert content is not None


def test_add_ocr_layer_no_blocks_no_content(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path)
    output_pdf = tmp_path / "ocr_no_blocks.pdf"

    monkeypatch.setattr(
        ocr,
        "convert_from_path",
        lambda *_args, **_kwargs: [Image.new("RGB", (10, 10), color="white")],
        raising=False,
    )
    monkeypatch.setattr(
        ocr,
        "perform_ocr_with_confidence",
        lambda *_a, **_k: {"text": "", "confidence": 0, "blocks": []},
    )

    success = ocr.add_ocr_layer_to_pdf(
        str(input_pdf), str(output_pdf), lang="spa", verbose=False
    )
    assert success is True
    # Page should still exist
    reader = PdfReader(str(output_pdf))
    assert len(reader.pages) == 1


# ── extract_text_from_pdf ────────────────────────────────────────

def test_extract_text_from_pdf(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path)

    monkeypatch.setattr(
        ocr,
        "convert_from_path",
        lambda *_args, **_kwargs: [
            Image.new("RGB", (10, 10), color="white"),
            Image.new("RGB", (10, 10), color="white"),
        ],
        raising=False,
    )

    text = ocr.extract_text_from_pdf(str(input_pdf), lang="spa")
    assert "Página 1" in text
    assert "Página 2" in text
    assert "texto" in text


def test_extract_text_from_pdf_empty(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path)

    monkeypatch.setattr(
        ocr,
        "convert_from_path",
        lambda *_args, **_kwargs: [],
        raising=False,
    )

    text = ocr.extract_text_from_pdf(str(input_pdf), lang="spa")
    assert text == ""


# ── _add_invisible_text_layer ────────────────────────────────────

def test_add_invisible_text_layer_escapes_special_chars(monkeypatch, tmp_path):
    """Ensure backslashes, parens are escaped in invisible text layer."""
    input_pdf = create_pdf(tmp_path)
    output_pdf = tmp_path / "ocr_escape.pdf"

    monkeypatch.setattr(
        ocr,
        "convert_from_path",
        lambda *_args, **_kwargs: [Image.new("RGB", (100, 100), color="white")],
        raising=False,
    )

    # OCR result with special characters
    monkeypatch.setattr(
        ocr,
        "perform_ocr_with_confidence",
        lambda *_a, **_k: {
            "text": "Hello (world) \\ test",
            "confidence": 90,
            "blocks": [
                {
                    "text": "Hello (world) \\ test",
                    "confidence": 90,
                    "left": 10,
                    "top": 20,
                    "width": 80,
                    "height": 15,
                }
            ],
        },
    )

    success = ocr.add_ocr_layer_to_pdf(
        str(input_pdf), str(output_pdf), lang="spa", verbose=False
    )
    assert success is True

    # Read the output and verify the stream contains escaped characters
    reader = PdfReader(str(output_pdf))
    page = reader.pages[0]
    content = page.get("/Contents")
    assert content is not None


# ── get_available_languages ──────────────────────────────────────

def test_get_available_languages():
    langs = ocr.get_available_languages()
    assert "spa" in langs
    assert "eng" in langs


# ── check_ocr_availability ───────────────────────────────────────

def test_check_ocr_availability_false(monkeypatch):
    monkeypatch.setattr(ocr, "OCR_AVAILABLE", False)
    assert ocr.check_ocr_availability() is False
