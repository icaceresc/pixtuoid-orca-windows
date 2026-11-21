"""Install the office on Windows: official Pixtuoid (oficina) or Dungeons & Agents (dungeon).

Each mode has its own pinned release; a local build or an owner-released zip can stand in
for either. The chosen mode is remembered in app/origen.json for the next update.
"""
import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

from oficina import APP, HOME, LAB, PROFILE, SOURCES, office_env, orca_json

VERSION = "0.23.0"
ARCHIVE = f"pixtuoid-v{VERSION}-x86_64-pc-windows-msvc.zip"
SHA256 = "e52205aba4061112f94f40529d920e0346c98c0f4123edeceebee12e80303dad"
RELEASE = f"https://github.com/pixtuoid/pixtuoid/releases/download/v{VERSION}/{ARCHIVE}"
# PLACEHOLDER: the Dungeons & Agents release (github.com/icaceresc/dungeons-and-agents) is not
# published yet. Its zip URL and SHA-256 land here before the publication gate; until then
# dungeon mode installs only from --local or --url.
DUNGEON_RELEASE = None
DUNGEON_SHA256 = None
MODES = ("oficina", "dungeon")
CONFIG = PROFILE / "config" / "pixtuoid" / "config.toml"
# Marks a data folder this installer made outside a clone, so the plugin may remove it.
MARKER = HOME / ".pixtuoid-orca-home"
EXES = ("pixtuoid.exe", "pixtuoid-hook.exe")
# What app/ holds (pinned, local or url), so a plain run never overwrites a custom build.
ORIGIN = "origen.json"


def installed_version(app=None):
    """The app's version line, or None when the folder holds no working Pixtuoid."""
    app = app or APP
    if not (app.is_file() and app.with_name("pixtuoid-hook.exe").is_file()):
        return None
    try:
        return subprocess.check_output([app, "--version"], text=True, timeout=20).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def installed_origin():
    """What app/origen.json says is installed, or None for an install made before it existed."""
    path = APP.with_name(ORIGIN)
    if not path.is_file():
        return None
    try:
        origin = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        origin = None
    # Unreadable, it is still ours and may hold a custom build: never guess it is the pin.
    return origin if isinstance(origin, dict) else {"kind": "desconocido"}


def is_custom(origin):
    return origin is not None and origin.get("kind") != "pinned"


def installed_mode():
    """The mode app/ holds; an install made before modes existed is the official office."""
    mode = (installed_origin() or {}).get("modo")
    return mode if mode in MODES else "oficina"


def pin_for(mode):
    """The pinned release (url, sha256) of a mode."""
    if mode == "oficina":
        return RELEASE, SHA256
    if not (DUNGEON_RELEASE and DUNGEON_SHA256):
        raise RuntimeError("Dungeons & Agents aun no tiene una version publicada fijada en este plugin. "
                           "Instala una compilacion propia: py -3 instalar.py --modo dungeon --local <carpeta>")
    return DUNGEON_RELEASE, DUNGEON_SHA256


def refuse_foreign(current):
    # An app/ that is neither a working Pixtuoid nor recorded by this installer may be
    # someone else's data: it is never replaced.
    if APP.parent.exists() and not (current or "").startswith("pixtuoid ") and installed_origin() is None:
        raise RuntimeError(f"Hay una instalacion distinta o incompleta en {APP.parent}. Muevela antes de instalar.")


@contextlib.contextmanager
def staging_folder():
    with tempfile.TemporaryDirectory(prefix=".instalacion-", dir=HOME) as directory:
        staging = Path(directory).resolve()
        if staging.parent != HOME:
            raise RuntimeError("La carpeta temporal quedo fuera del repositorio.")
        yield staging


def sha256_of(path):
    with path.open("rb") as data:
        return hashlib.file_digest(data, "sha256").hexdigest()


def download(url, archive):
    with urllib.request.urlopen(url, timeout=60) as response, archive.open("wb") as out:
        shutil.copyfileobj(response, out)
    return sha256_of(archive)


def extract(archive, output):
    with zipfile.ZipFile(archive) as release:
        release.extractall(output)
    if not all((output / name).is_file() for name in (*EXES, "LICENSE")):
        raise RuntimeError("La descarga no contiene los binarios y la licencia esperados.")


def check_pixtuoid(output):
    version = installed_version(output / "pixtuoid.exe") or ""
    if not version.startswith("pixtuoid "):
        raise RuntimeError(f"El pixtuoid.exe nuevo no responde como Pixtuoid a --version: {version!r}.")


def swap_in(staging, output, origin):
    """Replace app/ with output/ and its origin record, rolling back if the move fails."""
    origin = dict(origin, installed=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
    (output / ORIGIN).write_text(json.dumps(origin, indent=2) + "\n", encoding="utf-8")
    previous = staging / "previous"
    if APP.parent.exists():
        # Update: the verified binary replaces the old one only after it passed every
        # check. The office must be closed: Windows keeps running .exe files locked.
        try:
            APP.parent.rename(previous)
        except OSError as error:
            raise RuntimeError(f"No se pudo reemplazar {APP.parent} ({error.strerror or error}): cierra la "
                               "oficina (py -3 oficina.py --stop) y vuelve a intentarlo.") from error
    try:
        output.rename(APP.parent)
    except OSError:
        if previous.exists():
            previous.rename(APP.parent)
        raise


def install_release(mode="oficina", force=False):
    """A mode's pinned release. force replaces a custom build even when it prints the pin."""
    url, sha256 = pin_for(mode)
    current = installed_version()
    origin = installed_origin()
    if current and not force:
        if origin is None:
            # Recorded before origen.json: only the official pin's version can tell.
            if mode == "oficina" and current == f"pixtuoid {VERSION}":
                return
        elif origin.get("kind") == "pinned" and origin.get("sha256") == sha256 and installed_mode() == mode:
            return
    refuse_foreign(current)
    with staging_folder() as staging:
        archive = staging / "pixtuoid.zip"
        digest = download(url, archive)
        if digest != sha256:
            raise RuntimeError("El SHA-256 del binario descargado difiere del publicado en GitHub.")
        output = staging / "app"
        extract(archive, output)
        swap_in(staging, output, {"kind": "pinned", "modo": mode, "source": url, "sha256": digest})


def install_url(url, sha256, mode="oficina"):
    """An owner-released zip with upstream's Windows layout, checked against its --sha256."""
    refuse_foreign(installed_version())
    with staging_folder() as staging:
        archive = staging / "pixtuoid.zip"
        digest = download(url, archive)
        if digest != sha256:
            raise RuntimeError(f"El SHA-256 del zip descargado ({digest}) difiere del indicado con --sha256.")
        output = staging / "app"
        extract(archive, output)
        check_pixtuoid(output)
        swap_in(staging, output, {"kind": "url", "modo": mode, "source": url, "sha256": digest})


def find_license(folder):
    """LICENSE beside the build or in a parent folder, never above the build's Git repository."""
    for candidate in (folder, *folder.parents):
        if (candidate / "LICENSE").is_file():
            return candidate / "LICENSE"
        if (candidate / ".git").exists():
            return None
    return None


def install_local(folder, mode="oficina"):
    """A local build: the two executables of a folder such as target\\release, plus LICENSE."""
    folder = Path(folder).resolve()
    missing = [name for name in EXES if not (folder / name).is_file()]
    if missing:
        raise RuntimeError(f"Faltan {', '.join(missing)} en {folder}.")
    license_file = find_license(folder)
    if license_file is None:
        raise RuntimeError(f"No se encontro LICENSE junto a {folder} ni en la raiz de su repositorio: el aviso "
                           "MIT de Pixtuoid debe acompanar al binario. Copia ahi el LICENSE de Pixtuoid.")
    refuse_foreign(installed_version())
    with staging_folder() as staging:
        output = staging / "app"
        output.mkdir()
        for name in EXES:
            shutil.copy2(folder / name, output / name)
        shutil.copy2(license_file, output / "LICENSE")
        check_pixtuoid(output)
        digests = {name: sha256_of(output / name) for name in EXES}
        swap_in(staging, output, {"kind": "local", "modo": mode, "source": str(folder), "sha256": digests})


def install_binary(options):
    """Install what the options ask for, in the mode asked or the one remembered.

    A plain run, or one asking for the mode already installed, never replaces a custom build
    silently; asking for the other mode, or --pinned, installs that mode's pinned release.
    """
    current = installed_mode()
    mode = options.modo or current
    if options.local:
        install_local(options.local, mode)
        print(f"Instalada la compilacion local de {Path(options.local).resolve()} ({mode}) en {APP.parent}.")
    elif options.url:
        install_url(options.url, options.sha256, mode)
        print(f"Instalado el binario de {options.url} ({mode}, SHA-256 verificado) en {APP.parent}.")
    else:
        origin = installed_origin()
        if is_custom(origin) and not options.pinned and mode == current:
            print(f"Se mantiene la compilacion propia de {APP.parent} ({origin.get('kind')}, {mode}: "
                  f"{origin.get('source', '?')}). Para volver a la version fijada: py -3 instalar.py --pinned")
            return
        install_release(mode, force=is_custom(origin) or mode != current)
        print(f"Modo {mode}: {'Dungeons & Agents' if mode == 'dungeon' else f'Pixtuoid v{VERSION}'} "
              f"instalado en {APP.parent}.")


def parser_for():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", nargs="+", choices=sorted(set(SOURCES.values())),
                        help="Limitar los agentes configurados. Por defecto detecta los disponibles en Orca.")
    binary = parser.add_mutually_exclusive_group()
    binary.add_argument("--local", metavar="CARPETA",
                        help="Instalar una compilacion propia: carpeta con pixtuoid.exe y pixtuoid-hook.exe "
                             "(por ejemplo target\\release). LICENSE se busca ahi o hasta la raiz de su repositorio.")
    binary.add_argument("--url", metavar="URL",
                        help="Instalar un zip https del propietario con la misma estructura que el de Pixtuoid "
                             "para Windows (exes y LICENSE en la raiz). Exige --sha256.")
    binary.add_argument("--pinned", action="store_true",
                        help="Volver a la version fijada del modo aunque haya una compilacion propia instalada.")
    parser.add_argument("--modo", choices=MODES,
                        help=f"oficina: Pixtuoid v{VERSION} oficial. dungeon: Dungeons & Agents (clases, "
                             "habilidades y clic que abre la sesion en Orca). Se recuerda para las "
                             "actualizaciones; por defecto, el instalado.")
    parser.add_argument("--sha256", metavar="HEX", help="SHA-256 esperado del zip de --url (64 hexadecimales).")
    return parser


def parse_options(parser, argv=None):
    options = parser.parse_args(argv)
    if options.sha256 and not options.url:
        parser.error("--sha256 solo se usa con --url.")
    if options.url:
        address = urllib.parse.urlsplit(options.url)
        if address.scheme != "https" or not address.netloc:
            parser.error("--url debe ser una direccion https.")
        if not options.sha256:
            parser.error("--url exige --sha256 con el SHA-256 esperado del zip.")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", options.sha256):
            parser.error("--sha256 debe tener 64 caracteres hexadecimales.")
        options.sha256 = options.sha256.lower()
    if options.local and not Path(options.local).is_dir():
        parser.error(f"--local no es una carpeta: {options.local}")
    return options


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
    parser = parser_for()
    options = parse_options(parser)
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
    if HOME != LAB and not MARKER.exists() and HOME.exists() and any(HOME.iterdir()):
        parser.error(f"{HOME} ya existe y no la creo este instalador. Elige otra carpeta.")
    HOME.mkdir(parents=True, exist_ok=True)
    if HOME != LAB and not MARKER.exists():
        MARKER.write_text("Pixtuoid for Orca data folder. Safe to delete while the office is closed.\n",
                          encoding="utf-8")
    install_binary(options)
    env = office_env()
    for key in ("APPDATA", "LOCALAPPDATA", "CLAUDE_CONFIG_DIR", "CODEX_HOME",
                "OPENCODE_CONFIG_DIR", "XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_DATA_HOME",
                "TEMP"):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG.exists():
        CONFIG.write_text(f'last-seen-version = "{VERSION}"\n', encoding="utf-8")
    connected = subprocess.run([APP, "connect", "--json", *sorted(chosen)], env=env, cwd=HOME,
                               capture_output=True, encoding="utf-8")
    if connected.returncode:
        raise RuntimeError(connected.stderr.strip() or connected.stdout.strip())
    outcomes = json.loads(connected.stdout)
    failures = [row for row in outcomes if row.get("outcome") not in {"connected", "no_op"}]
    if {row["id"] for row in outcomes} != chosen or failures:
        raise RuntimeError(f"Pixtuoid no preparo todas las fuentes: {failures}")
    (PROFILE / "fuentes.json").write_text(json.dumps(sorted(chosen)) + "\n", encoding="utf-8")
    print(f"Fuentes preparadas en el perfil aislado: {', '.join(sorted(chosen))}.")
    if HOME == LAB:
        shortcut()
        print(f"Abre {LAB / 'Abrir oficina.lnk'} con doble clic.")
    else:
        # Orca's plugin folder changes on every update: it opens the office itself.
        print("Abre la oficina desde Orca: Pixtuoid: Open office window.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as error:
        raise SystemExit(f"No se pudo instalar Pixtuoid: {error}") from error
