# F-A1 authorization pin: qualification plan (DESIGNED, NOT EXECUTED; revision 2)

Maximum proposed local budget: **30 targeted case executions**. Counting rule: one execution is one test invocation; a parametrized case counts once per parameter; the `Exec` column sums to 30. GitHub CI is mandatory for the exact PR heads and carries what is not run locally. Acceptance criteria are declared before any implementation exists. Writer-separation cases need **real OS identities** (two distinct non-root users, real ownership and modes, `mode=ro`); an in-process mock result for those cases is INCONCLUSIVE, never PASS. Verdicts: HELD / BREACH / CHARACTERIZED / INCONCLUSIVE / BLOCKED. A case that cannot run for lack of an OS facility is INCONCLUSIVE.

| ID | Exec | Category | Setup | Acceptance criterion |
|---|---|---|---|---|
| FA1-01 | 1 | Original F-A1 substitution | historical V08 `test_au7` scenario: binding rewritten to `op-other`, commitment recomputed | REFUSE `policy_identity_mismatch` / `pin_binding_mismatch:operation`; 0 effects, 0 receipts |
| FA1-02 | 1 | Legitimate workflow-issued claim | real Control Plane decision, installer-installed pin | executes: 1 effect; receipt carries `pin_epoch` |
| FA1-03 | 1 | Cross-operation selection | two activated operations; pin for A, binding says B | REFUSE; the Registry row for B is never consulted |
| FA1-04 | 1 | Recomputed commitment | supplier recomputes `claim_commitment` and `operation_commitment` after the rewrite | REFUSE; commitment recomputation never changes the outcome |
| FA1-05 | 1 | Supplier pin installation (real OS) | executor identity tries to open the pin store read-write, insert a row, create a journal | permission denied; store bytes unchanged |
| FA1-06 | 2 | Unauthorized pin modification (real OS) | (a) executor identity tries UPDATE/DELETE/rename/unlink/chmod of the pin file, fence or anchor; (b) tries to redirect pin, fence or anchor paths through constructor/executor arguments | (a) denied, bytes unchanged; (b) arguments rejected as host-only |
| FA1-07 | 1 | Missing pin | verified store, no row for the decision | REFUSE `pin_absent`, 0 effects, no fallback |
| FA1-08 | 1 | Stale revision | claim `grant_revision` differs from the pin | REFUSE `pin_lineage_mismatch:grant_revision` |
| FA1-09 | 1 | Supersession | old decision's pin committed `superseded` through the full fenced protocol | REFUSE `pin_status:superseded` |
| FA1-10 | 1 | Revocation before authority check | terminal row fully committed before the effect starts | REFUSE; 0 effects |
| FA1-11 | 1 | Concurrent revocation and effects | harness: N effects in flight holding the shared fence while one revocation starts | the revocation does not complete while any earlier shared-fence effect is in flight; once the terminal row commits no later effect commits with the previous pin; every receipt `pin_epoch` is consistent with the serialized order; the revocation is reported pending until its row commits |
| FA1-12 | 1 | Revocation propagation delay | Control Plane marks revoked; installer not yet started | effect still passes under the old pin (CHARACTERIZED, documented limit); refused from the first read after the installer's intent |
| FA1-13 | 1 | Fence unavailable | an executor holds the shared fence and does not release it | terminal transition stays pending; no terminal row, no committed-epoch advance, no unfenced commit; new governed effects for that decision are held (`pin_transition_pending`); no report of completion; after the holder exits, recovery completes the transition through the exclusive fence |
| FA1-14 | 1 | Starvation / admission barrier | continuous stream of new claims for the covered decision plus unrelated decisions while a revocation is pending | covered-decision claims are held, unrelated decisions are admitted and do not block the installer, and the revocation completes once the pre-intent in-flight effects finish (no reliance on `flock` fairness) |
| FA1-15 | 1 | Stale authorization replay | claim for a terminal decision; installer attempt to re-activate a terminal decision | Runtime REFUSE; installer refuses and logs |
| FA1-16 | 1 | Database rollback | restore the pin store to an earlier point with the anchor intact | HOLD (`pin_anchor_inconsistent`); the earlier active pin is not honoured |
| FA1-17 | 1 | External-anchor mismatch | anchor ahead of or inconsistent with the store, or intent in an invalid relation | HOLD all decisions (`pin_anchor_inconsistent`) |
| FA1-18 | 1 | Anchor unavailable | delete or make unreadable the anchor | HOLD all decisions (`pin_anchor_unavailable`); installer refuses to write |
| FA1-19 | 1 | Crash A: before the intent is durable | kill the installer before the anchor replace | no barrier, no pending, no state change; restart re-derives the transition from the Control Plane |
| FA1-20 | 1 | Crash B/D/F/H: intent durable, row not committed, installer down then restarted | kill after the intent; run effects; restart installer | covered decision HELD for the whole interval with the installer down; unrelated decisions admitted; on restart the mandatory reconcile completes the transition through the exclusive fence; the intent was never cleared by anything else |
| FA1-21 | 1 | Crash C: while holding the exclusive fence (with hot journal) | kill the installer mid-transaction | OS releases the lock; executor HOLD (`pin_store_unreadable`) while the journal is hot; installer recovery rolls back or completes; no fabricated commit |
| FA1-22 | 1 | Crash E: after the row commit, before the anchor completion | kill between steps 6 and 7 | Runtime accepts and refuses the decision by the terminal row; reconcile verifies the row against the intent and completes the anchor; a mismatching row yields HOLD all |
| FA1-23 | 1 | F-01 original policy-widening | original F-01 exploit | REFUSE `policy_not_subset:allowed_actions` (Amendment 3 unchanged) |
| FA1-24 | 1 | Five-set containment intact | one representative additional set | REFUSE; the remaining sets run in the Runtime's existing F-01 CI suite |
| FA1-25 | 1 | Valid narrower policy | narrower executor policy, valid pin | executes |
| FA1-26 | 1 | Transaction-critical evidence failure | fail the receipt/evidence insert | 0 committed effects; the shared fence is released |
| FA1-27 | 1 | Legacy required-scope refusal | claim without a binding on a pin-required destination | REFUSE `pin_required_binding_absent`; no legacy fallback |
| FA1-28 | 1 | First-writer rows | supplier pre-seeds an approval/grant row inconsistent with the pin | REFUSE; rows confer no authority beyond agreement with the pin |
| FA1-29 | 1 | Installer precondition | export for a withdrawn, expired or unknown grant, or a mismatched `catalogue_digest` | no pin installed; refusal logged |

Total executions: 30. Not run locally (carried by CI or by documented limits): the other four F-01 sets; idempotent and conflicting install unit tests; non-required destination regression (V05/V06/V07 CI); consistent restore of both store and anchor, which is the documented UNDETECTED limit and is recorded as CHARACTERIZED by analysis, not as a pass.

Do not rerun the full V05/V06/V07/V08 batteries locally. Historical V08 F-A1 breach evidence in PR #235 is never edited or allow-listed; V08 requalification is a separate authorization.
