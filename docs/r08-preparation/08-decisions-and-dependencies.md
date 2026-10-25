# R08-PREP 08: Integrated decision register, reconciliation record and dependency map

Purpose: (1) record the contradictions and tensions found while reconciling documents 01-07 and how each was handled; (2) consolidate every decision raised by the lanes into one register with owner, class and blocking consequence, cross-referencing (not restating) the existing PR #17 register D1-D13 and alignment rows V1-V9; (3) map findings to R07, R08, R09, R10, R11, R12, R14, R15, R16 and R17; (4) separate what can proceed independently from what must stay blocked.

Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification. This document settles nothing; where it records a position it says whose ruling is needed.

## 1. Sources and revisions examined

| Source | Revision |
|---|---|
| Registry repo `cogno-us/cognous-ocs-registry` `main` | `eb850c8d303961d099a123534121aeac280b242b` (rev-parse verified at integration) |
| Plan v1.2 / crosswalk A1-A10 | blobs `32319775c6e2d9c3fff1e2171c8f4c9d096911d6` / `a53a5b31e11d3176377588497c73acc0250b6cfe`; v1.1 `6ece90f6...` frozen, not rewritten |
| PR #13 `docs/historical-recovery/` | head `2a2fb9c668ed2a428e67344b16f96b87b4e82d88` (provisional input; not duplicated) |
| PR #17 `docs/registry-schema-analysis/` | head `bdfb2b7268690d9406cc1de257dc6feede0fdb5a` (provisional input; D1-D13, V1-V9 in its file 08) |
| ISS Core PR #12 GCR review | head `547b9052805b7e57ee44ae15f064725b97823405` (eight documents; reference only; ISS Core not modified) |
| Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; `ENGINEERING_CONSTITUTION.md` and `ADOPTION.md` read (see R-07) |
| Control Plane / Execution Runtime | clone heads `7a4bcd40...` / `c5e97e87...`; S01/S02 pins `0a41faa9...` / `ec728da6...` (see R-09) |
| COG-REG-SHARED-ADD-01 | **Not available; not inspected.** Cited only through what plan v1.2 and the crosswalk say about it |

Not inspected by the integration owner beyond reading documents 01-07 in full: lane source claims were not independently re-derived; no test suite was run for this PR.

## 2. Reconciliation record (contradictions and tensions found)

| ID | Finding | Handling |
|---|---|---|
| R-01 | Outcome vocabulary: lane D (04 section 4.3) and the Control Plane (`hold` for effect-time refusal; `deny` emitted only by one adapter, per 06) use REFUSE/DENY/HOLD/RETRY differently from lane F's first draft | 04 section 4.3 is the controlling candidate; 06 section 4.1 now defers to it. Mapping onto existing `failure_class`/reason codes stays unsettled (LD-02). No new reason codes are proposed as approved |
| R-02 | RETRY: lane F first said "same inputs, transient"; lane D says a new transaction under a freshly resolved pin, new attempt identity | Lane D definition adopted (it matches the existing `retry_eligible: False` rule for in-doubt effects) |
| R-03 | `effective_conditions` meant two things: the ISS review's record-borne validity field (07 G-06) and lane D's observed grant/approval/evidence state | Lane D's tuple member renamed `observed_authority_conditions`. Where an effective interval lives (record vs selection) stays open for the GCR envelope (G-06); documents 01 and 02 place interval, epoch and revocation reference in SELECTION, consistent with the reading of v1.2 section 3.1 recorded in PR #17 V1. Not adjudicated |
| R-04 | Lane D decision IDs `D-01..D-08` collide visually with PR #17 `D1..D13` | Lane D IDs written `LD-01..LD-09` (LD-09 added after review). All other lane prefixes (A-, B-, C-, E-, F-, G-) are unchanged |
| R-05 | Participation granularity: PR #17 file 05 sets it per consumer profile; plan v1.2 section 3.2 (optional vs required "per operation") and section 3.4 set it per operation. Lane A's A-03 raised selection granularity | Per-operation participation is **settled by v1.2** (PR #17 V5 records the divergence; correction is pending in PR #17). A-03 is narrowed to the selection-scope key and one-effective-per-scope rule |
| R-06 | F1 and the Control Plane: lanes C and E agree no Control Plane source references `LocalExecutionPolicy`; the policy caller is an unnamed host integrator (C-01/E-05). Lane D's binding extends the claim `policy_state` row, which is the grant policy channel and does not carry `LocalExecutionPolicy` values; `policy.check` runs before the claim, outside the atomic transaction (03 section 3.4) | Recorded as a design constraint, not resolved. The tuple binding can detect a changed selection/record/evaluator identity at commit only if the selection is modelled as a policy row the destination reads (C-03/LD-01); it does not re-evaluate narrowed allow-lists inside the transaction. Alternative: evidence-only attachment (03 I2.2), which does not prove transaction-time authority |
| R-07 | Constitution reading was uneven across lanes (G read CA05, CA12, CA14, CA18 only; A did not read ADOPTION.md). Integration owner read `ADOPTION.md`: it states that publication, possession, a passing check or a merge does not establish adoption, and that an adopting authority must identify exact revision, scope and effective point | No adoption instrument for the OCS registry program was found in the materials examined; the Constitution is cited as pinned normative guidance only, and **formal adoption is not claimed or inferred**. Article citations in each document are limited to what that lane says it read |
| R-08 | ISS review documents cite OCS v1.2 PR #16 head `100aa407...`. `git diff --stat 100aa407 origin/main -- docs/plans/PROJECT_PLAN-v1.2.md` shows the merged plan differs (49 insertions, 35 deletions) | Differences not analysed line by line. Every ISS-derived statement is secondary and must be rechecked against the merged v1.2 text by the owners in R14 |
| R-09 | S01/S02 pins vs later clone heads: Runtime head adds terminal approval revocation not present at `ec728da6`; Control Plane head differs from `0a41faa9` in one file (`local_authority_effect.py`); other cited files had identical blobs (03 section 1, 04 section 1) | Claims are labelled by revision. Which Runtime/Control Plane revision is the integration baseline for R10 is an open ruling (LD-06) |
| R-10 | A-09 asks for builder confirmation that `status` inside the digested body makes in-place supersession impossible | Left open (builder-routine). Not confirmed in this PR; nothing in the other documents depends on it beyond the justification of lifecycle rule C2 |
| R-11 | Field names for the same concepts are not yet harmonized across documents (for example `selection_ref`/`selection_id`, `consumer_id`, scope tuple in 02 vs 03 vs 04) | Harmonization is R08 contract work, not done here. No contradiction of meaning was found; no field list in this PR is normative |
| R-12 | Plan v1.2 contains two headings numbered "3.3" (atomic effective-policy binding; the threat-model paragraph) | Documents cite "section 3.3" for atomic binding and name the threat model explicitly where meant |

## 3. Decisions already settled by v1.2 (not reopened here)

Three separate objects RECORD / SELECTION / ACTIVATION (section 3.1); authority separation, configuration is non-authorizing, no transfer to GCR or OCS grants (A2); separate lifecycles (A3); minimal shared envelope, no shared database or common interpreter (A4); atomic effective-policy binding with no global atomicity claim (A5, scope clarified); source preservation (A6, GCR-owned); typed composition, unknown composition refuses, no universal epistemic algebra (A7); sequencing R14 read-only before R15 (A8); MSOP is a candidate until the operator adopts it (A9); independent qualification, ISSBench V2 for ISS V6 candidates (A10); explicit deny-all and per-operation participation required, no permissive fallback for required participation (section 3.2); release, publication and production HOLD.

## 4. Consolidated decision register

Classes: **ARCH** OCS Architect ruling; **OP** operator approval; **GCR** GCR-owner-only; **QUAL** independent qualifier; **BLD** builder routine. "Also pending in" cross-references PR #17 D1-D13 / V1-V9 (see its file 08; not restated). PR #13 (historical inventory) is pending adjudication wherever a row cites W-identifiers. "Blocks" names the first phase that cannot start or close.

### 4.1 Lifecycle (document 01)
| ID | Decision | Owner | Also pending in | Blocks |
|---|---|---|---|---|
| A-01 | Adopt three-machine split and transition sets as normative, or amend | OP / ARCH | V3, V1 | R08 |
| A-02 | Record `status` in successor format: absent, author-intent, or event-derived | OP / ARCH | D3, V3 | R08 |
| A-03 | Selection-scope key; one-effective-per-scope and conflict rule (participation granularity itself is settled, R-05) | ARCH | V5, V1 | R08, R10 |
| A-04 | Independent-review level and approver roster for Tier 1 record/selection approval | OP / QUAL | D13, D2 | R09 |
| A-05 | Perpetual selections permitted; default absent interval | OP | PR #17 05 open item (a) | R08 |
| A-06 | Effect on an `effective` selection when its pinned record is withdrawn or superseded | ARCH with GCR owner for shared conventions | none | R09, R10 |
| A-07 | Legacy bridge for `s03-v1`, or S04-only | OP | D3 | R08 migration |
| A-08 | Mandatory vs optional activation profile exists | OP | D7, V5, V6 | R10 |
| A-09 | Builder confirmation of F3 (status inside digest) | BLD | none | R08 justification only |
| A-10 | Archival, erasure and legal-hold authority | OP (GCR owner for cognitive evidence) | V7 | R09 completeness |

### 4.2 Authentication and custody (document 02)
| ID | Decision | Owner | Also pending in | Blocks |
|---|---|---|---|---|
| B-01 | Authentication primitive (BitRep + custody profile, ODES DSSE Ed25519, Control Plane `producer_keys` pattern, or pin-only); no fourth | ARCH then OP | D2, V1 | R09 |
| B-02 | Owner and procedure for issuer enrollment, key ceremony, secure time, trust-snapshot distribution, key storage | OP | D2 | R09 gate |
| B-03 | Whether records need origin signatures or signed selection suffices | ARCH | D2, D3, V3 | R08, R09 |
| B-04 | Role separation: selection authority, record approver, witness; any waiver | OP | D2 | R09 |
| B-05 | Anti-rollback: configuration floor or durable high-water mark | ARCH | none | R09 |
| B-06 | Scope/tenant inside the BitRep custody claim, or in signed selection bytes | ARCH with BitRep owner | V1 | R09 |
| B-07 | May a selection name an older record version (rollback as forward epoch) | ARCH | D3 | R09 |
| B-08 | Status freshness bound and revocation distribution latency | OP | none (depends on 60-versus-300 if freshness families join) | R09, R12 |
| B-09 | Loaded-code integrity (T5): accept exclusion or approve a control | OP / QUAL | none | R09, R17 |
| B-10 | Dependency profile for the verifier (S04 is stdlib-only) | BLD / ARCH | none | R09 |
| B-11 | External witness location and holder | OP | none | R09 |
| B-12 | Independent security review scope and reviewer (gate G2) | OP | none | R09 |

### 4.3 Consumer integration (document 03)
| ID | Decision | Owner | Also pending in | Blocks |
|---|---|---|---|---|
| C-01 | Name the production host integrator that constructs `LocalExecutionPolicy` and the executor | OP / ARCH | related D7 | R10 |
| C-02 | Is a mandatory profile ever authorized (host must not build the executor on REFUSE) | OP | D7 | R10 |
| C-03 | May a selection be expressed as grant `policy_versions` / `PolicyStatus.digest`, or evidence-only | ARCH | D2 | R10 |
| C-04 | Who authenticates `PolicyStatus.digest` adoption (current signer is an asserted name) | ARCH / QUAL | D2 | R10 |
| C-05 | Evaluator compatibility declaration format and approver | ARCH | none | R10, R12 |
| C-06 | Route A, Route B, or both in the MSOP | OP | none | R10 |
| C-07 | F1 amount/effects ceiling classification (W8-091, W6-042, W8-014) before any numeric field joins | OP | D1, D6 | R11 |
| C-08 | 60-versus-300, W3-063, W9-027 before any freshness/dedupe field | OP | D1, D4, D12 | R11 |

### 4.4 Effective-policy consistency (document 04)
| ID | Decision | Owner | Also pending in | Blocks |
|---|---|---|---|---|
| LD-01 | Extend the claim/destination policy row, or define a separate binding | ARCH | D7, V2 | R10 |
| LD-02 | Map REFUSE/DENY/HOLD/RETRY to existing `failure_class`/reason codes; free text vs closed codes | ARCH | D8 | R10, R17 |
| LD-03 | Mandatory vs optional for the F1 effect profile | OP | D7 | R10 |
| LD-04 | Selection-withdrawal propagation to the destination authority table | ARCH / OP | D2 | R10 |
| LD-05 | Receipt content: policy/approval commitment and selection tuple | ARCH | none | R10 |
| LD-06 | Compatibility with terminal approval revocation (pin vs head); integration baseline revision | OP | none | R10 |
| LD-07 | Independent qualifier for the effect-time path | QUAL | D13 | R17 |
| LD-09 | Selection-expiry binding gap at commit (04 section 4.2) | ARCH | V1 | R10 |
| LD-08 | Classification of W8-091, W3-063, W9-027 for retry/dedupe/cap semantics | OP / ARCH | D1, D6, D12 | R11 |

### 4.5 Minimum operational profile (document 05)
| ID | Decision | Owner | Also pending in | Blocks |
|---|---|---|---|---|
| E-01 | Adopt Option 1, 2 or 3 as candidate MSOP | OP | D11, V6 | R08 scope, R09-R11 sequencing |
| E-02 | Is a required-participation profile in the MSOP, for which operation classes | OP | D7, V5 | R10 |
| E-03 | Deny-all expression and empty-record semantics in the successor contract | OP / ARCH | V4 | R08 |
| E-04 | Is the Control Plane a required registry consumer in the MSOP (brings F4/F5, blocked) | OP / ARCH | D1 | R10, R11 |
| E-05 | Named Runtime construction site and owner approval for a registry hook | ARCH / Runtime owner | none | R10 |
| E-06 | Execution environment declared safe-emulator only | OP | none | R10, R17 |
| E-07 | Authentication mechanism and trust roots for selection (see B-01, B-02) | OP | D2 | R09 |
| E-08 | Independent qualification owner and oracle author for Tier 1 | OP | D13 | R11, R17 |
| E-09 | New contract version vs envelope validator route for F1; successor must not edit `s03-v1` | ARCH | D3 | R08 |
| E-10 | Whether F1b is an additive increment after the MSOP | OP | D11 | R11 |

### 4.6 Qualification (document 06)
| ID | Decision | Owner | Also pending in | Blocks |
|---|---|---|---|---|
| F-01 | Designate the independent qualifier for OCS Tier 1 registry families | OP | D13 | R11 activation, R17 |
| F-02 | Confirm ISSBench V2 as GCR-side qualifier; one coordinator or two | GCR / OP | V7 | R15, R16 |
| F-03 | Approve REFUSE/HOLD/DENY/RETRY definitions (04 section 4.3) and the Control Plane `hold` convention | ARCH | V5 | R10, R17 |
| F-04 | May builder-authored S05 expectations be re-approved by the qualifier, or must be re-derived | QUAL | none | R11, R17 |
| F-05 | Home of registry TestSpecs in `cognous-stack-qualification` | ARCH / OP | none | R17 |
| F-06 | Trusted time source and clock-skew rules for expiry rows | ARCH | V1 | R09, R17 |
| F-07 | Whether rollback/revocation detection (epoch/anchor) is in the MSOP | OP | V1, V2 | R09, R17 |
| F-08 | Residual-risk owner for T1-T14 | OP | none | R17 |

### 4.7 GCR boundary (document 07)
| ID | Decision | Owner | Also pending in | Blocks |
|---|---|---|---|---|
| G-01 | Which of shared candidates S1-S9 are shared at all; S8/S9 only as opaque namespaced strings | ARCH + GCR | D1, D2, D10, V1 | R14 |
| G-02 | Namespacing rule for record, family and selection ids | ARCH (OCS side), GCR (GCR side) | D10 | R14 |
| G-03 | Canonical serialization and digest algorithm for any shared digest | ARCH + GCR; OP | D1, D10 | R14 |
| G-04 | Whether `status`/activity may appear in any shared envelope | ARCH | D3, V3 | R14 |
| G-05 | Whether selection/revocation references are exchanged or kept domain-local | GCR + ARCH | V1, D2 | R14, R16 |
| G-06 | `effective_conditions` in a record, or only in selection (see R-03) | ARCH + GCR | PR #17 05 | R14 |
| G-07 | Whether any mandatory-participation profile is ever authorized | OP | D7, V5 | R10, R16 |
| G-08 | Independent qualifier for isolation rows N-01..N-17 | QUAL | D13 | R16, R17 |
| G-09 | Retrieve COG-REG-SHARED-ADD-01 text and digest custody | OP | D10 | R08, R14 |

## 5. Which unresolved classifications the designs depend on

W8-091, W3-063, W9-027, W8-014, W6-042 and the 60-versus-300 relationship (PR #13/#17 D1, D4, D6, D12) gate any family beyond F1a/F1b and any freshness/dedupe/numeric field (C-07, C-08, LD-08). F1a/F1b were not found to depend on them (05 section 6), which is not adjudicated. None of the shared candidates S1-S9 depends on them (07). No document here settles any of them.

## 6. Phase mapping

| Phase | What R08-PREP supplies (candidate) | Decisions to close first | Stays blocked until |
|---|---|---|---|
| R07 inventory | Documents 05, 08: which classifications each design depends on | D1, D10; C-07, C-08; PR #13 and PR #17 adjudication | Operator adopts a migration profile (R07 gate) |
| R08 contract | 01 (lifecycles), 02 section 4.3 (selection object), 03 I1/I4, 05 (MSOP options), 07 (shared candidates) | A-01, A-02, A-03, A-05, A-07, E-01, E-03, E-09, G-01..G-06, G-09 | Operator approves contract version and scope; successor schema distinct from `s03-v1`; GCR Architect preliminary disposition |
| R09 authentication, lifecycles, custody | 01, 02 | B-01..B-12, A-04, A-06, F-06, F-07 | Independent security review of authority-bearing paths (gate G2); trust root exists |
| R10 OCS integration | 03, 04 | C-01..C-06, LD-01..LD-06, LD-09, E-02, E-04..E-06, G-07 | Approved successor contract and independently qualified consumer for any mandatory behavior; Runtime/Control Plane owner approval; production path stays inactive |
| R11 family migrations | 05 options; per-family rows | E-10, C-07, C-08, LD-08, F-01, F-04 | Each family separately operator-authorized, bounded and independently qualified |
| R12 distribution/auditability | 03 I4, 02 witness/anchor, 04 evidence | B-08, B-11, C-05 | R09-R11 selected profile |
| R14 GCR read-only crosswalk | 07 (candidates, matrix N-01..N-17, GCR-owner questions) | G-01..G-06, G-08, G-09 | An actual GCR baseline and the GCR owner's review; R14 is not R15 readiness |
| R15 GCR local consumer | none (excluded) | GCR-owner decisions in section 8 | Separate GCR owner and operator authorization |
| R16 cross-domain | 07 matrix as input only | G-05, G-07, F-02 | R10-R12 and R15 |
| R17 independent qualification | 06 (22-row matrix QM-01..QM-22, gap list, qualifier preconditions) | F-01..F-08, B-09, B-12, LD-07 | A designated independent qualifier; frozen candidate sources |

R13 (legacy retirement) and R18 (release) were not part of the assignment's mapping and remain downstream of qualified R11 migrations and R17 respectively.

## 7. Task independence (candidates only; this PR authorizes none of them)

**Could proceed without further rulings, each needing its own authorization:** (a) A-09 read-only confirmation (builder); (b) operator retrieval of COG-REG-SHARED-ADD-01 (G-09/D10); (c) owner adjudication of PR #13 and PR #17 (inventory work, not R08-PREP); (d) a read-only diff of PR #16 head `100aa407` against merged v1.2 to re-ground the ISS review (R-08); (e) a read-only survey identifying real hosts that construct `LocalExecutionPolicy` (input to C-01); (f) designation of an independent qualifier (F-01/D13, an operator act).

**Must stay blocked:** any successor-contract validator or schema code (A-01, A-02, E-03, E-09); any signing/verification library or key handling (B-01, B-02, B-10); any Runtime or Control Plane hook, claim/destination/receipt change (C-01, LD-01, LD-05, E-05); any mandatory-profile behavior (C-02, G-07); numeric/freshness/dedupe families and F6 (C-07, C-08, LD-08, D5); F1b migration (E-10, D11); any GCR consumer or shared field exchange (G-01, G-05); any activation, pin approval or selection.

## 8. Questions reserved exclusively to a GCR owner

Whether any GCR rule family is configuration-shaped and its payload/evaluator; selection and pin custody and trust root for GCR; cognitive admission semantics and what a selection epoch means for a GCR commit; source retention versus authorized erasure; memory, reliance, invalidation, canonical state and negative-record custody; acceptability of the namespace field as the only cross-system field; output-envelope policy; GCR interface-readiness disposition for R14 and independent authorization for R15 (07 section 7). OCS documents here do not answer them.

## 9. New rulings this preparation asks of the operator or OCS Architect (not in D1-D13)

Critical path to an approvable R08 contract: C-01 (who is the host integrator), E-01 and E-02 (profile and participation), A-01/A-02/E-03/E-09 (lifecycle, status, deny-all, successor-contract route), B-01..B-04 (authentication primitive, trust-root owner, role separation), C-03 and LD-01 (how a selection reaches the effect boundary), LD-02 (outcome mapping), LD-06 (integration baseline revision), F-01 (qualifier), G-09 (addendum text). Each is a named-owner decision in section 4 with its blocking phase.
