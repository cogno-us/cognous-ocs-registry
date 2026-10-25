# Migration candidates (ranked recommendations)

Not implementation authority. Nothing here authorizes S06, a new migration, a registry record, a manifest pin, a runtime change or an import from the historical catalogue. Each candidate would need its own operator decision, scope and exit criteria under the plan. Labels: **[V]** verified here, **[I]** inferred.

## 1. Position

No migration directly from the historical catalogue is recommended. [I, from verified facts]

- The catalogue has no entry typed as a configurable policy parameter (0 of 3,190). [V]
- 2,978 of 3,190 rules have unresolved MVP applicability; 3,190 of 3,190 have no independent qualification; only 11 have a source-stated implementation link. [V]
- It is a V0.1 review-tag catalogue; V0.2 provenance is unestablished (`unresolved.md` U1). [V]
- Its largest populations (reason vocabularies, ODES README rows, verifier findings) are closed vocabularies or documentation rows that S02 section 4 says stay in code. [V]

So the candidates below come from S02's own family analysis; the catalogue contributes provenance, cross-references and gaps. Ranking uses these factors, applied to the evidence in this directory:

| Factor | Why it matters |
|---|---|
| Value already supplied as data | The registry then moves data and leaves evaluator code unchanged |
| Tier and blast radius | Tier 1 admission or authority subject matter needs CA14 and CA18 controls and wider review |
| Oracle available | S01 baseline (63 tests) and S05 differential harness exist only for `LocalExecutionPolicy` |
| Blocking unresolved S02 rows | A migration that touches an unresolved classification would resolve it by implication |
| Catalogue support | Whether the catalogue adds verified, source-backed material for the family |

## 2. Ranked candidates

### Rank 1: F1 remaining fields (`max_amount`, `max_effects`, institutions, authority domains)

- Basis: already caller-supplied data in `LocalExecutionPolicy`; S02 deferred these only because the architect narrowed the first increment to units, adapters and actions. S05 demonstrated bounded equivalence for the allow-list profile and records unsupported representation classes (E01 to E19). [V from `docs/sprint-status.md` and S02 section 6]
- Catalogue support: none. No catalogue entry establishes a correspondence to `LocalExecutionPolicy` or to its allow-list fields. Four entries do contain the strings `max_amount` or `max_effects`: the action-manifest validator rule `R-AM:VAL:E023` (which names `max_amount` in its statement about `effect_limits`) and the Control Plane reason codes `authority_limit_malformed`, `effect_limit_malformed` and `missing_amount_limit`. These are lexical leads; this exercise did not establish that any refers to the Runtime policy ceilings. The 11 F1 lexical leads comprise 9 reason codes, 1 validator rule and 1 `unknown` entry; none is a match. [V]
- Blockers: none among the 32 unresolved rows for these fields, except W8-091 (`max_effects = current.effective_max_effects`, value origin not visible), which touches the same field name and must be ruled on before `max_effects` is considered. [V]
- Gates: S06 closed; new operator decision; S05 unsupported classes addressed or explicitly kept as refusals; CA14 and CA18 controls; a registry-supplied value must never be more permissive than the caller-constructed policy.
- Not by implication: the check order, reason texts and `__post_init__` validation remain code.

### Rank 2: F7 dedupe and replay-window default (`dedupe_ttl_seconds=600`)

- Basis: one default literal, constructor-overridable, Tier 2 minimum for the value, Tier 1 for the guard. [V from S02 section 3]
- Catalogue support: reason codes `dedupe_operation_effect_applied`, `dedupe_unresolved_attempt_blocks_new_key`, `escalation_after_key_ttl`, `attempt_unresolved_past_horizon` and ODES time-conformance rows are adjacent material for a later equivalence design. They establish nothing about the TTL. [I]
- Blockers: W3-063 (TTL logic, deliberately models forgetting the key) and W9-027 (differing definitions of "applied" and "unresolved" attempt) are unresolved and sit on the same behaviour. Both need architect rulings first.
- Gates: the two rulings; a differential oracle for dedupe behaviour (none exists); S06 closed; operator decision.

### Rank 3: F5 runtime-authority profile declarations

- Basis: host-profile data already; Tier 1 with wide blast radius. [V from S02]
- Catalogue support: the strongest of any family. The `runtime-authority-reasons/0.1` (121) and `/0.2` (164) registries are versioned files at the pinned Control Plane tag, with 43 codes only in 0.2, and one reason-code name (`holder_inventory_missing`) is shared with S02 W8-068. [V] This supports pinning a registry version by digest as a reference, not making the vocabulary configurable.
- Blockers: W8-014 (profile toggles) is unresolved; the architect has not ruled on whether 0.1 and 0.2 are one evolving commitment or two (`classification-crosswalk.md` section 8, item 3); S02 section 4 keeps closed vocabularies in code.
- Gates: those decisions; independent review proportionate to Tier 1; S06 closed.

### Rank 4: F4 observation and freshness bounds

- Basis: highest value, Tier 1, widest blast radius; partly literals at call sites. [V from S02]
- Catalogue support: the most material by count (199 lexical leads, 74 ODES `freshness-clocks` rows) but largely error-code tables of unknown normative strength; none carries the S02 literals. [V counts, I reading]
- Blockers: the explicitly unresolved 60-versus-300 relationship and W6-042 (absent observation policy), which sit directly on the family. Adjacent observation vocabulary is also unresolved (W2-025 required observation set; W6-004 evidence kinds; W6-005 unknown-state behaviours). Any migration here would resolve at least one by implication.
- Gates: rulings on all of the above; a freshness oracle (none exists); S06 closed.

### Not recommended

- F2, F3, F6, F8, F9, F10, F11: as in S02 (literals, mixed tier, little test evidence, or already data with nothing to gain). The catalogue adds no support. [V]
- Any catalogue-only family (governed-exchange transport profile, ODES time-conformance, journal, delegation, reconciliation, constitution clauses): either `requires_unavailable_component` under the MVP profile (governed-exchange, 204 entries), unresolved for applicability, or documentation rows. [V]
- Importing catalogue content into the registry: out of scope per plan S02/S03, and 17,704 evidence records have no source revision. [V]

## 3. Recommended non-migration actions (decisions, not work orders)

1. Define "V0.2" and identify the intended inventory (`unresolved.md` U1). Until then, cite this catalogue as V0.1 review-tag material.
2. Rule on the 32 unresolved S02 rows, starting with those blocking Ranks 1 and 2: W8-091, W3-063, W9-027.
3. Decide the adoption status of the 229 proposed Constitution v0.1 clauses, and whether the 35 adopted floors need an adoption record cited from the catalogue.
4. Decide identity policy for cross-repository duplicates before any entry is cited as "the rule".
5. If the catalogue is to be relied on further, re-run it against current repository heads and record source revisions for the 17,704 evidence records that lack one.
6. If S02 is ever extended beyond Runtime and Control Plane, the catalogue's ten other repositories are the obvious scope, with the catalogue entries as pointers only.

## 4. Summary table

| Rank | Family | Catalogue support | Main blocker | Oracle exists |
|---|---|---|---|---|
| 1 | F1 remaining fields | none | operator decision; W8-091 for `max_effects` | yes (S01 and S05 for the allow-list profile; extension needed) |
| 2 | F7 dedupe default | adjacent codes only | W3-063, W9-027 | no |
| 3 | F5 authority declarations | registries 0.1 and 0.2 pinned at tag; one shared name | W8-014; 0.1/0.2 ruling | no |
| 4 | F4 freshness bounds | most material, weakest strength | 60-versus-300; W6-042; adjacent W2-025, W6-004, W6-005 | no |
