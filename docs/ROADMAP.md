# Roadmap - Mejoras Futuras

## 🎯 Mejoras Prioritarias

### 1. OCR (Reconocimiento Óptico de Caracteres)
**Objetivo:** Hacer el PDF searchable/buscable
- [ ] Integración con Tesseract OCR (`pytesseract`)
- [ ] Detección automática de idioma
- [ ] Opción `--ocr` para añadir capa de texto invisible sobre imágenes
- [ ] Opción `--ocr-lang` para especificar idioma (español, inglés, etc.)
- [ ] Preservar formato original mientras se añade texto

**Ejemplo de uso:**
```bash
python cli.py impares.pdf pares.pdf -o salida.pdf --interleave --reverse-pdfs 1 --ocr --ocr-lang spa
```

**Librerías necesarias:**
- `pytesseract` - Python wrapper para Tesseract
- `pdf2image` - Convertir páginas PDF a imágenes
- Tesseract instalado en el sistema

---

### 2. Auto-Deskew Inteligente
**Objetivo:** Detectar y corregir automáticamente páginas torcidas
- [ ] Detección de inclinación con OpenCV o deskew
- [ ] Rotación automática basada en contenido de texto
- [ ] Detección de bordes para alineación
- [ ] Opción `--auto-deskew` con detección automática de ángulo

**Librerías necesarias:**
- `opencv-python` o `deskew`
- `numpy` para procesamiento de imágenes
- `scipy` para transformaciones

---

### 3. Mejora de Calidad de Imagen
**Objetivo:** Mejorar la legibilidad de documentos escaneados
- [ ] `--enhance` - Mejora automática de contraste y brillo
- [ ] `--denoise` - Eliminación de ruido en escaneos
- [ ] `--binarize` - Conversión a blanco y negro puro (reduce tamaño)
- [ ] `--sharpen` - Mejora de nitidez del texto
- [ ] `--despeckle` - Eliminar manchas y artefactos

**Librerías necesarias:**
- `Pillow` (ya incluido)
- `opencv-python`
- `scikit-image`

---

### 4. Detección y Eliminación de Páginas en Blanco
**Objetivo:** Limpiar el documento automáticamente
- [ ] Detectar páginas vacías o casi vacías
- [ ] Opción `--remove-blank` para eliminarlas automáticamente
- [ ] Umbral configurable de "blancura"
- [ ] Reporte de páginas eliminadas

---

### 5. Compresión Avanzada
**Objetivo:** Reducir drásticamente el tamaño del archivo
- [ ] Múltiples niveles de compresión (bajo, medio, alto)
- [ ] Conversión de imágenes a JPEG con calidad configurable
- [ ] Downsampling de imágenes (reducir DPI)
- [ ] Opción `--compress-level` (1-9)
- [ ] Opción `--max-dpi` para limitar resolución

**Ejemplo:**
```bash
--optimize --compress-level 7 --max-dpi 300
```

---

### 6. Corrección de Márgenes y Recorte
**Objetivo:** Eliminar bordes innecesarios
- [ ] Auto-crop para eliminar márgenes blancos
- [ ] Detección de bordes del contenido real
- [ ] Opción `--autocrop` con márgenes configurables
- [ ] `--margin` para añadir margen uniforme

---

### 7. Marca de Agua y Metadata
**Objetivo:** Añadir información al documento
- [ ] `--watermark` para añadir marca de agua (texto o imagen)
- [ ] `--metadata` para establecer autor, título, tema, etc.
- [ ] `--page-numbers` para añadir numeración
- [ ] Timestamps automáticos

---

### 8. Bookmarks y Tabla de Contenidos
**Objetivo:** Mejorar navegabilidad
- [ ] Añadir marcadores automáticos
- [ ] Detección de capítulos/secciones
- [ ] Opción `--add-toc` para tabla de contenidos
- [ ] `--bookmark-file` para cargar estructura desde JSON/YAML

---

### 9. Detección Automática de Orden
**Objetivo:** Simplificar el uso
- [ ] Analizar PDFs y detectar si necesitan inversión
- [ ] Modo `--auto` que determine el mejor orden
- [ ] Heurística basada en numeración de páginas
- [ ] Sugerencias al usuario sobre configuración óptima

---

### 10. Procesamiento por Lotes (Batch)
**Objetivo:** Procesar múltiples documentos
- [ ] `--batch` para procesar directorios completos
- [ ] Patrón de nombres para emparejar PDFs
- [ ] Procesamiento paralelo de múltiples documentos
- [ ] Archivo de configuración para opciones comunes

**Ejemplo:**
```bash
python cli.py --batch input_dir/ --output-dir output_dir/ --config config.yaml
```

---

### 11. Interfaz Gráfica (GUI)
**Objetivo:** Facilitar uso para usuarios no técnicos
- [ ] GUI simple con tkinter o PyQt
- [ ] Drag & drop de archivos
- [ ] Preview de páginas
- [ ] Configuración visual de opciones

---

### 12. Validación y Reparación
**Objetivo:** Asegurar calidad del resultado
- [ ] Validar integridad del PDF resultante
- [ ] Reparar PDFs corruptos antes de mezclar
- [ ] Verificar que todas las páginas son legibles
- [ ] `--validate` para modo verificación

---

### 13. Formatos Adicionales
**Objetivo:** Ampliar compatibilidad
- [ ] Importar desde imágenes (JPG, PNG, TIFF)
- [ ] Exportar a otros formatos (PDF/A, PDF/X)
- [ ] Conversión desde TIFF multipágina
- [ ] Soporte para CBR/CBZ (cómics)

---

### 14. Configuración Avanzada
**Objetivo:** Personalización detallada
- [ ] Archivo de configuración `.pdfmergerc`
- [ ] Perfiles predefinidos (documento, foto, ebook, etc.)
- [ ] `--profile` para cargar configuración guardada
- [ ] Guardar opciones favoritas

---

### 15. Logging y Reportes
**Objetivo:** Mejor diagnóstico y seguimiento
- [ ] Log detallado de operaciones
- [ ] Reporte JSON/HTML del proceso
- [ ] Métricas de calidad (tamaño, DPI, etc.)
- [ ] `--report` para generar informe completo

---

## 📦 Dependencias Proyectadas

### Básicas (ya incluidas)
- ✅ PyPDF2
- ✅ pikepdf
- ✅ Pillow

### OCR
- `pytesseract`
- `pdf2image`
- `tesseract` (sistema)

### Procesamiento de Imagen
- `opencv-python` (cv2)
- `numpy`
- `scikit-image`
- `deskew`

### GUI
- `PyQt6` o `tkinter` (incluido en Python)
- `Pillow` para preview

### Avanzadas
- `img2pdf` - Conversión de imágenes
- `ocrmypdf` - OCR integrado para PDFs
- `reportlab` - Generar PDFs desde cero
- `pdfplumber` - Extracción avanzada de texto

---

## 🚀 Plan de Implementación

### Fase 1 - Calidad (1-2 meses)
1. OCR básico con Tesseract
2. Auto-deskew inteligente
3. Mejora de calidad de imagen

### Fase 2 - Automatización (1 mes)
4. Detección de páginas en blanco
5. Detección automática de orden
6. Compresión avanzada

### Fase 3 - Usabilidad (1-2 meses)
7. Procesamiento por lotes
8. Configuración avanzada
9. Logging y reportes

### Fase 4 - Extras (flexible)
10. Marca de agua y metadata
11. Bookmarks automáticos
12. GUI
13. Validación y reparación

---

## 💡 Ideas Adicionales

### Integración con Servicios
- [ ] Subida automática a Google Drive, Dropbox
- [ ] Integración con Evernote, OneNote
- [ ] API REST para uso en workflows

### Machine Learning
- [ ] Clasificación automática de documentos
- [ ] Detección de tipo de documento (factura, carta, etc.)
- [ ] Extracción inteligente de campos (fechas, importes, etc.)

### Colaboración
- [ ] Modo servidor para uso compartido
- [ ] Colas de procesamiento
- [ ] Notificaciones por email al completar

### Cloud/Docker
- [ ] Dockerfile para despliegue fácil
- [ ] Versión cloud-ready
- [ ] Lambda/Function para procesamiento serverless

---

## 📝 Contribuciones

¿Tienes ideas para mejorar el proyecto? 
1. Abre un issue con tu sugerencia
2. Implementa la funcionalidad y crea un PR
3. Documenta el uso en el README

---

## 🎓 Recursos de Aprendizaje

- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)
- [OpenCV Python Tutorials](https://docs.opencv.org/master/d6/d00/tutorial_py_root.html)
- [pikepdf Documentation](https://pikepdf.readthedocs.io/)
- [PDF Reference (ISO 32000)](https://www.adobe.com/devnet/pdf/pdf_reference.html)
