# R1-E — Registry Ergonomics and Private-Preview Integration Addendum v1.0

**Status:** PROPOSED STATIC PLAN AMENDMENT, NON-AUTHORIZING.  
**Parent:** `docs/plans/REGISTRY-R1-POST19-CONSOLIDATION-PLAN-v1.0.md` (merged Registry PR #73).  
**Downstream:** `docs/plans/OCS-P1-POST-R1-PRIVATE-PREVIEW-PLAN-v1.0.md` (merged Registry PR #74).  
**Owner repo:** `cogno-us/cognous-open-control-stack-ergonomics`.  
**Governing:** Engineering Constitution and ADOPTION.md at `cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; Registry Static Migration Plan v1.1 §12; Engineering Plan v1.5; audits/architecture PRs #60/#65/#67/#68/#72.

## 1. Source-backed reason for R1-E

The Ergonomics repository README describes a `0.1.0-draft` non-authorizing user-facing `cognous-ocs` CLI with offline synthetic demo, `doctor`, `validate`, `dashboard`, evidence rendering and CI. Its `pyproject.toml` `stack` extra pins four component revisions (Action Manifest, Control Plane, Replay Bundle, Evidence Pack), including Control Plane `0a41faa97269...`. It does not currently declare the unified Registry, the newer Control Plane EffectivePolicySnapshot, or Registry lifecycle management as supported Ergonomics commands. The README explicitly states Ergonomics does not govern, issue verdicts or modify component data.

Consequently the existing front door cannot yet reliably present the post-19 Registry's effective-policy provenance and lifecycle status to private evaluators. This addendum extends the **read-only inspection/diagnostic/presentation surface**, not the Registry's authority.

## 2. Timing and dependency order

**Prerequisites:** Registry 19/19 consumer integration, approved D-06/D-07/AR-1 outcomes, completion of R1 baseline and core behavior-preserving Registry/Control Plane consolidation, compatible exact-head component pin manifest. Begin implementation only after the Architect approves the relevant R1 work package. This plan may merge beforehand.

**Recommended order:** R0 19/19 → R1 baseline → R2–R4 core refactor → **R1-E Ergonomics integration** in parallel with R5 test/evidence cleanup → R6 equivalence and Architect acceptance → R7 engineering freeze including Ergonomics pin → P1 preview sandbox and scenario delivery → R8 independent Tier 1 at the approved freeze. If R1-E changes the final frozen package, include it in the qualification candidate; do not add unqualified UI/tooling after the freeze.

## 3. Bounded deliverables

**E1. Public-interface and pin inventory.** Inventory Registry and Control Plane supported inspection/export APIs at current heads; choose *supported* public interfaces, not imports of internal Registry classes or direct database mutation. Reconcile the hub `component-lock.json` with Ergonomics `stack` extras and provenance. Report exact selected SHA and what was tested. Do not silently refresh pins or claim selected/production status based on main alone.

**E2. Read-only Registry diagnosis.** Extend `cognous-ocs doctor` or a narrowly versioned `registry doctor` interface to report supported/frozen contract versions; required family presence; selector/scope mismatches; expired/withdrawn/invalid selections; trust/epoch errors; and missing effective-policy binding. Every negative classification must originate from an authoritative Registry/Control Plane verification result or from clearly labeled *local setup checks*, never an invented governance verdict. Missing verifier capability should show **UNVERIFIED**, never PASS.

**E3. Effective-policy inspection.** Add a read-only `registry inspect` or report command exposing signed policy metadata, family/version, scope, source digest, effective-policy identity and actual effective restrictions where explicitly safe to disclose. Distinguish host original policy from Registry narrowing; label authority provenance and missing inputs. Redact any secret, signing key, private payload or personal identifiers. Registry/Control Plane remain the policy and commitment source of truth.

**E4. Evidence and preview UX.** Extend the existing static dashboard/evidence viewer to render operator-run P1 outputs: expected vs actual decision, reason/evidence, policy identity, mock effect, revocation/refusal path and replay status. Show warnings: synthetic, non-authorizing wrapper, not production-qualified. Provide one understandable guided walkthrough with no manual GitHub CLI requirement for invited reviewers. Evaluators receive sanitized generated reports initially; no direct external workflow dispatch.

**E5. Diagnostics contract and tests.** Version schemas for read-only output, preserve CLI exit codes and existing commands, add deterministic unsupported-version and missing-selection tests, no network in normal tests, test exact SHA pin compatibility, use approved fixture data only. Evidence/decision displays must match authoritative component outputs byte-for-byte or by clearly defined lossless normalization. Preserve older ergonomics demo behavior.

**E6. Documentation.** Update CLI contract, component support matrix, hub pins and preview instructions; explicitly separate inspect/validate/demo from issue/sign/revoke/activate. Avoid claiming all 19 parameters are configurable by a human-facing policy authoring tool if only signed Registry records and host APIs are supported.

## 4. Explicit non-goals

No policy-writing UI, issuer keys, key custody, Registry record signing, activation or revocation of production policies, new trust roots, agent/task role hierarchy, independent decision evaluator, permission to overwrite component stores, real destination credentials, self-service external GitHub access, new hosted SaaS, or blanket claims of deployment-wide durable activation. Later administrative management needs separately designed authenticated roles, approvals, audit, anti-rollback and separation-of-duties control, and does not belong in R1-E.

## 5. Acceptance and stop gates

- Ergonomics remains a one-way, non-authorizing dependency; direct components function identically without it.
- A missing or invalid mandatory Registry family cannot display as PASS, even when demo fixtures are malformed.
- Effective-policy and source identity match the actual component-verifier outputs; signing/commitment bytes remain unchanged.
- No credentials or secret policy material in rendered reports or uploaded artifacts.
- Exact pinned component compatibility and deterministic offline regression on Python 3.11/3.12; existing demo, doctor, schema and CLI contract tests remain valid.
- Changes that require new component authority APIs, altered signing/refusal semantics, persisted binding changes or new external access: **STOP**, open explicit decision and separate implementation track.
- Provide before/after command surface map, pin manifest, negative tests, sample static preview report and exact CI evidence for Architect review.

## 6. Plan amendments and release limits

Treat R1-E as a new named work package between core refactor and R1 engineering freeze; add the Ergonomics exact source SHA to R7 freeze index and P1 evaluator artifact manifest. P1's operator-run synthetic scenarios should use Ergonomics primarily to **present** evidence, not to execute or authorize effects. Independent Tier 1 remains deferred, not waived; Ed25519 security issues and publication/release/production holds are unchanged.

**This addendum does not authorize code implementation or merge in Ergonomics; it only places the work in the static sequence.**
