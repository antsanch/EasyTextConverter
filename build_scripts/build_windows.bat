@echo off
echo === Compilando Pandoc GUI para Windows (.exe standalone) ===

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

pip install -r requirements.txt

pyinstaller --name "pandoc-gui" ^
    --onefile ^
    --windowed ^
    --noconfirm ^
    --clean ^
    src\main.py

echo === Compilacion finalizada ===
echo El archivo ejecutable esta en: dist\pandoc-gui.exe
pause

