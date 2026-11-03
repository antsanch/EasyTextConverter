"""
Main Application Window for EasyTextConverter.
Provides a clean, modern interface with a full top menu bar (File, Edit, Pandoc, Help),
a large Markdown text editor, one-click export buttons on top for Scribus (ODT),
and disk file management (Open, Save, Close, Save As).
"""

import os
import sys
import platform
import subprocess
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QPlainTextEdit, QLabel, QFileDialog, QMessageBox, QFrame,
    QApplication, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QAction, QCloseEvent

from src.core.pandoc_manager import find_pandoc, get_app_data_dir
from src.core.converter import convert_markdown, FORMAT_CONFIG
from src.core.formatter import replace_escaped_newlines, has_escaped_newlines
from src.ui.download_dialog import PandocDownloadDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1000, 720)
        self.setMinimumSize(800, 520)

        self.pandoc_path = None
        self.pandoc_version = None
        self.current_file_path: Optional[str] = None
        self.is_modified = False
        self.last_dir = os.path.expanduser("~")

        self._init_menu_bar()
        self._init_ui()
        self._update_window_title()
        self._check_pandoc_status(prompt_download_if_missing=False)

    def _init_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                font-size: 13px;
                color: #334155;
                padding: 2px 6px;
            }
            QMenuBar::item {
                padding: 4px 10px;
                background: transparent;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #e2e8f0;
                color: #0f172a;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px;
                font-size: 12px;
                color: #1e293b;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #eff6ff;
                color: #1d4ed8;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e2e8f0;
                margin: 4px 6px;
            }
        """)

        # ------------------ ARCHIVO MENU ------------------
        file_menu = menubar.addMenu("&Archivo")

        new_action = QAction("&Nuevo", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_file_new)
        file_menu.addAction(new_action)

        open_action = QAction("&Abrir archivo...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_file_open)
        file_menu.addAction(open_action)

        save_action = QAction("&Guardar", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_file_save)
        file_menu.addAction(save_action)

        save_as_action = QAction("Guardar &como...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._on_file_save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Export submenu
        export_menu = QMenu("&Exportar con Pandoc", self)
        
        exp_odt = QAction("ODT (Scribus / LibreOffice)...", self)
        exp_odt.setShortcut("Ctrl+Shift+E")
        exp_odt.triggered.connect(lambda: self._on_export_clicked("odt"))
        export_menu.addAction(exp_odt)

        exp_docx = QAction("DOCX (Microsoft Word)...", self)
        exp_docx.triggered.connect(lambda: self._on_export_clicked("docx"))
        export_menu.addAction(exp_docx)

        exp_html = QAction("HTML5 (Página Web)...", self)
        exp_html.triggered.connect(lambda: self._on_export_clicked("html"))
        export_menu.addAction(exp_html)

        exp_rtf = QAction("RTF (Texto enriquecido)...", self)
        exp_rtf.triggered.connect(lambda: self._on_export_clicked("rtf"))
        export_menu.addAction(exp_rtf)

        exp_epub = QAction("EPUB (Libro digital)...", self)
        exp_epub.triggered.connect(lambda: self._on_export_clicked("epub"))
        export_menu.addAction(exp_epub)

        file_menu.addMenu(export_menu)

        file_menu.addSeparator()

        close_file_action = QAction("&Cerrar archivo", self)
        close_file_action.setShortcut("Ctrl+W")
        close_file_action.triggered.connect(self._on_file_close)
        file_menu.addAction(close_file_action)

        exit_action = QAction("&Salir", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ------------------ EDITAR MENU ------------------
        edit_menu = menubar.addMenu("&Editar")

        undo_action = QAction("&Deshacer", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(lambda: self.editor.undo())
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Rehacer", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(lambda: self.editor.redo())
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cor&tar", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(lambda: self.editor.cut())
        edit_menu.addAction(cut_action)

        copy_action = QAction("&Copiar", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(lambda: self.editor.copy())
        edit_menu.addAction(copy_action)

        paste_action = QAction("&Pegar", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self._paste_clipboard)
        edit_menu.addAction(paste_action)

        select_all_action = QAction("&Seleccionar todo", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(lambda: self.editor.selectAll())
        edit_menu.addAction(select_all_action)

        edit_menu.addSeparator()

        rep_nl_action = QAction("Reemplazar '\\n' por saltos reales", self)
        rep_nl_action.setShortcut("Ctrl+Shift+R")
        rep_nl_action.triggered.connect(self._on_replace_newlines_clicked)
        edit_menu.addAction(rep_nl_action)

        clear_action = QAction("&Vaciar editor", self)
        clear_action.triggered.connect(self._clear_text)
        edit_menu.addAction(clear_action)

        # ------------------ PANDOC MENU ------------------
        pandoc_menu = menubar.addMenu("&Pandoc")

        check_pandoc_action = QAction("&Comprobar / Actualizar versión de Pandoc...", self)
        check_pandoc_action.triggered.connect(self._on_pandoc_badge_clicked)
        pandoc_menu.addAction(check_pandoc_action)

        open_pandoc_dir_action = QAction("Abrir carpeta de Pandoc en el disco", self)
        open_pandoc_dir_action.triggered.connect(self._open_pandoc_folder)
        pandoc_menu.addAction(open_pandoc_dir_action)

        # ------------------ AYUDA MENU ------------------
        help_menu = menubar.addMenu("A&yuda")

        scribus_guide_action = QAction("Guía de importación en &Scribus", self)
        scribus_guide_action.triggered.connect(self._show_scribus_help)
        help_menu.addAction(scribus_guide_action)

        about_action = QAction("&Acerca de EasyTextConverter", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # 1. TOP TOOLBAR WITH DIRECT SAVE BUTTONS
        top_bar = self._create_top_toolbar()
        main_layout.addWidget(top_bar)

        # 2. LARGE MARKDOWN TEXT EDITOR
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "Pega o abre aquí tu texto en Markdown...\n\n"
            "Ejemplo:\n"
            "### 2. Lectura Explorativa: Topografía y Rastreo\n\n"
            "La lectura explorativa es una aproximación superficial y rápida...\n\n"
            "#### A) Barrido Panorámico (Skimming)\n"
            "Consiste en examinar el texto de forma global:\n"
            "* ¿Cuál es el tema general del texto?\n"
            "* ¿Qué tipo de texto es?\n\n"
            "1. Leer el título y los subtítulos con atención.\n"
            "2. Leer la primera oración completa del primer párrafo.\n\n"
            "Haz clic arriba en '📥 Guardar ODT (Scribus)' para exportar con estilos listos para maquetar."
        )

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

    def _create_top_toolbar(self) -> QWidget:
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # PROMINENT SCRIBUS / ODT BUTTON
        self.btn_odt = QPushButton("📥 Guardar ODT (Scribus)")
        self.btn_odt.setToolTip("Exportar a OpenDocument Text (.odt) para Scribus y LibreOffice (Ctrl+Shift+E)")
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

        # REPLACE \n BUTTON
        self.btn_replace_nl = QPushButton("↵ Reemplazar \\n")
        self.btn_replace_nl.setToolTip("Convierte secuencias literales '\\n' en saltos de línea reales (Ctrl+Shift+R)")
        self.btn_replace_nl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_replace_nl.setStyleSheet("""
            QPushButton {
                background-color: #f0fdf4;
                color: #15803d;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #86efac;
                border-radius: 6px;
                padding: 9px 13px;
            }
            QPushButton:hover {
                background-color: #dcfce7;
                border-color: #4ade80;
            }
            QPushButton:pressed {
                background-color: #bbf7d0;
            }
        """)
        self.btn_replace_nl.clicked.connect(self._on_replace_newlines_clicked)
        layout.addWidget(self.btn_replace_nl)

        # Spacer
        layout.addStretch()

        # UTILITY BUTTONS
        btn_open = QPushButton("📂 Abrir")
        btn_open.setToolTip("Abrir archivo Markdown desde el disco (Ctrl+O)")
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #334155;
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
        btn_open.clicked.connect(self._on_file_open)
        layout.addWidget(btn_open)

        btn_paste = QPushButton("📋 Pegar")
        btn_paste.setToolTip("Pegar contenido del portapapeles (Ctrl+V)")
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

    def _update_window_title(self):
        filename = os.path.basename(self.current_file_path) if self.current_file_path else "Sin título"
        modified_mark = "*" if self.is_modified else ""
        self.setWindowTitle(f"{filename}{modified_mark} - EasyTextConverter")

    def _on_text_changed(self):
        text = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.stats_label.setText(f"{words:,} palabras | {chars:,} caracteres")

        if not self.is_modified:
            self.is_modified = True
            self._update_window_title()

    # ------------------ FILE OPERATIONS ------------------

    def _check_unsaved_changes(self) -> bool:
        """Returns True if it is safe to proceed (saved, discarded, or not modified)."""
        if not self.is_modified or not self.editor.toPlainText().strip():
            return True

        filename = os.path.basename(self.current_file_path) if self.current_file_path else "el documento actual"
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Cambios no guardados")
        box.setText(f"¿Deseas guardar los cambios realizados en {filename}?")
        btn_save = box.addButton("Guardar", QMessageBox.ButtonRole.AcceptRole)
        btn_discard = box.addButton("Descartar", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked == btn_save:
            return self._on_file_save()
        elif clicked == btn_discard:
            return True
        else:
            return False

    def _on_file_new(self):
        if not self._check_unsaved_changes():
            return
        self.editor.clear()
        self.current_file_path = None
        self.is_modified = False
        self._update_window_title()
        self._set_status("Nuevo documento en blanco creado.")

    def _on_file_open(self):
        if not self._check_unsaved_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir archivo de texto o Markdown",
            self.last_dir,
            "Archivos Markdown y Texto (*.md *.markdown *.txt *.text);;Todos los archivos (*.*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as e:
                QMessageBox.critical(self, "Error al leer archivo", f"No se pudo leer el archivo:\n{e}")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error al leer archivo", f"No se pudo leer el archivo:\n{e}")
            return

        self.editor.setPlainText(content)
        self.current_file_path = file_path
        self.is_modified = False
        self.last_dir = os.path.dirname(file_path)
        self._update_window_title()
        self._set_status(f"Archivo abierto: {os.path.basename(file_path)}")

    def _on_file_save(self) -> bool:
        if self.current_file_path:
            return self._save_to_path(self.current_file_path)
        else:
            return self._on_file_save_as()

    def _on_file_save_as(self) -> bool:
        default_name = self.current_file_path or os.path.join(self.last_dir, "documento.md")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo Markdown",
            default_name,
            "Archivo Markdown (*.md);;Archivo de Texto (*.txt);;Todos los archivos (*.*)"
        )
        if not file_path:
            return False

        if not file_path.lower().endswith((".md", ".markdown", ".txt")):
            file_path += ".md"

        return self._save_to_path(file_path)

    def _save_to_path(self, file_path: str) -> bool:
        try:
            content = self.editor.toPlainText()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.current_file_path = file_path
            self.is_modified = False
            self.last_dir = os.path.dirname(file_path)
            self._update_window_title()
            self._set_status(f"Guardado en: {file_path}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar el archivo:\n{e}")
            return False

    def _on_file_close(self):
        if not self._check_unsaved_changes():
            return
        self.editor.clear()
        self.current_file_path = None
        self.is_modified = False
        self._update_window_title()
        self._set_status("Archivo cerrado.")

    def closeEvent(self, event: QCloseEvent):
        if self._check_unsaved_changes():
            event.accept()
        else:
            event.ignore()

    # ------------------ UTILITY & CONVERSION ------------------

    def _on_replace_newlines_clicked(self):
        content = self.editor.toPlainText()
        if not content.strip():
            self._set_status("El editor está vacío.")
            return

        repaired, count = replace_escaped_newlines(content)
        if count > 0:
            self.editor.setPlainText(repaired)
            self._set_status(f"✓ ¡Listo! Se reemplazaron {count} '\\n' por retornos de carro reales.")
        else:
            self._set_status("No se encontraron secuencias '\\n' en el texto.")

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

    def _open_pandoc_folder(self):
        data_dir = get_app_data_dir()
        self._open_folder(data_dir)

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

        # Check for literal '\n' sequences in text
        if has_escaped_newlines(content):
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Question)
            box.setWindowTitle("Secuencias \\n detectadas")
            box.setText(
                "Se detectaron secuencias literales '\\n' en el texto.\n\n"
                "¿Deseas reemplazarlas por retornos de carro reales antes de guardar?"
            )
            btn_replace = box.addButton("Reemplazar \\n y Guardar", QMessageBox.ButtonRole.AcceptRole)
            btn_keep = box.addButton("Guardar tal cual", QMessageBox.ButtonRole.ActionRole)
            box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            box.exec()

            if box.clickedButton() == btn_replace:
                content, count = replace_escaped_newlines(content)
                self.editor.setPlainText(content)
                self._set_status(f"✓ Se reemplazaron {count} '\\n' por retornos de carro.")
            elif box.clickedButton() != btn_keep:
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

        base_name = "documento"
        if self.current_file_path:
            base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]

        default_filename = os.path.join(self.last_dir, f"{base_name}{ext}")
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            f"Guardar como {fmt['name']}",
            default_filename,
            filter_str
        )

        if not output_file:
            return

        if not output_file.lower().endswith(ext):
            output_file += ext

        self.last_dir = os.path.dirname(output_file)
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

    def _show_scribus_help(self):
        QMessageBox.information(
            self,
            "Guía de Importación en Scribus",
            "Cómo importar tu documento ODT en Scribus conservando todos los estilos:\n\n"
            "1. En Scribus, inserta un 'Marco de Texto' en tu página.\n"
            "2. Haz clic derecho sobre el marco y selecciona 'Obtener texto...' (Get Text...).\n"
            "3. Selecciona tu archivo .odt generado.\n"
            "4. En el diálogo del importador de ODT, asegúrate de marcar 'Importar estilos'.\n\n"
            "¡Listo! Los títulos H1, H2, H3, viñetas, listas numeradas y negritas se mapearán a los Estilos de Párrafo de Scribus (F3)."
        )

    def _show_about_dialog(self):
        ver = self.pandoc_version or "no instalado"
        QMessageBox.about(
            self,
            "Acerca de EasyTextConverter",
            "<h3>EasyTextConverter</h3>"
            "<p>Conversor visual de Markdown a ODT (Scribus / LibreOffice), DOCX, HTML5, RTF y EPUB.</p>"
            f"<p><b>Motor Pandoc:</b> v{ver}</p>"
            "<p>Multiplataforma para Linux y Windows.</p>"
        )

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
