from __future__ import annotations

from pathlib import Path

from unlearn.indexer.extractors import PythonExtractor, TypeScriptExtractor


def _by_name(entities, name):
    return [e for e in entities if e.name == name]


def test_python_extracts_functions_and_classes(python_simple_root: Path):
    ex = PythonExtractor()
    user_src = (python_simple_root / "models" / "user.py").read_bytes()
    result = ex.extract(user_src, "models/user.py")

    assert _by_name(result.entities, "User")[0].kind == "class"
    assert _by_name(result.entities, "User")[0].properties["decorators"] == ["dataclass"]
    assert _by_name(result.entities, "get_user_by_id")[0].kind == "function"


def test_python_resolves_decorators_as_calls(python_simple_root: Path):
    ex = PythonExtractor()
    src = (python_simple_root / "routes" / "users.py").read_bytes()
    result = ex.extract(src, "routes/users.py")

    callees = {(c.callee_name, c.caller_name) for c in result.calls}
    assert ("auth_required", "get_user") in callees
    assert ("auth_required", "create_user") in callees
    # Real call inside body
    assert ("send_welcome_email", "create_user") in callees


def test_python_relative_import_parsing():
    src = b"from .helpers import foo\nfrom ..util import bar\n"
    result = PythonExtractor().extract(src, "pkg/mod.py")
    assert result.imports[0].is_relative
    assert result.imports[0].relative_level == 1
    assert result.imports[0].module == "helpers"
    assert result.imports[0].imported_names == ["foo"]
    assert result.imports[1].relative_level == 2
    assert result.imports[1].module == "util"


def test_python_nested_function_marked_nested(python_simple_root: Path):
    src = (python_simple_root / "auth" / "middleware.py").read_bytes()
    result = PythonExtractor().extract(src, "auth/middleware.py")
    decorated = _by_name(result.entities, "decorated")[0]
    assert decorated.properties["is_nested"] is True
    assert decorated.properties["is_exported"] is False


def test_typescript_extracts_functions_classes_types(typescript_simple_root: Path):
    ex = TypeScriptExtractor("typescript")
    src = (typescript_simple_root / "src" / "types" / "user.ts").read_bytes()
    result = ex.extract(src, "src/types/user.ts")

    names = {(e.kind, e.name) for e in result.entities}
    assert ("type", "UserType") in names
    assert ("function", "makeUser") in names


def test_typescript_arrow_function(typescript_simple_root: Path):
    ex = TypeScriptExtractor("typescript")
    src = (typescript_simple_root / "src" / "utils" / "helpers.ts").read_bytes()
    result = ex.extract(src, "src/utils/helpers.ts")
    names = {e.name for e in result.entities}
    assert "formatCurrency" in names
    assert "slug" in names  # arrow function


def test_typescript_class_with_extends_and_methods():
    src = b"export class A extends B { run() { return 1; } }"
    result = TypeScriptExtractor("typescript").extract(src, "x.ts")
    a = next(e for e in result.entities if e.name == "A")
    assert a.kind == "class"
    assert a.properties["bases"] == ["B"]
    run = next(e for e in result.entities if e.name == "run")
    assert run.properties["is_method"] is True
