"""Generate tests/vectors/r08v7/frozen_baseline_manifest.json: the r08-v6 manifest plus every r08-v6 module, contract, test and vector, each hashed from
`git show <baseline>:<path>` with baseline = the r08-v6 head 42a666328b974a7581013358bcf8bc7b9eac7761. Run from the repository root."""
import hashlib, json, subprocess
BASE = "42a666328b974a7581013358bcf8bc7b9eac7761"
old = json.loads(subprocess.check_output(["git", "show", BASE + ":tests/vectors/r08v6/frozen_baseline_manifest.json"], text=True))
tracked = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE], text=True).split()
extra = [p for p in tracked if (p.startswith("registry_successor/v6_") and p.endswith(".py")) or p in ("docs/r08-v6-contract.md", "tests/r08v6_support.py")
         or (p.startswith("tests/test_r08v6_") and p.endswith(".py")) or p.startswith("tests/vectors/r08v6/")]
paths = set(old["files"]) | set(extra)
files = {p: hashlib.sha256(subprocess.check_output(["git", "show", BASE + ":" + p])).hexdigest() for p in sorted(paths)}
changed = [p for p in old["files"] if files[p] != old["files"][p]]
print("baseline", BASE, "files", len(files), "previously-frozen changed vs the v6 manifest:", changed)
doc = {"baseline_commit": BASE, "files": files,
       "note": "r08-v6 baseline plus the r08-v6 modules, contract, tests and vectors; every file hashed from `git show <baseline>:<path>`",
       "profile": "frozen baseline for r08-v7"}
open("tests/vectors/r08v7/frozen_baseline_manifest.json", "w").write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
