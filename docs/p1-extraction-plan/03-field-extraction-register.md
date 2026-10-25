# 3. Configuration-field extraction register

Status: planning only; **scope approved: exactly eight V1 fields** ([09](09-operator-scope-decision.md)). The manifest is `docs/registry-v1-scope-assessment/data/configuration-extraction-manifest.jsonl` of `cogno-us/cognous-stack-qualification` PR #227, **merged** at `be1994a961e4e40612d999972ede6547a3729887` (final PR head `1b34db3442c70701d6ffad67db94a49492b1827b`). Each field row below was re-read against source at the exact pins (Runtime `c5e97e87`, Control Plane `7a4bcd40`); no repository test was run. Benefit and complexity levels are the manifest's reasoned inference, not demand data.

## Provenance of the 96-row inventory (preserved)

| Revision | Role |
|---|---|
| PR #227 head `64b4942b4c3cd142db26482af85cbaec024aa043` | The head this plan's first draft analysed (manifest sha256 `3938c5f9…`). Retained as the original analytical provenance. |
| PR #227 head `a2718f30` | Intermediate head (routine Copilot repairs). Manifest, acceptance matrix and crosswalk were byte-identical to `64b4942b`. |
| PR #227 final head `1b34db3442c70701d6ffad67db94a49492b1827b` | Applies the Architect's duplicate-field ruling (Option B). Manifest sha256 `e1ce9f97…`. |
| Merge commit `be1994a961e4e40612d999972ede6547a3729887` | **Baseline for this plan.** The merge changes only the 49 files of `docs/registry-v1-scope-assessment/`. |

Reconciliation of the manifest between `64b4942b` and the merge (compared row by row, 96 rows each, identical field IDs): every row gains two empty columns (`shared_underlying_field`, `duplicate_of`); one row changes disposition. `CP-F3-07` (`FreshnessProfile.lease_acquire_timeout_seconds`) and `CP-F4-13` describe one underlying field; both are now `UNRESOLVED`, `CP-F4-13` governs, and the field counts once. **None of the eight V1 fields and none of the deferred `max_amount` rows changed.** Source identities were not replaced: every cited source pin remains the one the manifest row carries.

## Manifest totals at the merge commit (96 rows; 24 Runtime, 72 Control Plane)

| Disposition | Rows | Rows at `64b4942b` | Treatment in this plan |
|---|---|---|---|
| `DIRECT_EXTRACTION` | 5 | 5 | All five are V1 |
| `CONDITIONAL_EXTRACTION` | 17 | 18 | Three are V1 (F4 two ages, F5 one age); `max_amount` is a deferred extension; thirteen deferred |
| `UNRESOLVED` | 16 | 15 | Not extracted; each stays unresolved until its source finding decides it |
| `CODE_OWNED_GUARDRAIL` | 47 | 47 | Stay code; listed so nothing adjacent is silently dropped |
| `NOT_RELEVANT_TO_V1` | 11 | 11 | Not extracted |

**Exactly eight fields are V1** (five `DIRECT`, three `CONDITIONAL` whose conditions the Architect's rulings R1 to R6 resolve). No count of rows is a count of safe migratable fields.

## The eight V1 fields

Columns: scenarios are existing IDs from the crosswalk (not restated); "Rulings" are the binding Architect rulings that settle the field.

| # | Field ID | Field (source, units) | Evaluator and source | Manifest disposition | Benefit / complexity | Rulings | Existing scenarios (examples) | Extraction form |
|---|---|---|---|---|---|---|---|---|
| 1 | RT-F1a-01 | `allowed_actions` (frozenset of non-empty str) | `LocalExecutionPolicy.check` `safe_executor.py:419` | DIRECT | HIGH / LOW | R8, R10, R14 | C11, C02, TC-L06-003/011/013/014 | Set intersection with caller; empty = explicit deny-all |
| 2 | RT-F1a-02 | `allowed_adapters` | `check` `:417` | DIRECT | MEDIUM / LOW | same | C11, C02, TC-L06-003/009/011 | Same |
| 3 | RT-F1a-03 | `allowed_units` | `check` `:423` | DIRECT | MEDIUM / LOW | same | C11, TC-L06-011/014 | Same; no per-unit ceilings |
| 4 | RT-F1b-01 | `allowed_institutions` | `check` `:413` (first dimension) | DIRECT | MEDIUM / LOW | same | C11, D02, C18 | Same; the independent `_check_trusted_context` (`control_plane_adapter.py:87-92`) stays |
| 5 | RT-F1b-02 | `allowed_authority_domains` | `check` `:415` | DIRECT | MEDIUM / LOW | same | C11, D02, C18 | Same |
| 6 | CP-F4-04 | `status_max_age_seconds` (int seconds, default 60) | `bounded.py:1271`, consumers `:2445`, `:2469`, `:2398-2400` (profile-less only) | CONDITIONAL | MEDIUM / HIGH | R1, R2, R3, R4 | D03, TC-D09-009/016 | `min(caller, registry)` after strict validation; code-owned bounds ([04](04-component-ownership-and-adapter-matrix.md)) |
| 7 | CP-F4-07 | `approval_max_age_seconds` (int seconds, default 60) | `bounded.py:1274`, consumer `:2505`; not hashed into the approval commitment | CONDITIONAL | MEDIUM / HIGH | R1, R2, R3, R4 | H01, TC-L06-015, D03 | Same |
| 8 | CP-F5-01 | `ActionClass.max_status_age_seconds` (int seconds, default 60, `ge=0`) | `runtime_authority.py:87`; consumers `bounded.py:2394-2399`, `:2082-2088`, `:2163`, `runtime_authority.py:341` | CONDITIONAL | MEDIUM / HIGH | R1 to R6 | C01, TC-D09-016 | Per-class `min` on the profile before construction; approvals bind to the effective profile (R5); extension cannot widen (R6) |

F1a/F1b (rows 1 to 5) form one Runtime family of five sets; F4/F5 (rows 6 to 8) are the Control Plane family. Task traceability: every PR in [06](06-pr-and-sprint-execution-plan.md) names the field IDs above and the scenario IDs or governance contracts it serves.

## Deferred extension: `max_amount` (RT-F1c-01), outside V1 (R7)

`max_amount` is **not** a V1 field and has no V1 task, slot, constant or test in any card. Its current code-owned enforcement is unchanged: the single, unit-less binary64 ceiling is validated inside `check` (`safe_executor.py:411`, `:425`), not in `__post_init__`; a bad ceiling raises `ValueError` before the institution check (Route A `observe` catches only `PermissionError`, so it escapes without `local_refusal`; Route B maps it to `local_policy_evaluation_error`). That behaviour is preserved, not changed, and is characterized only as an existing, untouched behaviour.

The D6 analysis is preserved here for a later profile; **no monetary encoding decision is made now (R7)**. Preserved analysis: the caller's value must stay authoritative (`min(caller, registry)`); the ceiling is unit-less, so central governance would be admissible only when the effective `allowed_units` after intersection is exactly one declared unit; a registry encoding such as `{unit, scale, value}` would have to convert to binary64 rounding down and refuse when it cannot represent exactly; a zero ceiling needs its own ruling. Any later extension needs separate scope approval, its own ADR and its own independent qualification (QG-02 is retained as DEFERRED, see [07](07-independent-qualification-matrix.md)).

## Semantics that matter (read at the pins; no repository test was run)

- **Runtime sets.** Each is `frozenset` of non-empty `str`, validated in `__post_init__` (`safe_executor.py:374-395`). **An empty frozenset is accepted** (verified by construction at `c5e97e87`) and means deny-all for that dimension; an omitted argument is a constructor `TypeError`, never an allow. The registry's pre-construction deny-all is therefore an **adapter contract, not constructor validation**. `check` order is fixed and first failure wins: ceiling validation, institution, domain, adapter, action, target, unit, amount, one effect, effect count. Exact membership; no case folding or wildcard. S03/S04 already cover the three F1a fields as intersection; **F1b is new** (S03 `supplies` is fixed at three, so F1b needs `r08-v2`).
- **Ages.** Plain Python `int` seconds everywhere in the Control Plane; no floats. Narrow-only holds mechanically: every consumer is monotone (a smaller bound refuses a superset). The caller value is unvalidated today (`inf` disables staleness on the no-profile path; `None`/`str`/`nan`/overflow crash `decide` rather than widen), so the host helper validates the caller value first and refuses, never clamps. Bounds and clock interactions are specified in [04](04-component-ownership-and-adapter-matrix.md) under R3.
- **F4 versus F5.** They never compete on one record. With a `RuntimeAuthorityProfile`, F5 owns grant status; F4 still owns conflict and policy status always, and grant status only without a profile. No cross-bound exists in code and none is added (R2). F4 ages are not extendable by outage extensions at all; only F5 class bounds are.
- **F5 approval coupling.** `approval_commitment` hashes the profile dump (`runtime_authority.py:186-194`). A narrowed profile changes it, so approvals issued under the caller profile fail with `runtime_authority_approval_mismatch` (`:268-271`): correct, fail closed (R5), but it looks like an outage if narrowing is applied after approval issuance. The effective profile must be the approval-bound profile.
- **`ObservationPolicy.max_age_seconds`** (the 300 s value) governs a different observed object and does not block F4 (R4, W6-042).

## Deferred families: any material missing customer capability?

Assessed against the manifest's benefit levels and the lane source reads. Deferral does not authorize weakening existing controls, and existing operation-identity and deduplication weaknesses stay independently tracked under their owning components. Deferred registry configuration is **not** absent OCS enforcement: each of these controls remains in code today.

| Family | Rows (disposition) | Benefit | Assessment |
|---|---|---|---|
| F1c `max_amount` | 1 CONDITIONAL (RT-F1c-01) | MEDIUM / HIGH | Deferred extension (R7); see above. Code enforcement retained |
| F1d target scope | 2 UNRESOLVED | LOW / NONE | The only candidate for a real gap ("cannot centrally govern target prefixes"). Needs a never-toward-`legacy-prefix` mode-ordering ruling and an oracle. Revisit first if a customer scenario requires target scoping |
| F6 permissions | 1 CONDITIONAL, 1 UNRESOLVED | LOW / NONE | Only the unsupported legacy shell is file-driven; supported path uses grants |
| F7 dedupe/funded authorities | 1 CONDITIONAL, 4 UNRESOLVED | LOW | Default-off operation identity is GAP-G1-01 (not a registry remedy, tracked under its owner) |
| F3 operational timeouts | 1 CONDITIONAL, 2 UNRESOLVED (one of them `CP-F3-07`, the duplicate of `CP-F4-13`) | LOW | Operational tunables; no governance need shown |
| F4 identity/mandate ages, tolerance, extension and the other F4 rows | F4 has 7 CONDITIONAL (two are V1), 5 UNRESOLVED, 3 guardrail | LOW | Same code shape; the helper validates the clock tolerance in the same pass, but only status and approval are extracted. Central freshness covers status and approval only |
| F5 `requires_revocation_assurance` | 1 CONDITIONAL | LOW | Needs the holder-inventory profile |
| F8 tool lists | 1 UNRESOLVED (MEDIUM) | MEDIUM | Revisit only with a scenario |
| F9, F10 | guardrail / not relevant | NONE | None |
| F11 redaction | 4 CONDITIONAL | LOW | Registry could only switch redaction on; D1/W9-002 open |

## Manifest errata carried against PR #227 (seven; recorded here, not fixed in PR #227)

PR #227 was merged without these corrections to the manifest rows (the merged lane notes record other, separate discrepancies). They are plan-lane findings from source reads at the pins. They change no disposition of the eight V1 fields; they are carried so the manifest rows are not read as authority where source disagrees. **Source identities are unchanged; this plan does not edit the inventory.**

1. RT-F1c rows describe `__post_init__` as validating every `LocalExecutionPolicy` field. `max_amount` and `max_effects` are validated in `check` (`:411-412`); a bad ceiling raises `ValueError` ahead of every other reason.
2. RT-F1b: with a `runtime_authority_profile`, Route A takes trusted institution and domain from the host manifest action (`control_plane_adapter.py:247-252`), not the resolver; `reconcile()` copies them from the snapshot (`:429-432`).
3. CP-F5-01 clause (b) "met on `ge=0`" is overstated: `ge=0` admits 0 and pydantic lax-coercion accepted `"60"`, `60.0`, `True` and `10**30` (probe at pydantic 2.13.5); clause (b) is only partly met and is closed by the strict-validation helper (R3).
4. CP-F4-04/07 cite a qualification-repo test. No Control Plane test at the pin passes the age kwargs, and no test exists for `conflict_status_stale_or_future` or `policy_status_stale_or_future`.
5. The F4 rows omit the failure modes of unvalidated constructor values (`inf`, huge ints, `bool`, `None`, `str`, negative tolerance).
6. Runtime copies the age attributes into its per-call view (`control_plane_adapter.py:340-343`) and forwards the profile snapshot (`:193-205`) but no new constructor kwarg; narrowing must therefore be applied to the attributes or profile before construction.
7. At the Runtime pin, tests isolate only unit, amount and action (`tests/test_route_a_local_policy_reason.py`); institution, domain and adapter coverage exists only in the qualification repo (existence only, not run).

Source pins to update when an implementation PR starts: Runtime and Control Plane heads move; the eight fields must be re-read at the new heads before any card is executed ([06](06-pr-and-sprint-execution-plan.md), "re-pin" rule).
