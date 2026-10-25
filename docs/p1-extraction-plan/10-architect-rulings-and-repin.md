# 10. Architect rulings in force, re-pin record and inventory reconciliation

Status: planning only. This page records decisions the Architect has already made so that the other documents do not reopen them. It authorizes nothing. Planning approval (this plan), implementation authorization (a separate Architect act) and independent qualification (a designated lead) remain three different things. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

## Re-pin to the merged inventory

| Reference | Provisional (first draft of this plan) | Authoritative now |
|---|---|---|
| Inventory (qualification repo PR #227) | head `64b4942b4c3cd142db26482af85cbaec024aa043` (earlier handoff: `947db3d2`) | merge commit `be1994a961e4e40612d999972ede6547a3729887` (final PR head `1b34db3442c70701d6ffad67db94a49492b1827b`) |
| Manifest | 96 rows, 18 CONDITIONAL, 15 UNRESOLVED | 96 rows representing 95 distinct fields: DIRECT 5, CONDITIONAL 17, UNRESOLVED 16, CODE_OWNED_GUARDRAIL 47, NOT_RELEVANT_TO_V1 11 |
| Model counts | Model B 23, B-only 14 (first-draft arithmetic) | Model A 9, Model B 22, Model B-only 13 (eligible-field counts, not qualification results) |

Historical pins are retained only for provenance. Canonical files used by P1: `docs/registry-v1-scope-assessment/09-configuration-extraction-handoff.md` and `docs/registry-v1-scope-assessment/data/configuration-extraction-manifest.{jsonl,csv}` at the merge commit. Verified by the Architect and in the merged package: 32/32 validation checks, required CI 8/8 green, 696 canonical scenarios, 162 suite-local claims recorded separately, evidence statuses unchanged, no independent qualification claimed. This plan does not repeat the inventory.

**Duplicate-field accounting.** CP-F3-07 and CP-F4-13 are two inventory rows for `FreshnessProfile.lease_acquire_timeout_seconds`. Both are UNRESOLVED, both rows are kept with their own family, CP-F4-13 governs, the field is counted once and it is excluded from Model B. It is not a V1 field.

## Approved V1 scope (operator; not reopened)

Option B, eight configurable fields, atomic Route B only. Runtime: `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`. Control Plane: `status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds`. `max_amount` is deferred. Everything else proposed stays outside the V1 implementation profile unless separately authorized. Existing code-owned enforcement and guardrails are preserved.

## Technical rulings in force

The Architect's directive of 2026-10-25 lists the rulings below (the Architect numbers them R1 to R14; they are quoted here by content and are not reopened).

| Item | Ruling | Where it lands |
|---|---|---|
| 1 | Age ceilings compose through validated per-scalar `min` | [03](03-field-extraction-register.md), `EXT-S1-4`, `EXT-S3-2` |
| 2 | Strict integer seconds; no universal five-second floor | `EXT-S1-4`, `EXT-S3-2`, risk 17 |
| 3 | No artificial cross-bound among the distinct F4 ages | [03](03-field-extraction-register.md) |
| 4 | Approval binds to the effective narrowed profile | `EXT-S3-4`, QG-04 |
| 5 | Outage extensions cannot widen registry limits | `EXT-S3-4`, risk 15 |
| 6 | `r08-v2` preserves `r08-v1` behaviour (additive, golden outputs byte-identical) | `EXT-S1-1`, `EXT-S1-3` |
| 7 | The Ed25519 adapter remains outside the core | `EXT-S1-7` |
| 8 | All 46 registry outcomes require safe mappings | `EXT-S1-5` completeness test |
| 9 | Claim-carried effective-policy identity is mandatory | `EXT-S4-0`, `EXT-S4-4` |
| 10 | B-lite keyword-argument carriage is rejected | [04](04-component-ownership-and-adapter-matrix.md) decision 2 |
| 11 | `EXT-S4-4` is mandatory (Control Plane change; both repositories re-pin) | [06](06-pr-and-sprint-execution-plan.md), `EXT-S4-5` |
| 12 | Commit-time revocation, expiry and epoch checks remain essential | `EXT-S4-2`, QG-08, QG-09 |
| 13 | The emulator host belongs to the registry, not the qualification repo | `EXT-S4-3` |
| 14 | Durable selection state requires custody and anti-rollback qualification | `EXT-S4-0`, `EXT-S4-2`, risk 6 |
| 15 | `engine/safe_executor.py` remains unchanged | all Runtime PRs; blob `2fc880da` |
| 16 | The Runtime accepts empty frozensets; preconstruction deny-all is an adapter convention | [04](04-component-ownership-and-adapter-matrix.md) decision 4 |

## The seven inventory errata (status)

All seven were found against the first-draft manifest by the P1 source reads at Runtime `c5e97e87` and Control Plane `7a4bcd40`. The merged inventory is closed; none of them changes a disposition or the V1 scope. Full text is in [03](03-field-extraction-register.md).

| # | Erratum | Status against the merged manifest |
|---|---|---|
| 1 | `max_amount` and `max_effects` are validated in `check`, not `__post_init__` | The merged RT-F1c-01 guardrail text already places re-validation in `check`; no action |
| 2 | Trusted institution and domain come from the host manifest action on Route A | Carried as an erratum for `EXT-S2-1` |
| 3 | CP-F5-01 clause (b) "met on `ge=0`" is overstated (pydantic lax coercion) | Carried as an erratum; closed by the `age_bounds` helper (`EXT-S3-2`) |
| 4 | CP-F4-04/07 cite a qualification-repo test; no Control Plane test passes the age kwargs | Carried as an erratum; closed by `EXT-S3-1` |
| 5 | F4 rows omit the failure modes of unvalidated constructor values | Carried as an erratum; closed by `EXT-S3-2` |
| 6 | Runtime copies the age attributes into its per-call view and forwards the profile snapshot, but no new kwarg | The merged CP-F4 rows already note the Runtime copy; narrowing stays before construction |
| 7 | Runtime tests isolate only unit, amount and action; institution, domain and adapter coverage exists only in the qualification repo | Carried as an erratum; closed by `EXT-S2-1` |

## Existing scenario and evidence limitations (unchanged)

`PASS_RECORDED` means a named historical case at the g8-r10 pins, not at the current heads; the scenario rows stay INCONCLUSIVE. Known-limit assertions are not PASS. D01, D03 and D04 stay INCONCLUSIVE. Collection is not execution. No independent Tier 1 qualification is claimed; qualification stays PREPARE-only until a lead is designated, and Copilot review is technical review, not qualification.
