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


class PythonExtractor:
    language = "python"

    def extract(self, source: bytes, file_path: str) -> FileExtraction:
        tree = get_parser("python").parse(source)
        root = tree.root_node

        extraction = FileExtraction(
            file_path=file_path,
            language=self.language,
            size_bytes=len(source),
        )

        for child in root.children:
            self._handle_top_level(child, source, extraction, decorators=[])

        return extraction

    # ----- top level dispatch -----

    def _handle_top_level(
        self,
        node: Node,
        source: bytes,
        extraction: FileExtraction,
        decorators: list[tuple[str, list[str]]],
    ) -> None:
        if node.type == "import_statement":
            extraction.imports.extend(self._parse_import_statement(node, source))
        elif node.type == "import_from_statement":
            extraction.imports.extend(self._parse_import_from_statement(node, source))
        elif node.type == "function_definition":
            self._handle_function(node, source, extraction, decorators=decorators)
        elif node.type == "class_definition":
            self._handle_class(node, source, extraction, decorators=decorators)
        elif node.type == "decorated_definition":
            decs = _parse_decorators(node, source)
            for c in node.children:
                if c.type in ("function_definition", "class_definition"):
                    self._handle_top_level(c, source, extraction, decorators=decs)

    # ----- imports -----

    def _parse_import_statement(self, node: Node, source: bytes) -> list[ImportStatement]:
        out: list[ImportStatement] = []
        for child in node.children:
            if child.type == "dotted_name":
                module = text_of(child, source)
                out.append(
                    ImportStatement(
                        line=line_start(node),
                        module=module,
                        imported_names=[],
                    )
                )
            elif child.type == "aliased_import":
                inner = find_child_by_field(child, "name")
                alias = find_child_by_field(child, "alias")
                module = text_of(inner, source) if inner else ""
                out.append(
                    ImportStatement(
                        line=line_start(node),
                        module=module,
                        imported_names=[],
                        alias=text_of(alias, source) if alias else None,
                    )
                )
        return out

    def _parse_import_from_statement(
        self, node: Node, source: bytes
    ) -> list[ImportStatement]:
        # `from X import a, b` — first dotted_name is module, rest are imported names.
        # `from .X import a` — first child is `relative_import` containing import_prefix + dotted_name.
        # `from . import a` — first child is `relative_import` with just import_prefix.
        is_relative = False
        relative_level = 0
        module = ""
        imported: list[str] = []
        alias: str | None = None

        # The `from` keyword is the first child; the module spec is at index 1.
        module_node: Node | None = None
        if len(node.children) >= 2:
            module_node = node.children[1]

        if module_node is None:
            return []

        if module_node.type == "relative_import":
            is_relative = True
            prefix = find_children_by_type(module_node, "import_prefix")
            if prefix:
                relative_level = sum(1 for c in prefix[0].children if c.type == ".")
            inner_dotted = find_children_by_type(module_node, "dotted_name")
            module = text_of(inner_dotted[0], source) if inner_dotted else ""
        elif module_node.type == "dotted_name":
            module = text_of(module_node, source)

        # Imported names: everything after the `import` keyword.
        seen_import_kw = False
        for child in node.children:
            if not seen_import_kw:
                if child.type == "import":
                    seen_import_kw = True
                continue
            if child.type == "dotted_name":
                imported.append(text_of(child, source))
            elif child.type == "aliased_import":
                inner = find_child_by_field(child, "name")
                a = find_child_by_field(child, "alias")
                if inner is not None:
                    imported.append(text_of(inner, source))
                if a is not None:
                    alias = text_of(a, source)
            elif child.type == "wildcard_import":
                imported.append("*")

        return [
            ImportStatement(
                line=line_start(node),
                module=module,
                imported_names=imported,
                alias=alias,
                is_relative=is_relative,
                relative_level=relative_level,
            )
        ]

    # ----- functions -----

    def _handle_function(
        self,
        node: Node,
        source: bytes,
        extraction: FileExtraction,
        decorators: list[tuple[str, list[str]]],
        is_method: bool = False,
        is_nested: bool = False,
    ) -> None:
        name_node = find_child_by_field(node, "name")
        if name_node is None:
            return
        name = text_of(name_node, source)
        start = line_start(node)
        end = line_end(node)

        params_node = find_child_by_field(node, "parameters")
        params = self._extract_params(params_node, source) if params_node else []

        return_type_node = find_child_by_field(node, "return_type")
        return_type = text_of(return_type_node, source) if return_type_node else None

        # async detection — first child is `async` token when async def.
        is_async = any(c.type == "async" for c in node.children)

        entity = ExtractedEntity(
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
                "decorators": [d for d, _chain in decorators],
                "is_exported": not is_nested,  # Python: top-level names exported by convention
            },
        )
        extraction.entities.append(entity)

        # Decorators become CALLS edges from the decorated entity to the decorator.
        for _text, chain in decorators:
            if chain:
                extraction.calls.append(
                    CallSite(
                        line=start,
                        callee_name=chain[-1],
                        callee_chain=chain,
                        caller_name=name,
                        caller_line=start,
                    )
                )

        body = find_child_by_field(node, "body")
        if body is not None:
            self._scan_body(
                body, source, extraction, caller_name=name, caller_line=start
            )

    def _extract_params(self, params_node: Node, source: bytes) -> list[str]:
        out: list[str] = []
        for child in params_node.children:
            if child.type in ("(", ")", ","):
                continue
            if child.type == "identifier":
                out.append(text_of(child, source))
            elif child.type == "typed_parameter":
                name = find_children_by_type(child, "identifier")
                if name:
                    out.append(text_of(name[0], source))
            elif child.type == "default_parameter":
                name = find_child_by_field(child, "name")
                if name:
                    out.append(text_of(name, source))
            elif child.type == "typed_default_parameter":
                name = find_child_by_field(child, "name")
                if name:
                    out.append(text_of(name, source))
            elif child.type in ("list_splat_pattern", "dictionary_splat_pattern"):
                out.append(text_of(child, source))
        return out

    # ----- classes -----

    def _handle_class(
        self,
        node: Node,
        source: bytes,
        extraction: FileExtraction,
        decorators: list[tuple[str, list[str]]],
    ) -> None:
        name_node = find_child_by_field(node, "name")
        if name_node is None:
            return
        name = text_of(name_node, source)
        start = line_start(node)
        end = line_end(node)

        # Bases: argument_list child.
        bases: list[str] = []
        superclasses = find_child_by_field(node, "superclasses")
        if superclasses is not None:
            for child in superclasses.children:
                if child.type in ("(", ")", ","):
                    continue
                if child.type == "identifier":
                    bases.append(text_of(child, source))
                elif child.type == "attribute":
                    # module.Class → take the last identifier
                    ids = find_children_by_type(child, "identifier")
                    if ids:
                        bases.append(text_of(ids[-1], source))
                elif child.type == "subscript":
                    base_name = find_children_by_type(child, "identifier")
                    if base_name:
                        bases.append(text_of(base_name[0], source))

        entity = ExtractedEntity(
            kind="class",
            name=name,
            line_start=start,
            line_end=end,
            properties={
                "bases": bases,
                "decorators": [d for d, _chain in decorators],
                "is_exported": True,
            },
        )
        extraction.entities.append(entity)

        for _text, chain in decorators:
            if chain:
                extraction.calls.append(
                    CallSite(
                        line=start,
                        callee_name=chain[-1],
                        callee_chain=chain,
                        caller_name=name,
                        caller_line=start,
                    )
                )

        if bases:
            extraction.inheritance.append(
                InheritanceEdge(class_name=name, class_line=start, base_names=bases)
            )

        # Walk methods inside the class body.
        body = find_child_by_field(node, "body")
        if body is None:
            return
        for child in body.children:
            if child.type == "function_definition":
                self._handle_function(child, source, extraction, decorators=[], is_method=True)
            elif child.type == "decorated_definition":
                decs = _parse_decorators(child, source)
                for inner in child.children:
                    if inner.type == "function_definition":
                        self._handle_function(
                            inner, source, extraction, decorators=decs, is_method=True
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
        # Iterative pre-order walk.
        # When we descend into a nested function_definition, switch caller.
        stack: list[tuple[Node, str | None, int | None]] = [
            (node, caller_name, caller_line)
        ]
        while stack:
            current, cname, cline = stack.pop()
            if current.type == "call":
                call = self._parse_call(current, source, cname, cline)
                if call is not None:
                    extraction.calls.append(call)
            # Switch caller when entering a nested function.
            if current.type == "function_definition" and current is not node:
                inner_name_node = find_child_by_field(current, "name")
                if inner_name_node is not None:
                    new_name = text_of(inner_name_node, source)
                    new_line = line_start(current)
                    # Also extract the nested function as its own entity.
                    self._handle_function(
                        current,
                        source,
                        extraction,
                        decorators=[],
                        is_method=False,
                        is_nested=True,
                    )
                    body = find_child_by_field(current, "body")
                    if body is not None:
                        stack.append((body, new_name, new_line))
                    continue
            # Class definitions inside a function body — handle as classes.
            if current.type == "class_definition" and current is not node:
                self._handle_class(current, source, extraction, decorators=[])
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
        chain = _attribute_chain(func, source)
        if not chain:
            return None
        return CallSite(
            line=line_start(call_node),
            callee_name=chain[-1],
            callee_chain=chain,
            caller_name=caller_name,
            caller_line=caller_line,
        )


def _parse_decorators(node: Node, source: bytes) -> list[tuple[str, list[str]]]:
    """Return (text, chain) for each decorator on a decorated_definition.

    `@dataclass` → ("dataclass", ["dataclass"])
    `@auth.required` → ("auth.required", ["auth", "required"])
    `@wraps(f)` → ("wraps(f)", ["wraps"])  — the call target's chain
    """
    out: list[tuple[str, list[str]]] = []
    for dec in find_children_by_type(node, "decorator"):
        # dec.children: [@, <expression>]
        if len(dec.children) < 2:
            continue
        target = dec.children[1]
        chain: list[str] = []
        if target.type == "call":
            func = target.child_by_field_name("function")
            if func is not None:
                chain = _attribute_chain(func, source)
        else:
            chain = _attribute_chain(target, source)
        text = text_of(target, source)
        out.append((text, chain))
    return out


def _attribute_chain(node: Node, source: bytes) -> list[str]:
    """Return the attribute chain for a call target.

    `foo()` → ["foo"]
    `a.b.c()` → ["a", "b", "c"]
    `obj.method()` → ["obj", "method"]
    Returns [] for un-resolvable callees (subscript, call, etc.).
    """
    if node.type == "identifier":
        return [text_of(node, source)]
    if node.type == "attribute":
        obj = node.child_by_field_name("object")
        attr = node.child_by_field_name("attribute")
        if obj is None or attr is None:
            return []
        prefix = _attribute_chain(obj, source)
        if not prefix:
            return []
        return prefix + [text_of(attr, source)]
    return []
