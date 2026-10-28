# Runtime F-01 suite and the durable authorization-pin path (PR-4, Phase D)

Non-authorizing, documentation only. No oracle is implemented, executed or independent; nothing here is qualified or certified. Release, publication and production are not authorized.

G0: ACCEPTED AND FROZEN. G1: PREPARATION ONLY. G1 CONTRACT/ORACLE IMPLEMENTATION: NOT AUTHORIZED. G2–G5: NOT AUTHORIZED. V09 independent V07 review: OPEN. V09 independent V08 Tier 1: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

Question: does the Runtime F-01 suite exercise the durable authorization-pin path? Source read at Runtime `0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491` and SQ `bb9b08904192b5f50a49e00ed8de0cab80fd7c19`.

## 1. Answer

**No.** `tests/test_f01_policy_containment.py` (18 collected tests) contains no reference to `authorization_pin`, `pin_required` or the installer. Every destination in it comes from `g.Gov(...)` (`tests/test_registry_selection_effect_guard.py`), which constructs `AtomicAuthorityEffectDestination` without the `authorization_pin` option. Only destinations built with `authorization_pin=` take the pin branch (`engine/local_authority_effect.py`: `_pin_reader is None` runs the body directly). The constructor option appears in exactly two test files: `tests/test_authorization_pin_guard.py` and `tests/test_authorization_pin_integration.py`.

## 2. Engine order (source, not test)

With a pin configured, execution is: lock-free barrier read, shared per-decision fence, second barrier read, `BEGIN IMMEDIATE`, claim-state validation, **pin step** (`check_claim_against_pin`), **selection guard including five-set containment** (`_selection_guard(..., pin_scope=...)`), effect write. A pin-valid claim therefore reaches containment in the same transaction. The question is test coverage of that combination, not whether the code path exists.

## 3. Direct-destination tests versus complete pin-plus-containment tests

| Class | Test | Pin | Sets covered | What is asserted |
|---|---|---|---|---|
| Direct destination (no pin) | Runtime F01-1..F01-14 (`test_f01_policy_containment.py`) | no | all five, one per set (F01-4..8) plus all five together (F01-2/3) | REFUSE policy_identity_mismatch, cause policy_not_subset:<set>, zero effects; HOLD store_unknown on bad record; digest/sets consistency |
| Direct destination (no pin) | SQ V07 a12..a16, a17, a18 (Runtime `ac247daf`) | no (older Runtime) | all five, one per set | per-set widening with a recomputed commitment; narrower and equal still execute |
| Pin + containment, test-only pin writer | `test_f01_containment_still_refuses_a_widened_policy_under_a_valid_pin` (pin guard, line 696) | yes (PinWriter) | allowed_actions only | REFUSE policy_identity_mismatch, cause policy_not_subset:allowed_actions, zero effects, fence released |
| Pin + containment, real installer | `test_f01_widening_still_refuses_under_a_valid_installer_pin` (integration, line 125) | yes (real installer) | all five widened together | status 'denied', zero effects, a selection_refusal present. No code, cause or per-set attribution. |
| Pin + containment, real CP/installer/guard | SQ FA1-23 and FA1-24 | yes | allowed_actions (FA1-23), allowed_units (FA1-24) | REFUSE policy_identity_mismatch with the per-set cause; FA1-25 narrower executes under the pin |

## 4. What is and is not demonstrated

- Pin + containment with a per-set attributed refusal: **allowed_actions and allowed_units only** (two of five).
- allowed_adapters, allowed_institutions, allowed_authority_domains under the pin: demonstrated only by the all-five aggregate case, which cannot show that each set is checked independently under the pin (a mutant that skips one set would still be refused because the other four widen).
- Pin + containment HOLD paths (damaged stored record payload under a valid pin), pin + containment multi-member or deny-all records, and pin + containment under a racing revocation: no test.
- The SQ expectation text of FA1-24 says "the other three sets run in the Runtime F-01 CI suite". That claim is wrong for the pin path (the F-01 suite has no pin) and also for CI: Runtime CI runs `python -m pytest -q tests` without PyNaCl or `OCS_REGISTRY_PIN_DIR`, so the six Registry-gated modules skip (environment-profile.md E-14).

## 5. Statements this package makes and does not make

- It does **not** claim the complete pin-plus-containment path is covered. Coverage of direct destination containment is not transferable to the pin path.
- It does **not** claim independent qualification of the pin path. Amendment 4 is a DRAFT (PD-4); Amendment 3 says it is not evidence F-01 is closed.
- It records the two-of-five finding as a gap for OW-9 (E-34, E-35, F-29, F-30) and as CONFIRMED OPEN in the closure table.
