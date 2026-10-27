"""Explicit wiki roots and exclusion of duplicate Git worktree copies."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import subprocess

from ..config import ROOT

ROOTS_FILE = ROOT / "data" / "wiki" / "roots.txt"
logger = logging.getLogger(__name__)


def configured_roots() -> list[Path]:
    """Environment overrides the file, including an explicitly empty value."""
    if "KB_WIKI_ROOTS" in os.environ:
        entries = os.environ["KB_WIKI_ROOTS"].split(os.pathsep)
    elif ROOTS_FILE.is_file():
        entries = [line.split("#", 1)[0] for line in ROOTS_FILE.read_text(encoding="utf-8").splitlines()]
    else:
        entries = []
    return list(dict.fromkeys(Path(entry.strip()).expanduser().resolve()
                             for entry in entries if entry.strip()))


@dataclass(frozen=True)
class WikiRoot:
    path: Path
    project: str
    skip_reason: str | None = None


def resolve_roots(paths: list[str | Path] | None = None) -> list[WikiRoot]:
    """Classify only the selected folders; never discover repositories by crawling."""
    selected = configured_roots() if paths is None else [Path(p).expanduser().resolve() for p in paths]
    resolved = []
    for path in dict.fromkeys(selected):
        if not path.is_dir():
            # A missing/unmounted root is not evidence that all its files vanished.
            raise FileNotFoundError(f"Configured wiki root is not a directory: {path}")
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--path-format=absolute", "--git-common-dir", "--git-dir", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
        reason = None
        project = path.parent.name
        if result.returncode == 0:
            common_dir, git_dir, repo_dir = result.stdout.strip().splitlines()
            project = Path(repo_dir).name
            if Path(common_dir).resolve() != Path(git_dir).resolve():
                reason = f"git worktree (git-dir {git_dir} differs from common-dir {common_dir})"
                logger.warning("Skipping wiki root %s: %s", path, reason)
        elif "not a git repository" not in result.stderr.lower():
            raise RuntimeError(f"Cannot check wiki root {path} for a git worktree: {result.stderr.strip()}")
        resolved.append(WikiRoot(path, project, reason))
    return resolved


def iter_pages(root: Path):
    """Yield markdown without raw inputs, directory links, or file symlinks."""
    def fail(error):
        raise error

    for directory, dirs, files in os.walk(root, onerror=fail):
        dirs[:] = sorted(name for name in dirs
                         if name.lower() not in {"inputs", "raw", ".git"}
                         and not (Path(directory) / name).is_symlink())
        for name in sorted(files):
            path = Path(directory) / name
            if path.suffix.lower() == ".md" and not path.is_symlink():
                yield path
