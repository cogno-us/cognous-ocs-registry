"""Composite family `f1abcd-local-execution-limits` for contract `r08-v4` (docs/r08-v4-contract.md; M3 PR-1).

Payload: EXACTLY nine members: the seven `f1abc` members (five f1ab allow-sets, `max_amount`, `max_effects`; unchanged rules, imported from the
frozen `v3_f1abc` and `v2_f1ab`) plus `allowed_target_prefixes` (list of tokens) and `target_match` (one of `exact`, `segment`, `legacy-prefix`). An
absent member refuses `field_missing`, an extra one `field_unknown`; nothing is ever defaulted (in particular `target_match` has NO default here, even
though the Runtime policy defaults to `segment`).

Source semantics (engine/safe_executor.py `LocalExecutionPolicy._target_allowed`, SEP = "/:"): the accepted set is a UNION over entries; per entry
  exact(e)   = {e}
  segment(e) = {t : t.startswith(e) and (t == e or e[-1] in SEP or t[len(e)] in SEP)}
  legacy(e)  = {t : t.startswith(e)}
so exact(e) <= segment(e) <= legacy(e) PER ENTRY. The mode names alone do NOT order two (list, mode) pairs: a caller `(["a/b"], legacy-prefix)` is
not comparable to a Registry `(["a"], exact)`. Composition therefore never compares modes alone.

Composition (operator `intersection`), a rule that is SOUND (the effective accepted set is a subset of the caller's AND of the Registry's):
  * mode m' = the stricter of the two modes (exact > segment > legacy-prefix);
  * entries P' = every entry e in (P_caller + P_registry) such that the accepted set of e under m' is contained in the accepted set of SOME caller
    entry under the caller mode AND of SOME Registry entry under the Registry mode (`contained`, exact string predicates below);
  * empty P' is deny-all (consumers build no policy).
It is not always COMPLETE: it may narrow below the exact set intersection (for example caller `(["a"], segment)` with Registry `(["a/b"],
legacy-prefix)` yields `(["a/b"], segment)`), never wider. This is documented, not an error. No fallback, no widening, no mode upgrade.

Ceilings and sets compose exactly as in `v3_f1abc`. Caller prefixes must be non-empty tokens (`frozen_token_valid`; the Runtime refuses an empty
prefix list): otherwise `composition_caller_invalid` and nothing is composed. Registry tokens follow the same frozen rule, so a prefix containing a
space or other excluded character cannot be governed (compatibility limitation).

Pure, non-authorizing, unqualified (BUILDER_TESTED). Registered ONLY in the `r08-v4` table. Imports no Runtime or Control Plane module.
"""
from typing import Any, Optional

from registry_successor import common as c
from registry_successor import v3_f1abc
from registry_successor.compose import CompositionResult
from registry_successor.v2_token import frozen_token_valid

FAMILY_F1ABCD = "f1abcd-local-execution-limits"
SET_FIELDS = v3_f1abc.SET_FIELDS
CEILING_FIELDS = v3_f1abc.CEILING_FIELDS
PREFIX_FIELD = "allowed_target_prefixes"
MODE_FIELD = "target_match"
F1ABCD_FIELDS = v3_f1abc.F1ABC_FIELDS + (PREFIX_FIELD, MODE_FIELD)

SEPARATORS = "/:"  # engine/safe_executor._TARGET_SEPARATORS
MODES = ("exact", "segment", "legacy-prefix")
_STRICTNESS = {"legacy-prefix": 0, "segment": 1, "exact": 2}
NOT_NARROWING = v3_f1abc.NOT_NARROWING
AMOUNT_MIN, AMOUNT_MAX = v3_f1abc.AMOUNT_MIN, v3_f1abc.AMOUNT_MAX
EFFECTS_MIN, EFFECTS_MAX = v3_f1abc.EFFECTS_MIN, v3_f1abc.EFFECTS_MAX


def matches(mode: str, entry: str, target: str) -> bool:
    """Whether `target` is accepted by the single `entry` under `mode` (the evaluator's per-entry rule; well-formedness of the target is a separate,
    later check in the Runtime and only ever narrows)."""
    if mode == "exact":
        return target == entry
    if not target.startswith(entry):
        return False
    if mode == "legacy-prefix":
        return True
    return len(target) == len(entry) or entry[-1] in SEPARATORS or target[len(entry)] in SEPARATORS


def contained(mode_a: str, x: str, mode_b: str, y: str) -> bool:
    """True only if EVERY target accepted by entry `x` under `mode_a` is accepted by entry `y` under `mode_b`. Exact string predicates; a False may be a
    conservative answer but a True is always sound."""
    if mode_a == "exact":
        return matches(mode_b, y, x)
    if mode_b == "exact":
        return False  # a segment/legacy entry accepts infinitely many targets, an exact entry one
    if mode_a == "segment":
        if mode_b == "legacy-prefix":
            return x.startswith(y)
        return x == y or (x.startswith(y) and (y[-1] in SEPARATORS or x[len(y)] in SEPARATORS))
    # mode_a == "legacy-prefix"
    if mode_b == "legacy-prefix":
        return x.startswith(y)
    return x.startswith(y) and (y[-1] in SEPARATORS or (len(x) > len(y) and x[len(y)] in SEPARATORS))


def stricter(mode_a: str, mode_b: str) -> str:
    return mode_a if _STRICTNESS[mode_a] >= _STRICTNESS[mode_b] else mode_b


def compose_targets(caller_prefixes, caller_mode: str, registry_prefixes, registry_mode: str) -> tuple:
    """(effective prefixes as a sorted tuple, effective mode). The sound rule of the module docstring."""
    mode = stricter(caller_mode, registry_mode)
    out = set()
    for e in set(caller_prefixes) | set(registry_prefixes):
        if (any(contained(mode, e, caller_mode, ce) for ce in caller_prefixes)
                and any(contained(mode, e, registry_mode, re_) for re_ in registry_prefixes)):
            out.add(e)
    return tuple(sorted(out)), mode


def is_mode(v: Any) -> bool:
    return type(v) is str and v in MODES


def _prefixes_ok(v: Any) -> bool:
    """Plain list, sorted by code point, duplicate-free, bounded; empty is the explicit deny-all."""
    if type(v) is not list or len(v) > c.MAX_ENTRIES:
        return False
    return all(type(x) is str and frozen_token_valid(x) for x in v) and v == sorted(set(v))


def payload_validator(payload: Any) -> Optional[str]:
    """None when valid, else a shape code in the v1 order (`field_type_invalid` before `field_invalid`). Safe to call alone."""
    if type(payload) is not dict or not all(type(k) is str for k in payload):
        return "field_type_invalid"
    keys = set(payload)
    if keys - set(F1ABCD_FIELDS):
        return "field_unknown"
    if set(F1ABCD_FIELDS) - keys:
        return "field_missing"
    if not all(type(payload[k]) is list for k in SET_FIELDS + (PREFIX_FIELD,)):
        return "field_type_invalid"
    if not all(type(payload[k]) is int for k in CEILING_FIELDS):
        return "field_type_invalid"
    if type(payload[MODE_FIELD]) is not str:
        return "field_type_invalid"
    if not all(type(x) is str for x in payload[PREFIX_FIELD]):
        return "field_type_invalid"
    code = v3_f1abc.payload_validator({k: payload[k] for k in v3_f1abc.F1ABC_FIELDS})  # the frozen seven-member validator, by import
    if code:
        return code
    if not _prefixes_ok(payload[PREFIX_FIELD]) or not is_mode(payload[MODE_FIELD]):
        return "field_invalid"
    return None


def normalize_caller(caller: Any) -> Optional[dict]:
    """Copy of a well-formed caller policy, or None: exactly the nine keys; the seven f1abc members as in `v3_f1abc`; prefixes a NON-EMPTY
    list/tuple/set/frozenset of valid tokens (sorted tuple); `target_match` an exact str in MODES."""
    snap = v3_f1abc._snapshot(caller, len(F1ABCD_FIELDS))
    if snap is None or set(snap) != set(F1ABCD_FIELDS):
        return None
    base = v3_f1abc.normalize_caller({k: snap[k] for k in v3_f1abc.F1ABC_FIELDS})
    if base is None:
        return None
    prefixes = snap[PREFIX_FIELD]
    if type(prefixes) not in (list, tuple, set, frozenset) or not prefixes:
        return None
    if not all(type(x) is str and frozen_token_valid(x) for x in prefixes) or not is_mode(snap[MODE_FIELD]):
        return None
    return {**base, PREFIX_FIELD: tuple(sorted(set(prefixes))), MODE_FIELD: snap[MODE_FIELD]}


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def _record_payload(record: Any) -> tuple:
    if getattr(record, "ok", False) is not True:
        return None, "composition_record_invalid"
    body = getattr(record, "record", None)
    if type(body) is not dict:
        return None, "composition_record_invalid"
    family, payload = body.get("family"), body.get("payload")
    if type(family) is not str or family != FAMILY_F1ABCD:
        return None, "composition_family_unsupported"
    if type(payload) is not dict:
        return None, "composition_record_invalid"
    snap = dict(payload)
    if payload_validator(snap) is not None:
        return None, "composition_record_invalid"
    return snap, None


def compose_f1abcd(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    try:
        if type(operator) is not str or operator != "intersection":
            return _refuse("composition_operator_unsupported")
        payload, code = _record_payload(record)
        if payload is None:
            return _refuse(code)
        cal = normalize_caller(caller)
        if cal is None:
            return _refuse("composition_caller_invalid")
        effective = {f: tuple(sorted(set(cal[f]) & set(payload[f]))) for f in SET_FIELDS}
        effective["max_amount"] = min(cal["max_amount"], payload["max_amount"])
        effective["max_effects"] = min(cal["max_effects"], payload["max_effects"])
        prefixes, mode = compose_targets(cal[PREFIX_FIELD], cal[MODE_FIELD], payload[PREFIX_FIELD], payload[MODE_FIELD])
        effective[PREFIX_FIELD], effective[MODE_FIELD] = prefixes, mode
        deny = (tuple(f for f in SET_FIELDS if not effective[f]) + (("max_effects",) if payload["max_effects"] == 0 else ())
                + ((PREFIX_FIELD,) if not prefixes else ()))
        wider = [k for k in CEILING_FIELDS if payload[k] > cal[k]]
        if _STRICTNESS[payload[MODE_FIELD]] < _STRICTNESS[cal[MODE_FIELD]]:
            wider.append(MODE_FIELD)
        detail = (NOT_NARROWING + ":" + ",".join(wider)) if wider else ""
        return CompositionResult(True, None, detail, effective, bool(deny), deny)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
