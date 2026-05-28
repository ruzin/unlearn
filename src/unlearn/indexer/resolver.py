"""Cross-file import and call resolution.

Runs after all files are parsed. Maps:
  - import statements → IMPORTS edges between files (and tracks which symbols
    each file pulls in from where)
  - call sites → CALLS edges to known function/class nodes
  - inheritance → INHERITS edges to known class nodes
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from ..graph.models import Edge, EdgeType, Node, NodeType, entity_node_id, file_node_id
from .extractors.base import (
    CallSite,
    FileExtraction,
    ImportStatement,
)


# ----- entity index -----


@dataclass
class _FileIndex:
    """Per-file lookup of the entities we extracted from it."""

    file_path: str
    by_name: dict[str, list[tuple[str, int, str]]]
    # name -> list of (kind, line_start, node_id)


def _build_file_index(extraction: FileExtraction) -> _FileIndex:
    by_name: dict[str, list[tuple[str, int, str]]] = {}
    for e in extraction.entities:
        node_id = entity_node_id(extraction.file_path, e.name, e.line_start)
        by_name.setdefault(e.name, []).append((e.kind, e.line_start, node_id))
    return _FileIndex(file_path=extraction.file_path, by_name=by_name)


# ----- import resolution -----

_PY_EXTS = (".py",)
_TS_EXTS = (".ts", ".tsx", ".js", ".jsx")


def compute_python_source_roots(known_files: set[str]) -> list[str]:
    """Derive Python package source roots from __init__.py placement.

    A "source root" is a directory where absolute imports can be resolved
    against — the parent of the topmost contiguous chain of __init__.py
    directories. For a flat layout (no nesting) this is the indexed root;
    for monorepos with services under services/<svc>/app/ this is each
    service directory.

    Returns the indexed root ("") first, then deeper roots sorted by depth
    so nearer-to-the-importer matches can be tried in order.
    """
    init_dirs = {
        str(PurePosixPath(f).parent)
        for f in known_files
        if f.endswith("/__init__.py") or f == "__init__.py"
    }
    roots: set[str] = {""}  # indexed root always counts (preserves flat-layout behaviour)
    for d in init_dirs:
        # Walk up while the parent also has an __init__.py — find the top of the package chain.
        cur = d
        while True:
            parent = str(PurePosixPath(cur).parent)
            if parent in (".", "") or parent == cur:
                roots.add("")
                break
            if parent in init_dirs:
                cur = parent
                continue
            roots.add(parent)
            break
    return sorted(roots, key=lambda r: r.count("/"))


def resolve_python_import(
    importer_file: str,
    stmt: ImportStatement,
    known_files: set[str],
    source_roots: list[str] | None = None,
) -> str | None:
    """Resolve a Python import to a file in the project.

    Returns the target file path (project-relative) or None if external/stdlib.
    For absolute imports, each entry in `source_roots` is tried as a prefix —
    this is how monorepos with per-package source roots get resolved.
    """
    if stmt.is_relative:
        importer_dir = str(PurePosixPath(importer_file).parent)
        # Walk up `relative_level - 1` directories.
        parts = importer_dir.split("/") if importer_dir != "." else []
        if stmt.relative_level > 1:
            parts = parts[: -(stmt.relative_level - 1)] if len(parts) >= stmt.relative_level - 1 else []
        base = "/".join(p for p in parts if p)
        module_parts = stmt.module.split(".") if stmt.module else []
        target_parts = [p for p in (base.split("/") if base else []) + module_parts if p]
        prefixes: list[str] = [""]  # already path-rooted
    else:
        if not stmt.module:
            return None
        target_parts = stmt.module.split(".")
        # For absolute imports, try the importer's own source root first
        # (deepest matching prefix), then any other roots.
        all_roots = source_roots if source_roots is not None else [""]
        importer_dir = str(PurePosixPath(importer_file).parent)
        own_roots = [r for r in all_roots if r == "" or importer_dir == r or importer_dir.startswith(r + "/")]
        other_roots = [r for r in all_roots if r not in own_roots]
        # Nearest source root to the importer goes first.
        own_roots.sort(key=lambda r: -len(r))
        prefixes = own_roots + other_roots

    if not target_parts:
        return None

    suffix_module = "/".join(target_parts) + ".py"
    suffix_pkg = "/".join(target_parts) + "/__init__.py"
    parent_target = "/".join(target_parts[:-1]) if len(target_parts) >= 2 else None
    last_part = target_parts[-1] if target_parts else None

    for prefix in prefixes:
        base = (prefix + "/") if prefix else ""
        cand = base + suffix_module
        if cand in known_files:
            return cand
        cand = base + suffix_pkg
        if cand in known_files:
            return cand
        if parent_target is not None and last_part is not None:
            cand = base + parent_target + "/" + last_part + ".py"
            if cand in known_files:
                return cand
            cand = base + parent_target + "/" + last_part + "/__init__.py"
            if cand in known_files:
                return cand

    return None


def resolve_ts_import(
    importer_file: str,
    stmt: ImportStatement,
    known_files: set[str],
) -> str | None:
    """Resolve a TypeScript/JavaScript import to a file in the project."""
    spec = stmt.module
    if not spec:
        return None

    # Bare specifiers (no leading . or /) are packages — external.
    if not spec.startswith(".") and not spec.startswith("/"):
        return None

    importer_dir = str(PurePosixPath(importer_file).parent)
    target = str(PurePosixPath(importer_dir) / spec)
    target = _normalise(target)

    # Exact path with extension already present.
    if target in known_files:
        return target

    # Try adding each extension.
    for ext in _TS_EXTS:
        candidate = target + ext
        if candidate in known_files:
            return candidate

    # Try as index file.
    for ext in _TS_EXTS:
        candidate = target + "/index" + ext
        if candidate in known_files:
            return candidate

    return None


def _normalise(path: str) -> str:
    parts: list[str] = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


# ----- main resolver -----


def build_graph_edges(
    extractions: list[FileExtraction],
) -> tuple[list[Node], list[Edge]]:
    """Build all nodes and edges for the graph from per-file extractions."""

    nodes: list[Node] = []
    edges: list[Edge] = []

    known_files: set[str] = {e.file_path for e in extractions}
    file_indexes: dict[str, _FileIndex] = {
        e.file_path: _build_file_index(e) for e in extractions
    }
    py_source_roots = compute_python_source_roots(known_files)

    # First pass: emit File nodes + entity nodes + CONTAINS edges.
    for ex in extractions:
        file_id = file_node_id(ex.file_path)
        nodes.append(
            Node(
                id=file_id,
                type=NodeType.FILE,
                name=PurePosixPath(ex.file_path).name,
                file_path=ex.file_path,
                properties={
                    "language": ex.language,
                    "size_bytes": ex.size_bytes,
                },
            )
        )
        for entity in ex.entities:
            ntype = {
                "function": NodeType.FUNCTION,
                "class": NodeType.CLASS,
                "type": NodeType.TYPE,
            }[entity.kind]
            eid = entity_node_id(ex.file_path, entity.name, entity.line_start)
            nodes.append(
                Node(
                    id=eid,
                    type=ntype,
                    name=entity.name,
                    file_path=ex.file_path,
                    properties={
                        "line_start": entity.line_start,
                        "line_end": entity.line_end,
                        **entity.properties,
                    },
                )
            )
            edges.append(
                Edge(
                    source_id=file_id,
                    target_id=eid,
                    type=EdgeType.CONTAINS,
                    properties={},
                )
            )

    # Second pass: resolve imports — produce IMPORTS edges and a per-file
    # symbol map: name → (target_file, target_node_id_or_None).
    file_symbol_map: dict[str, dict[str, tuple[str, str | None]]] = {}

    for ex in extractions:
        symbol_map: dict[str, tuple[str, str | None]] = {}
        file_symbol_map[ex.file_path] = symbol_map
        for stmt in ex.imports:
            target_file = _resolve_import(ex, stmt, known_files, py_source_roots)
            if target_file is None:
                continue
            edges.append(
                Edge(
                    source_id=file_node_id(ex.file_path),
                    target_id=file_node_id(target_file),
                    type=EdgeType.IMPORTS,
                    properties={
                        "module": stmt.module,
                        "imported_names": stmt.imported_names,
                        "line": stmt.line,
                    },
                )
            )
            target_idx = file_indexes.get(target_file)
            if stmt.imported_names:
                for name in stmt.imported_names:
                    if name == "*":
                        continue
                    target_node_id: str | None = None
                    if target_idx is not None:
                        candidates = target_idx.by_name.get(name)
                        if candidates:
                            target_node_id = candidates[0][2]
                    bound = stmt.alias if stmt.alias and len(stmt.imported_names) == 1 else name
                    symbol_map[bound] = (target_file, target_node_id)
                    # Emit a REFERENCES edge from the importing file to the imported entity.
                    # This is what marks something as "in use" even without a direct call.
                    if target_node_id is not None:
                        edges.append(
                            Edge(
                                source_id=file_node_id(ex.file_path),
                                target_id=target_node_id,
                                type=EdgeType.REFERENCES,
                                properties={"via": "import", "line": stmt.line},
                            )
                        )
            else:
                # Whole-module import: `import foo` or `import foo as bar`.
                bound = stmt.alias or (stmt.module.split(".")[-1] if stmt.module else "")
                if bound:
                    symbol_map[bound] = (target_file, None)

    # Third pass: resolve call sites.
    for ex in extractions:
        symbol_map = file_symbol_map[ex.file_path]
        own_index = file_indexes[ex.file_path]
        for call in ex.calls:
            target_node_id = _resolve_call(
                call, ex.file_path, symbol_map, own_index, file_indexes
            )
            if target_node_id is None:
                continue
            source_node_id = _resolve_caller(call, ex.file_path)
            if source_node_id is None:
                source_node_id = file_node_id(ex.file_path)
            edges.append(
                Edge(
                    source_id=source_node_id,
                    target_id=target_node_id,
                    type=EdgeType.CALLS,
                    properties={"call_site_line": call.line},
                )
            )

    # Fourth pass: inheritance.
    for ex in extractions:
        symbol_map = file_symbol_map[ex.file_path]
        own_index = file_indexes[ex.file_path]
        for inh in ex.inheritance:
            source_node_id = entity_node_id(ex.file_path, inh.class_name, inh.class_line)
            for base in inh.base_names:
                target = _resolve_name(base, symbol_map, own_index, file_indexes)
                if target is None:
                    continue
                edges.append(
                    Edge(
                        source_id=source_node_id,
                        target_id=target,
                        type=EdgeType.INHERITS,
                        properties={},
                    )
                )

    return nodes, edges


def _resolve_import(
    extraction: FileExtraction,
    stmt: ImportStatement,
    known_files: set[str],
    py_source_roots: list[str],
) -> str | None:
    if extraction.language == "python":
        return resolve_python_import(
            extraction.file_path, stmt, known_files, py_source_roots
        )
    return resolve_ts_import(extraction.file_path, stmt, known_files)


def _resolve_call(
    call: CallSite,
    importer_file: str,
    symbol_map: dict[str, tuple[str, str | None]],
    own_index: _FileIndex,
    file_indexes: dict[str, _FileIndex],
) -> str | None:
    if not call.callee_chain:
        return None

    head = call.callee_chain[0]
    tail = call.callee_chain[-1]

    # 1) Method-like: receiver is self/this — look up tail in own file.
    if head in ("self", "this") and len(call.callee_chain) >= 2:
        candidates = own_index.by_name.get(tail)
        if candidates:
            return candidates[0][2]
        return None

    # 2) Same-file lookup by bare name.
    if len(call.callee_chain) == 1:
        candidates = own_index.by_name.get(head)
        if candidates:
            return candidates[0][2]

    # 3) Imported symbol — `head` is the bound name in this file.
    if head in symbol_map:
        target_file, target_node_id = symbol_map[head]
        if target_node_id is not None and len(call.callee_chain) == 1:
            return target_node_id
        # `module.func()` — head is a module import, tail is the function.
        if len(call.callee_chain) >= 2 and target_node_id is None:
            target_idx = file_indexes.get(target_file)
            if target_idx is not None:
                candidates = target_idx.by_name.get(tail)
                if candidates:
                    return candidates[0][2]
        # `func()` where func was imported as a symbol; node id resolved above.
        if target_node_id is not None and len(call.callee_chain) >= 2:
            # Imported symbol then attribute (e.g. method on class) — unresolved.
            return None

    return None


def _resolve_caller(call: CallSite, file_path: str) -> str | None:
    if call.caller_name is None or call.caller_line is None:
        return None
    return entity_node_id(file_path, call.caller_name, call.caller_line)


def _resolve_name(
    name: str,
    symbol_map: dict[str, tuple[str, str | None]],
    own_index: _FileIndex,
    file_indexes: dict[str, _FileIndex],
) -> str | None:
    """Resolve a bare name (e.g. a class base) to a node id."""
    if name in own_index.by_name:
        return own_index.by_name[name][0][2]
    if name in symbol_map:
        target_file, target_node_id = symbol_map[name]
        if target_node_id is not None:
            return target_node_id
        target_idx = file_indexes.get(target_file)
        if target_idx is not None and name in target_idx.by_name:
            return target_idx.by_name[name][0][2]
    return None


