"""Install the pinned Pixtuoid release in this checkout on Windows."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

from oficina import APP, LAB, PROFILE, SOURCES, office_env, orca_json

VERSION = "0.23.0"
ARCHIVE = f"pixtuoid-v{VERSION}-x86_64-pc-windows-msvc.zip"
SHA256 = "e52205aba4061112f94f40529d920e0346c98c0f4123edeceebee12e80303dad"
RELEASE = f"https://github.com/pixtuoid/pixtuoid/releases/download/v{VERSION}/{ARCHIVE}"
CONFIG = PROFILE / "config" / "pixtuoid" / "config.toml"


def install_release():
    if APP.is_file() and APP.with_name("pixtuoid-hook.exe").is_file():
        version = subprocess.check_output([APP, "--version"], text=True).strip()
        if version == f"pixtuoid {VERSION}":
            return
    if APP.parent.exists():
        raise RuntimeError(f"Hay una instalacion distinta o incompleta en {APP.parent}. Muevela antes de instalar.")
    with tempfile.TemporaryDirectory(prefix=".instalacion-", dir=LAB) as directory:
        staging = Path(directory).resolve()
        if staging.parent != LAB:
            raise RuntimeError("La carpeta temporal quedo fuera del repositorio.")
        archive = staging / ARCHIVE
        with urllib.request.urlopen(RELEASE, timeout=60) as response, archive.open("wb") as out:
            shutil.copyfileobj(response, out)
        with archive.open("rb") as data:
            digest = hashlib.file_digest(data, "sha256").hexdigest()
        if digest != SHA256:
            raise RuntimeError("El SHA-256 del binario descargado difiere del publicado en GitHub.")
        output = staging / "app"
        with zipfile.ZipFile(archive) as release:
            release.extractall(output)
        if not all((output / name).is_file() for name in ("pixtuoid.exe", "pixtuoid-hook.exe", "LICENSE")):
            raise RuntimeError("La descarga no contiene los binarios y la licencia esperados.")
        output.rename(APP.parent)


def shortcut():
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not pythonw.is_file():
        raise RuntimeError("Falta pythonw.exe junto al Python utilizado para instalar.")
    env = dict(os.environ, PIXTUOID_SHORTCUT_DIR=str(LAB), PIXTUOID_SHORTCUT_PYTHON=str(pythonw))
    command = r"""
$ErrorActionPreference = 'Stop'
$root = $env:PIXTUOID_SHORTCUT_DIR
$wsh = New-Object -ComObject WScript.Shell
$link = $wsh.CreateShortcut((Join-Path $root 'Abrir oficina.lnk'))
$link.TargetPath = $env:PIXTUOID_SHORTCUT_PYTHON
$link.Arguments = '"' + (Join-Path $root 'oficina.py') + '"'
$link.WorkingDirectory = $root
$link.IconLocation = (Join-Path $root 'app\pixtuoid.exe') + ',0'
$link.Description = 'Pixtuoid flotante con sesiones locales de Orca'
$link.Save()
"""
    subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                   env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", nargs="+", choices=sorted(set(SOURCES.values())),
                        help="Limitar los agentes configurados. Por defecto detecta los disponibles en Orca.")
    options = parser.parse_args()
    if sys.platform != "win32" or os.environ.get("PROCESSOR_ARCHITECTURE") != "AMD64" or sys.version_info < (3, 11):
        parser.error("Se necesita Windows x64 y Python 3.11 o posterior de 64 bits.")
    orca = shutil.which("orca.exe")
    if not orca:
        parser.error("orca.exe debe estar en PATH y Orca debe estar abierto.")
    installed = orca_json(orca, "agent", "installed")["agents"]
    available = {SOURCES[row["id"]] for row in installed if row.get("id") in SOURCES}
    chosen = set(options.sources) if options.sources else available
    if not chosen:
        parser.error("Orca aun no reconoce un agente compatible.")
    missing = chosen - available
    if missing:
        parser.error(f"Orca no reconoce estas fuentes: {', '.join(sorted(missing))}")
    required_cli = {"antigravity": "agy", "claude-code": "claude", "codex": "codex"}
    for source in sorted(chosen & required_cli.keys()):
        command = required_cli[source]
        if shutil.which(command) is None:
            parser.error(f"{source} necesita {command} en PATH para preparar su perfil aislado.")
    install_release()
    env = office_env()
    for key in ("APPDATA", "LOCALAPPDATA", "CLAUDE_CONFIG_DIR", "CODEX_HOME",
                "OPENCODE_CONFIG_DIR", "XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_DATA_HOME",
                "TEMP"):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG.exists():
        CONFIG.write_text(f'last-seen-version = "{VERSION}"\n', encoding="utf-8")
    connected = subprocess.run([APP, "connect", "--json", *sorted(chosen)], env=env, cwd=LAB,
                               capture_output=True, encoding="utf-8")
    if connected.returncode:
        raise RuntimeError(connected.stderr.strip() or connected.stdout.strip())
    outcomes = json.loads(connected.stdout)
    failures = [row for row in outcomes if row.get("outcome") not in {"connected", "no_op"}]
    if {row["id"] for row in outcomes} != chosen or failures:
        raise RuntimeError(f"Pixtuoid no preparo todas las fuentes: {failures}")
    (PROFILE / "fuentes.json").write_text(json.dumps(sorted(chosen)) + "\n", encoding="utf-8")
    shortcut()
    print(f"Fuentes preparadas en el perfil aislado: {', '.join(sorted(chosen))}.")
    print(f"Abre {LAB / 'Abrir oficina.lnk'} con doble clic.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as error:
        raise SystemExit(f"No se pudo instalar Pixtuoid: {error}") from error
