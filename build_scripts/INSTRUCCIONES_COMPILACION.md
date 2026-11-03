# Guía de Compilación de Ejecutables (Linux y Windows)

Este documento detalla los pasos para generar los binarios independientes (*standalone*) de **EasyTextConverter** tanto para **Linux** como para **Windows**. 

Ambos ejecutables son completamente autónomos: incluyen todas las dependencias necesarias de Python y PyQt6, por lo que el usuario final **no necesita tener Python instalado**.

---

## 🐧 1. Compilación para Linux (Binario Nativo)

### Requisitos
- Linux (Ubuntu, Debian, Fedora, Arch, etc.).
- Python 3.10 o superior.

### Pasos:
1. Abre una terminal y sitúate en la raíz del proyecto:
   ```bash
   cd EasyTextConverter
   ```

2. Ejecuta el script de compilación:
   ```bash
   ./build_scripts/build_linux.sh
   ```
   *(Este script activa el entorno virtual `.venv` si existe, instala dependencias y ejecuta PyInstaller con el flag `--onefile`).*

3. **Resultado:**
   El ejecutable autónomo se creará en:
   ```text
   dist/EasyTextConverter
   ```

4. **Para ejecutarlo:**
   ```bash
   ./dist/EasyTextConverter
   ```

---

## 🪟 2. Compilación para Windows (`.exe` Nativo)

> **Nota técnica:** PyInstaller requiere ejecutarse en el sistema operativo destino para empaquetar las librerías dinámicas (`.dll`) y el runtime de C++ de Windows.

### Requisitos en la PC con Windows
- Windows 10 u 11 (64-bit).
- [Python 3.10 o superior para Windows](https://www.python.org/downloads/) (asegúrate de marcar la casilla *"Add python.exe to PATH"* durante la instalación).

### Método A: Doble Clic (Recomendado)
1. Copia o descarga la carpeta `EasyTextConverter` en tu máquina con Windows.
2. Entra a la carpeta `build_scripts` y haz doble clic sobre:
   ```text
   build_windows.bat
   ```
3. La ventana de comandos instalará las dependencias y compilará automáticamente el archivo.

### Método B: Desde la Consola de Windows (CMD o PowerShell)
1. Abre CMD o PowerShell en la raíz del proyecto:
   ```cmd
   cd C:\ruta\a\EasyTextConverter
   ```
2. Instala los requerimientos:
   ```cmd
   pip install -r requirements.txt
   ```
3. Ejecuta PyInstaller:
   ```cmd
   pyinstaller --name "EasyTextConverter" --onefile --windowed --noconfirm --clean src\main.py
   ```

4. **Resultado:**
   El ejecutable standalone se creará en:
   ```text
   dist\EasyTextConverter.exe
   ```
   *(Puedes mover este archivo `.exe` a cualquier otra computadora con Windows y funcionará con doble clic).*

---

## ☁️ 3. Compilación Automática en la Nube con GitHub Actions (Sin necesitar Windows)

Si estás trabajando en Linux y no tienes una máquina con Windows a mano, el proyecto ya cuenta con un flujo de trabajo automatizado en `.github/workflows/build.yml`.

### Pasos:
1. Crea un repositorio en tu cuenta de GitHub (puede ser público o privado).
2. Conecta y sube tu proyecto desde tu terminal Linux:
   ```bash
   git remote add origin https://github.com/TU-USUARIO/TU-REPOSITORIO.git
   git branch -M main
   git push -u origin main
   ```
3. En GitHub, ve a la pestaña **Actions**:
   - Verás el flujo **"Build Executables (Linux & Windows)"** ejecutándose en paralelo sobre dos máquinas virtuales reales (Ubuntu y Windows Server).
   - Al cabo de ~2 minutos, podrás descargar directamente los artefactos:
     - `EasyTextConverter-windows-x86_64.exe`
     - `EasyTextConverter-linux-x86_64`

### Para generar una Release con descarga pública:
Si creas una etiqueta (*tag*) en git:
```bash
git tag v1.0.0
git push origin v1.0.0
```
GitHub creará automáticamente una página de **Release** en tu repositorio con los dos ejecutables listos para que cualquier persona los descargue.

---

## 🛠️ Preguntas Frecuentes y Consejos

### ¿El ejecutable incluye Pandoc?
El ejecutable no infla su tamaño con Pandoc de fábrica; en su primer arranque, **la aplicación detecta si Pandoc existe y lo descarga automáticamente desde los releases oficiales de GitHub**, almacenándolo en la carpeta de datos de usuario de cada sistema:
- En Linux: `~/.local/share/EasyTextConverter/bin/pandoc`
- En Windows: `%LOCALAPPDATA%\EasyTextConverter\bin\pandoc.exe`
Si deseas distribuirlo en modo 100% portable sin conexión a internet, simplemente copia el archivo `pandoc` o `pandoc.exe` dentro de una subcarpeta llamada `bin` junto a tu ejecutable.

### SmartScreen o Antivirus en Windows
Al ser un ejecutable nuevo y no firmado con un certificado comercial de código, Windows Defender o SmartScreen puede mostrar una advertencia azul: *"Windows protegió su PC"*.
- Solo haz clic en **"Más información"** y luego en **"Ejecutar de todas formas"**.
