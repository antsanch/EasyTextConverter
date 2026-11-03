#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "=== Compilando Pandoc GUI para Linux (Onefile) ==="

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

pyinstaller \
    --name "pandoc-gui" \
    --onefile \
    --windowed \
    --noconfirm \
    --clean \
    src/main.py

echo "=== Compilación completada con éxito ==="
echo "El ejecutable se encuentra en: dist/pandoc-gui"
