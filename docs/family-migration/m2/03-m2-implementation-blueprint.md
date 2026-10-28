# M2 — Implementation blueprint (corrected)

Status: PROPOSAL. No production code is written or authorized. Paths are from the pinned sources (Registry `2afbd8c`, Runtime `0dde0ef`, Control Plane `d66ae07`, SQ `bb9b089`). Architecture: composite `f1abc-local-execution-limits` (see `02`).

## Registry (cogno-us/cognous-ocs-registry) — REQUIRED

| Change | Where |
|---|---|
| Composite family module | new `registry_successor/v3_f1abc.py`: payload validator (five sets via the f1ab validators by import; two ceilings per `02` §4), caller normalizer (`02` §5, float refused), `compose_f1abc` (f1ab set composition unchanged + `min` ceilings; `deny_all` on empty set or `max_effects = 0`) |
| Contract `r08-v3` entry points | new v3 record validation, signing-domain constant, `verify_and_decide_v3`; v2 entry points remain hardwired to `r08-v2` |
| Family table | `families.table_for_contract_version("r08-v3")` returns a table with the one family |
| Policy identity | v3 identity row over seven members (pattern of `v2_policy_identity`) |
| Reason codes | none added; CODES / CODES_V2 / CODES_V2_REV2 untouched |
| Vectors | new v3 vector file (see `04`); no edit of v2 vectors |

Unchanged: all `r08-v1`/`r08-v2` modules, vectors and docs; `v2_f1ab.py`, `v2_age_bounds.py`; G0/G1 records.

## Control Plane — NO CODE CHANGE EXPECTED (D-6)

Source confirms the binding treats `family` as an identifier string and `effective_policy_digest` as an opaque sha256 (`canonical_policy_binding.IDENTIFIERS`, `DIGESTS`, `_IDENTIFIER` pattern); `f1abc-local-execution-limits` is valid. The CP reads no f1ab constants; the claim carries one `policy_binding`. Minimum compatibility requirements: (1) the existing binding profile `ocs-policy-binding/1` is reused; (2) after cutover the CP issues bindings with the new family. Residual: the profile's digest-domain constant `ocs-reg/r08-v2/policy-binding` is a CP-owned label; if the Architect requires a v3 label the minimum change is one new profile/domain constant. No new grant authority.

## Execution Runtime — REQUIRED

| Change | Where | Notes |
|---|---|---|
| Family-aware selection store | `engine/registry_selection_authority.py`: the hardcoded `FAMILY_F1AB` at activation validation (~1258), `record_policy_digest` (~876, ~1312), `_check_policy_containment` (~1451–1478), `policy_digest_of` / `sa_fields` (~1562–1587) | f1ab behaviour byte-identical; f1abc field list is the 5 sets + 2 ceilings; verification dispatches to `verify_and_decide_v3` for r08-v3 records |
| Coexistence rule | activation validation | refuse `f1abc` activation while an `active` f1ab row exists for the same five scope fields (and the reverse); require `participation = required` for f1abc so the ratchet refuses unbound claims |
| Ceiling application | `engine/registry_f1a_narrowing.py` (new f1abc path beside `evaluate_with_registry_selection`) | build the narrowed policy with `dataclasses.replace` setting the five sets and the two ceilings to the composed values; the unchanged evaluator `check` decides; no policy built on `deny_all` |
| Effect-time guard | `check_effect(... , policy_effective_ceilings=...)` (new optional argument beside `policy_effective_sets`), plumbed from `local_authority_effect._selection_guard` and `execute_claim_atomic` | inside the existing `BEGIN IMMEDIATE`: executor ceilings ≤ record; `float(claim.amount) ≤ record max_amount`; `claim.max_effects ≤ record max_effects`; one digest over all seven members must equal the binding digest |
| Evidence / refusal | existing `SelectionRefusal` paths | refusal before the effect insert; ledger untouched |
| Pin | Runtime pin to the Registry commit carrying `r08-v3` | |

Unchanged (retained): `safe_executor.LocalExecutionPolicy` and `check`, `_strict_positive_int`, `_strict_finite_number`, `validate_snapshot`; `local_authority_effect` budget registration, `claim.max_effects` equality, `used_effects` increment; `DurableRefundDestination` per-grant count; `control_plane_adapter` equality checks.

## Effect-count semantics (Correction 3): enforcement map

| # | Concept | Exact existing enforcement point |
|---|---|---|
| 1 | Caller `max_effects` policy ceiling | `LocalExecutionPolicy.max_effects`, validated by `_strict_positive_int` and compared in `check()`: `op.effective_max_effects > max_effects` → `PermissionError("local effect-count restriction")`. Called from `SafeExecutor` (~890), `atomic_local_control_plane_executor` (~69), `control_plane_adapter` (~101) |
| 2 | Grant and authorization effect budgets | Control Plane `bounded.py`: `effective_max_effects = min(requirement.max_effects, grant.max_effects, action.effect_limits.max_effects)` (~2570); per-permission `proposal.effects > permission["max_effects"]` (~2680, ~2739). Claim `max_effects = current.effective_max_effects` (CP `local_authority_effect` ~541) |
| 3 | Operation `effective_max_effects` | `FrozenOperation.effective_max_effects`; must equal `claim.max_effects` (`local_authority_effect` ~738) and the decision binding (`control_plane_adapter` ~141, ~312) |
| 4 | Single-operation effect-count invariant | `op.effects == 1`: `validate_snapshot` (`exactly_one`) and `check()` ("supports exactly one effect") |
| 5 | Durable ledger consumption and remaining budget | `effect_budgets_v1(max_effects, used_effects)`: registered with `claim.max_effects` and required equal on re-registration (~447–450); checked and incremented inside `execute_claim_atomic` (`used_effects >= max_effects` refuses, ~1004–1009; `used_effects + 1`, ~1045). Synthetic destination also counts effects per grant (`safe_executor` ~813) |

How the Registry ceiling narrows, without replacing authority context or ledger: the Registry value only lowers the policy ceiling at point 1 (`effective max_effects = min(caller, registry)`), so an operation whose authorized `effective_max_effects` (point 3, itself already the minimum of point 2) exceeds it is refused whole; it is never clamped or rewritten. At effect time the same bound is re-asserted against the authenticated record (`claim.max_effects ≤ record.max_effects`). Points 2, 3, 4 and 5 are not modified. No double counting: the Registry value is not added to, subtracted from or compared with `used_effects`; remaining budget is still `claim.max_effects − used_effects`. No additional effect authority: the ceiling can only cause refusal; `op.effects == 1` is unchanged. `max_effects = 0` in a record is deny-all before any policy or claim is evaluated.

## Stack Qualification — REQUIRED (qualification)

Differential test of the f1abc-composed policy against baseline `LocalExecutionPolicy` (all seven fields); independent Tier 1 qualification before acceptance, not performed by the builder.

## PR sequence once authorized

1. Registry: `r08-v3` composite family, validation, composition, identity, vectors, tests (PR-1).
2. Runtime: family-aware selection store and coexistence rule, f1ab behaviour byte-identical.
3. Runtime: ceiling application and effect-time guard with the tests from `04`.
4. Control Plane: only if the digest-domain label must change (D-6).
5. SQ: differential and cross-component run; independent qualification.
