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
