from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ExtractedEntity:
    """A function, class, or type extracted from a single file."""

    kind: str  # "function" | "class" | "type"
    name: str
    line_start: int
    line_end: int
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportStatement:
    line: int
    module: str  # raw module spec — "auth.middleware", "./auth", ".helpers", etc.
    imported_names: list[str]  # bare symbol names; ["*"] for wildcard, [] for whole-module import
    alias: str | None = None  # `import foo as bar` → bar
    is_relative: bool = False
    relative_level: int = 0  # 1 for `from .`, 2 for `from ..`


@dataclass
class CallSite:
    line: int
    callee_name: str  # bare last segment, e.g. "validate_token" for `auth.validate_token(...)`
    callee_chain: list[str]  # full attribute chain, e.g. ["auth", "validate_token"]
    caller_name: str | None  # name of enclosing function/method, None if module-level
    caller_line: int | None  # line_start of the enclosing function/method


@dataclass
class InheritanceEdge:
    class_name: str
    class_line: int
    base_names: list[str]  # bare names of base classes/interfaces


@dataclass
class FileExtraction:
    file_path: str  # relative to project root
    language: str
    size_bytes: int
    entities: list[ExtractedEntity] = field(default_factory=list)
    imports: list[ImportStatement] = field(default_factory=list)
    calls: list[CallSite] = field(default_factory=list)
    inheritance: list[InheritanceEdge] = field(default_factory=list)


class Extractor(Protocol):
    language: str

    def extract(self, source: bytes, file_path: str) -> FileExtraction: ...
