# M2 — Implementation blueprint (smallest required change)

Status: PROPOSAL. No production code is written or authorized. Paths are from the pinned sources (Registry `2afbd8c`, Runtime `0dde0ef`, Control Plane `d66ae07`, SQ `bb9b089`).

## Registry (cogno-us/cognous-ocs-registry) — REQUIRED

| Change | Where | Notes |
|---|---|---|
| Successor family module | new `registry_successor/v3_f1c.py` | payload validator (exact keys, `type is int`, ranges), caller normalizer, `compose_f1c` (`min`, deny-all on record `max_effects = 0`), pattern of `v2_age_bounds.py` |
| Record validation / signing for `r08-v3` | new v3 entry points beside the v2 ones | new signing domain; v2 entry points keep hardwired `r08-v2` |
| Family table | `families.py`: add `table_for_contract_version("r08-v3")` | v1/v2 tables untouched |
| Policy identity | `v2_policy_identity.py` pattern, new v3 row | identity preimage over canonical ints |
| Signed selection | selection record carries family `f1c-local-execution-ceilings` | per `registry_successor` selection rules |
| Reason codes | none expected | reuse existing sets; do not edit CODES / CODES_V2 / CODES_V2_REV2 |
| Negative vectors | new vector file for v3 (see `04`) | no edit to v2 vectors |

Unchanged: all `r08-v1`/`r08-v2` modules, vectors and docs; `v2_f1ab.py`, `v2_age_bounds.py`; G0/G1 records.

## Control Plane (cogno-us/cognous-control-plane) — REQUIRED ONLY IF NECESSARY

Expected: **no change**. Its source holds no f1ab/family constants; the policy binding carries one `family` and an `effective_policy_digest` as opaque values; the authorization identity (pin export) is preserved. Required only if **[D-1]** picks a standalone family needing a second binding, or **[D-6]** finds a family allow-list. No new grant authority in either case.

## Execution Runtime (cogno-us/cognous-execution-runtime) — REQUIRED

| Change | Where | Notes |
|---|---|---|
| Family-aware selection store | `engine/registry_selection_authority.py`: replace the hardcoded `FAMILY_F1AB` at the activation validation, `record_policy_digest`, `_check_policy_containment`, `policy_digest_of` / `policy_sets_of` / `sa_fields` sites | behaviour for f1ab identical; add f1c path |
| Ceiling application | `engine/registry_f1a_narrowing.py` (`evaluate_with_registry_selection`): apply composed ceilings, then call the unchanged evaluator | effective = min of caller, registry and grant/claim limits |
| Effect-time guard | `registry_selection_authority.check_effect` (containment inside `BEGIN IMMEDIATE`): add direct record checks, `op.amount ≤ record.max_amount`, `claim.max_effects ≤ record.max_effects`, executor-reported ceilings ≤ record | revalidation at effect time; fail closed |
| Refusal / evidence | existing refusal and evidence paths | no effect dispatched, ledger unchanged on refusal |
| Pin | Runtime pin to the Registry commit carrying `r08-v3` | installer/guard unchanged otherwise |

Unchanged: `safe_executor.LocalExecutionPolicy` and `check` (protected evaluator, `_strict_positive_int`, `_strict_finite_number`), `local_authority_effect` ledger logic, `effect_budgets_v1`.

## Stack Qualification — REQUIRED (qualification, not code)

Differential test of the composed policy against baseline `LocalExecutionPolicy` for the two ceilings; independent Tier 1 qualification before acceptance (not performed by the builder).

## PR sequence once authorized

1. Registry: `r08-v3` family, validation, composition, identity, vectors, tests.
2. Runtime: family-aware selection store (f1ab behaviour byte-identical, proven by existing tests).
3. Runtime: ceiling application and effect-time guard, tests from `04`.
4. Control Plane: only if [D-1]/[D-6] require it.
5. SQ: differential and cross-component run; independent qualification.
