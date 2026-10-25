# 3. Configuration-field extraction register

Status: planning only. The manifest is **PR #227 head `64b4942b`, unmerged, not adopted** (`docs/registry-v1-scope-assessment/data/configuration-extraction-manifest.jsonl`, 96 rows). Each of the nine rows below was re-read against source at the exact pins (Runtime `c5e97e87`, Control Plane `7a4bcd40`); no repository test was run. Benefit and complexity levels are the manifest's reasoned inference, not demand data.

## Manifest totals (96 rows)

| Disposition | Rows | Treatment in this plan |
|---|---|---|
| `DIRECT_EXTRACTION` | 5 | All five mandatory |
| `CONDITIONAL_EXTRACTION` | 18 | Four proposed (below); fourteen deferred |
| `UNRESOLVED` | 15 | Not extracted; each stays unresolved until its source finding decides it |
| `CODE_OWNED_GUARDRAIL` | 47 | Stay code; listed so nothing adjacent is silently dropped |
| `NOT_RELEVANT_TO_V1` | 11 | Not extracted |

Total configurable fields proposed for extraction: **9** (5 mandatory, 4 conditional). Recommended V1 acceptance scope: **8** (all but `max_amount`). No count of rows is a count of safe migratable fields.

## The nine proposed fields

Columns: scenarios are existing IDs from the crosswalk (not restated); "Decisions" are the named rulings that gate the field.

| # | Field ID | Field (source, units) | Evaluator and source | Disposition | Benefit / complexity | Decisions | Existing scenarios (examples) | Extraction form |
|---|---|---|---|---|---|---|---|---|
| 1 | RT-F1a-01 | `allowed_actions` (frozenset of non-empty str) | `LocalExecutionPolicy.check` `safe_executor.py:419` | DIRECT | HIGH / LOW | none | C11, C02, TC-L06-003/011/013/014 | Set intersection with caller; empty = explicit deny-all |
| 2 | RT-F1a-02 | `allowed_adapters` | `check` `:417` | DIRECT | MEDIUM / LOW | none | C11, C02, TC-L06-003/009/011 | Same |
| 3 | RT-F1a-03 | `allowed_units` | `check` `:423` | DIRECT | MEDIUM / LOW | none | C11, TC-L06-011/014 | Same; do not add per-unit ceilings |
| 4 | RT-F1b-01 | `allowed_institutions` | `check` `:413` (first dimension) | DIRECT | MEDIUM / LOW | none | C11, D02, C18 | Same; independent `_check_trusted_context` (`control_plane_adapter.py:87-92`) stays |
| 5 | RT-F1b-02 | `allowed_authority_domains` | `check` `:415` | DIRECT | MEDIUM / LOW | none | C11, D02, C18 | Same |
| 6 | RT-F1c-01 | `max_amount` (single unit-less binary64 ceiling, inclusive) | `check` `:411`, `:425` | CONDITIONAL | MEDIUM / HIGH | D4, D6, encoding (G3) | C11, TC-L06-014 | `min(caller, registry)`, single declared unit only; see [04](04-component-ownership-and-adapter-matrix.md) |
| 7 | CP-F4-04 | `status_max_age_seconds` (int seconds, default 60) | `bounded.py:1271`, consumers `:2445`, `:2469`, `:2398-2400` (profile-less only) | CONDITIONAL | MEDIUM / HIGH | D4, W6-042 | D03, TC-D09-009/016 | `min(caller, registry)` per scalar, code floor >= 1, strict int |
| 8 | CP-F4-07 | `approval_max_age_seconds` (int seconds, default 60) | `bounded.py:1274`, consumer `:2505`; not hashed into the approval commitment | CONDITIONAL | MEDIUM / HIGH | D4, W6-042 | H01, TC-L06-015, D03 | Same |
| 9 | CP-F5-01 | `ActionClass.max_status_age_seconds` (int seconds, default 60, `ge=0`) | `runtime_authority.py:87`; consumers `bounded.py:2394-2399`, `:2082-2088`, `:2163`, `runtime_authority.py:341` | CONDITIONAL | MEDIUM / HIGH | D4, W6-042, W8-014 | C01, TC-D09-016 | Per-class `min` on the profile before construction; serialized after F4 |

### Semantics that matter (read at the pins; no repository test was run)

- **Runtime sets.** Each is `frozenset` of non-empty `str`, validated in `__post_init__` (`safe_executor.py:374-395`). An empty set is accepted and means deny-all for that dimension; an omitted argument is a constructor `TypeError`, never an allow. `check` order is fixed and first failure wins: ceiling validation, institution, domain, adapter, action, target, unit, amount, one effect, effect count. Exact membership; no case folding or wildcard. S03/S04 already cover the three F1a fields as intersection; **F1b is new** (S03 `supplies` is fixed at three, so F1b needs a new contract version).
- **`max_amount`.** Validated inside `check` (`:411`), not `__post_init__`. A bad ceiling raises `ValueError` before the institution check: Route A `observe` catches only `PermissionError`, so it escapes without `local_refusal`; Route B maps it to `local_policy_evaluation_error`. That behaviour is preserved, not changed.
- **Ages.** Plain Python `int` seconds everywhere in the Control Plane; no floats. Narrow-only holds mechanically: every consumer is monotone (a smaller bound refuses a superset). The caller value is unvalidated today (`inf` disables staleness on the no-profile path; `None`/`str`/`nan`/overflow crash `decide` rather than widen), so the helper validates the caller value first and refuses, never clamps. A bound of 0 is a de facto deny-all, so a code floor of at least 1 is required (the exact number is the Control Plane owner's proposal, at least the workflow clock tolerance of 5).
- **F4 versus F5.** They never compete on one record. With a `RuntimeAuthorityProfile`, F5 owns grant status; F4 still owns conflict and policy status always, and grant status only without a profile. No cross-bound exists in code; the recommended ruling is "none required".
- **F5 approval coupling.** `approval_commitment` hashes the profile dump (`runtime_authority.py:186-194`). A narrowed profile changes it, so approvals issued under the caller profile fail with `runtime_authority_approval_mismatch` (`:268-271`): correct, fail closed, but it looks like an outage if narrowing is applied after approval issuance. The effective profile must be the approval-bound profile.

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

## Manifest corrections to carry back (errata for PR #227, not fixed here)

The lane source reads found these discrepancies. They change no disposition, but the manifest rows should be corrected before the manifest is adopted.

1. RT-F1c rows describe `__post_init__` as validating every `LocalExecutionPolicy` field. `max_amount` and `max_effects` are validated in `check` (`:411-412`); a bad ceiling raises `ValueError` ahead of every other reason.
2. RT-F1b: with a `runtime_authority_profile`, Route A takes trusted institution and domain from the host manifest action (`control_plane_adapter.py:247-252`), not the resolver; `reconcile()` copies them from the snapshot (`:429-432`).
3. CP-F5-01 clause (b) "met on `ge=0`" is overstated: `ge=0` admits 0 and pydantic lax-coercion accepted `"60"`, `60.0`, `True` and `10**30` (probe at pydantic 2.13.5); clause (b) is only partly met and is closed by the helper.
4. CP-F4-04/07 cite a qualification-repo test. No Control Plane test at the pin passes the age kwargs, and no test exists for `conflict_status_stale_or_future` or `policy_status_stale_or_future`.
5. The F4 rows omit the failure modes of unvalidated constructor values.
6. Runtime copies the age attributes into its per-call view (`control_plane_adapter.py:340-343`) and forwards the profile snapshot (`:193-205`) but no new constructor kwarg; narrowing must therefore be applied to the attributes or profile before construction.
7. At the Runtime pin, tests isolate only unit, amount and action (`tests/test_route_a_local_policy_reason.py`); institution, domain and adapter coverage exists only in the qualification repo (existence only, not run).

Task traceability: every PR in [06](06-pr-and-sprint-execution-plan.md) names the field IDs above and the scenario IDs or governance contracts it serves.
