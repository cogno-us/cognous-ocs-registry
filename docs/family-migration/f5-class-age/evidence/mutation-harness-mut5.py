"""Mutation check for registry_f5_class_age_governance.py: every mutant must be KILLED by tests/test_f5_class_age_governance.py (or be documented equivalent)."""
import subprocess, sys, pathlib, shutil, json
S = "/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad"
src_root = pathlib.Path(sys.argv[1]); work = pathlib.Path(S) / "m12" / "mutroot"
if work.exists(): shutil.rmtree(work)
shutil.copytree(src_root, work, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
F = work / "src/agent_control_plane/registry_f5_class_age_governance.py"
orig = F.read_text()
M = [
 ("M01 drop widening guard", "    if any(effective[k] > host_ages[k] for k in host_ages):\n        return None, Refusal(\"effective_policy_widens_host\", None, kind)\n", ""),
 ("M02 drop min cross-check", " or any(effective[k] != min(host_ages[k], registry[k]) for k in registry)", ""),
 ("M03 class age not applied", "        action[\"max_status_age_seconds\"] = effective[action[\"class_id\"]]\n", "        pass\n"),
 ("M04 wrong class used for every action", "        action[\"max_status_age_seconds\"] = effective[action[\"class_id\"]]\n", "        action[\"max_status_age_seconds\"] = min(effective.values())\n"),
 ("M05 extension limit not composed", "        freshness[\"max_age_extension_seconds\"] = min(freshness[\"max_age_extension_seconds\"], room)\n", "        pass\n"),
 ("M06 room measured from host not narrowed", "max(0, registry[cid] - effective[cid])", "max(0, registry[cid] - 0)"),
 ("M07 extension may exceed host limit", "min(freshness[\"max_age_extension_seconds\"], room)", "room"),
 ("M08 no profile-modified check", "        if type(held) is not RuntimeAuthorityProfile or profile_digest(held) != pdigest:\n            raise _refuse(\"profile_modified\", boundary)\n", ""),
 ("M09 drop all three change comparisons", "        if new_effective != effective or new_digest != digest or new_pdigest != pdigest:\n            raise _refuse(\"selection_changed\", boundary)\n", ""),
 ("M10 drop effective-profile digest comparison only", " or new_pdigest != pdigest", ""),
 ("M11 drop effective map comparison only", "new_effective != effective or ", ""),
 ("M12 drop policy digest comparison only", " or new_digest != digest", ""),
 ("M13 destination not gated", "destination=_GatedDestination(destination, self._f5_commit_gate)", "destination=destination"),
 ("M14 gate raises plain error", "            raise DefinitiveDestinationRejection(REJECTION_CODE) from None", "            raise RuntimeError(REJECTION_CODE) from None"),
 ("M15 no effect-entry check", "        self._f5_revalidate(proposal, \"effect\", entry_time)\n", ""),
 ("M16 no decision-entry check", "        self._f5_revalidate(proposal, \"decision\", self._evaluation_time(now))\n", ""),
 ("M17 scoped class coverage not required", "    if scoped.class_id not in registry:\n        return None, Refusal(\"scoped_class_not_governed\", None, kind)\n", ""),
 ("M18 policy_binding profile accepted", "    if host.policy_binding is not None:\n            raise _refuse(\"policy_binding_unsupported\", \"construction\")\n", ""),
 ("M19 proposal scope not checked", " or proposal.tenant_id != scope.tenant_id or proposal.action_id != scope.action_id", ""),
 ("M20 execute-entry clock ignored at gate", "self._evaluation_time(_EXEC_NOW.get())", "self._evaluation_time(None)"),
 ("M21 ambiguity not detected", "        if cid in ages and ages[cid] != age:\n            return None, \"class_age_ambiguous\"\n", ""),
 ("M22 manifest authority not rechecked", "        if authority != self._f5_authority:\n            raise _refuse(\"manifest_authority_changed\", boundary)\n", ""),
 ("M23 verifier type not enforced", "    if type(verifier) is not verifier_cls:\n        return None, Refusal(\"verifier_not_admitted\")\n", ""),
 ("M24 lax record parser", "object_pairs_hook=_strict_pairs, ", ""),
 ("M25 optional participation", "verify_and_decide_v2(\"required\"", "verify_and_decide_v2(\"optional\""),
 ("M26 deny_all ignored", " or decision.deny_all is not False", ""),
 ("M27 hold accepted as applied kind", "    if kind != \"applied\"", "    if False"),
]
res = []
for name, a, b in M:
    if orig.count(a) != 1:
        res.append((name, "PATTERN COUNT %d" % orig.count(a), "")); print(res[-1]); continue
    F.write_text(orig.replace(a, b))
    r = subprocess.run([f"{S}/venv-g1-212/bin/python", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests/test_f5_class_age_governance.py"], cwd=work, capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin", "PYTHONPATH": f"{work}:{work}/src", "OCS_REGISTRY_PIN_DIR": f"{S}/m12/regpin", "OCS_REQUIRE_REGISTRY_PIN": "1"})
    tail = [l for l in r.stdout.splitlines() if l.startswith("FAILED")]
    status = "KILLED" if r.returncode else "SURVIVED"
    res.append((name, status, tail[0][:120] if tail else r.stdout.strip().splitlines()[-1][:120]))
    print(*res[-1], flush=True)
F.write_text(orig)
json.dump(res, open(f"{S}/m12/ev/mutation-results.json", "w"), indent=1)
print("TOTAL", len(res), "KILLED", sum(1 for x in res if x[1] == "KILLED"), "SURVIVED", [x[0] for x in res if x[1] == "SURVIVED"], "PATTERN", [x[0] for x in res if x[1].startswith("PATTERN")])
