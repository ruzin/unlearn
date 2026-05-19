from __future__ import annotations

from typing import Iterator

from tree_sitter import Node


def text_of(node: Node | None, source: bytes) -> str:
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def walk(node: Node) -> Iterator[Node]:
    """Iterative pre-order traversal."""
    stack: list[Node] = [node]
    while stack:
        current = stack.pop()
        yield current
        # children: push reversed so traversal is left-to-right.
        stack.extend(reversed(current.children))


def find_child_by_field(node: Node, field_name: str) -> Node | None:
    return node.child_by_field_name(field_name)


def find_children_by_type(node: Node, type_name: str) -> list[Node]:
    return [c for c in node.children if c.type == type_name]


def first_named_child_of_type(node: Node, type_name: str) -> Node | None:
    for c in node.children:
        if c.type == type_name:
            return c
    return None


def line_start(node: Node) -> int:
    return node.start_point[0] + 1


def line_end(node: Node) -> int:
    return node.end_point[0] + 1
