# 3. Configuration-field extraction register

Status: planning only. The manifest is the **merged inventory** (qualification repo merge commit `be1994a961e4e40612d999972ede6547a3729887`, PR #227 accepted by the Architect): `docs/registry-v1-scope-assessment/data/configuration-extraction-manifest.{jsonl,csv}`, 96 rows representing 95 distinct underlying fields. The first draft of this plan read PR #227 head `64b4942b` (provenance only). Each V1 row below was re-read against source at the exact pins (Runtime `c5e97e87`, Control Plane `7a4bcd40`); no repository test was run. Benefit and complexity levels are the manifest's reasoned inference, not demand data.

## Manifest totals (96 rows, 95 distinct fields)

| Disposition | Rows | Treatment in this plan |
|---|---|---|
| `DIRECT_EXTRACTION` | 5 | All five are V1 fields |
| `CONDITIONAL_EXTRACTION` | 17 | Three are V1 fields (the Control Plane ages); fourteen deferred (including `max_amount`) |
| `UNRESOLVED` | 16 | Not extracted; each stays unresolved until its source finding decides it. Includes CP-F3-07 and CP-F4-13 |
| `CODE_OWNED_GUARDRAIL` | 47 | Stay code; listed so nothing adjacent is silently dropped |
| `NOT_RELEVANT_TO_V1` | 11 | Not extracted |

**Duplicate-field accounting.** CP-F3-07 and CP-F4-13 are two inventory rows for one underlying field, `FreshnessProfile.lease_acquire_timeout_seconds`; both are UNRESOLVED, CP-F4-13 governs, the field is counted once (hence 95 distinct fields) and is excluded from Model B. Model counts under the inventory methodology (eligible fields, not qualification results): Model A 9, Model B 22, Model B-only 13.

Total configurable fields in V1: **8** (5 Runtime, 3 Control Plane), operator-approved. `max_amount` (RT-F1c-01) is deferred. No count of rows is a count of safe migratable fields.

## The eight V1 fields and the deferred `max_amount`

Columns: scenarios are existing IDs from the crosswalk (not restated); "Decisions" are the named rulings that gate the field.

| # | Field ID | Field (source, units) | Evaluator and source | Disposition | Benefit / complexity | Decisions | Existing scenarios (examples) | Extraction form |
|---|---|---|---|---|---|---|---|---|
| 1 | RT-F1a-01 | `allowed_actions` (frozenset of non-empty str) | `LocalExecutionPolicy.check` `safe_executor.py:419` | DIRECT | HIGH / LOW | none | C11, C02, TC-L06-003/011/013/014 | Set intersection with caller; empty = explicit deny-all |
| 2 | RT-F1a-02 | `allowed_adapters` | `check` `:417` | DIRECT | MEDIUM / LOW | none | C11, C02, TC-L06-003/009/011 | Same |
| 3 | RT-F1a-03 | `allowed_units` | `check` `:423` | DIRECT | MEDIUM / LOW | none | C11, TC-L06-011/014 | Same; do not add per-unit ceilings |
| 4 | RT-F1b-01 | `allowed_institutions` | `check` `:413` (first dimension) | DIRECT | MEDIUM / LOW | none | C11, D02, C18 | Same; independent `_check_trusted_context` (`control_plane_adapter.py:87-92`) stays |
| 5 | RT-F1b-02 | `allowed_authority_domains` | `check` `:415` | DIRECT | MEDIUM / LOW | none | C11, D02, C18 | Same |
| — | RT-F1c-01 | **DEFERRED, not V1.** `max_amount` (single unit-less binary64 ceiling, inclusive) | `check` `:411`, `:425` | CONDITIONAL | MEDIUM / HIGH | D4, D6, encoding (G3) | C11, TC-L06-014 | Not built in V1. If later authorized: `min(caller, registry)`, single declared unit only; see [04](04-component-ownership-and-adapter-matrix.md) |
| 6 | CP-F4-04 | `status_max_age_seconds` (int seconds, default 60) | `bounded.py:1271`, consumers `:2445`, `:2469`, `:2398-2400` (profile-less only) | CONDITIONAL | MEDIUM / HIGH | D4, W6-042 | D03, TC-D09-009/016 | `min(caller, registry)` per scalar, code floor >= 1, strict int |
| 7 | CP-F4-07 | `approval_max_age_seconds` (int seconds, default 60) | `bounded.py:1274`, consumer `:2505`; not hashed into the approval commitment | CONDITIONAL | MEDIUM / HIGH | D4, W6-042 | H01, TC-L06-015, D03 | Same |
| 8 | CP-F5-01 | `ActionClass.max_status_age_seconds` (int seconds, default 60, `ge=0`) | `runtime_authority.py:87`; consumers `bounded.py:2394-2399`, `:2082-2088`, `:2163`, `runtime_authority.py:341` | CONDITIONAL | MEDIUM / HIGH | D4, W6-042, W8-014 | C01, TC-D09-016 | Per-class `min` on the profile before construction; serialized after F4 |

### Semantics that matter (read at the pins; no repository test was run)

- **Runtime sets.** Each is `frozenset` of non-empty `str`, validated in `__post_init__` (`safe_executor.py:374-395`). An empty set is accepted and means deny-all for that dimension; an omitted argument is a constructor `TypeError`, never an allow. `check` order is fixed and first failure wins: ceiling validation, institution, domain, adapter, action, target, unit, amount, one effect, effect count. Exact membership; no case folding or wildcard. S03/S04 already cover the three F1a fields as intersection; **F1b is new** (S03 `supplies` is fixed at three, so F1b needs a new contract version).
- **`max_amount` (deferred; behaviour stays exactly as is).** Validated inside `check` (`:411`), not `__post_init__`. A bad ceiling raises `ValueError` before the institution check: Route A `observe` catches only `PermissionError`, so it escapes without `local_refusal`; Route B maps it to `local_policy_evaluation_error`. That behaviour is preserved, not changed.
- **Ages.** Plain Python `int` seconds everywhere in the Control Plane; no floats. Composition is a validated per-scalar `min` on strict integer seconds. Narrow-only holds mechanically: every consumer is monotone (a smaller bound refuses a superset). The caller value is unvalidated today (`inf` disables staleness on the no-profile path; `None`/`str`/`nan`/overflow crash `decide` rather than widen), so the helper validates the caller value first and refuses, never clamps. A bound of 0 is a de facto deny-all, so the helper enforces a code floor of at least 1. There is **no universal five-second floor**, and no artificial cross-bound is imposed among the distinct F4 ages (Architect rulings, [10](10-architect-rulings-and-repin.md)).
- **F4 versus F5.** They never compete on one record. With a `RuntimeAuthorityProfile`, F5 owns grant status; F4 still owns conflict and policy status always, and grant status only without a profile. No cross-bound exists in code; the recommended ruling is "none required".
- **F5 approval coupling.** `approval_commitment` hashes the profile dump (`runtime_authority.py:186-194`). A narrowed profile changes it, so approvals issued under the caller profile fail with `runtime_authority_approval_mismatch` (`:268-271`): correct, fail closed, but it looks like an outage if narrowing is applied after approval issuance. Approval binds to the effective narrowed profile: the effective profile must be the approval-bound profile.

## Deferred families: any material missing customer capability?

Assessed against the manifest's benefit levels and the lane source reads. None creates a concrete justification to expand the initial profile; each is recorded with the capability it leaves unavailable.

| Family | Rows (disposition) | Benefit | Assessment |
|---|---|---|---|
| F1d target scope | 2 UNRESOLVED | LOW / NONE | The only candidate for a real gap ("cannot centrally govern target prefixes"). Needs a never-toward-`legacy-prefix` mode-ordering ruling (D4, D9, W1-029) and an oracle. Revisit first if a customer scenario requires target scoping. |
| F6 permissions | 1 CONDITIONAL, 1 UNRESOLVED | LOW / NONE | Only the unsupported legacy shell is file-driven; supported path uses grants. No gap. |
| F7 dedupe/funded authorities | 1 CONDITIONAL, 4 UNRESOLVED | LOW | Default-off operation identity is GAP-G1-01 (not a registry remedy). No registry gap. |
| F3 operational timeouts | 2 CONDITIONAL | LOW | Operational tunables. No governance need shown. |
| F4 identity/mandate ages, tolerance, extension, and the other F4 rows | 10 (5 CONDITIONAL, 5 UNRESOLVED, including the two extracted ages counted separately) | LOW | Same code shape; validate them in the same helper for near-zero cost (CP-PR-1) but do not extract. State in exclusions that central freshness covers status and approval only. |
| F5 `requires_revocation_assurance` | 1 CONDITIONAL | LOW | Needs the holder-inventory profile. |
| F8 tool lists | 1 UNRESOLVED (MEDIUM) | MEDIUM | `PolicyConfig.allowed_tools/blocked_tools` JSON file: unresolved, and the family is otherwise guardrail or not relevant. Revisit only with a scenario. |
| F9, F10 | guardrail / not relevant | NONE | None. |
| F11 redaction | 4 CONDITIONAL | LOW | Registry could only switch redaction on; low benefit; D1/W9-002 open. |

## The seven inventory errata (reconciled against the merged inventory)

The P1 source reads found these seven discrepancies against the first-draft manifest. The merged inventory is closed and accepted and is not edited by this plan. None changes a disposition or the V1 scope. They are carried here as errata for the owning component PRs and for the independent oracle author, who must read the source rather than rely on the manifest wording. Where a merged row already states the corrected fact, that is noted in [10](10-architect-rulings-and-repin.md).

1. RT-F1c rows describe `__post_init__` as validating every `LocalExecutionPolicy` field. `max_amount` and `max_effects` are validated in `check` (`:411-412`); a bad ceiling raises `ValueError` ahead of every other reason.
2. RT-F1b: with a `runtime_authority_profile`, Route A takes trusted institution and domain from the host manifest action (`control_plane_adapter.py:247-252`), not the resolver; `reconcile()` copies them from the snapshot (`:429-432`).
3. CP-F5-01 clause (b) "met on `ge=0`" is overstated: `ge=0` admits 0 and pydantic lax-coercion accepted `"60"`, `60.0`, `True` and `10**30` (probe at pydantic 2.13.5); clause (b) is only partly met and is closed by the helper.
4. CP-F4-04/07 cite a qualification-repo test. No Control Plane test at the pin passes the age kwargs, and no test exists for `conflict_status_stale_or_future` or `policy_status_stale_or_future`.
5. The F4 rows omit the failure modes of unvalidated constructor values.
6. Runtime copies the age attributes into its per-call view (`control_plane_adapter.py:340-343`) and forwards the profile snapshot (`:193-205`) but no new constructor kwarg; narrowing must therefore be applied to the attributes or profile before construction.
7. At the Runtime pin, tests isolate only unit, amount and action (`tests/test_route_a_local_policy_reason.py`); institution, domain and adapter coverage exists only in the qualification repo (existence only, not run).

Deferred-family and `max_amount` assessment is unchanged by the scope approval: no scenario in the merged inventory justifies expanding the V1 profile.

Task traceability: every PR in [06](06-pr-and-sprint-execution-plan.md) names the field IDs above and the scenario IDs or governance contracts it serves.
