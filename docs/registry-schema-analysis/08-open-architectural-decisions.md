# 08 Open architectural decisions

Non-authorizing. Each item is a decision someone other than this analysis must make. Nothing proceeds on an assumed answer. Architect rulings are classification and design input only: they authorize no build, selection, activation or pin, each of which needs a separate operator decision (T3). The ISS Architect's role and the existence of the ISS questions below are not verified by any source available here.

## For the OCS Architect

| Id | Decision | Why it blocks | Options |
|---|---|---|---|
| D1 | Classify the 32 S02 unresolved rows (03 §4), starting with W8-091, W3-063, W9-027, W8-014, W6-042 and the 60-versus-300 relationship | Every F1c, F4, F5, F7 proposal depends on them | Per row: invariant, caller data, or registry-eligible |
| D2 | Authentication of records and selections (signing, key custody, or pin-only) | Digest is integrity only (T2); no activation is possible without this | Pin-only (current); signed records; signed selections |
| D3 | Where "active" lives: inside the record (S03) or in selection and activation only | A self-declared status lets a record state its own activity | Keep the frozen `s03-v1` gate (only `active` accepted) unchanged; move activity out for successor-format records only |
| D4 | Stricter direction for each scalar: F7 TTL, deadline, horizon; F4 ages, `clock_tolerance_seconds`, `anchor_deadline_to_inputs`; F5 class fields | Without it, composition is not definable (04 §4) | Per field, written ruling |
| D5 | F6 absent-agent semantics: unconstrained or deny | Two internally consistent but different policies | Unconstrained (overlay semantics); deny (key-wise intersection) |
| D6 | Classification of the `max_effects` and `max_amount` ceilings | F1c and the W8-091 row | Invariant; caller data; registry-eligible |
| D7 | Whether a mandatory-registry ACTIVATION profile is ever authorized | Optional refusal can leave a broader caller policy in force (T7) | Optional only; add mandatory profile |
| D8 | Treatment of `runtime-authority-reasons/0.1` and `/0.2`: one evolving commitment or two | Needed before any reason-vocabulary reference record | One; two |
| D9 | Whether F1d (target prefixes and match mode) may ever be registry data | New semantics and a security-weakening mode | Never; prefix-only with containment rule |
| D10 | Status of `COG-REG-SHARED-ADD-01` and supply of its text | The envelope was built without it (05 §0) | Provide; revise envelope |
| D11 | Next increment: F1b (recommended by S06) or another | Sequencing (09) | F1b; F6; none |
| D12 | Whether the W9-027 divergence between `dedupe.py` and `merge.py` is intended | Affects the F7 resolution semantics | Intended; defect to be fixed in Control Plane (outside this repository) |
| D13 | Independent qualification owner for Tier 1 families | S05 limits would carry over | Designate; defer |

## For the ISS Architect

No ISS architecture source was available to this analysis. The following are questions, not assumptions.

1. Does ISS have any rule family that is configuration-shaped today? If not, no ISS payload is needed and the envelope's namespace field is sufficient.
2. Are ISS cognitive policies governed by operators comparable to OCS allow-lists, ceilings and freshness bounds? This analysis assumes **no** equivalence.
3. Which component holds ISS selection and pin custody, and is it disjoint from OCS custody?
4. Is the envelope's `target_consumer` namespace acceptable as the only cross-system field?
5. Confirm there is no shared service, authority ledger or common family payload requirement.

Additional items: (a) whether a selection with no `valid_until` (perpetual) is acceptable; (b) whether `effective_conditions`-style windows may ever live in a record (this proposal says no).

## Constraints that stand regardless

Release, publication and production remain on HOLD. No pin is approved. No record is activated.
