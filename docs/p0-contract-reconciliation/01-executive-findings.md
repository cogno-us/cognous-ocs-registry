# 1. Executive findings

## Bottom line

V0.2 left a usable foundation of **adopted decisions and principles** and a set of **implemented, builder-tested** components, but **no frozen registry wire profile and no independent qualification of any registry contract**. The registry program (S03–S05, R08-S01) and V0.2 share one doctrine and can be joined by adapters. There is **one genuine conflict** (who issues the epoch and owns the activation decision), and it is bounded and resolvable by an Architect ADR without operator escalation. **P1 can proceed now without another broad contract review.**

## Counts (139 canonical contracts; ledger `02-contract-ledger.jsonl`)

| Current status | Count |
|---|---|
| `ADOPTED_FROZEN` | 35 |
| `IMPLEMENTED_NOT_QUALIFIED` | 44 |
| `PROPOSED_ONLY` | 44 |
| `UNVERIFIED` | 11 |
| `SUPERSEDED` | 3 |
| `CONFLICTING` | 2 (one genuine conflict, one stale status label) |

| Disposition | Count |
|---|---|
| `REUSE_UNCHANGED` | 69 |
| `REUSE_WITH_ADAPTER` | 30 |
| `DEFER` | 36 |
| `SUPERSEDED_BY_ADOPTED_CONTRACT` | 3 |
| `TARGETED_RECONCILIATION` | 1 |

Of the 99 contracts with a reuse disposition, 70 are adopted or implemented (33 `ADOPTED_FROZEN`, 37 `IMPLEMENTED_NOT_QUALIFIED`). The other 29 are proposals, unverified items or one stale label, usable only as design input. No contract is `ADOPTED_FROZEN` and independently qualified.

## What is already settled (reuse; do not reopen)

- **The partition doctrine.** OCS-DGR-ARCH/1.0.0: governance rules are versioned data; constitutional invariants stay enforced code; evaluators are registered code with no expression language (hub `docs/declarative-governance-registry.md`, recorded as an adopted direction in `operator-decisions.md`). Registry plan v1.3 §3 restates it. No contradictory partition exists in either program.
- **Control Plane and Runtime remain the only effect-authorization points.** A registry cannot issue grants, substitute for the Control Plane or authorize effects (plan v1.3 §1, §3.1; hub operator decisions). A selection is not a grant.
- **M0 decisions** (operator, 2026-10-22): ADR-P01 (JCS canonical JSON for new commitments, legacy form kept as a named profile), P02, P03 (hub-owned immutable digest-pinned artifact; a separate registry repository "can follow if requirements justify it"), P04, P05, P07, P08, P09, SP-01 (stable effect identity), the 12-state workflow vocabulary and the AOI decisions (rows 13–20).
- **Registry-side decisions** in this repository: S03/S04 frozen sources, S05 conditions, F1a adopted as the *target* Minimum Supported Operational Profile (a scope decision, not operational acceptance), record / selection / activation as distinct objects, activation consumer-owned, and the standing no-activation, no-key-ceremony, no-verifier holds.
- **W0 contracts C1–C8** and the lock-selected component interfaces are available as the frozen historical baseline (tuple g8-r10). They are historical reference, not current release or qualification status.

## Implemented but not qualified (reusable as code, never as qualified)

Hub `ocs-registry-record/0`, `ocs-mandatory-manifest/0` and `check_completeness` (steps 2.1, 2.3); registry S03 validator, S04 overlay consumer, S05 differential harness; R08-S01 `r08-v1` successor foundation (record, selection envelope, layered verification, F1a composition, decision entrypoint) with a test-double verifier; Route B atomic authority/effect profile. Evidence is builder tests plus Copilot code review. Always cite as "Copilot-reviewed, not independently qualified".

## Proposed only (do not rely on as contract)

Contracts 1.2, 1.3 and 1.4 *as documents* (their header: "PROPOSED until the M0 gate records an outcome"; M0 adopted underlying ADRs, not the text); `ocs-registry-record/1` and `ocs-mandatory-manifest/1` candidates; step 2.4 activation, epoch, freshness and rollback; F3 packages FP-01..FP-05; the scanner ruleset profile; AOI-C01/C02 text; the Q1–Q17 Architect rulings (self-described "binding for this programme" but with no operator transcription or decision record: UNVERIFIED as adoption; usable as Architect-role technical guidance, not as frozen contract).

## Genuinely open

**One genuine conflict (TR-01):** V0.2 proposals give the Control Plane the registry epoch and the activation decision (contract 1.3 §3/§5; Q14 default 5). Adopted plan v1.3 §3 item 3 and R08 make activation consumer-owned, with the selection authority issuing the epoch. For Runtime-enforced families the two cannot both hold. Recommended resolution: one Architect ADR assigning, per family, the enforcing component's own gate as activator and high-water holder, the selection authority as epoch issuer, and the registry as neither. Control Plane authority is preserved; none moves to the registry. See `06-targeted-conflict-register.md`.

**Missing contracts (bounded; none requires redesign):** selection validity and applicability at the commit boundary (R10); selection-withdrawal propagation to the destination; a durable carrier for registry refusal evidence; rule-set/selection identity in decision context (FP-04); evaluator `qualification_ref` for `LocalExecutionPolicy.check`; per-field composition rulings and numeric payload encoding beyond F1a; a Control Plane adapter for F4/F5; an authenticated trust root and verifier (R09).

**Unresolved authority boundaries:** named host integrator for Runtime policy construction (C-01); R09 trust-root custody, key ceremony and witness holder (operator-authorized); production registry location and pin carrier (ADR-P03 follow-on); independent Tier 1 qualification lead (F-01, not designated); hub lock pin `ec728da6` versus provisional `c5e97e87` for terminal approval revocation (an ordinary pin reconciliation, R10-F-03).

## Evidence hazards to carry forward

1. `component-lock.json` `qualification_status: "accepted"` and `evidence-snapshot.json` `"current"` describe an earlier tuple that `docs/release-status.md` calls superseded. Do not cite them as qualification of the current lock.
2. "Frozen" in registry documents means byte-pinned blobs plus Architect direction; it never means qualified.
3. A heading "Frozen qualification entry" in hub `s03/minimum-profile-and-coverage.md` sits over rows that all read "Open".
4. "registry" means three things: the governance registry (OCS-DGR), the `cognous-ocs-registry` repository, and The Index (`cognous-evidence-registry`). Ledger rows use full names.
5. Stale status text: `docs/sprint-status.md` ("R08-S01 DRAFT PR"), hub `historical-status-snapshot.md` ("no execution has started").

## Operator decisions generated by P0

**None.** Every item above is a technical reconciliation owned by the Architect and component owners under plan v1.3 §8. The operator-gated items that already existed (trust-root ceremony, production host owner, Tier 1 lead designation, activation, release) are unchanged and are not new questions. TR-01 escalates only if its ADR would move authority away from the Control Plane's existing gate, which the recommended resolution does not do.

## Architect confirmation requested (P0 exit gate)

Confirm (a) the ledger statuses, in particular the ruling that Q1–Q17 is UNVERIFIED as adoption and ADR-P03 is not in conflict with this repository; (b) the TR-01 resolution; (c) that P1 may rely on the contracts listed in `07-p1-handoff.md`.
