# S02 — Hardcoded-rule inventory (bounded, source-backed)

Non-authorizing, builder-side, unqualified. Release, publication and production HOLD. Inventory only: no registry, no rule extraction, no runtime change, no catalogue import, no S03.

- Plan: OCS-REG-PLAN v1.1, S02 section: https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.1.md (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`)
- Constitution (pinned): https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md
- Authorization: operator decision D5 (`docs/decisions/2026-10-24-operator-decisions-D1-D5.md`); S01 PASS at merge `6feb06ec`, closeout `f8aaf11d`.
- Exact sources: Execution Runtime `ec728da6dc301a664b331ac8986afd6e850a1273` (the g8-r10 Runtime); Control Plane `0a41faa972699f7ec3063967a14cd9bdd3e67d27` (the g8-r10 lock's `control_plane`). Both verified by `git rev-parse HEAD` in this session.

## 1. Method and limits

Nine read-only workers inspected disjoint file sets and classified each rule-bearing construct into one of six classes. The builder (integration owner) reconciled counts, verified the finalist candidates against source, and normalised tiers to the pinned Constitution table (Tier 1 critical: authority, admission, security, trust, atomic state, irreversible effects, negative-evidence custody; Tier 2 substantive; Tier 3 routine). Raw tables: `docs/s02-evidence/W1.md` to `W9.md`.

Limits (stated, not hidden):
- Worker classifications were produced by AI workers and are provisional. Only the items marked VERIFIED below were re-read against source by the integration owner.
- This is not an exhaustive or complete census. Not inventoried: `tests/`, `examples/`, `conformance/`, `schemas/` contents (pointers only), the Control Plane `tools/`, and any component outside Runtime and Control Plane. No claim of completeness is made.
- "Test evidence" in the raw tables is by name or grep; no upstream test suite was run in S02. The only behavioural evidence run here is the S01 suite.
- Misclassification risk is highest for CONFIGURABLE-CANDIDATE and UNRESOLVED rows; both are listed below.

## 2. Counts (620 rows; reconciled by script)

| Class | Rows |
|---|---|
| MANDATORY-INVARIANT | 354 |
| SERIALIZATION-OR-EVIDENCE | 90 |
| INCIDENTAL-CONDITIONAL | 51 |
| REFUSAL-OR-REASON-VOCABULARY | 50 |
| CONFIGURABLE-CANDIDATE | 43 |
| UNRESOLVED | 32 |

By worker (rows): W1 Runtime `safe_executor.py` 74; W2 Runtime admission/grant 97; W3 Runtime effect/recovery 95; W4 CP policy gate 35; W5 CP reasons/validation 51; W6 CP `bounded.py` 1-1400 49; W7 CP `bounded.py` 1401-2756 65; W8 CP authority/freshness 101; W9 CP remaining 53.

## 3. Source-to-rule-family crosswalk (candidates only)

"Already data" means the value is supplied by a caller, constructor or profile today (the code reads it; it is not a literal). Most CONFIGURABLE-CANDIDATE rows are of that kind: the configurable part exists, the surrounding gate is code. Row IDs refer to `docs/s02-evidence/`.

| Family | Sources (file:line; row IDs) | Evaluator / boundary | Already data? | Existing tests | Tier (normalised) |
|---|---|---|---|---|---|
| F1 Local execution policy values: allowed institutions, authority domains, adapters, actions, units, target prefixes, `max_amount`, `max_effects`, `target_match` | Runtime `engine/safe_executor.py:358-372` (fields), `410-430` (`LocalExecutionPolicy.check`); W1-033, W1-040, W1-041, W1-043 | `LocalExecutionPolicy.check` fixed order and reason texts; `__post_init__` fail-closed validation (`:374-395`); `_target_allowed` / `_target_is_well_formed` (`:396-408`, `:347-355`) | Yes: constructed by the caller | S01 suite (63 tests: positive, 7 refusals, boundary equality, order, target modes, well-formedness) | Subject matter Tier 1 (pre-dispatch admission to an effect); data values only |
| F2 Target-match vocabulary and separators | `safe_executor.py:343-344`; W1-029 (UNRESOLVED), W1-030 | enumerated modes `segment`/`exact`/`legacy-prefix`; separators `/:` | No: literals | S01 target-mode tests | Tier 1 subject; keep in code |
| F3 Size/depth/timeout budgets | `safe_executor.py:147-184` (depth 32, 10000 nodes, 1 MiB); `openshell_environment.py:36-38,74,93-94,118,151-158,192`; `strict_json.py:21,24-33` (`MAX_TEXT=200`); `cli_run.py:61` (1 MiB); W1-007/008, W2-083/086/087, W5-048, W9-003 | resource bounds on admission/IO | Mostly literals | none seen for most | Split: W1-007/008 are admission guards, so Tier 1; remaining bounds on I/O and process resources are Tier 2 minimum (resource-exhaustion and security consequences, CA14) |
| F4 Observation / status / approval freshness bounds | CP `cli_run.py:510` (`ObservationPolicy(300, 5)` literal; VERIFIED); `bounded.py:411-415,1264-1280,1890-1968,2352-2368,2394-2400,2431-2474,2506`; `freshness.py:62-72` (W8 FR coordinates are cumulative; see errata in `docs/s02-evidence/README.md`); Runtime `recovery_resolution.py:266-269` (`0 <= age <= 86400`, inline literal; VERIFIED); W6-016/040/041, W7-021/040/042/047/050, W8-040/043/044, W9-001, W3-087 | admission freshness gates; `ObservationPolicy.max_age_seconds` has no default (VERIFIED `bounded.py:411-415`) | Mixed: constructor/profile values plus call-site literals | `test_bounded_authorization.py`, `test_freshness.py` (by name) | Tier 1 |
| F5 Per-action-class authority declarations | CP `runtime_authority.py:87-121,153-170`; W8-005..011, W8-014 | status age, `on_unreadable`, revocation assurance, reversibility, evidence thresholds | Yes: host profile | `test_runtime_authority.py`, `test_reversibility.py` (by name) | Tier 1 |
| F6 Agent permission allow-list | Runtime `engine/permissions.py:15-23`, `permissions.json:1-4`; W2-001, W2-003 | exact-membership allow check | Data file already | `tests/test_permissions.py` (by name) | Tier 1 |
| F7 Dedupe / replay-window defaults | Runtime `dedupe_destination.py:105` (`dedupe_ttl_seconds=600`; VERIFIED); W3-062; CP `DedupeProfile` | key-memory TTL | Default literal, ctor-overridable | `test_n4_dedupe_destination.py` (by name) | Tier 2 minimum: the TTL governs duplicate suppression of effects; the guard itself is Tier 1 (W3-063 UNRESOLVED) |
| F8 Demo policy tool lists | CP `demo_policies.py:36-39,81-84`; W4-020/021 | demo only | Literals | none found | Tier 3 not asserted: demo lists feed authority records (W4-022/023 grant read/write); treat as Tier 2 until reviewed |
| F9 Tenant id length bound | `safe_executor.py:318-321` (W1-027); CP `bounded.py:151-154` (W6-008) | shape validation | Literal | none found for the 128 bound | Tier 2 |
| F10 Diagnostic trend thresholds | CP `reason_vocabulary.py:21-25,31-32` (`5`, `1`); W5-002 | non-gating trend report | kwargs with defaults | `test_rule_revision.py:118-120` (by name) | Tier 2 minimum: Tier 3 not asserted; changing a threshold changes reported behaviour, so it is treated as Tier 2 until reviewed |
| F11 Redaction defaults | CP `models.py:420-451`, `cli.py:107-114`; W9-002 | redaction config | Mechanism configurable, defaults literal | W9-002 lists tests for default payload redaction and fingerprint blanking (by name; upstream suite not run in S02) | Tier 2 minimum, with confidentiality and privacy controls treated as Tier 1 (security scope) until reviewed; Tier 3 is not justified |

### 3a. Candidate accounting: rows not mapped to a family above

Four of the 43 configurable candidates had no explicit crosswalk disposition. Each is mapped here (provisional, worker-classified, not re-read against source beyond the cited lines):

| Row | Subject | Disposition |
|---|---|---|
| W8-041 | `FreshnessProfile.reaper_interval_seconds` (`freshness.py:64`, default 30) | F4 adjacent: liveness interval, not an admission gate; Tier 2 minimum |
| W8-042 | `FreshnessProfile.nonce` (`freshness.py:66`, default True) | F4 adjacent: toggles a freshness safeguard, so Tier 1 until reviewed; not a migration candidate |
| W8-068 | `HolderInventory` (host-enumerated holders; empty gives `holder_inventory_missing`) | F5 adjacent: host data feeding an authority check; Tier 1 until reviewed |
| W8-072 | `OperationIdentityProfile` resolver labels | Evidence labels only per worker; Tier 2 minimum; omitted from F1-F11 as a labelling item |

## 4. Explicit non-migratable invariants (kept in code)

These must not move to configurable data under CA05, CA12 and CA18; they are classed MANDATORY-INVARIANT in the raw tables (354 rows) unless listed in section 5:
- Check order and fail-closed validation in `LocalExecutionPolicy` (`check`, `__post_init__`, strict number validators), the unreachable-but-present "exactly one effect" rule, and target well-formedness (control/format/surrogate characters, dot-segments).
- Envelope/snapshot validation, payload commitments, attempt state machine, destination commit and durable failure recording (W1).
- Operation admission and qualification (W2), including the required observation set (W2-025, UNRESOLVED).
- Grant, approval, revocation, recovery and atomic authority-effect logic (W3).
- Policy-gate rule chain, manifest gate and validation (W4, W5), authority/freshness/reversibility admission gates and `bounded.py` decision flow (W6 to W8).
- Closed reason-code vocabularies (50 REFUSAL rows): external commitments under CA12/CA21; changes need an authorized compatibility transition.

## 5. Unresolved classifications (32)

W1-029, W1-056, W1-058, W1-073; W2-025, W2-036, W2-038, W2-067, W2-077, W2-082; W3-024, W3-063; W4-004, W4-014, W4-015, W4-018, W4-022, W4-023, W4-033; W5-011, W5-012, W5-023, W5-028, W5-044; W6-004, W6-005, W6-042; W8-014, W8-091; W9-007, W9-017, W9-027. One-line reasons are in the raw tables. They stay unresolved; none is proposed for migration. Highest-attention items: W4-033 (unsigned rule-revision rows recorded, not refused), W5-044 (authority/actor mismatch is a warning), W9-017 (AGT warnings force `hold`), W9-027 (the definitions of "applied/unresolved attempt" differ between `merge.py` and `dedupe.py`).

## 6. Recommended first migration family (proposal only; S03 not authorized)

**Family: F1, Local execution policy values** (Runtime `LocalExecutionPolicy` construction data). **Narrowed initial increment, per Architect ruling of 2026-10-24: allowed units, allowed adapters and allowed actions only** (`allowed_units`, `allowed_adapters`, `allowed_actions`; `safe_executor.py:358-372`, checked at `:418-424`).

Why F1: every value is already caller-supplied data, so migration moves data and leaves evaluator code unchanged; it is the S01 baseline with a pinned source and a hash-locked reproducible suite (63 tests, including per-restriction refusals, ordering and negative controls); the destination is synthetic SQLite with no external effects. Why narrowed: fewer fields means a smaller change surface and a simpler equivalence comparison.

Deferred (not in the first increment, and not migratable by implication): amount ceiling and effect-count ceiling (`max_amount`, `max_effects`), target prefixes and match modes (`allowed_target_prefixes`, `target_match`, F2), and, because the ruling names only units, adapters and actions, also institutions and authority domains. All corresponding code checks remain mandatory and unchanged.

What stays in code regardless: check order, reason texts, `__post_init__` fail-closed validation, strict number validators, the one-effect rule, target well-formedness and match-mode semantics, and all validation upstream of `check`.

Risk, stated plainly: the narrowed subset is still Tier 1 admission-related subject matter. The smaller scope reduces change complexity; it does not remove the need for CA14 (secure by construction: least privilege, enabled-path security review) and CA18 (versioned, authenticated, reviewed policy data; protected invariants not overridable by configuration; missing, invalid or unsupported records fail closed; negative tests; proportionate independent review). A registry-supplied value must never make the policy more permissive than the explicit caller-constructed one. The alternatives F3, F8, F10 and F11 are not recommended as the first family. F3 (admission guards W1-007/008 are Tier 1, remaining bounds Tier 2 minimum) and F11 (confidentiality/privacy controls treated as Tier 1, rest Tier 2 minimum) are mixed-tier; F8 and F10 are Tier 2 minimum with Tier 3 not asserted. They are mostly literals with little or no test evidence by name, and would not exercise the registry contract meaningfully. F4 and F5 (freshness and authority declarations) are higher value but Tier 1 with wider blast radius.

Recommended bounded S03 scope (proposal; needs a new operator decision): a one-family schema and deterministic validator for exactly these three allow-lists, with stable identity/version/hash, provenance, applicability, registered evaluator reference, required inputs, fail-closed behaviour for missing/invalid/unsupported records, and non-authorizing semantics; no population from the historical catalogue, no change to `LocalExecutionPolicy` code in S03.

## 7. Observations recorded, not judged

- `cli_run._write_atomic` has no fsync or fchmod, unlike `atomic_write.write_bytes_atomic` (W9).
- `replay.to_json` does not use `strict_json` (W9).
- `PolicyViolationError` and `FrameConfigurationError` are defined but not raised in W9's files.
- The embedded Runtime `CONTROL_PLANE_COMMIT` `2ea9528e...` differs from the lock's `0a41faa9` (S01 finding, unchanged).
- The runtime-authority configuration schema carries a default of `60` at line 18; it appears to be a status-age bound, not the `300` observation window at `cli_run.py:510`; the relationship is an explicitly UNRESOLVED source relationship (Architect ruling 7) and is not verified here; it is carried forward and not silently resolved.
- Worker tier labels were inconsistent (two workers did not read the Constitution); this document's tiers are normalised and are still provisional.

## 7a. Architect rulings applied (2026-10-24)

The bounded 620-row inventory is retained, with all provisional and unresolved classifications identified; S02 is not expanded into an exhaustive inventory or qualification exercise. The 32 unresolved items stay unresolved and none is migrated or silently resolved. Candidate-family tier language was corrected where Tier 3 was unjustified (F3, F7, F8, F11). F1 is narrowed as in section 6. S03 is not begun.

## 8. Validation (PASS / FAIL / SKIP)

- Pin checks: Runtime `ec728da6` and Control Plane `0a41faa9` confirmed by `git rev-parse HEAD`: PASS.
- Count reconciliation: 620 rows parsed from nine files, class counts sum to 620: PASS (script, not committed).
- Finalist spot-checks against source (`cli_run.py:510`, `bounded.py:411-415`, `dedupe_destination.py:105`, `recovery_resolution.py:266-269`, `safe_executor.py:358-430`): PASS.
- S01 suite unchanged and re-run on this branch: see PR comment for the exact result.
- Upstream Runtime/Control Plane test suites: SKIP (not run in S02).
- Independent review: not performed at authoring time; requested on the PR.
