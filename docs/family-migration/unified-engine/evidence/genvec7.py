"""Generate tests/vectors/r08v7/identity_vectors.json with an INDEPENDENT canonical encoder (json.dumps sort_keys, ASCII), not the module's.
The preimage carries the integer `family_schema_revision` (not the legacy `family_version` tag). Run from the repository root."""
import hashlib, json
DOM = b"ocs-reg/r08-v7/effective-policy\n"
IRR = "f5-action-class-irreversibility-policy"
CASES = [
    ("irr-baseline", {"class_irreversible": {"class-a": "irreversible", "class-b": "no_change"}}),
    ("irr-all-irreversible", {"class_irreversible": {"class-a": "irreversible", "class-b": "irreversible", "class-c": "irreversible"}}),
    ("irr-all-no-change", {"class_irreversible": {"class-a": "no_change"}}),
    ("irr-single-irreversible", {"class_irreversible": {"class-a": "irreversible"}}),
]
vectors = []
for vid, eff in CASES:
    pre = {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v7", "family": IRR, "family_schema_revision": 1, "deny_all": [], "effective": eff}
    body = json.dumps(pre, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    vectors.append({"id": vid, "family": IRR, "effective": eff, "preimage": pre, "digest": "sha256:" + hashlib.sha256(DOM + body).hexdigest()})
open("tests/vectors/r08v7/identity_vectors.json", "w").write(json.dumps({"domain": "ocs-reg/r08-v7/effective-policy\\n", "profile": "ocs-effective-policy/1", "vectors": vectors}, indent=1, sort_keys=True) + "\n")
