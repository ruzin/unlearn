"""Smoke tests for MCP tool registration and end-to-end execution."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from unlearn.mcp.server import build_server


def _names(tools):
    return {t.name for t in tools}


def test_all_six_tools_registered(python_simple_root: Path):
    server = build_server(python_simple_root)
    tools = asyncio.run(server.list_tools())
    names = _names(tools)
    expected = {
        "impact_analysis",
        "trace_dependencies",
        "find_hotspots",
        "find_dead_code",
        "find_circular_dependencies",
        "get_context",
    }
    assert expected.issubset(names)


def test_impact_analysis_tool_returns_structured_dict(python_simple_root: Path):
    server = build_server(python_simple_root)
    result = asyncio.run(
        server.call_tool("impact_analysis", {"entity": "validate_token"})
    )
    # result is a tuple (text_content, structured_content) in FastMCP 1.x.
    # Both representations should mention the target name.
    if isinstance(result, tuple):
        text_or_struct = result[1] if len(result) > 1 else result[0]
    else:
        text_or_struct = result
    serialised = json.dumps(text_or_struct, default=str)
    assert "validate_token" in serialised


def test_find_dead_code_tool(python_simple_root: Path):
    server = build_server(python_simple_root)
    result = asyncio.run(server.call_tool("find_dead_code", {}))
    serialised = json.dumps(result, default=str)
    assert "old_token_validator" in serialised


def test_graph_stats_tool(python_simple_root: Path):
    server = build_server(python_simple_root)
    result = asyncio.run(server.call_tool("graph_stats", {}))
    serialised = json.dumps(result, default=str)
    assert "files" in serialised
