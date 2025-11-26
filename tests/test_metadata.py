from pathlib import Path

import pytest
from PyPDF2 import PdfReader, PdfWriter

import utils.metadata as md

pytestmark = pytest.mark.skipif(
    not md.METADATA_AVAILABLE,
    reason="Metadata utilities require PyPDF2/reportlab",
)


def create_pdf(path: Path, pages: int = 2):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    with path.open("wb") as fh:
        writer.write(fh)


def test_add_metadata_injects_fields(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    create_pdf(input_pdf)

    success = md.add_metadata(
        str(input_pdf),
        str(output_pdf),
        title="Contrato",
        author="Autor",
        subject="Asunto",
        keywords="k1,k2",
        verbose=True,
    )

    assert success is True
    reader = PdfReader(str(output_pdf))
    metadata = reader.metadata
    assert metadata["/Title"] == "Contrato"
    assert metadata["/Author"] == "Autor"


def test_create_watermark_page_returns_bytes():
    payload = md.create_watermark_page("CONFIDENCIAL", opacity=0.2, font_size=20)
    assert isinstance(payload, bytes)
    assert len(payload) > 0


def test_add_text_watermark_applies_to_all_pages(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    create_pdf(input_pdf)

    success = md.add_text_watermark(
        str(input_pdf),
        str(output_pdf),
        watermark_text="CONF",
        opacity=0.5,
        font_size=30,
        rotation=15,
        verbose=True,
    )

    assert success is True
    reader = PdfReader(str(output_pdf))
    assert len(reader.pages) == 2


def test_add_page_numbers_outputs_same_page_count(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    create_pdf(input_pdf)

    success = md.add_page_numbers(
        str(input_pdf),
        str(output_pdf),
        position="bottom-right",
        font_size=12,
        margin=15,
        verbose=True,
    )

    assert success is True
    reader = PdfReader(str(output_pdf))
    assert len(reader.pages) == 2


def test_metadata_helpers_return_false_when_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(md, "METADATA_AVAILABLE", False)
    input_pdf = tmp_path / "input.pdf"
    create_pdf(input_pdf)
    output_pdf = tmp_path / "output.pdf"

    assert (
        md.add_text_watermark(str(input_pdf), str(output_pdf), "X", verbose=True)
        is False
    )
    assert md.add_page_numbers(str(input_pdf), str(output_pdf), verbose=True) is False
    assert (
        md.add_metadata(str(input_pdf), str(output_pdf), title="T", verbose=True)
        is False
    )


def test_metadata_functions_handle_exceptions(monkeypatch, tmp_path):
    input_pdf = tmp_path / "input.pdf"
    create_pdf(input_pdf)

    def boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(md, "PdfReader", boom, raising=False)
    assert (
        md.add_metadata(str(input_pdf), str(tmp_path / "out1.pdf"), verbose=True)
        is False
    )
    assert (
        md.add_text_watermark(
            str(input_pdf), str(tmp_path / "out2.pdf"), "X", verbose=True
        )
        is False
    )
    assert (
        md.add_page_numbers(str(input_pdf), str(tmp_path / "out3.pdf"), verbose=True)
        is False
    )
