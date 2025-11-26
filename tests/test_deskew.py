import pytest
from PIL import Image

import utils.deskew as dk


@pytest.fixture(autouse=True)
def reset_flags(monkeypatch):
    monkeypatch.setattr(dk, "DESKEW_AVAILABLE", True)
    monkeypatch.setattr(dk, "PDF_IMAGE_AVAILABLE", True)


def test_detect_skew_angle_returns_zero_when_disabled(monkeypatch):
    monkeypatch.setattr(dk, "DESKEW_AVAILABLE", False)
    img = Image.new("RGB", (5, 5), color="white")
    assert dk.detect_skew_angle(img) == 0.0


def test_auto_deskew_image_rotates_when_angle_exceeds_threshold(monkeypatch):
    img = Image.new("RGB", (10, 10), color="white")

    monkeypatch.setattr(dk, "detect_skew_angle", lambda _img: 5.0)

    calls = {}

    def fake_rotate(image, angle):
        calls["angle"] = angle
        return image

    monkeypatch.setattr(dk, "rotate_image", fake_rotate)

    corrected, angle = dk.auto_deskew_image(img, threshold=1.0, verbose=True)
    assert angle == 5.0
    assert calls["angle"] == -5.0
    assert corrected is img


def test_auto_deskew_pdf_generates_output(monkeypatch, tmp_path):
    dummy_img = Image.new("RGB", (10, 10), color="white")

    monkeypatch.setattr(
        dk,
        "convert_from_path",
        lambda *_args, **_kwargs: [dummy_img.copy(), dummy_img.copy()],
        raising=False,
    )
    monkeypatch.setattr(
        dk,
        "auto_deskew_image",
        lambda img, **_: (img, 0.0),
    )

    class DummyImg2Pdf:
        @staticmethod
        def convert(images):
            return b"PDF" + b"".join(images)

    monkeypatch.setattr(dk, "img2pdf", DummyImg2Pdf, raising=False)

    output = tmp_path / "deskewed.pdf"
    success = dk.auto_deskew_pdf("input.pdf", str(output), threshold=0.1, verbose=True)

    assert success is True
    assert output.exists()
    assert output.read_bytes().startswith(b"PDF")


def test_auto_deskew_pdf_returns_false_without_deps(monkeypatch, tmp_path):
    monkeypatch.setattr(dk, "DESKEW_AVAILABLE", False)
    result = dk.auto_deskew_pdf("a.pdf", str(tmp_path / "out.pdf"), verbose=True)
    assert result is False


def test_detect_skew_angle_with_mocked_cv2(monkeypatch):
    img = Image.new("RGB", (20, 20), color="white")

    class DummyCV2:
        THRESH_BINARY = 0
        THRESH_OTSU = 0

        @staticmethod
        def threshold(arr, *_args, **_kwargs):
            return None, arr

        @staticmethod
        def Canny(arr, *_args, **_kwargs):
            return arr

        @staticmethod
        def HoughLinesP(*_args, **_kwargs):
            return [[(0, 0, 10, 10)], [(0, 10, 10, 0)]]

    monkeypatch.setattr(dk, "DESKEW_AVAILABLE", True)
    monkeypatch.setattr(dk, "cv2", DummyCV2)
    angle = dk.detect_skew_angle(img)
    assert isinstance(angle, float)


def test_rotate_image_and_auto_deskew_threshold(monkeypatch):
    img = Image.new("RGB", (10, 10), color="white")

    def fake_detect(_img):
        return 0.1

    monkeypatch.setattr(dk, "detect_skew_angle", fake_detect)
    rotated = dk.rotate_image(img, 5)
    assert isinstance(rotated, Image.Image)

    corrected, angle = dk.auto_deskew_image(img, threshold=1.0, verbose=True)
    assert angle == 0.1
    assert corrected is img


def test_auto_deskew_pdf_handles_exception(monkeypatch, tmp_path):
    monkeypatch.setattr(dk, "DESKEW_AVAILABLE", True)
    monkeypatch.setattr(dk, "PDF_IMAGE_AVAILABLE", True)

    def boom(*_a, **_k):
        raise RuntimeError("fail")

    monkeypatch.setattr(dk, "convert_from_path", boom, raising=False)
    assert (
        dk.auto_deskew_pdf("in.pdf", str(tmp_path / "out.pdf"), verbose=True) is False
    )
