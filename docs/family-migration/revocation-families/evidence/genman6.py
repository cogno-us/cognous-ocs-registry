"""Generate tests/vectors/r08v6/frozen_baseline_manifest.json: the r08-v5 manifest plus every r08-v5 module, contract, test and vector, each hashed from
`git show <baseline>:<path>` with baseline = Registry main e8b572cc669bee668abc88846f7b071a74f13440. Run from the repository root."""
import glob, hashlib, json, os, subprocess
BASE = "e8b572cc669bee668abc88846f7b071a74f13440"
old = json.loads(subprocess.check_output(["git", "show", BASE + ":tests/vectors/r08v5/frozen_baseline_manifest.json"], text=True))
tracked = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE], text=True).split()
extra = [p for p in tracked if (p.startswith("registry_successor/v5_") and p.endswith(".py")) or p in ("docs/r08-v5-contract.md", "tests/r08v5_support.py")
         or (p.startswith("tests/test_r08v5_") and p.endswith(".py")) or p.startswith("tests/vectors/r08v5/")]
paths = set(old["files"]) | set(extra)
files = {p: hashlib.sha256(subprocess.check_output(["git", "show", BASE + ":" + p])).hexdigest() for p in sorted(paths)}
changed = [p for p in old["files"] if files[p] != old["files"][p]]
print("baseline", BASE, "files", len(files), "previously-frozen changed:", changed)
doc = {"baseline_commit": BASE, "files": files,
       "note": "r08-v5 baseline plus the merged r08-v5 modules, contract, tests and vectors; every file hashed from `git show <baseline>:<path>`",
       "profile": "frozen baseline for r08-v6"}
open("tests/vectors/r08v6/frozen_baseline_manifest.json", "w").write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
