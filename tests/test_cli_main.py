import sys
from pathlib import Path

import pytest
from PyPDF2 import PdfWriter

import cli


def create_pdf(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as fh:
        writer.write(fh)
    return path


def test_cli_main_process_single_pdf(monkeypatch, tmp_path):
    input_pdf = create_pdf(tmp_path, "one.pdf")
    output_pdf = tmp_path / "out.pdf"

    class DummyProcessor:
        def __init__(self, options):
            self.options = options

        def process_pdf(self, input_path, output_path):
            Path(output_path).write_bytes(b"PDF")
            assert input_path == str(input_pdf)
            return True

    monkeypatch.setattr(cli, "PDFMergerCore", DummyProcessor)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "cli.py",
            str(input_pdf),
            "-o",
            str(output_pdf),
            "--ocr",
            "--profile",
            "document",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0


def test_cli_main_merge_multiple(monkeypatch, tmp_path):
    pdf1 = create_pdf(tmp_path, "front.pdf")
    pdf2 = create_pdf(tmp_path, "back.pdf")
    output_pdf = tmp_path / "merged.pdf"

    class DummyProcessor:
        def __init__(self, options):
            self.options = options
            self.call = None

        def merge_and_process(self, inputs, output_path, interleave=False):
            self.call = (inputs, output_path, interleave)
            Path(output_path).write_bytes(b"PDF")
            return True

    dummy = DummyProcessor(cli.ProcessingOptions())
    monkeypatch.setattr(cli, "PDFMergerCore", lambda options: dummy)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "cli.py",
            str(pdf1),
            str(pdf2),
            "-o",
            str(output_pdf),
            "--interleave",
            "--reverse-pdfs",
            "1",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    assert dummy.call[2] is True
    assert len(dummy.call[0]) == 2
    assert dummy.call[0][1].reverse is True
