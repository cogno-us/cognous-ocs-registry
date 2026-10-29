"""Generate tests/vectors/r08v8/frozen_baseline_manifest.json: the r08-v7 manifest plus every r08-v7 module, engine module, contract, test and vector that this change does NOT
edit, each hashed from `git show <baseline>:<path>` with baseline = Registry main 67512a71546748cd888e4cf790485ea0bef9199a. The three engine files that carry ADDITIVE edits
(profile.py, identity.py, profiles.py) are recorded as `additive_edits`: baseline sha256 plus the exact line-level diff (current lines and the baseline lines they replace), so a
test can reverse the edit and prove the baseline is recovered byte for byte. Run from the repository root. APPROVED CANDIDATE; BUILDER_TESTED."""
import difflib, hashlib, json, subprocess
BASE = "67512a71546748cd888e4cf790485ea0bef9199a"
EDITED = ["registry_successor/engine/profile.py", "registry_successor/engine/identity.py", "registry_successor/engine/profiles.py"]
GUARDS_EDITED = {"tests/test_r08v7_frozen_baseline.py", "tests/test_ext_s1_5_identity_module.py"}  # allowlist-only edits, not frozen


def show(p):
    return subprocess.check_output(["git", "show", BASE + ":" + p])


old = json.loads(show("tests/vectors/r08v7/frozen_baseline_manifest.json"))
tracked = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE], text=True).split()
extra = [p for p in tracked if p not in EDITED and p not in GUARDS_EDITED and (
    (p.startswith("registry_successor/v7_") and p.endswith(".py")) or (p.startswith("registry_successor/engine/") and p.endswith(".py"))
    or p == "docs/r08-v7-contract.md" or p == "tests/r08v7_support.py" or (p.startswith("tests/test_r08v7_") and p.endswith(".py"))
    or p.startswith("tests/vectors/r08v7/"))]
paths = set(old["files"]) | set(extra)
files = {p: hashlib.sha256(show(p)).hexdigest() for p in sorted(paths)}
changed = [p for p in old["files"] if files[p] != old["files"][p]]
print("baseline", BASE, "files", len(files), "previously-frozen changed vs the v7 manifest:", changed)
additive = {}
for p in EDITED:
    b = show(p).decode("utf-8").splitlines(keepends=True)
    cur = open(p, encoding="utf-8").read().splitlines(keepends=True)
    ops = [{"tag": tag, "baseline_lines": [i1, i2], "current_lines": [j1, j2], "baseline_text": "".join(b[i1:i2]), "current_text": "".join(cur[j1:j2])}
           for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, b, cur, autojunk=False).get_opcodes() if tag != "equal"]
    additive[p] = {"baseline_sha256": hashlib.sha256(show(p)).hexdigest(), "ops": ops}
    print(p, [(o["tag"], o["baseline_lines"], o["current_lines"]) for o in ops])
doc = {"baseline_commit": BASE, "files": files, "additive_edits": additive,
       "note": "r08-v7 baseline plus the r08-v7 modules, engine modules, contract, tests and vectors this change does not edit; every file hashed from `git show <baseline>:<path>`",
       "profile": "frozen baseline for r08-v8 (APPROVED CANDIDATE)"}
open("tests/vectors/r08v8/frozen_baseline_manifest.json", "w").write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
