"""Start a local Qdrant process when one is configured for this installation."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import urlopen

from .config import ROOT


def _ready_url(base_url: str) -> str:
    parsed = urlsplit(base_url)
    return urlunsplit((parsed.scheme, parsed.netloc, "/readyz", "", ""))


def _is_ready(ready_url: str, timeout: float = 2.0) -> bool:
    try:
        with urlopen(ready_url, timeout=timeout) as response:
            return response.status == 200
    except (OSError, URLError, ValueError):
        return False


def ensure_qdrant() -> None:
    """Start the configured Qdrant binary and wait for its readiness endpoint."""
    base_url = os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333")
    ready_url = _ready_url(base_url)
    if _is_ready(ready_url):
        return

    binary = os.environ.get("KB_QDRANT_BIN")
    if not binary:
        return

    parsed = urlsplit(base_url)
    if not parsed.hostname:
        raise ValueError(f"KB_QDRANT_URL must include a host: {base_url}")
    http_port = parsed.port or 6333
    storage = Path(os.environ.get("KB_QDRANT_STORAGE", str(ROOT / "qdrant-storage")))
    snapshots = storage.parent / "qdrant-snapshots"
    storage.mkdir(parents=True, exist_ok=True)
    snapshots.mkdir(parents=True, exist_ok=True)
    log_path = storage / "qdrant.log"

    child_env = os.environ.copy()
    child_env.update({
        "QDRANT__SERVICE__HOST": "127.0.0.1",
        "QDRANT__SERVICE__HTTP_PORT": str(http_port),
        "QDRANT__SERVICE__GRPC_PORT": str(http_port + 1),
        "QDRANT__STORAGE__STORAGE_PATH": str(storage),
        "QDRANT__STORAGE__SNAPSHOTS_PATH": str(snapshots),
        "QDRANT__TELEMETRY_DISABLED": "true",
    })

    print(f"[kb] Starting Qdrant; log: {log_path}", file=sys.stderr)
    with log_path.open("ab") as log_file:
        options = {
            "env": child_env,
            "stdin": subprocess.DEVNULL,
            "stdout": log_file,
            "stderr": log_file,
            "close_fds": True,
        }
        if os.name == "nt":
            options["creationflags"] = (
                subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.CREATE_NO_WINDOW
            )
        else:
            options["start_new_session"] = True
        subprocess.Popen([binary], **options)

    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if _is_ready(ready_url):
            print(f"[kb] Qdrant is ready at {base_url}", file=sys.stderr)
            return
        time.sleep(1)

    raise TimeoutError(
        f"Qdrant did not become ready at {base_url} within 60 seconds; "
        f"see {log_path}"
    )
