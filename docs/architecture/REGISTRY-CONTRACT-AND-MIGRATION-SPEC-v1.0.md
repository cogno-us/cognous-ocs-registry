# Cognous Registry Contract and Migration Specification v1.0

Status: PROPOSED, NON-AUTHORIZING. Companion to docs/architecture/REGISTRY-TARGET-ARCHITECTURE-v1.0.md and Static Migration Plan v1.1 section 12. Governing Constitution: cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b plus ADOPTION.md. Inventoried denominator: 19 parameters / 12 canonical rules (audit PR #60). No Registry code change or successor contract allocation is made here.

## 1. Target contract boundaries

The *candidate* successor r08-v6 should reuse an exact canonical signed record envelope, version-separated signing input, trusted selection envelope and typed registered policy families. Frozen r08-v1 through r08-v5 contracts, signing domains, reason vocabularies, vectors and legacy import paths must not be mutated or silently translated. Define envelope/protocol version separately from per-family schema revisions for future evolvability.

**Proposed record logical fields** (not an enacted exact wire schema): contract_version, family_id, family_schema_version, bounded payload, non_authorizing=true, record identity/digest, enforcing-component binding and evaluator reference. A signed selection must bind exact record digest, consumer, tenant, institution, authority domain, operation, selection ID, epoch/supersession/withdrawal, issuance/expiry, selector and issuer provenance, and revocation/trust references. The exact existing r08-v5 wire names/canonical encodings must be reused or mapped explicitly by a versioned adapter; do not invent wire compatibility by assertion.

**Verification result**: typed refusal with preserved reason/evidence or a verified, scope-bound, immutable proposed effective-policy snapshot. Never return permissive caller-only policy on failed REQUIRED selection.

## 2. Typed family contracts (proposed schema catalogue)

| Family | Payload keys and typed domains | Narrowing and invariants |
|---|---|---|
| runtime.allow_sets | allowed_actions, allowed_adapters, allowed_units, allowed_institutions, allowed_authority_domains: bounded sorted unique opaque-token arrays | exact intersection; empty deny-all; missing required keys refuse |
| runtime.ceilings | max_amount, max_effects: bounded exact integers | minimum of caller/record; zero effect ceiling denies; no float/bool coercion |
| runtime.target | allowed_target_prefixes: bounded target token array; target_match: closed enum [exact, segment, legacy-prefix] | joint accepted-target-set containment; mode and list never composed separately |
| cp.f4_ages | status_max_age_seconds, approval_max_age_seconds: exact bounded integer seconds | minimum; preserve host zero behavior, strict caller validation |
| cp.f5_class_age | class_status_max_age_seconds: nonempty class-id to bounded exact integer map | per-class minimum; unknown Registry class refuses; extension cap cannot defeat effective bound |
| cp.f5_unreadable | class_on_unreadable: nonempty class-id to [refuse, bounded_tolerance] map | only bounded_tolerance to refuse; original host irreversible invalidity must refuse before composition |
| cp.f5_revocation_assurance | per-class requires_revocation_assurance: exact Boolean map (proposed key naming) | false to true only; actual holder evidence must be checked, no synthetic assurance |
| cp.terminal_revocation | enablement for terminal-revocation/0.1: exact Boolean (proposed key naming) | off to on only; enforcement observes recorded revocation, cannot invent authority or revocation observation |
| cp.f5_irreversibility | per-class irreversible: exact Boolean map (proposed key naming) | false to true only; reversible_until/reversal_cost and other dependent members must remain valid; do not claim Registry attests factual reversibility |
| cp.freshness_anchor | anchor_deadline_to_inputs: exact Boolean | false to true; preserve deadline and outage-extension invariants |
| cp.observation | max_age_seconds and clock_tolerance_seconds: exact bounded integer seconds | minimum independently only if cross-field timing validity and binding are proved; missing ObservationPolicy remains hold |

**Important:** Proposed family identifiers, new key spellings and combined-family grouping above are DESIGN CANDIDATES, not already accepted r08-v6 schemas. The migration builder must reconcile them with existing r08-v2/v3/v4/v5 fields, strict source ranges and signing domains before any contract freeze. The six outstanding parameters require source-backed exact wire schema and explicit Architect decisions where their current coupling is unresolved. No independent generic rule interpreter.

## 3. Typed API and resolution semantics

Conceptual pure interfaces, not enacted Python signatures:

- verify_selection(record_bytes, selection_bytes, expected_scope, trust_snapshot, evaluation_time) -> verified selection | typed refusal
- compose_family(host_value, verified_family_payload, declared_applicability) -> restricted typed value | refusal
- resolve_effective_policy(host_policy, mandatory_family_selections, scope, evaluation_time) -> immutable effective-policy snapshot | refusal
- enforce_at_boundary(bound_snapshot, current_selection_material, live_authority_state, boundary) -> verified/no-effect refusal

Resolver **MUST**: validate host first; verify all applicable families; reject missing/failing mandatory family; check cross-field validity after composing; enforce monotone non-widening; bind a single final profile digest plus family identities; fail closed on unavailable trust or incomplete source; recompute or reverify at supported lifecycle boundaries. A composition is an atomic eligibility check even if individual family records are separately signed. Define trustworthy cross-record snapshot semantics before claiming full distributed atomicity.

The original evaluator continues to read the same typed host-policy fields (now from verified effective configuration) wherever its existing schema permits. Do not replace protected source semantics with bare Registry lookups or unrestricted runtime variables.

## 4. Source-to-policy migration mapping (19 audited fields)

| # | Field | Existing source/consumer | Target resolved carrier |
|---|---|---|---|
| 1 | allowed_actions | Runtime safe_executor.LocalExecutionPolicy.check | effective LocalExecutionPolicy.actions |
| 2 | allowed_adapters | Runtime safe_executor.LocalExecutionPolicy.check | effective LocalExecutionPolicy.adapters |
| 3 | allowed_units | Runtime safe_executor.LocalExecutionPolicy.check | effective LocalExecutionPolicy.units |
| 4 | allowed_institutions | Runtime safe_executor.LocalExecutionPolicy.check | effective LocalExecutionPolicy.institutions |
| 5 | allowed_authority_domains | Runtime safe_executor.LocalExecutionPolicy.check | effective LocalExecutionPolicy.authority domains |
| 6 | max_amount | Runtime safe_executor.py ceiling | effective LocalExecutionPolicy.max_amount |
| 7 | max_effects | Runtime safe_executor.py ceiling | effective LocalExecutionPolicy.max_effects |
| 8 | allowed_target_prefixes | Runtime safe_executor._target_allowed | joint effective target policy |
| 9 | target_match | Runtime safe_executor._target_allowed | joint effective match mode |
| 10 | status_max_age_seconds | Control Plane bounded.py status age | bound effective F4 scalar |
| 11 | approval_max_age_seconds | Control Plane bounded.py approval freshness | bound effective F4 scalar |
| 12 | ActionClass.max_status_age_seconds | Control Plane bounded.py _class_age_bound; freshness.py | effective RuntimeAuthorityProfile ActionClass age |
| 13 | ActionClass.on_unreadable | Control Plane bounded.py cached-grant branch | effective RuntimeAuthorityProfile ActionClass enum |
| 14 | ActionClass.requires_revocation_assurance | Control Plane runtime_authority.py / holder_inventory.py | effective ActionClass requirement, holder evidence separate |
| 15 | terminal-revocation/0.1 enablement | Control Plane runtime_authority.py / bounded.py recorded-grant denial | effective terminal-revocation profile setting |
| 16 | ActionClass.irreversible | Control Plane reversibility.py / bounded.py | effective ActionClass irreversible flag with dependent validation |
| 17 | FreshnessProfile.anchor_deadline_to_inputs | Control Plane freshness.py / bounded.py / policy_binding.py | effective FreshnessProfile anchor |
| 18 | ObservationPolicy.max_age_seconds | Control Plane bounded.py _reconcile_observation | effective ObservationPolicy bound |
| 19 | ObservationPolicy.clock_tolerance_seconds | Control Plane bounded.py observation future-time check | effective ObservationPolicy tolerance |

Paths are conceptual source-to-field mappings, not instructions to edit evaluators or a claim that all typed effective carriers already exist. For source commit IDs and exact audit symbols use the adopted parameter-catalogue.json; at migration time pin current source heads and re-check.

## 5. Explicit architectural blockers before implementation

1. **F4**: constructor scalar pairs currently are workflow-local, not persisted decision or approval commitment; choose future binding/compatibility before promising global replay equivalence.
2. **Activation**: host-wide durable one-configuration-per-tenant/action/authority-scope binding absent; local ledger is advisory.
3. **Observation**: ObservationPolicy binding to existing decision/commitment, clock semantics and 60/300 relationship unresolved; constructor clock_tolerance is a DISTINCT blocked parameter, not in the 19.
4. **Reversibility**: transition false->true may make dependent attributes invalid; compose with explicit final validity and do not replace evidence-based effective_reversibility semantics.
5. **Deadline anchor**: relationship to age_ceilings, outage extensions and profile commitment needs exact contract.
6. **Revocation**: evidence and lifecycle requirements for requires_revocation_assurance and terminal revocation; no change to who can revoke.
7. **Selection source**: rollback/high-water trust, epoch and revocation custody; no authorized CP ratchet.
8. **Cross-family**: coherent signed snapshot and applicable family set, especially across multiple selectors and Runtime/Control Plane.
9. **Version**: r08-v6 is a candidate; freeze only after approval of exact wire schemas, reason mappings, compatibility/downgrade and signing inputs.

If an actual enforcement boundary is missing, record the field as blocked and do not claim the parameter migrated.

## 6. Implementation strategy: one integrated work package

**Step I — Contract freeze:** Architect approves exact typed wire schemas, version domain, mandatory applicability, error codes, consumer binders and all high-risk decisions above. Never rewrite frozen v1–v5 vectors.

**Step II — Registry implementation:** add unified family registrations and reusable verifier/envelope mechanics, with exact-family validators and no dynamic policy code. Maintain strict cross-version isolation, deterministic composition and explicit refusal.

**Step III — Consumer migration:** replace qualified host configuration *source* access with a verified, immutable effective-policy reference upstream of unchanged evaluators. Reuse merged GovernedLifecycle/GovernedPolicyWorkflow; preserve original host validity, effect-time selection checks, approval identity and recorded negative evidence. Runtime and Control Plane can be parallel workstreams with independent files and test fixtures.

**Step IV — Focused development safety:** run schema/canonicalization, frozen vector compatibility, compilation/import, family differential and targeted changed-value negative tests in CI for each PR; do not repeatedly schedule independent qualification. Keep one review gate for the integrated work package and stop on protected evaluator or authority semantic changes.

**Step V — Final integrated assurance:** freeze component SHAs and evidence; run one coordinated complete functional, adversarial, replay/restore, revocation, mutation, security and independent Tier 1 campaign against full 19-parameter integration. Preserve initial/final failure deltas and no paid calls without authorization. V09 remains separate; Ed25519 #26/#34 security-held; publication, release, production HOLD.

## 7. Acceptance and inventory ledger

Record separately: eligible (19), Registry-represented, consumer-integrated, independently accepted. Last verified merged engineering baseline 13 integrated; six remaining: revocation assurance, terminal revocation, irreversibility, anchor deadline, observation max age, observation clock tolerance. Related two-parameter builder work may be in progress but does not change merged accounting. No newly proposed feature or extra blocked age parameter may silently alter the 19 denominator.

**This file is a proposal, not a request to merge implementation or authorize a new trust root, approval format, authorization mechanism or production release.**
