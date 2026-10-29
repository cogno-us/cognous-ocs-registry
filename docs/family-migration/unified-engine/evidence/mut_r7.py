"""Mutation check of the r08-v7 unified-engine guards. Usage: python mut_r7.py <repo_root> <out_dir>
Copies the repo to a temp root, applies ONE string mutation at a time to an engine module, the irreversibility family module or a thin v7 module, runs the
r08-v7 test files, records KILLED/SURVIVED. Frozen files (v1..v6 modules) are not mutated: they are protected by the byte-identity baseline test.
Environment: MUT_ONLY=ID1,ID2 (subset), MUT_PY (interpreter), MUT_K (pytest -k expression), MUT_SUFFIX (output suffix).
BUILDER_TESTED developer evidence."""
import json, os, pathlib, shutil, subprocess, sys, tempfile
src_root, out_dir = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
work = pathlib.Path(tempfile.mkdtemp(prefix="mut_r7_"))
shutil.rmtree(work); shutil.copytree(src_root, work, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
D = work / "registry_successor"
E = "engine/"
IR, PR, PF, SE, RE, VE, DE, ID = (E + "families_irreversibility.py", E + "profile.py", E + "profiles.py", E + "selection.py", E + "record.py", E + "verify.py",
                                  E + "decide.py", E + "identity.py")
TF, TD, TI = "v7_families.py", "v7_decision.py", "v7_policy_identity.py"
M = [
 # --- the irreversibility family
 ("IR01 order inverted", IR, "{IRREVERSIBLE: 0, NO_CHANGE: 1}", "{IRREVERSIBLE: 1, NO_CHANGE: 0}"),
 ("IR02 stricter picks the looser", IR, "return a if _RANK[a] <= _RANK[b] else b", "return a if _RANK[a] >= _RANK[b] else b"),
 ("IR03 is_value accepts str subclass", IR, "return type(v) is str and v in _RANK", "return isinstance(v, str) and v in _RANK"),
 ("IR04 payload sort check dropped", IR, " or names != sorted(names)", ""),
 ("IR05 class limit off by one", IR, "if not m or len(m) > MAX_CLASSES:\n        return \"field_invalid\"", "if not m or len(m) > MAX_CLASSES + 1:\n        return \"field_invalid\""),
 ("IR06 empty class map accepted", IR, "    if not m or len(m) > MAX_CLASSES:\n        return \"field_invalid\"", "    if len(m) > MAX_CLASSES:\n        return \"field_invalid\""),
 ("IR07 unknown registry class accepted", IR, "if set(reg) - set(base):", "if False:"),
 ("IR08 caller value domain not checked", IR, "    if not all(frozen_token_valid(k) for k in m) or not all(is_value(v) for v in m.values()):\n        return None", "    if not all(frozen_token_valid(k) for k in m):\n        return None"),
 ("IR09 empty caller map accepted", IR, "if m is None or not m:", "if m is None:"),
 ("IR10 not-narrowing reported on equal values", IR, "if k in base and _RANK[reg[k]] > _RANK[base[k]]]", "if k in base and _RANK[reg[k]] >= _RANK[base[k]]]"),
 ("IR11 family not checked in composer", IR, "if type(family_seen) is not str or family_seen != FAMILY_IRREVERSIBILITY:", "if type(family_seen) is not str:"),
 ("IR12 payload str-subclass value accepted", IR, "or not all(type(v) is str for v in m.values()):", "or not all(isinstance(v, str) for v in m.values()):"),
 ("IR13 operator not checked", IR, "if type(operator) is not str or operator != \"intersection\":", "if False:"),
 ("IR14 registry overrides caller (lowering)", IR, "eff = {k: (stricter(base[k], reg[k]) if k in reg else base[k]) for k in base}", "eff = {k: (reg[k] if k in reg else base[k]) for k in base}"),
 ("IR15 deny_all set", IR, "{IRR_FIELD: eff}, False, ())", "{IRR_FIELD: eff}, True, (IRR_FIELD,))"),
 ("IR16 record ok flag truthy accepted", IR, "if getattr(record, \"ok\", False) is not True:", "if not getattr(record, \"ok\", False):"),
 ("IR17 payload type before value order lost", IR, "    if not all(type(k) is str for k in m) or not all(type(v) is str for v in m.values()):\n        return \"field_type_invalid\"\n", ""),
 ("IR18 caller class tokens unchecked", IR, "    if not all(frozen_token_valid(k) for k in m) or not all(is_value(v) for v in m.values()):\n        return None", "    if not all(is_value(v) for v in m.values()):\n        return None"),
 ("IR19 caller class map not sorted/copied", IR, "return {IRR_FIELD: {k: m[k] for k in sorted(m)}}", "return {IRR_FIELD: snap[IRR_FIELD]}"),
 ("IR20 vocabulary order swapped", IR, "VALUES = (IRREVERSIBLE, NO_CHANGE)", "VALUES = (NO_CHANGE, IRREVERSIBLE)"),
 ("IR21 schema revision changed", IR, "SCHEMA_REVISION = 1", "SCHEMA_REVISION = 2"),
 ("IR22 payload key type check dropped", IR, "if type(payload) is not dict or not all(type(k) is str for k in payload):", "if type(payload) is not dict:"),
 ("IR23 caller map bound off by one", IR, "m = _snapshot(snap[IRR_FIELD], MAX_CLASSES)", "m = _snapshot(snap[IRR_FIELD], MAX_CLASSES + 1)"),
 ("IR24 payload member unknown tolerated", IR, "    if keys - set(IRR_FIELDS):\n        return \"field_unknown\"\n", ""),
 ("IR25 payload member missing tolerated", IR, "    if set(IRR_FIELDS) - keys:\n        return \"field_missing\"\n", ""),
 ("IR26 caller extra key tolerated", IR, "if snap is None or set(snap) != set(IRR_FIELDS):", "if snap is None or IRR_FIELD not in snap:"),
 # --- profile, table and dispatch
 ("PR01 lookup accepts non-exact str", PR, "    if type(family) is not str:\n        return None\n    try:\n        entry", "    try:\n        entry"),
 ("PR02 table selector accepts str subclass", PR, "if type(version) is str and version == profile.version:", "if version == profile.version:"),
 ("PR03 compose_for ignores contract version", PR, "    if not table_for_contract_version(profile, version).ok:\n        return _refuse(\"contract_unsupported\")\n", ""),
 ("PR04 unknown family composes", PR, "        if spec is None:\n            return _refuse(\"composition_family_unsupported\")\n", ""),
 ("PR05 compose operator not checked", PR, "        if type(operator) is not str or operator != \"intersection\":\n            return _refuse(\"composition_operator_unsupported\")\n", ""),
 ("PR06 require_profile accepts subclasses", PR, "if type(profile) is not ContractProfile:", "if not isinstance(profile, ContractProfile):"),
 ("PR07 identical domains allowed", PR, "        if self.selection_signing_domain == self.effective_policy_domain:\n            _fail(\"domains must differ\")\n", ""),
 ("PR08 domain need not name the version", PR, " or (\"/\" + self.version + \"/\").encode(\"ascii\") not in prefix", ""),
 ("PR09 domain need not end in newline", PR, "not prefix.endswith(b\"\\n\") or ", ""),
 ("PR10 schema revision 0 allowed", PR, "entry.schema_revision < 1 or", "entry.schema_revision < 0 or"),
 ("PR11 tag profile may carry a revision", PR, "if entry.schema_revision is not None or type(row.version_value) is not str", "if type(row.version_value) is not str"),
 ("PR12 family table aliased not copied", PR, "object.__setattr__(self, \"families\", MappingProxyType(families))", "object.__setattr__(self, \"families\", MappingProxyType(fam))"),
 ("PR13 record ok flag truthy accepted", PR, "        if getattr(record, \"ok\", False) is not True:\n            return _refuse(\"composition_record_invalid\")", "        if not getattr(record, \"ok\", False):\n            return _refuse(\"composition_record_invalid\")"),
 ("PR14 table order not compared", PR, "or list(fam) != list(ident):", "or set(fam) != set(ident):"),
 ("PR15 family entry type unchecked", PR, "type(entry) is not FamilyEntry or ", ""),
 ("PR16 revision bool accepted", PR, "type(entry.schema_revision) is not int or entry.schema_revision < 1", "not isinstance(entry.schema_revision, int) or entry.schema_revision < 1"),
 ("PR17 spec family vs key unchecked", PR, " or entry.spec.family != key:", ":"),
 ("PR18 identity members vs spec unchecked", PR, "\\\n                    or tuple(entry.spec.payload_fields) != row.members or not callable(row.is_value):", "\\\n                    or not callable(row.is_value):"),
 # --- shipped profiles and thin bindings
 ("PF01 v7 selection domain wrong", PF, "SELECTION_DOMAIN_V7 = b\"ocs-reg/r08-v7/selection\\n\"", "SELECTION_DOMAIN_V7 = b\"ocs-reg/r08-v7/selectionx\\n\""),
 ("PF02 v7 effective domain wrong", PF, "EFFECTIVE_DOMAIN_V7 = b\"ocs-reg/r08-v7/effective-policy\\n\"", "EFFECTIVE_DOMAIN_V7 = b\"ocs-reg/r08-v7/effective-policx\\n\""),
 ("PF03 v7 evaluator binding swapped", PF, "evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),\n    caller_normalizer=irr", "evaluator_binding=(c.EVALUATOR_BINDING, c.EVALUATOR_ID),\n    caller_normalizer=irr"),
 ("PF04 v7 enforcing component runtime", PF, "enforcing_component=families.COMPONENT_CONTROL_PLANE,\n)\n\nV7", "enforcing_component=families.COMPONENT_RUNTIME,\n)\n\nV7"),
 ("PF05 v6 compat tag value changed", PF, "VERSION_MEMBER_TAG, row.family_version)", "VERSION_MEMBER_TAG, \"v7\")"),
 ("PF06 v7 uses the legacy tag member", PF, "irr.is_value, VERSION_MEMBER_REVISION, irr.SCHEMA_REVISION)", "irr.is_value, VERSION_MEMBER_TAG, \"v7\")"),
 ("PF07 v6 compat value vocabulary of the wrong family", PF, "_V6_IS_VALUE = MappingProxyType({v6_ra.FAMILY_F5RA: v6_ra.is_value, v6_tr.FAMILY_TR: v6_tr.is_value})", "_V6_IS_VALUE = MappingProxyType({v6_ra.FAMILY_F5RA: v6_tr.is_value, v6_tr.FAMILY_TR: v6_ra.is_value})"),
 ("TH01 v7 families bound to the v6 profile", TF, "FAMILIES_V7: Mapping = _profiles.V7.specs", "FAMILIES_V7: Mapping = _profiles.V6_COMPAT.specs"),
 ("TH02 v7 lookup bound to the v6 profile", TF, "return _p.lookup(_profiles.V7, family)", "return _p.lookup(_profiles.V6_COMPAT, family)"),
 ("TH03 v7 table selector bound to the v6 profile", TF, "return _p.table_for_contract_version(_profiles.V7, version)", "return _p.table_for_contract_version(_profiles.V6_COMPAT, version)"),
 ("TH04 v7 decision bound to the v6 profile", TD, "return _decide.verify_and_decide(_profiles.V7,", "return _decide.verify_and_decide(_profiles.V6_COMPAT,"),
 ("TH05 v7 identity bound to the v6 profile", TI, "return _id.effective_policy_digest(_profiles.V7, family, payload, contract_version)", "return _id.effective_policy_digest(_profiles.V6_COMPAT, family, payload, contract_version)"),
 ("TH06 v7 identity default contract version", TI, "def effective_policy_digest(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION)", "def effective_policy_digest(family: Any, payload: Any, contract_version: Any = \"r08-v6\")"),
 ("TH07 v7 compose_for bound to the v6 profile", TF, "return _p.compose_for(_profiles.V7, version, caller, record, operator)", "return _p.compose_for(_profiles.V6_COMPAT, version, caller, record, operator)"),
 # --- signing / selection / record
 ("SE01 parser accepts any contract version", SE, "if type(version) is not str or version != profile.version:", "if type(version) is not str:"),
 ("SE02 signing input without the domain", SE, "return p.require_profile(profile).selection_signing_domain + c.canonical_bytes(statement)", "return c.canonical_bytes(statement)"),
 ("SE03 statement family unchecked", SE, "    if spec is None:\n        return \"family_unsupported\"\n", "    if spec is None:\n        return None\n"),
 ("SE04 evaluator binding unchecked", SE, "        if (ev[\"evaluator_id\"], ev[\"binding\"]) != spec.evaluator_binding:\n            return \"evaluator_unsupported\"\n", ""),
 ("SE05 withdrawal shape unchecked", SE, "        if stmt[\"record\"] is not None or stmt[\"evaluator\"] is not None or stmt[\"supersedes\"] is None:", "        if False:"),
 ("SE06 empty effective interval accepted", SE, "if start is None or end is None or not start < end:\n        return \"field_invalid\"\n    if c.parse_timestamp(stmt[\"issued_at\"])", "if start is None or end is None or start > end:\n        return \"field_invalid\"\n    if c.parse_timestamp(stmt[\"issued_at\"])"),
 ("SE07 unknown disposition accepted", SE, "    if disposition not in DISPOSITIONS:", "    if False:"),
 ("SE08 record_version zero accepted", SE, "1 <= pin[\"record_version\"] <= c.MAX_INT", "0 <= pin[\"record_version\"] <= c.MAX_INT"),
 ("SE09 statement digest not compared", SE, "    if c.digest(env[\"statement\"]) != env[\"statement_digest\"]:", "    if False:"),
 ("SE10 statement kind unchecked", SE, "    if stmt[\"kind\"] != \"selection\":", "    if False:"),
 ("SE11 parse accepts a foreign envelope kind", SE, "    if env[\"kind\"] != \"selection-envelope\":", "    if False:"),
 ("RE01 record accepts any contract version", RE, "if type(version) is not str or version != profile.version:", "if type(version) is not str:"),
 ("RE02 record family unchecked", RE, "        if spec is None:\n            return record_mod._refuse(\"family_unsupported\")\n", ""),
 ("RE03 supersession unchecked", RE, "        if not record_mod._supersession_ok(body):", "        if False:"),
 ("RE04 payload digest unchecked", RE, "        if body[\"payload_digest\"] != c.digest(body[\"payload\"]):", "        if False:"),
 ("RE05 record digest unchecked", RE, "        if body[\"record_digest\"] != c.digest({k: v for k, v in body.items() if k != \"record_digest\"}):", "        if False:"),
 ("RE06 record kind unchecked", RE, "        if body.get(\"kind\") != \"record\":", "        if False:"),
 # --- verification
 ("VE01 verifier accepts a foreign envelope version", VE, "or type(declared) is not str or declared != profile.version", "or type(declared) is not str"),
 ("VE02 revoked key not checked", VE, "elif key_id in trust[\"revoked_keys\"]:", "elif False:"),
 ("VE03 withdrawal not refused", VE, "mark(\"disposition\", \"selection_withdrawn\", \"the authenticated statement withdraws the selection\")", "mark(\"disposition\", None)"),
 ("VE04 expiry boundary inclusive", VE, "elif when >= end:", "elif when > end:"),
 ("VE05 not-yet-effective boundary exclusive", VE, "elif when < start:", "elif when <= start:"),
 ("VE06 epoch floor exclusive", VE, "floor is not None and epoch < floor", "floor is not None and epoch <= floor"),
 ("VE07 authority not enforced", VE, "None if authorized else \"issuer_not_authorized\"", "None"),
 ("VE08 operation mismatch ignored", VE, "elif statement.get(\"operation\") != context.operation:", "elif False:"),
 ("VE09 selection revocation ignored", VE, "revoked = (statement.get(\"selection_id\"), statement.get(\"epoch\")) in trust[\"revoked_selections\"]", "revoked = False"),
 ("VE10 key admission optional", VE, "mandatory = True  # key admission", "mandatory = False  # key admission"),
 ("VE11 trust expiry boundary inclusive", VE, "elif when >= trust[\"valid_until\"]:", "elif when > trust[\"valid_until\"]:"),
 ("VE12 consumer mismatch ignored", VE, "if statement.get(\"consumer_id\") != context.consumer_id:", "if False:"),
 ("VE13 verifier signs over a foreign domain", VE, "message = sel_e.signing_input(profile, statement)", "message = b\"ocs-reg/r08-v5/selection\\n\" + c.canonical_bytes(statement)"),
 ("VE14 verifier signs over the bare statement", VE, "message = sel_e.signing_input(profile, statement)", "message = c.canonical_bytes(statement)"),
 ("VE15 shape re-check of the private copy skipped", VE, "shape_code = \"field_invalid\" if \"disposition\" not in statement else sel_e.statement_code(profile, statement)", "shape_code = None"),
 ("VE16 scope mismatch ignored", VE, "            elif (scope.get(\"tenant\"), scope.get(\"institution\"), scope.get(\"authority_domain\")) != (", "            elif False and (scope.get(\"tenant\"), scope.get(\"institution\"), scope.get(\"authority_domain\")) != ("),
 ("VE17 digest integrity not checked", VE, "        if c.digest(statement) == selection.statement_digest:", "        if True:"),
 ("VE18 record binding skipped", VE, "            bad = v._record_binding(statement, record)\n            mark(\"record_binding\", *(bad if bad else (None,)))", "            pass"),
 ("VE19 verifier missing not refused", VE, "        if verifier is None:\n            mark(\"authenticity\", \"verifier_unavailable\"", "        if False:\n            mark(\"authenticity\", \"verifier_unavailable\""),
 ("VE20 non-canonical base64 tolerated", VE, "            raw = decode_canonical_base64(text)\n            if raw is None:", "            raw = decode_canonical_base64(text)\n            if False:"),
 # --- decision
 ("DE01 participation not compared", DE, "if getattr(report, \"participation\", None) != participation:", "if False:"),
 ("DE02 pinned record digest not compared", DE, "if getattr(report, \"bound_record_digest\", None) != recomputed:", "if False:"),
 ("DE03 binding layer not required", DE, "or layers.get(\"record_binding\") != \"pass\":", "or False:"),
 ("DE04 optional caller not normalized", DE, "            if normalized is not None:\n                break\n", "            pass\n"),
 ("DE05 failed report accepted", DE, "if getattr(report, \"ok\", False) is not True:\n            code", "if False:\n            code"),
 ("DE06 required refusal returns the caller", DE, "base = PolicyDecision(\"required_policy_unavailable\", None,", "base = PolicyDecision(\"required_policy_unavailable\", caller,"),
 ("DE07 record digest recompute skipped", DE, "if recomputed != body.get(\"record_digest\") or", "if False or"),
 ("DE08 compose with a version-less dispatch", DE, "result = p.compose_for(profile, profile.version, caller, record)", "result = p.compose(profile, caller, record)"),
 ("DE09 typed detail dropped", DE, "return _refusal(profile, participation, caller, code if code in CODES else \"selection_missing\", typed=typed)", "return _refusal(profile, participation, caller, code if code in CODES else \"selection_missing\")"),
 ("DE10 payload digest recompute skipped", DE, "or c.digest(body[\"payload\"]) != body.get(\"payload_digest\"):", "or False:"),
 ("DE11 applied_deny_all never reported", DE, "kind = \"applied_deny_all\" if result.deny_all else \"applied\"", "kind = \"applied\""),
 ("DE12 optional refusal flag", DE, "detail or \"optional overlay not applied; caller policy unchanged (not denial)\", True)", "detail or \"optional overlay not applied; caller policy unchanged (not denial)\", False)"),
 ("DE13 composer accepts a missing record", DE, "        if record is None:\n            return _refusal(profile, participation, caller, \"composition_record_invalid\", \"no record supplied\")\n", ""),
 # --- identity
 ("ID01 effective domain is the v5 prefix", ID, "return pid._sha(p.require_profile(profile).effective_policy_domain, preimage)", "return pid._sha(b\"ocs-reg/r08-v5/effective-policy\\n\", preimage)"),
 ("ID02 preimage omits contract_version", ID, "\"contract_version\": contract_version, \"family\": family,", "\"family\": family,"),
 ("ID03 preimage omits family", ID, "\"family\": family,\n            profile.identity", "\n            profile.identity"),
 ("ID04 preimage omits the version member", ID, "            profile.identity[family].version_member: version_value, \"deny_all\"", "            \"deny_all\""),
 ("ID05 preimage omits effective", ID, "\"deny_all\": [], \"effective\": plain_payload}", "\"deny_all\": [], \"effective\": {}}"),
 ("ID06 preimage names a constant revision", ID, "    return row.version_value\n", "    return 1\n"),
 ("ID07 scalar value domain not checked", ID, "        if not row.is_value(value):\n            pid._refuse(\"field_invalid\", field)\n", ""),
 ("ID08 class limit off by one", ID, "len(value) > pid.MAX_LIST_ENTRIES", "len(value) > pid.MAX_LIST_ENTRIES + 1"),
 ("ID09 deny_all non-empty in preimage", ID, "\"deny_all\": [], \"effective\": plain_payload}", "\"deny_all\": [\"x\"], \"effective\": plain_payload}"),
 ("ID10 other contract versions registered", ID, "    if contract_version != profile.version:\n        pid._refuse(\"contract_unsupported\", \"contract_version\")", "    if False:\n        pid._refuse(\"contract_unsupported\", \"contract_version\")"),
 ("ID11 class value domain not checked", ID, "            if not row.is_value(value[cls]):\n                pid._refuse(\"field_invalid\", field + \".\" + cls)\n", ""),
 ("ID12 empty class map accepted", ID, "if not value or len(value) > pid.MAX_LIST_ENTRIES or", "if len(value) > pid.MAX_LIST_ENTRIES or"),
 ("ID13 contract version type unchecked", ID, "    if type(contract_version) is not str:\n        pid._type_refusal(\"contract_version\", contract_version)\n", ""),
 ("ID14 default contract version is not the profile's", ID, "    if contract_version is DEFAULT:\n        contract_version = profile.version\n", "    if contract_version is DEFAULT:\n        contract_version = \"r08-v6\"\n"),
 ("ID15 class value type check dropped", ID, "            if type(value[cls]) is not str:\n                pid._type_refusal(field + \".\" + cls, value[cls])\n", ""),
 ("ID16 unknown member tolerated", ID, "    if unknown:\n        pid._refuse(\"field_unknown\", min(unknown))\n", ""),
 ("ID17 missing member tolerated", ID, "    if missing:\n        pid._refuse(\"field_missing\", min(missing))\n", ""),
 ("ID18 payload copy skipped (aliased input)", ID, "    d = pid._plain(payload)\n", "    d = payload\n"),
]
ONLY = [x for x in os.environ.get("MUT_ONLY", "").split(",") if x]
PY = os.environ.get("MUT_PY", sys.executable)
TESTS = sorted(str(p.relative_to(work)) for p in (work / "tests").glob("test_r08v7_*.py"))
def run():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    k = ["-k", os.environ["MUT_K"]] if os.environ.get("MUT_K") else []  # e.g. "not modulo and not carries_exactly" to deselect the source-parity tests
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
        status, detail = ("KILLED", (tail[0][:160] if tail else r.stdout.strip().splitlines()[-1][:160])) if r.returncode else ("SURVIVED", "v7 tests pass")
        log.append("=== %s [%s]\n%s\n" % (name, status, r.stdout[-1500:]))
    finally:
        F.write_text(orig)
    res.append((name, status, detail)); print(*res[-1], flush=True)
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / ("mutation-results-r08v7%s.json" % os.environ.get("MUT_SUFFIX", ""))).write_text(json.dumps({"tests": TESTS, "results": res}, indent=1))
(out_dir / ("mutation-raw-log-r08v7%s.txt" % os.environ.get("MUT_SUFFIX", ""))).write_text("\n".join(log))
print("TOTAL", len(res), "KILLED", sum(1 for x in res if x[1] == "KILLED"), "SURVIVED", [x[0] for x in res if x[1] == "SURVIVED"], "PATTERN", [x[0] for x in res if x[1].startswith("PATTERN")])
