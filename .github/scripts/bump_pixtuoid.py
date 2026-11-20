"""Bump instalar.py to the latest stable Pixtuoid release, verifying its SHA-256.

Reads GitHub's `releases/latest` (never drafts, pre-releases or unreleased `main`),
downloads the Windows x64 archive and checks it against the digest GitHub publishes for
that asset. Only then are VERSION and SHA256 rewritten. With --dry-run nothing is
written. Results go to $GITHUB_OUTPUT when it is set (updated, version).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "instalar.py"
API = "https://api.github.com/repos/pixtuoid/pixtuoid/releases/latest"
VERSION_LINE = re.compile(r'^VERSION = "(\d+)\.(\d+)\.(\d+)"$', re.M)
SHA_LINE = re.compile(r'^SHA256 = "[0-9a-f]{64}"$', re.M)


def parse(version):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", version or "")
    if not match:
        raise ValueError(f"Not a stable release version: {version!r}")
    return tuple(int(part) for part in match.groups())


def pinned(text):
    match = VERSION_LINE.search(text)
    if not match or not SHA_LINE.search(text):
        raise ValueError("instalar.py has no VERSION/SHA256 pin")
    return tuple(int(part) for part in match.groups())


def asset_for(release):
    """The Windows x64 archive of a stable release and the SHA-256 GitHub publishes for it."""
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("The latest release is a draft or a pre-release")
    version = ".".join(map(str, parse(release.get("tag_name"))))
    name = f"pixtuoid-v{version}-x86_64-pc-windows-msvc.zip"
    for asset in release.get("assets") or []:
        if asset.get("name") == name:
            digest = asset.get("digest") or ""
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise ValueError(f"{name} has no published SHA-256 digest")
            return version, asset["browser_download_url"], digest.removeprefix("sha256:")
    raise ValueError(f"The release has no {name}")


def bump(text, version, sha256):
    """instalar.py with the new pin, or None when the pin is already this version or newer."""
    if parse(version) <= pinned(text):
        return None
    text = VERSION_LINE.sub(f'VERSION = "{version}"', text, count=1)
    return SHA_LINE.sub(f'SHA256 = "{sha256}"', text, count=1)


def get(url, accept="application/vnd.github+json"):
    request = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "pixtuoid-orca-release-check"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        request.add_header("Authorization", f"Bearer {token}")
    return urllib.request.urlopen(request, timeout=120)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report only; never write instalar.py")
    options = parser.parse_args()
    with get(API) as response:
        release = json.load(response)
    version, url, published = asset_for(release)
    text = INSTALLER.read_text(encoding="utf-8")
    current = ".".join(map(str, pinned(text)))
    updated = bump(text, version, published)
    if updated is None:
        print(f"Pixtuoid {current} is pinned; the latest stable release is {version}. Nothing to do.")
    else:
        digest = hashlib.sha256()
        with get(url, "application/octet-stream") as response:
            for chunk in iter(lambda: response.read(1 << 20), b""):
                digest.update(chunk)
        if digest.hexdigest() != published:
            raise SystemExit(f"The downloaded {version} archive does not match its published SHA-256")
        print(f"Pixtuoid {version} is newer than the pinned {current}; SHA-256 verified ({published}).")
        if not options.dry_run:
            INSTALLER.write_text(updated, encoding="utf-8", newline="\n")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as out:
            out.write(f"updated={'true' if updated and not options.dry_run else 'false'}\n")
            out.write(f"version={version}\n")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"Pixtuoid release check failed: {error}")
