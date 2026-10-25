"""EXT-S1-2: replay of the r08-v1 golden outcomes captured from the UNREFACTORED head (tests/golden/r08_v1_golden.json).

Every stored case is executed through the public r08-v1 interfaces and must reproduce the stored outcome exactly (compared
as canonical JSON bytes). A diff means r08-v1 behaviour changed: stop; never regenerate the file to obtain a pass.
DEVELOPER-TESTED builder evidence, not an independently qualified oracle.
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest

GOLDEN = Path(__file__).resolve().parent / "golden"
sys.path.insert(0, str(GOLDEN))
import v1_runner  # noqa: E402

DATA = json.loads((GOLDEN / "r08_v1_golden.json").read_text(encoding="utf-8"))


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def test_golden_file_is_the_expected_format():
    assert DATA["golden_format"] == 1 and DATA["contract"] == "r08-v1"
    assert len(DATA["cases"]) >= 5000
    assert [c["id"] for c in DATA["cases"]] == list(range(len(DATA["cases"])))
    kinds = {c["kind"] for c in DATA["cases"]}
    assert kinds == {"record", "selection", "verify", "decide", "compose", "compose_raw", "resolve", "resolve_authoritative"}


def test_golden_corpus_reaches_every_v1_code():
    from registry_successor import common as c
    seen = set()

    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get("code"), str):
                seen.add(x["code"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    for case in DATA["cases"]:
        walk(case["expected"])
    assert seen == set(c.CODES), sorted(set(c.CODES) ^ seen)


@pytest.mark.parametrize("chunk", range(0, len(DATA["cases"]), 500))
def test_v1_golden_replay_byte_identical(chunk):
    bad = []
    for case in DATA["cases"][chunk:chunk + 500]:
        got = v1_runner.execute(case, DATA["records"], DATA["selections"])
        if _canon(got) != _canon(case["expected"]):
            bad.append(case["id"])
    assert not bad, "r08-v1 behaviour changed for golden case ids %s" % bad[:20]


def test_golden_sha256_is_stable_within_run():
    # identity of the stored file is recorded in the PR description; this only guards against accidental truncation
    raw = (GOLDEN / "r08_v1_golden.json").read_bytes()
    assert len(hashlib.sha256(raw).hexdigest()) == 64 and len(raw) > 1_000_000
