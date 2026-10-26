"""R08-S01 isolation checks (developer-tested): the successor package is independent of the frozen modules and the Runtime,
performs no I/O, and its refusal codes are a closed, documented set. Bytes of frozen artifacts are pinned by tests/test_s06_integrity.py.
"""
import ast
import re
from pathlib import Path

from registry_successor import common

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "registry_successor"
FORBIDDEN_IMPORTS = {"registry_contract", "registry_consumer", "engine", "baseline", "socket", "subprocess", "urllib", "http",
                     "requests", "os", "pathlib", "shutil", "random", "secrets", "cryptography", "nacl", "ssl"}
ALLOWED_TIME_USE = {"datetime"}


def _imports(path):
    tree = ast.parse(path.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def test_successor_package_has_no_forbidden_imports():
    for path in sorted(PKG.glob("*.py")):
        bad = _imports(path) & FORBIDDEN_IMPORTS
        assert not bad, (path.name, bad)


def test_no_module_reads_the_clock_or_opens_files():
    for path in sorted(PKG.glob("*.py")):
        text = path.read_text()
        assert not re.search(r"datetime\.now|utcnow|\btime\.time\(|\btime\.monotonic", text), path.name
        assert not re.search(r"\bopen\(", text), path.name


def _emitted_codes():
    """String codes passed to the refusal helpers or listed as dict values (a static approximation)."""
    pattern = re.compile(r"[a-z]+(?:_[a-z0-9]+)+\Z")
    found = set()
    for path in sorted(PKG.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") in {"_refuse", "fail", "_fail"}:
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    found.add((path.name, node.args[0].value))
            if isinstance(node, ast.Dict):
                for value in node.values:
                    if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value in common.CODES:
                        found.add((path.name, value.value))
    return {item for item in found if pattern.match(item[1])}


def test_every_refusal_code_emitted_by_modules_is_in_the_closed_set():
    emitted = _emitted_codes()
    assert emitted, "static scan found nothing"
    # Amended narrowly (Architect Batch 6 ruling 4.4): every module is held to the 46 `r08-v1` codes EXCEPT the one registered successor module, which may
    # also emit the revision-2 vocabulary (`CODES_V2_REV2`: the 48 plus the three additive codes). The two v2-only codes of revision 1 and everything
    # outside revision 2 stay refused everywhere (tests/test_ext_s1_5_guard_amendment.py holds the negative regressions).
    from registry_successor.v2_codes import CODES_V2_REV2

    allowed = {"v2_policy_identity.py": set(CODES_V2_REV2) - {"selection_withdrawn", "trust_snapshot_version_stale"}}
    unknown = {item for item in emitted if item[1] not in allowed.get(item[0], set(common.CODES))}
    assert not unknown, sorted(unknown)


def test_codes_have_layer_and_meaning():
    assert common.CODES
    for code, (layer, meaning) in common.CODES.items():
        assert re.fullmatch(r"[a-z]+(_[a-z0-9]+)*", code)
        assert layer and meaning


def test_implementation_doc_lists_exactly_the_closed_codes():
    doc = (ROOT / "docs" / "r08-s01-implementation.md").read_text()
    listed = set(re.findall(r"^\| `([a-z_0-9]+)` \|", doc, flags=re.M))
    assert listed == set(common.CODES)
