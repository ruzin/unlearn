"""End-to-end: index → cache → load → query."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from unlearn.graph import find_dead_code, impact_analysis
from unlearn.graph.serialise import load_from_disk, save_to_disk
from unlearn.indexer import index_repo


def test_index_cache_reload_gives_identical_queries(
    python_simple_root: Path, tmp_path: Path
):
    fresh = index_repo(python_simple_root)

    cache = tmp_path / "graph.json"
    save_to_disk(fresh.store, str(python_simple_root), cache)
    reloaded, _ = load_from_disk(cache)

    fresh_impact = impact_analysis(fresh.store, "validate_token")
    reloaded_impact = impact_analysis(reloaded, "validate_token")
    assert _normalise(fresh_impact) == _normalise(reloaded_impact)

    fresh_dead = find_dead_code(fresh.store)
    reloaded_dead = find_dead_code(reloaded)
    assert _normalise(fresh_dead) == _normalise(reloaded_dead)


def _normalise(d):
    """Round-trip through JSON with sorted keys, then deep-sort lists of dicts."""
    raw = json.loads(json.dumps(d, sort_keys=True, default=str))
    return _deep_sort(raw)


def _deep_sort(value):
    if isinstance(value, dict):
        return {k: _deep_sort(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        sorted_items = [_deep_sort(v) for v in value]
        try:
            return sorted(sorted_items, key=lambda x: json.dumps(x, sort_keys=True))
        except TypeError:
            return sorted_items
    return value


def test_cli_index_then_info(python_simple_root: Path, tmp_path: Path):
    """Run the CLI as a subprocess; ensure it indexes and then reads stats."""
    # Copy fixture to tmp_path so we don't litter the repo with .unlearn dirs.
    import shutil

    target = tmp_path / "repo"
    shutil.copytree(python_simple_root, target)

    env = {**_clean_env(), "PYTHONPATH": str(Path(__file__).parent.parent / "src")}
    index_proc = subprocess.run(
        [sys.executable, "-m", "unlearn.cli", "index", str(target)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert index_proc.returncode == 0, index_proc.stderr
    assert "Indexed" in index_proc.stdout
    assert (target / ".unlearn" / "graph.json").exists()

    info_proc = subprocess.run(
        [sys.executable, "-m", "unlearn.cli", "info", str(target)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert info_proc.returncode == 0, info_proc.stderr
    payload = json.loads(info_proc.stdout.split("{", 1)[1].rsplit("}", 1)[0].join(["{", "}"]))
    assert payload["files"] >= 10


def _clean_env():
    import os

    e = dict(os.environ)
    return e
