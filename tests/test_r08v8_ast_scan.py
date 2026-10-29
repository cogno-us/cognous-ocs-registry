"""AST scan of the NEW `r08-v8` modules: no interpreter, no executable rule, no I/O, no clock, no randomness, no mutable global, no new reason code (APPROVED CANDIDATE;
BUILDER_TESTED; not independently qualified). A policy is data validated by exact type and range; nothing here evaluates text or loads code.
"""
import ast
from pathlib import Path

import pytest

from registry_successor import v2_codes

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "registry_successor"
NEW = [PKG / "engine" / "families_anchor.py", PKG / "engine" / "families_observation.py", PKG / "v8_decision.py", PKG / "v8_families.py", PKG / "v8_policy_identity.py"]
FAMILY_MODULES = NEW[:2]
BANNED_CALLS = {"eval", "exec", "compile", "open", "__import__", "getattr_static", "input", "print", "breakpoint", "globals", "locals", "vars", "setattr", "delattr", "id", "hash"}
BANNED_IMPORTS = {"subprocess", "socket", "os", "sys", "pickle", "importlib", "ctypes", "marshal", "http", "urllib", "time", "datetime", "random", "secrets", "json", "re", "shutil",
                  "pathlib", "tempfile", "threading", "multiprocessing", "asyncio", "builtins", "codecs", "runpy", "code", "ast", "operator", "functools", "inspect"}
BANNED_ATTRS = {"system", "popen", "exec_module", "load_module", "literal_eval", "loads", "load", "dumps", "dump", "now", "today", "time", "monotonic", "random", "urandom",
                "__subclasses__", "__globals__", "__builtins__", "__dict__", "__class__", "__bases__", "__mro__", "__code__"}


def tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", NEW, ids=lambda p: p.name)
def test_no_interpreter_no_io_no_clock_no_randomness(path):
    t = tree(path)
    called = {n.func.id for n in ast.walk(t) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not called & BANNED_CALLS, called & BANNED_CALLS
    imported = {a.name.split(".")[0] for n in ast.walk(t) if isinstance(n, ast.Import) for a in n.names}
    imported |= {(n.module or "").split(".")[0] for n in ast.walk(t) if isinstance(n, ast.ImportFrom)}
    assert not imported & BANNED_IMPORTS, imported & BANNED_IMPORTS
    attrs = {n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)}
    assert not attrs & BANNED_ATTRS, attrs & BANNED_ATTRS
    names = {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}
    assert not names & {"__builtins__", "__import__", "eval", "exec"}, names
    assert not [n for n in ast.walk(t) if isinstance(n, (ast.Global, ast.Nonlocal, ast.Lambda, ast.Await, ast.AsyncFunctionDef, ast.Yield, ast.YieldFrom, ast.With, ast.AsyncWith))]
    text = path.read_text(encoding="utf-8")
    assert "control_plane" not in text.replace("control-plane", "") and "moltbot" not in text.lower()


@pytest.mark.parametrize("path", NEW, ids=lambda p: p.name)
def test_imports_are_only_the_registry_successor_package_and_typing_helpers(path):
    t = tree(path)
    allowed_roots = {"registry_successor", "typing", "collections", "itertools", "types"}
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            assert {a.name.split(".")[0] for a in n.names} <= allowed_roots
        if isinstance(n, ast.ImportFrom):
            assert n.level == 0 and (n.module or "").split(".")[0] in allowed_roots, n.module


@pytest.mark.parametrize("path", FAMILY_MODULES, ids=lambda p: p.name)
def test_no_mutable_module_global_and_no_class_state(path):
    t = tree(path)
    assert not [n for n in t.body if isinstance(n, ast.ClassDef)]
    for node in t.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            assert not isinstance(value, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)), ast.unparse(node)
            if isinstance(value, ast.Call):
                assert ast.unparse(value.func) in ("MappingProxyType",), ast.unparse(node)
    import importlib
    mod = importlib.import_module("registry_successor.engine." + path.stem)
    for name, value in vars(mod).items():
        if not name.startswith("__"):
            assert not isinstance(value, (list, dict, set, bytearray)), (path.name, name)


def test_only_codes_of_the_closed_vocabulary_are_emitted_and_none_is_added():
    emitted = set()
    for path in FAMILY_MODULES:
        for node in ast.walk(tree(path)):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and (node.value.startswith(("field_", "composition_"))):
                emitted.add(node.value)
    assert emitted == {"field_type_invalid", "field_unknown", "field_missing", "field_invalid", "composition_operator_unsupported", "composition_record_invalid",
                       "composition_family_unsupported", "composition_caller_invalid"}
    assert emitted <= set(v2_codes.CODES_V2_REV2)
    assert len(v2_codes.CODES_V2_REV2) == 51  # no new reason code: the closed vocabulary is the merged one
    assert not [p for p in NEW if "CODES_V2_REV3" in p.read_text(encoding="utf-8")]


def test_every_refusal_call_in_the_family_modules_uses_a_literal_code_of_the_closed_vocabulary():
    for path in FAMILY_MODULES:
        for node in ast.walk(tree(path)):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_refuse":
                arg = node.args[0]
                if isinstance(arg, ast.Name):  # the anchor module forwards the literal code returned by `_record_payload` (covered by the emitted-literals test)
                    assert arg.id == "code" and path.name == "families_anchor.py", ast.unparse(node)
                else:
                    assert isinstance(arg, ast.Constant) and arg.value in v2_codes.CODES_V2_REV2, ast.unparse(node)


def test_family_modules_do_not_import_each_other_or_any_other_family_or_the_profiles():
    for path in FAMILY_MODULES:
        for n in ast.walk(tree(path)):
            if isinstance(n, ast.ImportFrom):
                assert n.module in ("registry_successor", "registry_successor.compose", "collections.abc", "typing", "itertools", "types"), (path.name, n.module)
