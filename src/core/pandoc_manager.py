"""
Manager to detect, verify, and download the latest Pandoc binary automatically.
Works cross-platform (Linux, Windows, macOS).
"""

import os
import sys
import platform
import shutil
import subprocess
import tarfile
import zipfile
import io
import requests
from typing import Optional, Callable, Tuple

APP_NAME = "pandoc-gui"

def get_app_data_dir() -> str:
    """Return platform-specific user data directory for the app."""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
        data_dir = os.path.join(base, APP_NAME)
    elif system == "Darwin":
        data_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    else:  # Linux and other Unix
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        data_dir = os.path.join(base, APP_NAME)
    
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_local_binary_path() -> str:
    """Get the expected path of the bundled/downloaded pandoc binary."""
    data_dir = get_app_data_dir()
    bin_dir = os.path.join(data_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    exe_name = "pandoc.exe" if platform.system() == "Windows" else "pandoc"
    return os.path.join(bin_dir, exe_name)

def get_portable_binary_path() -> Optional[str]:
    """Check if pandoc exists next to the current application or executable."""
    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    exe_name = "pandoc.exe" if platform.system() == "Windows" else "pandoc"
    candidates = [
        os.path.join(app_dir, exe_name),
        os.path.join(app_dir, "bin", exe_name),
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None

def get_pandoc_version(pandoc_path: str) -> Optional[str]:
    """Return pandoc version string if executable runs successfully."""
    try:
        # Hide window on Windows
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        res = subprocess.run(
            [pandoc_path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            startupinfo=startupinfo
        )
        if res.returncode == 0 and res.stdout:
            first_line = res.stdout.strip().splitlines()[0]
            # e.g. "pandoc 3.1.13" or "pandoc 3.13"
            parts = first_line.split()
            if len(parts) >= 2:
                return parts[1]
            return first_line
    except Exception:
        pass
    return None

def find_pandoc() -> Tuple[Optional[str], Optional[str]]:
    """
    Search for pandoc in:
    1. Local app data directory
    2. Portable app directory
    3. System PATH
    Returns (path, version) or (None, None).
    """
    # 1. Local downloaded binary
    local_path = get_local_binary_path()
    if os.path.isfile(local_path):
        ver = get_pandoc_version(local_path)
        if ver:
            return local_path, ver

    # 2. Portable binary next to app
    portable_path = get_portable_binary_path()
    if portable_path:
        ver = get_pandoc_version(portable_path)
        if ver:
            return portable_path, ver

    # 3. System PATH
    system_path = shutil.which("pandoc")
    if system_path:
        ver = get_pandoc_version(system_path)
        if ver:
            return system_path, ver

    return None, None

def resolve_latest_release_info() -> Tuple[str, str]:
    """
    Find latest tag and matching download URL for the current OS and architecture.
    Returns (tag, download_url).
    """
    system = platform.system()
    machine = platform.machine().lower()

    # Determine tag via direct HTTP redirect (safe against GitHub API limits)
    tag = "3.13"
    try:
        resp = requests.get("https://github.com/jgm/pandoc/releases/latest", allow_redirects=True, timeout=10)
        resolved_tag = resp.url.split("/")[-1]
        if resolved_tag and resolved_tag != "latest":
            tag = resolved_tag
    except Exception:
        pass

    # Try API first to get exact asset names if available
    api_url = f"https://api.github.com/repos/jgm/pandoc/releases/tags/{tag}"
    assets = []
    try:
        r = requests.get(api_url, timeout=10)
        if r.status_code == 200:
            assets = r.json().get("assets", [])
    except Exception:
        pass

    # Helper to find asset url or fallback to predictable release URL
    if system == "Windows":
        # Windows 64-bit zip
        target_sub = "windows-x86_64.zip"
        for a in assets:
            if target_sub in a.get("name", ""):
                return tag, a["browser_download_url"]
        return tag, f"https://github.com/jgm/pandoc/releases/download/{tag}/pandoc-{tag}-windows-x86_64.zip"

    elif system == "Darwin":
        # macOS
        is_arm = ("arm" in machine or "aarch64" in machine)
        target_sub = "arm64-macOS.zip" if is_arm else "x86_64-macOS.zip"
        for a in assets:
            if target_sub in a.get("name", ""):
                return tag, a["browser_download_url"]
        return tag, f"https://github.com/jgm/pandoc/releases/download/{tag}/pandoc-{tag}-{target_sub}"

    else:
        # Linux
        is_arm = ("aarch64" in machine or "arm64" in machine)
        target_sub = "linux-arm64.tar.gz" if is_arm else "linux-amd64.tar.gz"
        for a in assets:
            if target_sub in a.get("name", ""):
                return tag, a["browser_download_url"]
        return tag, f"https://github.com/jgm/pandoc/releases/download/{tag}/pandoc-{tag}-{target_sub}"

def download_and_extract_pandoc(
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> str:
    """
    Downloads and extracts the latest pandoc binary to the local app data directory.
    progress_callback receives (percentage_float_0_to_100, status_message_str).
    Returns the path to the installed pandoc binary.
    """
    target_path = get_local_binary_path()
    
    if progress_callback:
        progress_callback(5.0, "Consultando última versión de Pandoc...")

    tag, download_url = resolve_latest_release_info()

    if progress_callback:
        progress_callback(10.0, f"Descargando Pandoc {tag}...")

    # Stream download
    headers = {"User-Agent": "pandoc-gui-downloader"}
    with requests.get(download_url, headers=headers, stream=True, timeout=30) as response:
        response.raise_for_status()
        total_length = response.headers.get("content-length")
        content_bytes = io.BytesIO()
        
        if total_length is None:
            content_bytes.write(response.content)
            if progress_callback:
                progress_callback(70.0, "Descarga completada. Extrayendo binario...")
        else:
            total_size = int(total_length)
            downloaded = 0
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    content_bytes.write(chunk)
                    downloaded += len(chunk)
                    percent = 10.0 + (downloaded / total_size) * 65.0
                    if progress_callback:
                        mb_done = downloaded / (1024 * 1024)
                        mb_tot = total_size / (1024 * 1024)
                        progress_callback(
                            percent,
                            f"Descargando: {mb_done:.1f} MB / {mb_tot:.1f} MB ({int((downloaded/total_size)*100)}%)"
                        )

    if progress_callback:
        progress_callback(80.0, "Extrayendo ejecutable...")

    content_bytes.seek(0)
    system = platform.system()

    extracted_bytes = None

    if download_url.endswith(".zip"):
        with zipfile.ZipFile(content_bytes) as z:
            exe_target = "pandoc.exe" if system == "Windows" else "pandoc"
            for member in z.namelist():
                if member.endswith(f"/{exe_target}") or member.endswith(f"\\{exe_target}") or member == exe_target:
                    extracted_bytes = z.read(member)
                    break
    elif download_url.endswith(".tar.gz") or download_url.endswith(".tgz"):
        with tarfile.open(fileobj=content_bytes, mode="r:gz") as t:
            for member in t.getmembers():
                if member.name.endswith("/pandoc") or member.name == "pandoc":
                    f = t.extractfile(member)
                    if f:
                        extracted_bytes = f.read()
                    break

    if not extracted_bytes:
        raise RuntimeError(f"No se pudo encontrar el binario de Pandoc dentro del archivo descargado ({download_url}).")

    # Write binary atomically
    temp_path = target_path + ".tmp"
    with open(temp_path, "wb") as f_out:
        f_out.write(extracted_bytes)

    if system != "Windows":
        os.chmod(temp_path, 0o755)

    if os.path.exists(target_path):
        os.remove(target_path)
    os.rename(temp_path, target_path)

    if system != "Windows":
        os.chmod(target_path, 0o755)

    if progress_callback:
        progress_callback(100.0, f"Pandoc {tag} instalado exitosamente.")

    return target_path
