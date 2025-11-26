import numpy as np
import pytest
from PIL import Image

import utils.image_processing as ip


@pytest.fixture(autouse=True)
def enable_dependencies(monkeypatch):
    monkeypatch.setattr(ip, "IMAGE_PROCESSING_AVAILABLE", True)
    monkeypatch.setattr(ip, "PDF_IMAGE_AVAILABLE", True)

    monkeypatch.setattr(ip, "Image", Image, raising=False)
    from PIL import ImageEnhance, ImageFilter

    monkeypatch.setattr(ip, "ImageEnhance", ImageEnhance, raising=False)
    monkeypatch.setattr(ip, "ImageFilter", ImageFilter, raising=False)
    monkeypatch.setattr(ip, "np", np, raising=False)

    class DummyFilters:
        @staticmethod
        def threshold_otsu(arr):
            return int(arr.mean())

    monkeypatch.setattr(ip, "filters", DummyFilters, raising=False)

    class DummyCV2:
        THRESH_BINARY = 0
        THRESH_OTSU = 0

        @staticmethod
        def fastNlMeansDenoisingColored(arr, *_args, **_kwargs):
            return arr

        @staticmethod
        def fastNlMeansDenoising(arr, *_args, **_kwargs):
            return arr

        @staticmethod
        def medianBlur(arr, *_args, **_kwargs):
            return arr

        @staticmethod
        def threshold(arr, *_args, **_kwargs):
            return None, arr

        @staticmethod
        def Canny(arr, *_args, **_kwargs):
            return arr

        @staticmethod
        def HoughLinesP(*_args, **_kwargs):
            return np.array([[[0, 0, 10, 0]]])

    monkeypatch.setattr(ip, "cv2", DummyCV2, raising=False)
    monkeypatch.setattr(ip, "convert_from_path", lambda *a, **k: [], raising=False)

    class DummyImg2Pdf:
        @staticmethod
        def convert(images):
            return b"PDF" + b"".join(images)

    monkeypatch.setattr(ip, "img2pdf", DummyImg2Pdf, raising=False)


def test_enhance_image_runs_transformations():
    img = Image.new("RGB", (10, 10), color="gray")
    enhanced = ip.enhance_image(img, contrast=1.2, brightness=1.1, sharpness=1.1)
    assert isinstance(enhanced, Image.Image)


def test_denoise_image_calls_cv2(monkeypatch):
    img = Image.new("RGB", (5, 5), color="white")
    called = {}

    class DummyCV2:
        @staticmethod
        def fastNlMeansDenoisingColored(arr, *_args):
            called["colored"] = arr.shape
            return arr

        @staticmethod
        def fastNlMeansDenoising(arr, *_args):
            called["gray"] = arr.shape
            return arr

        @staticmethod
        def medianBlur(arr, *_args):
            return arr

    monkeypatch.setattr(ip, "cv2", DummyCV2)

    result = ip.denoise_image(img, strength=5)
    assert isinstance(result, Image.Image)
    assert "colored" in called


def test_binarize_image_uses_threshold():
    img = Image.new("L", (10, 10), color=200)

    binary = ip.binarize_image(img, threshold=None)
    assert set(np.array(binary).flatten()) <= {0, 255}


def test_autocrop_image_trims_borders():
    img = Image.new("L", (20, 20), color=255)
    for x in range(5, 15):
        img.putpixel((x, 10), 0)

    cropped = ip.autocrop_image(img, margin=1)
    assert cropped.width < img.width


def test_adjust_dpi_resizes_image():
    img = Image.new("RGB", (10, 10), color="white")
    img.info["dpi"] = (72, 72)
    resized = ip.adjust_dpi(img, target_dpi=144)
    assert resized.width == 20


def test_process_pdf_images_runs_pipeline(monkeypatch, tmp_path):
    sequence = {
        "autocrop": 0,
        "denoise": 0,
        "despeckle": 0,
        "enhance": 0,
        "sharpen": 0,
        "binarize": 0,
    }

    def track(name):
        def wrapper(img):
            sequence[name] += 1
            return img

        return wrapper

    monkeypatch.setattr(
        ip,
        "convert_from_path",
        lambda *_a, **_k: [Image.new("RGB", (10, 10), color="white")],
        raising=False,
    )
    monkeypatch.setattr(ip, "autocrop_image", track("autocrop"))
    monkeypatch.setattr(ip, "denoise_image", track("denoise"))
    monkeypatch.setattr(ip, "despeckle_image", track("despeckle"))
    monkeypatch.setattr(ip, "enhance_image", track("enhance"))
    monkeypatch.setattr(ip, "sharpen_image", track("sharpen"))
    monkeypatch.setattr(ip, "binarize_image", track("binarize"))

    class DummyImg2Pdf:
        @staticmethod
        def convert(images):
            return b"PDF" + b"".join(images)

    monkeypatch.setattr(ip, "img2pdf", DummyImg2Pdf)

    output = tmp_path / "processed.pdf"
    success = ip.process_pdf_images(
        "input.pdf",
        str(output),
        enhance=True,
        denoise=True,
        binarize=True,
        sharpen=True,
        despeckle=True,
        autocrop=True,
        max_dpi=150,
        verbose=True,
    )

    assert success is True
    assert output.exists()
    assert all(count == 1 for count in sequence.values())


def test_process_pdf_images_returns_false_without_dependencies(monkeypatch, tmp_path):
    monkeypatch.setattr(ip, "IMAGE_PROCESSING_AVAILABLE", False)
    result = ip.process_pdf_images("a.pdf", str(tmp_path / "out.pdf"), verbose=True)
    assert result is False


def test_binarize_image_fallback_when_unavailable(monkeypatch):
    monkeypatch.setattr(ip, "IMAGE_PROCESSING_AVAILABLE", False)
    img = Image.new("RGB", (5, 5), color="white")
    converted = ip.binarize_image(img)
    assert converted.mode == "1"


def test_sharpen_and_despeckle(monkeypatch):
    img = Image.new("RGB", (5, 5), color="white")

    class DummyCV2:
        @staticmethod
        def medianBlur(arr, *_args, **_kwargs):
            return arr

    monkeypatch.setattr(ip, "cv2", DummyCV2, raising=False)
    sharpened = ip.sharpen_image(img)
    despeckled = ip.despeckle_image(img)
    assert isinstance(sharpened, Image.Image)
    assert isinstance(despeckled, Image.Image)


def test_autocrop_handles_empty_image():
    img = Image.new("L", (5, 5), color=255)
    cropped = ip.autocrop_image(img)
    assert cropped.size == img.size


def test_adjust_dpi_no_change():
    img = Image.new("RGB", (5, 5), color="white")
    img.info["dpi"] = (144, 144)
    result = ip.adjust_dpi(img, target_dpi=144)
    assert result == img


def test_process_pdf_images_handles_exception(monkeypatch, tmp_path):
    def boom(*_a, **_k):
        raise RuntimeError("fail")

    monkeypatch.setattr(ip, "convert_from_path", boom, raising=False)
    assert (
        ip.process_pdf_images("a.pdf", str(tmp_path / "out.pdf"), verbose=True) is False
    )
