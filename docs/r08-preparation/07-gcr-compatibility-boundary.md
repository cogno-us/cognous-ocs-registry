# R08-PREP Lane G: GCR compatibility boundary (shared candidates and negative isolation)

## 1. Purpose and scope

Purpose: identify which parts of the proposed OCS registry architecture MAY be shared by any conforming Governed Cognition Runtime (GCR), define each shared candidate with what it proves and does not prove, give an authority-transfer test per field, build a negative isolation matrix, and list questions reserved to a GCR authority owner. Cross-reference and critique of PR #17 file 05 for authority leakage, not a redesign.

Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification.

## 2. Sources and revisions examined

| Source | Pin | Notes |
|---|---|---|
| Registry repo main | `eb850c8d303961d099a123534121aeac280b242b` (rev-parse verified) | plan v1.2 §3, R14-R16, §9; crosswalk A1, A2, A4, A7, A8; `docs/s03-contract.md` |
| PR #17 `docs/registry-schema-analysis/` | head `bdfb2b7268690d9406cc1de257dc6feede0fdb5a` (rev-parse verified) | file 05 (common envelope), file 08 (D1-D13, V1-V9, GCR Architect questions) |
| ISS Core PR #12 review (8 documents) | head `547b9052805b7e57ee44ae15f064725b97823405` | all eight read in full: architectural-review, authority-crosswalk, composition-semantics, envelope-compatibility, integration-roadmap, open-decisions, qualification-plan, transaction-binding. Each cites OCS v1.2 PR #16 head `100aa407...` and ISS Core main `f6723d54...` (S04), not the merged v1.2 |
| Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` | CA05, CA12, CA14, CA18 text read (lines 92-146); other articles not read for this lane |

NOT inspected: **COG-REG-SHARED-ADD-01 (7-page addendum) was not available in any repository or project material.** ISS Core source (`versioned-governance.ts`, `state-delta.ts`, `governed-memory.ts`, Governor channels), the ISS static plan, ISSBench V2 and ISS V6 monograph were not inspected; every statement about ISS behavior below rests on the eight review documents, which are secondary. Control Plane/Runtime clones not inspected (no OCS effect-time contract was needed for this lane). PR #13 not inspected.

Statements that rest ONLY on plan v1.2 / crosswalk summaries of the addendum (not on the addendum): that it "defines shared outer conventions with separate domain authority and warns against cross-domain proof transfer" (plan §2); crosswalk A2 "addendum §§1, 3, 5, 7-8", A4 "§§4, 10", A7 "§6", A8 "§§12-13" section mappings. The section numbers are the crosswalk's claims; I did not verify them. PR #17 file 05 §0 likewise states it was built without the addendum text (open decision D10).

## 3. Findings from source

1. [EXISTING] S03 record (`docs/s03-contract.md` §3) carries `record_id`, `record_version`, `record_type`, `contract_version`, `status`, `non_authorizing`, `supersedes`, `source`, `applicability{runtime_source_blob_id}`, `evaluator{evaluator_id,binding,supplies}`, `data_digest`, `provenance`, `record_digest`. Digests are integrity, not authenticity; S03 "provides no authentication"; case L1 pins that an altered and re-digested record is ACCEPTED. [DEV-TESTED by `tests/test_s03_contract.py`, not executed by me.]
2. [EXISTING] S03 `applicability` is an OCS Runtime evaluator source blob id, and `evaluator` is a single OCS Runtime binding (`LocalExecutionPolicy.check`). Both are OCS-specific values; neither has a domain or system namespace.
3. [EXISTING] S03 has no selection object, no epoch, no revocation reference. Selection exists only as the S04 manifest (described in PR #17 05 §3; S04 code not re-inspected by me). Consistent with ISS review: "S04 local trusted pin is not authenticated approval" (that sentence concerns ISS S04, a different artifact from OCS S04).
4. [PROPOSAL, PR #17 05 §2] The provisional envelope adds `envelope_version`, `family`, `canonicalization`, `governing_refs`, `applicability.target_consumer` and optional `consumer_profile_id`, and removes time windows from the record. Not adopted; depends on open D1-D3 and D10.
5. [EXISTING, secondary] ISS review documents state: common outer envelope ACCEPT; common payload schema and evaluator REJECT; shared physical service NOT REQUIRED; cross-domain selection authority REJECT (envelope-compatibility). Evidence for ISS S00-S04 is "developer-tested bounded local mechanics" only; no production authentication, atomic negative-record custody, output-envelope enforcement or effect-time OCS authority (architectural-review). I did not verify these against ISS source.
6. [EXISTING, secondary] The ISS review's candidate Record field list includes `effective_conditions` inside the record. PR #17 05 explicitly forbids record-borne time windows. **Tension recorded, not resolved** (see G-06).
7. [EXISTING] Plan v1.2 R14 is documentation-only crosswalk with exit "negative isolation matrix and explicit GCR interface-readiness disposition (not an implementation approval)"; R15 requires independent GCR readiness; R16 requires "a matched policy identity that confers no transferable decision authorization". The matrix below is a candidate input to R14, not the R14 exit.

## 4. Candidate contract / design [PROPOSAL throughout]

### 4.1 Boundary rule

[PROPOSAL] The only thing shared is a **reference vocabulary** (names, formats and verification rules for identifying and integrity-checking configuration data). Nothing shared carries a verdict. A shared field answers "which data is this and has it changed?"; it never answers "may this be used, here, now?". Each domain owns its own answer to the second question.

### 4.2 Shared candidates (each is a CANDIDATE for sharing, not a decision to share)

Authority-transfer test (ATT): "If a foreign consumer sees only this field, can it infer permission?" Required answer for every candidate: NO.

| # | Candidate | Definition | Proves | Does NOT prove | ATT |
|---|---|---|---|---|---|
| S1 | Record identity (`record_id`, `record_version`) | Stable name plus strictly increasing integer within one issuing namespace. Must be namespaced by domain/system, else identical ids collide across domains (S03 id pattern has no namespace) | That two references name the same logical record in that namespace | That the record exists in a foreign store, is valid, published, approved, selected or applicable to the foreign domain; that it means the same thing to another domain | NO. A matched id across domains confers nothing |
| S2 | Family identity (`family`, S03 `record_type`) | Typed family id naming the payload contract | Which payload schema the author claims | That a foreign consumer supports the family, or that same-named families have the same semantics. Family ids must be domain-scoped; an OCS family name is never an ISS family | NO. Unknown family means unsupported, not permitted |
| S3 | Contract version (`contract_version`, `envelope_version`) | Version of payload contract / envelope layout | Which parse and validation rules apply | Compatibility with a foreign consumer; that newer is better; permission to upgrade | NO. Never negotiated upward implicitly |
| S4 | Provenance | Decision ref, authored time, author, source locator | Who or what the author asserts it came from | Authenticated origin (S03 provenance is informational and unauthenticated); factual truth; approval | NO. Free text asserts, does not authorize |
| S5 | Canonical digest (`data_digest`, `record_digest`, `canonicalization` label) | sha256 over a named canonical form fixed by the consumer's host, not by the record | Bytes match what the digest was computed over under that canonical form | Authenticity, authorization, freshness, currency, selection, or loaded-code integrity. Re-digested forgeries pass (L1) | NO. Highest leakage risk: a "verified digest" must never be rendered as "verified" without qualification |
| S6 | Applicability (`target_consumer` with system namespace; exact component source blob id) | Narrowing statement of where a record MAY be considered | That the author scoped it narrowly; a consumer whose namespace differs must refuse | That the named consumer should or does apply it. It narrows consideration only; `consumer_profile_id` must never select optional/mandatory participation | NO |
| S7 | Registered evaluator reference (`evaluator.id`, revision, source/build identity) | Name of a vetted, domain-registered deterministic code evaluator | Which evaluator the author intends | That the evaluator exists, is registered, is the loaded build, or that any foreign runtime may execute it. A reference is a name, never an invocation | NO. Reference must not be resolvable across domains |
| S8 | Selection identity (`selection_id`, epoch, exact record/version/digest pins) | Name and revision of a separately approved selection | Which exact records a selection names, if its custody is established in its own domain | That selection is approved, authenticated, current, in-interval or withdrawn; that it applies outside its issuing domain. Approval status is not carried by the identity | NO. Foreign selection id is an opaque label, never an input to activation |
| S9 | Supersession and revocation references (`supersedes`, `withdrawal_or_revocation_ref`) | Pointers to a predecessor record or to a withdrawal/revocation artifact | Lineage claimed by the author; that a revocation artifact is named | That lineage is authentic; that revocation has been observed; that absence of a revocation reference means not revoked. A foreign consumer must not infer "still valid" from "no revocation seen" | NO. Absence is not permission |

[PROPOSAL] S8 and S9 are the weakest candidates: a selection or revocation is meaningful only inside the custody of its owning domain. Sharing them means sharing a reference *format*, not any foreign-readable state. I recommend treating them as candidates to share only as opaque, namespaced strings.

### 4.3 Explicitly NOT shared (no common ownership, no common interpretation)

| Excluded | Owner | Registry/shared layer may carry |
|---|---|---|
| Cognitive admission (e.g. claim insertion) | GCR | pinned reference only, as decision metadata |
| Canonical cognitive state / state transition | GCR | no write path; reference only |
| Memory and source custody; non-forgetting | GCR | no deletion or erasure semantics |
| Epistemic reliance and invalidation | GCR | typed evidence-status requirement references only if qualified |
| OCS execution grants | OCS Control Plane/Runtime | nothing |
| OCS effect-time authorization | OCS | nothing |
| Domain-specific evaluators | each domain | S7 reference only |
| Mandatory floors, negative-record custody | each enforcing domain | policy reference only; never a disable switch |

[PROPOSAL] No generic OCS allow-list operator may be assumed to govern cognitive admissibility. OCS allow-list intersection is an OCS-family rule; the ISS review itself says the ISS 512-character bound "is not interchangeable with OCS allow-list evaluator" and marks answer-region composition UNSUPPORTED (composition-semantics). A foreign family needs its own payload schema and evaluator, defined by the GCR owner.

### 4.4 Refusal behavior [PROPOSAL]

Foreign-origin or foreign-namespaced input to an OCS consumer: REFUSE with an explicit unsupported/not-applicable reason; never ignore the field; never treat as a pass; never fall back to latest. For OCS optional overlay profiles (frozen S04 behavior) a refusal returns the caller policy unchanged, which is NOT denial. For any mandatory requirement, behavior needs an approved successor contract and an independently qualified consumer (D7); this lane does not define it.

### 4.5 Negative isolation matrix [PROPOSAL; candidate input to R14, not its exit; all rows NOT EXECUTED, no consumer exists]

Each row: given the condition, the required outcome is that the foreign domain obtains **no authority**. Q-numbers cross-reference the ISS review qualification plan where one applies.

| ID | Condition | Required result |
|---|---|---|
| N-01 | Record id/version/digest identical in OCS and GCR stores | No authorization or applicability in either; each domain resolves only inside its own namespace and custody |
| N-02 | Matching `record_digest` seen by foreign consumer | Integrity only; no selection, no activation |
| N-03 | Foreign selection id/epoch presented to local consumer | Not activated locally; refused as not-local (ISS Q03-like) |
| N-04 | Foreign evaluator reference in a local record | Not resolved, not executed; `evaluator_unsupported` class refusal (ISS Q04-like) |
| N-05 | Unknown family or contract version from the other domain | Explicit unsupported refusal; no best-effort parse |
| N-06 | Foreign record "published" or PR merged | No effect on local selection or activation |
| N-07 | Foreign revocation reference visible, local custody absent | Not treated as local revocation nor as local clearance; local state is whatever local custody says |
| N-08 | No foreign revocation visible | Not evidence of validity |
| N-09 | OCS approved selection presented to GCR | Not cognitive admission, not a StateDelta authority (ISS Q12-like) |
| N-10 | GCR admitted fact or GCR-side selection presented to OCS | Not an OCS grant; OCS requires its own effect-time authorization (ISS Q11-like) |
| N-11 | `latest` or highest version in foreign domain | Never selected implicitly |
| N-12 | Foreign provenance claiming approval | Informational; no authority |
| N-13 | One domain's registry outage or invalid cache | Other domain unaffected; no shared dependency (ISS Q15-like) |
| N-14 | Shared canonical-form label mismatch | Refusal; record cannot introduce a canonical form |
| N-15 | Cross-domain supersession (record claims to supersede a foreign record) | Refused; lineage is intra-namespace only |
| N-16 | `consumer_profile_id` in a foreign record | Narrows applicability only; cannot choose optional/mandatory profile |
| N-17 | Restore/replay of historical cross-reference | Historical reference inspectable; never reactivates current authorization (ISS Q13-like) |

### 4.6 What OCS must NOT depend on [PROPOSAL]

ISS V6 is only a **source/implementation reference** for the GCR role (A1, v1.2 header). OCS R07-R13 and the OCS-only MSOP must not depend on: ISS code, ISS Core S05 or ISSBench completion; any ISS family; ISS selection custody; ISS release status; ISS reference-vocabulary changes; a shared database, authority ledger, common interpreter or common wire service. The dependence runs the other way only after R14/R15 and separate owner decisions. OCS completion is distinct from cross-domain completion (v1.2 §3.4).

### 4.7 Critique of PR #17 file 05 for authority leakage (cross-reference only)

| Item | Leakage risk | Disposition |
|---|---|---|
| `applicability.target_consumer` system-namespace part (05 §2, §5) | Without enforced namespace, id/consumer collisions across domains. Sole cross-system discriminator, so it carries all isolation weight | Keep; make mandatory-refuse-on-mismatch; depends on D10/GCR Q4 |
| `record_id` has no namespace (S03 pattern) | N-01 collision | Add domain-namespaced identity or require pair (namespace, id) [PROPOSAL; see G-02] |
| `canonicalization` label | Cross-domain digest comparison implies equivalence | Per-consumer fixed set (05 already says so); equality of digests across canonical forms means nothing |
| `supersedes` carries id, version, digest | Could be read as validity transfer | Intra-namespace only (N-15) |
| `selected_by`, `governing_refs` | Informational text that a foreign reader may over-trust | Label as non-evidentiary |
| `valid_from/valid_until` in selection, absent in record | Foreign consumer lacking selection sees no interval and may assume perpetual | Absent interval is not permission (05 flags perpetual as open; see 08 item (a)) |
| `record_digest` also naming "source" blob ids | Component-specific ids invite reuse as foreign identity | Treat as OCS-only applicability values, not shared S6 fields |
| `status` in record (S03) | A record that states "active" is read by foreign tools as activation | 05 already flags (D3); shared envelope must not export `status` as activity |

## 5. Constitutional and v1.2 mapping

| Item | Mapping |
|---|---|
| CA05 (fail closed without inventing policy) | unknown family/version/foreign reference refuses; no invented mapping between domains (N-04, N-05) |
| CA14 (secure by construction) | digest is not security qualification; N-02, S5 |
| CA18 (governed policy, protected invariants) | authenticated policy required before activation; shared fields do not provide authentication; mandatory floors stay in domain code (§4.3) |
| CA12 (no unqualified degradation) | no claim that a shared envelope preserves GCR floors; those floors are GCR-owned |
| Plan v1.2 | §3.1 (three objects), §3.2 (no universal algebra, no shared interpreter), §3.3 (binding; not claimed here), §3.4, R08, R14 (exit, with interface-readiness disposition by GCR owner), R15, R16 (matched identity confers no authorization), R17 |
| Crosswalk | A1 (GCR terminology), A2 (authority separation), A4 (minimal shared envelope), A7 (typed composition; no universal epistemic intersection), A8 (sequencing: R14 read-only, R15 separately authorized). Section numbers of the addendum cited by the crosswalk were not verified |

I did not read the other Constitution articles for this lane, and do not infer formal adoption of the Constitution from the plan's references.

## 6. Decisions raised

| ID | Decision | Owner | Blocking consequence | PR #17 overlap |
|---|---|---|---|---|
| G-01 | Which of S1-S9 (if any) are shared at all; S8, S9 only as opaque namespaced strings | OCS Architect + GCR owner | No shared wire contract; R14 crosswalk cannot name shared fields | D1, D2, D10; V1 |
| G-02 | Namespacing rule for record, family and selection ids (system/domain prefix) | OCS Architect (OCS side); GCR owner (GCR side) | N-01 and N-15 cannot be asserted; collision risk | D10; GCR Q4 |
| G-03 | Canonical serialization and digest algorithm for any shared digest, and canonical-form negotiation | OCS Architect + GCR owner; Operator | Shared digests incomparable; ISS review D01 | D1, D10 |
| G-04 | Whether `status`/activity may appear in any shared envelope | OCS Architect | Leakage of self-declared activity (§4.7) | D3; V3 |
| G-05 | Whether selection/revocation references are exchanged at all or kept domain-local | GCR owner + OCS Architect | R14/R16 revocation-propagation tests undefined (N-07, N-08) | V1; D2 |
| G-06 | Whether `effective_conditions` may sit in a record (ISS review candidate) or only in selection (PR #17 05) | OCS Architect + GCR owner | Divergent envelopes; perpetual-record risk | 05 §2; 08 item (b) |
| G-07 | Whether any mandatory-participation profile is ever authorized | Operator | "Mandatory" claims on cross-domain data are meaningless without it; refusals remain overlay-only | D7; V5 |
| G-08 | Independent qualifier for matrix rows N-01..N-17 | Independent qualifier | Rows stay NOT EXECUTED; no isolation claim | D13 |
| G-09 | Retrieval of COG-REG-SHARED-ADD-01 text and digest custody | Operator | This lane's mapping to the addendum remains unverified; if the addendum differs, it governs and this lane may be wrong | D10 |

Dependencies on open S02/PR #13/PR #17 classifications: none of the S1-S9 definitions depends on W8-091, W3-063, W9-027, W8-014, W6-042 or the 60-versus-300 relationship. Any cross-domain F1 (allow-list) family sharing would depend on D1 and D6, but this lane does not propose sharing OCS payloads.

## 7. Questions reserved exclusively to a GCR authority owner (stated, not answered)

- Whether any GCR rule family is configuration-shaped, and what its payload and evaluator are (PR #17 08 GCR Q1, Q2).
- Which GCR component holds selection and pin custody, and the GCR trust root (GCR Q3; ISS review D03).
- Cognitive admission semantics, admissibility of any cited record, and what an acceptable "selection epoch" means for a GCR commit (ISS review D04).
- Source retention versus authorized erasure and legal retention (ISS review D07).
- Memory, reliance, invalidation, canonical state and state transition rules, negative-record custody.
- Whether the shared namespace field is acceptable as the only cross-system field (GCR Q4) and that no shared service, ledger or common payload is required (GCR Q5).
- Output-envelope policy (currently reported unimplemented in the ISS review; I cannot confirm).
- GCR interface-readiness disposition for R14, and the independent GCR authorization for R15.

## 8. Risks and unresolved constraints

- Evidence is second-hand for the GCR side: eight review documents written against OCS v1.2 PR #16 head `100aa407...`, not the merged v1.2. Differences between PR #16 and the merged plan were not diffed by me.
- COG-REG-SHARED-ADD-01 was not inspected. Any divergence between it and PR #17 05, the ISS review or this document makes those documents wrong in that respect.
- Candidate S1-S9 are reasoned from S03 fields, PR #17 05 and the ISS envelope list; none is implemented as a shared contract. No GCR consumer exists and no matrix row has been executed [none QUALIFIED].
- Identifier namespacing is not present in S03, so cross-domain collision is a real near-term property of existing data, not a hypothetical.
- A digest can be verified successfully for a forged or re-digested record (L1); any tooling that shows "verified" across domains risks being read as authority.
- No claim of GCR implementation readiness is made, and no claim of cross-domain atomicity. Cross-domain commit consistency is out of scope; each domain owns its boundary (v1.2 §3.3) and any cross-domain behavior beyond reference matching is unproven.
- The ISS review notes the S04 pin is not authenticated approval; OCS has the same open authentication question (D2). Sharing a field format cannot close it.
