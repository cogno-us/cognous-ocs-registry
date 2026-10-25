"""S05 independent oracle for the three registry-overlaid LocalExecutionPolicy allow-lists (frozen before the harness).

Plan: OCS-REG-PLAN v1.1 S05 (blob 6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2).
Constitution: cognous-engineering-constitution 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b.

Pure Python. It imports nothing from the Runtime (engine), the S03 validator or the S04 consumer, so its expected
outcomes cannot depend on the candidate implementation. It encodes only the documented rule, read from the historical
policy source (baseline engine/safe_executor.py, LocalExecutionPolicy.check) and the S04 authorization:

  effective_allowed[field] = caller_allowed[field] ∩ registry_allowed[field]      (S04 required semantics)
  with every other restriction allowing, an operation is refused by the FIRST failing membership test in the
  fixed order adapter, action, unit, with the historical reason texts; otherwise it is admitted.

The oracle is frozen: tests/test_s05_equivalence.py pins this file's git blob id. Changing an expectation requires a
separately recorded amendment, never an edit to obtain a pass.
"""
from itertools import product

FIELDS = ("allowed_adapters", "allowed_actions", "allowed_units")  # check order
OP_KEY = {"allowed_adapters": "adapter", "allowed_actions": "action", "allowed_units": "unit"}
REASON = {
    "allowed_adapters": "local adapter restriction",
    "allowed_actions": "local action restriction",
    "allowed_units": "local unit restriction",
}
CODE = {"allowed_adapters": "a", "allowed_actions": "x", "allowed_units": "u"}  # "A" means admitted

ADMIT = "A"

VALUES = {
    "allowed_adapters": ("urn:s05:adapter-1", "urn:s05:adapter-2", "urn:s05:adapter-3"),
    "allowed_actions": ("act.s05.one", "act.s05.two", "act.s05.three"),
    "allowed_units": ("USD", "EUR", "GBP"),
}
OUTSIDE = {
    "allowed_adapters": "urn:s05:adapter-outside",
    "allowed_actions": "act.s05.outside",
    "allowed_units": "JPY",
}


def subsets(values, *, non_empty=False):
    """All subsets of `values` as sorted tuples, in a fixed deterministic order."""
    out = []
    for mask in range(2 ** len(values)):
        chosen = tuple(v for i, v in enumerate(values) if mask >> i & 1)
        if chosen or not non_empty:
            out.append(tuple(sorted(chosen)))
    return out


def effective(caller: dict, registry: dict) -> dict:
    """Set intersection per field. Inputs map field name to an iterable of strings."""
    return {f: frozenset(caller[f]) & frozenset(registry[f]) for f in FIELDS}


def verdict(op: dict, sets: dict):
    """None if admitted; otherwise the historical reason text of the first failing check. Other checks allow."""
    for f in FIELDS:
        if op[OP_KEY[f]] not in sets[f]:
            return REASON[f]
    return None


def code(op: dict, sets: dict) -> str:
    for f in FIELDS:
        if op[OP_KEY[f]] not in sets[f]:
            return CODE[f]
    return ADMIT


# ---------------------------------------------------------------------------- grids

def _sized(n):
    return {f: VALUES[f][:n] for f in FIELDS}


def g1_caller_policies():
    """G1: universe of 2 values per field; caller allow-lists are every subset (including empty): 4**3 = 64."""
    u = _sized(2)
    per = [subsets(u[f]) for f in FIELDS]
    return [dict(zip(FIELDS, combo)) for combo in product(*per)]


def g1_registry_records():
    """G1: registry allow-lists are every non-empty subset (the S03 record rule): 3**3 = 27."""
    u = _sized(2)
    per = [subsets(u[f], non_empty=True) for f in FIELDS]
    return [dict(zip(FIELDS, combo)) for combo in product(*per)]


def g1_operations():
    """G1: each operation value is one of the 2 universe values or one value outside every list: 3**3 = 27."""
    per = [VALUES[f][:2] + (OUTSIDE[f],) for f in FIELDS]
    return [{OP_KEY[f]: v for f, v in zip(FIELDS, combo)} for combo in product(*per)]


def g2_pairs(field):
    """G2: universe of 3 values; only `field` varies. Caller subsets 8 x registry non-empty subsets 7 = 56 pairs.
    The other two fields allow the whole universe in both caller and registry, so they never refuse a universe value."""
    full = {f: VALUES[f] for f in FIELDS}
    pairs = []
    for c in subsets(VALUES[field]):
        for r in subsets(VALUES[field], non_empty=True):
            caller, registry = dict(full), dict(full)
            caller[field], registry[field] = c, r
            pairs.append((caller, registry))
    return pairs


def g2_operations(field):
    """G2: the field under test takes the 3 universe values and one outside value; others use their first value."""
    ops = []
    for v in VALUES[field] + (OUTSIDE[field],):
        op = {OP_KEY[f]: VALUES[f][0] for f in FIELDS}
        op[OP_KEY[field]] = v
        ops.append(op)
    return ops
