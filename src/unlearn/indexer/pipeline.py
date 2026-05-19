from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..graph.store import GraphStore
from ..utils.files import to_repo_relative, walk_repo
from ..utils.timing import stopwatch
from .extractors.base import Extractor, FileExtraction
from .extractors.python import PythonExtractor
from .extractors.typescript import TypeScriptExtractor
from .languages import SUPPORTED_EXTENSIONS, language_for_file
from .resolver import build_graph_edges


# Languages that have a v0.1 extractor.
_EXTRACTORS: dict[str, Extractor] = {
    "python": PythonExtractor(),
    "typescript": TypeScriptExtractor("typescript"),
    "javascript": TypeScriptExtractor("javascript"),
}


@dataclass
class IndexResult:
    root: str
    files_indexed: int
    files_skipped: int
    languages: dict[str, int]
    elapsed_ms: float
    store: GraphStore


def _enabled_extensions(languages: set[str] | None) -> set[str]:
    if not languages:
        # All extensions for languages we have extractors for.
        return {
            ext for ext, lang in SUPPORTED_EXTENSIONS.items() if lang in _EXTRACTORS
        }
    return {ext for ext, lang in SUPPORTED_EXTENSIONS.items() if lang in languages}


def index_repo(
    root: Path,
    languages: set[str] | None = None,
) -> IndexResult:
    """Walk `root`, parse all supported files, and build a graph."""
    root = root.resolve()
    extensions = _enabled_extensions(languages)

    extractions: list[FileExtraction] = []
    files_skipped = 0
    lang_counts: dict[str, int] = {}

    with stopwatch() as elapsed:
        for path in walk_repo(root, extensions):
            lang = language_for_file(path.name)
            if lang is None:
                files_skipped += 1
                continue
            extractor = _EXTRACTORS.get(lang) or _EXTRACTORS.get(_canonical_lang(lang))
            if extractor is None:
                files_skipped += 1
                continue
            try:
                source = path.read_bytes()
            except OSError:
                files_skipped += 1
                continue
            rel = to_repo_relative(path, root)
            extraction = extractor.extract(source, rel)
            extractions.append(extraction)
            lang_counts[extraction.language] = lang_counts.get(extraction.language, 0) + 1

        nodes, edges = build_graph_edges(extractions)
        store = GraphStore()
        for n in nodes:
            store.add_node(n)
        for e in edges:
            store.add_edge(e)

    return IndexResult(
        root=str(root),
        files_indexed=len(extractions),
        files_skipped=files_skipped,
        languages=lang_counts,
        elapsed_ms=elapsed["ms"],
        store=store,
    )


def _canonical_lang(name: str) -> str:
    # tsx and typescript share an extractor in this build (when we add it).
    if name in ("tsx",):
        return "typescript"
    return name
