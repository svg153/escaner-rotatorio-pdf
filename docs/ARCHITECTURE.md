# 🏗️ Nueva Arquitectura - Documentación

## Cambios Principales

### ✅ **Separación de Responsabilidades**

La lógica de negocio ha sido completamente separada del CLI, permitiendo:
- ✅ Reutilización en diferentes interfaces (CLI, Web, GUI, API)
- ✅ Testing más sencillo
- ✅ Código más mantenible
- ✅ Escalabilidad futura

---

## 📁 Estructura Nueva

```
de_escaner_rotatorio_a_pdf_completo/
│
├── 🧠 CORE LOGIC (models/)
│   └── pdf_processor.py              ← Lógica principal
│       ├── PDFInput                  (clase)
│       ├── ProcessingOptions         (clase)
│       └── PDFMergerCore            (clase principal)
│
├── 🖥️ INTERFACES
│   ├── cli.py                        ← CLI nuevo (sin lógica)
│   ├── web_api_example.py           ← Ejemplo API REST
│   └── gui_example.py               ← Ejemplo GUI tkinter
│
└── 🛠️ UTILITIES
    └── utils/                        ← Utilidades compartidas
        ├── ocr.py
        ├── image_processing.py
        ├── deskew.py
        ├── blank_detection.py
        └── metadata.py
```

---

## 🔄 Cambios de API

### Antes (CLI acoplado)
```python
# Todo mezclado en un solo archivo
python pdf_merger_advanced.py --first a.pdf --second b.pdf -o out.pdf
```

### Ahora (Arquitectura limpia)

#### **Opción 1: CLI Nuevo**
```bash
# Múltiples PDFs como argumentos posicionales
python cli.py pdf1.pdf pdf2.pdf pdf3.pdf -o output.pdf

# Intercalar (útil para escaneos doble cara)
python cli.py impares.pdf pares.pdf -o output.pdf --interleave --reverse-pdfs 1

# Procesar un solo PDF
python cli.py documento.pdf -o procesado.pdf --ocr --optimize
```

#### **Opción 2: Uso Programático**
```python
from models.pdf_processor import PDFInput, ProcessingOptions, PDFMergerCore

# Crear inputs
pdfs = [
    PDFInput(path="pdf1.pdf", reverse=False),
    PDFInput(path="pdf2.pdf", reverse=True),
    PDFInput(path="pdf3.pdf", reverse=False)
]

# Configurar opciones
options = ProcessingOptions(
    ocr=True,
    ocr_lang='spa',
    optimize=True,
    enhance=True
)

# Procesar
processor = PDFMergerCore(options)
processor.merge_and_process(pdfs, "output.pdf")
```

#### **Opción 3: API REST**
```bash
# Iniciar servidor
python web_api_example.py

# Llamar API
curl -X POST http://localhost:5000/api/merge \
  -F "files=@pdf1.pdf" \
  -F "files=@pdf2.pdf" \
  -F "interleave=true" \
  -o merged.pdf
```

#### **Opción 4: GUI**
```bash
python gui_example.py
# Se abre ventana gráfica
```

---

## 📊 Clases Principales

### 1. **PDFInput**
Representa un PDF de entrada con configuración.

```python
@dataclass
class PDFInput:
    path: str          # Ruta al archivo PDF
    reverse: bool = False  # Si invertir páginas
```

**Ejemplo:**
```python
# PDF normal
pdf1 = PDFInput(path="documento.pdf")

# PDF con páginas invertidas
pdf2 = PDFInput(path="pares.pdf", reverse=True)
```

---

### 2. **ProcessingOptions**
Todas las opciones de procesamiento en un solo objeto.

```python
@dataclass
class ProcessingOptions:
    # OCR
    ocr: bool = False
    ocr_lang: str = 'spa'
    
    # Deskew
    deskew: bool = False
    auto_deskew: bool = False
    
    # Imagen
    enhance: bool = False
    denoise: bool = False
    binarize: bool = False
    # ... más opciones
```

**Ejemplo:**
```python
# Perfil para documentos de oficina
options = ProcessingOptions(
    ocr=True,
    ocr_lang='spa',
    binarize=True,
    optimize=True,
    compress_level=7
)

# Perfil para fotografías
options = ProcessingOptions(
    enhance=True,
    denoise=True,
    optimize=False
)
```

---

### 3. **PDFMergerCore**
Clase principal que ejecuta toda la lógica.

```python
class PDFMergerCore:
    def __init__(self, options: ProcessingOptions)
    
    # Métodos principales
    def merge_pdfs(pdf_inputs, output_path)
    def interleave_pdfs(pdf_inputs, output_path)
    def process_pdf(input_pdf, output_pdf)
    def merge_and_process(pdf_inputs, output_path, interleave)
```

**Ejemplo:**
```python
# Crear procesador
processor = PDFMergerCore(options)

# Caso 1: Solo mezclar
processor.merge_pdfs(pdfs, "merged.pdf")

# Caso 2: Intercalar (escaneos doble cara)
processor.interleave_pdfs(pdfs, "interleaved.pdf")

# Caso 3: Solo procesar
processor.process_pdf("input.pdf", "output.pdf")

# Caso 4: Mezclar y procesar
processor.merge_and_process(pdfs, "final.pdf", interleave=True)
```

---

## 🎯 Casos de Uso

### Caso 1: CLI Simple
**Escenario:** Usuario quiere mezclar 3 PDFs desde terminal

```bash
python cli.py doc1.pdf doc2.pdf doc3.pdf -o resultado.pdf
```

**Ventajas:**
- Simple y directo
- Sin necesidad de especificar "first" y "second"
- Soporta cualquier número de PDFs

---

### Caso 2: Escaneo Doble Cara
**Escenario:** Escaneé páginas impares y pares por separado

```bash
# El segundo PDF (índice 1) está al revés
python cli.py impares.pdf pares.pdf -o completo.pdf --interleave --reverse-pdfs 1
```

**Ventajas:**
- Intercala automáticamente
- Controla qué PDFs invertir por índice
- Resultado final ordenado correctamente

---

### Caso 3: Web Application
**Escenario:** Servicio web para que usuarios suban y procesen PDFs

```python
# web_api_example.py ya implementado
from flask import Flask, request, send_file
from models.pdf_processor import PDFMergerCore, PDFInput, ProcessingOptions

@app.route('/api/merge', methods=['POST'])
def merge_pdfs():
    # Recibir archivos
    files = request.files.getlist('files')
    
    # Crear inputs
    pdf_inputs = [PDFInput(path=f.path) for f in files]
    
    # Procesar
    processor = PDFMergerCore(ProcessingOptions())
    processor.merge_and_process(pdf_inputs, output_path)
    
    # Devolver resultado
    return send_file(output_path)
```

**Ventajas:**
- Misma lógica que CLI
- Sin duplicación de código
- Fácil de mantener

---

### Caso 4: Desktop Application
**Escenario:** Aplicación de escritorio con interfaz gráfica

```python
# gui_example.py ya implementado
import tkinter as tk
from models.pdf_processor import PDFMergerCore, PDFInput, ProcessingOptions

class PDFMergerGUI:
    def process_pdfs(self):
        # Obtener archivos de la interfaz
        pdf_inputs = [PDFInput(path=f) for f in self.pdf_files]
        
        # Crear opciones desde checkboxes
        options = ProcessingOptions(
            ocr=self.ocr_var.get(),
            optimize=self.optimize_var.get()
        )
        
        # Procesar
        processor = PDFMergerCore(options)
        processor.merge_and_process(pdf_inputs, output_path)
```

**Ventajas:**
- Usuario no técnico puede usar
- Misma lógica confiable
- Visual y fácil de usar

---

### Caso 5: Script Automatizado
**Escenario:** Procesar automáticamente PDFs en un servidor

```python
#!/usr/bin/env python3
from pathlib import Path
from models.pdf_processor import PDFInput, ProcessingOptions, PDFMergerCore

# Buscar todos los PDFs en un directorio
pdf_dir = Path("/incoming/pdfs")
pdfs = [PDFInput(path=str(f)) for f in pdf_dir.glob("*.pdf")]

# Configurar para archivado
options = ProcessingOptions(
    ocr=True,
    ocr_lang='spa',
    remove_blank=True,
    optimize=True,
    title="Documento Archivado",
    author="Sistema Automático"
)

# Procesar
processor = PDFMergerCore(options)
processor.merge_and_process(pdfs, "/archive/merged.pdf")
```

**Ventajas:**
- Automatización completa
- Reutiliza toda la lógica
- Configurable vía código

---

## 🔧 Migración desde Versión Antigua

### CLI Antiguo → Nuevo

**Antes (CLI legacy, ya retirado):**
```bash
python legacy_cli.py --first a.pdf --second b.pdf -o out.pdf
```

**Ahora:**
```bash
python cli.py a.pdf b.pdf -o out.pdf
```

**Antes (intercalar con legacy):**
```bash
python legacy_cli.py --first impares.pdf --second pares.pdf -o out.pdf
```

**Ahora:**
```bash
python cli.py impares.pdf pares.pdf -o out.pdf --interleave --reverse-pdfs 1
```

---

### Código Antiguo → Nuevo

**Antes:**
```python
# Función monolítica
merge_pdfs(pdf1, pdf2, output, reverse_first, reverse_second, position, ...)
```

**Ahora:**
```python
# Arquitectura limpia
pdfs = [PDFInput("a.pdf"), PDFInput("b.pdf", reverse=True)]
options = ProcessingOptions(ocr=True, optimize=True)
processor = PDFMergerCore(options)
processor.merge_and_process(pdfs, "output.pdf")
```

---

## 📈 Ventajas de la Nueva Arquitectura

### ✅ **1. Flexibilidad**
- Usa la misma lógica en CLI, Web, GUI, Scripts
- Fácil añadir nuevas interfaces sin tocar el core

### ✅ **2. Testabilidad**
```python
# Test unitario simple
def test_merge():
    pdfs = [PDFInput("test1.pdf"), PDFInput("test2.pdf")]
    options = ProcessingOptions()
    processor = PDFMergerCore(options)
    
    result = processor.merge_pdfs(pdfs, "output.pdf")
    assert result == True
```

### ✅ **3. Mantenibilidad**
- Cambios en lógica solo afectan `models/pdf_processor.py`
- Interfaces no necesitan actualizarse
- Menos bugs, menos duplicación

### ✅ **4. Escalabilidad**
- Fácil añadir nuevas funcionalidades
- Código organizado y modular
- Documentación clara

### ✅ **5. Reutilización**
- Misma lógica en todos lados
- No repetir código
- DRY (Don't Repeat Yourself)

---

## 🚀 Próximos Pasos

### Interfaces Futuras

1. **REST API Completa**
   - Autenticación
   - Rate limiting
   - Documentación OpenAPI/Swagger

2. **Web App con React**
   - Frontend moderno
   - Drag & drop de archivos
   - Preview de PDFs

3. **Electron App**
   - Aplicación de escritorio cross-platform
   - Más features que GUI simple

4. **CLI Mejorado**
   - Autocompletado
   - Colores en terminal
   - Barra de progreso visual

5. **Batch Processor**
   - Procesar directorios completos
   - Paralelización
   - Monitoreo de carpetas

---

## 📖 Ejemplos Completos

Ver archivos:
- `cli.py` - CLI completo funcional
- `web_api_example.py` - API REST con Flask
- `gui_example.py` - GUI con tkinter

---

## 🤝 Contribuir

Para añadir una nueva interfaz:

1. Importar las clases del core:
```python
from models.pdf_processor import PDFInput, ProcessingOptions, PDFMergerCore
```

2. Crear inputs y options según tu interfaz

3. Usar el procesador:
```python
processor = PDFMergerCore(options)
processor.merge_and_process(pdfs, output_path)
```

4. ¡Listo! La lógica compleja ya está implementada.

---

**La arquitectura está lista para el futuro.** 🚀
