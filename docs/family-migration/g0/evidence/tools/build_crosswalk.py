#!/usr/bin/env python3
"""Build the machine-readable S02 old-to-current crosswalk (all 620 historical rows).

Inputs: docs/s02-evidence/W1..W9.md (read-only, historical). Needs full-object clones of the Runtime and Control Plane that contain the historical
pins and the current mains. Method (deterministic, no heuristics on meaning): resolve each row's historical file reference with the per-worker abbreviation
table, then map the cited old line ranges onto the current file with `git diff -U0 -M` hunks. The historical classification is copied unchanged.
"""
import json, re, subprocess, sys, collections
from pathlib import Path

REG = Path(sys.argv[1])            # registry checkout (reads docs/s02-evidence)
RT, CP = Path(sys.argv[2]), Path(sys.argv[3])
OLD = {"runtime": "ec728da6dc301a664b331ac8986afd6e850a1273", "control_plane": "0a41faa972699f7ec3063967a14cd9bdd3e67d27"}
NEW = {"runtime": sys.argv[4], "control_plane": sys.argv[5]}
REPO = {"runtime": RT, "control_plane": CP}
CPSRC = "src/agent_control_plane/"
ABBR = {
 "W3": {"LAE": "engine/local_authority_effect.py", "RC": "engine/revocation_closeout.py", "RR": "engine/recovery_resolution.py", "AX": "engine/atomic_local_control_plane_executor.py",
        "DC": "engine/delayed_commit_destination.py", "DD": "engine/dedupe_destination.py"},
 "W8": {"RA": CPSRC + "runtime_authority.py", "FR": CPSRC + "freshness.py", "RV": CPSRC + "reversibility.py", "LAE": CPSRC + "local_authority_effect.py",
        "WI": CPSRC + "witness.py", "HI": CPSRC + "holder_inventory.py", "OI": CPSRC + "operation_identity.py"},
}
DEFAULT_FILE = {"W1": "engine/safe_executor.py", "W6": CPSRC + "bounded.py"}
WREPO = {"W1": "runtime", "W2": "runtime", "W3": "runtime", "W4": "control_plane", "W5": "control_plane", "W6": "control_plane", "W7": "control_plane", "W8": "control_plane", "W9": "control_plane"}


def git(repo, *a):
    p = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)
    return p.returncode, p.stdout


def parse_rows():
    rows = []
    for f in sorted((REG / "docs" / "s02-evidence").glob("W*.md")):
        for l in f.read_text().splitlines():
            if re.match(r"\| W\d+-\d+", l):
                c = [x.strip() for x in l.strip().strip("|").split("|")]
                rows.append(dict(zip(["id", "loc", "construct", "encodes", "cls", "evaluator", "inputs", "failure", "rationale", "tests", "tier"], c)))
    return rows


TOK = re.compile(r"(?:(?P<pre>[A-Za-z0-9_./-]+\.(?:py|json)|[A-Z]{2,3}):)?(?P<rng>\d+(?:-\d+)?(?:\s*,\s*\d+(?:-\d+)?)*)")


def refs(row):
    w = row["id"].split("-")[0]
    out, bad = [], []
    last = None
    for m in TOK.finditer(row["loc"].replace(" (docstring)", "")):
        pre = m.group("pre")
        if pre:
            last = pre
        file = last
        if file is None:
            file = DEFAULT_FILE.get(w)
        elif file in ABBR.get(w, {}):
            file = ABBR[w][file]
        elif file.endswith((".py", ".json")) and "/" not in file:
            file = (CPSRC if WREPO[w] == "control_plane" else "engine/") + file
        elif file.endswith((".py", ".json")):
            file = file if file.startswith(("engine/", "src/")) else (CPSRC + file if WREPO[w] == "control_plane" else file)
        else:
            bad.append(m.group(0)); continue
        if file is None:
            bad.append(m.group(0)); continue
        for part in re.split(r"\s*,\s*", m.group("rng")):
            a, _, b = part.partition("-"); out.append((file, int(a), int(b or a)))
    return out, bad


_hunks = {}


def hunks(repo_key, path):
    k = (repo_key, path)
    if k in _hunks: return _hunks[k]
    repo = REPO[repo_key]
    rc_o, _ = git(repo, "cat-file", "-e", f"{OLD[repo_key]}:{path}")
    exists_old = rc_o == 0
    rc_n, _ = git(repo, "cat-file", "-e", f"{NEW[repo_key]}:{path}")
    exists_new = rc_n == 0
    res = {"exists_old": exists_old, "exists_new": exists_new, "hunks": [], "renamed_to": None, "same_blob": False}
    if exists_old and exists_new:
        _, o = git(repo, "rev-parse", f"{OLD[repo_key]}:{path}"); _, n = git(repo, "rev-parse", f"{NEW[repo_key]}:{path}")
        res["same_blob"] = o.strip() == n.strip()
        if not res["same_blob"]:
            _, d = git(repo, "diff", "-U0", "--no-renames", OLD[repo_key], NEW[repo_key], "--", path)
            for m in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", d, re.M):
                oa, oc, na, nc = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1), int(m.group(3)), int(m.group(4) if m.group(4) is not None else 1)
                res["hunks"].append((oa, oc, na, nc))
    elif exists_old and not exists_new:
        _, d = git(repo, "diff", "-M", "--name-status", OLD[repo_key], NEW[repo_key])
        for l in d.splitlines():
            p = l.split("\t")
            if p[0].startswith("R") and p[1] == path: res["renamed_to"] = p[2]
    _hunks[k] = res
    return res


def map_range(h, a, b):
    """Map old [a,b] to new using -U0 hunks; return (status, new_a, new_b)."""
    shift = 0
    touched = []
    for oa, oc, na, nc in h["hunks"]:
        o_start = oa if oc else oa + 1          # first old line touched (for pure insertion oc==0: insertion point after oa)
        o_end = oa + oc - 1
        if oc == 0:                              # pure insertion after old line oa
            if a <= oa < b: touched.append((oa, nc))
            elif oa < a: shift += nc
            continue
        if o_end < a: shift += nc - oc
        elif o_start > b: pass
        else: touched.append((o_start, o_end))
    if touched: return "CHANGED", None, None
    return "UNCHANGED_SHIFTED" if shift else "UNCHANGED", a + shift, b + shift


def main():
    out = []
    for r in parse_rows():
        w = r["id"].split("-")[0]; rk = WREPO[w]
        rf, bad = refs(r)
        entries, statuses = [], []
        for f, a, b in rf:
            h = hunks(rk, f)
            if not h["exists_old"]:
                st, cf, na, nb = "UNRESOLVABLE_REFERENCE", None, None, None
            elif h["renamed_to"]:
                st, cf, na, nb = "MOVED", h["renamed_to"], None, None
            elif not h["exists_new"]:
                st, cf, na, nb = "DELETED", None, None, None
            elif h["same_blob"]:
                st, cf, na, nb = "UNCHANGED", f, a, b
            else:
                s, na, nb = map_range(h, a, b); st, cf = s, f
            oldlen = None
            if h["exists_old"]:
                rc, txt = git(REPO[rk], "show", f"{OLD[rk]}:{f}"); oldlen = len(txt.splitlines())
            if oldlen is not None and b > oldlen and st in ("UNCHANGED", "UNCHANGED_SHIFTED", "CHANGED"):
                st = "FILE_UNCHANGED_COORDINATE_UNMAPPED" if h["same_blob"] else "FILE_CHANGED_COORDINATE_UNMAPPED"
                na = nb = None
            entries.append({"old_file": f, "old_lines": [a, b], "old_file_length": oldlen, "status": st, "current_file": cf, "current_lines": [na, nb] if na else None}); statuses.append(st)
        if bad or not entries: statuses.append("UNRESOLVABLE_REFERENCE")
        order = ["DELETED", "MOVED", "FILE_CHANGED_COORDINATE_UNMAPPED", "CHANGED", "UNRESOLVABLE_REFERENCE", "FILE_UNCHANGED_COORDINATE_UNMAPPED", "UNCHANGED_SHIFTED", "UNCHANGED"]
        overall = next((s for s in order if s in statuses), "UNRESOLVABLE_REFERENCE")
        out.append({"id": r["id"], "worker": w, "repository": "cogno-us/cognous-execution-runtime" if rk == "runtime" else "cogno-us/cognous-control-plane",
                    "historical": {"loc": r["loc"], "construct": r["construct"], "class": r["cls"], "tier": r["tier"], "evaluator": r["evaluator"]},
                    "old_source_sha": OLD[rk], "current_source_sha": NEW[rk], "references": entries, "unparsed_reference_tokens": bad, "mechanical_status": overall,
                    "semantic_status": None, "g0_resolution": None})
    json.dump(out, sys.stdout, indent=1)
    c = collections.Counter(x["mechanical_status"] for x in out); print(dict(c), file=sys.stderr)


main()
