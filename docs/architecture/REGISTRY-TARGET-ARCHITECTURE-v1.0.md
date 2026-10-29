# Cognous Registry Target Architecture v1.0

Status: PROPOSED, NON-AUTHORIZING (2026-10-28). Governing: Engineering Constitution and ADOPTION.md at 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b; Static Migration Plan v1.1 section 12; Engineering Plan v1.5; audit PR #60. Last merged accounting 13/19 integrated, six outstanding, zero independently accepted. Frozen r08-v1 through r08-v5 remain preserved.

## Purpose

Define one target architecture for all 19 audited Registry-manageable parameters (within 12 canonical audit rules). Registry stores and authenticates **restrictions**, never originating authority, permissions, approvals or execution. A verified overlay can narrow a valid host policy, never widen or repair an invalid host configuration. Existing Control Plane and Runtime evaluators retain their enforcement semantics.

## Inventory and proposed target family grouping

| # | Exact audited parameter | Target grouping | Narrowing |
|---|---|---|---|
| 1 | allowed_actions | Runtime allow sets | intersection |
| 2 | allowed_adapters | Runtime allow sets | intersection |
| 3 | allowed_units | Runtime allow sets | intersection |
| 4 | allowed_institutions | Runtime allow sets | intersection |
| 5 | allowed_authority_domains | Runtime allow sets | intersection |
| 6 | max_amount | Runtime ceilings | numeric minimum |
| 7 | max_effects | Runtime ceilings | numeric minimum |
| 8 | allowed_target_prefixes | Runtime target scope | joint containment with match mode |
| 9 | target_match | Runtime target scope | joint containment with prefixes |
| 10 | status_max_age_seconds | Control Plane constructor ages | numeric minimum |
| 11 | approval_max_age_seconds | Control Plane constructor ages | numeric minimum |
| 12 | ActionClass.max_status_age_seconds | ActionClass freshness | per-class numeric minimum, extension bounded |
| 13 | ActionClass.on_unreadable | ActionClass failure posture | bounded_tolerance to refuse |
| 14 | ActionClass.requires_revocation_assurance | ActionClass revocation posture | false to true, evidence required |
| 15 | terminal-revocation/0.1 enablement | Terminal revocation | off to on, no new revocation authority |
| 16 | ActionClass.irreversible | ActionClass irreversibility | false to true, dependent fields valid |
| 17 | FreshnessProfile.anchor_deadline_to_inputs | Freshness coupling | false to true |
| 18 | ObservationPolicy.max_age_seconds | Observation freshness | numeric minimum |
| 19 | ObservationPolicy.clock_tolerance_seconds | Observation freshness | numeric minimum |

Numbers 8 and 9 form one jointly narrowable unit; independent parameter count remains 19. The last six rows numbered 14-19 are not yet verified as merged. Audit canonical IDs, types and source pins are in docs/audit/registry-eligibility-2026-10-28/parameter-catalogue.json. Three additional age/tolerance parameters remain BLOCKED outside the denominator; the funded-authority item remains unresolved.

## Trust, policy and execution architecture

1. Host provides original authorization limits and a fixed consumer/tenant/institution/authority-domain/operation scope, with ActionClass and action identifiers as applicable.
2. The authorized Registry selector provides a signed canonical record and selection bound to scope, family, version, epoch, revocation, trust and validity window.
3. A stable verifier authenticates selection, trust, supersession and record, returning typed refusal or effective restricted policy. Missing required selection fails closed.
4. Registered family composers enforce exact schemas, typed narrowing operators and cross-field invariants. Validate the **original host first** and the **final composed result after**; do not allow partial family activation.
5. A typed effective-policy snapshot carries applied family identities, scope, policy digests, provenance and final values into existing enforcement; do not load arbitrary mutable variables mid-effect.
6. Profile-bearing fields compose before approval issuance and are covered by existing approval_commitment and persisted catalogue_digest. Non-profile fields require explicit binding decisions.
7. Recheck mandatory selections at construction, decision entry, execute entry and the closest supported pre-dispatch gate; preserve definitive failed-attempt semantics. Delegated destination.apply is not transaction-atomic with revocation.
8. Keep refusal, evidence, recovery and replay consistent with existing component authority and original negative records. Host selection_source must provide durable epoch/trust/revocation high-water protection.

## Applicability, administration and activation

Scope is explicitly consumer_id, tenant_id, institution_id, authority_domain and operation_id, mapped by the host to action/action class. Per-agent and per-task use is possible by a host-owned mapping, but a universal native agent_id/task_id, wildcard hierarchy and enterprise administration UI are NOT presently established. One authoritative governed configuration per tenant/action/authority scope is a **target requirement**, not implemented deployment-wide: GovernedActivationLedger is only local and advisory. A durable host activation contract needs review; plain workflows can otherwise bypass Registry use.

Separate host policy owner, signed selector, deployment activator, approval issuer and executor. Registry selection alone never authorizes an effect.

## Versioning and compatibility

Preserve r08-v1 through r08-v5 signing domains, canonicalization, exported API behavior and frozen vectors. Candidate r08-v6 is a proposed unified successor, not allocated or implemented by this document. Separate envelope protocol version from typed family schema revision while retaining signature-domain separation and exact family dispatch; reject unknown versions and silent legacy reinterpretation. Reuse parsing and verification mechanics but keep each family's mathematical narrowing and evidence obligations specialized.

## Architect decisions required before final target-state adoption

- F4 constructor scalar binding: currently workflow-local, absent from persisted decision and approval commitment.
- ObservationPolicy binding, clock domain/ranges and the unresolved 60-versus-300 temporal relationship.
- Durable authoritative applicability/activation and cross-process conflict controls.
- Atomic selection snapshots across multiple family sources, rollback and revocation visibility.
- Reversibility transformation and validation of dependent ActionClass members.
- Anchor-deadline coupling to age ceilings/outage extensions.
- Revocation-assurance evidence, terminal-revocation authority and actual consuming boundaries.
- Successor contract version allocation and migration/rollback compatibility.

## End-state gates

D1 target architecture, D2 contract/migration specification, then one integrated implementation work package and one final coordinated cross-repository test/independent Tier 1 qualification campaign following final source/evidence freeze. Maintain lightweight developer schema, targeted and CI checks along the way. V09 separate; Ed25519 #26/#34 security-held; release/publication/production HOLD. No protected evaluator refactor or new authority is authorized here.
