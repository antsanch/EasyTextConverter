"""
Handles conversion of Markdown text to various target formats using Pandoc.
"""

import os
import subprocess
import platform
from typing import Dict, Any, Optional, Tuple

# Supported formats and their metadata
FORMAT_CONFIG: Dict[str, Dict[str, Any]] = {
    "odt": {
        "name": "ODT (Scribus / LibreOffice)",
        "ext": ".odt",
        "description": "Formato recomendado para Scribus (conserva estilos y títulos)",
        "pandoc_args": ["-f", "markdown", "-t", "odt", "--standalone"],
    },
    "docx": {
        "name": "DOCX (Word)",
        "ext": ".docx",
        "description": "Documento editable de Microsoft Word",
        "pandoc_args": ["-f", "markdown", "-t", "docx", "--standalone"],
    },
    "html": {
        "name": "HTML5",
        "ext": ".html",
        "description": "Página web con estilos básicos integrados",
        "pandoc_args": ["-f", "markdown", "-t", "html5", "--standalone"],
    },
    "rtf": {
        "name": "RTF (Rich Text)",
        "ext": ".rtf",
        "description": "Formato de texto enriquecido estándar",
        "pandoc_args": ["-f", "markdown", "-t", "rtf", "--standalone"],
    },
    "epub": {
        "name": "EPUB",
        "ext": ".epub",
        "description": "Libro electrónico digital",
        "pandoc_args": ["-f", "markdown", "-t", "epub", "--standalone"],
    },
    "md": {
        "name": "Markdown (.md)",
        "ext": ".md",
        "description": "Guardar archivo Markdown tal cual",
        "pandoc_args": [],
    },
}

def convert_markdown(
    markdown_text: str,
    target_format: str,
    output_path: str,
    pandoc_path: str,
    extra_args: Optional[list] = None
) -> Tuple[bool, str]:
    """
    Converts markdown_text to target_format and saves to output_path.
    Returns (success: bool, message: str).
    """
    if not markdown_text.strip():
        return False, "El texto Markdown está vacío. Por favor pega o escribe algún contenido."

    fmt_info = FORMAT_CONFIG.get(target_format.lower())
    if not fmt_info:
        return False, f"Formato no soportado: {target_format}"

    # Special case: direct markdown save
    if target_format.lower() == "md":
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)
            return True, f"Archivo Markdown guardado con éxito en {output_path}"
        except Exception as e:
            return False, f"Error al guardar archivo Markdown: {str(e)}"

    if not pandoc_path or not os.path.exists(pandoc_path):
        return False, "No se encontró el ejecutable de Pandoc. Por favor descárgalo primero."

    # Build command
    cmd = [pandoc_path] + fmt_info["pandoc_args"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.extend(["-o", output_path])

    # Windows: hide cmd window
    startupinfo = None
    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            startupinfo=startupinfo
        )
        stdout, stderr = process.communicate(input=markdown_text)

        if process.returncode != 0:
            err_msg = stderr.strip() if stderr else "Error desconocido durante la conversión."
            return False, f"Pandoc error (código {process.returncode}):\n{err_msg}"

        if not os.path.exists(output_path):
            return False, "La conversión finalizó pero el archivo de salida no fue creado."

        size_kb = os.path.getsize(output_path) / 1024
        return True, f"¡Convertido con éxito a {fmt_info['name']}! ({size_kb:.1f} KB)\nGuardado en: {output_path}"

    except Exception as e:
        return False, f"Excepción al ejecutar Pandoc: {str(e)}"

