# G0 acceptance matrix (predeclaration)

G0 APPROVED / CLOSED on merge of PR #40; schedule per [Amendment 1](../decisions/2026-10-26-amendment-1-plan-v1.4-g0-schedule.md). Documentation only. **Nothing in this file has been run for the demonstration, and no proposed test has passed.** "Existing" means a test or vector that exists in a repository today and was developer-tested at its own scope; it is **not** independently qualified and is not evidence for the integrated profile. Every row's independent gate is open: Tier 1 NOT STARTED, no independent lead, no independent cryptographic reviewer. Profile: [MSOP-F1a-C11](g0-minimum-profile.md). Sprints: [plan v1.4](../plans/PROJECT_PLAN-v1.4.md) section 4 (NOT AUTHORIZED).

Legend. Gates: **S07** independent security assessment, **S08** independent Tier 1 oracle run. Status: **EXISTS-REF** a reference model or unit test exists but nothing binds it to the Runtime consumer; **MISSING** no test exists; **BLOCKED/NOT RUN** until its sprint. Kit = `registry_conformance/vectors` (EXT-S1-8, #28; the consumer under test is the kit's own reference model, not the Runtime). The kit-group mappings are candidate mappings, UNVERIFIED until S06 binds them.

## 1. ADR-REG-S4-0 acceptance rows AR-01..AR-27 (full set preserved; none dropped)

Source: [ADR section 11](../decisions/2026-10-26-adr-ext-s4-0-integration-contract.md). Evidence for every row: raw per-case output, exact pins, positive/negative verdict, evidence-stream entry. All rows apply to the profile except as noted.

| AR | Case | Existing | Missing | Sprint | Expected outcome |
|---|---|---|---|---|---|
| 01 | Forged binding (altered member, recomputed commitment, altered stored claim JSON) | Control Plane #84 commitment tests (no-binding path); kit GD | Claim-carried binding tests | S02, S05 | Refused under the lock |
| 02 | Substituted identity (each tuple member, foreign `activation_ref`) | Kit GD-02; #33 identity vectors | Runtime guard tests | S05 | `policy_identity_mismatch` REFUSE |
| 03 | Expired at the lock (clock read after lock) | Kit SN-04 (edge) | Runtime lock-time test | S05 | `selection_expired` REFUSE, no fallback |
| 04 | Revoked before and after the lock | Kit RV | Runtime test | S05 | Before: REFUSE. After commit: no rollback, disclosed |
| 05 | Stale epoch; row swapped between check and commit | Kit EP, CW | `_transaction_stage` race test | S05 | `selection_epoch_stale` REFUSE_STALE, no effect |
| 06 | Grant/approval mismatch (neither alone suffices) | CP approval-mismatch tests | Binding + guard test | S02, S05 | Refused |
| 07 | Change after authorization | Kit RV | Runtime test | S05 | Refused at commit |
| 08 | Restore/rollback: older store, ahead anchor, head mismatch | Kit RC | Durable-store test | S04, S06 | Store `unknown`, HOLD for every participation |
| 09 | Required-policy failure | Kit GD-03/04 | Runtime test | S05 | Never the caller policy |
| 10 | Ratchet downgrade by claim, selection, caller, restart, restore | Kit RT | Durable ratchet test | S04, S05 | `participation_mismatch`/HOLD; ratchet survives restart |
| 11 | Six-step approval revival (generation counter) | Control Plane #84 generation tests | End-to-end run | S06 | Old approval stays invalid; fresh one succeeds |
| 12 | Generation direction: behind vs ahead | CP generation tests | Runtime test | S05, S06 | REFUSE_STALE vs HOLD |
| 13 | Fallback bases (only the two positive bases admit) | Kit GD-05/06 | Runtime test | S05 | Per ADR 6.1 |
| 14 | Withdrawn disposition on a ratcheted scope | Kit RT, RV | S01 emitter, end-to-end | S01, S06 | Refused upstream, no authorizing profile |
| 15 | Unknown reason code, label, version or profile | #231 successor suite; kit PS | Runtime test | S05, S06 | HOLD, never success |
| 16 | Evidence write failure after refusal; crash after admitted fallback | none | Fault-injection tests | S05 | Refusal stands, `evidence_unavailable`; fallback evidence same transaction or no effect |
| 17 | Saturation (epoch, generation) | Kit EP | Runtime test | S04, S05 | Activate refuses; withdraw/revoke still work |
| 18 | Sequence gap, hash-chain break, orphan row, evidence truncation | Kit TM | Durable-store test | S04 | HOLD, store `unknown` |
| 19 | No registry call, socket or network I/O in a transaction | none | I/O-trap test | S05, S06 | Fails if any occurs |
| 20 | Legacy preimage for a scope with row/history/ratchet/unknown store | none | Binding test | S02, S05 | REFUSE |
| 21 | Single carried-ahead generation | none | Runtime test | S05 | HOLD for that decision; `store_state` unchanged |
| 22 | `activate`/`withdraw` under a different `selection_id` (lineage replacement) | Kit EP-06 | Durable test | S04, S05 | `selection_conflict`/`lineage_replacement_prohibited`; ratchet, high-water, revocation intact |
| 23 | Optional/no-binding claim via new `selection_id` over a ratcheted scope | Kit RT-01/02 | Runtime test | S05, S06 | Refused; ratchet survives |
| 24 | Log write with label/digest outside allow-list or null | none | Writer test | S04 | `field_invalid`; no entry; no default to 0.2 |
| 25 | Entry violating the nullability table | none | Schema/writer tests | S04 | Refused; closed 24-member schema |
| 26 | Recovery with no verified log copy / non-reproducing anchor / genesis with anchor | Kit RC | Recovery test | S04, S06 | Store stays `unknown`; nothing resets |
| 27 | Snapshot revokes a pair/key with no row, then that pair is activated | Kit SN, RV | Runtime test | S04, S05 | Revoke logged and replayable; activation refused |

Independent gate for all rows: S07 for rows touching verification, key custody, atomic guard and recovery (01-10, 15-20, 24-27); S08 for the full set at exact pins with an oracle authored independently of the builder.

## 2. Other batteries to reuse

| Battery | Existing | Use in profile | Missing | Sprint | Gate |
|---|---|---|---|---|---|
| EXT-S1-8 kit (#28) | `tests/test_conformance_kit.py` (25 tests), 11 vector files, 103 vectors | Bind to the Runtime consumer; expected verdicts ACCEPT / REFUSE / REFUSE_STALE / UNKNOWN | The binding adapter | S06 | S08 |
| EXT-S1-9 adversarial verifier cases | Partial: `test_r08_verify.py`, `test_core_security_mutants.py`, `test_core_security_sig_and_key_admission.py`, `test_adapter_ed25519_*.py` | Forged, altered, expired, wrong key | Replay across tenant/consumer/operation, wrong participation, unselected pin, below-floor and older snapshot hiding a revocation, **v1-signed replayed as v2** (see G0-GAP-4; S01 signing tests in Amendment 1 section 3) | S01 | S07, S08 |
| EXT-S1-5 identity vectors (#30, #33, #35) | `tests/test_ext_s1_5_vectors.py`, `docs/ext-implementation/data/ext-s1-5-policy-identity-vectors.json` | Effective-policy digest equality, differing per caller | Runtime computes the same digest | S03A, S05, S06 | S08 |
| Ed25519 and canonical base64 (#26, #34) | Adapter, CCTV (914 vectors), Wycheproof, security vectors, `test_r08_v2_canonical_base64_vectors.py` | Signature admission | Platform beyond Linux x86-64 CPython 3.11-3.13 | S07 | S07 (independent crypto reviewer) |
| Frozen S05 differential | `tests/s05_expectations.json`, `s05_oracle.py`, `docs/s05-results/` | Regression: narrowing is still intersection-only for the three sets | Do not re-run for G0; re-run only if code under it changes | S03/S06 | none (builder) |
| Stack Qualification #231 | `suites/reasons-successor` (172 codes, 164 preserved, substitution negatives) | Reasons-0.3 vocabulary pin | Re-pin at S03 heads | S03 | S08 |
| Unchanged no-binding claims | EXT-S2-1/S3-1 characterization (cards); FS-RT/FS-CP | Byte-identical control | Not yet written (EXT-S2-1 NOT STARTED) | S03 | S08 |
| Catalog scenarios C11, D02, C02, C01, D03 | `scenarios/catalog.json` all NOT RUN; known-limit tests assert limits, not protection | Scenario evidence rows | Execution against the integrated profile | S06 | S08 |

## 3. Security and qualification readiness (G0 task 6)

| Topic | Status | Concrete readiness action (no qualification is run here) |
|---|---|---|
| Independent Tier 1 lead | None designated (GAP-G4-13) | Operator names a lead before the S06 oracle freeze; lead is independent of the builder and Architect |
| Independent cryptographic review | None. #26 and #34 SECURITY-HELD; AI reviews recorded in `docs/adapters/ed25519.md` are not independent | Operator commissions a named human reviewer using the review package list in `docs/adapters/ed25519.md`; hold labels stay until a recorded result |
| CCTV vector licence | BSD-3-Clause directory licence retained with vectors; upstream author confirmation **not obtained**; Architect decision on scope pending (`tests/vectors/cctv/SOURCE.md`) | Decide: accept as is, obtain confirmation, or use the documented fetched-fixture fallback (`docs/adapters/ed25519.md`) |
| Synthetic keys | Test keys only; not operational trust, rotation or compromise handling | Keep exclusion explicit in every report; no key ceremony in scope |
| Anchor custody | ADR: external anchor, advanced after acknowledged heads; a restore between the last anchor update and the store head is undetectable; custody of the anchor by the Runtime host is an assumption, not a qualified control | State the anchor holder and update cadence at S04 predeclaration; S07 reviews it; no operational custody claim |
| SECURITY-HELD components | EXT-S1-7 adapter (#26), core verifier hardening (#34) | Lift only on a recorded independent result (S07) |
| Missing security-critical cases | (1) v1-signed replayed as v2 / v2 signing-domain separation (G0-GAP-4). (2) Replay across tenant, consumer, operation. (3) Older snapshot hiding a revocation. (4) Runtime I/O-in-transaction trap (AR-19). (5) Evidence-write fault injection (AR-16). (6) Platform and Python outside the tested scope (excluded). | Assign per section 2; items 1-3 to the Registry (S01/G0-GAP-2); 4-5 to S05 |
| Independence rule | Builder tests, CI and AI/Copilot review never count as independent (Constitution ADOPTION.md; plan section 5) | Keep "BUILDER-TESTED / AI-REVIEWED" wording; no qualification claim in any status |
