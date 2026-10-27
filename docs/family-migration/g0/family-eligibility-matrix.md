# G0 family eligibility matrix

Proposals only; none is ratified, none is implemented. Rows are source-backed by `current-candidate-ledger.json` (record ids `A-001` abbreviate `G0-A-001`). G0: AUTHORIZED. G1–G5: NOT AUTHORIZED. V09 independent qualification: OPEN. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

Disposition vocabulary: MIGRATED / ALREADY-GOVERNED / ELIGIBLE-NOT-MIGRATED / RETAIN-IN-CODE / OUT-OF-SCOPE / UNRESOLVED / BLOCKED. Nothing is MIGRATED under this program: no migration has been implemented.

## 1. Counts

| Disposition | Records (source sites) | Rule groups (unique rules) |
|---|---|---|
| ALREADY-GOVERNED | 10 | 5 |
| ELIGIBLE-NOT-MIGRATED | 30 | 23 |
| RETAIN-IN-CODE | 60 | 56 |
| OUT-OF-SCOPE | 10 | 8 |
| UNRESOLVED | 5 | 4 |
| BLOCKED | 1 | 1 |
| MIGRATED | 0 | 0 |
| Total | 116 | 97 |

A *record* is one source site found by one worker. A *rule group* merges records that describe the same rule across components (ten merges, 19 records absorbed). Records by eligibility: {'CONDITIONAL': 36, 'ELIGIBLE': 5, 'NOT_ELIGIBLE': 69, 'UNRESOLVED': 6}.

## 2. Families F1–F11 and their parts

| Family | Part | Proposed disposition | Records | Evidence and note |
|---|---|---|---|---|
| F1a | actions/adapters/units in f1ab | ALREADY-GOVERNED | A-001, B-009, B-012, B-013 | Registry r08-v2 f1ab narrows (intersection) with explicit [] deny-all; Runtime effect-time guard enforces F-01 subset on all five sets. |
| F1a | frozen r08-v1/S04 file overlay (three keys, non-empty lists) | OUT-OF-SCOPE | A-015 | Frozen historical overlay; unchanged by this program. |
| F1b | institutions/authority domains in f1ab | ALREADY-GOVERNED | A-002, B-010, B-012 | Source conflict with Plan v1.0 M1 ('carried unchanged'): in r08-v2 f1ab both sets are validated, narrowed and may be deny-all like the other three (v2_f1ab.py F1AB_FIELDS). 'Carried unchanged' holds only for the frozen r08-v1/S04 overlay. Gap is evidence, not mechanism: decision-level narrowing/deny-all/exhaustive-grid negative oracles exist only for allowed_units. |
| F1c | max_amount | ELIGIBLE-NOT-MIGRATED | A-003, B-007, D-001 | No Registry slot (contract: 'no max_amount slot'; Amendment 3: caller-owned). Needs a new narrowing-only family or contract version; Runtime guard compares nothing for it today. |
| F1c | max_effects | ELIGIBLE-NOT-MIGRATED | A-004, B-008 | Same as max_amount. Runtime ledger consumes max_effects from the provisioned claim (G0-B-017, retained). |
| F1d | allowed_target_prefixes | ELIGIBLE-NOT-MIGRATED | A-005, B-006, D-002 | No Registry slot; order relation (subset of prefixes vs extension semantics) is non-trivial. |
| F1d | target_match mode choice | ELIGIBLE-NOT-MIGRATED | A-006, B-004 | Choice among three closed modes; narrowing order between modes must be defined (exact narrower than segment narrower than legacy-prefix is not proven in source). |
| F2 | mode vocabulary, separators, well-formedness | RETAIN-IN-CODE | B-005, B-011 | Evaluator semantics (safe_executor.py); W1-029 stays UNRESOLVED as a row, with a proposal that the closed vocabulary is IMMUTABLE_CONTROL. |
| F3 | admission and parsing floors | RETAIN-IN-CODE | A-010, A-011, A-013, B-001, B-002, B-017, B-023, B-026, B-028, B-030, D-005, D-009, D-010, D-013, D-016, D-019, D-028 | Mandatory floors / fail-closed admission bounds; no config path may lower or raise them. |
| F3 | host-owned lowering of non-admission resource budgets (OpenShell timeout, CLI input cap, manifest file cap, bounded-json defaults) | UNRESOLVED | B-027, C-040, D-006, D-024 | Workers proposed RETAIN-IN-CODE (conditional). Whether the Registry should carry resource budgets at all is a scope decision; none changes an authority decision. (Lead override: Lead keeps UNRESOLVED because the question is scope (Registry carrying resource budgets), not value-level eligibility.) |
| F3 | run-record caps supplied by the lease author | OUT-OF-SCOPE | D-026 | Caller/author-supplied data in a hub reference profile. |
| F4 | status_max_age_seconds / approval_max_age_seconds scalars in Registry f4 | ALREADY-GOVERNED | A-007, A-009 | r08-v2 f4 carries two ints (1..2147483647, min(caller, registry)); contradicts Plan v1.0 'F4 not covered'. |
| F4 | identity/mandate ages and clock tolerance (Control Plane ctor defaults) | ELIGIBLE-NOT-MIGRATED | C-003, C-004, C-005, C-006 | Not carried by f4. Mapping decision needed: under a runtime-authority profile the class bound replaces the global status bound only for grant status; conflict and policy status keep the ctor bound. |
| F4 | destination observation policy (300 s / 5 s) | ELIGIBLE-NOT-MIGRATED | C-001, C-002, D-011 | Distinct concept from the 60 s authority-input bound; no code relates the two (60 vs 300 analysis in the exit report). |
| F4 | freshness profile: extension limit and anchor | ELIGIBLE-NOT-MIGRATED | C-019, C-020 | Opt-in profile members; extension 0 refuses all; anchor toggles deadline anchoring. |
| F4 | freshness profile: liveness mechanics (lease, reaper, nonce) | RETAIN-IN-CODE | C-016, C-017, C-018, C-007 | Liveness/safeguard mechanics; nonce toggle is a safeguard; selection rule is evaluator semantics. |
| F4 | Registry snapshot / selection validity windows (signed data) | RETAIN-IN-CODE | A-012 | valid_from/valid_until are authenticated data inside records, not configuration. |
| F4 | Runtime recovery freshness window (86400 s) | ELIGIBLE-NOT-MIGRATED | B-016 | Inline literal at recovery_resolution.py; narrow-only lowering candidate. Tier conflict: worker rated it Tier 3, S02 section 3 tiers freshness bounds (F4) as Tier 1 (ruling needed). |
| F4 | freshness values in other repositories (hub, exchange, resolver assurance, federated governance) | ELIGIBLE-NOT-MIGRATED | D-015, D-020, D-021, D-022 | Scope confirmation required: these live in non-core repositories and reference profiles. |
| F5 | class age map in Registry f5 | ALREADY-GOVERNED | A-008, C-021, C-031 | r08-v2 f5 carries class->age; policy-binding/0.1 ceilings and approval-generation binding already host-configured. |
| F5 | unreadable behaviour, revocation assurance, reversibility, class declarations | ELIGIBLE-NOT-MIGRATED | C-008, C-009, C-010, C-011 | Host profile values; only narrowing directions can be Registry-governed; three-value UNKNOWN_BEHAVIORS has one gate branch. |
| F5 | host trust configuration (producer keys, catalogue, signer sets, holder inventory) | RETAIN-IN-CODE | C-013, C-014, C-023, C-032 | Trust anchors and authority roots are never externalized. |
| F5 | evidence criteria thresholds | RETAIN-IN-CODE | C-012 | Arrive inside the issuer-approved authority context (CALLER_SUPPLIED), not host config. |
| F5 | operation-identity labels | OUT-OF-SCOPE | C-015 | Labels recorded on attempt rows; no policy effect. |
| F6 | Runtime permissions.py/permissions.json | OUT-OF-SCOPE | B-014 | Legacy/synthetic data file; not on the governed effect path. |
| F6 | action-manifest authority_required and per-tool allow lists | UNRESOLVED | D-008 | Live authored home of F6-like values; ownership and narrowing order undecided. |
| F7 | Runtime dedupe_ttl_seconds | OUT-OF-SCOPE | B-015 | Models provider dedupe horizon (provider fact), validated per destination. |
| F7 | Control Plane DedupeProfile | UNRESOLVED | C-022 | Policy versus provider fact undecided (worker C question). |
| F8 | demo defaults and config file schema | OUT-OF-SCOPE | C-025, C-027 | Demo-only / inert (policy_config.default_action has no consumer). |
| F8 | authority-granting helpers and legacy PolicyGate evaluator | RETAIN-IN-CODE | C-026, C-028, C-029, C-030 | Demo grants confer authority (read/write); evaluator is protected semantics. |
| F9 | tenant_id <= 128 (Runtime admission, Control Plane sites) | RETAIN-IN-CODE | B-003, C-035, C-036 | Identifier-shape admission bound repeated in 8 places across 3 repositories with no shared source; canonical binding restricts further. Narrowing config would desynchronize sites. |
| F9 | action-manifest tenant bound | UNRESOLVED | D-004 | Worker D rated CONDITIONAL; cross-repository single-source question undecided. |
| F10 | trend report keyword defaults (5, 1) | ELIGIBLE-NOT-MIGRATED | C-037 | Non-gating diagnostic; no consumer influences an authority decision. Low priority. (Lead override: Worker proposed OUT-OF-SCOPE; lead aligns to approved wave M8.) |
| F11 | default values in action-manifest and replay-bundle | ELIGIBLE-NOT-MIGRATED | D-007, D-012 | Conditional: defaults only; confidentiality may only be tightened. |
| F11 | Control Plane RedactionConfig, redaction mechanism, truncation | RETAIN-IN-CODE | C-038, C-039, C-041 | Confidentiality controls stay code-enforced; configuration may only widen redaction. |

Plan wave per family: F1a → (migrated before this program: r08-v2 f1ab); F1b → M1; F1c → M2; F1d → M3; F2 → (stays in code); F3 → M6; F4 → M11; F5 → M12; F6 → M4; F7 → M5; F8 → M9; F9 → M7; F10 → M8; F11 → M10.

## 3. Source-backed conflicts with Plan v1.0 premises

1. **M1 / F1b is already governed.** In r08-v2 the f1ab record carries all five sets (`allowed_actions, allowed_adapters, allowed_units, allowed_institutions, allowed_authority_domains`); institutions and authority domains are validated, narrowed by intersection and may be deny-all (`registry_successor/v2_f1ab.py`). "Carried unchanged" is true only of the frozen r08-v1/S04 overlay (`registry_consumer/consumer.py:42`). Runtime enforces the F-01 five-set subset at effect time. The gap is negative oracles, not mechanism.
2. **F4 and F5 are partly governed.** `FAMILIES_V2` already registers `f4` (status and approval ages) and `f5` (class→age map). Plan v1.0 states F4/F5 are not covered. Identity/mandate ages, clock tolerance, the observation policy and the other F5 profile fields are not covered.
3. **Registry carries no operator-configurable value** and no slot for `max_amount`, `max_effects`, `allowed_target_prefixes` or `target_match`; Amendment 3 records them as caller-owned residuals. The Runtime effect-time guard compares only the five sets.
4. **F6/F7 candidates named by S02 are legacy or provider facts** (Runtime `permissions.json`, `dedupe_ttl_seconds`). The live homes of F6-like values are the action-manifest `authority_required`/`tools.allowed` declarations (unresolved ownership).
5. **S02 omitted whole repositories.** Twenty NEW families were found (section 4); only the redaction defaults and the tenant bound were visible to S02 outside Runtime/Control Plane.

## 4. NEW source-backed families

| Family | Records | Disposition | Eligibility |
|---|---|---|---|
| NEW:family-dispatch | A-014 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:authorization-pin | B-018, B-019, B-020, B-021 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:selection-store | B-022 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:synthetic-refund-profile | B-024 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:refusal-vocabulary | B-025 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:authority-writer | B-029 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:host-tooling | B-031 | OUT-OF-SCOPE | NOT_ELIGIBLE |
| NEW:dedupe-ttl | C-022 | UNRESOLVED | UNRESOLVED |
| NEW:merge-record | C-024 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:effect-limits | C-033 | UNRESOLVED | UNRESOLVED |
| NEW:validity-windows | C-034 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:shape-bounds | C-036 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:manifest-default-posture | D-003 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:exchange-delivery-retry | D-014 | RETAIN-IN-CODE | CONDITIONAL |
| NEW:destination-admission-rate-limit | D-017 | RETAIN-IN-CODE | NOT_ELIGIBLE |
| NEW:audit-budget | D-018 | ELIGIBLE-NOT-MIGRATED | CONDITIONAL |
| NEW:inventory-staleness | D-023 | OUT-OF-SCOPE | NOT_ELIGIBLE |
| NEW:claim-scanner-terms | D-025 | UNRESOLVED | CONDITIONAL |
| NEW:consequence-tier-delay-ceilings | D-027 | BLOCKED | NOT_ELIGIBLE |
| NEW:qualification-harness-thresholds | D-029 | OUT-OF-SCOPE | NOT_ELIGIBLE |

Only five NEW families carry a non-retain disposition: `NEW:dedupe-ttl` (UNRESOLVED), `NEW:effect-limits` (UNRESOLVED; W8-091), `NEW:audit-budget` (ELIGIBLE-NOT-MIGRATED, reference profile only), `NEW:claim-scanner-terms` (UNRESOLVED; outside effect/authority) and `NEW:consequence-tier-delay-ceilings` (BLOCKED; owner confirmation, proposed and unenforced).

## 5. Constitutional constraints applied

CA05 (no invented policy, default or floor), CA12 (floors protected), CA18 (policy versioned, authenticated, reviewed; invariants protected from config override), and the Constitution's statement that no particular rules engine, storage form or activation mechanism is required. Every eligible row is governed by plan section 7: configuration may only narrow, unknown/absent/corrupt input never adds permission, and a measurable baseline plus negative tests must exist before any increment.
