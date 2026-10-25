# 06 Successor schema and family payload proposals

**Proposal only. Not implemented. No file in this directory is read by any code.** The examples are **ILLUSTRATIVE**: digests are placeholders, values are invented, and none is a valid S03 record or a real policy. Labels: [V] [R] [I].

## 1. Four layers, kept apart

| Layer | Content | Status |
|---|---|---|
| Current implemented contract | S03 `s03-v1` record, validator, S04 consumer, S05 evidence for F1a | Frozen on `main`; unchanged by this work |
| Proposed successor | Envelope (05) plus typed family payloads (this file) | Proposal |
| Unsupported historical representations | S05 classes E01 to E19 (values the historical constructor accepts and S03 refuses). E20, the empty-string entry, is not a representation gap: the historical constructor already rejects it, so no such historical policy can exist [V, `docs/s06-representation-and-e05.md`]; the 3,190 catalogue entries; reason vocabularies as policy | Not representable; remain so |
| Future engineering work | Anything in 09 | Not authorized |

## 2. Design rules

1. **Minimal common envelope** (05 §2). Family-specific data lives only in `data`.
2. **Typed family payloads.** One `family` id per payload type, each with a closed field list, its own `contract_version` and a registered evaluator. No generic key-value payload, no expression language, no rule engine. A family that cannot be expressed as closed typed fields stays in code.
3. **Version compatibility.** `envelope_version` and `contract_version` are exact-match against the consumer's supported set. A consumer refuses a higher or unknown version; it never reads a newer record "best effort". `s03-v1` records remain valid under their own contract and are never reinterpreted as a successor family.
4. **Canonicalization.** The canonical form is named in the record. Existing form: JSON with sorted keys, separators `(",",":")`, `ensure_ascii`, sha256, as S03. A new canonicalization id is a version change. Strict parsing: duplicate keys, NaN/Infinity, trailing data and invalid UTF-8 are malformed (current validator and consumer already do this [V]).
5. **Applicability constraints.** Exact match on target consumer namespace and id, exact component source blob id(s), optional profile id. No version ranges, no wildcards. A record whose applicability does not match the consumer is refused, never "partially applied".
6. **Selection references.** A record never references its own selection. A selection references records by id, version and `record_digest`.
7. **Supersession.** Version n names version n-1 by id, version and digest; the chain is checked by the validator; a selection names exactly one version per record id. Supersession is a lineage fact; it does not activate or deactivate anything.
8. **Mandatory versus optional dependency.** Set by the consumer's ACTIVATION profile (05 §4). Optional: refusal means not applied. Mandatory: refusal means the consumer denies. A record cannot choose.
9. **Unsupported-value handling.** An unsupported value is refused whole (`record_invalid` or a family-unsupported class), never coerced, truncated or skipped. Values outside the typed domain (for example a lone surrogate, S05 E05) are refused; the registry never claims equivalence for them.
10. **No widening.** For each field the family states its stricter direction and composition (04 §3). The consumer computes the effective value from the caller's value and the record; the result is never broader than the caller's.

## 3. Refusal and error classes

Existing S03 codes (12, ordered) and S04 codes are unchanged [V]. Proposed additions for a successor, each an extension class and not a modification of the existing ones:

| Class | Meaning |
|---|---|
| `envelope_unsupported` | unknown `envelope_version` |
| `family_unsupported` | unknown `family` or family `contract_version` |
| `canonicalization_unsupported` | unknown canonicalization id |
| `consumer_namespace_mismatch` | `target_consumer` namespace or id differs from the consumer's |
| `evaluator_revision_unknown` | evaluator source blob not registered |
| `selection_unauthenticated` | selection digest does not match the pin (existing S04 `manifest_pin_mismatch` maps here) |
| `record_not_in_selection` | record absent from the selection or digest differs |
| `record_expired`, `record_not_yet_effective` | `effective_conditions` outside the trusted clock |
| `requirement_conflict` | two records impose incompatible requirements on one field and the family has no ruled composition |
| `dependency_missing` | a mandatory dependency (for example F7 destination capability) is absent |
| `composition_unsupported` | the family has no ruled non-widening composition |
| `widening_attempt` | a post-composition assertion fails because the computed effective value is broader than the caller's (generalisation of `widening_violations`). This indicates a defect in a family's composition and is not expected in conforming operation: a registry value that is a superset of the caller's is clamped by intersection and is **not** a refusal |

Refusal means "not applied" under the optional profile and "deny" under the mandatory profile. Neither is an authorization.

## 4. S03/S04 migration compatibility

- `s03-v1` records, the S04 manifest `s04-v1`, the consumer API and the S05 oracle are unchanged. A successor validator would be a **new module** that handles successor records and delegates to the existing validator for `s03-v1`. Nothing in `registry_contract/` or `registry_consumer/` is edited.
- The three-field F1a record is representable as a successor `local-execution-allowlist` payload with identical `data`; its `record_digest` would differ because the envelope differs. No digest of an existing record changes.
- The `s03-v1` acceptance gate is preserved unchanged: the frozen validator refuses every record whose `status` is not `active` (`status_not_active`; `registry_contract/validator.py:232-233`, pinned by `tests/test_s03_contract.py`). The successor must not accept a `proposed`, `superseded` or `withdrawn` `s03-v1` record on the strength of a selection. External activity semantics (selection and ACTIVATION) apply only to successor-format records (08 D3).
- S05 equivalence results do not transfer to any successor. A successor needs its own differential evidence (07).

## 5. Illustrative payloads

### 5.1 F1 LocalExecutionPolicy (F1a + F1b + F1c) [ILLUSTRATIVE]

```json
{
  "family": "local-execution-policy",
  "contract_version": "example-0",
  "data": {
    "allowed_units": ["unit-a"],
    "allowed_adapters": ["adapter-a"],
    "allowed_actions": ["action-a"],
    "allowed_institutions": ["institution-a"],
    "allowed_authority_domains": ["domain-a"],
    "max_effects_ceiling": 1
  }
}
```

Composition: five sets by intersection; `max_effects_ceiling` by minimum with the caller value. `max_amount` is omitted because binary64 handling (W1-015) and the classification of the ceiling (W8-091) need rulings first. `allowed_target_prefixes` and `target_match` are excluded (F1d, 04 §4.1).

### 5.2 F6 agent permission allow-list [ILLUSTRATIVE]

```json
{
  "family": "agent-permission-allowlist",
  "contract_version": "example-0",
  "data": {
    "agents": {
      "agent-a": ["read", "write"],
      "agent-b": ["read"]
    },
    "agents_absent_from_record": "<UNDECIDED: unconstrained | deny>"
  }
}
```

The field `agents_absent_from_record` is shown only to mark open decision D5; it is not a proposed value. Composition per agent: intersection. The evaluator `PermissionSystem.is_allowed` is not in this repository's baseline.

### 5.3 F7 dedupe profile [ILLUSTRATIVE]

```json
{
  "family": "dedupe-profile",
  "contract_version": "example-0",
  "data": {
    "provider_horizon_seconds": 300,
    "escalation_deadline_seconds": 400,
    "dedupe_ttl_seconds": 600,
    "requires_destination_capability": "dedupe-ttl/0.1"
  }
}
```

Joint check on the effective triple: `provider_horizon <= escalation_deadline < dedupe_ttl`. The capability is a mandatory dependency on the destination. Composition is conditional on rulings D4 and W3-063 (04 §4.2). Values are invented; the Runtime default of 600 is the only number taken from source.

### 5.4 F4 freshness profile [ILLUSTRATIVE]

```json
{
  "family": "freshness-bounds",
  "contract_version": "example-0",
  "data": {
    "authority_status_max_age_seconds": 60,
    "destination_observation_max_age_seconds": 300,
    "clock_tolerance_seconds": 5
  },
  "effective_conditions": { "not_after": "2099-01-01T00:00:00Z" }
}
```

The two ages are separate typed fields because they bound different observed objects (03 §3); no rule relates them. The clock is the consumer's trusted clock, never the record's. Composition per age: minimum under a ruled direction and with a code floor. `clock_tolerance_seconds` has no ruled direction and would be excluded until one is ruled.

### 5.5 F5 authority profile (tightening subset) [ILLUSTRATIVE]

```json
{
  "family": "authority-class-tightening",
  "contract_version": "example-0",
  "data": {
    "classes": {
      "class-a": { "irreversible": true, "max_status_age_seconds": 30, "on_unreadable": "refuse" }
    }
  }
}
```

The payload can only tighten a class the host already declares: it cannot add a class, and `allow_synthetic_resolver` and similar relaxing toggles are not representable. A class absent from the host profile is refused (`requirement_conflict`).

### 5.6 ISS example

None. No ISS architecture source was available to this analysis, so no ISS family is proposed. An ISS example is deferred to the ISS Architect (08).
