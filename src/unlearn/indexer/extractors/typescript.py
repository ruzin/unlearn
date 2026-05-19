from __future__ import annotations

from tree_sitter import Node

from ..languages import get_parser
from .base import (
    CallSite,
    ExtractedEntity,
    FileExtraction,
    ImportStatement,
    InheritanceEdge,
)
from .common import (
    find_child_by_field,
    find_children_by_type,
    line_end,
    line_start,
    text_of,
)


class TypeScriptExtractor:
    """Handles TypeScript, TSX, and JavaScript via tree-sitter-typescript / -javascript."""

    def __init__(self, language: str = "typescript") -> None:
        self.language = language

    def extract(self, source: bytes, file_path: str) -> FileExtraction:
        parser_lang = self.language
        if parser_lang == "javascript":
            parser_lang = "javascript"
        elif file_path.endswith(".tsx"):
            parser_lang = "tsx"
        else:
            parser_lang = "typescript"
        tree = get_parser(parser_lang).parse(source)
        root = tree.root_node

        extraction = FileExtraction(
            file_path=file_path,
            language=self.language,
            size_bytes=len(source),
        )

        for child in root.children:
            self._handle_top_level(child, source, extraction, is_exported=False)
        return extraction

    def _handle_top_level(
        self,
        node: Node,
        source: bytes,
        extraction: FileExtraction,
        is_exported: bool,
    ) -> None:
        if node.type == "import_statement":
            extraction.imports.extend(self._parse_import(node, source))
        elif node.type == "export_statement":
            self._handle_export(node, source, extraction)
        elif node.type == "function_declaration":
            self._handle_function(node, source, extraction, name=None, is_exported=is_exported)
        elif node.type == "class_declaration":
            self._handle_class(node, source, extraction, is_exported=is_exported)
        elif node.type == "interface_declaration":
            self._handle_type(node, source, extraction, kind="interface", is_exported=is_exported)
        elif node.type == "type_alias_declaration":
            self._handle_type(node, source, extraction, kind="type_alias", is_exported=is_exported)
        elif node.type == "enum_declaration":
            self._handle_type(node, source, extraction, kind="enum", is_exported=is_exported)
        elif node.type == "lexical_declaration":
            self._handle_lexical(node, source, extraction, is_exported=is_exported)
        elif node.type == "variable_statement":
            self._handle_lexical(node, source, extraction, is_exported=is_exported)

    def _handle_export(
        self, node: Node, source: bytes, extraction: FileExtraction
    ) -> None:
        for child in node.children:
            if child.type in ("export", "default", ";", "{", "}", ","):
                continue
            self._handle_top_level(child, source, extraction, is_exported=True)

    # ----- imports -----

    def _parse_import(self, node: Node, source: bytes) -> list[ImportStatement]:
        source_node: Node | None = None
        for child in node.children:
            if child.type == "string":
                # string_fragment is the inner text without quotes.
                inner = find_children_by_type(child, "string_fragment")
                if inner:
                    source_node = inner[0]
                else:
                    source_node = child
                break
        if source_node is None:
            return []
        module = text_of(source_node, source)

        names: list[str] = []
        alias: str | None = None
        clause = find_children_by_type(node, "import_clause")
        if clause:
            for c in clause[0].children:
                if c.type == "identifier":
                    # default import — `import foo from './x'`
                    names.append("default")
                    alias = text_of(c, source)
                elif c.type == "named_imports":
                    for spec in find_children_by_type(c, "import_specifier"):
                        name_node = find_child_by_field(spec, "name")
                        alias_node = find_child_by_field(spec, "alias")
                        if name_node is not None:
                            names.append(text_of(name_node, source))
                        if alias_node is not None and name_node is not None:
                            # `import { x as y }` — track as a named import; alias kept implicit.
                            pass
                elif c.type == "namespace_import":
                    ids = find_children_by_type(c, "identifier")
                    if ids:
                        alias = text_of(ids[0], source)
                    names.append("*")

        return [
            ImportStatement(
                line=line_start(node),
                module=module,
                imported_names=names,
                alias=alias,
            )
        ]

    # ----- functions -----

    def _handle_function(
        self,
        node: Node,
        source: bytes,
        extraction: FileExtraction,
        name: str | None,
        is_exported: bool,
        is_method: bool = False,
        is_nested: bool = False,
    ) -> None:
        if name is None:
            name_node = find_child_by_field(node, "name")
            if name_node is None:
                return
            name = text_of(name_node, source)

        start = line_start(node)
        end = line_end(node)

        params_node = find_child_by_field(node, "parameters")
        params = self._extract_params(params_node, source) if params_node else []

        return_type_node = find_child_by_field(node, "return_type")
        return_type: str | None = None
        if return_type_node is not None:
            # type_annotation wraps `: SomeType` — extract just the type portion.
            raw = text_of(return_type_node, source).lstrip(":").strip()
            return_type = raw or None

        is_async = any(c.type == "async" for c in node.children)

        extraction.entities.append(
            ExtractedEntity(
                kind="function",
                name=name,
                line_start=start,
                line_end=end,
                properties={
                    "params": params,
                    "return_type": return_type,
                    "is_async": is_async,
                    "is_method": is_method,
                    "is_nested": is_nested,
                    "is_exported": is_exported and not is_nested,
                },
            )
        )

        body = find_child_by_field(node, "body")
        if body is not None:
            self._scan_body(body, source, extraction, caller_name=name, caller_line=start)

    def _extract_params(self, params_node: Node, source: bytes) -> list[str]:
        out: list[str] = []
        for child in params_node.children:
            if child.type in ("(", ")", ","):
                continue
            if child.type in ("required_parameter", "optional_parameter"):
                pattern = find_child_by_field(child, "pattern")
                if pattern is not None:
                    out.append(text_of(pattern, source))
            elif child.type == "identifier":
                out.append(text_of(child, source))
        return out

    # ----- classes -----

    def _handle_class(
        self,
        node: Node,
        source: bytes,
        extraction: FileExtraction,
        is_exported: bool,
    ) -> None:
        name_node = find_child_by_field(node, "name")
        if name_node is None:
            return
        name = text_of(name_node, source)
        start = line_start(node)
        end = line_end(node)

        bases: list[str] = []
        heritage = find_children_by_type(node, "class_heritage")
        if heritage:
            for clause in heritage[0].children:
                if clause.type == "extends_clause":
                    for c in clause.children:
                        if c.type in ("identifier", "type_identifier"):
                            bases.append(text_of(c, source))
                elif clause.type == "implements_clause":
                    for c in clause.children:
                        if c.type in ("identifier", "type_identifier"):
                            bases.append(text_of(c, source))

        extraction.entities.append(
            ExtractedEntity(
                kind="class",
                name=name,
                line_start=start,
                line_end=end,
                properties={
                    "bases": bases,
                    "is_exported": is_exported,
                },
            )
        )
        if bases:
            extraction.inheritance.append(
                InheritanceEdge(class_name=name, class_line=start, base_names=bases)
            )

        body = find_child_by_field(node, "body")
        if body is None:
            return
        for child in body.children:
            if child.type == "method_definition":
                method_name_node = find_child_by_field(child, "name")
                if method_name_node is None:
                    continue
                method_name = text_of(method_name_node, source)
                self._handle_function(
                    child, source, extraction, name=method_name, is_exported=False, is_method=True
                )

    # ----- types -----

    def _handle_type(
        self,
        node: Node,
        source: bytes,
        extraction: FileExtraction,
        kind: str,
        is_exported: bool,
    ) -> None:
        name_node = find_child_by_field(node, "name")
        if name_node is None:
            return
        name = text_of(name_node, source)
        extraction.entities.append(
            ExtractedEntity(
                kind="type",
                name=name,
                line_start=line_start(node),
                line_end=line_end(node),
                properties={
                    "kind": kind,
                    "is_exported": is_exported,
                },
            )
        )

    # ----- variable declarations (arrow functions) -----

    def _handle_lexical(
        self,
        node: Node,
        source: bytes,
        extraction: FileExtraction,
        is_exported: bool,
    ) -> None:
        for decl in find_children_by_type(node, "variable_declarator"):
            name_node = find_child_by_field(decl, "name")
            value = find_child_by_field(decl, "value")
            if name_node is None or value is None:
                continue
            if value.type == "arrow_function":
                name = text_of(name_node, source)
                self._handle_function(
                    value, source, extraction, name=name, is_exported=is_exported
                )

    # ----- body scanning for calls -----

    def _scan_body(
        self,
        node: Node,
        source: bytes,
        extraction: FileExtraction,
        caller_name: str | None,
        caller_line: int | None,
    ) -> None:
        stack: list[tuple[Node, str | None, int | None]] = [
            (node, caller_name, caller_line)
        ]
        while stack:
            current, cname, cline = stack.pop()
            if current.type == "call_expression":
                call = self._parse_call(current, source, cname, cline)
                if call is not None:
                    extraction.calls.append(call)
            if (
                current.type in ("function_declaration", "arrow_function", "function_expression")
                and current is not node
            ):
                # Nested function — switch caller context and keep walking.
                inner_name_node = find_child_by_field(current, "name")
                if inner_name_node is not None:
                    new_name = text_of(inner_name_node, source)
                    new_line = line_start(current)
                    self._handle_function(
                        current,
                        source,
                        extraction,
                        name=new_name,
                        is_exported=False,
                        is_nested=True,
                    )
                    body = find_child_by_field(current, "body")
                    if body is not None:
                        stack.append((body, new_name, new_line))
                    continue
            for child in reversed(current.children):
                stack.append((child, cname, cline))

    def _parse_call(
        self,
        call_node: Node,
        source: bytes,
        caller_name: str | None,
        caller_line: int | None,
    ) -> CallSite | None:
        func = find_child_by_field(call_node, "function")
        if func is None:
            return None
        chain = _ts_chain(func, source)
        if not chain:
            return None
        return CallSite(
            line=line_start(call_node),
            callee_name=chain[-1],
            callee_chain=chain,
            caller_name=caller_name,
            caller_line=caller_line,
        )


def _ts_chain(node: Node, source: bytes) -> list[str]:
    if node.type == "identifier":
        return [text_of(node, source)]
    if node.type == "this":
        return ["this"]
    if node.type == "member_expression":
        obj = node.child_by_field_name("object")
        prop = node.child_by_field_name("property")
        if obj is None or prop is None:
            return []
        prefix = _ts_chain(obj, source)
        if not prefix:
            return []
        return prefix + [text_of(prop, source)]
    return []
