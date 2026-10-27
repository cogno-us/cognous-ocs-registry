# F-A1 authorization pin: minimum cross-component implementation proposal (NOT authorized; no code)

Companion to [Amendment 4](../r08-v2-contract-amendment-4.md) (draft). Baselines: Registry `a1169a05`, Control Plane `1bee3696`, Runtime `ac247daf`. Source references are to those commits. Every step is a separate PR in its own repository, reviewed by the Architect; none is started. RELEASE/PUBLICATION/PRODUCTION: HOLD.

## Sequence (small, ordered)

| Step | Repo | Change | Existing source touched |
|---|---|---|---|
| 1 | `cognous-control-plane` | `export_authorization_pin(...)`: read-only, called inside the handoff region after snapshot validation; returns the closed dict of Amendment 4 section 3.1 (CPAA-sourced members). Re-checks `catalogue_digest` and `approval_commitment` equality against persisted decision state and `binding_digest(body)` against host config. | `src/agent_control_plane/local_authority_effect.py` (`_materialize_under_handoff` ~439-566, `_binding_issuance_reasons` 182-209, `_validate_issuance_snapshot` 251-401), `runtime_authority.py` (236-251, 470-478), `canonical_policy_binding.py` (95-100). No new decision logic; no change to issuance. |
| 2 | `cognous-execution-runtime` (new, outside `engine/` package) | Host installer + pin library: append-only pin store (`rollback-journal`), fence, anchor writer, installer log, reconcile pass. Runs only as the installer OS identity. Lives under a new top-level `host/` directory so the executor package cannot import a writer. | none in `engine/` |
| 3 | `cognous-execution-runtime` | Runtime guard: `PinReader` (read-only open, chain check, anchor decision table, fence shared lock); call inserted in `execute_claim_atomic` after `_validate_claim_state` (`engine/local_authority_effect.py:887`) and before `_selection_guard` (:891); `check_effect` receives the pin-derived scope (`engine/registry_selection_authority.py:1366-1376` currently builds scope from `binding`); `provision_claim` (:272-452) must not seed authority for a pin-required destination and must refuse conflicting rows; receipt carries pin epoch (receipt dict :901-916); typed refusal subclass reused (`atomic_local_control_plane_executor.py`). | `engine/local_authority_effect.py`, `engine/registry_selection_authority.py`, new `engine/authorization_pin.py` |
| 4 | `cognous-stack-qualification` | OS-isolation test harness (two non-root identities) and the case battery. | tests only |
| 5 | independent | requalify V08 against patched components | not authorized here |

## Storage layout

- **Pin store** `pins.sqlite3`: one table `authorization_pin_v1(pin_epoch INTEGER PRIMARY KEY, decision_id, payload_json, status, prev_pin_digest, pin_digest)`, append-only (insert-only triggers are defense in depth only; they are file-resident and are NOT the boundary). `journal_mode=DELETE`. Owner installer, mode 0644, directory 0755, no executor-writable ancestor.
- **Fence** `pins.fence`: empty file, owner installer, 0644.
- **Anchor** `pins.anchor.json` (`ocs-s4/pin-anchor/1`): separate directory/volume under its custodian, outside the pin store's restore domain. Replaces nothing in the existing `HostAnchorFile`; that class (`registry_selection_authority.py:551-640`) is writable by the Runtime process today and unkeyed, so only its flock + atomic-replace + fsync pattern is reused.
- Effect database and selection store: unchanged.

## Host writer and reader responsibilities

- Installer (writer): runs the Control Plane export, verifies preconditions, appends rows, runs the anchor protocol, takes the exclusive fence for terminal transitions, writes the installer log, reconciles after crashes. Never opens the effect database.
- Executor (reader): opens read-only, verifies anchor and chain, reads one row by `decision_id`, compares. Never writes, creates files in, or chmods the pin directory.

## How the requirements are met

- Existing `BEGIN IMMEDIATE` preserved: the pin step runs inside it; the fence is taken before it (lock order fence then effect DB).
- Consistency of pin and effect state: by the fence protocol of Amendment 4 section 6 and epoch-stamped receipts, not by SQLite. Separate databases alone do not create an atomic cross-store boundary; degraded fence mode leaves a bounded in-flight window, disclosed.
- Stale authorization rejected: terminal statuses are irreversible; `grant_revision` and `pin_epoch` checks; anchor regression HOLDs.
- Independent operation source verified: pin derived from persisted CPAA decision state (catalogue/approval commitment equality, host-config digest) by an installer the supplier cannot invoke; Runtime compares the claim binding to it and builds the scope key from the pin.
- F-A1 prevented: rewriting `operation` changes `binding_digest`; the pin's digest is not supplier-writable; recomputing the claim commitment is irrelevant to the pin comparison; the scope key no longer comes from the claim.

## Migration and compatibility

`authorization_pin_required` is host configuration, default OFF so existing destinations and all V05/V06/V07 behavior are byte-identical. ON means every governed effect needs a pin and a claim without a binding is refused. No claim member, canonical binding member, log schema or generation rule changes. `provision_claim` behavior for non-required destinations is unchanged. Digest function: the guard must use a digest implementation pinned by the shared vectors; today the Runtime imports the Control Plane module (`registry_selection_authority.py:1363`) and calls only `binding_defect`, so a vendored copy with a vector test is proposed rather than a runtime import through a supplier-reachable path (inference: import path control is a deployment matter).

## Deployment assumptions (must be true; see Amendment 4 P-1..P-5)

Distinct OS identities for installer, executor and CPAA service; CPAA stores, resolver and host-config writable only by CPAA/installer; pin directory chain unwritable by executor; pin/anchor/fence paths fixed by host config; rollback-journal pin store opened `mode=ro`; external anchor custody for any anti-rollback claim.

## Facts established by read-only experiment (throwaway users, 2026-10-27, worker-reported)

Cross-user `mode=ro` read of a `journal_mode=DELETE` database works; the executor identity cannot create, rename, unlink or chmod in the installer's directory; a WAL database cannot be opened read-only across identities when sidecars are absent; `flock` shared/exclusive works on a read-only descriptor across identities and a killed holder releases it; a hot journal left by a killed installer makes the read-only executor fail (fail-closed availability loss); a supplier holding the exclusive lock blocks installer and executors (availability, not integrity). These were small experiments, not a qualification.

## Expected security tests

See [qualification-plan.md](qualification-plan.md).
