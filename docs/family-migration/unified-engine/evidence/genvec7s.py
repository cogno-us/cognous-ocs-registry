"""Generate tests/vectors/r08v7/signed_selection_vector.json (one deterministic signed selection; SYNTHETIC test keys). Run from the repository root with PYTHONPATH=. ."""
import base64, json, sys
sys.path.insert(0, "tests")
import r08_support as r
import r08v7_support as t
from registry_successor.engine import profiles, selection as selection_e
out = {}
for family in t.FAMILIES:
    rec = t.record(family=family)
    stmt = t.statement(rec)
    msg = selection_e.signing_input(profiles.V7, stmt)
    sig = t.sign(stmt)
    d = t.decide(rec=rec)
    out[family] = {"record": rec, "statement": stmt, "envelope": t.envelope(stmt), "signing_input_hex": msg.hex(), "signature": sig,
                   "signature_hex": base64.b64decode(sig).hex(), "effective": d.effective, "note": "SYNTHETIC test keys; BUILDER_TESTED; non-authorizing"}
open("tests/vectors/r08v7/signed_selection_vector.json", "w").write(json.dumps(out, indent=1, sort_keys=True) + "\n")
