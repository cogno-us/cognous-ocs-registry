"""Mutation check of the r08-v6 critical guards. Usage: python mut_r6.py <repo_root> <out_dir>
Copies the repo to a temp root, applies ONE string mutation at a time to a v6 module, runs the v6 test files, records KILLED/SURVIVED.
Frozen files (verify.py, families.py, ...) are not mutated: they are protected by the byte-identity baseline test. BUILDER_TESTED developer evidence."""
import json, os, pathlib, shutil, subprocess, sys, tempfile
src_root, out_dir = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
work = pathlib.Path(tempfile.mkdtemp(prefix="mut_r6_"))
shutil.rmtree(work); shutil.copytree(src_root, work, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
D = work / "registry_successor"
RA, TR, FA, ID, SE, VE, DE, RE = ("v6_class_revocation_assurance.py", "v6_terminal_revocation.py", "v6_families.py", "v6_policy_identity.py",
                                  "v6_selection.py", "v6_verify.py", "v6_decision.py", "v6_record.py")
M = [
 # --- family 1: class revocation assurance
 ("RA01 order inverted", RA, "_RANK = {REQUIRED: 0, NOT_REQUIRED: 1}", "_RANK = {REQUIRED: 1, NOT_REQUIRED: 0}"),
 ("RA02 stricter picks the looser", RA, "return a if _RANK[a] <= _RANK[b] else b", "return a if _RANK[a] >= _RANK[b] else b"),
 ("RA03 is_value accepts str subclass", RA, "return type(v) is str and v in _RANK", "return isinstance(v, str) and v in _RANK"),
 ("RA04 payload sort check dropped", RA, " or names != sorted(names)", ""),
 ("RA05 class limit off by one", RA, "if not m or len(m) > MAX_CLASSES:\n        return \"field_invalid\"", "if not m or len(m) > MAX_CLASSES + 1:\n        return \"field_invalid\""),
 ("RA06 empty class map accepted", RA, "    if not m or len(m) > MAX_CLASSES:\n        return \"field_invalid\"", "    if len(m) > MAX_CLASSES:\n        return \"field_invalid\""),
 ("RA07 unknown registry class accepted", RA, "if set(reg) - set(base):", "if False:"),
 ("RA08 caller value domain not checked", RA, " or not all(is_value(v) for v in m.values()):\n        return None\n    return {F5RA_FIELD", ":\n        return None\n    return {F5RA_FIELD"),
 ("RA09 empty caller map accepted", RA, "if m is None or not m:", "if m is None:"),
 ("RA10 not-narrowing reported on equal values", RA, "if k in base and _RANK[reg[k]] > _RANK[base[k]]]", "if k in base and _RANK[reg[k]] >= _RANK[base[k]]]"),
 ("RA11 family not checked in composer", RA, "if type(family_seen) is not str or family_seen != FAMILY_F5RA:", "if type(family_seen) is not str:"),
 ("RA12 payload str-subclass value accepted", RA, "or not all(type(v) is str for v in m.values()):", "or not all(isinstance(v, str) for v in m.values()):"),
 ("RA13 operator not checked", RA, "if type(operator) is not str or operator != \"intersection\":", "if False:"),
 ("RA14 registry overrides caller (widening)", RA, "eff = {k: (stricter(base[k], reg[k]) if k in reg else base[k]) for k in base}", "eff = {k: (reg[k] if k in reg else base[k]) for k in base}"),
 ("RA15 deny_all set", RA, "{F5RA_FIELD: eff}, False, ())", "{F5RA_FIELD: eff}, True, (F5RA_FIELD,))"),
 ("RA16 record ok flag truthy accepted", RA, "if getattr(record, \"ok\", False) is not True:", "if not getattr(record, \"ok\", False):"),
 ("RA17 payload type before value order lost", RA, "    if not all(type(k) is str for k in m) or not all(type(v) is str for v in m.values()):\n        return \"field_type_invalid\"\n", ""),
 ("RA18 caller class tokens unchecked", RA, "    if not all(frozen_token_valid(k) for k in m) or not all(is_value(v) for v in m.values()):\n        return None", "    if not all(is_value(v) for v in m.values()):\n        return None"),
 ("RA19 caller class map unsorted/aliased not copied", RA, "return {F5RA_FIELD: {k: m[k] for k in sorted(m)}}", "return {F5RA_FIELD: snap[F5RA_FIELD]}"),
 # --- family 2: terminal revocation
 ("TR01 order inverted", TR, "_RANK = {ON: 0, OFF: 1}", "_RANK = {ON: 1, OFF: 0}"),
 ("TR02 stricter picks the looser", TR, "return a if _RANK[a] <= _RANK[b] else b", "return a if _RANK[a] >= _RANK[b] else b"),
 ("TR03 either-side-on lost (registry wins)", TR, "eff = stricter(base, reg)", "eff = reg"),
 ("TR04 either-side-on lost (caller wins)", TR, "eff = stricter(base, reg)", "eff = base"),
 ("TR05 not-narrowing reported on equal values", TR, "if _RANK[reg] > _RANK[base] else \"\"", "if _RANK[reg] >= _RANK[base] else \"\""),
 ("TR06 not-narrowing never reported", TR, "if _RANK[reg] > _RANK[base] else \"\"", "if False else \"\""),
 ("TR07 is_value accepts str subclass", TR, "return type(v) is str and v in _RANK", "return isinstance(v, str) and v in _RANK"),
 ("TR08 payload type check dropped", TR, "    if type(value) is not str:\n        return \"field_type_invalid\"\n", ""),
 ("TR09 caller value domain not checked", TR, " or not is_value(snap[TR_FIELD]):", ":"),
 ("TR10 family not checked in composer", TR, "if type(family_seen) is not str or family_seen != FAMILY_TR:", "if type(family_seen) is not str:"),
 ("TR11 deny_all set", TR, "{TR_FIELD: eff}, False, ())", "{TR_FIELD: eff}, True, (TR_FIELD,))"),
 ("TR12 operator not checked", TR, "if type(operator) is not str or operator != \"intersection\":", "if False:"),
 ("TR13 invalid caller replaced by default", TR, "    if cal is None:\n            return _refuse(\"composition_caller_invalid\")", "    if cal is None:\n            cal = {TR_FIELD: OFF}"),
 ("TR14 caller extra key tolerated", TR, "if snap is None or set(snap) != set(TR_FIELDS) or", "if snap is None or TR_FIELD not in snap or"),
 ("TR15 payload extra key tolerated", TR, "    if keys - set(TR_FIELDS):\n        return \"field_unknown\"\n", ""),
 ("TR16 record ok flag truthy accepted", TR, "if getattr(record, \"ok\", False) is not True:", "if not getattr(record, \"ok\", False):"),
 # --- table and dispatch
 ("FA01 lookup accepts non-exact str", FA, "    if type(family) is not str:\n        return None\n    try:\n        return FAMILIES_V6.get", "    try:\n        return FAMILIES_V6.get"),
 ("FA02 table selector accepts str subclass", FA, "if type(version) is str and version == CONTRACT_V6:", "if version == CONTRACT_V6:"),
 ("FA03 dispatch always the first family", FA, "return spec.composer(caller, record, operator)", "return ra.compose_f5ra(caller, record, operator)"),
 ("FA04 dispatch always the second family", FA, "return spec.composer(caller, record, operator)", "return tr.compose_tr(caller, record, operator)"),
 ("FA05 compose_for ignores contract version", FA, "    if not table_for_contract_version_v6(version).ok:\n        return _refuse(\"contract_unsupported\")\n", ""),
 ("FA06 unknown family composes", FA, "    if spec is None:\n            return _refuse(\"composition_family_unsupported\")\n", ""),
 ("FA07 table contract constant changed", FA, "CONTRACT_V6 = \"r08-v6\"", "CONTRACT_V6 = \"r08-v5\""),
 # --- identity
 ("ID01 effective domain is the v5 prefix", ID, "b\"ocs-reg/r08-v6/effective-policy\\n\"", "b\"ocs-reg/r08-v5/effective-policy\\n\""),
 ("ID02 preimage omits contract_version", ID, "\"contract_version\": contract_version, \"family\": family,", "\"family\": family,"),
 ("ID03 preimage omits family", ID, "\"family\": family, \"family_version\": version,", "\"family_version\": version,"),
 ("ID04 preimage omits family_version", ID, "\"family\": family, \"family_version\": version,", "\"family\": family,"),
 ("ID05 preimage omits effective", ID, "\"deny_all\": [], \"effective\": plain_payload}", "\"deny_all\": [], \"effective\": {}}"),
 ("ID06 family version tag v5", ID, "FAMILY_VERSION = \"v6\"", "FAMILY_VERSION = \"v5\""),
 ("ID07 scalar value domain not checked", ID, "        if not tr.is_value(value):\n            pid._refuse(\"field_invalid\", field)\n", ""),
 ("ID08 class limit off by one", ID, "len(value) > pid.MAX_LIST_ENTRIES", "len(value) > pid.MAX_LIST_ENTRIES + 1"),
 ("ID09 deny_all non-empty in preimage", ID, "\"deny_all\": [], \"effective\": plain_payload}", "\"deny_all\": [\"x\"], \"effective\": plain_payload}"),
 ("ID10 older contract versions registered", ID, "REGISTERED_CONTRACT_VERSIONS = (CONTRACT_VERSION,)", "REGISTERED_CONTRACT_VERSIONS = (CONTRACT_VERSION, \"r08-v5\")"),
 ("ID11 class value domain not checked", ID, "            if not ra.is_value(value[cls]):\n                pid._refuse(\"field_invalid\", field + \".\" + cls)\n", ""),
 ("ID12 empty class map accepted", ID, "if not value or len(value) > pid.MAX_LIST_ENTRIES or", "if len(value) > pid.MAX_LIST_ENTRIES or"),
 # --- signing / selection / verify / record / decision
 ("SE01 signing domain is the v5 prefix", SE, "SIGNING_DOMAIN_V6 = b\"ocs-reg/r08-v6/selection\\n\"", "SIGNING_DOMAIN_V6 = b\"ocs-reg/r08-v5/selection\\n\""),
 ("SE02 parser accepts any contract version", SE, "if type(version) is not str or version != V6_CONTRACT:", "if type(version) is not str:"),
 ("SE03 statement family unchecked", SE, "    if spec is None:\n        return \"family_unsupported\"\n", "    if spec is None:\n        return None\n"),
 ("SE04 evaluator binding unchecked", SE, "        if (ev[\"evaluator_id\"], ev[\"binding\"]) != spec.evaluator_binding:\n            return \"evaluator_unsupported\"\n", ""),
 ("RE01 record accepts any contract version", RE, "if type(version) is not str or version != v6_families.CONTRACT_V6:", "if type(version) is not str:"),
 ("RE02 record family unchecked", RE, "    if spec is None:\n            return record_mod._refuse(\"family_unsupported\")\n", ""),
 ("VE01 verifier accepts a foreign envelope version", VE, "or type(declared) is not str or declared != V6_CONTRACT", "or type(declared) is not str"),
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
 ("VE13 signature domain of the verifier is the v5 one", VE, "message = v6_sel.signing_input_v6(statement)", "message = v6_sel.signing_input_v6(statement)[:0] + b\"ocs-reg/r08-v5/selection\\n\" + c.canonical_bytes(statement)"),
 ("DE01 participation not compared", DE, "if getattr(report, \"participation\", None) != participation:", "if False:"),
 ("DE02 pinned record digest not compared", DE, "if getattr(report, \"bound_record_digest\", None) != recomputed:", "if False:"),
 ("DE03 binding layer not required", DE, "or layers.get(\"record_binding\") != \"pass\":", "or False:"),
 ("DE04 optional caller not normalized", DE, "            if normalized is not None:\n                break\n", "            pass\n"),
 ("DE05 withdrawn/failed report accepted", DE, "if getattr(report, \"ok\", False) is not True:\n            code", "if False:\n            code"),
 ("DE06 required refusal returns the caller", DE, "base = PolicyDecision(\"required_policy_unavailable\", None,", "base = PolicyDecision(\"required_policy_unavailable\", caller,"),
 ("DE07 record digest recompute skipped", DE, "if recomputed != body.get(\"record_digest\") or", "if False or"),
]
ONLY = [x for x in os.environ.get("MUT_ONLY", "").split(",") if x]
PY = os.environ.get("MUT_PY", sys.executable)
TESTS = sorted(str(p.relative_to(work)) for p in (work / "tests").glob("test_r08v6_*.py"))
def run():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([PY, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"] + TESTS, cwd=work, capture_output=True, text=True, env=env)
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
        status, detail = ("KILLED", (tail[0][:160] if tail else r.stdout.strip().splitlines()[-1][:160])) if r.returncode else ("SURVIVED", "v6 tests pass")
        log.append("=== %s [%s]\n%s\n" % (name, status, r.stdout[-1500:]))
    finally:
        F.write_text(orig)
    res.append((name, status, detail)); print(*res[-1], flush=True)
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "mutation-results-r08v6.json").write_text(json.dumps({"tests": TESTS, "results": res}, indent=1))
(out_dir / "mutation-raw-log-r08v6.txt").write_text("\n".join(log))
print("TOTAL", len(res), "KILLED", sum(1 for x in res if x[1] == "KILLED"), "SURVIVED", [x[0] for x in res if x[1] == "SURVIVED"], "PATTERN", [x[0] for x in res if x[1].startswith("PATTERN")])
