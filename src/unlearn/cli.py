"""click-based CLI: `unlearn index`, `unlearn serve`, `unlearn info`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .graph.serialise import load_from_disk, save_to_disk
from .indexer import index_repo


CACHE_RELATIVE = Path(".unlearn") / "graph.json"


def _cache_path(root: Path) -> Path:
    return root / CACHE_RELATIVE


def _parse_languages(value: str | None) -> set[str] | None:
    if not value:
        return None
    aliases = {"py": "python", "ts": "typescript", "tsx": "tsx", "js": "javascript"}
    out: set[str] = set()
    for raw in value.split(","):
        token = raw.strip().lower()
        if not token:
            continue
        out.add(aliases.get(token, token))
    return out or None


@click.group()
@click.version_option(package_name="unlearn")
def main() -> None:
    """Codebase knowledge graph for AI agents."""


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--no-cache", is_flag=True, help="Don't write .unlearn/graph.json")
@click.option(
    "--languages",
    default=None,
    help="Comma-separated languages to index (e.g. py,ts).",
)
def index(path: Path, no_cache: bool, languages: str | None) -> None:
    """Index a repo (builds graph, caches to disk)."""
    root = path.resolve()
    langs = _parse_languages(languages)
    click.echo(f"Indexing {root} ...")
    result = index_repo(root, languages=langs)
    stats = result.store.stats()
    click.echo(
        f"Indexed {result.files_indexed} files "
        f"({sum(result.languages.values())} parsed) in {result.elapsed_ms:.0f} ms"
    )
    click.echo(
        f"  files: {stats['files']}, functions: {stats['functions']}, "
        f"classes: {stats['classes']}, types: {stats['types']}, edges: {stats['edges']}"
    )
    if not no_cache:
        cache = _cache_path(root)
        save_to_disk(result.store, str(root), cache)
        click.echo(f"  cache: {cache.relative_to(root) if cache.is_relative_to(root) else cache}")


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False, path_type=Path))
def info(path: Path) -> None:
    """Show graph stats for a repo (loads from cache if present)."""
    root = path.resolve()
    cache = _cache_path(root)
    if cache.exists():
        store, payload = load_from_disk(cache)
        click.echo(f"Loaded from cache: {cache}")
        click.echo(f"  indexed_at: {payload.get('indexed_at')}")
    else:
        click.echo(f"No cache found at {cache} — indexing fresh.")
        result = index_repo(root)
        store = result.store
    stats = store.stats()
    click.echo(json.dumps(stats, indent=2))


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False, path_type=Path))
def serve(path: Path) -> None:
    """Start the MCP server over stdio (for Claude Code)."""
    root = path.resolve()
    cache = _cache_path(root)
    if not cache.exists():
        click.echo(f"No cache at {cache} — indexing first.", err=True)
        result = index_repo(root)
        save_to_disk(result.store, str(root), cache)
        click.echo(f"Indexed {result.files_indexed} files in {result.elapsed_ms:.0f} ms.", err=True)
    # Defer import so plain `--help` doesn't pay the MCP startup cost.
    from .mcp.server import run_stdio

    run_stdio(root)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
