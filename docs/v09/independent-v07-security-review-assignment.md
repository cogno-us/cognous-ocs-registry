# Assignment A: independent V07 security review

Non-authorizing. Prepared by the Lead Builder for the Architect to issue. **No reviewer is designated by this document.** The builder performed no part of this review and must not.

## 1. Reviewer role required
An independent cryptographic and security reviewer, a human individual or body designated in writing by the Architect, who did not write, run or review the code or tests under review and who holds the authority to withhold a PASS. Plan v1.5 section 5 requires the independent cryptographic reviewer to be identified **before** the independent oracle is frozen. AI sessions, separate AI sessions and CI runs do not qualify (Constitution `ADOPTION.md` at `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`). The reviewer may use tools, but the verdict and the oracle are theirs.

## 2. Exact revisions (pin the SHAs, never branch names)
| Component | Pin |
|---|---|
| Registry (contracts, verifier, Ed25519 adapter) | `b695f67d944286c76100ddab36818f926958297f` (docs-only successor of `1a4de32605519c505142b1ba3a57fa5b259b0b2c`; contract blobs identical, see `candidate-manifest.json`) |
| Control Plane | `d66ae07fa240510efdcc11ed4b3e1189dcefc822` |
| Runtime | `b5605f525ae73cbb7adcfef4716c67cdd33a5f7d` |
| Stack Qualification | `bb9b08904192b5f50a49e00ed8de0cab80fd7c19` |
| Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` |
Historical pins for the F-01 record (do not review these as current): Registry `943ab183`, Runtime `4199a6c7` (breach); Registry `a1169a05`, Runtime `ac247daf` (remediation). Run `python tools/verify_v09_candidate.py --components-dir <clones>` first; it must print `OK`.

## 3. Scope
1. **Ed25519 and canonical base64**: `registry_adapters/ed25519_verifier.py`, `registry_successor/canonical_b64.py`, `registry_successor/key_admission.py`, `docs/adapters/ed25519.md`, `docs/core-security-canonical-signature-and-key-admission.md`, `requirements-ed25519*.txt`. The security-held changes **#26** (`51469cbe0642`, adapter) and **#34** (`06b9ab9568c8`, core verifier hardening) are in scope. The hold is lifted only by the Architect, never by this review's author or the builder.
2. **Binding and authorization provenance**: Control Plane `canonical_policy_binding.py`, claim issuance, `authorization_pin_export.py`; Runtime `engine/authorization_pin*.py`; Amendment 4.
3. **Runtime atomicity**: `engine/registry_selection_authority.py`, `engine/local_authority_effect.py` inside `execute_claim_atomic` (`BEGIN IMMEDIATE`), evidence atomicity.
4. **Registry authority containment**: Amendment 3 and the five-set narrowing; the F-01 historical breach (A08 at Runtime `4199a6c7`) and its remediation (Runtime `ac247daf`).
5. **Restore, replay and anti-rollback limits**: the hash-chained selection log, ratchet, anchor and snapshot expiry; the disclosed consistent-restore limit (L-08).

## 4. Contracts
`docs/r08-v2-contract.md` and Amendments 1-4; ADR EXT-S4-0 (`docs/decisions/2026-10-26-adr-ext-s4-0-integration-contract.md`); `docs/f-a1-authorization-pin/`; Plan v1.5. Blob SHAs are in `candidate-manifest.json`.

## 5. Oracle freeze procedure (what makes the assessment independent)
1. **Phase 1, contracts and source only.** The reviewer receives sections 2-4 and the repositories at the pins, and nothing from `results/` or the builder's inventories.
2. The reviewer writes an inventory and acceptance oracles from the contracts and source, **freezes them as an immutable commit or signed hash recorded with the Architect**, and only then
3. **Phase 2** receives the builder's evidence for cross-reading: Stack Qualification `results/v07-security/` (`THREAT_MODEL.md`, `INVENTORY.md`, `FINDINGS.md`, `historical_findings.json`, `requalification/REQUALIFICATION.md`, `local-runs/`), the V06 record `results/v06-e2e/`, and [evidence-index.md](evidence-index.md). Any gap between the frozen oracle and the builder's cases is reported, not backfilled.

## 6. Raw evidence the reviewer must keep
Their own raw runs (commands, environment, interpreter and library versions, stdout/stderr, exit codes), every failed or abandoned attack, and the frozen oracle commit. Nothing is discarded or overwritten.

## 7. Known limitations (do not re-find as new)
Register B and exclusions in [limitations-and-exclusions.md](limitations-and-exclusions.md), in particular: assessor of the existing V07 was the builder; Ed25519 soundness not assessed by anyone independent; synthetic keys only (X-02); CCTV vector-license status open (L-16); consistent database-plus-anchor restore undetected and anchor custody undemonstrated (L-08); `claim_json` not authenticated at lock time (L-05); pydantic 2.11.9 behaviour on the Runtime side untested (L-14); partial Python 3.11/3.12 coverage (L-17).

## 8. Mandatory failure reporting
Report every finding with severity (CRITICAL, HIGH, MEDIUM, LOW, QUALIFICATION GAP), exact pin, reproduction, expected versus observed, preconditions, and what was **not** demonstrated. A finding is reported even if it matches a known limitation, and the reviewer states which. Do not omit negative results. The reviewer's verdict must not be edited by the builder.

## 9. Verdict criteria (exact-pin, scoped)
- **PASS**: every in-scope mandatory case HELD or CHARACTERIZED-as-disclosed at the pins, with the reviewer's own raw evidence, and no open CRITICAL or HIGH finding.
- **BLOCK**: any CRITICAL or HIGH finding, any mandatory-invariant failure (signature acceptance of non-canonical or forged input, key admission bypass, authority or policy expansion, non-atomic effect or evidence, accepted rollback or replay beyond the disclosed limit), or a result the reviewer cannot reconcile with the contracts.
- **INCONCLUSIVE**: a mandatory case could not be run or its environment was invalid (missing library, missing facility, SKIP, environment error). INCONCLUSIVE is never PASS and never converted to PASS by a later builder run.
The verdict applies only to the stated pins and scope; it is not a release, publication or production clearance.

## 10. Standing holds
V09 formal acceptance: HELD. Ed25519 #26/#34: SECURITY-HELD. Release, Publication, Production: HOLD.
