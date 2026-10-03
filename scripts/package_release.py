#!/usr/bin/env python3
"""Create split GitHub release bundles for the technical and philosophy shelves."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
QDRANT_VERSION = "1.18.2"
COLLECTIONS = {
    "developer_knowledge_v10": {"alias": "developer_knowledge", "bundle": "kb-core"},
    "philosophy": {"bundle": "kb-philosophy"},
}
CHUNK_SIZE = 8 * 1024 * 1024


def _qdrant_request(base_url: str, path: str, method: str = "GET"):
    request = Request(f"{base_url.rstrip('/')}{path}", method=method)
    try:
        return urlopen(request, timeout=60)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Qdrant request failed: {method} {path}: {exc}") from exc


def _qdrant_json(base_url: str, path: str, method: str = "GET") -> dict:
    with _qdrant_request(base_url, path, method) as response:
        payload = json.load(response)
    return payload.get("result", payload)


def point_count(base_url: str, collection: str) -> int:
    result = _qdrant_json(base_url, f"/collections/{quote(collection, safe='')}")
    return int(result["points_count"])


def _source_files(source_root: Path, bundle_name: str) -> list[tuple[Path, str]]:
    data_dir = source_root / "data"
    files: list[tuple[Path, str]] = []
    if bundle_name == "kb-core":
        files.extend(
            (path, path.relative_to(source_root).as_posix())
            for directory, suffix in (("markdown", ".md"), ("chunks", ".json"))
            for path in sorted((data_dir / directory).glob(f"*{suffix}"))
            if path.is_file()
        )
    else:
        files.extend(
            (path, path.relative_to(source_root).as_posix())
            for directory in ("markdown", "chunks")
            for path in sorted((data_dir / directory / "philosophy").rglob("*"))
            if path.is_file()
        )
    return files


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def split_bundle(
    bundle_path: Path,
    bundle_name: str,
    part_size: int,
    output_dir: Path,
) -> dict:
    """Split a bundle and return hashes and sizes for its release manifest row."""
    if part_size < 1:
        raise ValueError("part_size must be positive")
    parts = []
    for stale_part in output_dir.glob(f"{bundle_name}.part*"):
        stale_part.unlink()
    with bundle_path.open("rb") as source:
        index = 0
        while True:
            name = f"{bundle_name}.part{index:02d}"
            part_path = output_dir / name
            part_digest = hashlib.sha256()
            written = 0
            with part_path.open("wb") as part_file:
                while written < part_size:
                    block = source.read(min(CHUNK_SIZE, part_size - written))
                    if not block:
                        break
                    part_file.write(block)
                    part_digest.update(block)
                    written += len(block)
            if written == 0:
                part_path.unlink(missing_ok=True)
                break
            parts.append({
                "name": name,
                "size": written,
                "sha256": part_digest.hexdigest(),
            })
            index += 1
    return {
        "parts": parts,
        "sha256": _sha256_file(bundle_path),
        "size": bundle_path.stat().st_size,
    }


def _create_snapshot(base_url: str, collection: str) -> str:
    result = _qdrant_json(
        base_url,
        f"/collections/{quote(collection, safe='')}/snapshots?wait=true",
        "POST",
    )
    name = result.get("name")
    if not name:
        raise RuntimeError(f"Qdrant did not return a snapshot name for {collection}")
    return str(name)


def _download_snapshot(base_url: str, collection: str, snapshot: str, target: Path) -> None:
    path = (
        f"/collections/{quote(collection, safe='')}/snapshots/"
        f"{quote(snapshot, safe='')}"
    )
    with _qdrant_request(base_url, path) as response, target.open("wb") as output:
        shutil.copyfileobj(response, output, length=CHUNK_SIZE)


def _delete_snapshot(base_url: str, collection: str, snapshot: str) -> None:
    path = (
        f"/collections/{quote(collection, safe='')}/snapshots/"
        f"{quote(snapshot, safe='')}"
    )
    with _qdrant_request(base_url, path, "DELETE"):
        pass


def _add_bundle(bundle_path: Path, files: list[tuple[Path, str]], snapshot_path: Path) -> None:
    with bundle_path.open("wb") as raw_file:
        with gzip.GzipFile(fileobj=raw_file, mode="wb", compresslevel=6, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as archive:
                for path, arcname in files:
                    archive.add(path, arcname=arcname, recursive=False)
                snapshot_arcname = snapshot_path.name
                archive.add(
                    snapshot_path,
                    arcname=f"snapshots/{snapshot_arcname}",
                    recursive=False,
                )


def _dry_run(source_root: Path, base_url: str, part_size: int) -> None:
    if part_size < 1:
        raise ValueError("--part-size must be positive")
    counts = {name: point_count(base_url, name) for name in COLLECTIONS}
    for bundle_name, collection in (
        ("kb-core", "developer_knowledge_v10"),
        ("kb-philosophy", "philosophy"),
    ):
        files = _source_files(source_root, bundle_name)
        uncompressed_bytes = sum(path.stat().st_size for path, _ in files)
        file_count = len(files) + 1  # The snapshot is a planned bundle member.
        print(
            f"{bundle_name}: {file_count} files; {uncompressed_bytes} uncompressed bytes "
            f"(snapshot size unavailable in dry-run; source files only); "
            f"{collection} points={counts[collection]}"
        )


def package_release(
    source_root: Path,
    output_dir: Path,
    base_url: str,
    part_size: int,
    tag: str,
) -> dict:
    if part_size < 1:
        raise ValueError("--part-size must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    point_counts = {name: point_count(base_url, name) for name in COLLECTIONS}
    bundle_files = {
        "kb-core": _source_files(source_root, "kb-core"),
        "kb-philosophy": _source_files(source_root, "kb-philosophy"),
    }
    collections = {
        name: {"points": point_counts[name], **attributes}
        for name, attributes in COLLECTIONS.items()
    }
    bundles = {}

    with tempfile.TemporaryDirectory(prefix=".package-", dir=output_dir) as temporary:
        work_dir = Path(temporary)
        for collection, bundle_name, snapshot_filename in (
            ("developer_knowledge_v10", "kb-core", "developer_knowledge_v10.snapshot"),
            ("philosophy", "kb-philosophy", "philosophy.snapshot"),
        ):
            snapshot_name = _create_snapshot(base_url, collection)
            snapshot_path = work_dir / snapshot_filename
            try:
                _download_snapshot(base_url, collection, snapshot_name, snapshot_path)
                bundle_path = output_dir / f"{bundle_name}.tar.gz"
                _add_bundle(bundle_path, bundle_files[bundle_name], snapshot_path)
                bundles[bundle_name] = split_bundle(
                    bundle_path, bundle_name, part_size, output_dir,
                )
                bundle_path.unlink()
            finally:
                _delete_snapshot(base_url, collection, snapshot_name)

    manifest = {
        "tag": tag,
        "created": datetime.now(timezone.utc).isoformat(),
        "collections": collections,
        "bundles": bundles,
        "qdrant_version": QDRANT_VERSION,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "release")
    parser.add_argument("--qdrant-url", default="http://127.0.0.1:6333")
    parser.add_argument("--part-size", type=int, default=1_900_000_000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tag", default="data-v10")
    args = parser.parse_args()

    try:
        if args.dry_run:
            _dry_run(args.source_root.resolve(), args.qdrant_url, args.part_size)
        else:
            manifest = package_release(
                args.source_root.resolve(), args.out.resolve(), args.qdrant_url,
                args.part_size, args.tag,
            )
            print(f"Wrote {args.out.resolve() / 'manifest.json'}")
            print(json.dumps(manifest["bundles"], indent=2))
    except (OSError, KeyError, RuntimeError, ValueError) as exc:
        print(f"package_release: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
