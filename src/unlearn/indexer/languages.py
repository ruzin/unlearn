from __future__ import annotations

from functools import lru_cache

from tree_sitter import Language, Parser


SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "javascript",
}


@lru_cache(maxsize=None)
def get_language(name: str) -> Language:
    if name == "python":
        import tree_sitter_python

        return Language(tree_sitter_python.language())
    if name == "javascript":
        import tree_sitter_javascript

        return Language(tree_sitter_javascript.language())
    if name == "typescript":
        import tree_sitter_typescript

        return Language(tree_sitter_typescript.language_typescript())
    if name == "tsx":
        import tree_sitter_typescript

        return Language(tree_sitter_typescript.language_tsx())
    raise ValueError(f"Unsupported language: {name}")


@lru_cache(maxsize=None)
def get_parser(name: str) -> Parser:
    return Parser(get_language(name))


def language_for_file(path: str) -> str | None:
    for ext, lang in SUPPORTED_EXTENSIONS.items():
        if path.endswith(ext):
            return lang
    return None
