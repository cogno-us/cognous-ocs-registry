"""Generate tests/vectors/r08v8/identity_vectors.json with an INDEPENDENT canonical encoder (json.dumps sort_keys, ASCII), not the module's.
The preimage carries the integer `family_schema_revision` (not the legacy `family_version` tag). Run from the repository root. APPROVED CANDIDATE."""
import hashlib, json
DOM = b"ocs-reg/r08-v8/effective-policy\n"
ANC, AGE, TOL = "f5-anchor-deadline-to-inputs-policy", "f5-observation-max-age-policy", "f5-observation-clock-tolerance-policy"
CASES = [
    ("anchor-anchor", ANC, {"anchor_deadline_to_inputs": "anchor"}),
    ("anchor-no-change", ANC, {"anchor_deadline_to_inputs": "no_change"}),
    ("max-age-min", AGE, {"observation_max_age_seconds": 1}),
    ("max-age-60", AGE, {"observation_max_age_seconds": 60}),
    ("max-age-300", AGE, {"observation_max_age_seconds": 300}),
    ("max-age-token-ceiling", AGE, {"observation_max_age_seconds": 2147483647}),
    ("tolerance-zero", TOL, {"observation_clock_tolerance_seconds": 0}),
    ("tolerance-5", TOL, {"observation_clock_tolerance_seconds": 5}),
    ("tolerance-token-ceiling", TOL, {"observation_clock_tolerance_seconds": 2147483647}),
]
vectors = []
for vid, fam, eff in CASES:
    pre = {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v8", "family": fam, "family_schema_revision": 1, "deny_all": [], "effective": eff}
    body = json.dumps(pre, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    vectors.append({"id": vid, "family": fam, "effective": eff, "preimage": pre, "digest": "sha256:" + hashlib.sha256(DOM + body).hexdigest()})
open("tests/vectors/r08v8/identity_vectors.json", "w").write(json.dumps({"domain": "ocs-reg/r08-v8/effective-policy\\n", "profile": "ocs-effective-policy/1", "vectors": vectors}, indent=1, sort_keys=True) + "\n")
