# Operator decision record: R08-S01 authorization (2026-10-24)

- Decision date: 2026-10-24 (as issued by the operator). Recorded in the R08-S01 PR; the decision was issued before it was recorded.
- Authority: Cognous operator (André de Lima).
- Source: the operator's instruction "R08-S01 IMPLEMENTATION AUTHORIZATION" (attachment `84b26530-attachment.txt` to the builder session). Quoted text is verbatim.
- Governing: plan v1.2 https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.2.md (blob `32319775c6e2d9c3fff1e2171c8f4c9d096911d6`); crosswalk https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.2-REVIEW-CROSSWALK.md; Constitution pin https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md (ADOPTION.md states that publication, reference or merge does not by itself establish adoption; formal adoption is not asserted); merged historical inventory `docs/historical-recovery`; merged rule-family analysis `docs/registry-schema-analysis`; merged R08 preparation `docs/r08-preparation` (merge `1324bab15da20a32fb82f54c444d1e808543b0e6`). Frozen: `registry_contract/`, `registry_consumer/`, `registry_records/`, `baseline/`. Read: `docs/s03-contract.md`, `docs/s04-implementation.md`, `docs/trust-limitations.md`, `docs/source-provenance.md`.

## Operator decision

- "I authorize R08-S01: SUCCESSOR CONTRACT AND AUTHENTICATED-SELECTION VERIFICATION FOUNDATION." "I also adopt F1a as the TARGET Minimum Supported Operational Profile (MSOP) for the initial OCS Registry. This is a scope decision, not operational acceptance." "Do not claim the full MSOP is complete."
- A parallel READ-ONLY R10 feasibility investigation is authorized. "No R09 operational custody or R10 implementation is authorized."
- Scope: new, separately versioned successor modules; s03-v1 and s04-v1 not modified; F1a fields `allowed_units`, `allowed_actions`, `allowed_adapters` only; explicit deny-all; selection statement; verification foundation against explicit trusted inputs (no invented trust roots, no production signing key, explicit refusal where absent); F1a intersection composition; authentication reuse assessment (no fourth cryptographic implementation); frozen candidate qualification specification (no self-certification of independent qualification); developer tests; one draft PR; at most one Copilot review.
- Not authorized: R09 operational custody; R10 integration implementation; F1b migration; GCR consumer; independent Tier 1 qualification (not yet performed; lead not designated); release, publication, production (HOLD); activation of any record or selection; approval of any pin; modification of the Runtime, Control Plane, ISS Core, the adopted plan or the qualification repository.
- Stop condition: "Stop after publishing the draft PR and handoff." Do not merge, activate or advance to another sprint without further operator authorization.

## Builder notes (recorded, not an expansion)

- Interface specification written before the modules: `docs/r08-s01-contract.md`. One lead builder owns integration; parallel lanes owned disjoint files.
- Parameters the operator left open, resolved conservatively and recorded as candidates in the contract: an F1a payload field that is absent refuses (typed semantics; neither implicit allow nor deny); perpetual selections are not representable (A-05 still open); no `status` field (event-derived lifecycle per the Architect ruling); selection signature is Ed25519 over a domain-separated canonical statement, verified only through an injected verifier (none is supplied).
