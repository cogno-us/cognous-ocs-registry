# EXT-S1-4: F4 and F5 integer-second age families

Status: **IMPLEMENTED / BUILDER_TESTED, not independently qualified.** No claim of independent qualification, Architect verdict or release. RELEASE, PUBLICATION and PRODUCTION: HOLD. Governing text (pinned by sha256 in `tests/test_ext_s1_4_age_slots.py`): `docs/r08-v2-contract.md` section 2, ADR EXT-S1-1 D-10, D-11, D-27, [DR-CP-AGE-1](../decisions/2026-10-25-dr-cp-age-1.md), card `EXT-S1-4`.

| Item | File | Notes |
|---|---|---|
| Family module | `registry_successor/v2_age_bounds.py` | Validators, caller normalizers and composers for F4 and F5. Pure; no Control Plane import. |
| Registration | `registry_successor/families.py` | `f4-control-plane-age-bounds` and `f5-action-class-age-bounds` added to `FAMILIES_V2` only (enforcing component `control-plane`). `FAMILIES`, v1 entry points and the v1 golden replay are untouched. |
| Range record | `docs/decisions/2026-10-25-dr-cp-age-1.md` | DR-CP-AGE-1: `AGE_MIN = 1`, `AGE_MAX = 2147483647` (technical representation ceiling, not an operational setting), with the source re-verification. |
| Evidence | `docs/ext-implementation/evidence/ext-s1-4-age-bound-probe.{py,out}` | Real Control Plane `decide()` probe at `7a4bcd40` (read-only; not part of the suite; never imported by registry code). |
| Tests | `tests/test_ext_s1_4_age_slots.py` | Boundary grids, min grids, key sets, mutation checks. Two f1ab test lines were relaxed (v2 table is now a superset; `f4` is no longer an unregistered v2 name). |

## Shapes

- F4 payload: exactly `status_max_age_seconds`, `approval_max_age_seconds`, each an exact `int` in `1..2147483647`. Caller policy: exactly the same two keys, each an exact `int` in `0..2147483647`. Effective: `{key: min(caller, registry)}`.
- F5 payload: exactly `class_status_max_age_seconds`, a non-empty object (at most 256 entries) `action_class -> int` with sorted keys, each key a `common.valid_token`, each value an exact `int` in `1..2147483647`. Caller policy: `{"class_status_max_age_seconds": {class: int 0..2147483647}}` (non-empty, at most 256, valid tokens). Effective: the caller's class map with each class present in the registry replaced by `min`; a caller class absent from the registry keeps the caller value; a registry class the caller does not define refuses.
- A registry value above the caller keeps the caller value; the result carries `detail = "registry_value_not_narrowing:<field or class names>"` and the result is still `ok`. `deny_all` is never set (a caller 0 stays 0; it is not the allowlist deny-all concept).
- Only operator `intersection` (the frozen dispatch name for narrowing) is accepted; anything else refuses `composition_operator_unsupported`.

## Refusal-code mapping (no code added; `CODES_V2` stays 48)

| Cause | Code |
|---|---|
| payload third key (including any amount, identity, mandate, tolerance or evidence-age key) | `field_unknown` |
| payload key absent | `field_missing` |
| payload value `bool`, float, str, None, bytes, int subclass, list, wrong container, non-str key | `field_type_invalid` |
| payload int below 1 or above `2147483647`; empty, oversized, unsorted or invalid-token class map | `field_invalid` |
| payload invalid at composition; registry class unknown to the caller | `composition_record_invalid` |
| invalid caller (key set, type, range 0..max, empty or oversized class map) | `composition_caller_invalid` |
| other family / varied family spelling | `composition_family_unsupported` |
| other operator | `composition_operator_unsupported` |

Gaps and judgement calls (all fail closed):

- No code distinguishes "registry class unknown to the caller" from an invalid record; it maps to `composition_record_invalid`. No code distinguishes "value above the ceiling" from "zero"; both are `field_invalid`.
- `registry_value_not_narrowing` is not a refusal code, so it is carried as the `detail` text of an accepted result. A consumer-side disposition vocabulary (EXT-S1-5) may promote it.
- F5 class keys: the contract gives no token rule for action classes, and the Control Plane only requires a non-empty `class_id`. The contract section 2 opaque-token rule (the same as the five-set lists) is applied; a class id longer than 128 characters or containing a separator, control character or `*` cannot be configured through the registry. Keys must be sorted (canonical-list convention) and the map is bounded at 256.
- The evaluator pin of an F4/F5 record is the existing `(EVALUATOR_ID, EVALUATOR_BINDING)` pair: the contract defines no Control Plane evaluator identity. EXT-S4 should define one if it wants a distinct pin.
- ADR D-27 and contract 2.1 still say `AGE_MAX` is pending; DR-CP-AGE-1 records the Architect's ruling that supersedes that wording (a separate docs-only amendment will record the versioned clarification). The merged ADR and contract are not edited.

## What the characterization does and does not establish

**Measured.** Control Plane source `cogno-us/cognous-control-plane@7a4bcd40b3b49e61ff3c294dcca53b52f460b22c`, real `BoundedAuthorizationWorkflow.decide()`, by `docs/ext-implementation/evidence/ext-s1-4-age-bound-probe.py` (output `ext-s1-4-age-bound-probe.out`; full table in [DR-CP-AGE-1](../decisions/2026-10-25-dr-cp-age-1.md)). Interpreter and platform: the probe output does not record them. The probe was re-run unchanged under CPython 3.13.17, Linux x86_64 (glibc 2.39), pydantic 2.13.5, and reproduced the previously committed `.out` byte for byte; it was then extended with the date and C-int cases below and the committed `.out` is the output of that extended run on the same interpreter, against a read-only, unmodified Control Plane checkout at the pin. That one interpreter and platform is the whole measured population.

- Three `decide()` modes: freshness profile ON, ON with `anchor_deadline_to_inputs`, and OFF.
- Values tested: class base `ActionClass.max_status_age_seconds` and the scalars `status_max_age_seconds` and `approval_max_age_seconds` at `2147483647`, `2147483648`, `2**34`, `2**53`, `2**62`, `2**63`, `2**64` and `10**30` for the scalars; class base at `2147483647`, `2147483648`, `2*10**11`, `2.5*10**11`, `3*10**11`, `2**63` and `2**64`; grant status aged exactly `2147483647` and `2147483648`; base 60 with an outage extension composed up to `2147483647`.
- Float-versus-int age comparison (`(now - observed).total_seconds() <= max_age`, one microsecond above the bound): correct at `2**31-1`, `2**31` and `2**33`; the first wrong acceptance sampled is at `2**34`. Values between the sampled points were not enumerated.
- Date overflow: the earlier characterization report put it near 2.5e11 s. The probe now measures it for the class base: `2*10**11` and `2.5*10**11` are `authorized` in all three modes, `3*10**11` raises `OverflowError: date value out of range` with the freshness profile on and anchored (the profile-off mode stays `authorized`). The exact boundary between 2.5e11 and 3e11 was not located. Class base `2**63` and `2**64` raise `OverflowError: Python int too large to convert to C int` with the profile on and anchored (off: `authorized`). For the scalars, the anchored mode raises that same C-int `OverflowError` at `2**53`, `2**62`, `2**63`, `2**64` and `10**30`; the boundary between `2**34` and `2**53` for that path was not located, and the freshness-on and off modes stayed `authorized` at every scalar value tested. No timedelta limit was probed separately.

**Not established.** The measurement supports the chosen bound on that source head, interpreter and platform, in those three modes. It does **not** prove that every possible timestamp, deployment environment or consumer can safely process `2147483647`. In particular it says nothing about other platforms or Python builds (32-bit time or integer widths, other C-int sizes), other timestamp or datetime libraries, deployment clocks (skew, clock steps, far-future or far-past `observed` timestamps), or other consumers, including the Execution Runtime, which was not measured.

**What the ceiling is.** `AGE_MAX = 2147483647` is a chosen technical representation ceiling, not an operational freshness recommendation and not a safety certificate. About 68 years is functionally no freshness bound; no operational value is implied.

**Obligations that follow.**

1. A deployment must stay inside its own component-owned operational limits. The effective configuration remains bounded by them.
2. A hosting component MUST apply its own stricter bounds in addition to the registry value. A registry value never replaces, relaxes or widens a component-owned bound. An extremely large valid registry value cannot silently disable a stricter component-owned bound; the registry can only narrow (`min(caller, registry)`), and a registry value above the caller yields the caller value, reported as `registry_value_not_narrowing`.
3. Existing mandatory component safety bounds are unchanged by this record.

## Not done here

No optional fallback (consumer-owned, EXT-S4-2); no host factory, no outage-extension composition or approval binding (EXT-S3-3/S3-4); no v2 record or selection entry point; no amount slot (reserved or inactive); no `identity_max_age_seconds`, `mandate_max_age_seconds`, `clock_tolerance_seconds` or evidence-obligation age (they refuse `field_unknown`); no Control Plane, Runtime or v1 behaviour change.
