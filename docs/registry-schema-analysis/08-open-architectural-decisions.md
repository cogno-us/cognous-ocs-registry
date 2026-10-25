# 08 Open architectural decisions

Non-authorizing. Each item is a decision someone other than this analysis must make. Nothing proceeds on an assumed answer. Architect rulings are classification and design input only: they authorize no build, selection, activation or pin, each of which needs a separate operator decision (T3). The ISS Architect's role and the existence of the ISS questions below are not verified by any source available here.

## For the OCS Architect

| Id | Decision | Why it blocks | Options |
|---|---|---|---|
| D1 | Classify the 32 S02 unresolved rows (03 §4), starting with W8-091, W3-063, W9-027, W8-014, W6-042 and the 60-versus-300 relationship | Every F1c, F4, F5, F7 proposal depends on them | Per row: invariant, caller data, or registry-eligible |
| D2 | Authentication of records and selections (signing, key custody, or pin-only) | Digest is integrity only (T2); no activation is possible without this | Pin-only (current); signed records; signed selections |
| D3 | Where "active" lives: inside the record (S03) or in selection and activation only | A self-declared status lets a record state its own activity | Keep the frozen `s03-v1` gate (only `active` accepted) unchanged; move activity out for successor-format records only |
| D4 | Stricter direction for each scalar: F7 TTL, deadline, horizon; F4 ages, `clock_tolerance_seconds`, `anchor_deadline_to_inputs`; F5 class fields | Without it, composition is not definable (04 §4) | Per field, written ruling |
| D5 | F6 absent-agent semantics: unconstrained or deny | Two internally consistent but different policies | Unconstrained (overlay semantics); deny (key-wise intersection) |
| D6 | Classification of the `max_effects` and `max_amount` ceilings | F1c and the W8-091 row | Invariant; caller data; registry-eligible |
| D7 | Whether a mandatory-registry ACTIVATION profile is ever authorized | Optional refusal can leave a broader caller policy in force (T7) | Optional only; add mandatory profile |
| D8 | Treatment of `runtime-authority-reasons/0.1` and `/0.2`: one evolving commitment or two | Needed before any reason-vocabulary reference record | One; two |
| D9 | Whether F1d (target prefixes and match mode) may ever be registry data | New semantics and a security-weakening mode | Never; prefix-only with containment rule |
| D10 | Supply the text and source digest of `COG-REG-SHARED-ADD-01` (v1.2 records it as accepted in principle) | The envelope was built without it (05 §0) | Provide; revise envelope |
| D11 | Next increment: F1b (recommended by S06) or another | Sequencing (09) | F1b; F6; none |
| D12 | Whether the W9-027 divergence between `dedupe.py` and `merge.py` is intentional, observable only under unsupported input, a real behavioral divergence, or still unresolved | Affects the F7 resolution semantics. It is not characterized as a runtime defect without a supported execution path and exact-source evidence | The four dispositions listed |
| D13 | Independent qualification owner for Tier 1 families | S05 limits would carry over | Designate; defer |

## For the GCR Architect (ISS V6 is the current reference implementation)

No ISS architecture source was available to this analysis. The following are questions, not assumptions.

1. Does ISS have any rule family that is configuration-shaped today? If not, no ISS payload is needed and the envelope's namespace field is sufficient.
2. Are ISS cognitive policies governed by operators comparable to OCS allow-lists, ceilings and freshness bounds? This analysis assumes **no** equivalence.
3. Which component holds ISS selection and pin custody, and is it disjoint from OCS custody?
4. Is the envelope's `target_consumer` namespace acceptable as the only cross-system field?
5. Confirm there is no shared service, authority ledger or common family payload requirement.

Additional items: (a) whether a selection with no `valid_until` (perpetual) is acceptable; (b) whether `effective_conditions`-style windows may ever live in a record (this proposal says no).

## Constraints that stand regardless

Release, publication and production remain on HOLD. No pin is approved. No record is activated.

## Alignment with adopted plan v1.2 (differences recorded as required decisions)

PR #17 was authored against v1.1. A targeted pass against `docs/plans/PROJECT_PLAN-v1.2.md` and `PROJECT_PLAN-v1.2-REVIEW-CROSSWALK.md` found no conclusion that contradicts v1.2. It found these points where this analysis predates or is silent on v1.2; each is a decision, not a change this analysis makes:

| Id | Difference | Decision needed |
|---|---|---|
| V1 | v1.2 §3.1 selections carry identity, **epoch**, tenant/scope, effective interval, withdrawal/revocation reference and exact evaluator pins; 05 §3 has identity, entries, runtime source, `valid_from/until` | Add epoch, tenant/scope and revocation reference to the selection (R08/R09) |
| V2 | v1.2 §3.3 requires atomic effective-policy binding and commit-boundary revalidation (A5); this analysis has no such protocol | Define binding fields and revalidation (R09/R10) |
| V3 | v1.2 §3.1 record lifecycle is draft, validation, approval, publication, supersession, archival; 05 §2 keeps only author intent (`proposed`, `withdrawn`) plus legacy statuses | Decide the record lifecycle vocabulary (relates to D3) |
| V4 | v1.2 §3.2 requires explicit deny-all semantics in a new version; 07 O3 only notes that deny-all cannot be authored today | Define deny-all in the successor contract (R08) |
| V5 | v1.2 sets optional versus required participation **per operation**; 05 §4 sets it per consumer profile | Decide granularity (R10) |
| V6 | v1.2 §3.4 requires an operator-approved Minimum Supported Operational Profile; this analysis has none and does not treat F1b as one | Operator adopts an MSOP after R07/R08 |
| V7 | v1.2 §3.3 non-forgetting and source preservation (A6) are GCR-owned; not discussed here | Record as out of scope for OCS registry records |
| V8 | v1.2 R11 default family order differs from this analysis' earlier order (09 now follows v1.2) | None beyond per-family authorization |
| V9 | Terminology: GCR is the architectural role (A1); this analysis said "ISS" | Terminology corrected in 05 and 08; no semantic change |

Confirmed consistent with v1.2: record, selection and activation are separate (05 §1); registry data creates no grant or authority; GCR and OCS keep separate evaluators and canonical authorities; shared policy identity transfers no qualification (05 §5, 07 T2); typed, family-specific composition and fail-closed unsupported composition (04 §3, 06 §3); the historical catalogue is not a migration inventory (01); R11 family migrations need separate authorization (09); GCR compatibility does not block OCS-only development (09). The 32 unresolved S02 classifications are preserved (03 §4).

## Architect rulings received (R07 disposition, 2026-10-24) and what remains open

Rulings are design guidance within the adopted v1.2 program. They authorize no implementation, selection, activation or pin. Source of the rulings: the OCS Architect's R07 handoff instruction to this builder; it is not yet a recorded decision file in this repository.

| Id | Ruling | Effect on this analysis |
|---|---|---|
| D2 | Operational selection requires authenticated authority; pin-only integrity is insufficient as a general authorization mechanism. Trust root, signing and custody are R09 design and operator approval | 05 states this; the pin-only profile of S04 remains a bounded, non-operational baseline |
| D3 | For successor contracts, record publication status confers no authority; selection and domain-owned activation decide whether policy may govern an operation. Frozen S03-v1 behavior, including its status validation, is preserved | Consistent with 05 §2 and 06 §4 |
| D4 | No universal monotonic direction; each scalar needs units, ordering, floor/ceiling, tightening direction, interaction with code invariants and a deterministic unsupported-case outcome | 04 §3 now says so; F7 and F4 composition stay conditional |
| D5 | **Unresolved.** Neither unconstrained nor deny is chosen; needs a source-backed baseline and operational-profile semantics before implementation | F6 absent-agent stays undecided in 06 §5.2 |
| D7 | A mandatory-participation profile is permitted as a design capability, not authorized for activation; required policy failure must not fall back to a broader caller policy | 05 §4 and 07 O2 updated |
| D8 | Keep runtime-authority-reasons 0.1 and 0.2 as distinct versioned artifacts pending lineage adjudication; do not infer a separate V0.2 rule catalogue | Consistent with 01 §1 |
| D9 | F1d stays deferred until containment and matching-mode semantics are shown non-widening | Consistent with 04 §4.1 |
| D10 | `COG-REG-SHARED-ADD-01` was given to the Architect. Durable repository custody and an exact verified digest are still required before normative reliance | The ID is referenced in six files of this repository at `main` (the v1.2 plan and crosswalk, the S06 authorization and consolidation report, the post-S06 direction and the sprint status), but none of them carries the addendum text; no file with its content or digest was found. Other repositories (ISS Core, Constitution, OCS) were not reachable in this session. This analysis relies on none of its content. Constitution `ADOPTION.md` was not read, so no claim about formal constitutional adoption is made |
| D11 | F1b (`allowed_institutions`, `allowed_authority_domains`) is the preferred first family extension; an architectural priority, not permission to implement or activate | 09 order starts with F1b |
| D13 | An independent Tier 1 qualification owner is mandatory before activation; not yet designated | Remains a dependency |

**Still open** (do not assume answers): D1 (the 32 S02 classifications, priority W8-091, W3-063, W9-027, W8-014, W6-042 and the 60-versus-300 distinction, which stays two quantities unless evidence shows a shared requirement); D6 (`max_effects` and `max_amount`: invariant, caller configuration, governed registry parameter, or layered); D12; the authentication trust root; approval and selection custody; mandatory versus optional participation per operation; deny-all encoding; the Minimum Supported Operational Profile; the qualification owner's designation; per-family migration authorization; and V1 to V6 above.

**Mapping to v1.2 phases:** D1, D6, D8, D12 and the S02 rows belong to R07; the successor contract, deny-all, envelope, V1 to V6 and D4, D5, D9 to R08; D2, D3, selection custody and revocation to R09; D7, participation per operation and V2 to R10; per-family authorization, D11 and F1b to R11; D13 to R11 and R17; the addendum's custody (D10) to R08; the GCR questions to R14 to R16.
