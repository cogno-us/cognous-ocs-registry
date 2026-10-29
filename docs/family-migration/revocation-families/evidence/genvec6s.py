"""Generate tests/vectors/r08v6/signed_selection_vector.json (one deterministic signed selection per family; SYNTHETIC test keys). Run from the repository root."""
import base64, json, sys
sys.path.insert(0, "tests")
import r08_support as r
import r08v6_support as t
from registry_successor import v6_selection
out = {}
for family in t.FAMILIES:
    rec = t.record(family=family)
    stmt = t.statement(rec)
    msg = v6_selection.signing_input_v6(stmt)
    sig = t.sign(stmt)
    d = t.decide(rec=rec)
    out[family] = {"record": rec, "statement": stmt, "envelope": t.envelope(stmt), "signing_input_hex": msg.hex(), "signature": sig,
                   "signature_hex": base64.b64decode(sig).hex(), "effective": d.effective, "note": "SYNTHETIC test keys; BUILDER_TESTED; non-authorizing"}
open("tests/vectors/r08v6/signed_selection_vector.json", "w").write(json.dumps(out, indent=1, sort_keys=True) + "\n")
