"""
Download dialog for downloading and updating the Pandoc binary with live progress.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from src.core.pandoc_manager import download_and_extract_pandoc


class DownloadThread(QThread):
    progress_signal = pyqtSignal(float, str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def run(self):
        try:
            def callback(percent: float, message: str):
                self.progress_signal.emit(percent, message)

            installed_path = download_and_extract_pandoc(progress_callback=callback)
            self.finished_signal.emit(installed_path)
        except Exception as e:
            self.error_signal.emit(str(e))


class PandocDownloadDialog(QDialog):
    def __init__(self, parent=None, auto_start=True):
        super().__init__(parent)
        self.setWindowTitle("Descarga de Pandoc")
        self.setFixedSize(480, 200)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.download_thread = None
        self.installed_path = None

        self._init_ui()

        if auto_start:
            self.start_download()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        self.title_label = QLabel("Descargando la versión más reciente de Pandoc...")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b;")
        layout.addWidget(self.title_label)

        self.status_label = QLabel("Preparando conexión con GitHub...")
        self.status_label.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                text-align: center;
                height: 22px;
                background-color: #f1f5f9;
                font-size: 11px;
                font-weight: 500;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                color: #334155;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_button)

        layout.addLayout(btn_layout)

    def start_download(self):
        self.download_thread = DownloadThread()
        self.download_thread.progress_signal.connect(self._on_progress)
        self.download_thread.finished_signal.connect(self._on_finished)
        self.download_thread.error_signal.connect(self._on_error)
        self.download_thread.start()

    def _on_progress(self, percent: float, message: str):
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(message)

    def _on_finished(self, installed_path: str):
        self.installed_path = installed_path
        self.progress_bar.setValue(100)
        self.status_label.setText("¡Instalación completada!")
        self.accept()

    def _on_error(self, error_message: str):
        QMessageBox.critical(
            self,
            "Error al descargar Pandoc",
            f"Ocurrió un error al intentar descargar Pandoc:\n\n{error_message}\n\n"
            "Verifica tu conexión a internet o intenta nuevamente."
        )
        self.reject()

    def closeEvent(self, event):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
        event.accept()

