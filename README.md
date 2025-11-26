# PDF Merger Tool

Herramienta moderna para combinar, procesar y optimizar PDFs escaneados cuando la impresora solo digitaliza a una cara. Mezcla automáticamente varios archivos (impares, pares, partes sueltas) en el orden correcto y permite aplicar OCR, limpieza, compresión o marcas de agua desde la línea de comandos, una interfaz web (Streamlit) o una API.

## Características principales

- ✅ Mezcla ilimitada de PDFs en el orden que definas
- ✅ Intercalado de páginas para escaneos a doble cara
- ✅ Inversión selectiva por archivo (`--reverse-pdfs 0 2 ...`)
- ✅ OCR multilenguaje, deskew, binarizado, nitidez, recorte, eliminación de páginas en blanco
- ✅ Compresión lossless y lossy (JPEG, DPI configurable)
- ✅ Metadatos (título, autor), números de página y marcas de agua
- ✅ Perfiles configurables (`config/profiles.yaml`) y UI en Streamlit

## Instalación

```bash
pip install -r requirements.txt
```

Requisitos mínimos: Python 3.10+, PyPDF2, pikepdf, Pillow, OpenCV, Tesseract (si usas `--ocr`).

## Uso rápido (CLI)

```bash
# Mezclar dos PDFs escaneados (impares y pares)
python cli.py impares.pdf pares.pdf -o completo.pdf --interleave --reverse-pdfs 1

# Añadir OCR en español y optimización
python cli.py impares.pdf pares.pdf -o completo_ocr.pdf \
  --interleave --reverse-pdfs 1 \
  --ocr --ocr-lang spa --auto-deskew --optimize

# Procesar varios PDFs ya ordenados
python cli.py cap1.pdf cap2.pdf anexos.pdf -o libro.pdf

# Re-encode lossy para reducir tamaño
python cli.py impares.pdf pares.pdf -o liviano.pdf \
  --interleave --reverse-pdfs 1 --lossy --lossy-dpi 120 --lossy-quality 60

# Consulta todas las opciones
python cli.py --help
```

Argumentos clave:
- Entradas: lista de rutas a PDF en el orden deseado.
- `-o/--output`: ruta de salida.
- `--interleave`: alterna páginas entre todos los PDFs (útil para escaneo doble cara).
- `--reverse-pdfs IDX [IDX ...]`: invierte la dirección de uno o más PDFs según su índice (0‑based).
- Procesamiento: `--ocr`, `--ocr-lang`, `--auto-deskew`, `--enhance`, `--denoise`, `--binarize`, `--sharpen`, `--autocrop`, `--remove-blank`, `--lossy`, `--lossy-dpi`, `--lossy-quality`, `--optimize`, `--compress-level`.
- Presentación: `--title`, `--author`, `--watermark`, `--page-numbers`.

## UI Web (Streamlit)

```bash
streamlit run streamlit_app.py
```

La barra lateral permite elegir tipología (perfil) y ajustar todas las opciones con tooltips explicativos. Tras procesar, podrás descargar el PDF resultante en la misma interfaz.

## API y GUI de ejemplo

- `web_api_example.py`: API REST (Flask) con endpoint `/api/merge`.
- `gui_example.py`: interfaz de escritorio (tkinter) para entornos sin navegador.

Ambas utilizan el mismo núcleo (`models/pdf_processor.py`) por lo que cualquier mejora en el core beneficia a todas las interfaces.

## Configuración y perfiles

`config/profiles.yaml` define perfiles reutilizables (`document`, `photo`, `ebook`, etc.). El valor por defecto se controla con la variable `PDF_MERGER_DEFAULT_PROFILE`. La UI de Streamlit permite alternarlos al vuelo.

## Tests

```bash
pytest
```

## Documentación detallada

- `docs/INSTALLATION.md`: instalación paso a paso y resolución de problemas.
- `docs/ARCHITECTURE.md`: diseño del core, interfaces y utilidades.
- `docs/ROADMAP.md`: mejoras planificadas y experimentos.

## Roadmap

Consulta `docs/ROADMAP.md` para conocer ideas y mejoras pendientes. Si añades una nueva interfaz o perfil, documenta el cambio en ese archivo.
