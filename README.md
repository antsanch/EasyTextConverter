# EasyTextConverter

Una interfaz gráfica moderna y ligera diseñada para redactar, pegar o abrir archivos de texto en **Markdown** y convertirlos con un solo clic a formatos como **ODT (Scribus / LibreOffice)**, **DOCX (Word)**, **HTML5**, **RTF**, **EPUB** y **Markdown original**.

---

## ✨ Características Principales

- **Diseñada para Maquetadores de Scribus y LibreOffice**:
  - Exportación directa a **ODT (`.odt`)**, el formato estándar y más confiable para importar en Scribus (*Clic derecho en el marco de texto → Obtener texto...*).
  - Mantiene intacta la jerarquía de títulos (`Heading 1`, `Heading 2`, `Heading 3`...), párrafos, citas, tablas, negritas, cursivas y listas sin colapsar.
- **Botones Directos de Guardado**:
  - `[📥 Guardar ODT (Scribus)]` (Acceso prioritario destacado).
  - `[📄 DOCX]`, `[🌐 HTML]`, `[📑 RTF]`, `[📖 EPUB]`, `[📝 MD]`.
- **Menú Superior Completo**:
  - **Archivo**: Nuevo (`Ctrl+N`), Abrir (`Ctrl+O`), Guardar (`Ctrl+S`), Guardar como (`Ctrl+Shift+S`), Exportar con Pandoc y Cerrar (`Ctrl+W`).
  - **Editar**: Deshacer, Rehacer, Cortar, Copiar, Pegar, Seleccionar todo, Reemplazo de `\n` y Limpiar.
  - **Pandoc**: Comprobación y descarga de actualizaciones en vivo.
  - **Ayuda**: Guía interactiva de importación para Scribus.
- **Herramienta `[↵ Reemplazar \n]`**:
  - Convierte secuencias literales `\n` o `\r\n` (típicas al copiar desde APIs, JSON o terminales) en retornos de carro reales sin alterar ninguna letra ni formato.
- **Descarga y Detección Automática de Pandoc**:
  - Si Pandoc no está instalado, la app lo descarga automáticamente desde los releases oficiales de GitHub con barra de progreso en vivo.
- **Multiplataforma**: Funciona de forma idéntica y nativa en **Linux** y **Windows**.

---

## 🚀 Uso Rápido (Desde el código fuente)

### Requisitos
- Python 3.10 o superior.

### Instalación y Ejecución
1. Clona o descarga este repositorio:
   ```bash
   cd EasyTextConverter
   ```

2. Crea y activa un entorno virtual:
   ```bash
   # En Linux / macOS:
   python3 -m venv .venv
   source .venv/bin/activate

   # En Windows:
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Ejecuta la aplicación:
   ```bash
   python src/main.py
   ```

---

## 📦 Compilación de Ejecutables Autónomos (Standalone)

Puedes empaquetar la aplicación en un solo archivo ejecutable para que funcione sin necesidad de tener Python instalado en el equipo destino.

### En Linux
Ejecuta el script de compilación:
```bash
./build_scripts/build_linux.sh
```
El binario resultante se encontrará en:
```text
dist/EasyTextConverter
```
*(Para ejecutarlo: `./dist/EasyTextConverter`)*

### En Windows
Haz doble clic en:
```cmd
build_scripts\build_windows.bat
```
O desde la consola de Windows:
```cmd
pyinstaller --name "EasyTextConverter" --onefile --windowed --noconfirm --clean src\main.py
```
El ejecutable resultante se encontrará en:
```text
dist\EasyTextConverter.exe
```

### Compilación Automática en la Nube (GitHub Actions)
El repositorio incluye un flujo de trabajo en `.github/workflows/build.yml`. Cuando subas este código a un repositorio de GitHub:
1. Compilará automáticamente las versiones de **Linux** y **Windows (`.exe`)**.
2. Podrás descargar los binarios compilados directamente desde la pestaña **Actions** o en la sección de **Releases** al crear una etiqueta (tag).

---

## 📖 Flujo de Trabajo Recomendado con Scribus

1. Abre **EasyTextConverter** y pega o abre tu archivo Markdown.
2. Haz clic en el botón superior azul: **`📥 Guardar ODT (Scribus)`**.
3. Elige la carpeta y el nombre del archivo (ej. `capitulo1.odt`).
4. Abre **Scribus**:
   - Dibuja un **Marco de Texto** en tu página de Scribus.
   - Haz clic derecho sobre el marco de texto y selecciona **Obtener texto...** (*Get Text...*).
   - Selecciona el archivo `.odt` guardado.
   - En el cuadro de diálogo del importador de ODT, asegúrate de marcar la casilla para **importar estilos**.
5. ¡Listo! Scribus creará y aplicará automáticamente los estilos de párrafo para `Heading 1`, `Heading 2`, `Paragraph`, así como las negritas y cursivas. Podrás modificar la tipografía, tamaños y colores de esos estilos desde el Gestor de Estilos (`F3`) de Scribus y se aplicarán a todo el documento.

---

## 📂 Estructura del Proyecto

```
EasyTextConverter/
├── src/
│   ├── main.py                  # Punto de entrada de la aplicación
│   ├── core/
│   │   ├── converter.py         # Conversión de Markdown (GFM) a ODT/DOCX/HTML/RTF
│   │   ├── formatter.py         # Reemplazo limpio de secuencias \n literales
│   │   └── pandoc_manager.py    # Búsqueda y autodescarga de la última versión de Pandoc
│   └── ui/
│       ├── main_window.py       # Ventana principal, menú superior y botones de exportación
│       └── download_dialog.py   # Modal con progreso de descarga
├── build_scripts/
│   ├── build_linux.sh           # Script para generar ejecutable standalone en Linux
│   ├── build_windows.bat        # Script para generar EasyTextConverter.exe en Windows
│   └── INSTRUCCIONES_COMPILACION.md # Guía detallada de compilación
├── .github/
│   └── workflows/
│       └── build.yml            # CI/CD para compilar Linux y Windows automáticamente
├── requirements.txt
└── README.md
```
