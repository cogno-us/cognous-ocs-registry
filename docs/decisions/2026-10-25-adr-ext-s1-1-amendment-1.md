# ADR EXT-S1-1 Amendment 1: D-27 `AGE_MAX`, effective-policy digest, identifier rules and additive reason codes

- Status: **AMENDMENT 1 to [ADR EXT-S1-1](2026-10-25-adr-ext-s1-1-v1-contract.md), effective on merge.** Documentation only. Authorizes no implementation, no source edit, no activation, no qualification. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.
- Companion normative text: [`docs/r08-v2-contract-amendment-1.md`](../r08-v2-contract-amendment-1.md) (the contract amendment; this record states the decisions and their provenance, the contract amendment states the rules, the worked examples and the code definitions).
- Authorization: the Architect authorized "one small documentation amendment covering: D-27 AGE_MAX decision; Effective-policy digest preimage; Canonical worked example; Versioned identifier rules; Source and decision provenance", with "Do not rewrite previously frozen historical records. Add a versioned clarification." The Architect's **Batch 6 rulings** (4.3, 4.7, N-10 to N-13) are recorded in decision A1-07 below. The Architect's N-4 ruling: the three proposed codes `not_activated`, `policy_identity_mismatch` and `store_unknown` carry required semantic distinctions and "may enter the versioned v2 reason registry through an explicit additive amendment. Do not change the closed v1 vocabulary. Do not overload an existing code if doing so would erase an authority-relevant distinction."
- Evidence rule: as in the frozen ADR, statements about component behaviour are source readings and builder tests, not qualified results.

## 1. Frozen records are not rewritten

The ADR above (`git` blob `f5ca77f9d21689f28066b62b1aba8587102c9cba`, sha256 `b9ad06be559bfb99c5e669ca7217d2ee28b62cda7738206c31fd8e6866233b67`), the contract `docs/r08-v2-contract.md` (blob `ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f`, sha256 `64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01`) and the outcome map `docs/p1-extraction-plan/data/ld02-outcome-map.json` (blob `2752800d240d4255af3e62d2e911b0821c8e2af4`, sha256 `dcb14ec1067ccf3218949de57312040dad9df926b134a67f2826e3f0c37d535c`) are unchanged by this amendment (observed at head `f618cdf`). Each decision below says which frozen decision it clarifies; the full row-by-row table is section 1 of the contract amendment.

## 2. Decisions

**A1-01 D-27 `AGE_MAX` is decided: `AGE_MIN = 1`, `AGE_MAX = 2147483647` (clarifies D-27, contract 2 and 2.1).**
Strict integers; a V1 **technical representation ceiling, not an operational freshness setting**; `effective = min(caller, registry)`; an invalid value is never clamped, coerced or replaced; the caller range is 0 to 2147483647 and a caller 0 stays 0. Source characterization supports the ceiling but does not prove every timestamp or deployment environment, and component-owned operational limits remain binding: a very large valid registry value can never silently disable a stricter component-owned bound. The detailed record is `DR-CP-AGE-1` in registry PR #31 (head `17d50c3443ccd96ab95d5c1a0a925845ff1c6f7b`, **pending, not merged**). Frozen wording replaced: D-27 "`AGE_MAX = 2678400` is NOT adopted" and "`MAX` **pending**"; contract 2.1 "Interim supported range ... with `MAX` pending"; ADR section 6 open item 1 (closed). Contract amendment section 2.

**A1-02 The effective-policy digest preimage is the domain-separated form (clarifies contract 4 and D-14/D-15; ruling OQ-3).**
`sha256` over `ocs-reg/r08-v2/effective-policy\n` followed by the canonical JSON of `{effective_policy_profile "ocs-effective-policy/1", contract_version "r08-v2", family, family_version, deny_all, effective}`. It is claim-carried, caller-dependent **evidence**, never compared to durable selection state, never authority. It is the canonical definition from the effective date of this amendment and supersedes the frozen contract 4 wording that describes the preimage only in words. The binding digest is unaffected because `effective_policy_digest` is an opaque, format-checked member. Contract amendment section 3.

**A1-03 Canonical worked example (clarifies contract 9).**
The frozen contract 9 `effective_policy_digest` value stays valid as a historical example of the binding digest. A second, fully worked example of the new preimage (exact canonical bytes in hex and the digest) is added and proved by recomputation in Python and Node. The amendment states which supersedes which. Contract amendment section 4.

**A1-04 Versioned identifier rules (clarifies D-15 and contract 4.1; ruling OQ-4 and the Architect's acceptance of the grammar).**
Rule set `ocs-identifier-rules/1`: binding identifiers match `\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z`, ASCII only, no normalization, case folding or trimming, exact UTF-8 bytes. Payload entries (allowed actions, adapters, units, institutions, authority domains) keep the contract section 2 opaque token rule (Architect confirmed). Scope tokens in statements are retained as provenance and refused only at binding projection. The rule set is bound to `ocs-policy-binding/1`; a future grammar is an explicit successor (new rules tag, new `binding_profile`, new prefix), never an in-place change. ADR section 6 open item 4 ("Binding identifier character set") is closed. Contract amendment section 5.

**A1-05 Three additive reason codes (clarifies D-02; ruling N-4).**
`not_activated` (layer `selection`, `REFUSE`), `policy_identity_mismatch` (layer `identity`, `REFUSE`) and `store_unknown` (layer `trust`, `UNKNOWN_FAIL_CLOSED`), each with its own definition and a documented reason it cannot be an existing code. They are disjoint from the 48 `CODES_V2` codes (computed from `registry_successor/v2_codes.py`, read-only). They form **revision 2** of the one Registry v2 reason vocabulary (designation `r08-v2-reasons/2`, symbol `CODES_V2_REV2`, **51 = 48 + 3** codes, a strict superset of revision 1 `CODES_V2`), declared here and implemented only by the `EXT-S1-5` implementation PR in `registry_successor/v2_codes.py`. No second registry or parallel file is permitted; the earlier draft label `r08-v2.1` is withdrawn (Architect: proposed designation, must not be confusable with `contract_version`). Fail-closed migration rule and evidence: contract amendment section 6.7. The closed `r08-v1` vocabulary (46) and `CODES_V2` (48) are unchanged; the pinned 48-code outcome map is not edited. `contract_version` stays `r08-v2`. Contract amendment section 6.

**A1-06 Family-version identity (clarifies contract 4 policy context; ruling N-3).**
The `family_version` comes from the registered, authenticated family contract (the section 2 table tag) and cannot be selected by the caller independently of the family. Contract amendment section 7.

**A1-07 Batch 6 rulings (clarifies D-02, contract 3.3 and the unknown-store rule of contract 8; rulings 4.3, 4.7, N-10 to N-13).**
RULED: `r08-v2-reasons/2` and `CODES_V2_REV2` are confirmed (48 + 3 = 51). `policy_identity_mismatch` accounts for all applicable authoritative identity members of the complete declared canonical binding version (`scope_key`, `selection_id`, `selection_epoch`, `selection_digest`, selected record identity, `activation_ref`); a definitively stale epoch is `REFUSE_STALE`, not an identity mismatch; no member absent from a historical contract version is manufactured. An unknown store is `HOLD` / `UNKNOWN_FAIL_CLOSED`, never `overlay_not_applied` merely because state is unknown; a refused projection does not establish never-activated; optional fallback needs authenticated consumer-owned state; `family_unsupported` and `contract_unsupported` are definitive `REFUSE`. `trust_snapshot_missing` stays one code with a typed, versioned evidence stage (INPUT, DURABLE_STATE) and malformed input is never called missing. N-10 (syntax-first v2 identity parsing; `snapshot_version` in `[1, 2^53-1]`) and N-13 (frozen Unicode token definition; ambiguous tokens refuse) are recorded in the contract amendment section 10. The kit and the PR #30 mapping differ from ruling 4.3 on overlapping cases; the alignment is owned by the PR #30 alignment PR, and this amendment edits neither. Contract amendment sections 5.3, 6.1, 6.4, 7 and 10; supersession row S-13.

## 3. Provenance of every ruling and source used

Architect rulings are cited by topic and date. Project documents named below are **recorded in the OCS Project, not in this repository**, and are not copied here. Where this ADR relies on a ruling that is only recorded in the Project, the repository-side reader should treat the contract amendment's rule text as the repository record.

| Topic | Ruling (all dated 2026-10-25) | Recorded in | Used for |
|---|---|---|---|
| D-27 `AGE_MIN`, interim bounded schema | Architect round 2 | This repository: ADR EXT-S1-1 section 6, D-27 (frozen) | Baseline that A1-01 clarifies |
| Round-2 rulings R1 to R6 (fallback, commit-time comparison, supersession, freshness ceiling, withdrawal disposition, `activation_ref`, serialization, approval revival) | Architect round 2 | This repository: ADR section 6 (frozen) | Context only; none reopened |
| Final rulings OQ-1 to OQ-5 (per-field integer ranges incl. `AGE_MAX` technical ceiling; typed reason-code mapping; effective-policy digest preimage; Unicode scope-token projection; scope key) | Architect final rulings | OCS Project doc `claude/ocs-p1-architect-final-rulings-2026-10-25.md` (not in this repository); mirrored as pending text in registry PR #30 spec section 12 | A1-01 (age ceiling), A1-02, A1-03, A1-04 (OQ-4). OQ-1 integer ranges other than age, and OQ-5, are **not** recorded by this amendment |
| `AGE_MAX = 2147483647` decision and DR-CP-AGE-1 | Architect Batch 3 and Batch 4 rulings | OCS Project docs `claude/ocs-p1-batch3-consolidated-report-2026-10-25.md`, `claude/ocs-p1-batch4-handoff-2026-10-25.md`, `claude/ocs-p1-architect-final-rulings-2026-10-25.md` (not in this repository); registry PR #31 (pending) | A1-01 |
| Identifier grammar accepted; payload entries keep the opaque token rule | Architect acceptance and confirmation (relayed in the brief for this PR) | OCS Project (not in this repository); ADR section 6 open item 4 (frozen, still reads proposed) | A1-04 |
| N-3 family-version identity | Architect ruling (relayed in the brief for this PR), recorded as a clarification only | OCS Project (not in this repository) | A1-06 |
| N-4 additive reason codes | Architect Batch 4 ruling (PR #30 section 12 N-4) | OCS Project docs as above; PR #30 spec section 8.2 (pending) | A1-05 |
| Track C authorization of one small documentation amendment | Architect | OCS Project (Track C authorization, relayed in the brief for this PR) | The whole amendment |
| Batch 6 rulings 4.3, 4.7, N-10, N-11, N-12, N-13 | Architect Batch 6 rulings | OCS Project (not in this repository) | A1-07 |
| Four-verdict vocabulary (`ACCEPT`, `REFUSE`, `REFUSE_STALE`, `UNKNOWN_FAIL_CLOSED`), ruling R1 | Architect | This repository: `docs/conformance/README.md` (registry PR #28, merged) | A1-05 verdict classes |

Pull requests and heads referenced:

| Reference | Head or merge | State when this amendment was written | Cited as |
|---|---|---|---|
| Registry PR #30 `docs(ext-s1-5): effective-policy identity spec and golden vectors` | `ad95f27201e46b2c838741915aee17d7cc2e5c28` (at drafting); since **merged** as `ab622503633e896bf9a12e518152298268bc50c9` (head `6f17a58e06b0a09501cc3d6e4cac5a491c5c7bb2`) | open at drafting, now merged | provenance; the quoted head is historical |
| Registry PR #31 `EXT-S1-4: F4/F5 integer-second age families` (draft; `DR-CP-AGE-1`) | `17d50c3443ccd96ab95d5c1a0a925845ff1c6f7b` | open draft, not merged | **pending/proposed** provenance only |
| Registry PR #29 `EXT-S1-3` | merge `f618cdf` (`origin/main`) | merged | Repository baseline of this amendment |
| Registry PR #22 (P1 extraction plan) | merge `d2c472e4a09543228bad62235e07a0dedfd7f48b` | merged | Plan baseline (as cited by the frozen ADR) |
| Control Plane source characterization | `cogno-us/cognous-control-plane@7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | cited by `DR-CP-AGE-1` (PR #31), not re-measured here | Source head of the age measurement |

Frozen-document anchors (git blob and sha256) are in section 1 above and in section 0 of the contract amendment; both are verified by `tests/test_contract_amendment_1_pins.py`.

## 4. Consequences for work in flight

- The `EXT-S1-5` implementation PR cites this amendment for the preimage, the identifier rules, the three codes and the `CODES_V2_REV2` declaration, and owns the code change and the new 51-code outcome map.
- The `EXT-S1-4` PR (#31) cites A1-01 for the `AGE_MAX` decision; its `DR-CP-AGE-1` remains the detailed measurement record.
- PR #30 keeps its spec and vectors; when it merges, its section 6 text and this amendment's section 3 must agree byte for byte (the Example 3 digest equals its vector `EP-001`). A divergence is resolved by a new amendment, not by editing this one.

## 5. Non-goals

No implementation; no change to frozen evaluator semantics; no change to `r08-v1` or to `CODES` (46) or `CODES_V2` (48); no edit of any frozen record; no trust-root, key, release or production decision. The amendment becomes effective on merge.
