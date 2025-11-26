"""
Simple GUI example using tkinter.
Shows how to use the core logic with a graphical interface.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading

from models.pdf_processor import PDFInput, ProcessingOptions, PDFMergerCore


class PDFMergerGUI:
    """Simple GUI for PDF Merger."""

    def __init__(self, root):
        self.root = root
        self.root.title("PDF Merger Tool")
        self.root.geometry("700x800")

        self.pdf_files = []
        self.create_widgets()

    def create_widgets(self):
        """Create GUI widgets."""
        # Title
        title = tk.Label(
            self.root, text="PDF Merger & Processor", font=("Arial", 16, "bold")
        )
        title.pack(pady=10)

        # File selection frame
        file_frame = tk.LabelFrame(self.root, text="Archivos PDF", padx=10, pady=10)
        file_frame.pack(padx=10, pady=5, fill="both", expand=True)

        # Listbox for files
        self.file_listbox = tk.Listbox(file_frame, height=6)
        self.file_listbox.pack(fill="both", expand=True, pady=5)

        # Buttons for file management
        btn_frame = tk.Frame(file_frame)
        btn_frame.pack()

        tk.Button(btn_frame, text="Añadir PDFs", command=self.add_files).pack(
            side="left", padx=5
        )
        tk.Button(btn_frame, text="Quitar Seleccionado", command=self.remove_file).pack(
            side="left", padx=5
        )
        tk.Button(btn_frame, text="Limpiar Todo", command=self.clear_files).pack(
            side="left", padx=5
        )

        # Interleave option
        self.interleave_var = tk.BooleanVar()
        tk.Checkbutton(
            file_frame,
            text="Intercalar páginas (útil para escaneos doble cara)",
            variable=self.interleave_var,
        ).pack(pady=5)

        # Processing options
        options_frame = tk.LabelFrame(
            self.root, text="Opciones de Procesamiento", padx=10, pady=10
        )
        options_frame.pack(padx=10, pady=5, fill="both")

        # Create two columns
        left_col = tk.Frame(options_frame)
        left_col.pack(side="left", fill="both", expand=True)

        right_col = tk.Frame(options_frame)
        right_col.pack(side="left", fill="both", expand=True)

        # OCR options
        self.ocr_var = tk.BooleanVar()
        tk.Checkbutton(
            left_col, text="OCR (hacer buscable)", variable=self.ocr_var
        ).pack(anchor="w")

        ocr_lang_frame = tk.Frame(left_col)
        ocr_lang_frame.pack(anchor="w", padx=20)
        tk.Label(ocr_lang_frame, text="Idioma:").pack(side="left")
        self.ocr_lang = tk.StringVar(value="spa")
        tk.Entry(ocr_lang_frame, textvariable=self.ocr_lang, width=10).pack(
            side="left", padx=5
        )

        # Image processing
        self.enhance_var = tk.BooleanVar()
        tk.Checkbutton(
            left_col, text="Mejorar contraste/brillo", variable=self.enhance_var
        ).pack(anchor="w")

        self.denoise_var = tk.BooleanVar()
        tk.Checkbutton(left_col, text="Eliminar ruido", variable=self.denoise_var).pack(
            anchor="w"
        )

        self.binarize_var = tk.BooleanVar()
        tk.Checkbutton(
            left_col, text="Blanco y negro", variable=self.binarize_var
        ).pack(anchor="w")

        self.sharpen_var = tk.BooleanVar()
        tk.Checkbutton(
            left_col, text="Mejorar nitidez", variable=self.sharpen_var
        ).pack(anchor="w")

        self.autocrop_var = tk.BooleanVar()
        tk.Checkbutton(
            left_col, text="Recortar bordes", variable=self.autocrop_var
        ).pack(anchor="w")

        # Other options
        self.auto_deskew_var = tk.BooleanVar()
        tk.Checkbutton(
            right_col, text="Auto-enderezar", variable=self.auto_deskew_var
        ).pack(anchor="w")

        self.remove_blank_var = tk.BooleanVar()
        tk.Checkbutton(
            right_col, text="Eliminar páginas en blanco", variable=self.remove_blank_var
        ).pack(anchor="w")

        self.optimize_var = tk.BooleanVar()
        tk.Checkbutton(
            right_col, text="Optimizar tamaño", variable=self.optimize_var
        ).pack(anchor="w")

        self.page_numbers_var = tk.BooleanVar()
        tk.Checkbutton(
            right_col, text="Añadir números de página", variable=self.page_numbers_var
        ).pack(anchor="w")

        # Watermark
        watermark_frame = tk.Frame(right_col)
        watermark_frame.pack(anchor="w", pady=5)
        tk.Label(watermark_frame, text="Marca de agua:").pack(side="left")
        self.watermark_var = tk.StringVar()
        tk.Entry(watermark_frame, textvariable=self.watermark_var, width=15).pack(
            side="left", padx=5
        )

        # Metadata
        metadata_frame = tk.LabelFrame(self.root, text="Metadata", padx=10, pady=10)
        metadata_frame.pack(padx=10, pady=5, fill="both")

        # Title
        title_frame = tk.Frame(metadata_frame)
        title_frame.pack(fill="x", pady=2)
        tk.Label(title_frame, text="Título:", width=10, anchor="w").pack(side="left")
        self.title_var = tk.StringVar()
        tk.Entry(title_frame, textvariable=self.title_var).pack(
            side="left", fill="x", expand=True
        )

        # Author
        author_frame = tk.Frame(metadata_frame)
        author_frame.pack(fill="x", pady=2)
        tk.Label(author_frame, text="Autor:", width=10, anchor="w").pack(side="left")
        self.author_var = tk.StringVar()
        tk.Entry(author_frame, textvariable=self.author_var).pack(
            side="left", fill="x", expand=True
        )

        # Profile selection
        profile_frame = tk.LabelFrame(self.root, text="Perfil Rápido", padx=10, pady=10)
        profile_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(profile_frame, text="Cargar perfil predefinido:").pack(
            side="left", padx=5
        )
        self.profile_var = tk.StringVar()
        profile_combo = ttk.Combobox(
            profile_frame,
            textvariable=self.profile_var,
            values=["", "document", "photo", "ebook", "archive", "share", "fast"],
            state="readonly",
        )
        profile_combo.pack(side="left", padx=5)
        tk.Button(profile_frame, text="Aplicar", command=self.apply_profile).pack(
            side="left", padx=5
        )

        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(padx=10, pady=5, fill="x")

        # Status label
        self.status_label = tk.Label(self.root, text="Listo", fg="green")
        self.status_label.pack(pady=5)

        # Process button
        tk.Button(
            self.root,
            text="PROCESAR PDFs",
            command=self.process_pdfs,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
        ).pack(padx=10, pady=10, fill="x")

    def add_files(self):
        """Add PDF files to the list."""
        files = filedialog.askopenfilenames(
            title="Seleccionar PDFs",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )

        for file in files:
            if file not in self.pdf_files:
                self.pdf_files.append(file)
                self.file_listbox.insert(tk.END, Path(file).name)

    def remove_file(self):
        """Remove selected file."""
        selection = self.file_listbox.curselection()
        if selection:
            idx = selection[0]
            self.file_listbox.delete(idx)
            del self.pdf_files[idx]

    def clear_files(self):
        """Clear all files."""
        self.file_listbox.delete(0, tk.END)
        self.pdf_files.clear()

    def apply_profile(self):
        """Apply a predefined profile."""
        profile_name = self.profile_var.get()
        if not profile_name:
            return

        # Load profile
        from cli import load_profile

        profile = load_profile(profile_name)

        if not profile:
            messagebox.showerror("Error", f"Perfil '{profile_name}' no encontrado")
            return

        # Apply profile settings
        self.ocr_var.set(profile.get("ocr", False))
        self.enhance_var.set(profile.get("enhance", False))
        self.denoise_var.set(profile.get("denoise", False))
        self.binarize_var.set(profile.get("binarize", False))
        self.sharpen_var.set(profile.get("sharpen", False))
        self.autocrop_var.set(profile.get("autocrop", False))
        self.auto_deskew_var.set(profile.get("auto_deskew", False))
        self.remove_blank_var.set(profile.get("remove_blank", False))
        self.optimize_var.set(profile.get("optimize", False))

        messagebox.showinfo("Éxito", f"Perfil '{profile_name}' aplicado")

    def process_pdfs(self):
        """Process PDFs in a separate thread."""
        if not self.pdf_files:
            messagebox.showwarning("Advertencia", "No hay archivos PDF seleccionados")
            return

        # Ask for output file
        output_file = filedialog.asksaveasfilename(
            title="Guardar PDF resultante",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )

        if not output_file:
            return

        # Start processing in thread
        thread = threading.Thread(
            target=self._process_thread, args=(output_file,), daemon=True
        )
        thread.start()

    def _process_thread(self, output_file):
        """Process PDFs in background thread."""
        try:
            # Update UI
            self.root.after(0, self._update_status, "Procesando...", "orange")
            self.root.after(0, self.progress.start)

            # Create PDF inputs
            pdf_inputs = [PDFInput(path=pdf) for pdf in self.pdf_files]

            # Create processing options
            options = ProcessingOptions(
                ocr=self.ocr_var.get(),
                ocr_lang=self.ocr_lang.get(),
                enhance=self.enhance_var.get(),
                denoise=self.denoise_var.get(),
                binarize=self.binarize_var.get(),
                sharpen=self.sharpen_var.get(),
                autocrop=self.autocrop_var.get(),
                auto_deskew=self.auto_deskew_var.get(),
                remove_blank=self.remove_blank_var.get(),
                optimize=self.optimize_var.get(),
                page_numbers=self.page_numbers_var.get(),
                watermark=(
                    self.watermark_var.get() if self.watermark_var.get() else None
                ),
                title=self.title_var.get() if self.title_var.get() else None,
                author=self.author_var.get() if self.author_var.get() else None,
                verbose=False,
            )

            # Process
            processor = PDFMergerCore(options)
            success = processor.merge_and_process(
                pdf_inputs, output_file, interleave=self.interleave_var.get()
            )

            # Update UI
            self.root.after(0, self.progress.stop)

            if success:
                self.root.after(0, self._update_status, "✓ Completado", "green")
                self.root.after(
                    0, messagebox.showinfo, "Éxito", f"PDF generado:\n{output_file}"
                )
            else:
                self.root.after(0, self._update_status, "✗ Error", "red")
                self.root.after(
                    0, messagebox.showerror, "Error", "Error al procesar PDFs"
                )

        except Exception as e:
            self.root.after(0, self.progress.stop)
            self.root.after(0, self._update_status, "✗ Error", "red")
            self.root.after(0, messagebox.showerror, "Error", str(e))

    def _update_status(self, text, color):
        """Update status label."""
        self.status_label.config(text=text, fg=color)


def main():
    """Run GUI application."""
    root = tk.Tk()
    PDFMergerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
