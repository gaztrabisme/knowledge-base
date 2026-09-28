#!/usr/bin/env python3
"""Install the knowledge-base data, a local Qdrant binary, and Claude MCP entry."""

from __future__ import annotations

import argparse
import hashlib
from http.client import HTTPException
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GITHUB_API = "https://api.github.com/repos/gaztrabisme/knowledge-base"
GITHUB_HEADERS = {"X-GitHub-Api-Version": "2022-11-28"}
STREAM_SIZE = 8 * 1024 * 1024
COLLECTION_NAMES = {
    "kb-core": "developer_knowledge_v8",
    "kb-philosophy": "philosophy",
}


class SafeRedirectHandler(HTTPRedirectHandler):
    """Do not forward GitHub API credentials to a release asset host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            old_host = urlsplit(req.full_url).netloc.casefold()
            new_host = urlsplit(newurl).netloc.casefold()
            if old_host != new_host:
                redirected.remove_header("Authorization")
                redirected.unredirected_hdrs.pop("Authorization", None)
        return redirected


def _opener():
    return build_opener(SafeRedirectHandler())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(STREAM_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def _stream_response(
    response,
    output: Path,
    expected_size: int | None = None,
    *,
    append: bool = False,
    total_size: int | None = None,
    publish: bool = True,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    initial_size = temporary.stat().st_size if append and temporary.exists() else 0
    mode = "ab" if append else "wb"
    total = initial_size
    display_total = total_size or expected_size
    next_percent = (total * 100 // display_total // 10 + 1) * 10 if display_total else 110
    is_tty = bool(getattr(sys.stderr, "isatty", lambda: False)())
    try:
        with temporary.open(mode) as destination:
            while block := response.read(STREAM_SIZE):
                destination.write(block)
                total += len(block)
                if is_tty:
                    print(f"\rDownloaded {total:,} bytes", end="", file=sys.stderr, flush=True)
                elif display_total:
                    downloaded_percent = total * 100 // display_total
                    while downloaded_percent >= next_percent and next_percent <= 100:
                        print(f"Downloaded {next_percent}% ({total:,} bytes)", file=sys.stderr)
                        next_percent += 10
    except Exception:
        if is_tty:
            print(file=sys.stderr)
        raise
    if is_tty:
        print(file=sys.stderr)
    elif not display_total:
        print(f"Downloaded {total:,} bytes", file=sys.stderr)
    if expected_size is not None and temporary.stat().st_size != expected_size:
        raise ValueError(
            f"Downloaded {temporary.stat().st_size} bytes; expected {expected_size}"
        )
    if publish:
        os.replace(temporary, output)
    return temporary


def _response_total(response, expected_size: int | None, offset: int) -> int | None:
    if expected_size is not None:
        return expected_size
    content_range = response.headers.get("Content-Range", "")
    match = re.search(r"/([0-9]+)$", content_range)
    if match:
        return int(match.group(1))
    content_length = response.headers.get("Content-Length")
    return offset + int(content_length) if content_length else None


def _download_resumable(
    url: str,
    output: Path,
    headers: dict[str, str] | None = None,
    *,
    timeout: int = 120,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
    attempts: int = 5,
) -> Path:
    """Download to a resumable .tmp file, publishing only verified content."""
    temporary = output.with_name(output.name + ".tmp")
    output.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(attempts):
        offset = temporary.stat().st_size if temporary.exists() else 0
        if expected_size is not None and offset >= expected_size:
            if offset == expected_size and (
                expected_sha256 is None or _sha256(temporary) == expected_sha256
            ):
                os.replace(temporary, output)
                return output
            temporary.write_bytes(b"")
            offset = 0

        request_headers = dict(headers or {})
        if offset:
            request_headers["Range"] = f"bytes={offset}-"
        request = Request(url, headers=request_headers, method="GET")
        try:
            with _opener().open(request, timeout=timeout) as response:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()
                if offset and status == 206:
                    range_match = re.match(
                        r"bytes ([0-9]+)-", response.headers.get("Content-Range", ""),
                    )
                    if not range_match or int(range_match.group(1)) != offset:
                        temporary.write_bytes(b"")
                        raise ValueError("Server returned a mismatched Content-Range")
                append = bool(offset and status == 206)
                base = offset if append else 0
                _stream_response(
                    response,
                    output,
                    expected_size=expected_size,
                    append=append,
                    total_size=_response_total(response, expected_size, base),
                    publish=False,
                )
            if expected_sha256 and _sha256(temporary) != expected_sha256:
                temporary.write_bytes(b"")
                raise ValueError(f"SHA-256 mismatch while downloading {output.name}")
            os.replace(temporary, output)
            return output
        except (HTTPError, URLError, OSError, TimeoutError, ValueError, EOFError, HTTPException) as exc:
            if isinstance(exc, HTTPError) and exc.code == 416 and temporary.exists():
                temporary.write_bytes(b"")
            if attempt + 1 == attempts:
                raise RuntimeError(
                    f"Download failed after {attempts} attempts: {url}: {exc}"
                ) from exc
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def _clear_download_tokens() -> None:
    for name in ("KB_GH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        os.environ.pop(name, None)


def _child_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in ("KB_GH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        environment.pop(name, None)
    return environment


def _github_json(path: str, token: str | None) -> dict:
    headers = {**GITHUB_HEADERS, "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{GITHUB_API}{path}", headers=headers)
    try:
        with _opener().open(request, timeout=60) as response:
            return json.load(response)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"GitHub API request failed: {exc}") from exc


def _github_asset(
    asset_url: str,
    output: Path,
    token: str | None,
    *,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
) -> None:
    headers = {"Accept": "application/octet-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        _download_resumable(
            asset_url,
            output,
            headers,
            timeout=120,
            expected_size=expected_size,
            expected_sha256=expected_sha256,
        )
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"GitHub release asset download failed: {exc}") from exc


def download_part(
    part: dict,
    destination: Path,
    local_release: Path | None,
    assets: dict[str, dict],
    token: str | None,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and _sha256(destination) == part["sha256"]:
        print(f"Already verified: {part['name']}", file=sys.stderr)
        return destination

    if local_release is not None:
        source = local_release / part["name"]
        if not source.is_file():
            raise FileNotFoundError(f"Release part not found: {source}")
        with source.open("rb") as response:
            temporary = _stream_response(
                response,
                destination,
                expected_size=int(part["size"]),
                publish=False,
            )
        if _sha256(temporary) != part["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {part['name']}")
        os.replace(temporary, destination)
    else:
        asset = assets.get(part["name"])
        if asset is None:
            raise FileNotFoundError(f"GitHub release has no asset named {part['name']}")
        _github_asset(
            asset["url"],
            destination,
            token,
            expected_size=int(part["size"]),
            expected_sha256=part["sha256"],
        )

    actual = _sha256(destination)
    if actual != part["sha256"]:
        destination.unlink(missing_ok=True)
        raise ValueError(f"SHA-256 mismatch for {part['name']}")
    if destination.stat().st_size != int(part["size"]):
        destination.unlink(missing_ok=True)
        raise ValueError(f"Size mismatch for {part['name']}")
    return destination


def assemble_bundle(bundle: dict, part_dir: Path, destination: Path) -> Path:
    """Verify parts and the combined archive before atomically publishing it."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    whole_digest = hashlib.sha256()
    total = 0
    try:
        with temporary.open("wb") as output:
            for part in bundle["parts"]:
                part_path = part_dir / part["name"]
                if not part_path.is_file():
                    raise FileNotFoundError(f"Release part not found: {part_path}")
                if _sha256(part_path) != part["sha256"]:
                    raise ValueError(f"SHA-256 mismatch for {part['name']}")
                if part_path.stat().st_size != int(part["size"]):
                    raise ValueError(f"Size mismatch for {part['name']}")
                with part_path.open("rb") as source:
                    while block := source.read(STREAM_SIZE):
                        output.write(block)
                        whole_digest.update(block)
                        total += len(block)
        if total != int(bundle["size"]):
            raise ValueError(f"Bundle size mismatch: got {total}, expected {bundle['size']}")
        if whole_digest.hexdigest() != bundle["sha256"]:
            raise ValueError("Whole-bundle SHA-256 mismatch")
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def _release_files(
    tag: str, local_release: Path | None, token: str | None, cache_dir: Path,
) -> tuple[dict, dict[str, dict]]:
    if local_release is not None:
        manifest_path = local_release / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("tag") != tag:
            raise ValueError(f"Local release tag is {manifest.get('tag')!r}, expected {tag!r}")
        return manifest, {}

    release = _github_json(f"/releases/tags/{quote(tag, safe='')}", token)
    assets = {asset["name"]: asset for asset in release.get("assets", [])}
    manifest_asset = assets.get("manifest.json")
    if manifest_asset is None:
        raise FileNotFoundError(f"GitHub release {tag} has no manifest.json asset")
    manifest_path = cache_dir / f"manifest-{tag}.json"
    # Keep metadata with the install and never persist credentials.
    _github_asset(manifest_asset["url"], manifest_path, token)
    return json.loads(manifest_path.read_text(encoding="utf-8")), assets


def _qdrant_asset_name() -> str:
    system = platform.system()
    machine = platform.machine().casefold()
    if system == "Windows" and machine in {"amd64", "x86_64"}:
        return "qdrant-x86_64-pc-windows-msvc.zip"
    if system == "Darwin" and machine in {"arm64", "aarch64"}:
        return "qdrant-aarch64-apple-darwin.tar.gz"
    if system == "Darwin" and machine in {"amd64", "x86_64"}:
        return "qdrant-x86_64-apple-darwin.tar.gz"
    if system == "Linux" and machine in {"amd64", "x86_64"}:
        return "qdrant-x86_64-unknown-linux-gnu.tar.gz"
    if system == "Linux" and machine in {"arm64", "aarch64"}:
        return "qdrant-aarch64-unknown-linux-musl.tar.gz"
    raise RuntimeError(f"Unsupported Qdrant platform: {system} {platform.machine()}")


def _download_qdrant(version: str, install_dir: Path, port: int = 6333) -> Path:
    asset_name = _qdrant_asset_name()
    executable_name = "qdrant.exe" if os.name == "nt" else "qdrant"
    binary = install_dir / "bin" / executable_name
    version_file = binary.parent / "qdrant.version"
    try:
        installed_version = version_file.read_text(encoding="utf-8").strip()
    except OSError:
        installed_version = None
    if binary.is_file() and installed_version == version:
        return binary

    replacing = binary.is_file()

    cache_dir = install_dir / ".kb-download"
    cache_dir.mkdir(parents=True, exist_ok=True)
    archive_path = cache_dir / f"qdrant-{version}-{asset_name}"
    if not archive_path.is_file():
        url = f"https://github.com/qdrant/qdrant/releases/download/v{version}/{asset_name}"
        _download_resumable(url, archive_path, timeout=120)

    extract_dir = cache_dir / f"qdrant-{version}-extract"
    shutil.rmtree(extract_dir, ignore_errors=True)
    extract_dir.mkdir(parents=True)
    if asset_name.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                name = PurePosixPath(member.filename)
                if name.is_absolute() or ".." in name.parts:
                    raise ValueError(f"Unsafe path in Qdrant archive: {member.filename}")
            archive.extractall(extract_dir)
    else:
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(extract_dir, filter="data")

    candidates = [path for path in extract_dir.rglob(executable_name) if path.is_file()]
    if not candidates:
        raise FileNotFoundError(f"{executable_name} missing from Qdrant asset {asset_name}")
    binary.parent.mkdir(parents=True, exist_ok=True)
    if replacing:
        stopped = _stop_owned_qdrant(install_dir, binary)
        if stopped is False:
            raise RuntimeError(
                "Could not stop the Qdrant process recorded for this storage directory; "
                "refusing to replace its binary"
            )
        if _qdrant_ready(f"http://127.0.0.1:{port}"):
            raise RuntimeError(
                f"Qdrant is still running on port {port}, and its process is not "
                "confirmed stopped for this storage directory; refusing to replace its binary"
            )
    shutil.copy2(candidates[0], binary)
    if os.name != "nt":
        binary.chmod(binary.stat().st_mode | 0o111)
    version_file.write_text(f"{version}\n", encoding="utf-8")
    archive_path.unlink(missing_ok=True)
    shutil.rmtree(extract_dir, ignore_errors=True)
    return binary


def _qdrant_request(url: str, method: str = "GET", data: bytes | None = None) -> dict:
    request = Request(url, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urlopen(request, timeout=60) as response:
            payload = response.read()
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Qdrant request failed: {method} {urlsplit(url).path}: {exc}") from exc
    if not payload:
        return {}
    body = json.loads(payload)
    return body.get("result", body)


def _qdrant_ready(base_url: str) -> bool:
    url = f"{base_url.rstrip('/')}/readyz"
    try:
        with urlopen(url, timeout=2) as response:
            return response.status == 200
    except (OSError, HTTPError, URLError, ValueError):
        return False


def _process_command(pid: int) -> str | None:
    if os.name == "nt":
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}').CommandLine"],
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            check=False,
        )
    return result.stdout.strip() or None


def _pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _stop_owned_qdrant(install_dir: Path, binary: Path) -> bool | None:
    storage = install_dir / "qdrant-storage"
    pid_file = storage / ".kb-qdrant-process.json"
    try:
        process = json.loads(pid_file.read_text(encoding="utf-8"))
        pid = int(process["pid"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if (
        process.get("storage") != str(storage.resolve())
        or process.get("binary") != str(binary.resolve())
    ):
        return None
    if not _pid_is_running(pid):
        pid_file.unlink(missing_ok=True)
        return None
    command = _process_command(pid)
    if not command or str(binary.resolve()) not in command:
        return None
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T"], check=False)
    else:
        os.kill(pid, 15)
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and _pid_is_running(pid):
        time.sleep(0.2)
    if _pid_is_running(pid):
        command = _process_command(pid)
        if not command or str(binary.resolve()) not in command:
            return None
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
        else:
            os.kill(pid, 9)
    if _pid_is_running(pid):
        return False
    pid_file.unlink(missing_ok=True)
    return True


def _collection_info(base_url: str, name: str) -> dict | None:
    try:
        result = _qdrant_request(
            f"{base_url.rstrip('/')}/collections/{quote(name, safe='')}",
        )
    except RuntimeError as exc:
        if "404" in str(exc):
            return None
        raise
    return result


def _collection_names(base_url: str) -> set[str]:
    result = _qdrant_request(f"{base_url.rstrip('/')}/collections")
    return {item["name"] for item in result.get("collections", [])}


def _aliases(base_url: str) -> dict[str, str]:
    result = _qdrant_request(f"{base_url.rstrip('/')}/aliases")
    return {
        item["alias_name"]: item["collection_name"]
        for item in result.get("aliases", [])
    }


def _change_alias(base_url: str, actions: list[dict]) -> None:
    body = json.dumps({"actions": actions}).encode("utf-8")
    _qdrant_request(f"{base_url.rstrip('/')}/collections/aliases", "POST", body)


def _extract_bundle(bundle_archive: Path, install_dir: Path) -> None:
    """Extract bundle data without following caller-provided data symlinks."""
    skip_roots = []
    for relative in (PurePosixPath("data/markdown"), PurePosixPath("data/chunks")):
        destination = install_dir
        has_symlink_parent = False
        for part in relative.parts:
            destination = destination / part
            has_symlink_parent |= destination.is_symlink()
        if has_symlink_parent:
            skip_roots.append(relative)

    with tarfile.open(bundle_archive, "r:gz") as archive:
        members = (
            member
            for member in archive
            if not any(
                root == PurePosixPath(member.name)
                or root in PurePosixPath(member.name).parents
                for root in skip_roots
            )
        )
        archive.extractall(install_dir, members=members, filter="data")


def _restore_snapshot(base_url: str, collection: str, snapshot: Path) -> None:
    import httpx

    boundary = uuid.uuid4().hex
    filename = snapshot.name
    prefix = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="snapshot"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("ascii")
    suffix = f"\r\n--{boundary}--\r\n".encode("ascii")
    content_length = len(prefix) + snapshot.stat().st_size + len(suffix)

    def body():
        yield prefix
        with snapshot.open("rb") as source:
            while block := source.read(STREAM_SIZE):
                yield block
        yield suffix

    url = (
        f"{base_url.rstrip('/')}/collections/{quote(collection, safe='')}"
        "/snapshots/upload?priority=snapshot&wait=true"
    )
    # httpx accepts an iterator body; requests' `files=` multipart encoder buffers
    # the full snapshot before sending it, so it cannot safely upload multi-GB files.
    with httpx.Client(timeout=httpx.Timeout(1800, connect=30), trust_env=False) as client:
        response = client.post(
            url,
            content=body(),
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(content_length),
            },
        )
        response.raise_for_status()


def _install_marker(install_dir: Path, port: int) -> Path:
    storage_dir = install_dir / "qdrant-storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    marker = storage_dir / ".kb-owner.json"
    marker.write_text(json.dumps({
        "install_dir": str(install_dir.resolve()),
        "port": port,
    }, indent=2) + "\n", encoding="utf-8")
    return marker


def _owns_running_store(marker: Path, install_dir: Path, port: int) -> bool:
    try:
        value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (
        value.get("install_dir") == str(install_dir.resolve())
        and value.get("port") == port
    )


def _prepare_qdrant(
    install_dir: Path,
    port: int,
    binary: Path,
    collections: dict,
) -> tuple[str, set[str]]:
    base_url = f"http://127.0.0.1:{port}"
    marker = install_dir / "qdrant-storage" / ".kb-owner.json"
    already_ready = _qdrant_ready(base_url)
    owned = _owns_running_store(marker, install_dir, port)
    if already_ready and not owned:
        counts_match = True
        for name, expected in collections.items():
            info = _collection_info(base_url, name)
            if info is None or int(info.get("points_count", -1)) != int(expected["points"]):
                counts_match = False
                break
        if not counts_match:
            raise RuntimeError(
                f"Qdrant already answers on port {port}, but it is not this install's "
                "storage and its collections do not match the release point counts"
            )
        return base_url, set(collections)

    if not already_ready:
        _install_marker(install_dir, port)
    os.environ["KB_QDRANT_URL"] = base_url
    os.environ["KB_QDRANT_BIN"] = str(binary)
    os.environ["KB_QDRANT_STORAGE"] = str(install_dir / "qdrant-storage")
    from knowledge_base.qdrant_boot import ensure_qdrant

    ensure_qdrant()
    matching = set()
    for name, expected in collections.items():
        info = _collection_info(base_url, name)
        if info is not None and int(info.get("points_count", -1)) == int(expected["points"]):
            matching.add(name)
    return base_url, matching


def _remove_alias_for(base_url: str, collection: str) -> None:
    aliases = _aliases(base_url)
    actions = [
        {"delete_alias": {"alias_name": alias}}
        for alias, target in aliases.items()
        if alias == "developer_knowledge" or target == collection
    ]
    if actions:
        _change_alias(base_url, actions)


def _restore_collections(
    manifest: dict,
    bundle_archives: dict[str, Path],
    base_url: str,
    matching: set[str],
    install_dir: Path,
) -> None:
    target_names = [
        name
        for name, collection_info in manifest["collections"].items()
        if name in COLLECTION_NAMES.values()
        and collection_info.get("bundle") in bundle_archives
    ]
    restore_names = set(target_names) - matching
    snapshots = {}
    for bundle_name, collection in COLLECTION_NAMES.items():
        if collection not in restore_names:
            continue
        _extract_bundle(bundle_archives[bundle_name], install_dir)
        snapshot = install_dir / "snapshots" / f"{collection}.snapshot"
        if not snapshot.is_file():
            raise FileNotFoundError(f"Snapshot missing from release bundle: {snapshot}")
        snapshots[collection] = snapshot

    existing = _collection_names(base_url)
    replacing = [name for name in target_names if name in existing and name not in matching]
    required_bytes = sum(snapshots[name].stat().st_size * 2 for name in replacing)
    free_bytes = shutil.disk_usage(install_dir).free
    if free_bytes < required_bytes:
        required_gib = required_bytes / (1024 ** 3)
        free_gib = free_bytes / (1024 ** 3)
        raise RuntimeError(
            f"Not enough free disk space to replace Qdrant collections: "
            f"need at least {required_gib:.2f} GiB for snapshot and restored data, "
            f"have {free_gib:.2f} GiB; the existing collections were left intact"
        )
    for name in target_names:
        if name in matching:
            continue
        if name in existing:
            if name == "developer_knowledge_v8":
                _remove_alias_for(base_url, name)
            _qdrant_request(
                f"{base_url}/collections/{quote(name, safe='')}", method="DELETE",
            )

    for bundle_name, collection in COLLECTION_NAMES.items():
        if collection not in restore_names:
            continue
        snapshot = snapshots[collection]
        _restore_snapshot(base_url, collection, snapshot)
        info = _collection_info(base_url, collection)
        expected = int(manifest["collections"][collection]["points"])
        if info is None or int(info.get("points_count", -1)) != expected:
            actual = None if info is None else info.get("points_count")
            raise RuntimeError(
                f"Restored {collection} with {actual} points; expected {expected}"
            )
        snapshot.unlink()

    if "developer_knowledge_v8" in target_names:
        aliases = _aliases(base_url)
        actions = []
        if "developer_knowledge" in aliases:
            actions.append({"delete_alias": {"alias_name": "developer_knowledge"}})
        actions.append({"create_alias": {
            "collection_name": "developer_knowledge_v8",
            "alias_name": "developer_knowledge",
        }})
        _change_alias(base_url, actions)


def _warm_models(edition: str) -> None:
    from fastembed import SparseTextEmbedding
    from sentence_transformers import CrossEncoder

    from knowledge_base.config import BM25_MODEL, EMBEDDING_MODEL, RERANKER_MODEL
    from knowledge_base.embedder import load_model

    print(f"Loading embedding model {EMBEDDING_MODEL}...", file=sys.stderr)
    load_model(EMBEDDING_MODEL)
    print(f"Loading sparse model {BM25_MODEL}...", file=sys.stderr)
    SparseTextEmbedding(BM25_MODEL)
    print(f"Loading reranker {RERANKER_MODEL}...", file=sys.stderr)
    CrossEncoder(RERANKER_MODEL, trust_remote_code=True)
    if edition == "full":
        philosophy_ranker = "BAAI/bge-reranker-v2-m3"
        print(f"Loading philosophy reranker {philosophy_ranker}...", file=sys.stderr)
        CrossEncoder(philosophy_ranker, trust_remote_code=True, max_length=512)


def _smoke_query(edition: str) -> None:
    from knowledge_base.search import get_client, hybrid_search

    print('Smoke query: "how does MVCC work in PostgreSQL"', file=sys.stderr)
    results = hybrid_search(
        "how does MVCC work in PostgreSQL",
        client=get_client(),
        top_k=3,
    )
    print("Technical books: " + ", ".join(result.book for result in results))
    if edition == "full":
        from knowledge_base.server import search_philosophy

        philosophy_results = search_philosophy("What is virtue?", top_k=1)
        print("Philosophy results: " + json.dumps(philosophy_results, ensure_ascii=False))


def _register(install_dir: Path, edition: str, port: int, binary: Path) -> None:
    claude = shutil.which("claude")
    uv = "uv"
    command = [
        "claude", "mcp", "add", "knowledge-base", "--scope", "user",
        "-e", f"KB_EDITION={edition}",
        "-e", f"KB_QDRANT_URL=http://127.0.0.1:{port}",
        "-e", f"KB_QDRANT_BIN={binary}",
        "-e", f"KB_QDRANT_STORAGE={install_dir / 'qdrant-storage'}",
        "--", uv, "run", "--project", str(install_dir), "--directory",
        str(install_dir), "python", "-m", "knowledge_base.server",
    ]
    if not claude:
        print("Claude CLI is not on PATH. Run this command to register the MCP server:")
        print(subprocess.list2cmdline(command) if os.name == "nt" else shlex.join(command))
        return

    listing = _run_claude(
        claude,
        ["mcp", "list"],
        check=False,
        capture_output=True,
        text=True,
        env=_child_environment(),
    )
    if re.search(r"\bknowledge-base\b", listing.stdout, re.IGNORECASE):
        _run_claude(claude, [
            "mcp", "remove", "knowledge-base", "--scope", "user",
        ], env=_child_environment())
    command[0] = claude
    _run_claude(claude, command[1:], env=_child_environment())
    print("Registered knowledge-base with Claude Code.")


def _run_claude(
    executable: str,
    arguments: list[str],
    **options,
) -> subprocess.CompletedProcess:
    command = [executable, *arguments]
    if os.name == "nt" and executable.casefold().endswith((".cmd", ".bat")):
        return subprocess.run(subprocess.list2cmdline(command), shell=True, **options)
    return subprocess.run(command, **options)


def _write_install_state(install_dir: Path, edition: str, tag: str, port: int) -> None:
    state = {
        "edition": edition,
        "tag": tag,
        "qdrant_port": port,
        "install_time": datetime.now(timezone.utc).isoformat(),
    }
    (install_dir / ".kb-install.json").write_text(
        json.dumps(state, indent=2) + "\n", encoding="utf-8",
    )


def _collections_match(base_url: str, collections: dict) -> bool:
    if not _qdrant_ready(base_url):
        return False
    for name, expected in collections.items():
        info = _collection_info(base_url, name)
        if info is None or int(info.get("points_count", -1)) != int(expected["points"]):
            return False
    return True


def _check_download_space(install_dir: Path, bundles: list[dict]) -> None:
    required = sum(int(bundle["size"]) for bundle in bundles) * 3.2
    free = shutil.disk_usage(install_dir).free
    if free < required:
        raise RuntimeError(
            "Not enough free disk space for the selected release bundles: "
            f"need {required / (1024 ** 3):.2f} GiB, "
            f"have {free / (1024 ** 3):.2f} GiB"
        )


def install(args: argparse.Namespace) -> None:
    install_dir = args.dir.resolve()
    install_dir.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("KB_GH_TOKEN")
    local_release = args.local_release.resolve() if args.local_release else None
    download_dir = install_dir / ".kb-download"
    download_dir.mkdir(parents=True, exist_ok=True)
    manifest, assets = _release_files(args.release_tag, local_release, token, download_dir)
    if manifest.get("tag") != args.release_tag:
        raise ValueError(
            f"Release manifest tag is {manifest.get('tag')!r}, expected {args.release_tag!r}"
        )
    bundle_names = ["kb-core"]
    if args.edition == "full":
        bundle_names.append("kb-philosophy")
    selected_bundles = []
    for bundle_name in bundle_names:
        if bundle_name not in manifest["bundles"]:
            raise ValueError(f"Release manifest is missing bundle {bundle_name}")
        selected_bundles.append(manifest["bundles"][bundle_name])

    collections = {
        name: value
        for name, value in manifest["collections"].items()
        if value.get("bundle") in bundle_names
    }
    state_path = install_dir / ".kb-install.json"
    if args.update and state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        binary = install_dir / "bin" / ("qdrant.exe" if os.name == "nt" else "qdrant")
        version_file = binary.parent / "qdrant.version"
        try:
            binary_version = version_file.read_text(encoding="utf-8").strip()
        except OSError:
            binary_version = None
        base_url = f"http://127.0.0.1:{args.qdrant_port}"
        if (
            state.get("tag") == args.release_tag
            and state.get("edition") == args.edition
            and binary.is_file()
            and binary_version == str(manifest["qdrant_version"])
            and _collections_match(base_url, collections)
        ):
            _clear_download_tokens()
            token = None
            if not args.skip_register:
                _register(install_dir, args.edition, args.qdrant_port, binary)
            _write_install_state(install_dir, args.edition, args.release_tag, args.qdrant_port)
            if not args.skip_register:
                print(f"Data release {args.release_tag} is current; refreshed MCP registration.")
            else:
                print(f"Data release {args.release_tag} is current.")
            return

    _check_download_space(install_dir, selected_bundles)

    part_paths = []
    for bundle_name in bundle_names:
        bundle = manifest["bundles"][bundle_name]
        for part in bundle["parts"]:
            part_paths.append(download_part(
                part, download_dir / part["name"], local_release, assets, token,
            ))

    _clear_download_tokens()
    token = None

    bundle_archives = {}
    for bundle_name in bundle_names:
        bundle = manifest["bundles"][bundle_name]
        archive = download_dir / f"{bundle_name}.tar.gz"
        bundle_archives[bundle_name] = assemble_bundle(bundle, download_dir, archive)

    version = str(manifest["qdrant_version"])
    binary = _download_qdrant(version, install_dir, args.qdrant_port)
    base_url, matching = _prepare_qdrant(
        install_dir, args.qdrant_port, binary, collections,
    )
    _restore_collections(
        manifest, bundle_archives, base_url, matching, install_dir,
    )
    for part_path in part_paths:
        part_path.unlink(missing_ok=True)
    for archive in bundle_archives.values():
        archive.unlink(missing_ok=True)

    # The explicit warm-up can be skipped; the required smoke query still exercises
    # the models needed for a real search.
    if not args.skip_models:
        _warm_models(args.edition)
    os.environ["KB_EDITION"] = args.edition
    os.environ["KB_QDRANT_URL"] = base_url
    os.environ["KB_QDRANT_BIN"] = str(binary)
    os.environ["KB_QDRANT_STORAGE"] = str(install_dir / "qdrant-storage")
    if not args.skip_register:
        _register(install_dir, args.edition, args.qdrant_port, binary)
    _smoke_query(args.edition)

    _write_install_state(install_dir, args.edition, args.release_tag, args.qdrant_port)
    print(f"Installed {args.edition} edition, release {args.release_tag}, in {install_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=ROOT)
    parser.add_argument("--edition", choices=("core", "full"), required=True)
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--qdrant-port", type=int, default=6333)
    parser.add_argument("--skip-models", action="store_true")
    parser.add_argument("--skip-register", action="store_true")
    parser.add_argument("--release-tag", default="data-v8")
    parser.add_argument("--local-release", type=Path)
    args = parser.parse_args()

    try:
        if not 1 <= args.qdrant_port <= 65535:
            raise ValueError("--qdrant-port must be between 1 and 65535")
        install(args)
    except (OSError, KeyError, HTTPError, URLError, RuntimeError, ValueError) as exc:
        print(f"install: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
