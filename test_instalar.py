"""Offline tests for instalar.py's binary choice: pinned, local build or owner URL."""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import instalar

SHA = "c" * 64


def parse(*argv):
    """The options, or the argparse error text when the arguments are refused."""
    error = io.StringIO()
    with contextlib.redirect_stderr(error):
        try:
            return instalar.parse_options(instalar.parser_for(), list(argv))
        except SystemExit:
            return error.getvalue()


def release_zip(names=("pixtuoid.exe", "pixtuoid-hook.exe", "LICENSE")):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        for name in names:
            archive.writestr(name, f"fake {name}")
    return data.getvalue()


class Sandbox:
    """A data folder inside the checkout with patched HOME/APP and a faked --version."""

    def __init__(self, version="pixtuoid 0.23.0"):
        self.version = version
        self.downloads = []

    def __enter__(self):
        self.directory = tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent)
        self.root = Path(self.directory.name).resolve()
        self.home = self.root / "home"
        self.home.mkdir()
        self.app = self.home / "app"
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(patch.object(instalar, "HOME", self.home))
        self.stack.enter_context(patch.object(instalar, "APP", self.app / "pixtuoid.exe"))
        self.stack.enter_context(patch.object(instalar.subprocess, "check_output", side_effect=self.check_output))
        return self

    def __exit__(self, *error):
        self.stack.close()
        self.directory.cleanup()

    def check_output(self, command, **_):
        return self.version + "\n"

    def serve(self, payload):
        def urlopen(url, timeout):
            self.downloads.append(url)
            return io.BytesIO(payload)
        self.stack.enter_context(patch.object(instalar.urllib.request, "urlopen", side_effect=urlopen))

    def old_app(self, origin=None):
        self.app.mkdir()
        for name in instalar.EXES:
            (self.app / name).write_bytes(b"old")
        if origin:
            (self.app / instalar.ORIGIN).write_text(json.dumps(origin), encoding="utf-8")

    def build(self, license_at="repo", git=True):
        repo = self.root / "fork"
        build = repo / "target" / "release"
        build.mkdir(parents=True)
        if git:
            (repo / ".git").mkdir()
        for name in instalar.EXES:
            (build / name).write_bytes(f"new {name}".encode())
        # A LICENSE above the build's repository must never be taken for Pixtuoid's.
        (self.root / "LICENSE").write_text("someone else's", encoding="utf-8")
        if license_at == "repo":
            (repo / "LICENSE").write_text("MIT License (Pixtuoid)", encoding="utf-8")
        elif license_at == "build":
            (build / "LICENSE").write_text("MIT License (Pixtuoid)", encoding="utf-8")
        return build

    def origin(self):
        return json.loads((self.app / instalar.ORIGIN).read_text(encoding="utf-8"))


class ArgumentTests(unittest.TestCase):
    def test_default_run_asks_for_no_custom_binary(self):
        options = parse()
        self.assertFalse(options.local or options.url or options.pinned or options.sha256)

    def test_url_needs_an_explicit_sha256(self):
        self.assertIn("--sha256", parse("--url", "https://example.invalid/p.zip"))

    def test_only_https_urls(self):
        for url in ("http://example.invalid/p.zip", "file:///C:/p.zip", "https:///p.zip"):
            self.assertIn("https", parse("--url", url, "--sha256", SHA), url)

    def test_sha256_must_be_64_hex(self):
        for digest in ("c" * 63, "c" * 65, "g" * 64, "sha256:" + SHA):
            self.assertIn("64", parse("--url", "https://example.invalid/p.zip", "--sha256", digest), digest)

    def test_sha256_is_normalized_and_only_for_url(self):
        options = parse("--url", "https://example.invalid/p.zip", "--sha256", "C" * 64)
        self.assertEqual(options.sha256, SHA)
        self.assertIn("--url", parse("--sha256", SHA))

    def test_one_binary_choice_and_local_must_be_a_folder(self):
        self.assertIn("not allowed", parse("--local", ".", "--pinned"))
        self.assertIn("--local", parse("--local", "no-such-folder-xyz"))
        self.assertEqual(parse("--local", ".").local, ".")


class LocalBuildTests(unittest.TestCase):
    def test_local_build_replaces_an_app_that_prints_the_same_version(self):
        with Sandbox() as box:
            box.old_app()
            build = box.build()
            instalar.install_local(build)
            self.assertEqual((box.app / "pixtuoid.exe").read_bytes(), b"new pixtuoid.exe")
            self.assertEqual((box.app / "LICENSE").read_text(encoding="utf-8"), "MIT License (Pixtuoid)")
            origin = box.origin()
            self.assertEqual((origin["kind"], origin["source"]), ("local", str(build)))
            self.assertEqual(origin["sha256"]["pixtuoid-hook.exe"],
                             hashlib.sha256(b"new pixtuoid-hook.exe").hexdigest())
            self.assertIn("installed", origin)
            self.assertEqual(list(box.home.glob(".instalacion-*")), [], "No staging left behind")

    def test_license_beside_the_exes_is_enough_without_a_repository(self):
        with Sandbox() as box:
            instalar.install_local(box.build(license_at="build", git=False))
            self.assertEqual((box.app / "LICENSE").read_text(encoding="utf-8"), "MIT License (Pixtuoid)")

    def test_missing_license_fails_and_keeps_the_old_app(self):
        with Sandbox() as box:
            box.old_app()
            with self.assertRaisesRegex(RuntimeError, "LICENSE"):
                instalar.install_local(box.build(license_at=None))
            self.assertEqual((box.app / "pixtuoid.exe").read_bytes(), b"old")

    def test_a_binary_that_is_not_pixtuoid_is_refused(self):
        with Sandbox(version="something 1.0") as box:
            box.old_app({"kind": "pinned"})
            with self.assertRaisesRegex(RuntimeError, "Pixtuoid"):
                instalar.install_local(box.build())
            self.assertEqual((box.app / "pixtuoid.exe").read_bytes(), b"old")

    def test_locked_app_fails_clearly_and_keeps_it(self):
        with Sandbox() as box:
            box.old_app()
            build = box.build()
            rename = Path.rename

            def locked(path, target):
                if path == box.app:
                    raise PermissionError(13, "Access is denied")
                return rename(path, target)
            with patch.object(Path, "rename", locked), \
                    self.assertRaisesRegex(RuntimeError, "cierra la oficina"):
                instalar.install_local(build)
            self.assertEqual((box.app / "pixtuoid.exe").read_bytes(), b"old")


class OwnerUrlTests(unittest.TestCase):
    URL = "https://example.invalid/pixtuoid-fantasy.zip"

    def test_sha_mismatch_installs_nothing(self):
        with Sandbox() as box:
            box.old_app()
            box.serve(release_zip())
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                instalar.install_url(self.URL, SHA)
            self.assertEqual(box.downloads, [self.URL])
            self.assertEqual((box.app / "pixtuoid.exe").read_bytes(), b"old")

    def test_verified_zip_is_installed_and_recorded(self):
        payload = release_zip()
        digest = hashlib.sha256(payload).hexdigest()
        with Sandbox() as box:
            box.old_app()
            box.serve(payload)
            instalar.install_url(self.URL, digest)
            self.assertEqual((box.app / "pixtuoid.exe").read_text(encoding="utf-8"), "fake pixtuoid.exe")
            self.assertEqual({k: box.origin()[k] for k in ("kind", "source", "sha256")},
                             {"kind": "url", "source": self.URL, "sha256": digest})

    def test_zip_without_license_is_refused(self):
        payload = release_zip(names=instalar.EXES)
        with Sandbox() as box:
            box.serve(payload)
            with self.assertRaisesRegex(RuntimeError, "licencia"):
                instalar.install_url(self.URL, hashlib.sha256(payload).hexdigest())
            self.assertFalse(box.app.exists())


class DefaultRunTests(unittest.TestCase):
    def options(self, **chosen):
        return SimpleNamespace(**dict({"local": None, "url": None, "sha256": None, "pinned": False,
                                       "modo": None}, **chosen))

    def test_installed_pin_is_kept_without_downloading(self):
        with Sandbox() as box:
            box.old_app()
            box.serve(b"")
            instalar.install_binary(self.options())
            self.assertEqual(box.downloads, [])

    def test_older_pin_downloads_the_pinned_release_with_its_sha_check(self):
        with Sandbox(version="pixtuoid 0.22.0") as box:
            box.old_app()
            box.serve(release_zip())
            with self.assertRaisesRegex(RuntimeError, "difiere del publicado en GitHub"):
                instalar.install_binary(self.options())
            self.assertEqual(box.downloads, [instalar.RELEASE])
            self.assertEqual((box.app / "pixtuoid.exe").read_bytes(), b"old")

    def test_pinned_install_is_recorded(self):
        payload = release_zip()
        with Sandbox(version="pixtuoid 0.22.0") as box, \
                patch.object(instalar, "SHA256", hashlib.sha256(payload).hexdigest()):
            box.serve(payload)
            instalar.install_binary(self.options())
            self.assertEqual(box.origin()["kind"], "pinned")

    def test_plain_run_keeps_a_custom_build_and_says_how_to_go_back(self):
        with Sandbox() as box:
            box.old_app({"kind": "local", "source": "C:\\fork\\target\\release"})
            box.serve(b"")
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                instalar.install_binary(self.options())
            self.assertEqual(box.downloads, [])
            self.assertIn("--pinned", printed.getvalue())
            self.assertEqual((box.app / "pixtuoid.exe").read_bytes(), b"old")

    def test_pinned_flag_replaces_a_custom_build_that_prints_the_pin(self):
        with Sandbox() as box:
            box.old_app({"kind": "url", "source": OwnerUrlTests.URL})
            box.serve(release_zip())
            with self.assertRaisesRegex(RuntimeError, "difiere del publicado en GitHub"):
                instalar.install_binary(self.options(pinned=True))
            self.assertEqual(box.downloads, [instalar.RELEASE], "Same version string, still replaced")

    def test_unknown_folder_is_still_refused(self):
        with Sandbox() as box:
            box.app.mkdir()
            (box.app / "notes.txt").write_text("not Pixtuoid", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Muevela"):
                instalar.install_local(box.build())


class ModeTests(unittest.TestCase):
    """`--modo oficina|dungeon`: which pinned build an install takes, remembered in origen.json."""

    def options(self, **chosen):
        return DefaultRunTests.options(self, **chosen)

    def dungeon_release(self, box, payload):
        """A file:// stand-in for the Dungeons & Agents release zip, with its real SHA-256."""
        archive = box.root / "dungeons-and-agents.zip"
        archive.write_bytes(payload)
        return (patch.object(instalar, "DUNGEON_RELEASE", archive.as_uri()),
                patch.object(instalar, "DUNGEON_SHA256", hashlib.sha256(payload).hexdigest()))

    def test_modo_is_one_of_the_two_offices(self):
        self.assertEqual(parse("--modo", "dungeon").modo, "dungeon")
        self.assertIsNone(parse().modo)
        self.assertIn("invalid choice", parse("--modo", "tavern"))

    def test_the_dungeon_pin_is_the_release_zip_and_its_digest(self):
        # Verified on 2026-11-23 for the team-banners build: `gh release view v1.0.1
        # --repo icaceresc/dungeons-and-agents` lists this digest, and sha256sum of the
        # downloaded zip prints it.
        self.assertEqual(instalar.pin_for("dungeon"), (
            "https://github.com/icaceresc/dungeons-and-agents/releases/download/v1.0.1/"
            "dungeons-and-agents-v1.0.1-x86_64-pc-windows-msvc.zip",
            "be69b42c7aa399b5ffecd5f41f185a941324d4a852dd9176bf432a86cc17596f"))
        self.assertEqual(instalar.pin_for("oficina"), (instalar.RELEASE, instalar.SHA256))

    def test_dungeon_release_is_downloaded_verified_and_remembered(self):
        payload = release_zip()
        with Sandbox() as box:
            box.old_app({"kind": "pinned", "modo": "oficina", "sha256": instalar.SHA256})
            url, sha = self.dungeon_release(box, payload)
            with url, sha:
                instalar.install_binary(self.options(modo="dungeon"))
                self.assertEqual((box.app / "pixtuoid.exe").read_text(encoding="utf-8"), "fake pixtuoid.exe")
                self.assertEqual({k: box.origin()[k] for k in ("kind", "modo", "sha256")},
                                 {"kind": "pinned", "modo": "dungeon", "sha256": instalar.DUNGEON_SHA256})
                self.assertEqual(instalar.installed_mode(), "dungeon")

    def test_a_tampered_dungeon_zip_installs_nothing(self):
        with Sandbox() as box:
            box.old_app({"kind": "pinned", "modo": "oficina", "sha256": instalar.SHA256})
            url, _ = self.dungeon_release(box, release_zip())
            with url, patch.object(instalar, "DUNGEON_SHA256", SHA):
                with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                    instalar.install_binary(self.options(modo="dungeon"))
            self.assertEqual((box.app / "pixtuoid.exe").read_bytes(), b"old")

    def test_plain_run_honours_the_remembered_mode(self):
        payload = release_zip()
        with Sandbox() as box:
            url, sha = self.dungeon_release(box, payload)
            with url, sha:
                box.old_app({"kind": "pinned", "modo": "dungeon", "sha256": instalar.DUNGEON_SHA256})
                box.serve(b"")
                instalar.install_binary(self.options())
                self.assertEqual(box.downloads, [], "The remembered dungeon pin is current: nothing to do")
                self.assertEqual((box.app / "pixtuoid.exe").read_bytes(), b"old")

    def test_switching_back_to_the_office_installs_the_official_pin(self):
        payload = release_zip()
        with Sandbox() as box, patch.object(instalar, "SHA256", hashlib.sha256(payload).hexdigest()):
            box.old_app({"kind": "pinned", "modo": "dungeon", "sha256": "d" * 64})
            box.serve(payload)
            instalar.install_binary(self.options(modo="oficina"))
            self.assertEqual(box.downloads, [instalar.RELEASE])
            self.assertEqual(box.origin()["modo"], "oficina")

    def test_a_local_dungeon_build_is_recorded_in_its_mode(self):
        with Sandbox() as box:
            build = box.build()
            instalar.install_binary(self.options(local=str(build), modo="dungeon"))
            self.assertEqual({k: box.origin()[k] for k in ("kind", "modo")}, {"kind": "local", "modo": "dungeon"})
            # Asking for the mode it is already in keeps the custom build.
            box.serve(b"")
            instalar.install_binary(self.options(modo="dungeon"))
            self.assertEqual(box.downloads, [])
            self.assertEqual(box.origin()["kind"], "local")

    def test_an_install_made_before_modes_is_the_official_office(self):
        with Sandbox() as box:
            box.old_app({"kind": "pinned"})
            self.assertEqual(instalar.installed_mode(), "oficina")
            box.app.joinpath(instalar.ORIGIN).unlink()
            self.assertEqual(instalar.installed_mode(), "oficina")


if __name__ == "__main__":
    unittest.main()
