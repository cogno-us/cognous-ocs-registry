# Worker F notes (Runtime 0dde0ef7, Control Plane d66ae07f, SQ bb9b0890; Registry 317eb76a context only)

All collection-only. Collected-0 modules are NOT RUN (PyNaCl absent; SQ component dirs unset); see test_inventory.json for static AST counts.

## Contradictions and things that look wrong
1. G0 ledger G0-A-001/002, G0-B-009/010/012/013 ("none new" missing oracles, FULL coverage, "carries these unchanged") conflict with topics.json: all 12 topics PARTIAL, 4 HIGH gaps. G0-B-009 "unchanged" is wrong for f1ab (five-set payload).
2. Docstring vs code: the effect-time path is described as Registry-independent, but `_compare_pinned` (registry_selection_authority.py:847-882) imports Registry and gives HOLD `registry_unavailable_for_policy_digest` when absent.
3. SQ FA1-24 says the other three sets run in the Runtime F-01 suite. That suite builds destinations without the pin option, so under the pin institutions/domains are not isolated anywhere (only the integration test, all five at once, no cause assertion).
4. SQ "independent" F-01 requalification imports Runtime fixtures (same builder family); not independent evidence.
5. Runtime/CP tests pin Registry 943ab18 (Runtime c5e97e87), not G0 Registry 317eb76a. M1-20 style pin assertions would fail at the G0 pins. Diff 943ab18..317eb76 was not inspected (NOT READ).
6. Same code, different class by raise site (trust_snapshot_expired HOLD at effect time vs REFUSE at sync; trust_snapshot_version_stale). Executor collapses REFUSE/REFUSE_STALE/HOLD to authority_hold/current_authority_rejected; typed class only in evidence.
7. LocalExecutionPolicy accepts empty and unbounded sets, '*' and any non-empty str, unlike the Registry token rule (1..128, no '*', <=256). Mismatch -> HOLD policy_digest_unavailable, untested.
8. evaluate_with_registry_selection (the only caller-intersect-record code) is imported by no engine module; effect time is executor-subset-of-record, not intersection.
9. All governed fixtures: single-member sets, one scope inst-a/domain-a/tenant-a. Extra institution/domain members inert on the governed path (INFERRED); scope is never related to payload sets.
10. M1-16 grid: 648 cells, stride-7 sample = 93 cells, only 2 ALLOW (INFERRED by enumeration, not run). Equivalence is therefore thin; G0 S05 equivalence is three-set.
11. CP authorization_pin_export.py:197-201 scope check untested.
12. Pin payload has 17 members, no policy sets/digest, so the pin cannot detect widening.
13. reconcile_claim_exact ignores the selection store; no record-level revocation exists.
14. test_authorization_pin_integration hard-codes CP_WORKTREE.
15. SQ baseline suites run against SQ's frozen F5b reference, not the Runtime pin.
16. Route A has no commit-time containment (ADR 7.6, disclosed).

## NOT READ
Registry tests (Worker R/E); most of SQ (~28,961 files); Runtime engine files openshell*, dedupe, delayed_commit, refund_intent, producer_contract; installer.py (grep only); registry_selection_authority.py 172-700 and 960-1116 by signature only; CP policy_binding.py, runtime_authority.py; SQ harness internals.
