#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "=== Compilando EasyTextConverter para Linux (Onefile) ==="

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

pyinstaller \
    --name "EasyTextConverter" \
    --onefile \
    --windowed \
    --noconfirm \
    --clean \
    src/main.py

echo "=== Compilación completada con éxito ==="
echo "El ejecutable se encuentra en: dist/EasyTextConverter"
