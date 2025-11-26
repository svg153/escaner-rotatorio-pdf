import argparse
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from cli import (  # noqa: E402
    apply_profile_to_args,
    create_processing_options,
    load_profile,
    parse_pdf_inputs,
)


def test_parse_pdf_inputs_marks_reversed(tmp_path):
    pdf_a = tmp_path / "a.pdf"
    pdf_b = tmp_path / "b.pdf"
    pdf_a.write_bytes(b"%PDF-1.4\n")
    pdf_b.write_bytes(b"%PDF-1.4\n")

    args = argparse.Namespace(pdfs=[str(pdf_a), str(pdf_b)], reverse_pdfs=[1, 10])

    pdf_inputs = parse_pdf_inputs(args)

    assert len(pdf_inputs) == 2
    assert not pdf_inputs[0].reverse
    assert pdf_inputs[1].reverse


def test_apply_profile_respects_user_overrides():
    args = argparse.Namespace(
        enhance=False,
        ocr=True,  # user already enabled -> profile should not override
        optimize=False,
        auto_deskew=False,
        deskew=False,
    )
    profile = {"enhance": True, "ocr": False, "auto_deskew": True}

    apply_profile_to_args(args, profile)

    assert args.enhance is True
    assert args.ocr is True
    assert args.auto_deskew is True


def test_create_processing_options_maps_all_fields():
    args = argparse.Namespace(
        ocr=True,
        ocr_lang="eng",
        deskew=True,
        auto_deskew=False,
        deskew_threshold=0.3,
        enhance=True,
        denoise=False,
        binarize=True,
        sharpen=False,
        despeckle=True,
        autocrop=False,
        max_dpi=300,
        remove_blank=True,
        blank_threshold=0.9,
        optimize=True,
        compress_level=7,
        lossy=True,
        lossy_dpi=200,
        lossy_quality=80,
        title="Title",
        author="Author",
        subject="Subject",
        keywords="k1,k2",
        watermark="CONF",
        watermark_opacity=0.5,
        watermark_size=40,
        watermark_rotation=30,
        page_numbers=True,
        page_number_position="top-right",
        page_number_size=12,
        page_number_margin=15,
        quiet=True,
    )

    options = create_processing_options(args)

    assert options.ocr is True
    assert options.ocr_lang == "eng"
    assert options.deskew is True
    assert options.auto_deskew is False
    assert options.blank_threshold == pytest.approx(0.9)
    assert options.optimize is True
    assert options.lossy_quality == 80
    assert options.watermark == "CONF"
    assert options.page_number_position == "top-right"
    assert options.verbose is False


def test_load_profile_returns_known_profile():
    profile = load_profile("document")
    assert profile is not None
    assert "enhance" in profile
