# F-A1 authorization pin: minimum cross-component implementation proposal (NOT authorized; no code)

Companion to [Amendment 4](../r08-v2-contract-amendment-4.md) (draft, revision 2). Baselines: Registry `a1169a05`, Control Plane `1bee3696`, Runtime `ac247daf`. Source references are to those commits. Every step is a separate PR in its own repository, reviewed by the Architect; none is started. Runtime implementation: NOT AUTHORIZED. RELEASE/PUBLICATION/PRODUCTION: HOLD. This revision aligns the proposal with the corrected Amendment 4 sections 6 and 7: **there is no unfenced terminal transition and no degraded mode.**

## Sequence (small, ordered)

| Step | Repo | Change | Existing source touched |
|---|---|---|---|
| 1 | `cognous-control-plane` | `export_authorization_pin(...)`: read-only, inside the handoff region after snapshot validation; returns the closed dict of Amendment 4 section 3.1 (Control Plane-sourced members). Re-checks `catalogue_digest` and `approval_commitment` against persisted decision state and `binding_digest(body)` against host config. | `src/agent_control_plane/local_authority_effect.py` (`_materialize_under_handoff` ~439-566, `_binding_issuance_reasons` 182-209, `_validate_issuance_snapshot` 251-401), `runtime_authority.py` (236-251, 470-478), `canonical_policy_binding.py` (95-100). No new decision logic; no change to issuance. |
| 2 | `cognous-execution-runtime` (new top-level `host/`, outside the `engine/` package) | Installer and pin library: append-only pin store, per-decision fence files, anchor writer with intent, installer log, mandatory start-up reconcile, bounded exclusive-fence retry. Runs only as the installer OS identity. | none in `engine/` |
| 3 | `cognous-execution-runtime` | Runtime guard: `PinReader` (read-only open, chain check, anchor decision table, per-decision shared fence, admission-barrier read); inserted around `execute_claim_atomic` (`engine/local_authority_effect.py:842-1020`): fence and barrier before `BEGIN IMMEDIATE` (:860), pin step after `_validate_claim_state` (:887) and before `_selection_guard` (:891), fence release in a `finally` after COMMIT/rollback (:994). `check_effect` receives the pin-derived scope (`engine/registry_selection_authority.py:1366-1376`). `provision_claim` (:272-452) seeds no authority for a pin-required destination. Receipt carries the pin epoch (:901-916). Reuse the typed refusal subclass (`atomic_local_control_plane_executor.py`). | `engine/local_authority_effect.py`, `engine/registry_selection_authority.py`, new `engine/authorization_pin.py` |
| 4 | `cognous-stack-qualification` | Real two-identity OS harness and the case battery. | tests only |
| 5 | independent | requalify V08 against patched components | not authorized here |

## Mechanism (minimum enforceable)

### Storage layout
- **Pin store** `pins.sqlite3`: `authorization_pin_v1(pin_epoch INTEGER PRIMARY KEY, decision_id, payload_json, status, prev_pin_digest, pin_digest)`, append-only, `journal_mode=DELETE`. Owner installer, files `0644`, directory chain `0755` with no executor-writable ancestor. Insert-only triggers are defense in depth only, never the boundary.
- **Fence directory** `fences/<sha256(decision_id)>.fence`: empty files, one per pin, created by the installer when it installs the pin; executor opens read-only.
- **Anchor** `pins.anchor.json` (`ocs-s4/pin-anchor/1`) with `committed_epoch`, `committed_head_digest`, optional `intent`, under the custodian, outside the pin store's restore domain. The existing `HostAnchorFile` (`registry_selection_authority.py:551-640`) is Runtime-writable and unkeyed, so only its flock + atomic replace + fsync pattern is reused; the pin anchor is written by the installer only.
- Effect database and selection store: unchanged.

### Durable pending intent
The installer writes the intent into the anchor by atomic replace with fsync of file and directory **before** it requests the exclusive fence. The intent is `{epoch = committed+1, decision_id, action, status, provenance_ref, intent_digest}`. It lives in the anchor (not in the pin store) so it is independent of the installer process being alive and of pin-store restores.

### New-effect admission barrier
Executor: (0) lock-free anchor read, HOLD if a `terminal` intent covers the `decision_id` (liveness only); (1) shared per-decision fence, non-blocking with deadline; (2) re-read the anchor **while holding the shared fence** and HOLD if covered; only then `BEGIN IMMEDIATE`. The fence is released in a `finally` after COMMIT or rollback.

### Lock ordering
Per-decision fence, then effect-database `BEGIN IMMEDIATE`. The executor holds one fence. The installer takes one exclusive fence at a time, never touches the effect database, and never waits for an executor while holding another lock. No cycle exists.

### Shared/exclusive acquisition and starvation
`flock` is not assumed fair. Starvation resistance comes from the barrier, not the lock: after the intent is durable, new entrants for the covered decision are held and release the fence at once; other decisions use other fence files. The installer therefore waits only for effects admitted before the intent. It retries `LOCK_NB` exclusive with backoff and a bounded deadline per attempt. **Bounded refusal, not an unfenced fallback:** on deadline it records `pending_blocked`, leaves the intent and barrier in place, and retries later; it never commits without the exclusive fence and never reports the transition effective.

### Terminal-row commit and external-anchor completion
Under the exclusive fence: verify (anchor committed == head, intent == recorded, chain intact, no terminal row yet), commit the terminal row (rollback-journal, fsync), append the installer log, then complete the anchor (committed = new head, intent cleared), mark complete, release the fence. The terminal row is effective at Runtime at its durable commit; the anchor completion is administrative and the Runtime accepts the state between them (store head equals the intent epoch).

### Crash recovery
Start-up reconcile is mandatory before the installer accepts any work. For each intent: re-validate the transition against persisted Control Plane authority; if `H = C` run exclusive acquisition and commit; if `H = intent.epoch` verify the row against the intent descriptor and complete the anchor. A pending terminal intent is never cleared without verified completion, never expires and has no abandon operation. Anchor loss or inconsistency needs an explicit logged operator re-baseline with chain continuity (ADR 3.6). Hot journals are recovered by the installer opening the store read-write.

### Installer progress or bounded refusal
Progress: completes when in-flight effects admitted before the intent finish. Bounded refusal: while blocked, the covered decision stays held (fail closed) and the installer emits `pending_blocked` evidence for the operator.

## Security guarantees (hold if the deployment assumptions hold)
1. A claim supplier cannot create, replace, delete or restore a pin (OS permissions), cannot set the pin, anchor or fence paths, and cannot change the operation used for Registry selection.
2. A terminal transition commits only under the exclusive per-decision fence, only after its intent is durable, and no effect commits using the previous active pin after that commit; no transition reaches its commit while an earlier shared-fence effect is in flight.
3. Pending, inconsistent, unavailable or conflicting authorization state holds or refuses governed effects; a pending transition is never reported effective.
4. F-01 five-set containment, claim commitment validation, evidence-write atomicity and the Registry selection guard are unchanged.

## Deployment assumptions (not guarantees; the operator must show them)
Distinct OS identities for installer, executor and Control Plane service; Control Plane stores, resolver and host config writable only by Control Plane/installer identities; pin directory chain and fence directory unwritable by the executor; paths fixed by host config; rollback-journal pin store opened `mode=ro`; every governed effect goes through the honest Runtime destination path (a supplier running arbitrary code in the executor process is excluded); same-host `flock` semantics (not NFS); **anchor custody outside the pin store's restore domain for any anti-rollback claim**, which code cannot prove.

## Migration and compatibility
`authorization_pin_required` is host configuration, default OFF, so existing destinations and V05/V06/V07 behavior are byte-identical. ON means every governed effect needs a pin and a claim without a binding is refused (no legacy fallback). No claim member, canonical binding member, log schema or generation rule changes; no new authorization decision authority; no new policy evaluator. Digest function: vendored copy with a shared-vector test rather than a runtime import through a supplier-reachable path (the Runtime today imports the Control Plane module at `registry_selection_authority.py:1363`).

## Facts established by earlier read-only experiment (worker-reported, throwaway users, not a qualification)
Cross-user `mode=ro` read of a rollback-journal database works and the executor cannot create/rename/unlink/chmod in the installer directory; a WAL database cannot be opened read-only across identities without sidecars; `flock` shared/exclusive works on read-only descriptors across identities and a crashed holder releases it; a killed installer's hot journal makes the read-only executor fail closed. The per-decision fence, the anchor intent barrier and the start-up reconcile are **designed but not experimentally verified**; qualification must verify them.

## Expected security tests
See [qualification-plan.md](qualification-plan.md).
