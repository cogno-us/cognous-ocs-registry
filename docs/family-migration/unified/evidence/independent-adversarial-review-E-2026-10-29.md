# Independent adversarial review E: Registry r08-v7 unified engine + Control Plane irreversibility/effective-policy

Registry b73c59e vs 42a6663; Control Plane 78cabe7 vs a62ca8d. No repo file edited. Probes: m12/probeE/{reg_probes.py,reg2.py,reg3.py,reg4.py,test_cp_probes.py,test_compat_base.py}.

## Verdict
No critical/high finding. No stop condition triggered (no active authority widening, no protected evaluator change, no approval-binding change).

## Mechanical checks
- Registry: `git diff --diff-filter=MDR` shows ONE modified file, tests/test_ext_s1_5_identity_module.py (allow-list extended with the 12 new module paths). No v1..v6 source/docs/vector/test file changed; a loop over every tracked r08-v1..v6, v1_..v6_, registry_adapters and core registry_successor/(verify|record|selection|common|decision) path shows no diff. r08-v1..v6 byte-identical.
- engine/verify.py vs v6_verify.py: after normalising names (sed) the ONLY differences are the profile parameter, `profile.version`, `sel_e.signing_input(profile, ..)`, `sel_e.statement_code(profile, ..)`, `p.require_profile`. Same layer order, same codes, same mandatory key admission, same withdraw handling, same final `ok` expression. engine/selection.py statement_code / _parse equal v6_selection except the profile lookups. engine/record.py equals v6_record. engine/decide.py equals v6_decision except profile tables.
- Control Plane evaluators bounded.py, runtime_authority.py, freshness.py, policy_binding.py, rule_revision.py, reversibility.py, holder_inventory.py: `git diff --stat` empty (byte-identical). Only src files changed: registry_effective_policy.py (new), registry_irreversibility_governance.py (new), registry_governed_policy.py (edited).
- Only readers of ActionClass.irreversible in src: bounded.py:2111 (class invalid if irreversible and on_unreadable != refuse), reversibility.py:186 -> bounded.py:2189 (cached tolerance, needs bounded_tolerance). A flip can only add refusals; confirmed by grep.
- Pinned tests: `tests/test_irreversibility_governance.py` -> 140 passed, 0 skipped (OCS_REQUIRE_REGISTRY_PIN=1, pin r7_reg b73c59e). The 5-file CI set -> 575 passed, 0 skipped (gate is `n >= 575`, zero headroom; see I-3).

## Probe outcomes (could not break unless stated)
Registry (reg_probes.py, 90 checks; the 4 printed "FINDING" lines were harness artefacts, re-verified: `ctx or default`, str-subclass JSON-dumps to plain str, `r.dumps` sorts keys, and object.__setattr__ on a frozen dataclass):
R1 v7 statement signed under v6/v5/v2/v1/no/effective-policy/no-newline domain: all `signature_invalid`. Reverse (v6 statement signed with v7 domain) refused by frozen v6 and by engine V6_COMPAT.
R2 envelope contract r08-v6/v5/v2/R08-V7/"r08-v7 "/v8/""/None/7: all `contract_unsupported`. Record contract_version variants refused. Parsed v6 selection fed to the V7 verifier and parsed v7 selection fed to frozen v6 verifier: `contract_unsupported`. str-subclass with always-equal `__eq__` as envelope contract: refused (`type(..) is str`).
R3 family confusion (v6 families in v7, trailing space, case, unreadable family, irr family under V6_COMPAT): `family_unsupported`.
R4 withdrawal: signed withdraw -> `selection_withdrawn`, ok False even with a record passed; optional+withdraw -> overlay_not_applied with caller unchanged; withdraw carrying a record pin refused at parse; disposition Select/SELECT/"withdraw "/""/None/1/list refused.
R5 record binding: stale digests, other sealed payload, version bump, id swap, evaluator swap, duplicate JSON key, unsorted raw class keys (`field_invalid`), NaN/1.0/1e2: all refused.
R6 key revoked, selection revoked, epoch floor, trust expiry at now==valid_until, effective at now==valid_until, naive/str now, wrong consumer/tenant/operation/ctx object, wrong key: refused with v6 codes.
R7 composition: `no_change` never lowers a caller `irreversible`; unknown Registry class, bool/int/None/"reversible"/upper-case values, unsorted keys, bool/subclass/empty/star caller maps: refused (`composition_record_invalid` / `composition_caller_invalid`).
R8 identity: contract r08-v6 -> `contract_unsupported`; V6 profile with irr family -> `family_unsupported`; preimage carries int `family_schema_revision` and no `family_version`.
R9 profile construction: v7 version with v6 selection domain rejected; V7.families immutable (MappingProxyType).
R10 differential fuzz engine(V6_COMPAT) vs frozen v6: 3000 mutated selection envelopes (random path set to junk/None/big int/other version/delete, with/without digest repair, trust None/revoked, now None/expired), 2000 mutated records, 1500 trust-snapshot/floor mutations, and a 1760-case participation x caller x selection x record x trust matrix incl. `optional`: 0 mismatches (equal decisions, reports, types).
Control Plane (test_cp_probes.py, 70 test items, all intended assertions hold except the notes below):
C1 4x3 matrix of host flag x Registry value (x optional T2): effective flag >= host flag everywhere; dump equal to host except `irreversible`; no other profile member changes (a).
C2 forged Registry results (lower T2, drop class, invent class, extra key, "irreversible "): every one refused (`effective_policy_widens_host` / `_invalid`).
C3 host classes with reversible_until, reversible_at_cost, bounded_tolerance: named `irreversible_flip_conflict:<cause>`; reads_protected_data / counterparty_observable=false are already irreversible by the model validator so the flip is a no-op, never a repair (b).
C4 host bounded_tolerance + Registry unreadable family that would narrow to refuse, alone or with class_age, f4, terminal, assurance declared: always `irreversible_flip_conflict:on_unreadable_not_refuse`; unreadable narrowing cannot hide the host defect (b).
C5 shared class_id: mixed on_unreadable across actions of one class -> conflict (every action of the class is checked); flag mismatch -> `class_irreversible_ambiguous` even with Registry no_change, before any source read; an unnamed defective class is untouched, naming it with `irreversible` -> conflict (c).
C6 replacement/revocation/untrusted/garbage material injected at source call 2 (decision), 3 (execute entry), 4 (commit gate): decision/execute raise; commit gate returns a failed attempt; effects stayed `{}` in all 15 cases (d).
C8/compat: same six pre-existing configurations built on a62ca8d (Registry 42a6663) and on 78cabe7 (Registry b73c59e): `configuration_digest` and `effective_profile_digest` identical in all six. Only change: the identity dict gains the key `class_irreversible: None` (and host.class_irreversible) (d).
C9 snapshot: all attributes frozen (FrozenInstanceError), families/scope/effective are tuples-only, no list/dict/set inside, identity_digest stable, mutating the returned identity dict does not affect it (f).
C10 resolve_effective_policy: missing material, None material, revoked family, revoked other family -> RegistryGovernedPolicyRefused (no partial); invalid host -> refused `host_class_invalid` (final check); lying host_irreversible map on a bounded_tolerance class -> `composed_profile_invalid`; omitting host_irreversible -> TypeError (fail closed, but not the refusal type) (f).
C12 Registry unavailable -> `registry_unavailable`, no fallback; Ed25519Verifier subclass -> `verifier_not_admitted`; v6 contract / v6 domain / v5 / participation optional -> `registry_not_applied`.
C13 ledger: a configuration with vs without the irr family cannot share the key (`conflicting_governed_configuration`); C14 superseded ledger blocks decision; C15 swapping the host profile back in at execute -> refused, no effect.

## Findings
### L-1 (low) resolve_effective_policy snapshot refs are read after, and separately from, the verified material
src/agent_control_plane/registry_effective_policy.py:142 `materials.get(name)` is read again (selection_ref) after derive_policy read `materials[name]`. A Mapping that returns another material on a later read yields a snapshot whose `selection_id`/`epoch` ("sel-evil-1", 99 in probe test_c10d) are not those of the selection that was verified (sel-test-1, 1). The effective value/digest are still the verified ones. Needs a hostile/mutable `materials` mapping supplied by the host itself; the snapshot is non-authorizing and read by no evaluator. Fix: read each material once and reuse it. Not a stop condition.

### L-2 (low) Engine exposes a public decide_verified that trusts a caller-supplied report
registry_successor/engine/decide.py:47. Predecessors kept this private (`_decide_verified` in decision.py:80, v3..v6_decision). With a duck-typed report (`ok=True`, `participation`, `layers={"record_binding":"pass"}`, `bound_record_digest` = digest of a validated record) probe reg3.py gets `applied` with no signature verification. Not reachable from the Control Plane (calls only verify_and_decide_v7 and pins the verifier type), and verify_selection's verifier is caller-supplied by design in every version. Suggest renaming with an underscore or documenting it as an internal. Not a stop condition.

### L-3 (low) final_composition_defect re-checks only one of the flip causes
registry_governed_policy.py:149-150. In the final-composition defence in depth only `on_unreadable != refuse` is re-evaluated. A forged final that flips a host class with `reversibility=reversible_until` (built with model_copy, bypassing validators) returns None from `final_composition_defect(..., irreversible_declared=True)` (probe test_c11); likewise a flip of any class cannot be tied to the classes the Registry named (the function does not know them). In the real path this is closed by (i) derive_irreversible/flip_conflict (host-based, runs first) and (ii) `compose_irreversible` using `model_validate`, whose flag/reversibility mismatch validator rejects the flip -> `effective_profile_invalid`. So the gap is defence-in-depth only. Not a stop condition.

### L-4 (low/info) Replacement selection with same effective value but other selection id/epoch (assessment of question g)
Confirmed: construction with {T1:IRR}; replacing at the decision boundary with {T1:IRR,T2:NC} under selection_id sel-other-9 epoch 77 is accepted and the execute succeeds; also accepted with a LOWER epoch (5 -> 1). The comparison at every boundary is `new_bound != self._gl_bound` (registry_governed_lifecycle.py:201); `bound` holds effective values and the Registry effective-policy digest, not selection id/epoch/record. The existing unreadable family behaves identically (probe test_c7b: authorized with another id/epoch). Authority assessment: not an authority risk. Every replacement is still fully Registry-verified at that boundary (signature, trust, scope, time, key and selection revocation, epoch floor), the effective value is equal, hence the effective RuntimeAuthorityProfile and approval_commitment are byte-identical; a replacement that changes any value is refused `selection_changed`. The residual is accountability, not authority: the snapshot (constructed once, `_gp_snapshot`) keeps reporting the construction-time selection id/epoch (sel-test-1/1) after a later boundary accepted a different selection, and epoch can regress to the extent the Registry trust floor allows. The authors' claim is accurate. Suggest documenting that the snapshot is construction-time only.

### I-1 (info) identity dict shape changed for existing configurations
`registry_governed_policy_identity` now always contains `class_irreversible` (None when undeclared) and `host.class_irreversible`. Digests are unchanged (verified above), but a consumer comparing the whole identity dict across versions will see a diff.

### I-2 (info) resolve_effective_policy skips construction-time host checks
It runs derive_policy only, so host_values / host_irreversible are caller-supplied rather than derived. Probes show the final composition check still refuses an invalid host and a lying host map, so it never returned a weaker or looser snapshot; the missing-parameter case raises TypeError, not RegistryGovernedPolicyRefused.

### I-3 (info) CI wording and gate
.github/workflows/tests.yml comment still says the pin is a 40-zero PLACEHOLDER and tests/test_f5_class_unreadable_governance.py:26 PIN_V7 comment says PLACEHOLDER, but both carry the real SHA b73c59e (verified by `rev-parse` step). The junit gate `n >= 575` equals the observed 575 exactly, so removing any test fails CI (intended, but fragile).

### I-4 (info) by-design/trust boundaries
Verifier object is caller-supplied (duck-typed verifier returning True verifies anything: reg_probes P7); same for v6. A frozen ContractProfile can be mutated with object.__setattr__ and a caller can build a custom ContractProfile (version r08-v7 + v7 domains + v6 tables constructs); profiles are trusted code inputs, not hostile input. engine.verify_selection / decide raise TypeError for a non-ContractProfile (documented programming error).

## Answers
Registry: every check, ordering and refusal code of v6_verify is preserved (normalised diff + 7000+ differential cases, 0 mismatches); no input made V7 or V6_COMPAT accept where v6/v7 must refuse (domain, version, family, withdrawal, record binding, scope/trust/time/epoch, key revocation).
(a) No: effective = stricter(host, registry) per class, derive_irreversible re-checks equality against that rule, rejects any lowering/extra/missing class, compose_irreversible only sets true, final_composition_defect rejects true->false and any non-governed member difference.
(b) Never repaired: flip needs host reversibility/reversible_until/reversal_cost None, host on_unreadable == refuse (host value, not composed), others default; tested host-vs-composed (C4).
(c) Covered (C5).
(d) All four boundaries re-derive through _gl_derive (construction, decision, execute entry, commit gate); configuration identity includes bound.class_irreversible and host_class_irreversible; compat digests identical.
(e) Identical.
(f) Immutable; resolve never returns a partial/weaker policy (raises); see L-1, I-2.
(g) See L-4.
