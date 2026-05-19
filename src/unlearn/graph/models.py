from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    FILE = "File"
    FUNCTION = "Function"
    CLASS = "Class"
    TYPE = "Type"


class EdgeType(str, Enum):
    CONTAINS = "CONTAINS"
    CALLS = "CALLS"
    IMPORTS = "IMPORTS"
    INHERITS = "INHERITS"
    REFERENCES = "REFERENCES"


@dataclass
class Node:
    id: str
    type: NodeType
    name: str
    file_path: str
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "file_path": self.file_path,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Node:
        return cls(
            id=data["id"],
            type=NodeType(data["type"]),
            name=data["name"],
            file_path=data["file_path"],
            properties=data.get("properties", {}),
        )


@dataclass
class Edge:
    source_id: str
    target_id: str
    type: EdgeType
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.type.value,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Edge:
        return cls(
            source_id=data["source"],
            target_id=data["target"],
            type=EdgeType(data["type"]),
            properties=data.get("properties", {}),
        )


def file_node_id(file_path: str) -> str:
    return file_path


def entity_node_id(file_path: str, name: str, line_start: int) -> str:
    return f"{file_path}::{name}::{line_start}"
