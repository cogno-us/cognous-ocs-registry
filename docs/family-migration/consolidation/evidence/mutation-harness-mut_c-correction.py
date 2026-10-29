"""Mutation check of the NEW critical guards (registry_governed_lifecycle.py, registry_governed_policy.py).
Each mutant must be KILLED by tests/test_governed_policy_composition.py; a survivor is retried against the three family suites and reported as killed-by-other."""
import subprocess, sys, pathlib, shutil, json, os
S = "/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad"
src_root = pathlib.Path(sys.argv[1]); work = pathlib.Path(S) / "m12" / "mutroot_c"
if work.exists(): shutil.rmtree(work)
shutil.copytree(src_root, work, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
D = work / "src/agent_control_plane"
LC, PO = "registry_governed_lifecycle.py", "registry_governed_policy.py"
M = [
 ("L01 commit gate does not reverify", LC, '            self._gl_reverify("effect_commit", self._evaluation_time(_EXEC_NOW.get()))\n', '            pass\n'),
 ("L02 gate raises a plain error", LC, "raise DefinitiveDestinationRejection(self._gl_rejection_code) from None", "raise RuntimeError(self._gl_rejection_code) from None"),
 ("L03 gate does not record the refusal", LC, "            self._gl_last_commit_refusal = exc.refusal\n", ""),
 ("L04 no decision-entry revalidation", LC, '        self._gl_revalidate(proposal, "decision", self._evaluation_time(now))\n', ""),
 ("L05 no effect-entry revalidation", LC, '        self._gl_revalidate(proposal, "effect", entry_time)\n', ""),
 ("L06 proposal tenant not checked", LC, " or proposal.tenant_id != scope.tenant_id", ""),
 ("L07 proposal action not checked", LC, " or proposal.action_id != scope.action_id", ""),
 ("L08 held state not checked first", LC, "        code = self._gl_held_defect()\n        if code is not None:\n            raise self._gl_refuse(code, boundary)\n        authority = _declared_authority", "        authority = _declared_authority"),
 ("L09 held state not checked last", LC, "        code = self._gl_held_defect()  # LAST: nothing between this check and the caller's next step runs Registry source code\n        if code is not None:\n            raise self._gl_refuse(code, boundary)\n", ""),
 ("L10 manifest authority not rechecked", LC, '        if authority != self._gl_authority:\n            raise self._gl_refuse("manifest_authority_changed", boundary)\n', ""),
 ("L11 bound comparison dropped", LC, "        if new_bound != self._gl_bound:\n", "        if False:\n"),
 ("L12 gate ignores execute-entry time", LC, "self._evaluation_time(_EXEC_NOW.get())", "self._evaluation_time(None)"),
 ("L13 execute does not publish its time", LC, "        token = _EXEC_NOW.set(now)\n", "        token = _EXEC_NOW.set(None)\n"),
 ("L14 gated destination skips the gate", LC, '        object.__getattribute__(self, "_gate")()\n        return', "        return"),
 ("L15 gated destination re-wrap allowed", LC, "    if destination is None or isinstance(destination, _GatedDestination):\n", "    if destination is None:\n"),
 ("L16 naive construction time accepted", LC, "    if now.tzinfo is None or now.utcoffset() is None:\n", "    if False:\n"),
 ("L17 test clock honoured without allow_test_time", LC, 'construction_time if (bool(workflow_kwargs.get("allow_test_time")) and construction_time is not None)', "construction_time if (construction_time is not None)"),
 ("L18 source failure swallowed", LC, '        raise refuse("selection_source_failed", boundary) from None\n', "        return None\n"),
 ("L19 scope validity loosened", LC, "all(_text(getattr(scope, f))", "any(_text(getattr(scope, f))"),
 ("P01 F4 family not verified", PO, "    if families.f4_ages is not None:\n        values, digest, refusal = f4mod", "    if False:\n        values, digest, refusal = f4mod"),
 ("P02 class-age family not verified", PO, "    if families.class_age is not None:\n        derived, refusal = agemod", "    if False:\n        derived, refusal = agemod"),
 ("P03 unreadable family not verified", PO, "    if families.class_unreadable is not None:\n        derived_u, refusal", "    if False:\n        derived_u, refusal"),
 ("P04 class-age refusal swallowed", PO, '            return None, _prefixed("class_age", refusal)\n', "            pass\n"),
 ("P05 final composition not validated", PO, "    if defect is not None:\n        return None, Refusal(defect)\n", ""),
 ("P06 scalar widening not checked", PO, "    if final_scalars is not None and any(final_scalars[k] > host_scalars[k] for k in f4mod.AGES):\n        return \"composed_widens_host\"\n", ""),
 ("P07 age widening not checked", PO, 'cf["max_status_age_seconds"] > ch["max_status_age_seconds"] or ', ""),
 ("P08 unreadable widening not checked", PO, ' or unrmod._RANK[cf["on_unreadable"]] > unrmod._RANK[ch["on_unreadable"]]', ""),
 ("P09 foreign-field change not detected", PO, 'return None if dh == df else "composed_profile_invalid"', "return None"),
 ("P10 extension widening not checked", PO, '        if ff.get("max_age_extension_seconds", 0) > fh.get("max_age_extension_seconds", 0):\n            return "composed_widens_host"\n', ""),
 ("P11 final host-invariant check dropped", PO, '    if unrmod.host_class_defect(final) is not None:\n        return "composed_profile_invalid"\n', ""),
 ("P12 original-host defect not rechecked in final", PO, '    if unrmod.host_class_defect(host) is not None:  # defence in depth: the original host must already have been admissible; a composition never repairs it\n        return "host_class_invalid"\n', ""),
 ("P13 host validity precheck removed", PO, '            defect = unrmod.host_class_defect(host)  # ORIGINAL host validity FIRST: before any Registry call or source read\n            if defect is not None:\n                raise _refuse(defect, "construction")\n', ""),
 ("P14 scope mismatch accepted", PO, '        raise _refuse("family_scope_mismatch", "construction")', "        pass"),
 ("P15 empty declaration accepted", PO, '        raise _refuse("no_family_declared", "construction")', "        pass"),
 ("P16 profile not required for profile families", PO, '        raise _refuse("runtime_authority_profile_required", "construction")', "        pass"),
 ("P17 policy_binding accepted", PO, '            if profile_families and host.policy_binding is not None:\n                raise _refuse("policy_binding_unsupported", "construction")\n', ""),
 ("P18 scalar edits not detected", PO, '                return "scalars_modified"', "                return None"),
 ("P19 profile edits not detected", PO, '                return "profile_modified"', "                return None"),
 ("P20 ledger claim ignored", PO, " and not activation_ledger.claim(key, configuration)", " and False"),
 ("P21 ledger supersession ignored", PO, '            return "activation_superseded"', "            return None"),
 ("P22 bound identity omits unreadable", PO, '"class_unreadable": unreadable, "effective_profile_digest"', '"class_unreadable": None, "effective_profile_digest"'),
 ("P23 bound identity omits class age", PO, 'bound = {"f4_ages": scalars, "class_age": age_part,', 'bound = {"f4_ages": scalars, "class_age": None,'),
 ("P24 bound identity omits F4", PO, 'bound = {"f4_ages": scalars,', 'bound = {"f4_ages": None,'),
 ("P25 bound identity omits profile digest", PO, '"effective_profile_digest": pdigest}', '"effective_profile_digest": None}'),
 ("P26 only the first family is re-read", PO, "for name, fam in _declared(self._gp_families)}\n\n    def _gl_derive", "for name, fam in _declared(self._gp_families)[:1]}\n\n    def _gl_derive"),
 ("P27 composition order changed", PO, 'FAMILY_NAMES = ("f4_ages", "class_age", "class_unreadable")', 'FAMILY_NAMES = ("class_unreadable", "class_age", "f4_ages")'),
 ("P28 narrowed scalars not applied", PO, "status_max_age_seconds=scalars[0][f4mod.AGES[0]]", "status_max_age_seconds=status_max_age_seconds"),
 ("P29 host profile passed instead of the effective one", PO, '            extra["runtime_authority_profile"] = profile\n', '            extra["runtime_authority_profile"] = host\n'),
 ("P30 family prefix dropped", PO, 'Refusal(name + ":" + refusal.code,', "Refusal(refusal.code,"),
 ("P31 unreadable composed over the host not the age profile", PO, "base = unrmod.compose_unreadable(base, effective)", "base = unrmod.compose_unreadable(host, effective)"),
 ("P32 host scalar validity not required", PO, '        if families.f4_ages is not None and not (_scalar(status_max_age_seconds) and _scalar(approval_max_age_seconds)):\n            raise _refuse("host_scalar_invalid", "construction")\n', ""),
 ("C01 configuration identity omits the bound identity", PO, '"bound": bound})', '})'),
 ("C02 configuration identity omits the host values", PO, '"host": {"scalars": host_scalars if scalars is not None else None, "class_age": host_ages, "class_unreadable": host_values},\n', ""),
 ("C03 claim made before construction completes", PO, "        destination = take_destination(workflow_kwargs, _refuse)\n        extra = {}\n", "        destination = take_destination(workflow_kwargs, _refuse)\n        if activation_ledger is not None and not activation_ledger.claim(key, configuration):\n            raise _refuse(\"conflicting_governed_configuration\", \"construction\")\n        extra = {}\n"),
 ("C04 claim is not atomic (check then set, no lock)", PO, "        with self._lock:\n            held = self._claims.setdefault(key, configuration_id)\n            return held == configuration_id\n", "        held = self._claims.get(key)\n        if held is None:\n            self._claims[key] = configuration_id\n            held = configuration_id\n        return held == configuration_id\n"),
 ("C05 final claim result ignored", PO, "        if activation_ledger is not None and not activation_ledger.claim(key, configuration):\n            raise _refuse(\"conflicting_governed_configuration\", \"construction\")\n\n    @property\n    def governed_last_commit_refusal", "        if activation_ledger is not None:\n            activation_ledger.claim(key, configuration)\n\n    @property\n    def governed_last_commit_refusal"),
]
ONLY = [x for x in os.environ.get('MUT_ONLY', '').split(',') if x]
OUT = os.environ.get('MUT_OUT', 'mutation-results-cp-consolidation.json')
PY = f"{S}/venv-g1-212/bin/python"
def run(test, pin, extra_env=None):
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": f"{work}:{work}/src", "OCS_REGISTRY_PIN_DIR": f"{S}/m12/{pin}", "OCS_REQUIRE_REGISTRY_PIN": "1"}
    return subprocess.run([PY, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", test], cwd=work, capture_output=True, text=True, env=env)
res = []
for name, fn, a, b in M:
    if ONLY and name.split()[0] not in ONLY: continue
    F = D / fn; orig = F.read_text()
    if orig.count(a) != 1:
        res.append((name, "PATTERN COUNT %d" % orig.count(a), "")); print(res[-1], flush=True); continue
    F.write_text(orig.replace(a, b))
    try:
        r = run("tests/test_governed_policy_composition.py", "regpin_v5")
        tail = [l for l in r.stdout.splitlines() if l.startswith("FAILED") or l.startswith("ERROR")]
        if r.returncode:
            status, detail = "KILLED", (tail[0][:140] if tail else r.stdout.strip().splitlines()[-1][:140])
        else:
            status, detail = "SURVIVED", "composition tests pass"
            for t, pin in (("tests/test_f4_age_governance.py", "regpin"), ("tests/test_f5_class_age_governance.py", "regpin"), ("tests/test_f5_class_unreadable_governance.py", "regpin_v5")):
                r2 = run(t, pin)
                if r2.returncode:
                    status, detail = "KILLED-BY-OTHER", t; break
    finally:
        F.write_text(orig)
    res.append((name, status, detail)); print(*res[-1], flush=True)
json.dump(res, open(f"{S}/m12/ev_c/{OUT}", "w"), indent=1)
print("TOTAL", len(res), "KILLED", sum(1 for x in res if x[1].startswith("KILLED")), "SURVIVED", [x[0] for x in res if x[1] == "SURVIVED"], "PATTERN", [x[0] for x in res if x[1].startswith("PATTERN")])
