from __future__ import annotations

from pathlib import Path
from typing import Iterator

DEFAULT_IGNORE = {
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    "target",
    ".unlearn",
    ".idea",
    ".vscode",
}


def walk_repo(
    root: Path,
    extensions: set[str],
    ignore: set[str] | None = None,
) -> Iterator[Path]:
    """Yield files under `root` matching one of `extensions`, skipping ignored dirs.

    `extensions` should include the dot, e.g. {".py", ".ts"}.
    """
    ignore_set = ignore or DEFAULT_IGNORE
    root = root.resolve()
    if root.is_file():
        if root.suffix in extensions:
            yield root
        return

    stack: list[Path] = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except (PermissionError, FileNotFoundError):
            continue
        for entry in entries:
            if entry.name in ignore_set:
                continue
            if entry.is_dir():
                stack.append(entry)
            elif entry.is_file() and entry.suffix in extensions:
                yield entry


def to_repo_relative(path: Path, root: Path) -> str:
    """Return `path` relative to `root` using forward slashes."""
    rel = path.resolve().relative_to(root.resolve())
    return rel.as_posix()
