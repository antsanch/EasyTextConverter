"""
Main Application Window for Pandoc GUI.
Provides a clean, modern interface with a large Markdown text editor,
one-click export buttons on top, especially optimized for Scribus (ODT),
and an intelligent Markdown auto-formatter to fix glued headings and lists.
"""

import os
import sys
import platform
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QPlainTextEdit, QLabel, QFileDialog, QMessageBox, QFrame,
    QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QAction

from src.core.pandoc_manager import find_pandoc
from src.core.converter import convert_markdown, FORMAT_CONFIG
from src.core.formatter import auto_format_markdown, has_potential_formatting_defects
from src.ui.download_dialog import PandocDownloadDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pandoc GUI - Conversor Markdown para Scribus y Documentos")
        self.resize(980, 700)
        self.setMinimumSize(780, 500)

        self.pandoc_path = None
        self.pandoc_version = None
        self.last_save_dir = os.path.expanduser("~")

        self._init_ui()
        self._check_pandoc_status(prompt_download_if_missing=False)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 12)
        main_layout.setSpacing(10)

        # 1. TOP TOOLBAR WITH DIRECT SAVE BUTTONS
        top_bar = self._create_top_toolbar()
        main_layout.addWidget(top_bar)

        # 2. LARGE MARKDOWN TEXT EDITOR
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "Pega aquí tu texto en Markdown...\n\n"
            "Ejemplo:\n"
            "# Título Principal (se convierte en estilo Heading 1 para Scribus y LibreOffice)\n\n"
            "Este es un párrafo con texto en **negrita**, *cursiva* y un [enlace](https://...).\n\n"
            "## Subtítulo de Sección (Heading 2)\n\n"
            "- Elemento de lista 1\n"
            "- Elemento de lista 2\n\n"
            "> Cita en bloque estilizada.\n\n"
            "💡 Tip: Si tu texto viene de PDF o web con títulos pegados sin saltos de línea,\n"
            "haz clic arriba en '✨ Auto-formatear' antes de exportar a ODT."
        )

        # Configure font
        mono_font = QFont("Consolas" if platform.system() == "Windows" else "Monospace", 11)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(mono_font)
        self.editor.setTabStopDistance(self.editor.fontMetrics().horizontalAdvance(' ') * 4)
        self.editor.textChanged.connect(self._on_text_changed)

        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 12px;
                line-height: 1.5;
                selection-background-color: #bfdbfe;
                selection-color: #1e293b;
            }
            QPlainTextEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        main_layout.addWidget(self.editor, stretch=1)

        # 3. BOTTOM STATUS BAR
        status_bar = self._create_bottom_bar()
        main_layout.addWidget(status_bar)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, lambda: self._on_export_clicked("odt"))
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, self._on_auto_format_clicked)
        QShortcut(QKeySequence("Ctrl+N"), self, self._clear_text)

    def _create_top_toolbar(self) -> QWidget:
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # PROMINENT SCRIBUS / ODT BUTTON
        self.btn_odt = QPushButton("📥 Guardar ODT (Scribus)")
        self.btn_odt.setToolTip("Exportar a OpenDocument Text (.odt) optimizado para Scribus y LibreOffice (Ctrl+Shift+S)")
        self.btn_odt.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_odt.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 10px 18px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        self.btn_odt.clicked.connect(lambda: self._on_export_clicked("odt"))
        layout.addWidget(self.btn_odt)

        # SECONDARY FORMAT BUTTONS
        secondary_formats = [
            ("📄 DOCX", "docx", "Documento Word (.docx)"),
            ("🌐 HTML", "html", "Página Web (.html)"),
            ("📑 RTF", "rtf", "Texto enriquecido (.rtf)"),
            ("📖 EPUB", "epub", "Libro electrónico (.epub)"),
            ("📝 MD", "md", "Guardar Markdown original (.md)"),
        ]

        for label, fmt_key, tooltip in secondary_formats:
            btn = QPushButton(label)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f1f5f9;
                    color: #334155;
                    font-size: 12px;
                    font-weight: 500;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 9px 12px;
                }
                QPushButton:hover {
                    background-color: #e2e8f0;
                    color: #0f172a;
                    border-color: #94a3b8;
                }
                QPushButton:pressed {
                    background-color: #cbd5e1;
                }
            """)
            btn.clicked.connect(lambda checked=False, k=fmt_key: self._on_export_clicked(k))
            layout.addWidget(btn)

        # AUTO-FORMAT BUTTON
        btn_format = QPushButton("✨ Auto-formatear")
        btn_format.setToolTip("Reparar títulos, listas y estilos pegados sin saltos de línea (Ctrl+Shift+F)")
        btn_format.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_format.setStyleSheet("""
            QPushButton {
                background-color: #f0fdf4;
                color: #15803d;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #86efac;
                border-radius: 6px;
                padding: 9px 14px;
            }
            QPushButton:hover {
                background-color: #dcfce7;
                border-color: #4ade80;
            }
            QPushButton:pressed {
                background-color: #bbf7d0;
            }
        """)
        btn_format.clicked.connect(self._on_auto_format_clicked)
        layout.addWidget(btn_format)

        # Spacer to push utility buttons to the right
        layout.addStretch()

        # UTILITY BUTTONS
        btn_paste = QPushButton("📋 Pegar")
        btn_paste.setToolTip("Pegar contenido del portapapeles")
        btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_paste.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #475569;
                font-size: 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #f8fafc;
                border-color: #94a3b8;
            }
        """)
        btn_paste.clicked.connect(self._paste_clipboard)
        layout.addWidget(btn_paste)

        btn_clear = QPushButton("🗑️ Limpiar")
        btn_clear.setToolTip("Limpiar todo el texto del editor")
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #ef4444;
                font-size: 12px;
                border: 1px solid #fca5a5;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #fef2f2;
                border-color: #f87171;
            }
        """)
        btn_clear.clicked.connect(self._clear_text)
        layout.addWidget(btn_clear)

        return toolbar

    def _create_bottom_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        self.status_msg_label = QLabel("Listo para convertir.")
        self.status_msg_label.setStyleSheet("color: #475569; font-size: 12px;")
        layout.addWidget(self.status_msg_label, stretch=1)

        self.stats_label = QLabel("0 palabras | 0 caracteres")
        self.stats_label.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(self.stats_label)

        # Vertical divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("color: #cbd5e1;")
        layout.addWidget(divider)

        # Pandoc status badge & button
        self.pandoc_badge = QPushButton("Buscando Pandoc...")
        self.pandoc_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pandoc_badge.setStyleSheet("""
            QPushButton {
                background-color: #f8fafc;
                color: #0f172a;
                font-size: 11px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
        """)
        self.pandoc_badge.clicked.connect(self._on_pandoc_badge_clicked)
        layout.addWidget(self.pandoc_badge)

        return bar

    def _on_text_changed(self):
        text = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.stats_label.setText(f"{words:,} palabras | {chars:,} caracteres")

    def _on_auto_format_clicked(self):
        content = self.editor.toPlainText()
        if not content.strip():
            self._set_status("El editor está vacío. Pega primero tu texto.")
            return

        repaired, count = auto_format_markdown(content)
        if count > 0:
            self.editor.setPlainText(repaired)
            self._set_status(f"✨ ¡Markdown reparado con éxito! Se aplicaron {count} correcciones de títulos/listas/espaciado.")
        else:
            self._set_status("El texto ya tiene una estructura correcta de Markdown.")

    def _paste_clipboard(self):
        clipboard = QApplication.clipboard()
        cb_text = clipboard.text()
        if cb_text:
            self.editor.insertPlainText(cb_text)
            self._set_status("Texto pegado desde el portapapeles.")
        else:
            self._set_status("El portapapeles no contiene texto.")

    def _clear_text(self):
        if not self.editor.toPlainText().strip():
            return
        reply = QMessageBox.question(
            self,
            "Limpiar editor",
            "¿Deseas vaciar todo el contenido del editor?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.editor.clear()
            self._set_status("Editor vaciado.")

    def _check_pandoc_status(self, prompt_download_if_missing=False) -> bool:
        path, version = find_pandoc()
        if path and version:
            self.pandoc_path = path
            self.pandoc_version = version
            self.pandoc_badge.setText(f"✓ Pandoc v{version}")
            self.pandoc_badge.setStyleSheet("""
                QPushButton {
                    background-color: #ecfdf5;
                    color: #065f46;
                    font-size: 11px;
                    font-weight: 500;
                    border: 1px solid #a7f3d0;
                    border-radius: 4px;
                    padding: 4px 10px;
                }
                QPushButton:hover {
                    background-color: #d1fae5;
                }
            """)
            self.pandoc_badge.setToolTip(f"Ubicación: {path}\nHaz clic para actualizar.")
            return True
        else:
            self.pandoc_path = None
            self.pandoc_version = None
            self.pandoc_badge.setText("⚠️ Descargar Pandoc")
            self.pandoc_badge.setStyleSheet("""
                QPushButton {
                    background-color: #fff7ed;
                    color: #9a3412;
                    font-size: 11px;
                    font-weight: bold;
                    border: 1px solid #fed7aa;
                    border-radius: 4px;
                    padding: 4px 10px;
                }
                QPushButton:hover {
                    background-color: #ffedd5;
                }
            """)
            self.pandoc_badge.setToolTip("Pandoc no está instalado. Haz clic para descargarlo automáticamente.")

            if prompt_download_if_missing:
                return self._trigger_pandoc_download()
            return False

    def _on_pandoc_badge_clicked(self):
        if self.pandoc_path:
            reply = QMessageBox.question(
                self,
                "Pandoc ya está instalado",
                f"Se detectó Pandoc versión {self.pandoc_version} en:\n{self.pandoc_path}\n\n"
                "¿Deseas comprobar y descargar la versión más reciente desde GitHub?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._trigger_pandoc_download()
        else:
            self._trigger_pandoc_download()

    def _trigger_pandoc_download(self) -> bool:
        dlg = PandocDownloadDialog(self, auto_start=True)
        if dlg.exec():
            return self._check_pandoc_status(prompt_download_if_missing=False)
        return False

    def _set_status(self, message: str, is_error: bool = False):
        color = "#dc2626" if is_error else "#1e293b"
        self.status_msg_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: {'500' if is_error else 'normal'};")
        self.status_msg_label.setText(message)

    def _on_export_clicked(self, format_key: str):
        content = self.editor.toPlainText().strip()
        if not content:
            QMessageBox.warning(
                self,
                "Texto vacío",
                "El área de texto está vacía. Por favor pega o escribe tu contenido en Markdown antes de guardar."
            )
            return

        # Check for glued headings defect
        if format_key != "md" and has_potential_formatting_defects(content):
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle("Aviso de Estructura Markdown")
            box.setText(
                "Se detectaron títulos o encabezados pegados directamente al texto sin saltos de línea.\n\n"
                "Si se convierte así, Pandoc interpretará todo el párrafo como parte del título.\n\n"
                "¿Deseas auto-formatear y reparar la estructura automáticamente antes de guardar?"
            )
            btn_fix = box.addButton("Auto-formatear y Guardar", QMessageBox.ButtonRole.AcceptRole)
            btn_ignore = box.addButton("Guardar tal cual", QMessageBox.ButtonRole.ActionRole)
            box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            box.exec()

            if box.clickedButton() == btn_fix:
                content, count = auto_format_markdown(content)
                self.editor.setPlainText(content)
                self._set_status(f"✨ Se repararon {count} títulos antes de guardar.")
            elif box.clickedButton() != btn_ignore:
                return

        # Ensure Pandoc is available (not required for raw .md save)
        if format_key != "md":
            if not self.pandoc_path:
                ok = self._check_pandoc_status(prompt_download_if_missing=True)
                if not ok:
                    self._set_status("Operación cancelada: Pandoc es requerido para esta conversión.", is_error=True)
                    return

        fmt = FORMAT_CONFIG[format_key]
        ext = fmt["ext"]
        filter_str = f"{fmt['name']} (*{ext});;Todos los archivos (*.*)"

        default_filename = os.path.join(self.last_save_dir, f"documento{ext}")
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            f"Guardar como {fmt['name']}",
            default_filename,
            filter_str
        )

        if not output_file:
            return

        # Ensure correct extension
        if not output_file.lower().endswith(ext):
            output_file += ext

        self.last_save_dir = os.path.dirname(output_file)
        self._set_status(f"Convirtiendo a {fmt['name']}...")
        QApplication.processEvents()

        # Run conversion
        success, message = convert_markdown(
            markdown_text=content,
            target_format=format_key,
            output_path=output_file,
            pandoc_path=self.pandoc_path or ""
        )

        if success:
            self._set_status(f"¡Guardado correctamente en: {os.path.basename(output_file)}!")
            
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Information)
            box.setWindowTitle("Conversión Exitosa")
            
            scribus_hint = ""
            if format_key == "odt":
                scribus_hint = (
                    "\n\n📌 Para usarlo en Scribus o LibreOffice:\n"
                    "• LibreOffice: Ábrelo directamente y verás los estilos Heading 1, 2, 3 en la barra de estilos.\n"
                    "• Scribus: Crea un marco de texto, clic derecho → 'Obtener texto...', selecciona este .odt y marca 'importar estilos'."
                )
            
            box.setText(f"El archivo fue generado exitosamente:\n{output_file}{scribus_hint}")
            btn_open_file = box.addButton("Abrir archivo", QMessageBox.ButtonRole.ActionRole)
            btn_open_folder = box.addButton("Abrir carpeta", QMessageBox.ButtonRole.ActionRole)
            box.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
            box.exec()

            clicked = box.clickedButton()
            if clicked == btn_open_file:
                self._open_file(output_file)
            elif clicked == btn_open_folder:
                self._open_folder(os.path.dirname(output_file))
        else:
            self._set_status("Error al convertir.", is_error=True)
            QMessageBox.critical(self, "Error de Conversión", message)

    def _open_file(self, filepath: str):
        try:
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", filepath])
            else:
                subprocess.Popen(["xdg-open", filepath])
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"No se pudo abrir el archivo directamente: {e}")

    def _open_folder(self, folderpath: str):
        try:
            if platform.system() == "Windows":
                os.startfile(folderpath)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folderpath])
            else:
                subprocess.Popen(["xdg-open", folderpath])
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"No se pudo abrir la carpeta: {e}")
