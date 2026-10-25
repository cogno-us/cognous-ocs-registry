# 09 Implementation roadmap

**Possible future engineering order. Not authorized, not scheduled, not started.** Every step needs its own operator decision. This analysis implements none of them.

## Order and reasons

| Step | Content | Depends on | Notes |
|---|---|---|---|
| 0 | Architect rulings D1 to D13 as relevant to the next step, plus an operator decision to proceed | none | Rulings are input only; building needs an operator decision |
| 1 | Authenticate selection (D2) and decide the ACTIVATION profile (D7) | 0 | Precondition for any activation; today none exists |
| 2 | Successor envelope validator as a new module, with the F1a payload only | 0, 1 | Proves the envelope without new semantics; S03/S04 untouched |
| 3 (alt) | Minimal alternative for F1b: an `s03-v2` contract with its own validator, a separately versioned manifest and a separate consumer path, all in new modules (the frozen S04 consumer accepts only `contract_version == "s03-v1"`, delegates to the frozen validator and applies only the three F1a fields, so it cannot consume `s03-v2`), without the full envelope | 0 | Smaller than steps 1-2; trades away the common envelope; frozen S03/S04 untouched |
| 3 | F1b (`allowed_institutions`, `allowed_authority_domains`) | 2 | Recommended by S06; same type and check; needs a new contract version and fresh differential evidence |
| 4 | F1c ceilings with typed numeric payload | 0 (D6), W1-015 | Min with code hard cap |
| 5 | F6 agent permissions | new baseline import, D5 | Moderate |
| 6 | F11 redaction union | tier ruling | Optional |
| 7 | F4 per-scalar ages | D1, D4, clock authority | Wide blast radius |
| 8 | F5 tightening subset | D1 (W8-014), D4 | Wide blast radius |
| 9 | F7 dedupe profile | D1 (W3-063, W9-027), D4, cross-component dependency | Last; needs both components |
| – | F1d, F2, F3 guards, M1 to M8, vocabularies, lifecycle, relaxing toggles | | Not migrated; remain code |

## Recommended migration order (summary)

This analysis' earlier order was F1a (done), F1b, F1c, F6, F4, F5, F7. The adopted plan's default order for architectural assessment (R11) is the remaining F1 set fields, then F6, then F1 numeric ceilings and target prefixes with distinct operators, then F4, F5 and justified F7/F3/F9/F10; this roadmap now follows v1.2: F1a (done) → F1b → F6 → F1c ceilings → F4 scalars → F5 tightening subset → F7. Either order is an assessment input, not an authorization; each family needs its own authorization (R11). F9 and F10 are not recommended (no value). F1d is not recommended without a ruling.

## What each step must carry

Frozen expectations written before code; an oracle written by someone other than the validator author, required for every family beyond F1a before any claim (07 §2); negative controls for each refusal class; Copilot review on the exact head (technical review only); no activation, no approved pin, and no Runtime integration in the same sprint.

## Explicitly not in this roadmap

Merging the schema proposal, implementing a successor, migrating rules, modifying S03/S04 behavior, activating records, approving pins, connecting the registry to Runtime, starting ISS/OCS integration, beginning production qualification.
