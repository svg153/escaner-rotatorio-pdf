# 🚀 Guía de Instalación y Configuración

## Índice

1. [Instalación Rápida](#instalación-rápida)
2. [Instalación Detallada por Sistema](#instalación-detallada-por-sistema)
3. [Verificación de Instalación](#verificación-de-instalación)
4. [Solución de Problemas](#solución-de-problemas)
5. [Primeros Pasos](#primeros-pasos)

---

## Instalación Rápida

### Para usuarios de Linux (Ubuntu/Debian)

```bash
# 1. Instalar dependencias del sistema
sudo apt-get update
sudo apt-get install -y python3 python3-pip tesseract-ocr tesseract-ocr-spa poppler-utils

# 2. Instalar dependencias Python
pip3 install -r requirements.txt

# 3. Probar
python3 cli.py --help
```

### Para usuarios de macOS

```bash
# 1. Instalar Homebrew (si no lo tienes)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Instalar dependencias
brew install python tesseract tesseract-lang poppler

# 3. Instalar dependencias Python
pip3 install -r requirements.txt

# 4. Probar
python3 cli.py --help
```

### Para usuarios de Windows

```bash
# 1. Instalar Python desde https://www.python.org/downloads/
# 2. Instalar Tesseract desde https://github.com/UB-Mannheim/tesseract/wiki
# 3. Instalar Poppler desde https://github.com/oschwartz10612/poppler-windows/releases/
# 4. Añadir al PATH las rutas de Tesseract y Poppler

# 5. Instalar dependencias Python
pip install -r requirements.txt

# 6. Probar
python cli.py --help
```

---

## Instalación Detallada por Sistema

### 🐧 Linux (Ubuntu/Debian)

#### Paso 1 (Linux): Python y pip

```bash
# Verificar Python
python3 --version  # Debe ser 3.6 o superior

# Instalar si no existe
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

#### Paso 2 (Linux): Tesseract OCR

```bash
# Instalar Tesseract
sudo apt-get install tesseract-ocr

# Instalar paquetes de idiomas
sudo apt-get install tesseract-ocr-spa  # Español
sudo apt-get install tesseract-ocr-eng  # Inglés
sudo apt-get install tesseract-ocr-fra  # Francés
sudo apt-get install tesseract-ocr-deu  # Alemán

# Verificar instalación
tesseract --version
tesseract --list-langs
```

#### Paso 3 (Linux): Poppler

```bash
# Instalar Poppler utilities
sudo apt-get install poppler-utils

# Verificar instalación
pdftoppm -v
```

#### Paso 4 (Linux): Dependencias Python

##### Opción A: Instalación Global

```bash
pip3 install -r requirements.txt
```

##### Opción B: Entorno Virtual (Recomendado)

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### Paso 5 (Linux): Dependencias Opcionales del Sistema

```bash
# Para mejor rendimiento en procesamiento de imágenes
sudo apt-get install libjpeg-dev libpng-dev libtiff-dev
```

---

### 🍎 macOS

#### Paso 1 (macOS): Homebrew

```bash
# Instalar Homebrew si no existe
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Verificar
brew --version
```

#### Paso 2 (macOS): Python

```bash
# Instalar Python 3
brew install python

# Verificar
python3 --version
```

#### Paso 3 (macOS): Tesseract

```bash
# Instalar Tesseract
brew install tesseract

# Instalar idiomas adicionales
brew install tesseract-lang

# Verificar
tesseract --version
tesseract --list-langs
```

#### Paso 4 (macOS): Poppler

```bash
# Instalar Poppler
brew install poppler

# Verificar
pdftoppm -v
```

#### Paso 5 (macOS): Dependencias Python

```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

### 🪟 Windows

#### Paso 1 (Windows): Python

1. Descargar Python desde [python.org](https://www.python.org/downloads/)
2. Durante instalación, marcar **"Add Python to PATH"**
3. Verificar en CMD:

```cmd
python --version
pip --version
```

#### Paso 2 (Windows): Tesseract OCR

1. Descargar desde [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Ejecutar instalador (ej: `tesseract-ocr-w64-setup-5.3.0.exe`)
3. Durante instalación, seleccionar idiomas adicionales (español, inglés, etc.)
4. Añadir al PATH:
   - Ruta típica: `C:\Program Files\Tesseract-OCR`
   - Panel de Control → Sistema → Variables de entorno
   - Añadir a PATH: `C:\Program Files\Tesseract-OCR`
5. Verificar en CMD:

```cmd
tesseract --version
tesseract --list-langs
```

#### Paso 3 (Windows): Poppler

1. Descargar desde [Poppler Windows](https://github.com/oschwartz10612/poppler-windows/releases/)
2. Extraer ZIP (ej: `poppler-24.02.0`)
3. Añadir al PATH:
   - Ruta típica: `C:\poppler\Library\bin`
   - Panel de Control → Sistema → Variables de entorno
   - Añadir a PATH: `C:\poppler\Library\bin`
4. Verificar en CMD:

```cmd
pdftoppm -v
```

#### Paso 4 (Windows): Dependencias Python

```cmd
# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## Verificación de Instalación

### Script de Verificación Automática

Crea un archivo `test_installation.py`:

```python
#!/usr/bin/env python3
"""Script para verificar la instalación."""

def check_python_packages():
    """Verifica paquetes Python."""
    packages = [
        'PyPDF2', 'pikepdf', 'PIL', 'pytesseract',
        'pdf2image', 'cv2', 'numpy', 'skimage',
        'reportlab', 'pdfplumber', 'img2pdf', 'yaml', 'tqdm'
    ]

    print("Verificando paquetes Python...")
    for pkg in packages:
        try:
            if pkg == 'PIL':
                __import__('PIL')
            elif pkg == 'cv2':
                __import__('cv2')
            else:
                __import__(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} (no instalado)")
    print()

def check_system_dependencies():
    """Verifica dependencias del sistema."""
    import subprocess
    import sys

    print("Verificando dependencias del sistema...")

    # Tesseract
    try:
        result = subprocess.run(['tesseract', '--version'],
                              capture_output=True, text=True)
        print(f"  ✅ Tesseract OCR")
    except FileNotFoundError:
        print(f"  ❌ Tesseract OCR (no encontrado)")

    # Poppler
    try:
        result = subprocess.run(['pdftoppm', '-v'],
                              capture_output=True, text=True)
        print(f"  ✅ Poppler (pdftoppm)")
    except FileNotFoundError:
        print(f"  ❌ Poppler (no encontrado)")

    print()

def check_tesseract_languages():
    """Verifica idiomas de Tesseract."""
    import subprocess

    print("Idiomas disponibles en Tesseract:")
    try:
        result = subprocess.run(['tesseract', '--list-langs'],
                              capture_output=True, text=True)
        langs = result.stdout.strip().split('\n')[1:]  # Skip header
        for lang in langs:
            print(f"  • {lang}")
    except:
        print("  ❌ No se pudo verificar")
    print()

if __name__ == '__main__':
    print("=" * 50)
    print("VERIFICACIÓN DE INSTALACIÓN")
    print("=" * 50)
    print()

    check_python_packages()
    check_system_dependencies()
    check_tesseract_languages()

    print("=" * 50)
    print("Verificación completada")
    print("=" * 50)
```

Ejecutar:

```bash
python3 test_installation.py
```

### Verificación Manual

```bash
# 1. Python
python3 --version

# 2. Tesseract
tesseract --version
tesseract --list-langs

# 3. Poppler
pdftoppm -v

# 4. Paquetes Python
pip list | grep -E "PyPDF2|pikepdf|Pillow|pytesseract|pdf2image|opencv|numpy|scikit|reportlab|yaml"

# 5. Herramienta
python3 cli.py --help
```

---

## Solución de Problemas

### Error: `ModuleNotFoundError: No module named 'PIL'`

```bash
pip install Pillow
```

### Error: `TesseractNotFoundError`

```bash
# Linux/Mac
which tesseract

# Windows
where tesseract

# Si no aparece, añadir al PATH
```

### Error: `pdf2image.exceptions.PDFInfoNotInstalledError`

```bash
# Instalar Poppler según tu sistema
# Ver pasos de instalación arriba
```

### Error: `ModuleNotFoundError: No module named 'cv2'`

```bash
pip install opencv-python
```

### Error: Instalación lenta o falla

```bash
# Instalar con más tiempo de timeout
pip install --timeout=1000 -r requirements.txt

# O instalar uno por uno
pip install PyPDF2
pip install pikepdf
pip install Pillow
# ... etc
```

### Problemas con numpy en Windows

Descarga el wheel precompilado desde
<https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy> y luego instala:

```bash
pip install numpy‑1.24.0‑cp311‑cp311‑win_amd64.whl
```

---

## Primeros Pasos

### Test Básico

```bash
# Usa cualquier par de PDFs que tengas
python3 cli.py test1.pdf test2.pdf -o output.pdf

# Si tus escaneos son de doble cara (impares/pares)
python3 cli.py test1.pdf test2.pdf -o output_intercalado.pdf \
  --interleave --reverse-pdfs 1
```

### Ejemplo Real

```bash
# Con OCR y optimización
python3 cli.py impares.pdf pares.pdf \
  -o resultado.pdf \
  --interleave --reverse-pdfs 1 \
  --ocr --ocr-lang spa \
  --auto-deskew --optimize \
  --remove-blank
```

### Verificar Resultado

```bash
# Ver metadata del PDF generado
pdfinfo resultado.pdf

# Ver tamaño
ls -lh resultado.pdf
```

---

## Actualización

### Actualizar dependencias

```bash
pip install --upgrade -r requirements.txt
```

### Actualizar herramienta

```bash
git pull  # Si es un repositorio Git
# O descargar la última versión
```

---

## Desinstalación

### Eliminar paquetes Python

```bash
pip uninstall -r requirements.txt -y
```

### Eliminar dependencias del sistema

**Linux:**

```bash
sudo apt-get remove tesseract-ocr poppler-utils
```

**macOS:**

```bash
brew uninstall tesseract poppler
```

**Windows:**

- Desinstalar desde Panel de Control
- O eliminar carpetas manualmente

---

## Soporte Adicional

- 📖 Lee **README_ADVANCED.md** para documentación completa
- 🐛 Reporta problemas en GitHub Issues
- 💬 Consulta ejemplos en **COMPARISON.md**
- 🎓 Revisa **IMPLEMENTATION_SUMMARY.md** para más info

---

**¡Instalación completada! Estás listo para procesar PDFs.** 🎉
