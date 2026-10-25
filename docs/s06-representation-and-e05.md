# S06 A and B — Representation-contract disposition and the E05 surrogate boundary

Non-authorizing, builder-side, Copilot-reviewed at most, not independently qualified. Release, publication and production HOLD. This page records existing behavior. It changes no S03 rule, no S04 semantics and no baseline behavior.

- Plan: OCS-REG-PLAN v1.1 (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`). Constitution pin: https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md
- Authorization: [decisions/2026-10-24-s06-authorization.md](decisions/2026-10-24-s06-authorization.md).
- Evidence: contract rules [s03-contract.md](s03-contract.md) section 3; consumer [s04-implementation.md](s04-implementation.md) sections 1 and 6; frozen classes `tests/s05_expectations.json` (E01–E20, B01–B05); results `docs/s05-results/differential-raw.json`; report [s05-equivalence-report.md](s05-equivalence-report.md).

## A. Historical constructor versus S03 record validation

Scope: the three fields `allowed_units`, `allowed_adapters`, `allowed_actions`.

**The five questions, answered per value class.** Terms: (1) *historically valid* means the baseline `LocalExecutionPolicy` constructor accepts the value (`safe_executor.py:374-387`: the field is a `frozenset` of non-empty `str`; an empty set is allowed; no character, length or size limit). (2) *Representable in S03* means a record containing it passes the S03 validator. (3) *Accepted by S04* means `apply_registry_overlay` returns ACCEPT for a record containing it, which additionally requires the pin, manifest, identity and source checks. (4) *Registry refusal* is S04 `REFUSE / record_refused` with S03 reason `record_invalid`. (5) *Caller authoritative* means the caller-constructed policy object is returned unchanged.

| Value class (frozen ID) | 1 Historically valid | 2 S03-representable | 3 S04 accepts | 4 Registry refusal | 5 Caller authoritative |
|---|---|---|---|---|---|
| Empty list in the **record** (E01) | yes (an empty set) | **no** (lists must be non-empty) | no | yes | yes, on refusal |
| Entry with a restricted Unicode category: format Cf (U+200B, E02), separator Zl (U+2028, E03), control Cc (NUL E04, DEL E14, U+001F E15), surrogate Cs (E05), unassigned Cn (E06), private use Co (E07) | yes | **no** (no C* or Z* characters) | no | yes | yes, on refusal |
| Whitespace and control characters: space inside, leading, trailing (E08–E10), tab (E11), newline (E12), no-break space Zs (E13) | yes | **no** | no | yes | yes, on refusal |
| Wildcard `*` alone or inside an entry (E16, E17) | yes (an opaque string; the baseline does no wildcard matching) | **no** (no `*`) | no | yes | yes, on refusal |
| Entry longer than 128 characters (E18; 129 tested) | yes | **no** | no | yes | yes, on refusal |
| List longer than 256 entries (E19; 257 tested) | yes | **no** | no | yes | yes, on refusal |
| Empty-string entry (E20) | **no** (constructor rejects it) | no | no | yes | n/a: the historical policy cannot exist |
| Entry of exactly 128 characters; list of exactly 256 entries (B01, B02) | yes | **yes** | yes | no | no: overlay applied |
| URN-style punctuation, non-ASCII letters, emoji category So (B03–B05) | yes | **yes** | yes | no | no: overlay applied |

Notes that the table cannot carry:

- **Ordering and duplicates are not limits.** The baseline holds a set; S03 requires sorted, duplicate-free arrays. Any set can be written that way, so these rules reject nothing a set can express. They fix a canonical form for the digest.
- **Refusal is whole-record.** One unsupported entry refuses the record. The registry never supplies the supported part of a list.
- **Refusal leaves the caller authoritative, which can be broader than the record's author intended.** The consumer is an optional overlay (S04 section 1). A record that tries to say "deny every value of this field" with an empty list is refused, so the caller's own list stays in force. An author can express deny-all only by listing values the caller never permits, which yields an empty intersection. This is existing, designed behavior. It is recorded here so nobody reads a refused empty-list record as having denied anything.
- **A caller policy that lists an unsupported value is still narrowable.** A representable record applied to such a caller yields the intersection; the unsupported value is dropped, not refused (S05 `designed_narrowing`, a designed outcome, not an inequivalence).
- **S04 adds only reasons unrelated to values:** pin, manifest, identity, installed-source and file-hash checks ([s04-implementation.md](s04-implementation.md) section 4). Value acceptance in S04 equals S03 ACCEPT.

**What S05 checked, kept separate.** *Refusal checks* (S03 and consumer outcomes, constructor acceptance): all of E01–E20 × 3 fields passed as frozen, including E05 and E20. *Per-class behavioral comparisons* (the caller policy governs after refusal and behaves like the historical policy; designed narrowing; recorded as `under_refusal` and `designed_narrowing` rows): present and passing for E02–E04 and E06–E19 (17 classes × 3 fields = 51 comparisons); **E05 was SKIPPED** (three comparisons, see section B); **E01 has none** (the harness guards them with `if caller_ok and entries`, and an empty list has no entry to exercise); **E20 has none** (no historically valid policy exists for it). For E01 the general behavior after any refusal is covered only by the refusal group (R01–R34 each check that the caller policy's behavior is unchanged over the G1 operations), not by a per-class comparison. **Erratum:** the S05 report's table line "57 full; 3 partial" for the representation group overstates this; the accurate split is 51 per-class behavioral comparisons passed, 3 skipped (E05), and 6 rows (E01 and E20 × 3 fields) with refusal checks only. The S05 report is a pinned historical record and is not edited; this page is the correction. For representable values the registry-backed policy equals the historical policy built from the intersection (G1, G2, B01–B05). Details: [s05-equivalence-report.md](s05-equivalence-report.md).

**Future contract change (recommendation only; not authorized; S03 rules unchanged):** if the program later needs to (a) express deny-all, or (b) cover values with whitespace or other excluded characters, that is a new contract version with its own decision and negative battery, because it changes what a record can say and, for (a), the meaning of refusal. Neither is needed for the tested profile.

## B. E05: the lone-surrogate boundary

**Finding (S05).** An entry containing a lone surrogate (`a\ud800b`) is accepted by the historical constructor, refused by S03 (category Cs, `record_invalid`) and refused by the consumer, as for the other classes. It differs in one way: no operation carrying that value can pass the historical snapshot boundary. `snapshot_envelope` calls `_admit_plain_data`, which sizes each string with `item.encode("utf-8")` (`safe_executor.py:163`); a lone surrogate raises `UnicodeEncodeError` there, before `LocalExecutionPolicy.check` runs.

**Three behavioral SKIPs are preserved.** The S05 harness could not compare behavior for E05 on any of the three fields, because both paths fail identically before policy evaluation. They are recorded as SKIP (`skipped_behavior_check` in `docs/s05-results/differential-raw.json`; `totals.skipped` = 3). They are **not** PASS and are not reclassified. The constructor, S03 and consumer checks for those rows ran and passed.

**Four properties that must not be conflated:**

| Property | E05 value | Where it is decided |
|---|---|---|
| Constructor acceptance | accepted (a non-empty `str`) | `__post_init__`, `safe_executor.py:374-387` |
| Snapshot representability | **not representable**: UTF-8 encoding fails | `snapshot_envelope` → `_admit_plain_data`, `safe_executor.py:163` |
| Policy evaluation | **not reached** through the executor path; whether `check()` could evaluate such a string if called directly with a hand-built object was not tested and is not claimed | `LocalExecutionPolicy.check` |
| Registry-record representability | **not representable**: category Cs is refused | S03 validator, `record_invalid` |

**What this does and does not mean.** It does not show an inequivalence: the registry-backed path cannot admit what the historical path cannot even snapshot. It does mean S05 demonstrates no equivalence for that class, and none is claimed. No baseline snapshot semantics are changed or proposed here. Whether the baseline boundary should reject such strings earlier, with a clearer reason, is a question for the Runtime owners and would change historical Runtime behavior, which is outside this program.
