"""Regression coverage for the portable installer without network or live Qdrant."""

import argparse
import hashlib
import io
import json
import os
import subprocess
import tarfile
import urllib.error
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from knowledge_base import qdrant_boot
from scripts import install as installer


class Response:
    def __init__(self, data=b"", status=200, headers=None, broken_after=None):
        self.data = data
        self.status = status
        self.headers = headers or {}
        self.broken_after = broken_after
        self.reads = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _size=-1):
        self.reads += 1
        if self.broken_after is not None and self.reads > self.broken_after:
            raise urllib.error.URLError("connection interrupted")
        if not self.data:
            return b""
        value, self.data = self.data, b""
        return value


def _make_core_bundle(path: Path, snapshot=b"snapshot", include_data=False):
    source = path.parent / "developer_knowledge_v8.snapshot"
    source.write_bytes(snapshot)
    with tarfile.open(path, "w:gz") as archive:
        archive.add(source, arcname="snapshots/developer_knowledge_v8.snapshot")
        if include_data:
            archive.addfile(
                tarfile.TarInfo("data/markdown/keep.md"),
                io.BytesIO(b"bundle markdown"),
            )
            archive.addfile(
                tarfile.TarInfo("data/chunks/keep.json"),
                io.BytesIO(b"bundle chunks"),
            )


def test_qdrant_ready_uses_imported_urlopen_without_network(monkeypatch):
    monkeypatch.setattr(installer, "urlopen", lambda *_args, **_kwargs: Response())
    assert installer._qdrant_ready("http://127.0.0.1:6363")


def test_installer_script_imports_project_from_outside_its_working_directory(tmp_path):
    root = str(installer.ROOT)
    script = str(installer.ROOT / "scripts" / "install.py")
    command = (
        "import runpy,sys; "
        f"sys.path=[p for p in sys.path if p != {root!r}]; "
        f"runpy.run_path({script!r}, run_name='installer_import_test'); "
        "from knowledge_base.qdrant_boot import ensure_qdrant"
    )
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [installer.sys.executable, "-c", command],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_core_restore_ignores_unselected_philosophy_bundle(tmp_path, monkeypatch):
    bundle = tmp_path / "core.tar.gz"
    _make_core_bundle(bundle)
    restored = []
    monkeypatch.setattr(installer, "_collection_names", lambda _url: set())
    monkeypatch.setattr(installer, "_restore_snapshot", lambda _url, name, _path: restored.append(name))
    monkeypatch.setattr(
        installer,
        "_collection_info",
        lambda _url, name: {"points_count": 10} if name == "developer_knowledge_v8" else None,
    )
    monkeypatch.setattr(installer, "_aliases", lambda _url: {})
    monkeypatch.setattr(installer, "_change_alias", lambda *_args: None)
    manifest = {
        "collections": {
            "developer_knowledge_v8": {"bundle": "kb-core", "points": 10},
            "philosophy": {"bundle": "kb-philosophy", "points": 3},
        }
    }

    installer._restore_collections(
        manifest, {"kb-core": bundle}, "http://127.0.0.1:6363", set(), tmp_path,
    )

    assert restored == ["developer_knowledge_v8"]


def test_bundle_extract_skips_symlinked_markdown_and_chunks(tmp_path):
    bundle = tmp_path / "core.tar.gz"
    _make_core_bundle(bundle, include_data=True)
    external = tmp_path / "readonly-source"
    markdown = external / "markdown"
    chunks = external / "chunks"
    markdown.mkdir(parents=True)
    chunks.mkdir()
    (markdown / "keep.md").write_text("source markdown", encoding="utf-8")
    (chunks / "keep.json").write_text("source chunks", encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    (data / "markdown").symlink_to(markdown, target_is_directory=True)
    (data / "chunks").symlink_to(chunks, target_is_directory=True)

    installer._extract_bundle(bundle, tmp_path)

    assert (markdown / "keep.md").read_text(encoding="utf-8") == "source markdown"
    assert (chunks / "keep.json").read_text(encoding="utf-8") == "source chunks"
    assert (tmp_path / "snapshots" / "developer_knowledge_v8.snapshot").read_bytes() == b"snapshot"


def _write_local_manifest(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.json").write_text(json.dumps({
        "tag": "data-v8",
        "qdrant_version": "1.18.2",
        "bundles": {
            "kb-core": {"size": 1, "parts": []},
            "kb-philosophy": {"size": 1, "parts": []},
        },
        "collections": {
            "developer_knowledge_v8": {"bundle": "kb-core", "points": 10},
            "philosophy": {"bundle": "kb-philosophy", "points": 3},
        },
    }), encoding="utf-8")


def _install_args(tmp_path, local_release, edition="core"):
    return argparse.Namespace(
        dir=tmp_path,
        edition=edition,
        update=True,
        qdrant_port=6363,
        skip_models=True,
        skip_register=True,
        release_tag="data-v8",
        local_release=local_release,
    )


def test_update_fast_path_requires_same_edition_and_matching_collections(
    tmp_path, monkeypatch,
):
    release = tmp_path / "release"
    _write_local_manifest(release)
    (tmp_path / ".kb-install.json").write_text(json.dumps({
        "tag": "data-v8", "edition": "full",
    }), encoding="utf-8")
    binary = tmp_path / "bin" / "qdrant"
    binary.parent.mkdir()
    binary.write_bytes(b"qdrant")
    (binary.parent / "qdrant.version").write_text("1.18.2", encoding="utf-8")

    class StopAfterFastPath(Exception):
        pass

    monkeypatch.setattr(installer, "_check_download_space", lambda *_: (_ for _ in ()).throw(StopAfterFastPath()))
    monkeypatch.setattr(installer, "_collections_match", lambda *_: pytest.fail("edition mismatch used fast path"))
    with pytest.raises(StopAfterFastPath):
        installer.install(_install_args(tmp_path, release, "core"))


@pytest.mark.parametrize(
    ("state_tag", "state_edition"),
    [("older-tag", "core"), ("data-v8", "full")],
)
def test_update_fast_path_rejects_tag_or_edition_mismatch(
    tmp_path, monkeypatch, state_tag, state_edition,
):
    release = tmp_path / "release"
    _write_local_manifest(release)
    (tmp_path / ".kb-install.json").write_text(json.dumps({
        "tag": state_tag, "edition": state_edition,
    }), encoding="utf-8")
    binary = tmp_path / "bin" / "qdrant"
    binary.parent.mkdir()
    binary.write_bytes(b"qdrant")
    (binary.parent / "qdrant.version").write_text("1.18.2", encoding="utf-8")

    class ContinueInstall(Exception):
        pass

    monkeypatch.setattr(installer, "_check_download_space", lambda *_: (_ for _ in ()).throw(ContinueInstall()))
    monkeypatch.setattr(installer, "_collections_match", lambda *_: pytest.fail("mismatched state used fast path"))
    with pytest.raises(ContinueInstall):
        installer.install(_install_args(tmp_path, release, "core"))


def test_update_fast_path_rejects_missing_or_wrong_collection_counts(monkeypatch):
    collections = {"developer_knowledge_v8": {"points": 10}}
    monkeypatch.setattr(installer, "_qdrant_ready", lambda _url: True)
    counts = {"developer_knowledge_v8": 10}
    monkeypatch.setattr(
        installer,
        "_collection_info",
        lambda _url, name: {"points_count": counts[name]} if name in counts else None,
    )
    assert installer._collections_match("http://127.0.0.1:6363", collections)
    counts["developer_knowledge_v8"] = 9
    assert not installer._collections_match("http://127.0.0.1:6363", collections)
    counts.clear()
    assert not installer._collections_match("http://127.0.0.1:6363", collections)


def test_update_fast_path_requires_qdrant_binary_even_with_version_marker(
    tmp_path, monkeypatch,
):
    release = tmp_path / "release"
    _write_local_manifest(release)
    (tmp_path / ".kb-install.json").write_text(json.dumps({
        "tag": "data-v8", "edition": "core",
    }), encoding="utf-8")
    version_file = tmp_path / "bin" / "qdrant.version"
    version_file.parent.mkdir()
    version_file.write_text("1.18.2", encoding="utf-8")

    class ContinueInstall(Exception):
        pass

    monkeypatch.setattr(installer, "_collections_match", lambda *_: pytest.fail("missing binary used fast path"))
    monkeypatch.setattr(installer, "_check_download_space", lambda *_: (_ for _ in ()).throw(ContinueInstall()))
    with pytest.raises(ContinueInstall):
        installer.install(_install_args(tmp_path, release, "core"))


def test_update_fast_path_registers_requested_core_edition(tmp_path, monkeypatch):
    release = tmp_path / "release"
    _write_local_manifest(release)
    (tmp_path / ".kb-install.json").write_text(json.dumps({
        "tag": "data-v8", "edition": "core",
    }), encoding="utf-8")
    binary = tmp_path / "bin" / "qdrant"
    binary.parent.mkdir()
    binary.write_bytes(b"qdrant")
    (binary.parent / "qdrant.version").write_text("1.18.2", encoding="utf-8")
    registered = []
    def collections_match(_url, collections):
        assert set(collections) == {"developer_knowledge_v8"}
        return True

    monkeypatch.setattr(installer, "_collections_match", collections_match)
    monkeypatch.setattr(installer, "_register", lambda _dir, edition, *_: registered.append(edition))
    monkeypatch.setattr(installer, "_write_install_state", lambda *_: None)

    args = _install_args(tmp_path, release, "core")
    args.skip_register = False
    installer.install(args)

    assert registered == ["core"]


def test_github_download_resumes_partial_file_and_retries_five_times(tmp_path, monkeypatch):
    content = b"abcdef"
    requests = []
    sleeps = []

    class Opener:
        def __init__(self):
            self.calls = 0

        def open(self, request, timeout):
            self.calls += 1
            requests.append((dict(request.header_items()), timeout))
            if self.calls == 1:
                return Response(b"abc", broken_after=1)
            if self.calls < 5:
                raise urllib.error.URLError("temporary failure")
            assert request.get_header("Range") == "bytes=3-"
            return Response(
                b"def", status=206,
                headers={"Content-Range": "bytes 3-5/6", "Content-Length": "3"},
            )

    opener = Opener()
    monkeypatch.setattr(installer, "_opener", lambda: opener)
    monkeypatch.setattr(installer.time, "sleep", sleeps.append)
    output = installer._download_resumable(
        "https://example.invalid/part", tmp_path / "part",
        expected_size=len(content), expected_sha256=hashlib.sha256(content).hexdigest(),
    )

    assert output.read_bytes() == content
    assert not output.with_name("part.tmp").exists()
    assert sleeps == [1, 2, 4, 8]
    assert requests[1][0].get("Range") == "bytes=3-"


def test_download_restarts_from_zero_when_range_is_ignored(tmp_path, monkeypatch):
    output = tmp_path / "part"
    output.with_name("part.tmp").write_bytes(b"old")
    seen = []

    class Opener:
        def open(self, request, timeout):
            seen.append(request.get_header("Range"))
            return Response(b"fresh")

    monkeypatch.setattr(installer, "_opener", lambda: Opener())
    assert installer._download_resumable(
        "https://example.invalid/part", output, expected_size=5,
    ).read_bytes() == b"fresh"
    assert seen == ["bytes=3-"]


def test_progress_is_multiline_in_logs_and_carriage_return_on_tty(monkeypatch, tmp_path):
    class Log(io.StringIO):
        def isatty(self):
            return False

    log = Log()
    monkeypatch.setattr(installer.sys, "stderr", log)
    installer._stream_response(io.BytesIO(b"x" * 100), tmp_path / "log", 100, publish=False)
    assert "Downloaded 10%" in log.getvalue()
    assert "Downloaded 100%" in log.getvalue()

    class Tty(Log):
        def isatty(self):
            return True

    tty = Tty()
    monkeypatch.setattr(installer.sys, "stderr", tty)
    installer._stream_response(io.BytesIO(b"x"), tmp_path / "tty", publish=False)
    assert "\rDownloaded" in tty.getvalue()


def test_qdrant_binary_updates_version_and_stops_owned_instance(tmp_path, monkeypatch):
    binary = tmp_path / "bin" / "qdrant"
    binary.parent.mkdir()
    binary.write_bytes(b"old-binary")
    (binary.parent / "qdrant.version").write_text("1.18.1", encoding="utf-8")
    archive_content = io.BytesIO()
    with zipfile.ZipFile(archive_content, "w") as archive:
        archive.writestr("qdrant", b"new-binary")

    def make_archive(_url, destination, *_args, **_kwargs):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive_content.getvalue())
        return destination

    stopped = []
    monkeypatch.setattr(installer, "_qdrant_asset_name", lambda: "qdrant-test.zip")
    monkeypatch.setattr(installer, "_download_resumable", make_archive)
    monkeypatch.setattr(installer, "_stop_owned_qdrant", lambda *args: stopped.append(args))
    monkeypatch.setattr(installer, "_qdrant_ready", lambda _url: False)

    result = installer._download_qdrant("1.18.2", tmp_path, port=6363)

    assert result.read_bytes() == b"new-binary"
    assert (binary.parent / "qdrant.version").read_text().strip() == "1.18.2"
    assert len(stopped) == 1
    assert stopped[0][1] == binary


def test_qdrant_binary_is_not_replaced_when_owned_process_fails_to_stop(
    tmp_path, monkeypatch,
):
    binary = tmp_path / "bin" / "qdrant"
    binary.parent.mkdir()
    binary.write_bytes(b"old-binary")
    version_file = binary.parent / "qdrant.version"
    version_file.write_text("1.18.1", encoding="utf-8")
    archive_content = io.BytesIO()
    with zipfile.ZipFile(archive_content, "w") as archive:
        archive.writestr("qdrant", b"new-binary")

    def make_archive(_url, destination, *_args, **_kwargs):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive_content.getvalue())

    monkeypatch.setattr(installer, "_qdrant_asset_name", lambda: "qdrant-test.zip")
    monkeypatch.setattr(installer, "_download_resumable", make_archive)
    monkeypatch.setattr(installer, "_stop_owned_qdrant", lambda *_: False)
    monkeypatch.setattr(installer, "_qdrant_ready", lambda _url: False)

    with pytest.raises(RuntimeError, match="Could not stop the Qdrant process"):
        installer._download_qdrant("1.18.2", tmp_path, port=6363)

    assert binary.read_bytes() == b"old-binary"
    assert version_file.read_text().strip() == "1.18.1"


def test_stop_qdrant_only_when_pid_record_matches_its_storage(tmp_path, monkeypatch):
    binary = tmp_path / "bin" / "qdrant"
    storage = tmp_path / "qdrant-storage"
    storage.mkdir()
    pid_file = storage / ".kb-qdrant-process.json"
    pid_file.write_text(json.dumps({
        "pid": 123,
        "binary": str(binary.resolve()),
        "storage": str(storage.resolve()),
        "port": 6363,
    }), encoding="utf-8")
    signals = []
    running = iter((True, False, False, False))
    monkeypatch.setattr(installer, "_pid_is_running", lambda _pid: next(running))
    monkeypatch.setattr(installer, "_process_command", lambda _pid: str(binary.resolve()))
    monkeypatch.setattr(installer.os, "kill", lambda *args: signals.append(args))

    assert installer._stop_owned_qdrant(tmp_path, binary)
    assert signals == [(123, 15)]

    pid_file.write_text(json.dumps({"pid": 123, "storage": "/other/storage", "port": 6363, "binary": str(binary.resolve())}), encoding="utf-8")
    assert not installer._stop_owned_qdrant(tmp_path, binary)


def test_disk_checks_fail_before_replacing_existing_collection(tmp_path, monkeypatch):
    bundle = tmp_path / "core.tar.gz"
    _make_core_bundle(bundle, b"snapshot-payload")
    monkeypatch.setattr(installer, "_collection_names", lambda _url: {"developer_knowledge_v8"})
    monkeypatch.setattr(installer.shutil, "disk_usage", lambda _path: installer.shutil._ntuple_diskusage(100, 90, 10))
    deletes = []
    monkeypatch.setattr(installer, "_qdrant_request", lambda *args, **_kwargs: deletes.append(args))

    with pytest.raises(RuntimeError, match="existing collections were left intact"):
        installer._restore_collections(
            {"collections": {"developer_knowledge_v8": {"bundle": "kb-core", "points": 10}}},
            {"kb-core": bundle}, "http://127.0.0.1:6363", set(), tmp_path,
        )

    assert deletes == []


def test_download_space_estimate_covers_selected_bundles(tmp_path, monkeypatch):
    monkeypatch.setattr(installer.shutil, "disk_usage", lambda _path: installer.shutil._ntuple_diskusage(100, 50, 100))
    with pytest.raises(RuntimeError, match="selected release bundles"):
        installer._check_download_space(tmp_path, [{"size": 100}])


def test_snapshot_upload_ignores_proxy_environment(tmp_path, monkeypatch):
    import httpx

    snapshot = tmp_path / "snapshot"
    snapshot.write_bytes(b"payload")
    options = {}

    class Client:
        def __init__(self, **kwargs):
            options.update(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def post(self, *_args, **_kwargs):
            return SimpleNamespace(raise_for_status=lambda: None)

    monkeypatch.setattr(httpx, "Client", Client)
    installer._restore_snapshot("http://127.0.0.1:6363", "developer_knowledge_v8", snapshot)
    assert options["trust_env"] is False


def test_registered_claude_process_uses_edition_and_scrubbed_environment(tmp_path, monkeypatch):
    for name in ("KB_GH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.setenv(name, "test-secret")
    calls = []
    monkeypatch.setattr(installer.shutil, "which", lambda _name: "/usr/bin/claude")

    def run_claude(_exe, arguments, **options):
        calls.append((arguments, options.get("env")))
        return subprocess.CompletedProcess([], 0, stdout="")

    monkeypatch.setattr(installer, "_run_claude", run_claude)
    installer._register(tmp_path, "core", 6363, tmp_path / "bin" / "qdrant")

    add_args, child_env = calls[-1]
    assert "KB_EDITION=core" in add_args
    assert all(name not in child_env for name in ("KB_GH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"))


def test_install_clears_tokens_after_selected_release_parts_download(tmp_path, monkeypatch):
    for name in ("KB_GH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.setenv(name, "test-secret")
    manifest = {
        "tag": "data-v8",
        "qdrant_version": "1.18.2",
        "bundles": {"kb-core": {"size": 1, "parts": [{"name": "core.part00"}]}},
        "collections": {"developer_knowledge_v8": {"bundle": "kb-core", "points": 10}},
    }
    seen_tokens = []
    monkeypatch.setattr(installer, "_release_files", lambda *_: (manifest, {}))
    monkeypatch.setattr(
        installer,
        "download_part",
        lambda _part, _dest, _local, _assets, token: seen_tokens.append(token) or tmp_path / "part",
    )

    def assemble(_bundle, _part_dir, _destination):
        assert all(name not in os.environ for name in ("KB_GH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"))
        return tmp_path / "archive"

    def download_qdrant(_version, _install_dir, _port):
        assert all(name not in os.environ for name in ("KB_GH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"))
        return tmp_path / "bin" / "qdrant"

    monkeypatch.setattr(installer, "assemble_bundle", assemble)
    monkeypatch.setattr(installer, "_check_download_space", lambda *_: None)
    monkeypatch.setattr(installer, "_download_qdrant", download_qdrant)
    monkeypatch.setattr(installer, "_prepare_qdrant", lambda *_: ("http://127.0.0.1:6363", {"developer_knowledge_v8"}))
    monkeypatch.setattr(installer, "_restore_collections", lambda *_: None)
    monkeypatch.setattr(installer, "_smoke_query", lambda *_: None)
    monkeypatch.setattr(installer, "_write_install_state", lambda *_: None)
    args = _install_args(tmp_path, tmp_path / "release", "core")
    args.update = False

    installer.install(args)

    assert seen_tokens == ["test-secret"]


def test_qdrant_boot_uses_storage_cwd_and_scrubs_tokens(tmp_path, monkeypatch):
    storage = tmp_path / "qdrant-storage"
    calls = []
    monkeypatch.setenv("KB_QDRANT_URL", "http://127.0.0.1:6363")
    monkeypatch.setenv("KB_QDRANT_BIN", str(tmp_path / "bin" / "qdrant"))
    monkeypatch.setenv("KB_QDRANT_STORAGE", str(storage))
    for name in ("KB_GH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.setenv(name, "test-secret")
    ready = iter((False, True))
    monkeypatch.setattr(qdrant_boot, "_is_ready", lambda _url: next(ready))
    monkeypatch.setattr(qdrant_boot.subprocess, "Popen", lambda _args, **kwargs: calls.append(kwargs) or SimpleNamespace(pid=123))

    qdrant_boot.ensure_qdrant()

    options = calls[0]
    assert Path(options["cwd"]) == storage
    assert all(name not in options["env"] for name in ("KB_GH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"))
    metadata = json.loads((storage / ".kb-qdrant-process.json").read_text())
    assert metadata["pid"] == 123


def test_proxy_and_secure_prompt_documentation_are_current():
    root = Path(__file__).resolve().parent.parent
    powershell = (root / "install.ps1").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    project = (root / "pyproject.toml").read_text(encoding="utf-8")
    ignore = (root / ".gitignore").read_text(encoding="utf-8")

    assert powershell.count("Invoke-WebRequest") == 1
    assert "Invoke-WebRequest -Uri $zipUrl -Headers $headers -OutFile $tempZip -UseBasicParsing @proxyArgs" in powershell
    assert "Invoke-RestMethod -Uri \"https://astral.sh/uv/install.ps1\" @proxyArgs" in powershell
    assert "DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials" in powershell
    assert '$secureToken = Read-Host "Enter GitHub Token" -AsSecureString' in readme
    assert "PtrToStringBSTR($bstr)" in readme
    assert 'requires-python = ">=3.11.4"' in project
    assert ".qdrant-initialized" in ignore
