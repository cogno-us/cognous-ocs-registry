# 05 Common envelope proposal

**Proposal only. Not implemented. Not authorized.** Labels: [V] [R] [I].

## 0. Source limitation

The brief names `COG-REG-SHARED-ADD-01`. Its text was not provided to this analysis; the S06 authorization record also says it was named by the operator and not provided to the registry sessions [V, `docs/decisions/2026-10-24-s06-authorization.md`]. The envelope below is built only from the field list in the brief and the current S03/S04 documents. If the addendum differs, the addendum governs and this file is wrong in that respect.

## 1. Three separate things

| Concept | What it is | Who controls it | Where it lives |
|---|---|---|---|
| RECORD | Versioned, typed, digest-bearing statement of a family's data | Author (unauthenticated provenance) | Registry repository |
| SELECTION | A manifest that names which record versions a consumer may consider, approved by an independent authority | Operator or delegate, separately attributable (T3) | Registry repository (the bytes); approval and pin held outside |
| ACTIVATION | The host's decision to use a selection: pin custody, optional or mandatory profile, trusted clock, trusted source | Host trusted configuration (`TrustConfig` today) | Outside the registry |

Rules:

1. A record must not authenticate or authorize itself. A digest is integrity, not authenticity (T2).
2. An approved selection manifest is not an execution grant. It narrows what a consumer may consider; it never grants an effect.
3. Neither a record nor a selection can declare itself mandatory, active or approved. Whether registry failure is fatal is a property of ACTIVATION (§4). A record that fails to load cannot force anything, so a self-declared "mandatory" flag is unenforceable.
4. A registry value may only narrow what the caller already permits (CR-NW generalised per family, 04 §3). No record can issue a grant, approval, resolver or holder.

## 2. RECORD envelope

| Field | Req | Meaning | S03 counterpart |
|---|---|---|---|
| `envelope_version` | yes | version of this envelope layout | new |
| `record_id`, `record_version` | yes | identity; version is a positive integer | `record_id`, `record_version` |
| `family` | yes | typed family id (for example `local-execution-allowlist`) | `record_type` |
| `contract_version` | yes | version of the family payload contract | `contract_version` (`s03-v1`) |
| `non_authorizing` | yes | constant `true` | same |
| `source` | yes | repository, commit, path, blob id, sha256, line ranges of the governing source | `source` |
| `provenance` | yes | decision reference, authored time, author; informational, unauthenticated | `provenance` |
| `canonicalization` | yes | identifier of the canonical form used for digests (for example `json-sorted-compact-ascii/1`) | implicit |
| `data` and `data_digest` | yes | family payload and sha256 of its canonical form | same |
| `record_digest` | yes | sha256 over the canonical envelope excluding itself | same |
| `applicability` | yes | `target_consumer` (system namespace plus consumer id), exact component source blob id(s), optional profile id | `runtime_source_blob_id` |
| `evaluator` | yes | registered code reference: id, exact source blob id, and `supplies` | `evaluator` (no revision today) |
| `governing_refs` | optional | references to decisions or constitutional clauses; informational | `decision_ref` |
| `effective_conditions` | optional | declarative `not_before`/`not_after` evaluated by the consumer's trusted clock; absent means no time limit | none |
| `supersedes` | yes | null, or id, version, digest of the immediately preceding version | same |

Deliberately absent: signatures or key identifiers (an authentication scheme is a separate decision, 08 D2); an `approved`, `active` or `mandatory` flag; any expression, predicate or script field (no general-purpose policy interpretation); any grant-bearing field; any reference to an ISS authority.

Open point: S03 includes `status` (`proposed`, `active`, `superseded`, `withdrawn`) inside the record, so a record states its own activity. In the successor, activity is a property of SELECTION and ACTIVATION. The record would keep only author intent (`proposed`, `withdrawn`); `active` and `superseded` would be legacy values readable only for `s03-v1` records. This is a design question for the Architect (08 D3).

## 3. SELECTION manifest

| Field | Meaning |
|---|---|
| `selection_id`, `selection_version` | identity |
| `target_consumer` | must equal the consumer's own namespace and id, else refused |
| `entries[]` | each: family, record id, record version, `record_digest`, file path; no ranges |
| `runtime_source` | exact blob id of the trusted evaluator source (as `s04-v1` does) |
| `selected_by` | reference to the separately attributable decision; informational |
| `valid_until` | optional; evaluated by the trusted clock |

The manifest digest is compared to a pin supplied by trusted invocation, never read from the repository (T4). The committed candidate manifest digest `sha256:948ab4f4…` is not an approved pin (T8) and is unaffected by this proposal.

## 4. ACTIVATION (not stored in the registry)

Host configuration: the pin, a trusted clock, the trusted evaluator source, and a **per-consumer profile** that is either *optional overlay* (a refusal means the overlay is not applied and the caller policy stands, T7) or *mandatory* (a refusal makes the consumer deny). Mandatory is a different, unauthorized profile today. The profile is chosen by the host, not by a record.

## 5. ISS and OCS

- Each system keeps its own authority boundary, selection custody and pin custody. There is no shared registry service and no shared authority ledger.
- The envelope is a layout, not a shared service. It does not require common family payloads: an ISS family, if one exists, is defined only by the ISS Architect.
- `applicability.target_consumer` includes a system namespace. A consumer refuses records and selections whose namespace is not its own.
- No ISS architecture source was available to this analysis; no ISS family or ISS semantics are asserted (08, section for the ISS Architect).
