"""Generate tests/vectors/r08v6/identity_vectors.json with an INDEPENDENT canonical encoder (json.dumps sort_keys, ASCII), not the module's.
Run from the repository root."""
import hashlib, json
DOM = b"ocs-reg/r08-v6/effective-policy\n"
RA, TR = "f5-action-class-revocation-assurance-policy", "f5-terminal-revocation-enablement-policy"
CASES = [
    ("ra-baseline", RA, {"class_requires_revocation_assurance": {"class-a": "required", "class-b": "not_required"}}),
    ("ra-all-required", RA, {"class_requires_revocation_assurance": {"class-a": "required", "class-b": "required", "class-c": "required"}}),
    ("ra-all-not-required", RA, {"class_requires_revocation_assurance": {"class-a": "not_required"}}),
    ("ra-single-required", RA, {"class_requires_revocation_assurance": {"class-a": "required"}}),
    ("tr-on", TR, {"terminal_revocation": "on"}),
    ("tr-off", TR, {"terminal_revocation": "off"}),
]
vectors = []
for vid, fam, eff in CASES:
    pre = {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v6", "family": fam, "family_version": "v6", "deny_all": [], "effective": eff}
    body = json.dumps(pre, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    vectors.append({"id": vid, "family": fam, "effective": eff, "preimage": pre, "digest": "sha256:" + hashlib.sha256(DOM + body).hexdigest()})
open("tests/vectors/r08v6/identity_vectors.json", "w").write(json.dumps({"domain": "ocs-reg/r08-v6/effective-policy\\n", "profile": "ocs-effective-policy/1", "vectors": vectors}, indent=1, sort_keys=True) + "\n")
