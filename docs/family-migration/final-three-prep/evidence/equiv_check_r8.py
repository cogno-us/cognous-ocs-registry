"""Empirical backstop for the three equivalence proofs in SUMMARY.txt (AN11, AN20/OB27). Run from the repository root with PYTHONPATH=. . Not a proof by itself."""
import itertools
from registry_successor.engine import families_anchor as f, families_observation as o
from registry_successor.compose import CompositionResult
F = f.ANCHOR_FIELD
vals = ["anchor", "no_change", "x", True, None, 1, b"anchor"]
keys = [F, "k", "other", 1, None, "anchor_deadline"]
callers = [None, {}, 5, "x", [F]] + [dict(it) for n in (1, 2, 3) for combo in itertools.product(keys, repeat=n) for it in [zip(combo, itertools.cycle(vals))] if len(dict(zip(combo, itertools.cycle(vals)))) == n]
# AN11 variant: `ANCHOR_FIELD not in snap` instead of `set(snap) != set(ANCHOR_FIELDS)`
def variant(caller):
    snap = f._snapshot(caller, len(f.ANCHOR_FIELDS))
    if snap is None or F not in snap or not f.is_value(snap[F]):
        return None
    return {F: snap[F]}
bad = [c for c in callers if variant(c) != f.normalize_caller(c)]
print("AN11 callers", len(callers), "differences", len(bad))
# AN20/OB27 variant: composing from the record payload itself instead of a copy of it
for name, mod, fam_id, field, good in (("AN20", f, f.FAMILY_ANCHOR, F, "anchor"), ("OB27", o, o.FAMILY_MAX_AGE, o.MAX_AGE_FIELD, 60)):
    diffs = 0
    for payload in [{field: good}, {field: good, "x": 1}, {}, {field: None}, {field: True}]:
        rec = type("Rec", (), {"ok": True, "record": {"family": fam_id, "payload": payload}})()
        before = dict(payload)
        r1 = (f.compose_anchor if mod is f else o.compose_max_age)({field: good}, rec)
        diffs += payload != before  # the composer never mutates the payload it reads, copy or alias
    print(name, "payload mutated by composer:", diffs)
