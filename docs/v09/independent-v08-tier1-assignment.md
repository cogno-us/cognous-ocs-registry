# Assignment B: independent V08 Tier 1 qualification

Non-authorizing. Prepared by the Lead Builder for the Architect to issue. **No reviewer is designated by this document.** The builder performed no part of this qualification and must not.

## 1. Reviewer role required
An independent Tier 1 qualification lead (human, designated in writing by the Architect) with authority to withhold PASS, plus an independent oracle author (may be the same person). Neither may be the builder, a builder-directed AI worker or a CI workflow. Plan v1.5 requires an "independent lead and oracle" and a "exact-pin verdict with negative evidence". Independence cannot be inferred from a second automated process (Constitution `ADOPTION.md` at `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`).

## 2. Exact post-merge pins
| Component | Pin |
|---|---|
| Registry | `b695f67d944286c76100ddab36818f926958297f` (contract blobs identical to `1a4de326`) |
| Control Plane | `d66ae07fa240510efdcc11ed4b3e1189dcefc822` |
| Runtime | `b5605f525ae73cbb7adcfef4716c67cdd33a5f7d` |
| Stack Qualification | `bb9b08904192b5f50a49e00ed8de0cab80fd7c19` |
The builder's F-A1 qualification ran at Runtime `3873a61b` (tree identical to the pin above) and Control Plane `d66ae07f`; it did **not** run at the Runtime merge SHA, and `.github/workflows/tier1-v08-fa1.yml` has no post-merge run. The independent qualifier pins the SHAs above and runs there. `python tools/verify_v09_candidate.py --components-dir <clones>` must print `OK` first.

## 3. Scope
1. **End-to-end authorized operation identity**: persisted Control Plane decision to export, trusted installer, pin store, Runtime guard, Registry scope derived from the pin; supplier-controlled claim content cannot replace provenance.
2. **F-A1 historical breach and remediation**: operation substitution with a recomputed commitment (historical BREACH at Runtime `ac247daf`, record in #235 `7b72de9ac7e4898c0f9bdad3e9b337775cc9c543`, `results/v08-tier1/`), refused at the pins with zero effects.
3. **Pin-store custody and OS separation**: installer on a dedicated OS identity, executor read-only (`mode=ro`), host-only paths; the reviewer must use **real, distinct, non-root OS identities**. An in-process or mocked result is INCONCLUSIVE.
4. **Revocation and effect serialization**: per-decision fences; terminal transition only under the exclusive fence, never unfenced; receipt `pin_epoch` consistent with the serialized order.
5. **Pending-intent barrier**: durable intent blocks new governed effects for the covered decision only; no starvation of unrelated decisions; no reliance on `flock` fairness.
6. **Crash and restart recovery**: kill the installer at each point of the crash table in Amendment 4 (states A-H); mandatory reconcile; no fabricated commit.
7. **Evidence atomicity**: receipt or evidence-insert failure leaves zero committed effects and releases the fence.
8. **F-01 regressions**: five-set containment (units, adapters, actions, institutions, authority domains) beneath a valid pin; narrower and equal policies execute.
9. **Anchor and store integrity**: rollback of the store, anchor mismatch, anchor loss (HOLD); the consistent-restore case is a disclosed limit, to be characterized not passed.
10. **Negative-case and refusal evidence**: typed refusals only (`policy_identity_mismatch`, `store_unknown`, `verifier_unavailable` with `pin_*` causes), no legacy fallback on pin-required destinations.

## 4. Contracts
`docs/r08-v2-contract-amendment-4.md` (and Amendments 1-3, `r08-v2-contract.md`), `docs/f-a1-authorization-pin/implementation-proposal.md`, Runtime `docs/authorization-pin-interface-freeze.md`, `docs/authorization-pin-integration-record.md`, `docs/authorization-pin-f3-acceptance-record.md`, Plan v1.5.

## 5. Oracle freeze procedure
1. **Phase 1**: the qualifier receives sections 2-4 and the repositories at the pins, nothing from `results/` of the builder.
2. The qualifier writes the scenario inventory and oracles from the contracts and source, with acceptance conditions per scenario, and freezes them as an immutable commit recorded with the Architect.
3. **Phase 2**: only then receive the builder's evidence for comparison: Stack Qualification `results/v08-fa1/` (`results.json`, `ledger.jsonl`, `runs/run-001.json`, `README.md`), the builder's predeclared plan `docs/f-a1-authorization-pin/qualification-plan.md` (30 cases, FA1-01..FA1-29 including FA1-06b; **builder-authored, not an independent oracle**), the historical V08 evidence in #235, and [evidence-index.md](evidence-index.md). Differences are reported, not backfilled.

## 6. Raw evidence locations (builder side)
- Local record (preserved, not 30 PASS): `results/v08-fa1/` at `bb9b0890`: 30 executions, HELD 28, CHARACTERIZED 1 (FA1-12), INCONCLUSIVE 1 (FA1-13).
- CI: run 40555193111 (head `ed4f45a5`, all 30 gated green), 40537952077 (first success), 40537445066 (original failed gate, harness defect). Artifact `v08-fa1-evidence` of 40555193111 expires 2027-01-25 and should be archived by the Architect.
- Historical V08: #235 head `7b72de9a` `results/v08-tier1/INDEX.md` (BLOCK; F-A1 BREACH; 44 of 50 local executions; CI 38 cases, 37 PASS, 1 FAIL).
- The qualifier's own raw runs belong in their own evidence location, retained complete.

## 7. Known limitations (do not re-find as new)
[limitations-and-exclusions.md](limitations-and-exclusions.md): FA1-12 propagation delay (L-07); consistent restore of store and anchor undetected and anchor custody undemonstrated (L-08); the builder's OS-isolation evidence is from root on ephemeral hosts with throwaway users, and the installer is a single process (X-08); FA1-13 local INCONCLUSIVE (L-11); no post-merge F-A1 CI (L-10); Runtime wrappers still call reusable workflows at `1c1755ff` (L-09); open LOW items L-01 to L-06.

## 8. Mandatory failure reporting
Every failing, blocked, skipped, inconclusive or abandoned case is reported with its raw evidence. Stop conditions (report and halt the affected line, do not work around): failure of independent authorization provenance, OS writer isolation, exclusive-fence revocation ordering, pending-intent fail-closed behaviour, pin-derived operation identity, atomic effect-time verification, or F-01 containment. No degraded mode and no unfenced terminal commit may be tolerated or excused. Do not allowlist a BREACH.

## 9. Verdict criteria (exact-pin, scoped)
- **PASS**: every mandatory scenario HELD with the qualifier's raw evidence at the pins (disclosed limits CHARACTERIZED, not passed), real two-identity OS separation exercised, and no open CRITICAL or HIGH finding.
- **BLOCK**: any BREACH or mandatory-invariant failure, any unauthorized effect, an unfenced terminal commit, an operation executed that the persisted Control Plane decision did not authorize, or an F-01 regression.
- **INCONCLUSIVE**: a mandatory scenario could not run or the environment was invalid (no root or no real OS identities, SKIP, wrong pin, missing dependency). Never PASS; not convertible by a later builder run.
The verdict applies to the stated pins only. It is not a release, publication or production clearance.

## 10. Standing holds
V09 formal acceptance: HELD. Independent V08 Tier 1: NOT STARTED until the Architect designates the qualifier and the oracle is frozen. Ed25519 #26/#34: SECURITY-HELD. Release, Publication, Production: HOLD.
