#!/usr/bin/env python3
"""Verify docs/v09/candidate-manifest.json against local clones of the four components.

Git objects only: no network access and no component code is executed. Usage:
    python tools/verify_v09_candidate.py --components-dir DIR
where DIR holds clones named cognous-ocs-registry, cognous-control-plane, cognous-execution-runtime, cognous-stack-qualification
(full history, so the merge commits and their parents exist). Exit 0 only if every check passes; any failure prints the reason and exits 1.
Non-authorizing verification metadata; not a qualification.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent.parent / "docs" / "v09" / "candidate-manifest.json"


def git(repo, *args, check=True):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {repo}: {p.stderr.decode().strip()}")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--components-dir", required=True)
    root = Path(ap.parse_args().components_dir)
    m = json.loads(MANIFEST.read_text())
    problems, ids = [], {}
    for c in m["components"]:
        name = c["repository"].split("/")[-1]
        ids[c["id"]] = (root / name, c)
        repo, sha = root / name, c["main_commit"]
        if not repo.is_dir():
            problems.append(f"{name}: clone missing at {repo}")
            continue
        try:
            if git(repo, "rev-parse", f"{sha}^{{tree}}").stdout.decode().strip() != c["main_tree"]:
                problems.append(f"{name}: tree of {sha} differs from the manifest")
            parents = git(repo, "log", "-1", "--format=%P", sha).stdout.decode().split()
            if parents != c["merge_parents"]:
                problems.append(f"{name}: parents {parents} differ from the manifest {c['merge_parents']}")
            for path, blob in c["blobs_git_sha1"].items():
                got = git(repo, "rev-parse", f"{sha}:{path}", check=False)
                if got.returncode != 0 or got.stdout.decode().strip() != blob:
                    problems.append(f"{name}: blob of {path} differs from the manifest")
            for path, want in c.get("sha256", {}).items():
                data = git(repo, "show", f"{sha}:{path}").stdout
                if hashlib.sha256(data).hexdigest() != want:
                    problems.append(f"{name}: sha256 of {path} differs from the manifest")
        except RuntimeError as exc:
            problems.append(str(exc))
    for q in m.get("qualified_commit_equivalence", []):
        repo, c = ids[q["component"]]
        try:
            anc = git(repo, "merge-base", "--is-ancestor", q["qualified_commit"], c["main_commit"], check=False).returncode == 0
            if anc != q["ancestor_of_main"]:
                problems.append(f"{q['component']}: ancestry of {q['qualified_commit']} differs from the manifest")
            teq = git(repo, "rev-parse", f"{q['qualified_commit']}^{{tree}}").stdout.decode().strip() == c["main_tree"]
            if teq != q["tree_equal_to_main"]:
                problems.append(f"{q['component']}: tree equality of {q['qualified_commit']} differs from the manifest")
        except RuntimeError as exc:
            problems.append(str(exc))
    for p in problems:
        print("FAIL:", p)
    print("OK: manifest matches the local clones" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
