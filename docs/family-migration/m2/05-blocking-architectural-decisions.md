# M2 — Architectural decisions and remaining blockers (corrected)

Status: for Architect confirmation. D-2, D-5 and D-7 are ACCEPTED as ruled. D-1, D-3, D-4 and D-6 are resolved below from source.

## D-1 — Family structure: OPTION B (composite) recommended

Requirement: standalone f1c may be adopted only if f1ab and f1c can be simultaneously bound and enforced without six hazards. Source (pinned) shows they cannot, using the existing architecture:

| Source fact | Where |
|---|---|
| A binding holds exactly one `family` identifier and one `effective_policy_digest`; the claim carries one `policy_binding` | Control Plane `canonical_policy_binding.MEMBERS`, `IDENTIFIERS`; Runtime `local_authority_effect` (`getattr(claim, "policy_binding")`) |
| The governed scope key includes `family`; a binding resolves exactly one activation row, one lineage, one epoch, one policy generation, one ratchet bit | Runtime `registry_selection_authority.check_effect` (~1371–1400: `scope = {…, "family": binding["family"]}`, `d.rows.get(gsd)`) |
| Containment is hardwired to `FAMILY_F1AB` and the five `sa_fields()`; the executor must pass exactly those five sets | `_check_policy_containment` (~1451–1478), `sa_fields` (~1562) |
| The narrowing adapter replaces only the five set fields and decides one record/selection | `registry_f1a_narrowing._build_narrowed_policy`, `FIELDS` |
| Unbound claims fall back to caller policy for withdrawn/expired non-ratcheted scopes | `_check_unbound` (~1494–1515) |

| Hazard | Why standalone f1c + f1ab fails on existing source |
|---|---|
| Policy substitution | One digest can name one family's policy; the other family's ceilings or sets have no digest binding, so the executor could present any values |
| Partial activation | Two scopes activate independently; a claim bound to one never reads the other |
| Independent withdrawal that widens | Withdrawing or revoking the unbound scope has no effect on a claim bound to the other, so the ceilings (or sets) silently drop |
| Generation / epoch | Per-scope counters; nothing orders them across two scopes |
| Atomic effect-time evaluation | `check_effect` verifies one row per call; two rows need a new multi-binding guard |
| Unqualified fallback | A missing second binding is indistinguishable from "not governed" |

Closing these needs a generic multi-family binding subsystem, which the Architect excluded. **Selected: composite `f1abc-local-execution-limits`** (five f1ab sets + `max_amount` + `max_effects`), one record, one selection, one activation, one seven-member digest. Preservation of f1ab semantics, coexistence and transition: `02` §9 and §12.

## D-2 — Zero semantics: ACCEPTED

`max_amount = 0` valid ceiling, evaluator unchanged. `max_effects = 0` explicit deny-all; no `LocalExecutionPolicy` is constructed; no effect is dispatched.

## D-3 — Float compatibility: decision B (explicit refusal)

Characterization and reasoning in `02` §6–§7. Governed path refuses any caller float `max_amount` (identity preimage is integer-only; accommodating floats needs a new float encoding). Registry records are exact ints. Legacy behaviour outside the governed path is unchanged. Documented compatibility limitation: operators using float or integral-float ceilings must express them as exact ints before a governed activation.

## D-4 — Numeric bounds

`max_amount` Registry 0..2^53 (source). `max_effects` Registry 0..2^53 − 1 with 0 = deny-all; derivation in `02` §4: no Runtime/Control Plane constraint below SQLite's 2^63 − 1; the Registry canonical-integer convention supplies 2^53 − 1. Caller `max_effects`: exact int ≥ 1, uncapped (the effective value is bounded by the record). Behaviour at 0, 1, max, max + 1, negative, bool, float and overflow: table in `02` §4. Alternative for the Architect: 2147483647.

## D-5 — Successor contract: ACCEPTED (`r08-v3`; v2 untouched)

## D-6 — Control Plane

Opaque family/digest handling is confirmed by source (identifier pattern admits the new family; digest is opaque sha256; no f1ab constant). Minimum compatibility for the composite: reuse of binding profile `ocs-policy-binding/1`, bindings issued with the new family after cutover. Single binding is not assumed to support multiple families.

## D-7 — Revocation and staleness: ACCEPTED

Governed f1abc activations require participation `required` (existing ratchet) so an unbound claim refuses; revoked, withdrawn, stale, absent, invalid or mismatched selections refuse with no fallback.

## Remaining implementation blockers

| ID | Item | Blocks | Needed |
|---|---|---|---|
| R-1 | Confirm the `max_effects` Registry bound 2^53 − 1 (or choose 2147483647) | PR-1 ranges | Architect |
| R-2 | Confirm reuse of the v2-labelled binding digest-domain constant for an r08-v3 family, or approve one new Control Plane constant | PR-4 only | Architect / Control Plane owner |
| R-3 | Runtime coexistence rule and `policy_effective_ceilings` plumbing are required Runtime changes (not in PR-1) | PR-2/PR-3 | none; scheduled |

None blocks PR-1 (Registry only) except R-1, which is a one-constant choice.

## Implementation authorization recommendation

AUTHORIZE PR-1 (Registry `r08-v3` composite family, validation, composition, identity, vectors, tests) upon confirmation of R-1. PR-2/PR-3 follow without further design. Release or production use is not recommended; Tier 1 independent qualification remains required before acceptance.

## Standing holds

M2 contract correction: AUTHORIZED. M2 implementation: NOT AUTHORIZED. G2–G5: NOT AUTHORIZED. V09 independent assurance: separate workstream. Ed25519: SECURITY-HELD. Release/publication/production: HOLD.
