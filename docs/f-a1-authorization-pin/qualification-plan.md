# F-A1 authorization pin: qualification plan (DESIGNED, NOT EXECUTED)

Maximum proposed local budget: **30 targeted case executions** (parametrized cases and reruns counted individually). GitHub CI is mandatory for the exact PR heads. Acceptance criteria below are declared before any implementation exists and do not depend on how it is written. Writer-separation cases need **real OS identities** (two distinct non-root users, real ownership and modes, `mode=ro`); an in-process mock result for those cases is recorded INCONCLUSIVE, never PASS. Verdict vocabulary: HELD / BREACH / CHARACTERIZED / INCONCLUSIVE / BLOCKED. A case that cannot run for lack of an OS facility is INCONCLUSIVE, not PASS.

| ID | Category | Setup | Acceptance criterion |
|---|---|---|---|
| FA1-01 | Original F-A1 operation substitution | historical V08 `test_au7` scenario: binding rewritten to `op-other`, commitment recomputed | REFUSE `policy_identity_mismatch` / `pin_binding_mismatch:operation`; 0 effects, 0 receipts |
| FA1-02 | Legitimate workflow-issued claim | real Control Plane decision, installer-installed pin, honest claim | executes: 1 effect, receipt carries `pin_epoch` |
| FA1-03 | Cross-operation selection | two activated operations; claim for A, pin for A, binding says B | REFUSE; the Registry row for B is never consulted (evidence shows pin-derived scope) |
| FA1-04 | Recomputed commitment attack | supplier recomputes `claim_commitment` and `operation_commitment` after any rewrite | REFUSE; no commitment recomputation changes the outcome |
| FA1-05 | Supplier pin installation attempt (real OS) | executor identity tries to open the pin store rw, create a row, create `-journal` | permission denied (EACCES / readonly error); store bytes unchanged |
| FA1-06 | Unauthorized pin modification (real OS) | executor identity tries UPDATE/DELETE/rename/unlink/chmod/replace of pin file and fence, and to redirect the path via constructor/executor arguments | denied; path arguments rejected as host-only |
| FA1-07 | Missing pin | verified store, no row for the decision | REFUSE `pin_absent` (no fallback), 0 effects |
| FA1-08 | Stale revision | claim `grant_revision` older than pin | REFUSE `pin_lineage_mismatch:grant_revision` |
| FA1-09 | Supersession | old decision pin appended `superseded` | REFUSE `pin_status:superseded` |
| FA1-10 | Revocation before authority check | `revoked` committed before the effect's pin read | REFUSE; 0 effects |
| FA1-11 | Revocation concurrent with effect commit (fenced) | race harness, 1 revocation vs N effects, fence acquired | no effect commits with `pin_epoch` below the revocation epoch after the row commit; every effect receipt epoch is consistent with the pin-commit order |
| FA1-12 | Revocation propagation delay | CPAA marks revoked; installer not yet run | effect still passes under the old pin (CHARACTERIZED, expected, documented); passes no later than the next pin read after installation |
| FA1-13 | Degraded fence | hold the shared fence from a stalled process | installer reports `fence_mode=degraded`; later reads refuse; in-flight effect (if any) carries the older epoch; never falsely ordered after |
| FA1-14 | Stale authorization replay | replay an older `active` row after a terminal row (installer refuses; direct file injection is excluded) and a claim for a terminal decision | installer refuses; Runtime REFUSE; injected conflict HOLD `pin_conflict` |
| FA1-15 | Database rollback | restore pin store to an earlier point with the anchor intact | HOLD (`H < C` or `I > H`) |
| FA1-16 | External-anchor mismatch | anchor ahead of / inconsistent with store | HOLD `pin_anchor_inconsistent` |
| FA1-17 | Anchor unavailable | delete / make unreadable the anchor | HOLD `pin_anchor_unavailable` |
| FA1-18 | Crash between pin commit and anchor update | kill installer after step 3 of the update order | next effect accepted (`I = H = C+1`); installer reconcile finalizes |
| FA1-19 | Crash before pin commit | kill installer after anchor intent | HOLD until reconcile |
| FA1-20 | Hot journal | kill installer mid-transaction | executor HOLD (`pin_store_unreadable`); installer recovery restores service |
| FA1-21 | Consistent restore of store and anchor | restore both | UNDETECTED: recorded CHARACTERIZED as the disclosed residual limit, not PASS |
| FA1-22 | F-01 widening regression | original F-01 policy-widening exploit | REFUSE `policy_not_subset:*` (Amendment 3 unchanged) |
| FA1-23 | Five-set containment intact | each of the five sets widened | all REFUSE |
| FA1-24 | Valid narrower policy | narrower executor policy, valid pin | executes |
| FA1-25 | Transaction-critical evidence failure | fail the receipt/evidence insert | 0 committed effects |
| FA1-26 | Legacy required-scope refusal | claim without a binding on a pin-required destination | REFUSE `pin_required_binding_absent`; no legacy fallback |
| FA1-27 | Non-required destination unchanged | default OFF | V05/V06/V07 observable behavior unchanged on the targeted subset |
| FA1-28 | First-writer rows | supplier pre-seeds a grant/approval row inconsistent with the pin | REFUSE (rows confer no authority beyond agreement with the pin) |
| FA1-29 | Installer precondition | export with a withdrawn/expired/unknown grant, or mismatched `catalogue_digest` | no pin installed; installer log records the refusal |
| FA1-30 | Idempotent and conflicting install | same payload twice; different payload for same decision | first is a no-op; second refused and logged |

Do not rerun the full V05/V06/V07/V08 batteries locally; they run in GitHub CI. Historical V08 F-A1 breach evidence in PR #235 is never edited or allow-listed; V08 requalification is a separate authorization.
