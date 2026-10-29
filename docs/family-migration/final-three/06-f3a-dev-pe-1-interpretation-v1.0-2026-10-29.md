# OCS-F3A-DEV-PE-1-INTERPRETATION/1.0 — successor clarification of read-only versus effecting refusal semantics (F3-A)

Status: **PROPOSED successor clarification (documentation only).** Takes effect only on recorded Architect adoption (section 9). It does **not** amend, edit or retroactively reinterpret the frozen qualification oracle (`03-f3-qualification-expectations-F3A-F3B-2026-10-29.md`) or the frozen contract (`02-architect-authorization-and-contract-freeze-2026-10-29.md`), and it does **not** convert the original F3-A FAIL into a PASS. Written by the Lead Builder (implementation owner). The Lead Builder issues no qualification verdict and does not self-certify (CA23).
Work package: OCS-F3A-DEV-PE-1-REMEDIATION · Archetype C · Tier T3 (documentation-only; see `08-ci-scope-declaration-dev-pe-1-2026-10-29.md`).

## 0. Exact source identities
| Subject | Identity |
|---|---|
| Control Plane integrated candidate (the code every statement below is bound to) | `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (merge of #97) |
| Registry migration closeout (this PR's base) | `2815643c3e15fbc6aadadbf88dc7596f10120992` |
| Frozen qualification oracle / contract (unaltered) | this directory, `03-…` and `02-…` at the base above |
| Independent qualification protocol (permanent predecessor evidence) | `PROTOCOL-F3-v1.md`, sha256 `e799b1083743526648a0c1c23d2c1455c0533ac843d88f3fe977dfd6a3850135`, frozen in qualification evidence commit `e08b5c2` before any candidate execution |
| Independent qualification evidence | commit `ed31764` of the qualifier's local evidence repository; delivered bundle `F3-qualification-evidence-ed31764.tar.gz`, sha256 `1d07a70439625de3b3e85e0ea3c088a43f14bc237649487d22d85da51a174fc5`; verdict report `VERDICTS-F3-20261029.md`, sha256 `57546d2b3fd390d905a731ee7904660fa06f42128aaeae68593a0677a8342cb1`. **No published GitHub location exists** (verified: neither commit is an object in either repository; the qualifier's push request was denied). This record does not invent one; the location is an open item for the Architect and the independent qualifier (section 8). |
| Constitution | `cogno-us/cognous-engineering-constitution` `dcdbe3b76843d672ca3cfb1f000124ecd78ed03c` (named by the directive). Normative articles are byte-identical to `230c0af` (used by the final-three work package). The OCS project adoption records pin `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; equality with that revision was not checked. No adoption is changed here. |
| Original verdicts (permanent) | F3-A: **FAIL — DEV-PE-1** (74 pass / 23 fail in the final run). F3-B: **PASS**, scoped. |

## 1. Historical literal wording (quoted, not altered)
* Frozen oracle `03`, line 23, F3-A expectation 1: "every member perturbed independently (…) changes the digest and makes execute AND pin-export refuse with `authorization_binding_changed` and a durable `EffectTimeRefusal`; the destination is untouched."
* Frozen contract `02`, section 4 rule 2 (line 52): "Execute and pin-export claim recompute the live member and compare. … unequal to the live value: refuse `authorization_binding_changed`." Section 2 row D-06.6 (line 31): "Reuse the registered `authorization_binding_changed` (durable `EffectTimeRefusal`). No new durable reason code." — the parenthesis qualifies the **reused code**, not a per-path obligation.
* Control Plane `docs/effective-configuration-binding.md` line 101 ("REFUSE, durable `EffectTimeRefusal`; execute and pin-export both") versus line 113 of the same file ("On the pin-export path the result is not `active` and carries no payload").

## 2. The conflict with read-only interface semantics, and its source
`authorization_pin_export.py` is documented as a read-only, non-authorizing assessment (module docstring lines 14-15; `docs/authorization-pin-export.md` lines 5 and 9-13: states `active`, terminal, `unknown`). Its mismatch outcome is `_unknown(...)`: state `unknown`, payload `None` (`authorization_pin_export.py:181-188`). It never calls `append_refusal` and constructs no `EffectTimeRefusal`; only `bounded.py:1694` (the effecting `execute` path) appends one. Claim issuance (`local_authority_effect.py:443-466`; refusal at 454-458) raises the existing `PermissionError("authorization-critical inputs changed before claim issuance")` and likewise writes none.
Chronology (git): the pin-export module and its doc were written on 2026-10-27 (`0fd44d0`) and are unchanged through `739efe7`. The Registry oracle and contract (`930dd3e`) were committed on 2026-10-29 10:06 UTC — two days **after** the read-only design — and the builder documentation line 101 (`2693e4d`, 10:36 UTC) repeated the oracle's wording. The discrepancy therefore arose when oracle text written for the effecting path was applied literally to two interfaces that were already, and remain, read-only. The independent qualifier observed exactly this (state `unknown`, payload `None`, no refusal row, destination untouched) and, under its frozen strict reading, recorded DEV-PE-1.

## 3. Architect-approved interpretation (verbatim intent)
A. **Effecting execution paths:** a configuration-binding mismatch must refuse the effect and produce the prescribed durable `EffectTimeRefusal` with `authorization_binding_changed`.
B. **Read-only assessment and pin-export paths:** a binding mismatch must fail closed, suppress the authorization payload and return the documented non-authorizing assessment outcome. Read-only interfaces must not acquire persistent write authority merely to manufacture an effect-time refusal record.
C. **Claim issuance:** a binding mismatch must prevent claim issuance and report the existing documented failure outcome. Claim issuance does not automatically acquire the effect-time journal-writing obligation.

## 4. Rationale (CA05, CA18, CA21)
* **CA05 — fail closed without inventing policy.** The clarification adds no policy, default or reason: every mismatch still produces no pin payload, no claim and no effect. Requiring a refusal row from a read-only interface would instead *invent* a write obligation.
* **CA18 — protected invariants.** No protected evaluator, approval commitment, signature domain, reason vocabulary or persisted schema is touched; `authorization_binding_changed` remains a typed-only registered reason (`schemas/runtime_authority_reasons_0_1…0_3.json`). Making the read-only paths write a refusal would require widening what they may persist.
* **CA21 — boundary commitments.** The behavior stated in section 5 is the behavior shipped since `0fd44d0` and observed by the qualifier. A search of the Control Plane docs, schemas, conformance material and Registry contracts found no relied-upon interface that treats pin-export as effecting, requires durable pin-export refusal evidence, or requires an `authorization_binding_changed` token on pin-export or claim (search commands recorded in `07-…`, section 3). The clarification therefore resolves an ambiguity; it does not modify a relied-upon external commitment. Were such an interface found, the stop condition in the directive (section 9 of the assignment) would apply and a compatibility transition would be required.

## 5. Required behavior per interface (at Control Plane `739efe7`; behavior unchanged by this record)
| Interface | On a configuration-binding mismatch | Source |
|---|---|---|
| **EXECUTE** (effecting) | Refuse; append a durable `EffectTimeRefusal` with reason `authorization_binding_changed`; raise the existing `PermissionError("authorization-critical inputs changed before effect")`; create no attempt row; do not touch the destination. | `bounded.py:1690-1711`; first `append_attempt` and `destination.apply` come after the raise |
| **PIN-EXPORT** (`assess_authorization_pin`, read-only assessment) | Fail closed: state is not `active` (observed `unknown`), payload `None`, reason text naming the unsupported authority; **no `EffectTimeRefusal` is written, no attempt row, no authorization-state write**; the destination is untouched. Existing resolution-check journaling (one `ResolutionCheck` row, stage `claim`, and input-time-floor bookkeeping via `_record_check`) is pre-existing, documented, and **unchanged** — this clarification does not describe pin-export as "writing nothing". | `authorization_pin_export.py:168-195`; `bounded.py:627-661` |
| **CLAIM ISSUANCE** | No claim is issued; the existing `PermissionError("authorization-critical inputs changed before claim issuance")` is raised; **no `EffectTimeRefusal` and no effect-time journal write is made or required**; the destination is untouched. | `local_authority_effect.py:443-466` |
The machine-readable `authorization_binding_changed` token is therefore an obligation of the effecting path (A) only; read-only and claim paths report it, if at all, in human-readable reason text.

## 6. What has not changed
Production code and every protected evaluator; `approval_commitment`, `catalogue_digest`, persisted schemas and published JSON schemas; signature domains; the reason vocabulary (no new code); the execute-path refusal requirement and its evidence; the legacy-compatibility, `legacy_cutoff`, unsigned-store and no-anti-rollback statements; the masked-host limitation text recorded in the companion Control Plane documentation PR; all other F3-A expectations (2-9) and all F3-B expectations; the frozen protocol's pass criteria; every standing hold. DEF-OBS-TOL-OVERFLOW-1 remains open and separate.

## 7. Qualification implications
* The original F3-A **FAIL stands** as permanent predecessor evidence, including all 23 failed assertions (22 × `test_A19_pin_export_refuses_per_perturbed_member[<member>-pin-export]`, each failing `reason_names_code` and `durable_effect_time_refusal`, plus `test_A06_frozen_legacy_store_cutoff_semantics`, sub-case `pin:cutoff0_idx0`) and all raw logs. Nothing in this record relabels, rescales or reinterprets them.
* This interpretation can support a **new** verdict only through independent readjudication by a fresh qualifier, against both the original literal wording and this successor, under its own exact protocol (`07-f3a-readjudication-handoff-2026-10-29.md`). The Lead Builder does not instruct, and this record does not imply, any particular outcome. Unresolved actual defects, if any, are not excused by this clarification.
* F3-B is not reopened.

## 8. Effective point, predecessor relationship, documentation corrections
* Predecessors: `03` (frozen oracle), `02` (frozen contract), qualification protocol `PROTOCOL-F3-v1.md` — all unaltered and remaining the record of what applied when they were frozen (ADOPTION.md: historical evidence is not retroactively recertified).
* Effective point: on recorded Architect adoption of this record, for interpretation of the D-06 contract from that point and for any readjudication that expressly adopts it. It is not retroactive to the frozen protocol.
* Companion documentation corrections (current docs corrected in place; historical records receive errata/successor notes, never in-place rewrites) are in a separate docs-only Control Plane PR. Errata for the Lead Builder's own unmerged PR #79 (annex A, `docs/post-migration/annex/A-f3-source-binding-and-coverage-map-developer-record.md`, line 58): the phrase "`fb24ed0` (not on main)" is incorrect — `fb24ed0` is an ancestor of Control Plane `739efe7` via the #97 branch history (not on main's first-parent line); to be applied as a new commit on that PR's branch, without history rewrite.
* Registry `docs/r08-v8-contract.md`: a post-integration note below line 3 records that the Control Plane consumers merged in Control Plane #97 (`739efe7`); the contract text itself is unchanged.

## 9. Project-specific adoption
Adopting authority: the Architect (ADOPTION.md; human approval alone is insufficient without valid authority and context). Required before this record governs: a recorded Architect decision identifying this exact document revision. This record does not select a constitutional revision (dcdbe3b / 230c0af / 1c2e920 remain as they were; #79 decision D7 is open). It does not alter any existing adoption.

## 10. Decisions requested of the Architect
1. Adopt, amend or reject this record (section 9).
2. Confirm the precise wording of B: "read-only" here means no authorization-state write and no effect-time refusal write; the existing `ResolutionCheck` journaling stays. If a stricter meaning is intended, that is a behavior change outside this record's authority.
3. Reconcile or retire the sentence in `03` line 23 by a new Registry decision record (this record does not edit it).
4. Designate a fresh independent qualifier and the evidence location for the readjudication (section 8 of `07-…`).
