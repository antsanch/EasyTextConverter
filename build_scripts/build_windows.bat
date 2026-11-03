@echo off
echo === Compilando EasyTextConverter para Windows (.exe standalone) ===

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

pip install -r requirements.txt

pyinstaller --name "EasyTextConverter" ^
    --onefile ^
    --windowed ^
    --noconfirm ^
    --clean ^
    src\main.py

echo === Compilacion finalizada ===
echo El archivo ejecutable esta en: dist\EasyTextConverter.exe
pause
