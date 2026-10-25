"""Runner for the r08-v1 golden corpus (EXT-S1-2). Test support only.

Executes one stored case against the PUBLIC r08-v1 interfaces and returns a JSON-able outcome. The runner uses only
public functions (validate_record_text, parse_selection_envelope, verify_selection, verify_and_decide, compose_f1a,
resolve_effective), so the same file is used unchanged to capture goldens from the unrefactored head and to replay them
after the refactor. Developer evidence, not an independent oracle.
"""
import copy
import dataclasses
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r08_support as s  # noqa: E402,F401
from registry_successor import common as c  # noqa: E402
from registry_successor import verify as v  # noqa: E402
from registry_successor.compose import compose_f1a  # noqa: E402
from registry_successor.decision import verify_and_decide  # noqa: E402
from registry_successor.record import validate_record_text  # noqa: E402
from registry_successor.record import RecordResult  # noqa: E402
from registry_successor.selection import parse_selection_envelope, resolve_authoritative, resolve_effective  # noqa: E402

UTC = datetime.timezone.utc


def jsonable(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {"__type__": type(value).__name__,
                **{f.name: jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}}
    if isinstance(value, dict):
        return {str(k): jsonable(x) for k, x in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(x) for x in value]
    if isinstance(value, (set, frozenset)):
        return sorted((jsonable(x) for x in value), key=lambda x: json.dumps(x, sort_keys=True))
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    return {"__repr__": repr(value)}


def build_now(spec):
    if spec is None:
        return None
    if spec == "naive":
        return datetime.datetime(2026, 10, 25, 12, 0, 0)
    if spec == "plus1":
        return datetime.datetime(2026, 10, 25, 12, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=1)))
    if spec == "string":
        return "2026-10-25T12:00:00Z"
    return datetime.datetime.strptime(spec, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def build_context(spec):
    if spec is None:
        return None
    if spec == "junk":
        return {"consumer_id": "consumer-test"}
    return c.ExpectedContext(*spec)


def build_trust(spec):
    if spec is None:
        return None
    if spec == "junk":
        return {"snapshot_id": "x"}
    issuers = []
    for i in spec["issuers"]:
        grants = tuple(v.AuthorityGrant(*g) for g in i["authority"])
        issuers.append(v.IssuerEntry(i["key_id"], i["issuer_id"], i["alg"], i["public_key"].encode("ascii"), grants))
    return v.TrustSnapshot(
        snapshot_id=spec["snapshot_id"], version=spec["version"], valid_until=spec["valid_until"],
        issuers=tuple(issuers), revoked_key_ids=frozenset(spec["revoked_key_ids"]),
        revoked_selections=frozenset((a, b) for a, b in spec["revoked_selections"]),
        min_epochs=tuple((a, b) for a, b in spec["min_epochs"]))


class _Reject:
    def verify(self, alg, public_key, message, signature):
        return False


class _Raises:
    def verify(self, alg, public_key, message, signature):
        raise RuntimeError("boom")


class _Truthy:
    def verify(self, alg, public_key, message, signature):
        return 1  # truthy but not `True`


def build_verifier(spec):
    return {None: None, "fake": s.FakeVerifier(), "reject": _Reject(), "raises": _Raises(), "truthy": _Truthy(),
            "junk": object()}[spec]


def build_caller(spec):
    if spec is None:
        return None
    kind = spec["kind"]
    if kind == "json":
        return spec["value"]
    if kind == "set":
        return {k: set(x) for k, x in spec["value"].items()}
    if kind == "tuple":
        return {k: tuple(x) for k, x in spec["value"].items()}
    if kind == "frozenset":
        return {k: frozenset(x) for k, x in spec["value"].items()}
    raise ValueError(kind)


def expand(text):
    """Stored texts are plain strings, or {"pad": n, "text": t} (n spaces then t) or {"wrap": [open, close, n]}."""
    if isinstance(text, dict):
        if "pad" in text:
            return " " * text["pad"] + text["text"]
        if "wrap" in text:
            o, cl, n = text["wrap"]
            return o * n + cl * n
        raise ValueError(text)
    return text


def c_record_result(shape, body, base):
    if shape == "ok":
        return RecordResult(True, None, "", body, base.record_digest)
    if shape == "not-ok":
        return RecordResult(False, "field_invalid", "x", body, None)
    if shape == "none":
        return None
    if shape == "bare":
        return object()
    raise ValueError(shape)


def execute(case, records, selections):
    records = {k: expand(v) for k, v in records.items()}
    selections = {k: expand(v) for k, v in selections.items()}
    kind = case["kind"]
    if kind == "record":
        return jsonable(validate_record_text(case["text"] if "text" in case else records[case["record"]]))
    if kind == "selection":
        text = case["text"] if "text" in case else selections[case["selection"]]
        return jsonable(parse_selection_envelope(text))
    if kind == "verify":
        sel = parse_selection_envelope(selections[case["selection"]])
        rec = validate_record_text(records[case["record"]]) if case.get("record") is not None else None
        rep = v.verify_selection(sel, build_context(case["context"]), build_trust(case["trust"]),
                                 build_verifier(case["verifier"]), build_now(case["now"]), rec)
        return jsonable(rep)
    if kind == "decide":
        rt = records[case["record"]] if case.get("record") is not None else case.get("record_text")
        st = selections[case["selection"]] if case.get("selection") is not None else case.get("selection_text")
        d = verify_and_decide(case["participation"], build_caller(case["caller"]) if case["caller"] is not None else None,
                              rt, st, build_context(case["context"]), build_trust(case["trust"]),
                              build_verifier(case["verifier"]), build_now(case["now"]))
        return jsonable(d)
    if kind == "compose":
        rec = validate_record_text(records[case["record"]])
        res = compose_f1a(build_caller(case["caller"]), rec, case.get("operator", "intersection"))
        return jsonable(res)
    if kind == "compose_raw":
        base = validate_record_text(records[case["record"]])
        body = copy.deepcopy(base.record) if isinstance(base.record, dict) else base.record
        for path, val in case["mutate"]:
            node = body
            for step in path[:-1]:
                node = node[step]
            if val == "__delete__":
                del node[path[-1]]
            else:
                node[path[-1]] = val
        rec = c_record_result(case["shape"], body, base)
        res = compose_f1a(build_caller(case["caller"]), rec)
        return jsonable(res)
    if kind == "resolve_authoritative":
        return jsonable(resolve_authoritative(*case.get("args", []), **case.get("kwargs", {})))
    if kind == "resolve":
        sels = [parse_selection_envelope(selections[i]) for i in case["selections"]]
        res = resolve_effective(sels, build_context(case["context"]), build_now(case["now"]))
        return jsonable(res)
    raise ValueError(kind)
