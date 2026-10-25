# Operator decision record — S04 preconditions P1-P3 and S04 authorization (2026-10-24)

- Decision date: 2026-10-24 (as issued by the operator). GitHub recording time: this file's first commit in the S04 PR; the decision was issued before it was recorded, and no retrospective approval date is claimed.
- Authority: Cognous operator (André de Lima), per OCS-REG-PLAN v1.1 change control.
- Source: operator message in the Claude Code S04 builder session on 2026-10-24: "adopt P1, P2, P3 as amended; authorize S04. I don't know what the pin is." That message followed (a) the Architect's S03 rulings and S04 architectural rulings (documents attached to the session, not repository originals) and (b) the operator's instruction "Use github copilot for independent reviews." This file is a builder transcription, not independently countersigned. The texts below are the Architect's proposed texts as adopted; where the operator amended P3, the amended text is used.
- Plan: https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.1.md (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`, unchanged). The plan heading "S04 ... PLANNED; NOT AUTHORIZED" is static plan text; authorization is carried by this decision, as for S02 (D5) and S03.
- Constitution (pinned): https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md (the Architect confirmed no successor pin).

## Adopted preconditions

### P1 — Authentication and trusted-host profile

Approve a bounded, non-production, trusted-host implementation in which candidate registry records and request inputs may be untrusted, but the approved selection identity, trusted execution configuration, installed Runtime source and verification code are outside the modeled attacker's control.

The modeled attacker may modify or submit candidate record bytes, including re-digesting modified records. They may not alter the approved selection manifest, its independently trusted pin, the canonical approved record, the trusted checkout, the installed Runtime source, or the trusted verifier-context configuration.

This profile excludes compromised host administrators, root, compromised interpreters, malicious trusted maintainers and attackers who control the trusted selection mechanism.

For this profile, repository review and exact-source commitments are acceptable authentication mechanisms only when the consumer independently verifies the approved record against a selection commitment obtained from the trusted execution configuration.

Do not introduce signatures, key management, dynamic discovery or production authentication infrastructure.

Do not claim that Git digests independently establish author identity or protect against modification of the trusted source.

### P2 — Manifest authority and context custody

Approve one immutable candidate-selection manifest containing:

- Exact record identity and version.
- Approved canonical record digest.
- Approved record source identity.
- Contract and registered evaluator identities.
- Runtime evaluator Git blob and SHA-256.
- Exact applicability and selected-version requirements.

The canonical manifest may be stored in the OCS Registry repository, but its authority must come from a separately attributable operator or authorized delegate decision.

The record cannot authorize itself. The trusted consumer must obtain the approved manifest identity independently of record input and verify the selected manifest bytes.

A manifest and record included in the same implementation PR do not become authorized solely because that PR was merged.

Reuse S01's exact source commitments. Derive verifier context from the trusted selected configuration and verified installed evaluator bytes.

`latest_known_version` means the version explicitly selected by the authorized manifest. It must never be derived from untrusted record metadata or directory enumeration.

### P3 — Independent Tier 1 assessment (as amended by the operator)

The Architect's proposed P3 text required a separately accountable independent qualification owner. The operator amended it as follows and adopted it:

> GitHub Copilot pull-request review (`copilot-pull-request-reviewer[bot]`) on the exact final PR head is the designated independent technical review for S04. The operator accepts this in place of a separately accountable qualification owner for S04 only. S04 PASS will be recorded as "Copilot-reviewed, not independently qualified." The builder will write the negative-case battery from the Architect's required list before implementation and will not certify its own Tier 1 migration. This exception does not extend to S05, release, publication or production, which still require an independent qualification owner.

The Architect's assessment coverage list remains the checklist for the review request: trust-boundary integrity and record tampering; manifest substitution and unauthorized version selection; Runtime source and applicability mismatch; registry refusal and fallback behavior; exact set intersection and non-widening; empty-intersection denial; preservation of baseline authorization, refusal and evidence semantics; negative controls and honest unsupported-profile treatment. The operator retains authority over final acceptance and any exception to reserved requirements.

### Limits

These preconditions do not authorize registry activation, publication or production deployment, or waive S05 behavioral-equivalence qualification. Release: HOLD. Publication: HOLD. Production: HOLD.

## Adopted S04 execution authorization

**Sprint:** S04 — first bounded rule-family migration, conditional on P1-P3 above (adopted). **Repository:** `cogno-us/cognous-ocs-registry`.

**Objective.** Implement one fixed, authenticated, repository-pinned registry overlay for three `LocalExecutionPolicy` fields: `allowed_units`, `allowed_adapters`, `allowed_actions`. The overlay must narrow the existing caller-constructed policy without changing mandatory enforcement logic.

**Single deliverable.** One small S04 implementation PR providing: (1) a minimal trusted selection-manifest format; (2) a bounded consumer that verifies approved manifest identity, record identity, record authenticity within the approved threat profile, evaluator source and applicability; (3) construction of an effective policy using intersection for exactly the three authorized fields; (4) observable registry `ACCEPT` and `REFUSE` dispositions; (5) focused tests for trust, refusal, non-widening and unchanged baseline behavior; (6) concise source provenance, limitations and acceptance evidence. No general-purpose registry platform is authorized.

**Allowed files.** New S04-specific files within `registry_consumer/`, `registry_records/` (one synthetic candidate record and its manifest, if needed), `tests/test_s04_*.py`, `docs/s04-implementation.md`, `docs/decisions/`, `docs/sprint-status.md`. Other narrowly necessary support files only when within the objective. Do not alter `baseline/execution-runtime/`. Do not change `registry_contract/validator.py` or its frozen S03 semantics merely to make an S04 candidate pass.

**Required semantics.** For each authorized field, `effective_allowed = caller_allowed ∩ registry_allowed`. An empty intersection is valid and means no value is permitted for that field. On registry REFUSE: apply no registry narrowing; preserve the caller-constructed policy unchanged; emit the refusal reason through the consumer's observable result; make no additional authorization or effect decision; never claim registry activation succeeded. The refusal-to-caller fallback is permitted only for this optional-overlay profile and must not become a general authorization fallback when registry participation is mandatory.

**Tests and review.** Build → Test → Fix → Retest → Commit. Required negative cases: candidate record modified and re-digested; incorrect approved record digest; unauthorized manifest replacement; incorrect selected version; wrong Runtime source identity; wrong evaluator binding; invalid or unsupported record; missing approved selection; missing or malformed verifier context; registry values exceeding caller permissions; disjoint allowed sets; empty allowed sets; refusal preserving the original policy; unexpected consumer exception producing no unauthorized narrowing or successful activation claim. One integration owner; target 1-3 working days, maximum 5. Request GitHub Copilot review and repair material findings.

**Merge conditions.** Standing builder autonomy to repair, retest, request review and merge eligible PRs, only after: (1) all applicable developer checks pass; (2) Copilot's material findings are resolved; (3) the review required by P3 as amended is complete with an acceptable scoped disposition; (4) source, selection and acceptance evidence is bound to the exact final PR head; (5) no unauthorized behavior change, authority expansion or weakening of protected invariants; (6) the actual GitHub actor has merge authority. Record the exact merge SHA and S04 PASS/BLOCKED disposition. Do not represent a successful developer test or Copilot review as independent qualification.

**Exclusions.** No dynamic registry activation, general record store, administrative API, tenant routing, expiry, signing infrastructure, policy scripting, alternative evaluator, new authorization authority, historical catalogue import or production deployment. No modification to amount/effect ceilings, target matching, institution or authority-domain restrictions, approval/grant logic or effect-time enforcement. The 32 unresolved S02 classifications and the 60-versus-300 observation relationship stay unresolved.

**S05 boundary.** S04 completion does not establish behavioral equivalence. Record representable and unrepresentable historical policy classes (empty allow-lists, excluded characters, oversized lists and oversized entries). Stop after S04; S05 is not authorized. Release, publication and production remain on HOLD.

## Builder interpretation: the trusted selection pin (recorded, not an expansion)

The operator does not know what the pin is, and none exists in the repository. The Architect requires the authoritative pin to be held outside the record-controlled source tree and the manifest bytes to be identified by immutable content digest or exact repository commit plus path, established independently of the untrusted record.

The builder reads this authorization as follows. S04 delivers the verification mechanism, in which the pin is the SHA-256 of the exact manifest bytes, supplied to the consumer by trusted configuration at invocation, never read from the record, the manifest or the repository. S04 also delivers one synthetic candidate manifest and record as test fixtures, and reports the candidate manifest digest. That digest is not an approved pin. P2 states that a manifest and record merged in the same implementation PR are not authorized by the merge. Approving any manifest digest for use is therefore a separate, later operator decision that S04 does not make and does not need. Until then nothing consumes the overlay: the consumer is not wired into Runtime, and no record is activated.

## Conditions applied by the builder

Real GitHub Copilot review of the complete current PR on the exact head, attributable to `copilot-pull-request-reviewer[bot]`; material findings repaired and tests rerun; no CI added; merge bound to the exact verified head; scope remains S04; stop at S05. This supersedes nothing else and does not extend merge authority beyond S04.
