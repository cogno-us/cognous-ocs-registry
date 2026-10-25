"""Pure consumer activation / high-water conformance functions (EXT-S1-8).

Status: IMPLEMENTED / DEVELOPER-TESTED. Not independently qualified.

This module is a CONFORMANCE KIT, not an activation store. It holds no state,
performs no I/O, reads no clock (time is the explicit integer ``now`` in every
observation) and imports only the standard library. The enforcing component
(Runtime / Control Plane) owns the real store; this kit defines the pure
transition and derivation rules (docs/r08-v2-contract.md sections 7 and 8) so
that vectors can be replayed against any implementation.

Public surface:

* ``empty_state()``                 a fresh, known, empty state value
* ``advance(state, observation)``   -> ``(new_state, verdict)``; never mutates inputs
* ``policy_state(state, scope, now, known_selection=None)``  derived read model
* ``scope_key(scope)``              canonical scope key string
* ``verify_state(state)``           None or the code that makes the state suspect

The kit never mints authorization, never reverses a revocation and never
lowers a high-water. A verdict ACCEPT means only that the transition or
comparison is consistent with the supplied state; it is not an authorization.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re

STATE_SCHEMA = "ocs-conformance-state/1"
EVIDENCE_SCHEMA = "ocs-registry-failure-detail/1"

ACCEPT = "ACCEPT"
REFUSE_STALE = "REFUSE_STALE"
REFUSE = "REFUSE"
UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"
VERDICTS = (ACCEPT, REFUSE_STALE, REFUSE, UNKNOWN_FAIL_CLOSED)

SCOPE_FIELDS = (
    "selection_id",
    "consumer_id",
    "tenant",
    "institution",
    "authority_domain",
    "operation",
    "family",
)
POLICY_STATES = (
    "not_selected",
    "selected_not_activated",
    "active",
    "withdrawn",
    "revoked",
    "expired",
    "not_yet_valid",
    "superseded",
    "unknown",
)
REQUIRED_UNAVAILABLE = "REQUIRED — UNAVAILABLE"
KINDS = (
    "select",
    "withdraw",
    "sync",
    "external_floor",
    "read",
    "guard",
    "restore",
    "lose_state",
    "rebaseline",
    "relax_scope_required",
)

_IDENT = re.compile(r"^[A-Za-z0-9._:/-]{1,128}$")
_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


class _Malformed(Exception):
    pass


# ---------------------------------------------------------------- basics


def _is_int(x):
    return type(x) is int


def _ident(x):
    return isinstance(x, str) and _IDENT.fullmatch(x) is not None


def _sha(x):
    return isinstance(x, str) and _SHA.fullmatch(x) is not None


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _entry_hash(entry):
    body = {k: v for k, v in entry.items() if k != "entry_hash"}
    return "sha256:" + hashlib.sha256(_canon(body)).hexdigest()


def scope_key(scope):
    """Canonical scope key string for the seven-field scope (contract section 7)."""
    if not isinstance(scope, dict) or set(scope) != set(SCOPE_FIELDS):
        raise _Malformed("scope must have exactly the seven scope fields")
    for f in SCOPE_FIELDS:
        if not _ident(scope[f]):
            raise _Malformed("scope field %s invalid" % f)
    return json.dumps([scope[f] for f in SCOPE_FIELDS], separators=(",", ":"))


def _chain_key(scope):
    return json.dumps([scope[f] for f in SCOPE_FIELDS if f != "selection_id"], separators=(",", ":"))


def _scope_from_key(key):
    return dict(zip(SCOPE_FIELDS, json.loads(key)))


def empty_state():
    return {
        "schema": STATE_SCHEMA,
        "store": "known",
        "unknown_reason": None,
        "rows": {},
        "log": [],
        "evidence": [],
        "rebaselines": [],
        "scope_required": {},
        "floors": {
            "high_water": {},
            "revoked": [],
            "revoked_keys": [],
            "snapshot_revoked": [],
            "snapshot_version": 0,
            "min_epochs": {},
        },
        "snapshot": None,
        "external": {"min_trust_snapshot_version": 0},
        "anchor": {"log_head": 0, "head_hash": None},
    }


# ------------------------------------------------------- state validation

_STATE_KEYS = {
    "schema", "store", "unknown_reason", "rows", "log", "evidence", "rebaselines",
    "scope_required", "floors", "snapshot", "external", "anchor",
}
_FLOOR_KEYS = {"high_water", "revoked", "revoked_keys", "snapshot_revoked", "snapshot_version", "min_epochs"}
_ROW_KEYS = {
    "activation_state", "epoch", "selection_digest", "participation", "valid_from",
    "valid_until", "issuer_key_id", "record", "activation_ref", "high_water_epoch",
}


def _shape_problem(st):
    try:
        if not isinstance(st, dict) or set(st) != _STATE_KEYS or st["schema"] != STATE_SCHEMA:
            return True
        if st["store"] not in ("known", "unknown"):
            return True
        if not isinstance(st["rows"], dict) or not isinstance(st["log"], list):
            return True
        if not isinstance(st["evidence"], list) or not isinstance(st["rebaselines"], list):
            return True
        if not isinstance(st["scope_required"], dict):
            return True
        fl = st["floors"]
        if not isinstance(fl, dict) or set(fl) != _FLOOR_KEYS:
            return True
        if not isinstance(fl["high_water"], dict) or not isinstance(fl["min_epochs"], dict):
            return True
        if not isinstance(fl["revoked"], list) or not isinstance(fl["revoked_keys"], list) or not isinstance(fl["snapshot_revoked"], list):
            return True
        if not _is_int(fl["snapshot_version"]) or fl["snapshot_version"] < 0:
            return True
        for pair in fl["revoked"] + fl["snapshot_revoked"]:
            if not (isinstance(pair, list) and len(pair) == 2 and isinstance(pair[0], str) and _is_int(pair[1])):
                return True
        for k, row in st["rows"].items():
            scope_key(_scope_from_key(k))
            if not isinstance(row, dict) or set(row) != _ROW_KEYS:
                return True
            if row["activation_state"] not in ("active", "withdrawn", "revoked"):
                return True
            if not _is_int(row["epoch"]) or row["epoch"] < 1:
                return True
            if row["participation"] not in ("required", "optional"):
                return True
            if not (_is_int(row["valid_from"]) and _is_int(row["valid_until"])):
                return True
        for e in st["log"]:
            if not isinstance(e, dict) or e.get("entry_type") not in ("activate", "withdraw", "revoke", "sync"):
                return True
        a = st["anchor"]
        if not isinstance(a, dict) or set(a) != {"log_head", "head_hash"}:
            return True
        if not _is_int(a["log_head"]) or a["log_head"] < 0:
            return True
        ex = st["external"]
        if not isinstance(ex, dict) or not _is_int(ex.get("min_trust_snapshot_version")):
            return True
        return False
    except Exception:  # any unexpected shape is a problem, never a pass
        return True


def _replay(st):
    """Rebuild the expected state facts from the log, or None if the log is broken."""
    try:
        return _replay_unsafe(st)
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return None


def _replay_unsafe(st):
    rows = {}
    revoked = set()
    explicit = set()
    keys = set()
    required = set()
    min_epochs = {}
    last_sync = None
    prev = None
    for e in st["log"]:
        if e.get("prev_hash") != prev or e.get("entry_hash") != _entry_hash(e):
            return None
        prev = e["entry_hash"]
        t = e["entry_type"]
        k = e.get("scope_key")
        if t == "activate":
            rows[k] = {
                "activation_state": "active", "epoch": e["epoch"], "selection_digest": e["selection_digest"],
                "activation_ref": e["entry_hash"], "participation": e["participation"],
                "valid_from": e["valid_from"], "valid_until": e["valid_until"],
                "issuer_key_id": e["issuer_key_id"], "record": e["record"],
            }
            if e["scope_required"]:
                required.add(k)
        elif t == "withdraw":
            r = rows.get(k)
            if r is None:
                return None
            rows[k] = {**r, "activation_state": "withdrawn", "epoch": e["epoch"], "selection_digest": e["selection_digest"],
                       "participation": e["participation"], "issuer_key_id": e["issuer_key_id"]}
        elif t == "revoke":
            sel = _scope_from_key(k)["selection_id"]
            revoked.add((sel, e["epoch"]))
            r = rows.get(k)
            if r is not None and r["epoch"] == e["epoch"]:
                rows[k] = {**r, "activation_state": "revoked"}
        elif t == "sync":
            for pair in e["revoked_selections"]:
                explicit.add((pair[0], pair[1]))
                revoked.add((pair[0], pair[1]))
            keys.update(e["revoked_key_ids"])
            for sel, floor in e["min_epochs"]:
                if floor > min_epochs.get(sel, 0):
                    min_epochs[sel] = floor
            last_sync = e
    return {"rows": rows, "revoked": revoked, "explicit": explicit, "keys": keys, "required": required,
            "min_epochs": min_epochs, "last_sync": last_sync}


def _anchor_problem(st, a):
    n = len(st["log"])
    if n < a["log_head"]:
        return "state_older_than_anchor"
    if a["log_head"] == 0:
        return "anchor_head_mismatch" if a["head_hash"] is not None else None
    if st["log"][a["log_head"] - 1]["entry_hash"] != a["head_hash"]:
        return "anchor_head_mismatch"
    return None


def _regress_problem(st):
    fl = st["floors"]
    for k, hwm in fl["high_water"].items():
        row = st["rows"].get(k)
        if (row["epoch"] if row else 0) < hwm:
            return "state_behind_floor"
    rep = _replay(st)
    if rep is None:
        return "log_chain_broken"
    for pair in fl["revoked"]:
        if (pair[0], pair[1]) not in rep["revoked"]:
            return "state_behind_floor"
    return None


def _state_problem(st, ext_anchor=None, check_anchor=True, extra_anchors=()):
    """None, or the code that makes ``st`` suspect. ``ext_anchor`` may be one anchor or a list."""
    if _shape_problem(st):
        return "state_malformed"
    rep = _replay(st)
    if rep is None:
        return "log_chain_broken"
    fl = st["floors"]
    if set(rep["rows"]) != set(st["rows"]):
        return "state_log_mismatch"
    for k, exp in rep["rows"].items():
        row = st["rows"][k]
        for f, v in exp.items():
            if row[f] != v:
                return "state_log_mismatch"
        if row["high_water_epoch"] != row["epoch"] or fl["high_water"].get(k, 0) < row["epoch"]:
            return "state_log_mismatch"
    # persisted sets must contain everything the log recorded (grow-only; an incomplete write fails closed)
    if not rep["revoked"] <= {(p[0], p[1]) for p in fl["revoked"]}:
        return "state_log_mismatch"
    if not rep["explicit"] <= {(p[0], p[1]) for p in fl["snapshot_revoked"]}:
        return "state_log_mismatch"
    if not rep["keys"] <= set(fl["revoked_keys"]):
        return "state_log_mismatch"
    if any(fl["min_epochs"].get(sel, 0) < floor for sel, floor in rep["min_epochs"].items()):
        return "state_log_mismatch"
    if not all(st["scope_required"].get(k) for k in rep["required"]):
        return "state_log_mismatch"
    ls = rep["last_sync"]
    if ls is not None and fl["snapshot_version"] < ls["snapshot_version"]:
        return "state_log_mismatch"
    snap = st["snapshot"]
    if snap is not None:
        if ls is None or snap != {"version": ls["snapshot_version"], "fingerprint": ls["fingerprint"], "valid_until": ls["valid_until"]}:
            return "state_log_mismatch"
        if snap["version"] != fl["snapshot_version"]:
            return "state_log_mismatch"
    if check_anchor:
        anchors = [st["anchor"]] + list(extra_anchors)
        if isinstance(ext_anchor, list):
            anchors.extend(ext_anchor)
        elif ext_anchor is not None:
            anchors.append(ext_anchor)
        for a in anchors:
            prob = _anchor_problem(st, a)
            if prob:
                return prob
    return _regress_problem(st)


def verify_state(state):
    """None if the state is internally consistent and not behind its own anchor."""
    return _state_problem(state)


# ----------------------------------------------------------- observations


def _need(obs, required, optional=()):
    keys = set(obs)
    if not set(required) <= keys or not keys <= set(required) | set(optional) | {"external_anchor"}:
        raise _Malformed("observation keys invalid for kind %s" % obs.get("kind"))


def _check_record(r):
    if not isinstance(r, dict) or set(r) != {"record_id", "record_version", "record_digest"}:
        raise _Malformed("record")
    if not (_ident(r["record_id"]) and _is_int(r["record_version"]) and r["record_version"] >= 1 and _sha(r["record_digest"])):
        raise _Malformed("record")


def _check_supersedes(s):
    if s is None:
        return
    if not isinstance(s, dict) or set(s) != {"selection_id", "epoch", "statement_digest"}:
        raise _Malformed("supersedes")
    if not (_ident(s["selection_id"]) and _is_int(s["epoch"]) and s["epoch"] >= 1 and _sha(s["statement_digest"])):
        raise _Malformed("supersedes")


def _check_statement(obs, with_window):
    scope_key(obs["scope"])
    if not (_is_int(obs["epoch"]) and obs["epoch"] >= 1 and _sha(obs["selection_digest"])):
        raise _Malformed("statement")
    _check_supersedes(obs["supersedes"])
    if obs["participation"] not in ("required", "optional") or not _ident(obs["issuer_key_id"]):
        raise _Malformed("statement")
    if type(obs["verified"]) is not bool:
        raise _Malformed("verified")
    if with_window:
        if not (_is_int(obs["valid_from"]) and _is_int(obs["valid_until"]) and obs["valid_from"] < obs["valid_until"]):
            raise _Malformed("window")
        _check_record(obs["record"])


def _check_snapshot(s):
    if not isinstance(s, dict) or set(s) != {"version", "fingerprint", "valid_until", "revoked_selections", "revoked_key_ids", "min_epochs"}:
        raise _Malformed("snapshot")
    if not (_is_int(s["version"]) and s["version"] >= 1 and _sha(s["fingerprint"]) and _is_int(s["valid_until"])):
        raise _Malformed("snapshot")
    for f in ("revoked_selections", "min_epochs", "revoked_key_ids"):
        if not isinstance(s[f], list):
            raise _Malformed("snapshot collection type")
    for pair in s["revoked_selections"]:
        if not (isinstance(pair, list) and len(pair) == 2 and _ident(pair[0]) and _is_int(pair[1]) and pair[1] >= 1):
            raise _Malformed("snapshot")
    for pair in s["min_epochs"]:
        if not (isinstance(pair, list) and len(pair) == 2 and _ident(pair[0]) and _is_int(pair[1]) and pair[1] >= 1):
            raise _Malformed("snapshot")
    if not all(_ident(k) for k in s["revoked_key_ids"]):
        raise _Malformed("snapshot")
    if len({tuple(p) for p in s["revoked_selections"]}) != len(s["revoked_selections"]):
        raise _Malformed("snapshot duplicate")
    if len({p[0] for p in s["min_epochs"]}) != len(s["min_epochs"]) or len(set(s["revoked_key_ids"])) != len(s["revoked_key_ids"]):
        raise _Malformed("snapshot duplicate")


def _check_binding(b):
    if b is None:
        return
    if not isinstance(b, dict) or set(b) != {"selection_epoch", "selection_digest", "record", "activation_ref", "trust_snapshot_version", "trust_snapshot_fingerprint"}:
        raise _Malformed("binding")
    if not (_is_int(b["selection_epoch"]) and b["selection_epoch"] >= 1 and _sha(b["selection_digest"]) and _sha(b["activation_ref"])):
        raise _Malformed("binding")
    if not (_is_int(b["trust_snapshot_version"]) and b["trust_snapshot_version"] >= 1 and _sha(b["trust_snapshot_fingerprint"])):
        raise _Malformed("binding")
    _check_record(b["record"])


def _validate_obs(obs):
    if not isinstance(obs, dict) or obs.get("kind") not in KINDS:
        raise _Malformed("kind")
    if not _is_int(obs.get("now")) or obs["now"] < 0:
        raise _Malformed("now")
    k = obs["kind"]
    ea = obs.get("external_anchor")
    if ea is not None and not (
        isinstance(ea, dict) and set(ea) == {"log_head", "head_hash"} and _is_int(ea["log_head"]) and ea["log_head"] >= 0
        and (ea["head_hash"] is None or _sha(ea["head_hash"]))
    ):
        raise _Malformed("external_anchor")
    if k == "select":
        _need(obs, ("kind", "now", "scope", "epoch", "selection_digest", "supersedes", "participation", "valid_from", "valid_until", "issuer_key_id", "record", "verified"))
        _check_statement(obs, True)
    elif k == "withdraw":
        _need(obs, ("kind", "now", "scope", "epoch", "selection_digest", "supersedes", "participation", "issuer_key_id", "verified"))
        _check_statement(obs, False)
    elif k == "sync":
        _need(obs, ("kind", "now", "snapshot"))
        _check_snapshot(obs["snapshot"])
    elif k == "external_floor":
        _need(obs, ("kind", "now", "min_trust_snapshot_version"))
        if not (_is_int(obs["min_trust_snapshot_version"]) and obs["min_trust_snapshot_version"] >= 0):
            raise _Malformed("floor")
    elif k in ("read", "lose_state"):
        _need(obs, ("kind", "now"))
    elif k == "guard":
        _need(obs, ("kind", "now", "claim"))
        c = obs["claim"]
        if not isinstance(c, dict) or set(c) != {"scope", "binding"}:
            raise _Malformed("claim")
        scope_key(c["scope"])
        _check_binding(c["binding"])
    elif k == "restore":
        _need(obs, ("kind", "now", "backup"))
        if _shape_problem(obs["backup"]):
            raise _Malformed("backup")
    elif k == "rebaseline":
        _need(obs, ("kind", "now", "authorized", "decision_ref"))
        if type(obs["authorized"]) is not bool or not _ident(obs["decision_ref"]):
            raise _Malformed("rebaseline")
    elif k == "relax_scope_required":
        _need(obs, ("kind", "now", "scope"), ("ratchet_digest", "ratchet_generation", "decision_ref", "authorized"))
        scope_key(obs["scope"])


# ------------------------------------------------------------- bookkeeping


def _verdict(verdict, code, **extra):
    v = {"verdict": verdict, "code": code}
    v.update(extra)
    return v


def _evidence(st, obs, v):
    scope = obs.get("scope")
    if not isinstance(scope, dict) and isinstance(obs.get("claim"), dict):
        scope = obs["claim"].get("scope")
    key = None
    if isinstance(scope, dict):
        try:
            key = scope_key(scope)
        except _Malformed:
            key = None
    st["evidence"].append({
        "schema": EVIDENCE_SCHEMA,
        "scope_key": key,
        "epoch": obs.get("epoch") if _is_int(obs.get("epoch")) else None,
        "selection_digest": obs.get("selection_digest") if _sha(obs.get("selection_digest")) else None,
        "registry_code": v["code"],
        "verdict": v["verdict"],
        "kind": obs.get("kind") if isinstance(obs.get("kind"), str) else None,
        "timestamp": obs.get("now") if _is_int(obs.get("now")) else None,
    })


def _refuse(st, obs, verdict, code, **extra):
    v = _verdict(verdict, code, **extra)
    if isinstance(st, dict) and isinstance(st.get("evidence"), list):
        _evidence(st, obs, v)
    return st, v


def _append(st, entry):
    prev = st["log"][-1]["entry_hash"] if st["log"] else None
    entry = {**entry, "prev_hash": prev}
    entry["entry_hash"] = _entry_hash(entry)
    st["log"].append(entry)
    st["anchor"] = {"log_head": len(st["log"]), "head_hash": entry["entry_hash"]}
    return entry


def _bump(d, key, value):
    if value > d.get(key, 0):
        d[key] = value


def _revoked(st, sel, epoch):
    return [sel, epoch] in st["floors"]["revoked"]


def _hw(st, key):
    row = st["rows"].get(key)
    return max(st["floors"]["high_water"].get(key, 0), row["epoch"] if row else 0)


# ------------------------------------------------- statement checks (select)
# Ordered refusal checks. Each returns None (pass) or (verdict, code). They are
# listed in module-level tuples so a mutation test can disable exactly one.


def _c_verified(st, o, ctx):
    if o["verified"] is not True:
        return REFUSE, "statement_not_verified"


def _c_window(st, o, ctx):
    if o["now"] < o["valid_from"]:
        return REFUSE, "selection_not_yet_effective"
    if o["now"] >= o["valid_until"]:
        return REFUSE, "selection_expired"


def _c_conflict(st, o, ctx):
    ck = _chain_key(o["scope"])
    for k in st["rows"]:
        s = _scope_from_key(k)
        if k != ctx["key"] and _chain_key(s) == ck:
            return REFUSE, "selection_conflict"


def _c_revoked_pair(st, o, ctx):
    if _revoked(st, o["scope"]["selection_id"], o["epoch"]):
        return REFUSE, "selection_revoked"


def _c_revoked_key(st, o, ctx):
    if o["issuer_key_id"] in st["floors"]["revoked_keys"]:
        return REFUSE, "issuer_key_revoked"


def _c_stale_epoch(st, o, ctx):
    if o["epoch"] <= _hw(st, ctx["key"]):
        return REFUSE_STALE, "selection_epoch_stale"
    if o["epoch"] < st["floors"]["min_epochs"].get(o["scope"]["selection_id"], 0):
        return REFUSE_STALE, "selection_epoch_stale"


def _c_supersession_select(st, o, ctx):
    row = ctx["row"]
    s = o["supersedes"]
    if row is None and not _has_history(st, ctx["key"]):
        if s is not None:
            return REFUSE, "selection_supersession_invalid"
        return None
    if not _names(row, o, s):
        return REFUSE, "selection_supersession_invalid"


def _c_supersession_withdraw(st, o, ctx):
    if ctx["row"] is None or not _names(ctx["row"], o, o["supersedes"]):
        return REFUSE, "selection_supersession_invalid"


def _c_withdraw_revoked_row(st, o, ctx):
    if ctx["row"] is not None and ctx["row"]["activation_state"] == "revoked":
        return REFUSE, "selection_revoked"


def _c_ratchet(st, o, ctx):
    if st["scope_required"].get(ctx["key"]) and o["participation"] != "required":
        return REFUSE, "participation_mismatch"


def _has_history(st, key):
    return key in st["floors"]["high_water"] or any(e.get("scope_key") == key for e in st["log"])


def _names(row, o, s):
    return (
        row is not None and isinstance(s, dict)
        and s["selection_id"] == o["scope"]["selection_id"]
        and s["epoch"] == row["epoch"]
        and s["statement_digest"] == row["selection_digest"]
    )


_SELECT_CHECKS = (
    ("verified", _c_verified), ("window", _c_window), ("conflict", _c_conflict),
    ("revoked_pair", _c_revoked_pair), ("revoked_key", _c_revoked_key), ("stale_epoch", _c_stale_epoch),
    ("supersession", _c_supersession_select), ("ratchet", _c_ratchet),
)
_WITHDRAW_CHECKS = (
    ("verified", _c_verified), ("revoked_pair", _c_revoked_pair),
    ("revoked_key", _c_revoked_key), ("withdraw_revoked_row", _c_withdraw_revoked_row),
    ("stale_epoch", _c_stale_epoch), ("supersession", _c_supersession_withdraw), ("ratchet", _c_ratchet),
)


def _run_checks(checks, st, o, ctx):
    for _, fn in checks:
        r = fn(st, o, ctx)
        if r is not None:
            return r
    return None


def _do_select(st, o):
    key = scope_key(o["scope"])
    ctx = {"key": key, "row": st["rows"].get(key)}
    bad = _run_checks(_SELECT_CHECKS, st, o, ctx)
    if bad:
        return _refuse(st, o, bad[0], bad[1])
    prior = ctx["row"]["activation_state"] if ctx["row"] else None
    entry = _append(st, {
        "entry_type": "activate", "scope_key": key, "epoch": o["epoch"], "selection_digest": o["selection_digest"],
        "issuer_key_id": o["issuer_key_id"], "prior_state": prior, "new_state": "active", "timestamp": o["now"],
        "participation": o["participation"], "valid_from": o["valid_from"], "valid_until": o["valid_until"],
        "record": o["record"], "scope_required": o["participation"] == "required",
    })
    st["rows"][key] = {
        "activation_state": "active", "epoch": o["epoch"], "selection_digest": o["selection_digest"],
        "participation": o["participation"], "valid_from": o["valid_from"], "valid_until": o["valid_until"],
        "issuer_key_id": o["issuer_key_id"], "record": o["record"], "activation_ref": entry["entry_hash"],
        "high_water_epoch": o["epoch"],
    }
    _bump(st["floors"]["high_water"], key, o["epoch"])
    if o["participation"] == "required":
        st["scope_required"][key] = True
    return st, _verdict(ACCEPT, "activated", activation_ref=entry["entry_hash"])


def _do_withdraw(st, o):
    key = scope_key(o["scope"])
    ctx = {"key": key, "row": st["rows"].get(key)}
    bad = _run_checks(_WITHDRAW_CHECKS, st, o, ctx)
    if bad:
        return _refuse(st, o, bad[0], bad[1])
    row = ctx["row"]
    _append(st, {
        "entry_type": "withdraw", "scope_key": key, "epoch": o["epoch"], "selection_digest": o["selection_digest"],
        "issuer_key_id": o["issuer_key_id"], "prior_state": row["activation_state"], "new_state": "withdrawn",
        "timestamp": o["now"], "participation": o["participation"],
    })
    st["rows"][key] = {**row, "activation_state": "withdrawn", "epoch": o["epoch"], "selection_digest": o["selection_digest"],
                       "participation": o["participation"], "issuer_key_id": o["issuer_key_id"],
                       "high_water_epoch": o["epoch"]}
    _bump(st["floors"]["high_water"], key, o["epoch"])
    return st, _verdict(ACCEPT, "withdrawn")


# ------------------------------------------------------------------- sync


def _recorded_fingerprint(st, version):
    for e in st["log"]:
        if e["entry_type"] == "sync" and e.get("snapshot_version") == version:
            return e.get("fingerprint")
    return None


def _do_sync(st, o):
    if st["store"] != "known":
        return _refuse(st, o, UNKNOWN_FAIL_CLOSED, "store_unknown")
    s = o["snapshot"]
    fl = st["floors"]
    if s["valid_until"] <= o["now"]:
        return _refuse(st, o, REFUSE, "trust_snapshot_expired")
    if s["version"] < st["external"]["min_trust_snapshot_version"] or s["version"] < fl["snapshot_version"]:
        return _refuse(st, o, REFUSE_STALE, "trust_snapshot_version_stale")
    revoked_in = {tuple(p) for p in s["revoked_selections"]}
    # omission is judged against pairs earlier snapshots listed explicitly; locally derived key revocations are retained, not required
    if not {tuple(p) for p in fl["snapshot_revoked"]} <= revoked_in or not set(fl["revoked_keys"]) <= set(s["revoked_key_ids"]):
        return _refuse(st, o, REFUSE_STALE, "trust_snapshot_revocation_omitted")
    for sel, floor in fl["min_epochs"].items():
        if dict((p[0], p[1]) for p in s["min_epochs"]).get(sel, 0) < floor:
            return _refuse(st, o, REFUSE_STALE, "min_epoch_floor_lowered")
    if s["version"] == fl["snapshot_version"]:
        if _recorded_fingerprint(st, s["version"]) == s["fingerprint"]:
            return st, _verdict(ACCEPT, "idempotent_redelivery")
        return _refuse(st, o, REFUSE_STALE, "trust_snapshot_version_stale")
    _append(st, {
        "entry_type": "sync", "scope_key": None, "epoch": None, "selection_digest": None, "issuer_key_id": None,
        "prior_state": None, "new_state": None, "timestamp": o["now"], "snapshot_version": s["version"],
        "fingerprint": s["fingerprint"], "valid_until": s["valid_until"],
        "revoked_selections": [list(p) for p in s["revoked_selections"]], "revoked_key_ids": list(s["revoked_key_ids"]),
        "min_epochs": [list(p) for p in s["min_epochs"]],
    })
    fl["snapshot_version"] = s["version"]
    st["snapshot"] = {"version": s["version"], "fingerprint": s["fingerprint"], "valid_until": s["valid_until"]}
    for p in s["revoked_selections"]:
        if list(p) not in fl["revoked"]:
            fl["revoked"].append(list(p))
        if list(p) not in fl["snapshot_revoked"]:
            fl["snapshot_revoked"].append(list(p))
    for k in s["revoked_key_ids"]:
        if k not in fl["revoked_keys"]:
            fl["revoked_keys"].append(k)
    for sel, floor in s["min_epochs"]:
        _bump(fl["min_epochs"], sel, floor)
    # revoke entries for rows hit by the snapshot; revocation is terminal for the pair
    for key in sorted(st["rows"]):
        row = st["rows"][key]
        sel = _scope_from_key(key)["selection_id"]
        if row["activation_state"] == "revoked":
            continue
        cause = None
        if (sel, row["epoch"]) in revoked_in:
            cause = "selection_revoked"
        elif row["issuer_key_id"] in fl["revoked_keys"]:
            cause = "issuer_key_revoked"
        if cause:
            _append(st, {
                "entry_type": "revoke", "scope_key": key, "epoch": row["epoch"], "selection_digest": row["selection_digest"],
                "issuer_key_id": row["issuer_key_id"], "prior_state": row["activation_state"], "new_state": "revoked",
                "timestamp": o["now"], "cause": cause,
            })
            if [sel, row["epoch"]] not in fl["revoked"]:
                fl["revoked"].append([sel, row["epoch"]])
            row["activation_state"] = "revoked"
    return st, _verdict(ACCEPT, "synced")


# --------------------------------------------------- environment / recovery


def _merge_floors(a, b):
    out = copy.deepcopy(a)
    for k, v in b["high_water"].items():
        _bump(out["high_water"], k, v)
    for p in b["revoked"]:
        if p not in out["revoked"]:
            out["revoked"].append(p)
    for p in b["snapshot_revoked"]:
        if p not in out["snapshot_revoked"]:
            out["snapshot_revoked"].append(p)
    for k in b["revoked_keys"]:
        if k not in out["revoked_keys"]:
            out["revoked_keys"].append(k)
    out["snapshot_version"] = max(a["snapshot_version"], b["snapshot_version"])
    for k, v in b["min_epochs"].items():
        _bump(out["min_epochs"], k, v)
    return out


def _do_lose_state(st, o):
    new = empty_state()
    new["store"] = "unknown"
    new["unknown_reason"] = "state_lost"
    new["anchor"] = copy.deepcopy(st["anchor"]) if not _shape_problem(st) else new["anchor"]
    if o.get("external_anchor") is not None and o["external_anchor"]["log_head"] >= new["anchor"]["log_head"]:
        new["anchor"] = copy.deepcopy(o["external_anchor"])
    if not _shape_problem(st):
        new["evidence"] = copy.deepcopy(st["evidence"])
    return _refuse(new, o, UNKNOWN_FAIL_CLOSED, "state_lost")


def _do_restore(st, o):
    cur = st
    new = copy.deepcopy(o["backup"])
    ok_cur = not _shape_problem(cur)
    lost = ok_cur and cur["store"] == "unknown" and cur["unknown_reason"] == "state_lost"
    if ok_cur:
        new["floors"] = _merge_floors(new["floors"], cur["floors"])
        for k, row in cur["rows"].items():
            _bump(new["floors"]["high_water"], k, row["epoch"])
        for k in cur["scope_required"]:
            new["scope_required"][k] = True
        new["external"]["min_trust_snapshot_version"] = max(
            new["external"]["min_trust_snapshot_version"], cur["external"]["min_trust_snapshot_version"])
        new["evidence"] = copy.deepcopy(cur["evidence"])
        new["rebaselines"] = copy.deepcopy(cur["rebaselines"])
    anchors = [copy.deepcopy(o["backup"]["anchor"])]
    if ok_cur:
        anchors.append(copy.deepcopy(cur["anchor"]))
    if o.get("external_anchor") is not None:
        anchors.append(copy.deepcopy(o["external_anchor"]))
    top = max(anchors, key=lambda a: a["log_head"])
    new["anchor"] = top
    if new["snapshot"] is not None and new["snapshot"]["version"] < new["floors"]["snapshot_version"]:
        # the restored support record is older than the retained snapshot high-water: no current support until a newer sync
        new["snapshot"] = None
    if lost:
        # lost state is unknown, never zero; an older copy does not repair it (needs external re-provisioning)
        new["store"] = "unknown"
        new["unknown_reason"] = "state_lost"
        return _refuse(new, o, UNKNOWN_FAIL_CLOSED, "state_lost")
    problem = _state_problem(new, extra_anchors=anchors)
    if problem is None and new["store"] == "known":
        return new, _verdict(ACCEPT, "restore_consistent")
    new["store"] = "unknown"
    new["unknown_reason"] = problem or "restore_unacknowledged"
    return _refuse(new, o, UNKNOWN_FAIL_CLOSED, new["unknown_reason"])


def _do_rebaseline(st, o):
    if st["store"] != "unknown":
        return _refuse(st, o, REFUSE, "rebaseline_not_needed")
    if o["authorized"] is not True:
        return _refuse(st, o, REFUSE, "rebaseline_not_authorized")
    if st["unknown_reason"] == "state_lost":
        return _refuse(st, o, REFUSE, "rebaseline_refused_state_lost")
    problem = _state_problem(st, check_anchor=False)
    if problem is not None:
        return _refuse(st, o, REFUSE, "rebaseline_refused_" + problem)
    st["store"] = "known"
    st["unknown_reason"] = None
    st["anchor"] = {"log_head": len(st["log"]), "head_hash": st["log"][-1]["entry_hash"] if st["log"] else None}
    st["rebaselines"].append({"decision_ref": o["decision_ref"], "timestamp": o["now"], "log_head": len(st["log"])})
    return st, _verdict(ACCEPT, "rebaselined")


def _do_external_floor(st, o):
    cur = st["external"]["min_trust_snapshot_version"]
    if o["min_trust_snapshot_version"] < cur:
        return _refuse(st, o, REFUSE_STALE, "external_floor_lowered")
    st["external"]["min_trust_snapshot_version"] = o["min_trust_snapshot_version"]
    return st, _verdict(ACCEPT, "floor_raised" if o["min_trust_snapshot_version"] > cur else "floor_unchanged")


# ------------------------------------------------------------ policy_state


def policy_state(state, scope, now, known_selection=None):
    """Derived read model (contract 7.2). Never stored, never input, never authority.

    ``known_selection`` is an optional ``{"selection_id", "epoch"}`` the reader knows
    about that is not (yet) activated. Returns ``{"policy_state", "required",
    "display"}``. There is no authorizing boolean in the result.
    """
    if not _is_int(now) or now < 0:
        raise ValueError("now must be a non-negative int")
    key = scope_key(scope)
    if _state_problem(state, check_anchor=True) is not None or state["store"] != "known":
        required = bool(isinstance(state, dict) and not _shape_problem(state) and state["scope_required"].get(key))
        return _view("unknown", required)
    row = state["rows"].get(key)
    fl = state["floors"]
    required = bool(state["scope_required"].get(key)) or bool(row and row["participation"] == "required")
    if row is None:
        if fl["high_water"].get(key, 0) > 0:
            return _view("unknown", required)
        ks = known_selection
        return _view("selected_not_activated" if ks else "not_selected", required)
    sel = scope["selection_id"]
    if row["activation_state"] == "revoked" or [sel, row["epoch"]] in fl["revoked"] or row["issuer_key_id"] in fl["revoked_keys"]:
        return _view("revoked", required)
    if row["activation_state"] == "withdrawn":
        return _view("withdrawn", required)
    ks = known_selection
    if row["epoch"] < fl["min_epochs"].get(sel, 0) or (ks and ks.get("selection_id") == sel and ks.get("epoch", 0) > row["epoch"]):
        return _view("superseded", required)
    if now >= row["valid_until"]:
        return _view("expired", required)
    if now < row["valid_from"]:
        return _view("not_yet_valid", required)
    return _view("active", required)


def _view(ps, required):
    if ps == "active":
        display = "ENABLED"
    elif required:
        # a required scope that is not active is never "disabled" and never a success state
        display = REQUIRED_UNAVAILABLE
    elif ps in ("withdrawn", "not_selected"):
        display = "DISABLED"
    else:
        display = ps
    return {"policy_state": ps, "required": required, "display": display}


# ------------------------------------------------------------------- guard


def _guard(st, o):
    st_out = copy.deepcopy(st)
    c = o["claim"]
    key = scope_key(c["scope"])
    now = o["now"]
    b = c["binding"]
    if _shape_problem(st):
        return st_out, _verdict(UNKNOWN_FAIL_CLOSED, "state_malformed")
    if st["store"] != "known":
        return st_out, _verdict(UNKNOWN_FAIL_CLOSED, "store_unknown")
    problem = _state_problem(st, o.get("external_anchor"))
    if problem:
        return st_out, _verdict(UNKNOWN_FAIL_CLOSED, problem)
    row = st["rows"].get(key)
    fl = st["floors"]
    sel = c["scope"]["selection_id"]
    ck = _chain_key(c["scope"])
    for k in st["rows"]:
        if k != key and _chain_key(_scope_from_key(k)) == ck:
            return st_out, _verdict(REFUSE, "selection_conflict")
    revoked = row is not None and (
        row["activation_state"] == "revoked" or [sel, row["epoch"]] in fl["revoked"])
    if b is None:
        return st_out, _guard_no_binding(st, key, row, revoked, now)
    if row is None:
        return st_out, _verdict(REFUSE, "not_activated")
    if revoked:
        return st_out, _verdict(REFUSE, "selection_revoked")
    if row["activation_state"] == "withdrawn":
        return st_out, _verdict(REFUSE, "selection_withdrawn")
    if b["selection_epoch"] < row["epoch"]:
        return st_out, _verdict(REFUSE_STALE, "selection_epoch_stale")
    if (b["selection_epoch"] != row["epoch"] or b["selection_digest"] != row["selection_digest"]
            or b["record"] != row["record"] or b["activation_ref"] != row["activation_ref"]):
        return st_out, _verdict(REFUSE, "policy_identity_mismatch")
    if row["epoch"] < fl["min_epochs"].get(sel, 0):
        return st_out, _verdict(REFUSE_STALE, "selection_epoch_stale")
    if row["issuer_key_id"] in fl["revoked_keys"]:
        return st_out, _verdict(REFUSE, "issuer_key_revoked")
    if now < row["valid_from"]:
        return st_out, _verdict(REFUSE, "selection_not_yet_effective")
    if now >= row["valid_until"]:
        return st_out, _verdict(REFUSE, "selection_expired")
    if st["scope_required"].get(key) and row["participation"] != "required":
        return st_out, _verdict(REFUSE, "participation_mismatch")
    snap = st["snapshot"]
    if snap is None:
        return st_out, _verdict(UNKNOWN_FAIL_CLOSED, "trust_snapshot_missing")
    if b["trust_snapshot_version"] < st["external"]["min_trust_snapshot_version"] or \
            _recorded_fingerprint(st, b["trust_snapshot_version"]) != b["trust_snapshot_fingerprint"]:
        return st_out, _verdict(REFUSE_STALE, "trust_snapshot_version_stale")
    if snap["valid_until"] <= now:
        return st_out, _verdict(UNKNOWN_FAIL_CLOSED, "trust_snapshot_expired")
    return st_out, _verdict(ACCEPT, "guard_pass", applied=True)


def _guard_no_binding(st, key, row, revoked, now):
    if st["scope_required"].get(key):
        return _verdict(REFUSE, "required_binding_missing")
    if revoked:
        return _verdict(REFUSE, "selection_revoked")
    if row is None:
        if _has_history(st, key):
            return _verdict(REFUSE, "optional_state_undetermined")
        return _fallback("never_activated")
    if row["activation_state"] == "withdrawn" and row["participation"] == "optional":
        return _fallback("withdrawn")
    if row["activation_state"] == "active" and row["participation"] == "optional" and now >= row["valid_until"]:
        return _fallback("expired")
    if row["activation_state"] == "active":
        return _verdict(REFUSE, "binding_omitted_over_active_policy")
    return _verdict(REFUSE, "optional_state_undetermined")


def _fallback(reason):
    return _verdict(ACCEPT, "overlay_not_applied", applied=False, fallback="caller_policy", fallback_reason=reason)


# ----------------------------------------------------------------- advance


def advance(state, observation):
    """Pure transition: ``(state, observation) -> (new_state, verdict)``.

    Inputs are never mutated. ``verdict`` is ``{"verdict": one of VERDICTS,
    "code": str, ...}``. Every rejected transition appends one negative-evidence
    record (``ocs-registry-failure-detail/1``) to ``new_state["evidence"]``; an
    ACCEPT never appends evidence. ``guard`` never changes state.
    """
    obs = copy.deepcopy(observation)
    try:
        _validate_obs(obs)
    except _Malformed:
        st = copy.deepcopy(state)
        return _refuse(st, obs if isinstance(obs, dict) else {}, REFUSE, "observation_malformed")
    kind = obs["kind"]
    if kind == "guard":
        return _guard(state, obs)
    st = copy.deepcopy(state)
    if _shape_problem(st):
        return st, _verdict(UNKNOWN_FAIL_CLOSED, "state_malformed")
    if kind == "lose_state":
        return _do_lose_state(st, obs)
    if kind == "restore":
        return _do_restore(st, obs)
    if kind == "rebaseline":
        return _do_rebaseline(st, obs)
    if kind == "relax_scope_required":
        # defined, NOT authorized in V1 (contract 7.3): refused by default, whatever it claims
        return _refuse(st, obs, REFUSE, "relaxation_not_authorized_v1")
    if st["store"] != "known":
        return _refuse(st, obs, UNKNOWN_FAIL_CLOSED, "store_unknown")
    problem = _state_problem(st, obs.get("external_anchor"))
    if problem:
        st["store"] = "unknown"
        st["unknown_reason"] = problem
        return _refuse(st, obs, UNKNOWN_FAIL_CLOSED, problem)
    if kind == "read":
        return st, _verdict(ACCEPT, "state_consistent")
    if kind == "select":
        return _do_select(st, obs)
    if kind == "withdraw":
        return _do_withdraw(st, obs)
    if kind == "sync":
        return _do_sync(st, obs)
    if kind == "external_floor":
        return _do_external_floor(st, obs)
    return _refuse(st, obs, REFUSE, "observation_malformed")  # unreachable; fail closed
