# r08-v2 implementation notes (EXT-S1-2: family dispatch foundation)

Status: **IMPLEMENTED / DEVELOPER-TESTED, not independently qualified.** Builder self-run evidence only; no Architect or independent verdict. RELEASE, PUBLICATION and PRODUCTION: HOLD. Governing documents: [`docs/r08-v2-contract.md`](r08-v2-contract.md) (canonical, binding), [ADR EXT-S1-1](decisions/2026-10-25-adr-ext-s1-1-v1-contract.md) (D-09, D-10, D-02, O-2), card `EXT-S1-2` in [`p1-extraction-plan/11-ext-pr-execution-cards.md`](p1-extraction-plan/11-ext-pr-execution-cards.md).

## What this package does

A behaviour-preserving refactor. It introduces the family dispatch table and declares `CODES_V2`. It adds no family, no v2 document shape, no v2 entry point and no new behaviour.

| Item | File | Notes |
|---|---|---|
| Dispatch table | `registry_successor/families.py` | `family -> (payload validator, composer, evaluator binding, caller normalizer, enforcing component)`; read-only (`MappingProxyType`); `lookup()` is exact string equality and never raises; `compose()` dispatches on the validated record's family in the `r08-v1` check order (operator, record validity, family registration, composer). |
| Registered families | same | `f1a-local-execution-allowlist` only (enforcing component `runtime`). `f1ab`, `f4`, `f5` are NOT registered (EXT-S1-3, EXT-S1-4). |
| Consumers of the table | `record.py`, `selection.py`, `decision.py` | The hard-coded `c.FAMILY_F1A` / `c.F1A_FIELDS` / evaluator-constant comparisons now read the table. Messages, codes, check order and outputs are unchanged. `common.py`, `compose.py`, `verify.py` are unchanged (the F1a constants and composer are the F1a table entry). |
| `CODES_V2` | `registry_successor/v2_codes.py` | The 46 `r08-v1` entries (taken from `common.CODES`, one definition) plus `trust_snapshot_version_stale` (layer `trust`) and `selection_withdrawn` (layer `disposition`) = 48; read-only. `common.CODES` is unchanged (46). Declared only: nothing emits either new code. |

An unregistered family refuses `family_unsupported` at record and selection parse and `composition_family_unsupported` at composition; a different case, surrounding whitespace, a non-string or an unhashable value is simply not registered. A refusal never carries a policy, so a required operation never returns the caller policy through the table (decision layer unchanged: `required_policy_unavailable`, `effective=None`, `caller_unchanged=False`).

One frozen-v1 detail is kept deliberately: when an optional operation refuses before a registered family is known (for example an unregistered family in the selection), the unchanged v1 entry point still normalizes the caller policy with the F1a normalizer (`families.V1_DEFAULT_FAMILY`). The v1 goldens pin this; it is not a default for later families.

## v1 byte-identity proof (ADR D-09)

- `tests/golden/r08_v1_golden.json` (sha256 `2080382903dbf80ebc739513c5a2b23dba38bbb1efc97231928af898305ddded`) holds 5194 cases (record, selection, verify, decide, compose, compose on hand-built record results, resolve, resolve_authoritative), including family case/whitespace/Unicode variants, mutated shapes and digests, a trust, verifier, time and caller grid, and the exhaustive 3x3 per-dimension composition grid. It reaches all 46 `CODES`. It was captured by `tests/golden/capture_v1_goldens.py` from the **unrefactored** head `07fe993` in the first commit of the PR, before any `registry_successor` edit. Regenerating it to obtain a pass is forbidden; a replay diff stops the PR.
- `tests/test_r08v2_golden_replay.py` replays every case through the public interfaces and compares canonical JSON bytes.
- `tests/test_r08v2_family_dispatch.py` adds: table shape and read-only checks, variant lookups, unregistered-family refusals end to end, F1a through the table equals the stored pre-refactor `compose_f1a` outputs, the required-never-returns-caller property over every required golden decision, v1/v2 contract-version and signing-domain separation, `CODES_V2` declaration, and scope guards (no `max_amount`, no v2 behaviour for the two new codes, no forbidden imports).
- Builder-run extra differential (not committed): 30000 seeded structural and character mutations of the corpus run through `verify_and_decide`, `validate_record_text` and `parse_selection_envelope` on the `07fe993` tree and on this branch gave an identical SHA-256 of all outputs.

## Not done here

No F1ab/F4/F5 family, no v2 statement shape or `disposition` layer, no `selection_withdrawn` or snapshot-floor behaviour, no identity object or code-disposition map, no adapters, no Ed25519, no Runtime or Control Plane change, no `max_amount` slot. `registry_contract/`, `registry_consumer/`, `baseline/` and existing tests are untouched.

# EXT-S1-3: `f1ab-local-execution-allowlist` five-set family

Status: **IMPLEMENTED / BUILDER_TESTED, not independently qualified.** No claim of independent qualification, Architect verdict or release. RELEASE, PUBLICATION and PRODUCTION: HOLD. Governing text (pinned by sha256 in `tests/test_r08v2_f1ab_family.py`): `docs/r08-v2-contract.md` section 2, ADR EXT-S1-1 D-10 and D-11, card `EXT-S1-3`.

| Item | File | Notes |
|---|---|---|
| Family module | `registry_successor/v2_f1ab.py` | Payload validator, caller normalizer and `compose_f1ab` for exactly `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`. |
| Registration | `registry_successor/families.py` | New read-only `FAMILIES_V2` (= v1 table plus `f1ab`), `lookup_v2`, `compose_v2`, and the version selector `table_for_contract_version`, `lookup_for`, `compose_for`. `FAMILIES`, `lookup`, `compose` and every v1 entry point are unchanged. |
| Tests | `tests/test_r08v2_f1ab_family.py`, `tests/test_r08v2_version_dispatch.py` | Source-pinned, BUILDER_TESTED. |

Behaviour: an absent key refuses `field_missing`, any sixth key (including any amount or age key) `field_unknown`, an empty list is an explicit deny-all for that dimension (all 32 combinations tested), lists must be plain, sorted, duplicate-free, at most 256 entries of 1..128 valid characters without `*`, exact-string matching. Composition is caller INTERSECTION registry per key; any refusal returns no effective policy and never the caller policy; no Runtime policy is ever constructed. A missing, extra, non-list or malformed caller key refuses `composition_caller_invalid` and is never replaced.

Rulings applied and judgement calls (prefer fail-closed):

- **Separate v2 table.** The frozen v1 golden pins that a v1 entry point refuses `f1ab` `family_unsupported`, so `f1ab` is registered only in `FAMILIES_V2`. The selector `families.table_for_contract_version(version)` maps exactly the string `r08-v1` to `FAMILIES` and exactly `r08-v2` to `FAMILIES_V2` (exact `str` type; `CONTRACT_V1` is `common.CONTRACT_VERSION`, `CONTRACT_V2` is declared beside it). Anything else (None, bytes, str subclass, case or whitespace variant, `r08-v3`, empty, non-str) returns a `TableSelection` with `ok=False`, code `contract_unsupported` and no table: no fallback, no implicit upgrade or downgrade, no reinterpretation of a payload under another version's table. `lookup_for(version, family)` returns None and `compose_for(version, caller, record, operator)` refuses `contract_unsupported` (no policy) for an unsupported version. The v2 statement shape and v2 record/selection entry points (EXT-S1-5/6) do not exist yet; they must call this selector, and `f1ab` is otherwise reachable only through `compose_v2`/`compose_for` and the spec's validators. The v1 decision path therefore still refuses an `f1ab` record (required: no policy; optional: caller unchanged as `overlay_not_applied`).
- **Payload entries.** All five lists keep the contract section 2 opaque-token rule (plain `str`, 1..128, no control, separator or `*`, exact-string matching). The V1 ASCII identifier grammar is not applied to payload entries; per the Architect it applies only to the canonical policy-binding identifier fields (EXT-S1-5, contract section 4.1). All entries must be plain `str`.
- **Optional fallback is not decided here.** Whether an omitted binding may fall back to the caller policy needs an authenticated, valid optional-state determination owned by the enforcing consumer (contract sections 4.3 and 7.4, EXT-S4-2). This module returns no fallback.

Not done: no v2 statement shape, no `r08-v2` record/selection entry point, no identity object, no `max_amount` or age slot (EXT-S1-4), no Runtime or Control Plane change, no evaluator rewrite. The `r08-v1` golden replay is unchanged and passes.
