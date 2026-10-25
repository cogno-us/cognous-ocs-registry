# Classification crosswalk: historical catalogue against S02

Non-authorizing. Labels: **[V]** verified here, **[I]** inferred, **[R]** reported by a source. "Match" in this document means an established correspondence between a catalogue entry and an S02 row or family. String co-occurrence and keyword hits are leads, never matches.

## 1. Two different populations

| | S02 (`docs/s02-inventory.md`) | Historical catalogue (`catalogue-v0.1`) |
|---|---|---|
| Derived from | Source code constructs (`file:line`) of two components | Documentation rows, JSON schemas, validator error tables, requirement files and test contracts of twelve repositories |
| Pins | Runtime `ec728da6`, Control Plane `0a41faa9` | Review tag `review-v0.1-g8-r10-20261022` in twelve repositories, including the same two commits [V] |
| Unit | 620 construct rows, six classes | 3,190 rule entries plus scenarios, tests, fixtures, evidence |
| Classification author | AI workers plus builder reconciliation, provisional | Loader and overlay passes, attributes stated "unknown" unless a source or overlay states them |
| Completeness claim | none; not exhaustive (tests, examples, conformance, schemas, other components not inventoried) | none; "entries absent from partition outputs are absent" |

Consequences [V counts]:

- 369 of 3,190 catalogue entries come from the two S02 repositories (Control Plane 349, Execution Runtime 20). 2,821 entries come from ten repositories S02 never inventoried.
- The 20 Runtime entries are rows of `docs/workstreams/openappa-host-contract.md`, not `engine/` code.
- The 349 Control Plane entries are 285 reason-registry codes (`schemas/runtime_authority_reasons_0_1.json` 121 and `_0_2.json` 164), 39 execution-attempt-lifecycle codes (`tests/contracts/execution-attempt-lifecycle/validate.py`) and 25 validator rules (`src/agent_control_plane/manifest_validation.py`). S02 states it did not inventory `schemas/` or `tests/` contents.
- The only code file that both inventories cover is `src/agent_control_plane/manifest_validation.py`: S02 rows W5-011 to W5-023 (13 rows: 10 `MANDATORY-INVARIANT`, 3 `UNRESOLVED`) and 25 catalogue `validator_rule` entries (`E001@control-plane-port` and so on). The 3 unresolved rows (W5-011, W5-012, W5-023) concern constants and a default posture, not the error codes the catalogue entries record, so the catalogue does not bear on them.

## 2. Class-level crosswalk

| S02 class (rows) | Nearest catalogue category (entries) | Entry-level match established? | String-level lead |
|---|---|---|---|
| `MANDATORY-INVARIANT` (354) | 2. enforcement candidates (240) and 1. policy (247) | No | 64 distinct reason-code names appear both in S02 mandatory rows and in catalogue reason codes (for example `action_blocked`, `adapter_mismatch`, `amount_exceeded`); S02 rows describe the check, the catalogue entry names the code [I] |
| `REFUSAL-OR-REASON-VOCABULARY` (50) | 4. reason codes (1,819 entries, 1,662 names) | No | 4 of 50 rows name 6 codes also in the catalogue: `escalation_after_key_ttl`, `grant_revocation_recorded`, `operation_grant_mismatch`, `operation_not_admitted`, `operation_renewal_unrecorded`, `renewal_not_written_by_grant_issuer`. The other 46 rows have no name-level counterpart under a crude extraction (snake_case tokens in the construct and what-it-encodes cells only) |
| `SERIALIZATION-OR-EVIDENCE` (90) | 6. evidence artifacts (not rules) | No | 1 name (`observation_unavailable`) |
| `INCIDENTAL-CONDITIONAL` (51) | none | No | none |
| `CONFIGURABLE-CANDIDATE` (43) | 3. configurable parameters (0) | No: the catalogue has no such type | see section 3 |
| `UNRESOLVED` (32) | 8. unresolved (640) | **Not equivalent.** S02 "unresolved" means invariant-or-configurable could not be decided from code; catalogue `unknown` means normative strength is not stated | none of the 32 rows has a name-level overlap |

Name-level overlap totals 69 distinct code names; the per-class figures above sum to more because a name can occur in rows of more than one class. These are string co-occurrences. No equivalence between an S02 row and a catalogue entry is claimed, consistent with the catalogue's own ruling that a code-string match is "not merged" and that registration is not enforcement.

## 3. Families F1 to F11

For each family: what S02 records, whether a catalogue counterpart is established, and the lexical leads found by `recount.py` (pattern in `recount-output.json`; case-insensitive search of statement, native id and title). Leads are over-inclusive and unreviewed.

| Family | S02 | Catalogue counterpart established? | Lexical leads (entries) | Note |
|---|---|---|---|---|
| F1 Local execution policy values | Recommended first family, narrowed to allowed units, adapters, actions | No | 11 (9 reason codes, 1 validator rule, 1 unknown) | Leads are limit-related codes such as `authority_limit_malformed`, `effect_limit_malformed`, `missing_amount_limit`. No catalogue entry names `LocalExecutionPolicy` or its allow-lists |
| F2 Target-match vocabulary | Tier 1 subject; keep in code; W1-029 unresolved | No | 0 | |
| F3 Size, depth, timeout budgets | Mixed tier; mostly literals | No | 39 | Mostly reason codes; relevance unreviewed |
| F4 Freshness and observation bounds | Tier 1; includes the unresolved 60-versus-300 relationship | No | 199 (85 reason codes, 104 `unknown`-strength rows, 10 other) | The `unknown` rows are largely ODES `contracts/freshness-clocks/README.md` rows (74), which read as error-code tables. No entry carries the `ObservationPolicy(300, 5)` literal, the 86,400 s recovery age or the 60 s schema default |
| F5 Per-action-class authority declarations | Tier 1; host profile data | Partial, string level | 17 (13 reason codes, 4 `unknown`) | S02 section 3a names `holder_inventory_missing` for `HolderInventory` (W8-068); the catalogue holds `R-CP:RAR02:holder_inventory_missing`. The name is shared [V]; the S02 row is host data feeding a check, the catalogue entry is a vocabulary entry [I] |
| F6 Agent permission allow-list | Data file already | No | 0 | |
| F7 Dedupe and replay-window defaults | Tier 2 minimum; guard W3-063 unresolved | No | 18 (11 reason codes, 7 `unknown`) | Codes `dedupe_operation_effect_applied`, `dedupe_unresolved_attempt_blocks_new_key`, `escalation_after_key_ttl`, `attempt_unresolved_past_horizon` touch the semantics of unresolved W3-063 and W9-027. They are not used to resolve either |
| F8 Demo policy tool lists | Tier 2 until reviewed | No | 0 | |
| F9 Tenant id length bound | Tier 2 | No | 0 | |
| F10 Diagnostic trend thresholds | Tier 2 minimum | No | 5 | ODES rule-revision rows (`taint_flag_inconsistent`, `trend_annotation_incomplete`) and `R-D10-cc772787`; a weak lexical overlap with `reason_vocabulary.py` |
| F11 Redaction defaults | Tier 2 minimum, confidentiality controls treated as Tier 1 | No | 14 (7 validator rules, 7 other) | Validator rules on redaction in action-manifest, evidence-pack and replay-bundle; not the Control Plane redaction configuration |

**Matches to F1 to F11: none established at entry level. One string-level link (F5, `holder_inventory_missing`).** [V]

## 4. Candidate families in the catalogue that S02 does not represent [I]

Entry counts use the catalogue's own `normative_subtype` label; the label is derived, not source-verified. Normative strength is `unknown` for most ODES README rows. Relevance to S02 is an inference.

| Catalogue subtype | Entries | Closest S02 area |
|---|---|---|
| ODES time-conformance comparisons (three comparison groups: 36, 36 and 9) | 81 | none; cross-implementation conformance rows |
| ODES freshness-clocks | 74 | F4 (adjacent) |
| Control-plane journal | 64 | none |
| Governed-exchange and operation identity | 56 and 56 | none (governed-exchange is `requires_unavailable_component` under the MVP profile, 204 entries) |
| Rule revision | 52 | F10 (adjacent), W4-033 |
| Verification report | 50 | none |
| Execution-attempt lifecycle (28 plus 39 refusal codes plus 39 replay-code mappings) | 106 | W3 attempt state machine (adjacent) |
| Effect reversibility | 27 | F5 (adjacent) |
| Bounded deferral | 26 | none |
| Action-manifest validator errors (25, plus 25 Control Plane port) and evidence-pack, replay-bundle validation rules | 50 plus 80 | W5 manifest validation (partial, see section 1) |
| Index evidence registry | 22 | none |
| Two-party reconciliation | 21 | none |
| Verifier checks v2 | 21 | none |
| Non-broadening delegation | 18 | none (S02 states only that registry-supplied values must never be more permissive) |
| Authority lineage | 16 | none |
| Source-family counting | 15 | none |
| Preregistration decisions | 15 | none |
| Constitution v0.1 clauses, proposed not adopted | 229 | none |
| Adopted constitutional floors `CR-001` to `CR-035` | 35 | S02 section 4 cites CA05, CA12, CA18 as the basis for non-migratable invariants |

## 5. Historical entries lacking current source backing

"Current source backing" here means a corresponding S02 row at a pinned S02 revision. [V counts, I interpretation]

- 2,821 entries (ten repositories) have no S02 counterpart because S02 did not inventory those repositories.
- Of the 369 entries in S02 repositories, at most the 25 `manifest_validation.py` entries correspond to a code file S02 inventoried; none corresponds to a specific S02 row.
- The 285 reason-registry entries are backed by a source file at the Control Plane tag [V], but that file is outside S02's inventoried code, and the current Control Plane `HEAD` (`7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` at check time) differs from the tag commit. Whether the registries changed since the tag was not assessed.
- Whether any entry still reflects the present head of its repository was not assessed for any of the twelve repositories.

## 6. Entries that should remain mandatory implementation invariants [I]

These are recommendations for the architect, not rulings.

1. The 35 adopted floors `CR-001` to `CR-035`. S02 section 4 states protected invariants must not move to configurable data (CA05, CA12, CA18).
2. All reason-code and refusal vocabularies (1,819 entries). S02 section 4 treats closed vocabularies as external commitments (CA12, CA21) needing an authorized compatibility transition. Registry versioning (0.1 and 0.2 coexisting) shows the vocabulary already evolves by versioned transition.
3. The 201 validator rules and the 39 Qualification `mandatory: true` rows, as enforcement or acceptance candidates. Whether any is wired into an enforcement path is not established; they stay out of configurable data until it is.
4. Everything S02 listed in its section 4 (check order, fail-closed validation, envelope validation, the one-effect rule, target well-formedness), none of which the catalogue represents.

## 7. Potential new configurable policy families [I]

None can be proposed from the catalogue alone: no entry is typed as a configurable parameter, and 2,978 of 3,190 have unresolved applicability. Candidates for later study, each blocked by a stated decision (see `migration-candidates.md`): ODES freshness-clock bounds (F4-adjacent), dedupe horizon semantics (F7-adjacent), Control Plane runtime-authority profile catalogue (F5). Governed-exchange transport profile parameters appear in the catalogue but are `requires_unavailable_component`.

## 8. Items requiring architectural decisions

1. Which release or version "V0.2" denotes, and which catalogue content belongs to it (`unresolved.md` U1).
2. Status of the 229 proposed Constitution v0.1 clauses.
3. Whether `runtime-authority-reasons/0.1` and `/0.2` are to be treated as one evolving external commitment or two.
4. Identity policy for cross-repository duplicates (68 native ids; 164 cross-repository duplicate-statement groups).
5. The 32 S02 unresolved classifications, each needing its own ruling (`unresolved.md` U4).
6. Whether evidence without a source revision (17,704 records) may support any rule-level claim.
