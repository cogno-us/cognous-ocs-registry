"""Mutation check of the r08-v8 remaining-families modules. Usage: python mut_r8.py <repo_root> <out_dir>
Copies the repo to a temp root, applies ONE string mutation at a time to a NEW module (engine/families_anchor.py, engine/families_observation.py, the three thin v8 modules),
to the V8 block of engine/profiles.py, or to the additive `scalar-int` branch of engine/identity.py and the KINDS tuple of engine/profile.py, runs the r08-v8 test files and
records KILLED/SURVIVED. Frozen files (v1..v7) are not mutated: they are protected by the byte-identity baseline tests.
Environment: MUT_ONLY=ID1,ID2 (subset), MUT_PY (interpreter), MUT_K (pytest -k expression), MUT_SUFFIX (output suffix).
APPROVED CANDIDATE; BUILDER_TESTED developer evidence."""
import json, os, pathlib, shutil, subprocess, sys, tempfile
src_root, out_dir = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
work = pathlib.Path(tempfile.mkdtemp(prefix="mut_r8_"))
shutil.rmtree(work); shutil.copytree(src_root, work, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
D = work / "registry_successor"
E = "engine/"
AN, OB, ID, PK, PF = E + "families_anchor.py", E + "families_observation.py", E + "identity.py", E + "profile.py", E + "profiles.py"
TD, TF, TI = "v8_decision.py", "v8_families.py", "v8_policy_identity.py"
M = [
 # --- the anchor family
 ("AN01 order inverted", AN, "{ANCHOR: 0, NO_CHANGE: 1}", "{ANCHOR: 1, NO_CHANGE: 0}"),
 ("AN02 stricter picks the looser", AN, "return a if _RANK[a] <= _RANK[b] else b", "return a if _RANK[a] >= _RANK[b] else b"),
 ("AN03 is_value accepts str subclass", AN, "return type(v) is str and v in _RANK", "return isinstance(v, str) and v in _RANK"),
 ("AN04 payload unknown member tolerated", AN, "    if keys - set(ANCHOR_FIELDS):\n        return \"field_unknown\"\n", ""),
 ("AN05 payload missing member tolerated", AN, "    if set(ANCHOR_FIELDS) - keys:\n        return \"field_missing\"\n", ""),
 ("AN06 payload value type check dropped", AN, "    if type(value) is not str:\n        return \"field_type_invalid\"\n", ""),
 ("AN07 payload key type check dropped", AN, "if type(payload) is not dict or not all(type(k) is str for k in payload):", "if type(payload) is not dict:"),
 ("AN08 family not checked in composer", AN, "if type(family_seen) is not str or family_seen != FAMILY_ANCHOR:", "if type(family_seen) is not str:"),
 ("AN09 operator not checked", AN, "if type(operator) is not str or operator != \"intersection\":", "if False:"),
 ("AN10 record ok flag truthy accepted", AN, "if getattr(record, \"ok\", False) is not True:", "if not getattr(record, \"ok\", False):"),
 ("AN11 caller extra key tolerated", AN, "or set(snap) != set(ANCHOR_FIELDS) or not is_value", "or ANCHOR_FIELD not in snap or not is_value"),
 ("AN12 caller value domain not checked", AN, " or not is_value(snap[ANCHOR_FIELD]):\n        return None", ":\n        return None"),
 ("AN13 registry overrides caller (lowering)", AN, "{ANCHOR_FIELD: stricter(base, reg)}", "{ANCHOR_FIELD: reg}"),
 ("AN14 not-narrowing reported on equal values", AN, "if _RANK[reg] > _RANK[base] else \"\"", "if _RANK[reg] >= _RANK[base] else \"\""),
 ("AN15 deny_all set", AN, "{ANCHOR_FIELD: stricter(base, reg)}, False, ())", "{ANCHOR_FIELD: stricter(base, reg)}, True, (ANCHOR_FIELD,))"),
 ("AN16 schema revision changed", AN, "SCHEMA_REVISION = 1", "SCHEMA_REVISION = 2"),
 ("AN17 member name changed", AN, "ANCHOR_FIELD = \"anchor_deadline_to_inputs\"", "ANCHOR_FIELD = \"anchor_deadline\""),
 ("AN18 vocabulary order swapped", AN, "VALUES = (ANCHOR, NO_CHANGE)", "VALUES = (NO_CHANGE, ANCHOR)"),
 ("AN19 caller snapshot bound off by one", AN, "snap = _snapshot(caller, len(ANCHOR_FIELDS))", "snap = _snapshot(caller, len(ANCHOR_FIELDS) + 1)"),
 ("AN20 payload copy skipped (aliased)", AN, "    snap = dict(payload)\n    if payload_validator(snap)", "    snap = payload\n    if payload_validator(snap)"),
 ("AN21 not-narrowing detail text changed", AN, "NOT_NARROWING = \"registry_value_not_narrowing\"", "NOT_NARROWING = \"registry_value_narrowing\""),
 ("AN22 value vocabulary admits false", AN, "_RANK = MappingProxyType({ANCHOR: 0, NO_CHANGE: 1})", "_RANK = MappingProxyType({ANCHOR: 0, NO_CHANGE: 1, \"false\": 2})"),
 ("AN23 payload dict type not exact", AN, "    if type(payload) is not dict:\n        return None, \"composition_record_invalid\"\n    snap", "    if not isinstance(payload, dict):\n        return None, \"composition_record_invalid\"\n    snap"),
 ("AN24 record body type not exact", AN, "    if type(body) is not dict:\n        return None, \"composition_record_invalid\"\n    family_seen", "    if not isinstance(body, dict):\n        return None, \"composition_record_invalid\"\n    family_seen"),
 # --- the two observation families
 ("OB01 max-age floor lowered to 0", OB, "MAX_AGE_MIN = 1", "MAX_AGE_MIN = 0"),
 ("OB02 tolerance floor raised to 1", OB, "TOLERANCE_MIN = 0", "TOLERANCE_MIN = 1"),
 ("OB03 ceiling off by one", OB, "INT_MAX = c.MAX_INT", "INT_MAX = c.MAX_INT + 1"),
 ("OB04 max-age accepts bool/subclass", OB, "def is_max_age(v: Any) -> bool:\n    return type(v) is int and", "def is_max_age(v: Any) -> bool:\n    return isinstance(v, int) and"),
 ("OB05 tolerance accepts bool/subclass", OB, "def is_tolerance(v: Any) -> bool:\n    return type(v) is int and", "def is_tolerance(v: Any) -> bool:\n    return isinstance(v, int) and"),
 ("OB06 max-age ceiling dropped", OB, "MAX_AGE_MIN <= v <= INT_MAX", "MAX_AGE_MIN <= v"),
 ("OB07 tolerance ceiling dropped", OB, "TOLERANCE_MIN <= v <= INT_MAX", "TOLERANCE_MIN <= v"),
 ("OB08 tolerance floor dropped", OB, "TOLERANCE_MIN <= v <= INT_MAX", "v <= INT_MAX"),
 ("OB09 max-age floor dropped", OB, "MAX_AGE_MIN <= v <= INT_MAX", "v <= INT_MAX"),
 ("OB10 payload unknown member tolerated", OB, "    if keys - {field}:\n        return \"field_unknown\"\n", ""),
 ("OB11 payload missing member tolerated", OB, "    if {field} - keys:\n        return \"field_missing\"\n", ""),
 ("OB12 payload value type check dropped", OB, "    if type(payload[field]) is not int:\n        return \"field_type_invalid\"\n", ""),
 ("OB13 composition takes the maximum", OB, "{field: min(base, reg)}", "{field: max(base, reg)}"),
 ("OB14 registry overrides caller", OB, "{field: min(base, reg)}", "{field: reg}"),
 ("OB15 not-narrowing reported on equal values", OB, "if reg > base else \"\"", "if reg >= base else \"\""),
 ("OB16 family not checked in composer", OB, "if type(family_seen) is not str or family_seen != family:", "if type(family_seen) is not str:"),
 ("OB17 operator not checked", OB, "if type(operator) is not str or operator != \"intersection\":", "if False:"),
 ("OB18 caller domain not checked", OB, "if snap is None or set(snap) != {field} or not ok(snap[field]):", "if snap is None or set(snap) != {field}:"),
 ("OB19 tolerance composer uses the max-age validator", OB, "return _compose(FAMILY_TOLERANCE, TOLERANCE_FIELD, tolerance_payload_validator,", "return _compose(FAMILY_TOLERANCE, TOLERANCE_FIELD, max_age_payload_validator,"),
 ("OB20 tolerance composer uses the max-age normalizer", OB, "tolerance_payload_validator, normalize_caller_tolerance, caller, record, operator)", "tolerance_payload_validator, normalize_caller_max_age, caller, record, operator)"),
 ("OB21 tolerance member aliases the held constructor name", OB, "TOLERANCE_FIELD = \"observation_clock_tolerance_seconds\"", "TOLERANCE_FIELD = \"clock_tolerance_seconds\""),
 ("OB22 max-age member loses its prefix", OB, "MAX_AGE_FIELD = \"observation_max_age_seconds\"", "MAX_AGE_FIELD = \"max_age_seconds\""),
 ("OB23 deny_all set", OB, "{field: min(base, reg)}, False, ())", "{field: min(base, reg)}, True, (field,))"),
 ("OB24 caller snapshot bound off by one", OB, "snap = _snapshot(caller, 1)", "snap = _snapshot(caller, 2)"),
 ("OB25 payload key type check dropped", OB, "if type(payload) is not dict or not all(type(k) is str for k in payload):\n        return \"field_type_invalid\"\n    keys", "if type(payload) is not dict:\n        return \"field_type_invalid\"\n    keys"),
 ("OB26 str-subclass family accepted by the composer", OB, "if type(family_seen) is not str or family_seen != family:", "if family_seen != family:"),
 ("OB27 payload copy skipped (aliased)", OB, "        snap = dict(payload)\n        if validator(snap)", "        snap = payload\n        if validator(snap)"),
 ("OB28 schema revision changed", OB, "SCHEMA_REVISION = 1", "SCHEMA_REVISION = 2"),
 ("OB29 not-narrowing detail text changed", OB, "NOT_NARROWING = \"registry_value_not_narrowing\"", "NOT_NARROWING = \"registry_value_narrowing\""),
 ("OB30 family id of max-age changed", OB, "FAMILY_MAX_AGE = \"f5-observation-max-age-policy\"", "FAMILY_MAX_AGE = \"f5-observation-max-age\""),
 ("OB31 family id of tolerance changed", OB, "FAMILY_TOLERANCE = \"f5-observation-clock-tolerance-policy\"", "FAMILY_TOLERANCE = \"f5-observation-clock-tolerance\""),
 ("OB32 max-age composer reads the tolerance field", OB, "return _compose(FAMILY_MAX_AGE, MAX_AGE_FIELD,", "return _compose(FAMILY_MAX_AGE, TOLERANCE_FIELD,"),
 ("OB33 record ok flag truthy accepted", OB, "        if getattr(record, \"ok\", False) is not True:", "        if not getattr(record, \"ok\", False):"),
 ("OB34 record body type not exact", OB, "        if type(body) is not dict:\n            return _refuse(\"composition_record_invalid\")\n        family_seen", "        if not isinstance(body, dict):\n            return _refuse(\"composition_record_invalid\")\n        family_seen"),
 ("OB35 payload dict type not exact", OB, "        if type(payload) is not dict:\n            return _refuse(\"composition_record_invalid\")\n        snap", "        if not isinstance(payload, dict):\n            return _refuse(\"composition_record_invalid\")\n        snap"),
 # --- the additive scalar-int identity kind
 ("SI01 scalar-int type check dropped", ID, "        if type(value) is not int:\n            pid._type_refusal(field, value)\n", ""),
 ("SI02 scalar-int type check accepts bool", ID, "        if type(value) is not int:", "        if not isinstance(value, int):"),
 ("SI03 scalar-int value domain not checked", ID, "            pid._type_refusal(field, value)\n        if not row.is_value(value):\n            pid._refuse(\"field_invalid\", field)\n    else:  # scalar-enum", "            pid._type_refusal(field, value)\n    else:  # scalar-enum"),
 ("SI04 scalar-int branch selected for scalar-enum", ID, "elif row.kind == \"scalar-int\":", "elif row.kind == \"scalar-enum\":"),
 ("SI05 scalar-int refuses with the wrong code", ID, "            pid._refuse(\"field_invalid\", field)\n    else:  # scalar-enum", "            pid._refuse(\"field_type_invalid\", field)\n    else:  # scalar-enum"),
 ("SI06 scalar-int member path wrong", ID, "        if type(value) is not int:\n            pid._type_refusal(field, value)", "        if type(value) is not int:\n            pid._type_refusal(None, value)"),
 ("SI07 KINDS lacks scalar-int", PK, "KINDS = (\"classmap-enum\", \"scalar-enum\", \"scalar-int\")", "KINDS = (\"classmap-enum\", \"scalar-enum\")"),
 ("SI08 KINDS admits an unknown kind", PK, "KINDS = (\"classmap-enum\", \"scalar-enum\", \"scalar-int\")", "KINDS = (\"classmap-enum\", \"scalar-enum\", \"scalar-int\", \"scalar-float\")"),
 # --- the V8 profile
 ("PV01 v8 selection domain wrong", PF, "SELECTION_DOMAIN_V8 = b\"ocs-reg/r08-v8/selection\\n\"", "SELECTION_DOMAIN_V8 = b\"ocs-reg/r08-v8/selectionx\\n\""),
 ("PV02 v8 effective domain wrong", PF, "EFFECTIVE_DOMAIN_V8 = b\"ocs-reg/r08-v8/effective-policy\\n\"", "EFFECTIVE_DOMAIN_V8 = b\"ocs-reg/r08-v8/effective-policx\\n\""),
 ("PV03 v8 anchor identity kind is scalar-int", PF, "IdentityRow(anc.FAMILY_ANCHOR, \"scalar-enum\"", "IdentityRow(anc.FAMILY_ANCHOR, \"scalar-int\""),
 ("PV04 v8 max-age identity kind is scalar-enum", PF, "IdentityRow(obs.FAMILY_MAX_AGE, \"scalar-int\"", "IdentityRow(obs.FAMILY_MAX_AGE, \"scalar-enum\""),
 ("PV05 v8 tolerance value vocabulary is max-age's", PF, "obs.TOLERANCE_FIELDS, obs.is_tolerance, VERSION_MEMBER_REVISION", "obs.TOLERANCE_FIELDS, obs.is_max_age, VERSION_MEMBER_REVISION"),
 ("PV06 v8 max-age value vocabulary is tolerance's", PF, "obs.MAX_AGE_FIELDS, obs.is_max_age, VERSION_MEMBER_REVISION", "obs.MAX_AGE_FIELDS, obs.is_tolerance, VERSION_MEMBER_REVISION"),
 ("PV07 v8 enforcing component runtime", PF, "        enforcing_component=families.COMPONENT_CONTROL_PLANE,\n    )\n\n\n_ANCHOR_SPEC", "        enforcing_component=families.COMPONENT_RUNTIME,\n    )\n\n\n_ANCHOR_SPEC"),
 ("PV08 v8 evaluator binding swapped", PF, "        evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),\n        caller_normalizer=normalizer,", "        evaluator_binding=(c.EVALUATOR_BINDING, c.EVALUATOR_ID),\n        caller_normalizer=normalizer,"),
 ("PV09 v8 anchor composer swapped", PF, "anc.payload_validator, anc.compose_anchor, anc.normalize_caller)", "anc.payload_validator, obs.compose_max_age, anc.normalize_caller)"),
 ("PV10 v8 tolerance schema revision 2", PF, "obs.FAMILY_TOLERANCE: FamilyEntry(_TOLERANCE_SPEC, obs.SCHEMA_REVISION)", "obs.FAMILY_TOLERANCE: FamilyEntry(_TOLERANCE_SPEC, 2)"),
 ("PV11 v8 family order changed", PF, "        anc.FAMILY_ANCHOR: FamilyEntry(_ANCHOR_SPEC, anc.SCHEMA_REVISION),\n        obs.FAMILY_MAX_AGE: FamilyEntry(_MAX_AGE_SPEC, obs.SCHEMA_REVISION),", "        obs.FAMILY_MAX_AGE: FamilyEntry(_MAX_AGE_SPEC, obs.SCHEMA_REVISION),\n        anc.FAMILY_ANCHOR: FamilyEntry(_ANCHOR_SPEC, anc.SCHEMA_REVISION),"),
 ("PV12 v8 contract version changed", PF, "CONTRACT_V8 = \"r08-v8\"", "CONTRACT_V8 = \"r08-v9\""),
 ("PV13 v8 registered in PROFILES", PF, "PROFILES = MappingProxyType({CONTRACT_V7: V7, v6_families.CONTRACT_V6: V6_COMPAT})", "PROFILES = MappingProxyType({CONTRACT_V7: V7, v6_families.CONTRACT_V6: V6_COMPAT, CONTRACT_V8: V8})"),
 ("PV14 v8 anchor uses the legacy tag member", PF, "anc.is_value, VERSION_MEMBER_REVISION, anc.SCHEMA_REVISION)", "anc.is_value, VERSION_MEMBER_TAG, \"v8\")"),
 ("PV15 v8 max-age family id mapped to the tolerance spec", PF, "obs.FAMILY_MAX_AGE: FamilyEntry(_MAX_AGE_SPEC,", "obs.FAMILY_MAX_AGE: FamilyEntry(_TOLERANCE_SPEC,"),
 ("PV16 v7 selection domain changed (v7 untouched)", PF, "SELECTION_DOMAIN_V7 = b\"ocs-reg/r08-v7/selection\\n\"", "SELECTION_DOMAIN_V7 = b\"ocs-reg/r08-v7/selectionx\\n\""),
 # --- thin v8 bindings
 ("TH01 v8 families bound to the v7 profile", TF, "FAMILIES_V8: Mapping = _profiles.V8.specs", "FAMILIES_V8: Mapping = _profiles.V7.specs"),
 ("TH02 v8 lookup bound to the v7 profile", TF, "return _p.lookup(_profiles.V8, family)", "return _p.lookup(_profiles.V7, family)"),
 ("TH03 v8 table selector bound to the v7 profile", TF, "return _p.table_for_contract_version(_profiles.V8, version)", "return _p.table_for_contract_version(_profiles.V7, version)"),
 ("TH04 v8 compose bound to the v7 profile", TF, "return _p.compose(_profiles.V8, caller, record, operator)", "return _p.compose(_profiles.V7, caller, record, operator)"),
 ("TH05 v8 compose_for bound to the v7 profile", TF, "return _p.compose_for(_profiles.V8, version, caller, record, operator)", "return _p.compose_for(_profiles.V7, version, caller, record, operator)"),
 ("TH06 v8 decision bound to the v7 profile", TD, "return _decide.verify_and_decide(_profiles.V8,", "return _decide.verify_and_decide(_profiles.V7,"),
 ("TH07 v8 identity digest bound to the v7 profile", TI, "return _id.effective_policy_digest(_profiles.V8, family, payload, contract_version)", "return _id.effective_policy_digest(_profiles.V7, family, payload, contract_version)"),
 ("TH08 v8 identity default contract version", TI, "def effective_policy_digest(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION)", "def effective_policy_digest(family: Any, payload: Any, contract_version: Any = \"r08-v7\")"),
 ("TH09 v8 preimage bound to the v7 profile", TI, "return _id.effective_preimage(_profiles.V8, family, payload, contract_version)", "return _id.effective_preimage(_profiles.V7, family, payload, contract_version)"),
 ("TH10 v8 payload validation bound to the v7 profile", TI, "return _id.validate_effective_payload(_profiles.V8, family, payload)", "return _id.validate_effective_payload(_profiles.V7, family, payload)"),
 ("TH11 v8 registered version bound to the v7 profile", TI, "return _id.registered_family_version(_profiles.V8, family, contract_version)", "return _id.registered_family_version(_profiles.V7, family, contract_version)"),
 ("TH12 v8 deny-all dimensions bound to the v7 profile", TI, "return _id.deny_all_dimensions(_profiles.V8, family, payload)", "return _id.deny_all_dimensions(_profiles.V7, family, payload)"),
 ("TH13 v8 digest-of-preimage bound to the v7 profile", TI, "return _id.effective_digest_of_preimage(_profiles.V8, preimage)", "return _id.effective_digest_of_preimage(_profiles.V7, preimage)"),
 ("TH14 v8 effective prefix of the v7 profile", TI, "EFFECTIVE_PREFIX = _profiles.V8.effective_policy_domain", "EFFECTIVE_PREFIX = _profiles.V7.effective_policy_domain"),
 ("TH15 v8 identity rows of the v7 profile", TI, "IDENTITY_FAMILIES = _profiles.V8.identity", "IDENTITY_FAMILIES = _profiles.V7.identity"),
 ("TH16 v8 public anchor id constant points at max-age", TF, "FAMILY_ANCHOR_V8 = _anchor.FAMILY_ANCHOR", "FAMILY_ANCHOR_V8 = _obs.FAMILY_MAX_AGE"),
 ("TH17 v8 public tolerance id constant points at max-age", TF, "FAMILY_OBSERVATION_CLOCK_TOLERANCE_V8 = _obs.FAMILY_TOLERANCE", "FAMILY_OBSERVATION_CLOCK_TOLERANCE_V8 = _obs.FAMILY_MAX_AGE"),
 ("TH18 v8 public family id tuple order changed", TF, "FAMILY_IDS_V8 = (FAMILY_ANCHOR_V8, FAMILY_OBSERVATION_MAX_AGE_V8, FAMILY_OBSERVATION_CLOCK_TOLERANCE_V8)", "FAMILY_IDS_V8 = (FAMILY_OBSERVATION_MAX_AGE_V8, FAMILY_ANCHOR_V8, FAMILY_OBSERVATION_CLOCK_TOLERANCE_V8)"),
]
ONLY = [x for x in os.environ.get("MUT_ONLY", "").split(",") if x]
PY = os.environ.get("MUT_PY", sys.executable)
TESTS = sorted(str(p.relative_to(work)) for p in (work / "tests").glob("test_r08v8_*.py"))
def run():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    k = ["-k", os.environ["MUT_K"]] if os.environ.get("MUT_K") else []  # e.g. "not frozen_baseline" to deselect the byte-identity tests
    return subprocess.run([PY, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"] + k + TESTS, cwd=work, capture_output=True, text=True, env=env)
base = run()
assert base.returncode == 0, "unmutated tree must pass:\n" + base.stdout[-2000:]
res, log = [], []
for name, fn, a, b in M:
    if ONLY and name.split()[0] not in ONLY: continue
    F = D / fn; orig = F.read_text()
    if orig.count(a) != 1:
        res.append((name, "PATTERN COUNT %d" % orig.count(a), "")); print(*res[-1], flush=True); continue
    F.write_text(orig.replace(a, b))
    try:
        r = run()
        tail = [l for l in r.stdout.splitlines() if l.startswith("FAILED") or l.startswith("ERROR")]
        status, detail = ("KILLED", (tail[0][:160] if tail else r.stdout.strip().splitlines()[-1][:160])) if r.returncode else ("SURVIVED", "v8 tests pass")
        log.append("=== %s [%s]\n%s\n" % (name, status, r.stdout[-1500:]))
    finally:
        F.write_text(orig)
    res.append((name, status, detail)); print(*res[-1], flush=True)
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / ("mutation-results-r08v8%s.json" % os.environ.get("MUT_SUFFIX", ""))).write_text(json.dumps({"tests": TESTS, "results": res}, indent=1))
(out_dir / ("mutation-raw-log-r08v8%s.txt" % os.environ.get("MUT_SUFFIX", ""))).write_text("\n".join(log))
print("TOTAL", len(res), "KILLED", sum(1 for x in res if x[1] == "KILLED"), "SURVIVED", [x[0] for x in res if x[1] == "SURVIVED"], "PATTERN", [x[0] for x in res if x[1].startswith("PATTERN")])
