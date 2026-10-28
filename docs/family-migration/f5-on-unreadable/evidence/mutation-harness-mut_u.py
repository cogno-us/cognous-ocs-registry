"""Mutation check for registry_f5_class_unreadable_governance.py: every mutant must be KILLED by tests/test_f5_class_unreadable_governance.py."""
import subprocess, sys, pathlib, shutil, json
S = "/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad".replace("4a7fc4b564f0","d850d4243c78") if False else "/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad"
src_root = pathlib.Path(sys.argv[1]); work = pathlib.Path(S) / "m12" / "mutroot_u"
if work.exists(): shutil.rmtree(work)
shutil.copytree(src_root, work, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
F = work / "src/agent_control_plane/registry_f5_class_unreadable_governance.py"
orig = F.read_text()
M = [
 ("M01 narrowing not applied (host value kept)", "        action[\"on_unreadable\"] = effective[action[\"class_id\"]]\n", "        pass\n"),
 ("M02 narrowing forced to refuse for every class", "        action[\"on_unreadable\"] = effective[action[\"class_id\"]]\n", "        action[\"on_unreadable\"] = \"refuse\"\n"),
 ("M03 widening to bounded_tolerance applied", "        action[\"on_unreadable\"] = effective[action[\"class_id\"]]\n", "        action[\"on_unreadable\"] = \"bounded_tolerance\"\n"),
 ("M04 order inverted (looser wins)", "    return a if _RANK[a] <= _RANK[b] else b\n", "    return a if _RANK[a] >= _RANK[b] else b\n"),
 ("M05 drop widening guard", "    if any(_RANK[effective[k]] > _RANK[host_values[k]] for k in host_values):\n        return None, Refusal(\"effective_policy_widens_host\", None, kind)\n", ""),
 ("M06 drop record-minimum cross-check", " or any(effective[k] != stricter(host_values[k], registry[k]) for k in registry)", ""),
 ("M07 drop unnamed-class host-value check", "    if any(k not in registry and effective[k] != host_values[k] for k in host_values):\n        return None, Refusal(\"effective_policy_invalid\", None, kind)\n", ""),
 ("M08 heal guard removed", "    if any(cl.irreversible and effective[cl.class_id] != cl.on_unreadable for cl in host.actions.values()):\n        return None, Refusal(\"registry_would_heal_invalid_class\", None, kind)\n", ""),
 ("M09 scoped class coverage not required", "    if scoped.class_id not in registry:\n        return None, Refusal(\"scoped_class_not_governed\", None, kind)\n", ""),
 ("M10 vocabulary check dropped on host", "        if type(cid) is not str or not cid or not _value(val):\n", "        if type(cid) is not str or not cid:\n"),
 ("M11 ambiguity not detected", "        if cid in values and values[cid] != val:\n            return None, \"class_unreadable_ambiguous\"\n", ""),
 ("M12 lax record parser (duplicate keys)", "object_pairs_hook=_strict_pairs, ", ""),
 ("M13 optional participation", "verify_and_decide_v5(\"required\"", "verify_and_decide_v5(\"optional\""),
 ("M14 deny_all ignored", " or decision.deny_all is not False", ""),
 ("M15 hold accepted as applied kind", "    if kind != \"applied\"", "    if False"),
 ("M16 verifier type not enforced", "    if type(verifier) is not verifier_cls:\n        return None, Refusal(\"verifier_not_admitted\")\n", ""),
 ("M17 operationally_authorized not required false", " or decision.operationally_authorized is not False", ""),
 ("M18 no profile-modified check (entry)", "        if type(held) is not RuntimeAuthorityProfile or profile_digest(held) != pdigest:\n            raise _refuse(\"profile_modified\", boundary)\n        authority = ", "        authority = "),
 ("M19 no profile-modified check (last)", "        held = self.runtime_authority_profile  # the held profile is re-checked LAST", "        return  # the held profile is re-checked LAST"),
 ("M20 drop all change comparisons", "        if new_effective != effective or new_digest != digest or new_age != age_part or profile_digest(new_profile) != pdigest:\n            raise _refuse(\"selection_changed\", boundary)\n", ""),
 ("M21 drop effective map comparison only", "new_effective != effective or ", ""),
 ("M22 drop policy digest comparison only", " or new_digest != digest", ""),
 ("M23 drop age part comparison only", " or new_age != age_part", ""),
 ("M24 drop final profile digest comparison only", " or profile_digest(new_profile) != pdigest:", ":"),
 ("M25 destination not gated", "destination=_GatedDestination(destination, self._fu_commit_gate)", "destination=destination"),
 ("M26 gate raises plain error", "            raise DefinitiveDestinationRejection(REJECTION_CODE) from None", "            raise RuntimeError(REJECTION_CODE) from None"),
 ("M27 no effect-entry check", "        self._fu_revalidate(proposal, \"effect\", entry_time)\n", ""),
 ("M28 no decision-entry check", "        self._fu_revalidate(proposal, \"decision\", self._evaluation_time(now))\n", ""),
 ("M29 policy_binding profile accepted", "        if host.policy_binding is not None:\n            raise _refuse(\"policy_binding_unsupported\", \"construction\")\n", ""),
 ("M30 proposal scope not checked", " or proposal.tenant_id != scope.tenant_id or proposal.action_id != scope.action_id", ""),
 ("M31 execute-entry clock ignored at gate", "self._evaluation_time(_EXEC_NOW.get())", "self._evaluation_time(None)"),
 ("M32 manifest authority not rechecked", "        if authority != self._fu_authority:\n            raise _refuse(\"manifest_authority_changed\", boundary)\n", ""),
 ("M33 age component dropped from joint derive", "    if age_scope is not None:\n        derived, refusal = derive_class_age(", "    if False:\n        derived, refusal = derive_class_age("),
 ("M34 age refusal swallowed", "            return None, Refusal(\"class_age:\" + refusal.code, refusal.registry_code, refusal.registry_kind)\n", "            pass\n"),
 ("M35 age scope mismatch accepted", "                raise _refuse(\"class_age_scope_mismatch\", \"construction\")\n", "                pass\n"),
 ("M36 half-configured age pair accepted", "        if (class_age_scope is None) != (class_age_selection_source is None):\n            raise _refuse(\"class_age_configuration_invalid\", \"construction\")\n", ""),
 ("M37 age source not consulted at boundaries", "        if self._fu_age_scope is not None:\n            try:\n                age_material = self._fu_age_source()", "        if False:\n            try:\n                age_material = self._fu_age_source()"),
 ("M38 gated destination re-wrapped allowed", "        if destination is None or isinstance(destination, _GatedDestination):\n", "        if destination is None:\n"),
 ("M39 unknown registry class not refused downstream", "    if registry is None or not set(registry) <= set(host_values) or", "    if registry is None or"),
 ("M41 host-validity precheck removed", "        defect = host_class_defect(host)  # host validity FIRST: before any Registry call or source read\n        if defect is not None:\n            raise _refuse(defect, \"construction\")\n", ""),
 ("M42 host-validity precheck ignores irreversibility", "    if any(cl.irreversible and cl.on_unreadable != \"refuse\" for cl in profile.actions.values()):", "    if any(cl.on_unreadable != \"refuse\" for cl in profile.actions.values()):"),
 ("M43 host-validity precheck inverted value", "    if any(cl.irreversible and cl.on_unreadable != \"refuse\" for cl in profile.actions.values()):", "    if any(cl.irreversible and cl.on_unreadable == \"refuse\" for cl in profile.actions.values()):"),
 ("M40 unreadable value composed before age (wrong base)", "        profile = compose_unreadable(base, effective)", "        profile = compose_unreadable(host, effective)"),
]
import os
ONLY = [x for x in os.environ.get('MUT_ONLY','').split(',') if x]
OUT = os.environ.get('MUT_OUT','mutation-results-cp.json')
res = []
for name, a, b in M:
    if ONLY and name.split()[0] not in ONLY:
        continue
    if orig.count(a) != 1:
        res.append((name, "PATTERN COUNT %d" % orig.count(a), "")); print(res[-1], flush=True); continue
    F.write_text(orig.replace(a, b))
    r = subprocess.run([f"{S}/venv-g1-212/bin/python", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests/test_f5_class_unreadable_governance.py"], cwd=work, capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin", "PYTHONPATH": f"{work}:{work}/src", "OCS_REGISTRY_PIN_DIR": f"{S}/m12/u_reg", "OCS_REQUIRE_REGISTRY_PIN": "1"})
    tail = [l for l in r.stdout.splitlines() if l.startswith("FAILED")]
    status = "KILLED" if r.returncode else "SURVIVED"
    res.append((name, status, tail[0][:130] if tail else r.stdout.strip().splitlines()[-1][:130]))
    print(*res[-1], flush=True)
F.write_text(orig)
json.dump(res, open(f"{S}/m12/ev5/{OUT}", "w"), indent=1)
print("TOTAL", len(res), "KILLED", sum(1 for x in res if x[1] == "KILLED"), "SURVIVED", [x[0] for x in res if x[1] == "SURVIVED"], "PATTERN", [x[0] for x in res if x[1].startswith("PATTERN")])
