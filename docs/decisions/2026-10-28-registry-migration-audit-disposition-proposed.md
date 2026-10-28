# Registry family migration — Architect audit disposition and restart gates (2026-10-28)

**Status: proposed decision record; not a merged ratification.** Evidence is draft audit [PR #60](https://github.com/cogno-us/cognous-ocs-registry/pull/60), head `0f11e5e97b114e79bae0fb29734feae991c278d0`. Applies alongside the [proposed Plan v1.1](../plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md). No production code or frozen S02/G0 evidence changed.

## Reconciled findings

| Unit | Audited total | Meaning |
|---|---:|---|
| S02 site rows | 620 | Historical sites, not unique policies |
| G0 rule groups | 97 | Earlier provisional deduplication |
| Canonical rules | 444 | Audit logical grouping, includes immutable mechanisms |
| Rules with configurable parameters | 52 | Configuration by any legitimate owner |
| Candidate configurable parameters | 80 | All ownership categories; 77 excluding 3 retained-in-code literals |
| Registry-manageable parameters | 19 | 14 core + 5 qualified/coupled, in 12 rules |
| Registry represented | 12 | Authenticated schema exists, regardless of consumer |
| Enforcement integrated | 9 | Five allow-set parameters + M2 (2) + M3 (2) |
| Independently accepted | 0 | No Tier 1 independent acceptance shown |
| Eligible but not integrated | 10 | Three already represented without Control Plane consumer |
| Additional blocked/unresolved | 3 / 1 | Outside the 19-parameter numerator |

These counts are **provisional until PR #60 and Plan v1.1 are adopted**. The audit is medium confidence, bounded source review, not an exhaustive proof that no additional candidate exists. Audit PR #60 reports 5,453 Registry tests passed, 1,694 skipped; exact-head Registry workflow passed. It did not independently qualify migrations.

## Material findings

1. The G0 `28 of 97` groups cannot be compared directly to `19 parameters in 12 rules`. Use the machine-readable parameter catalogue as the denominator, rather than historical literal sites or composite-family repeats.
2. F4 status and approval ages, and F5 class ages, are **represented but not integrated** on merged main. These are legitimate consumer-integration tasks, not new Registry schema work.
3. M2/M3 are merged and effect-integrated, pending independent acceptance. Historical AD-07 remains marked OPEN; later Architect implementation approvals should be recorded as an additive dated disposition, not a rewrite of frozen history.
4. M11 PR #58, CP #87 and tracking #59 remain unmerged. The new constructor clock-tolerance slot needs explicit Architect scope/range authorization; ObservationPolicy tolerance is distinct. CP #87 has family-atomicity and constructor-only revocation limitations and lacks pin-dependent CI coverage.
5. The newly detected qualified candidate is terminal-revocation enablement, requiring approval-commitment semantics. Other qualified/coupled fields remain contingent on consumer and identity design.
6. Coverage limitations remain in Stack Qualification, Orchestrator, Governed Exchange, hub and selected producer surfaces. Do not advertise this denominator as exhaustive.

## Pending decisions and hold

- Audit PR #60 adoption, then Plan v1.1 adoption.
- F4 ages-only consumer restart authorization, scope atomicity and revocation lifecycle.
- Constructor tolerance AR-1/AR-2 separately; do not auto-merge Registry #58.
- F5 approval-commitment coupling before its Control Plane consumer.
- Dated AD-07 closure addendum preserving historical row.
- Independent Tier 1 acceptance remains pending. Release, publication and production remain HOLD.

**Recommended sequencing:** approve corrected audit; adopt Plan v1.1; authorize bounded F4 ages-only integration (not constructor tolerance), then return to eligible parameters per the audited ledger. No autonomous engineering restart is granted by this record.
