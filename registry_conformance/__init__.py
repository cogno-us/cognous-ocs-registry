"""OCS consumer activation / high-water conformance kit (EXT-S1-8).

IMPLEMENTED / DEVELOPER-TESTED. Not independently qualified. A conformance
kit, not an activation store: pure functions and vectors, no I/O, no
persistence, no clock reads. Not imported by any registry core module.

``highwater`` holds the pure transition (``advance``) and derivation
(``policy_state``) functions. This module holds the strict vector validator
and the pure vector runner used by the tests and by component owners.
"""

import copy
import itertools

from . import highwater
from .highwater import (  # noqa: F401  (re-exported public surface)
    ACCEPT, REFUSE, REFUSE_STALE, UNKNOWN_FAIL_CLOSED, VERDICTS, advance, empty_state,
    policy_state, scope_key, verify_state,
)

VECTOR_SCHEMA = "ocs-conformance-vectors/1"
VECTOR_LABEL = "SYNTHETIC-TEST-ONLY"


class MalformedVector(ValueError):
    """Raised when a vector document does not meet the strict vector schema."""


_STEP_KEYS = {
    "advance": ({"op", "obs", "expect"}, {"note", "raw"}),
    "policy_state": ({"op", "scope", "now", "expect"}, {"known_selection", "note"}),
    "save": ({"op", "name"}, {"note"}),
    "swap_to": ({"op", "name"}, {"note"}),
    "tear": ({"op", "kind"}, {"scope", "note"}),
    "concurrent": ({"op", "observations", "expect"}, {"note"}),
    "check": ({"op", "expect"}, {"note"}),
}
_TEARS = ("state_ahead_of_log", "log_ahead_of_state", "log_entry_corrupted", "row_validity_extended",
          "row_issuer_changed", "revoked_set_truncated", "ratchet_cleared")
_ALLOWED_EXPECT_ADVANCE = {"verdict", "code", "applied", "fallback_reason"}
_ALLOWED_VERDICT_KEYS = {"verdict", "code", "applied", "fallback", "fallback_reason", "activation_ref"}
_CHECK_KEYS = {"log_length", "evidence_count", "store", "row", "row_absent", "high_water", "revoked", "scope_required", "rebaselines"}


def _bad(msg):
    raise MalformedVector(msg)


def _is_int(x):
    return type(x) is int


def validate_vector_set(doc):
    """Strictly validate a vector document; raise MalformedVector on any defect."""
    if not isinstance(doc, dict):
        _bad("document must be an object")
    allowed = {"schema", "label", "status", "scope_base", "defaults", "vectors"}
    if set(doc) - allowed or not {"schema", "label", "vectors"} <= set(doc):
        _bad("document keys")
    if doc["schema"] != VECTOR_SCHEMA:
        _bad("schema")
    if doc["label"] != VECTOR_LABEL:
        _bad("label must be SYNTHETIC-TEST-ONLY")
    base = doc.get("scope_base", {})
    if not isinstance(base, dict) or not all(isinstance(v, str) for v in base.values()):
        _bad("scope_base")
    defaults = doc.get("defaults", {})
    if not isinstance(defaults, dict) or not all(k in highwater.KINDS and isinstance(v, dict) for k, v in defaults.items()):
        _bad("defaults")
    vectors = doc["vectors"]
    if not isinstance(vectors, list) or not vectors:
        _bad("vectors must be a non-empty list")
    seen = set()
    for v in vectors:
        _validate_vector(v, seen)


def _validate_vector(v, seen):
    if not isinstance(v, dict) or not {"id", "title", "cites", "scopes", "steps"} <= set(v) or set(v) - {"id", "title", "cites", "scopes", "steps"}:
        _bad("vector keys")
    if not isinstance(v["id"], str) or not v["id"] or v["id"] in seen:
        _bad("vector id missing or duplicate")
    seen.add(v["id"])
    if not isinstance(v["title"], str) or not v["title"]:
        _bad("title")
    if not isinstance(v["cites"], list) or not v["cites"] or not all(isinstance(c, str) and c for c in v["cites"]):
        _bad("cites")
    scopes = v["scopes"]
    if not isinstance(scopes, dict) or not scopes or not all(isinstance(k, str) and isinstance(s, dict) for k, s in scopes.items()):
        _bad("scopes")
    steps = v["steps"]
    if not isinstance(steps, list) or not steps:
        _bad("steps must be a non-empty list")
    for s in steps:
        _validate_step(s, scopes)


def _scope_ref_ok(ref, scopes):
    return isinstance(ref, str) and ref in scopes


def _validate_step(s, scopes):
    if not isinstance(s, dict) or s.get("op") not in _STEP_KEYS:
        _bad("unknown step op")
    req, opt = _STEP_KEYS[s["op"]]
    if not req <= set(s) or set(s) - req - opt:
        _bad("step keys for %s" % s["op"])
    op = s["op"]
    if op == "advance":
        if not isinstance(s["obs"], dict) or ("raw" in s and type(s["raw"]) is not bool):
            _bad("advance obs")
        _validate_expect_verdict(s["expect"])
        sc = s["obs"].get("scope")
        if isinstance(sc, str) and sc not in scopes:
            _bad("unknown scope label")
    elif op == "policy_state":
        if not _scope_ref_ok(s["scope"], scopes) or not _is_int(s["now"]):
            _bad("policy_state step")
        e = s["expect"]
        if not isinstance(e, dict) or set(e) - {"policy_state", "display"} or "policy_state" not in e or e["policy_state"] not in highwater.POLICY_STATES:
            _bad("policy_state expect")
    elif op in ("save", "swap_to"):
        if not isinstance(s["name"], str) or not s["name"]:
            _bad("name")
    elif op == "tear":
        if s["kind"] not in _TEARS or (s["kind"] != "log_entry_corrupted" and not _scope_ref_ok(s.get("scope"), scopes)):
            _bad("tear step")
    elif op == "concurrent":
        obs = s["observations"]
        if not isinstance(obs, list) or not 2 <= len(obs) <= 4 or not all(isinstance(o, dict) and o.get("kind") in highwater.KINDS for o in obs):
            _bad("concurrent observations")
        e = s["expect"]
        ac = e.get("accepted_count") if isinstance(e, dict) else None
        if not isinstance(e, dict) or set(e) != {"accepted_count", "allowed_final"} or not (
            _is_int(ac) or (isinstance(ac, list) and ac and all(_is_int(x) for x in ac))
        ):
            _bad("concurrent expect")
        if not isinstance(e["allowed_final"], list) or not e["allowed_final"]:
            _bad("allowed_final")
        for fin in e["allowed_final"]:
            if not isinstance(fin, dict) or not all(k in scopes and isinstance(m, dict) and set(m) == {"activation_state", "epoch"} for k, m in fin.items()):
                _bad("allowed_final entry")
    elif op == "check":
        _validate_check(s["expect"], scopes)


def _validate_check(e, scopes):
    if not isinstance(e, dict) or not e or set(e) - _CHECK_KEYS:
        _bad("check expect")
    for k in ("log_length", "evidence_count", "rebaselines"):
        if k in e and not (_is_int(e[k]) and e[k] >= 0):
            _bad("check %s must be a non-negative int" % k)
    if "store" in e and e["store"] not in ("known", "unknown"):
        _bad("check store")
    for k in ("row", "high_water"):
        if k in e:
            if not isinstance(e[k], dict) or not e[k]:
                _bad("check %s must be a non-empty object" % k)
            for label, want in e[k].items():
                if label not in scopes:
                    _bad("check %s: unknown scope label %r" % (k, label))
                if k == "row" and not (isinstance(want, dict) and set(want) == {"activation_state", "epoch"}):
                    _bad("check row entry")
                if k == "high_water" and not _is_int(want):
                    _bad("check high_water entry")
    for k in ("row_absent", "scope_required"):
        if k in e:
            if not isinstance(e[k], list) or not e[k] or not all(isinstance(x, str) and x in scopes for x in e[k]):
                _bad("check %s: scope labels must exist" % k)
    if "revoked" in e:
        r = e["revoked"]
        if not isinstance(r, list) or not r or not all(
                isinstance(p, list) and len(p) == 2 and isinstance(p[0], str) and _is_int(p[1]) for p in r):
            _bad("check revoked")


def _validate_expect_verdict(e):
    if not isinstance(e, dict) or set(e) - _ALLOWED_EXPECT_ADVANCE or not {"verdict", "code"} <= set(e):
        _bad("expect keys")
    if e["verdict"] not in VERDICTS or not isinstance(e["code"], str) or not e["code"]:
        _bad("expect verdict/code")


# ------------------------------------------------------------------ runner


def _resolve_scope(ref, scopes, base):
    if isinstance(ref, str):
        return {**base, **scopes[ref]}
    return ref


def _macro(value, state, scopes, base, saved):
    if isinstance(value, dict) and len(value) == 1:
        (k, a), = value.items()
        if k == "$row":
            sc = _resolve_scope(a["scope"], scopes, base)
            return state["rows"][scope_key(sc)][a["field"]]
        if k == "$anchor":
            return copy.deepcopy(state["anchor"])
        if k == "$saved":
            return copy.deepcopy(saved[a])
        if k == "$saved_anchor":
            return copy.deepcopy(saved[a]["anchor"])
    if isinstance(value, dict):
        return {k: _macro(v, state, scopes, base, saved) for k, v in value.items()}
    if isinstance(value, list):
        return [_macro(v, state, scopes, base, saved) for v in value]
    return value


def _materialize(obs, kind_defaults, state, scopes, base, saved, raw=False):
    kd = {} if raw else kind_defaults.get(obs.get("kind"), {})
    out = {**copy.deepcopy(kd), **copy.deepcopy(obs)}
    out = _macro(out, state, scopes, base, saved)
    if isinstance(out.get("scope"), str):
        out["scope"] = _resolve_scope(out["scope"], scopes, base)
    if isinstance(out.get("claim"), dict) and isinstance(out["claim"].get("scope"), str):
        out["claim"]["scope"] = _resolve_scope(out["claim"]["scope"], scopes, base)
    return out


def _invariants(kind, before, after, verdict):
    """Global safety invariants checked after every advance step."""
    errs = []
    if set(verdict) - _ALLOWED_VERDICT_KEYS:
        errs.append("verdict carries unknown keys (kit must not mint authorization): %s" % sorted(verdict))
    if verdict["verdict"] not in VERDICTS:
        errs.append("unknown verdict")
    if kind == "guard" and verdict["code"] != "observation_malformed":
        if before != after:
            errs.append("guard changed state")
        return errs
    if kind == "lose_state":
        return errs
    if highwater._shape_problem(after):
        return errs  # malformed-state refusals return the state as given
    bf, af = before["floors"], after["floors"]
    for k, v in bf["high_water"].items():
        if af["high_water"].get(k, 0) < v:
            errs.append("high-water lowered")
    if not all(p in af["revoked"] for p in bf["revoked"]) or not all(k in af["revoked_keys"] for k in bf["revoked_keys"]):
        errs.append("revocation set shrank")
    if af["snapshot_version"] < bf["snapshot_version"]:
        errs.append("snapshot high-water lowered")
    for k, v in bf["min_epochs"].items():
        if af["min_epochs"].get(k, 0) < v:
            errs.append("min_epochs floor lowered")
    if after["external"]["min_trust_snapshot_version"] < before["external"]["min_trust_snapshot_version"]:
        errs.append("external floor lowered")
    if not set(before["scope_required"]) <= set(after["scope_required"]):
        errs.append("scope_required ratchet cleared")
    if after["evidence"][: len(before["evidence"])] != before["evidence"]:
        errs.append("evidence not append-only")
    if kind != "restore":
        if after["log"][: len(before["log"])] != before["log"]:
            errs.append("log not append-only")
        for k, row in before["rows"].items():
            if k not in after["rows"] or after["rows"][k]["epoch"] < row["epoch"]:
                errs.append("row epoch lowered")
    added = len(after["evidence"]) - len(before["evidence"])
    if verdict["verdict"] == ACCEPT and added != 0:
        errs.append("ACCEPT appended negative evidence")
    if verdict["verdict"] != ACCEPT and added != 1:
        errs.append("rejected transition did not append exactly one negative evidence record")
    return errs


def _final_map(state, scopes, base):
    out = {}
    for label, sc in scopes.items():
        row = state["rows"].get(scope_key({**base, **sc}))
        if row:
            out[label] = {"activation_state": row["activation_state"], "epoch": row["epoch"]}
    return out


def _check(state, exp, scopes, base):
    errs = []
    fin = _final_map(state, scopes, base)
    for key, val in exp.items():
        if key == "log_length" and len(state["log"]) != val:
            errs.append("log_length %d != %s" % (len(state["log"]), val))
        elif key == "evidence_count" and len(state["evidence"]) != val:
            errs.append("evidence_count %d != %s" % (len(state["evidence"]), val))
        elif key == "store" and state["store"] != val:
            errs.append("store %s != %s" % (state["store"], val))
        elif key == "rebaselines" and len(state["rebaselines"]) != val:
            errs.append("rebaselines %d != %s" % (len(state["rebaselines"]), val))
        elif key == "row":
            for label, want in val.items():
                if fin.get(label) != want:
                    errs.append("row %s %s != %s" % (label, fin.get(label), want))
        elif key == "row_absent":
            for label in val:
                if label in fin:
                    errs.append("row %s present" % label)
        elif key == "high_water":
            for label, want in val.items():
                got = state["floors"]["high_water"].get(scope_key({**base, **scopes[label]}), 0)
                if got != want:
                    errs.append("high_water %s %s != %s" % (label, got, want))
        elif key == "revoked":
            for p in val:
                if list(p) not in state["floors"]["revoked"]:
                    errs.append("revoked set lacks %s" % (p,))
        elif key == "scope_required":
            for label in val:
                if not state["scope_required"].get(scope_key({**base, **scopes[label]})):
                    errs.append("ratchet not set for %s" % label)
    return errs


def _tear(state, step, scopes, base):
    st = copy.deepcopy(state)
    kind = step["kind"]
    if kind == "log_entry_corrupted":
        st["log"][-1]["timestamp"] = (st["log"][-1].get("timestamp") or 0) + 1
    else:
        key = scope_key(_resolve_scope(step["scope"], scopes, base))
        if kind == "state_ahead_of_log":
            st["rows"][key]["epoch"] += 1
            st["rows"][key]["high_water_epoch"] += 1
        elif kind == "log_ahead_of_state":
            del st["rows"][key]
        elif kind == "row_validity_extended":
            st["rows"][key]["valid_until"] += 5000
        elif kind == "row_issuer_changed":
            st["rows"][key]["issuer_key_id"] = "key-other"
        elif kind == "revoked_set_truncated":
            st["floors"]["revoked"] = []
            st["floors"]["snapshot_revoked"] = []
        elif kind == "ratchet_cleared":
            st["scope_required"].pop(key, None)
    return st


def run_vector(doc, vector):
    """Run one vector (pure). Returns a list of failure strings; empty means pass."""
    base = doc.get("scope_base", {})
    defaults = doc.get("defaults", {})
    scopes = vector["scopes"]
    state = empty_state()
    saved = {}
    fails = []

    def fail(i, msg):
        fails.append("%s step %d: %s" % (vector["id"], i, msg))

    for i, step in enumerate(vector["steps"]):
        op = step["op"]
        if op == "advance":
            obs = _materialize(step["obs"], defaults, state, scopes, base, saved, step.get("raw", False))
            new, verdict = advance(state, obs)
            for e in _invariants(obs.get("kind"), state, new, verdict):
                fail(i, e)
            for k, v in step["expect"].items():
                got = verdict.get(k)
                if got != v:
                    fail(i, "expected %s=%r got %r (code %s)" % (k, v, got, verdict.get("code")))
            state = new
        elif op == "policy_state":
            ks = step.get("known_selection")
            got = policy_state(state, _resolve_scope(step["scope"], scopes, base), step["now"], ks)
            for k, v in step["expect"].items():
                if got[k] != v:
                    fail(i, "policy_state %s expected %r got %r" % (k, v, got[k]))
        elif op == "save":
            saved[step["name"]] = copy.deepcopy(state)
        elif op == "swap_to":
            if step["name"] not in saved:
                fail(i, "no saved state %r" % step["name"])
            else:
                state = copy.deepcopy(saved[step["name"]])
        elif op == "tear":
            state = _tear(state, step, scopes, base)
        elif op == "check":
            for e in _check(state, step["expect"], scopes, base):
                fail(i, e)
        elif op == "concurrent":
            obs_list = [_materialize(o, defaults, state, scopes, base, saved) for o in step["observations"]]
            finals = []
            for perm in itertools.permutations(range(len(obs_list))):
                s = state
                accepted = 0
                for idx in perm:
                    new, verdict = advance(s, obs_list[idx])
                    for e in _invariants(obs_list[idx].get("kind"), s, new, verdict):
                        fail(i, "perm %s: %s" % (perm, e))
                    accepted += verdict["verdict"] == ACCEPT
                    s = new
                want = step["expect"]["accepted_count"]
                if accepted not in (want if isinstance(want, list) else [want]):
                    fail(i, "perm %s accepted %d not in %s" % (perm, accepted, want))
                fm = _final_map(s, scopes, base)
                finals.append(fm)
                if fm not in step["expect"]["allowed_final"]:
                    fail(i, "perm %s final %s not an allowed serial outcome" % (perm, fm))
    return fails


def run_vector_set(doc):
    """Validate then run every vector. Returns the list of all failures (empty = pass)."""
    validate_vector_set(doc)
    out = []
    for v in doc["vectors"]:
        out.extend(run_vector(doc, v))
    return out
