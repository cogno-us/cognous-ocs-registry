# G1 successor-contract strategy for later migrations (deliverable 6)

G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

**Status: strategy for Architect review. No contract is created, drafted into the contract directory, or implemented by this document.** AD-03 (direction accepted): prefer a versioned successor contract over silently modifying frozen r08-v2 schemas; the specific family/version design is deferred to G1 and requires its own authorization.

## 1. What source says about how a new field enters the Registry

- The contract version is an exact-string switch (`families.table_for_contract_version`): `r08-v1` → `FAMILIES`, `r08-v2` → `FAMILIES_V2`; anything else is `contract_unsupported` with no fallback.
- A family is registered only by editing `FAMILIES_V2` and, separately, `IDENTITY_FAMILIES` (`v2_policy_identity.py`, `REGISTERED_CONTRACT_VERSIONS = ("r08-v2",)`). No test asserts the two tables have equal key sets (AD-04, open).
- There is no per-family version field; `f1ab` is the family id plus a derived family version tag. A new f1ab layout therefore means a new family id or a new contract version.
- Signing input is domain-separated per contract version (`v2_selection.py`); the code set is a numbered revision (`CODES` 46, `CODES_V2` 48, `CODES_V2_REV2` 51).
- Records and cross-version documents are refused (`contract_unsupported`) as definitive REFUSE; this must hold for any successor.
- The frozen contract says "no max_amount slot"; Amendment 3 records `max_amount` and target prefixes as caller-owned residuals. Adding them is a contract change, not an implementation detail.
- F4 (`status_max_age_seconds`, `approval_max_age_seconds`) and F5 (class→age map) are already registered families; successors carry **only the residual fields** (AD-02).

## 2. Options

| Option | Description | For | Against |
|---|---|---|---|
| A. New family ids inside r08-v2 | Register e.g. a numeric-ceiling family in both tables under the existing contract version | Smallest edit; no new signing domain | Edits the frozen r08-v2 surface (tables, code set revision); contradicts AD-03 direction |
| B. One successor contract version carrying all later families (recommended for review) | Define a successor version once, with an extensible family table, introduced when the first wave needs it; `f1ab` carried with identical semantics; new fields added as families under it | Frozen r08-v2 untouched; one new signing domain, one code-set revision; existing records stay valid; oracle suites become version-parametrised | One larger design review before the first new field; coupling of waves to one version |
| C. One successor version per wave | r08-v3 for F1c, r08-v4 for F1d, and so on | Smallest per-wave blast radius | Version churn; consumers must support many exact-string versions; repeated domain-separation and code-set work |

Recommendation for review: **Option B**, designed at G1 and implemented only after separate authorization. The M1 oracle suites should be written version-parametrised from the start so the same vectors can later assert that the successor's `f1ab` is semantically identical to r08-v2's.

## 3. Principles any successor must carry

1. Additive and narrowing-only: Registry data may only shrink what a caller permits; absent, unknown, corrupt or unsupported input never adds permission.
2. Explicit order relation per field before any implementation (equal, subset, minimum, enum strictness); fields without a proven order (target prefixes, target modes, G0 AD-07) stay out until ruled.
3. Explicit deny-all and absent-key semantics per field (`[]` versus `field_missing`).
4. Closed vocabularies and typed reasons; new reasons go through a numbered code-set revision, never reuse with changed meaning; REFUSE versus HOLD classification stated in the contract, not left to an unratified outcome map.
5. Frozen artefacts untouched: r08-v2 schemas, amendments, golden vectors and reason registries are not edited; the successor is a new document set.
6. Domain-separated signing and a separate registered-versions entry; no cross-version acceptance.
7. Existing records are not rewritten; coexistence rules and sunset (if any) are explicit.
8. Residual fields only for F4/F5; already-governed fields are excluded.

## 4. Sequence (each step needs its own authorization)

| Step | Content | Gate |
|---|---|---|
| SC-0 | Scope and principles ruling (PD-8: option A/B/C; which waves share a version) | Architect decision |
| SC-1 | Successor contract draft, documentation only | Architect review; no code |
| SC-2 | Oracle-first vectors for the new fields, written by the independent author before any implementation | Independent author designated |
| SC-3 | Registry implementation of the successor | Authorized wave increment; builder tests plus independent oracles |
| SC-4 | Runtime and Control Plane wiring (adapter, guard, binding, pin export), importer pin updates (AD-16), verifier reasons (AD-17) | Per-component requalification |
| SC-5 | Qualification: same-organization first, independent where the plan requires | Plan v1.5 gates |

## 5. Separation from M1

M1 oracle closure (OW-1..OW-9) is independent of this strategy: it needs no new field, no new contract version and no production change. Later waves M2, M3, M10, M11 and M12 depend on SC-0..SC-2; M1 does not.
