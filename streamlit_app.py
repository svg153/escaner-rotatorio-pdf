"""Streamlit interface for PDF Merger Tool."""

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

import streamlit as st
import yaml

from models.pdf_processor import PDFInput, ProcessingOptions, PDFMergerCore

LOGGER = logging.getLogger("pdf_merger_streamlit")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

DEFAULT_PROFILE_NAME = os.getenv("PDF_MERGER_DEFAULT_PROFILE", "document")
PROFILE_PATH = Path(__file__).parent / "config" / "profiles.yaml"

OPTION_FALLBACKS: Dict[str, object] = {
    "interleave": False,
    "ocr": False,
    "ocr_lang": "spa",
    "auto_deskew": False,
    "enhance": False,
    "denoise": False,
    "binarize": False,
    "sharpen": False,
    "autocrop": False,
    "remove_blank": False,
    "optimize": False,
    "compress_level": 5,
    "title": "",
    "author": "",
    "watermark": "",
    "page_numbers": False,
}

OCR_LANG_OPTIONS: Dict[str, str] = {
    "spa": "Español (spa)",
    "eng": "English (eng)",
    "fra": "Français (fra)",
    "deu": "Deutsch (deu)",
    "ita": "Italiano (ita)",
    "por": "Português (por)",
}


def save_uploaded_file(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> str:
    """Save an uploaded file to a temporary location and return the path."""
    suffix = Path(uploaded_file.name).suffix or '.pdf'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        return tmp_file.name


def cleanup_temp_files(paths: List[str]):
    """Delete temporary files."""
    for path in paths:
        try:
            os.remove(path)
        except OSError:
            pass


@st.cache_data(show_spinner=False)
def load_profiles_file() -> Dict[str, Dict[str, object]]:
    if not PROFILE_PATH.exists():
        return {}
    with PROFILE_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data


@st.cache_data(show_spinner=False)
def fetch_default_settings(profile_name: str) -> Dict[str, object]:
    profiles = load_profiles_file()
    return profiles.get(profile_name, {})


def initialize_defaults(defaults: Dict[str, object]):
    if st.session_state.get("defaults_initialized"):
        return
    for key, fallback in OPTION_FALLBACKS.items():
        st.session_state.setdefault(key, defaults.get(key, fallback))
    st.session_state["defaults_initialized"] = True


def apply_defaults(defaults: Dict[str, object]):
    for key, fallback in OPTION_FALLBACKS.items():
        st.session_state[key] = defaults.get(key, fallback)


def log_run(entry: dict) -> dict:
    """Append a log entry with the options the user selected."""
    entry.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    entry.setdefault("run_id", str(uuid4()))
    serialized = json.dumps(entry, ensure_ascii=False)
    LOGGER.info(serialized)
    return entry


def main():
    st.set_page_config(page_title="PDF Merger Tool", page_icon="📄", layout="wide")
    st.title("📄 PDF Merger Tool - Streamlit Edition")
    st.write(
        "Sube tus archivos PDF, configura las opciones y descarga un único PDF procesado."
    )

    profiles = load_profiles_file()
    default_values = fetch_default_settings(DEFAULT_PROFILE_NAME)
    initialize_defaults(default_values)

    with st.sidebar:
        st.header("⚙️ Opciones")
        profile_names = list(profiles.keys()) or [DEFAULT_PROFILE_NAME]
        default_index = profile_names.index(DEFAULT_PROFILE_NAME) if DEFAULT_PROFILE_NAME in profile_names else 0
        selected_profile = st.selectbox(
            "Tipología (perfil)",
            options=profile_names,
            index=default_index,
            key="selected_profile",
            help="Selecciona el perfil de configuración cargado desde config/profiles.yaml"
        )
        if selected_profile != st.session_state.get("current_profile"):
            apply_defaults(fetch_default_settings(selected_profile))
            st.session_state["current_profile"] = selected_profile

        interleave = st.checkbox(
            "Intercalar páginas",
            key="interleave",
            help="Útil cuando tienes páginas impares y pares por separado."
        )

        st.subheader("Mejoras")
        ocr = st.checkbox(
            "Agregar OCR",
            key="ocr",
            help="Crea una capa de texto buscable usando Tesseract. Requiere que tengas Tesseract instalado."
        )
        ocr_lang = st.selectbox(
            "Idioma OCR",
            options=list(OCR_LANG_OPTIONS.keys()),
            format_func=lambda code: OCR_LANG_OPTIONS.get(code, code),
            key="ocr_lang",
            help="Elige un idioma disponible en Tesseract (instala el paquete correspondiente en tu sistema)."
        )
        auto_deskew = st.checkbox(
            "Auto-enderezar",
            key="auto_deskew",
            help="Detecta la inclinación de cada página (OpenCV) y la corrige automáticamente."
        )
        enhance = st.checkbox(
            "Mejorar contraste/brillo",
            key="enhance",
            help="Aplica una curva de contraste y exposición para resaltar texto tenue."
        )
        denoise = st.checkbox(
            "Eliminar ruido",
            key="denoise",
            help="Suaviza motas/grano del escaneo usando filtros bilaterales."
        )
        binarize = st.checkbox(
            "Convertir a blanco y negro puro",
            key="binarize",
            help="Aplica binarización (umbral adaptativo). Ideal para texto, pero elimina colores."
        )
        sharpen = st.checkbox(
            "Mejorar nitidez",
            key="sharpen",
            help="Realza bordes del texto para que se vea más definido."
        )
        autocrop = st.checkbox(
            "Recortar bordes",
            key="autocrop",
            help="Recorta márgenes blancos detectados automáticamente."
        )
        remove_blank = st.checkbox(
            "Eliminar páginas en blanco",
            key="remove_blank",
            help="Detecta páginas vacías por porcentaje de blanco y las elimina."
        )
        optimize = st.checkbox(
            "Optimizar/Comprimir",
            key="optimize",
            help="Recomprime el PDF (pikepdf) para reducir el tamaño final."
        )
        compress_level = st.slider(
            "Nivel de compresión",
            min_value=0,
            max_value=9,
            key="compress_level",
            help="0 = sin compresión extra, 9 = máxima compresión (puede tardar más)."
        )

        st.subheader("Metadata")
        title = st.text_input("Título", key="title", help="Se incrusta en las propiedades del PDF.")
        author = st.text_input("Autor", key="author", help="Nombre que aparecerá como autor del documento.")
        watermark = st.text_input("Marca de agua", key="watermark", help="Texto grande y semitransparente sobre cada página.")
        page_numbers = st.checkbox(
            "Agregar números de página",
            key="page_numbers",
            help="Añade numeración en el pie de página."
        )

    uploaded_files = st.file_uploader(
        "Sube uno o varios archivos PDF",
        type=["pdf"],
        accept_multiple_files=True,
    )

    reverse_selection = []
    if uploaded_files:
        st.subheader("📑 Archivos cargados")
        st.markdown(
            "Selecciona qué archivos necesitan invertirse (por ejemplo, cuando se escanearon en orden invertido desde la bandeja)."
            " Cada archivo se procesará en el orden mostrado; si además activas **Intercalar páginas**,"
            " se alternarán siguiendo este listado."
        )

        for idx, uploaded_file in enumerate(uploaded_files, start=1):
            row = st.container()
            with row:
                cols = st.columns([0.7, 0.3])
                cols[0].markdown(f"**{idx}. {uploaded_file.name}**")
                invert_key = f"reverse_{idx}_{uploaded_file.name}"
                invert_flag = cols[1].checkbox(
                    "Invertir",
                    key=invert_key,
                    help="Activa si este PDF contiene páginas en orden inverso (ej. pares escaneadas al revés)",
                    value=st.session_state.get(invert_key, False)
                )
                status = "Invertido" if invert_flag else "Normal"
                cols[0].caption(status)
                if invert_flag:
                    reverse_selection.append(uploaded_file.name)

    output_filename = st.text_input(
        "Nombre del archivo resultante",
        value="resultado.pdf",
        help="Solo el nombre; se descargará al terminar."
    )

    st.info("Cada vez que pulses 'Procesar PDFs' se toman las opciones actuales. Cambia los parámetros y vuelve a generar para comparar resultados con los mismos archivos.")

    process_clicked = st.button("🚀 Procesar PDFs", use_container_width=True)

    if process_clicked:
        if not uploaded_files:
            st.error("Debes subir al menos un PDF.")
            st.stop()

        with st.spinner("Procesando documentos..."):
            temp_inputs = []
            pdf_inputs = []

            try:
                for uploaded_file in uploaded_files:
                    temp_path = save_uploaded_file(uploaded_file)
                    temp_inputs.append(temp_path)
                    pdf_inputs.append(
                        PDFInput(
                            path=temp_path,
                            reverse=uploaded_file.name in reverse_selection
                        )
                    )

                options = ProcessingOptions(
                    ocr=ocr,
                    ocr_lang=ocr_lang or "spa",
                    auto_deskew=auto_deskew,
                    enhance=enhance,
                    denoise=denoise,
                    binarize=binarize,
                    sharpen=sharpen,
                    autocrop=autocrop,
                    remove_blank=remove_blank,
                    optimize=optimize,
                    compress_level=compress_level,
                    title=title or None,
                    author=author or None,
                    watermark=watermark or None,
                    page_numbers=page_numbers,
                    verbose=False,
                )

                processor = PDFMergerCore(options)
                output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
                success = processor.merge_and_process(
                    pdf_inputs,
                    output_path,
                    interleave=interleave,
                )

                log_run({
                    "profile": selected_profile,
                    "files": [f.name for f in uploaded_files],
                    "reverse_selection": reverse_selection,
                    "interleave": interleave,
                    "options": {
                        "ocr": ocr,
                        "ocr_lang": ocr_lang,
                        "auto_deskew": auto_deskew,
                        "enhance": enhance,
                        "denoise": denoise,
                        "binarize": binarize,
                        "sharpen": sharpen,
                        "autocrop": autocrop,
                        "remove_blank": remove_blank,
                        "optimize": optimize,
                        "compress_level": compress_level,
                        "title": title,
                        "author": author,
                        "watermark": watermark,
                        "page_numbers": page_numbers,
                    },
                    "output_filename": output_filename,
                    "status": "success" if success else "error"
                })

                if not success:
                    st.error("Hubo un error al procesar los PDFs. Revisa la consola para más detalles.")
                else:
                    with open(output_path, "rb") as result_file:
                        st.success("✅ PDF generado correctamente")
                        st.download_button(
                            label="⬇️ Descargar PDF",
                            data=result_file,
                            file_name=output_filename or "resultado.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary"
                        )
            finally:
                cleanup_temp_files(temp_inputs)
                # El archivo final se elimina automáticamente cuando Streamlit termina


if __name__ == "__main__":
    main()
