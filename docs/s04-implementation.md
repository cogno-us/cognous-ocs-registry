# S04 — Registry overlay consumer: LocalExecutionPolicy allow-lists

Non-authorizing, builder-side, unqualified. Release, publication and production HOLD. Mechanism only: nothing consumes this overlay, no record is approved for use, and the Runtime is unchanged.

- Plan: OCS-REG-PLAN v1.1, S04 section: https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.1.md (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`)
- Constitution (pinned): https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md
- Authorization: [decisions/2026-10-24-s04-preconditions-and-authorization.md](decisions/2026-10-24-s04-preconditions-and-authorization.md) (P1-P3 as adopted; P3 amended by the operator). Contract: [s03-contract.md](s03-contract.md).
- Materially applicable CA articles: CA05, CA12, CA14, CA18. Tier 1 subject matter (pre-dispatch admission to an effect).

## 1. What it does

`registry_consumer.apply_registry_overlay(caller_policy, trust, manifest_path, record_path)` returns an `OverlayResult`. For exactly `allowed_actions`, `allowed_adapters` and `allowed_units`: `effective = caller ∩ registry`. Everything else in `LocalExecutionPolicy` is the caller's, untouched: institutions, authority domains, target prefixes and match mode, amount and effect ceilings, check order, reason texts and validation. An empty intersection is valid and denies that field's values (the baseline constructor already allows an empty set). `ACCEPT` returns a new policy and `overlay_applied True`. Every `REFUSE` returns the caller's policy **object, unchanged**, `overlay_applied False`, and a reason. The function never raises; an unexpected exception is `consumer_error`.

This is an optional-overlay profile. A refusal means "overlay not applied", not "denied", and is never evidence of compliance. If registry participation is ever mandatory, refusal must fail closed instead; that is a different profile and not authorized here.

## 2. Trust model (P1, P2)

| Asset | Modeled attacker may modify? | How the consumer treats it |
|---|---|---|
| Candidate record file | Yes, including re-digesting it | Accepted only if its file SHA-256 equals the manifest's approved value, then validated by the frozen S03 validator |
| Selection manifest file | No (if replaced, the pin catches it) | Accepted only if its exact bytes hash to the trusted pin |
| The pin (`TrustConfig.manifest_sha256`) | No | Supplied by the operator's trusted invocation; never read from the record, the manifest or the repository |
| Runtime source commitments (S01 blob and SHA-256) | No | Supplied in `TrustConfig`; the installed evaluator file is re-hashed against them |
| Installed Runtime source, the consumer code, the trusted checkout | No | Out of scope: not defended |

Excluded attackers (exclusions, not resistance claims): host administrators, root, a compromised interpreter, malicious maintainers acting with their authority, malicious package or build infrastructure, and anyone who can replace the pin or the installed Runtime. Git and file digests establish integrity against the pin. They do not establish author identity.

Context custody: the S03 validator context is `{runtime_source_blob_id, runtime_source_sha256}` from `TrustConfig` after verification of the installed bytes, and `latest_known_version` from the **manifest's** selected version. The record's own claims never supply any of them. No directory is scanned and no manifest is discovered; paths are explicit arguments.

## 3. Manifest format (`s04-v1`)

One strict JSON object, unknown fields refused, at most 1 MiB, duplicate keys and NaN refused: `manifest_type` `local-execution-allowlist-selection`; `manifest_version` `s04-v1`; `contract_version` `s03-v1`; `record` {`record_id`, `record_version` (1 to 2147483647, the selected version), `record_digest` (the S03 `record_digest`), `file_sha256` (of the exact record file bytes)}; `record_source` {`repository`, `commit`, `path`} (provenance of the approved record; informational, **not verified** by the consumer, which has no git access); `evaluator` {`evaluator_id`, `binding`} exactly the registered S03 values; `runtime` {`source_blob_id`, `source_sha256`} which must equal the trusted `TrustConfig` values.

## 4. Check order and reason codes

First failure wins: `caller_policy_invalid` (not exactly a `LocalExecutionPolicy`; a subclass with a replaced `check` is refused) → `trust_config_invalid` → `runtime_source_unverified` (installed evaluator bytes differ from the commitments, or are unreadable) → `manifest_missing` → `manifest_pin_mismatch` → `manifest_invalid` (also oversize) → `manifest_runtime_mismatch` → `record_missing` → `record_file_mismatch` (also oversize) → `record_refused` (with the S03 reason in `validator_reason`) → `record_identity_mismatch` (record id, version or digest differ from the manifest). `consumer_error` covers any unexpected exception. Files are read once and the same bytes are verified and parsed.

## 5. Candidate fixtures and the pin

`registry_records/` holds one synthetic record and its manifest, matching the S01 fixture policy values. They are test fixtures, not an approved selection.

- Candidate manifest digest (SHA-256 of the committed manifest bytes): `sha256:948ab4f40bb0acf211124db42df2eb5908627e95d84b0019fade2f0b726c2791`
- This digest is **not an approved pin.** P2: a manifest and record merged in the implementation PR are not authorized by the merge. Approving a manifest digest for any use is a separate operator decision, which this sprint does not make. Until then nothing in the repository, Runtime or any process supplies a pin to the consumer, so nothing activates it. `record_source.commit` in the fixture is a placeholder (all zeros) because the consumer does not verify it.

## 6. S05 hand-off: representation coverage

The S03 record contract is stricter than the baseline constructor. A caller policy that needs any of the following cannot be expressed as a record, and the consumer refuses such a record (`record_refused`, S03 `record_invalid`), so the caller policy stays in force: an **empty allow-list** in the record (the caller's own empty set is fine, and the intersection can be empty); entries with **whitespace, control, format or other C*/Z* characters**; entries containing `*`; **more than 256 entries** in a list; entries **longer than 128 characters**. Test group R1 pins each class. S05 must compare original and registry-backed behavior for representable inputs, enumerate these classes separately, and must not claim universal constructor equivalence.

## 7. Tests and review

Battery `tests/test_s04_overlay.py` was written from the adopted required negative-case list and committed before the consumer existed (first commit fails at collection). It builds its own manifests, records and hashes, and drives the baseline `check` for behavioral assertions. It also pins that `registry_contract/` (S03, frozen) and `baseline/` are unchanged, and that the consumer has no discovery, network, process or dynamic-code calls. Mutation checks of the consumer (22 scratch mutations) were all caught after two test gaps were closed; they are not committed. The widening cross-check in the consumer is unreachable by construction (intersection cannot widen); it is defence in depth and is tested by fault injection.

Review (P3 as amended): GitHub Copilot review on the exact final head is the designated independent technical review. **S04 PASS is "Copilot-reviewed, not independently qualified."** The builder wrote both the code and the battery. The exception does not extend to S05, release, publication or production.

## 8. Limitations and no-claims

AI-assisted builder work; not independently qualified. Not wired to Runtime: `LocalExecutionPolicy`, the executor and `baseline/` are unchanged and nothing calls the consumer. No record store, discovery, activation, expiry, tenant scoping, signing, key management or administration. `record_source` is unverified provenance. The consumer verifies the evaluator file's bytes on disk, not the code object loaded in a running process. Behavioral equivalence is untested (S05). The 32 unresolved S02 classifications and the 60-versus-300 observation relationship stay unresolved. S05 is not authorized.
