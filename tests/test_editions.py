"""Packaging and MCP registry contracts for the portable editions."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.install import assemble_bundle, download_part
from scripts.package_release import split_bundle

ROOT = Path(__file__).resolve().parent.parent
TECHNICAL_TOOLS = {
    "search", "search_book", "read_chunk", "get_chapter", "list_books", "grep_books",
}


@pytest.mark.parametrize(
    ("edition", "expected"),
    [
        ("core", TECHNICAL_TOOLS),
        ("full", TECHNICAL_TOOLS | {"search_philosophy", "list_philosophy"}),
    ],
)
def test_server_registers_the_requested_edition_tools(edition, expected):
    env = os.environ.copy()
    env["KB_EDITION"] = edition
    command = (
        "import asyncio, json, knowledge_base.server as server; "
        "print(json.dumps(sorted(tool.name for tool in "
        "asyncio.run(server.mcp.list_tools()))))"
    )
    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    names = json.loads(result.stdout.strip().splitlines()[-1])
    assert set(names) == expected
    assert len(names) == (6 if edition == "core" else 8)


def test_bundle_parts_hash_and_reassemble(tmp_path):
    source = tmp_path / "kb-core.tar.gz"
    contents = b"release bundle data across three deliberately small parts"
    source.write_bytes(contents)
    local_release = tmp_path / "local-release"
    local_release.mkdir()

    bundle = split_bundle(source, "kb-core", 17, local_release)

    assert [part["name"] for part in bundle["parts"]] == [
        "kb-core.part00", "kb-core.part01", "kb-core.part02", "kb-core.part03",
    ]
    assert [part["size"] for part in bundle["parts"]] == [17, 17, 17, len(contents) - 51]
    assert bundle["sha256"] == hashlib.sha256(contents).hexdigest()
    for part in bundle["parts"]:
        actual = hashlib.sha256(
            (local_release / part["name"]).read_bytes()
        ).hexdigest()
        assert actual == part["sha256"]

    staging = tmp_path / "install-staging"
    for part in bundle["parts"]:
        download_part(part, staging / part["name"], local_release, {}, None)
    assembled = staging / "assembled.tar.gz"
    assert assemble_bundle(bundle, staging, assembled) == assembled
    assert assembled.read_bytes() == contents


def test_bundle_reassembly_rejects_corrupt_local_release_part(tmp_path):
    source = tmp_path / "kb-philosophy.tar.gz"
    source.write_bytes(b"a small philosophy archive")
    local_release = tmp_path / "local-release"
    local_release.mkdir()
    bundle = split_bundle(source, "kb-philosophy", 10, local_release)
    (local_release / bundle["parts"][0]["name"]).write_bytes(b"x" * 10)

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        assemble_bundle(bundle, local_release, tmp_path / "assembled.tar.gz")
