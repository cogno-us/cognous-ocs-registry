# R10 feasibility: closing the F1 effect-time gap (read-only investigation, R08-S01 lane G)

Purpose: compare the smallest defensible ways to make registry-derived F1 restrictions hold at the authority-to-effect commit, as the Architect's C-03/LD-01 ruling requires. This is a recommendation for Architect adjudication. **Nothing is implemented, no Runtime or Control Plane file is changed, and no option is selected.**

Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification. The F1 authority-to-effect guarantee remains **UNQUALIFIED**. A registry selection is not an OCS execution grant. Recording a digest does not prove atomic validity.

## 1. Sources and revisions examined

| Source | Revision | Note |
|---|---|---|
| Execution Runtime | HISTORICAL pin `ec728da6dc301a664b331ac8986afd6e850a1273`; CURRENT head `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` (re-fetched, unchanged) | Engine differs in `engine/local_authority_effect.py` only (+52/-3; terminal approval revocation) |
| Control Plane | HISTORICAL pin `0a41faa972699f7ec3063967a14cd9bdd3e67d27`; CURRENT head `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | `src/agent_control_plane/local_authority_effect.py` differs (+8/-2, claim journal); `bounded.py` blob `2cc8d998...` identical at both |
| Registry | `main` `1324bab15da20a32fb82f54c444d1e808543b0e6`; frozen evaluator blob `2fc880dae37eac76e5074533435740ce0684209d` | `safe_executor.py` blob equals the Runtime's at pin and head |
| Prior findings read | `docs/r08-preparation/03`, `04`, `10`; `docs/r08-s01-contract.md` | Not repeated; cited |

Line numbers are at the Runtime head `c5e97e87` unless marked "(pin N)". `engine/atomic_local_control_plane_executor.py` (blob `d5ff3135...`) and `engine/safe_executor.py` are byte-identical at pin and head. Not inspected: any production host, the hub repository, Control Plane resolver implementations, `COG-REG-SHARED-ADD-01`. **No test or suite was run by this lane**; statements about upstream tests rest on file names and docstrings only.

## 2. What the source shows (the gap, precisely)

1. **[EXISTING] The F1 check is outside the transaction.** Route B: `AtomicLocalControlPlaneExecutor.execute` calls `self.policy.check(snapshot.operation)` at `atomic_local_control_plane_executor.py:69`, then `destination.execute_claim_atomic(...)` at line 97. The atomic path opens `BEGIN IMMEDIATE` at `engine/local_authority_effect.py:798`, takes trusted time after the lock (line 800), calls `_validate_claim_state` (line 825), consumes the claim and inserts the effect and receipt. `policy.check` is never evaluated inside it. Route A: `policy.check` runs in `observe()` (`control_plane_adapter.py:101`) and again in `execute_snapshot` (`safe_executor.py:890`); the destination `apply` is then called with no authority re-read (`bounded.py:1782-1783` comment) and the freshness profile "narrows this window; it does not close it" (`bounded.py:1797-1800`). Route A has no destination-transaction read of authority at all.
2. **[EXISTING] What the F1a result depends on.** The F1a restrictions are membership tests on `op.adapter_id`, `op.action_id` and `op.unit` (`safe_executor.py:417-424`). At commit, `_validate_claim_state` already requires those three values (and `operation_commitment`, line 698) to equal the claim exactly (lines 690, 691, 696). So between check and commit the **operation cannot change**; the only thing that can differ is the **allowed sets** that were in force, which in a registry design come from a selection and a record.
3. **[EXISTING] The only policy state revalidated at commit** is the claim's `policy_state` rows `{ref, version, status}` (and tenant), compared with `authority_policies_v1` (lines 746-758). They come from the grant approval's `policy_versions` and carry no digest, selection, epoch, interval or evaluator identity (`local_authority_effect.py` Control Plane lines 48-52, 106-107). A selection is not a grant policy ref (Architect ruling), so these rows are not the vehicle.
4. **[EXISTING] Expiry at commit.** Only the claim's own interval (line 707) and the grant's interval (line 724) are checked, against the trusted clock taken under the lock. The claim `expires_at` is `min(grant expiry, proposal expiry, caller-supplied expires_at)` (Control Plane lines 385-391), so a caller-supplied `expires_at` can already shorten it.
5. **[EXISTING] Authority rows are written by trusted writers** with `BEGIN IMMEDIATE` (`set_policy_state`, line 553 at head; pin 505), which serialize with the effect transaction; one SQLite database only; same-host file access can bypass the Python modules (`docs/execution-boundary.md`, "These controls do not constitute host confinement"). `provision_claim` (line 262) **seeds** missing grant/approval/policy/evidence rows from the claim but never overwrites an existing row; the profile marker (lines 186-189) refuses any other profile URN.
6. **[EXISTING] Precedent for in-transaction re-evaluation.** The optional `sqlite-effective-grant/0.1` destination keeps a retained sorted permission set and refuses, under the actual `BEGIN IMMEDIATE`, when `requested_permissions` is not a subset (`engine/effective_grant.py:80-103`, `effective_grant_permissions_insufficient`). It cannot be combined with the atomic profile on one database (lines 95-101 and 802-806). It shows the pattern is accepted in this codebase; it does not qualify it.
7. **[EXISTING] Qualification hook.** `_transaction_stage(stage)` (line 778; stages `before_begin`, `after_begin`, `after_effect_insert_before_commit`, `after_commit`) is the existing deterministic-barrier seam; upstream tests subclass it (`tests/test_atomic_post_commit_fault_injection.py:60`, `tests/test_crashed_holder.py:95`). Existence only; not run.
8. **[EXISTING] Evidence written in the transaction** is the attempt, the attempt event, the consumed claim, the budget increment, the effect and the receipt, which today holds `grant_state_commitment`, `checked_at`, `claim_id`, `attempt_id` (lines 831-843). Failure rows (`record_failure`) are written **after** a refusal in a separate step (`atomic_local_control_plane_executor.py:188`), so refusal evidence is recorded, not committed with a decision.

## 3. Options

Common to all: registry-side outputs (verified selection, record digest, evaluator identity, effective sets) are data; OCS owns the decision at commit. No registry call is made from inside any transaction. No new execution engine is created.

### Option A: re-evaluate the registry-derived F1 restrictions inside the existing atomic boundary
- **Idea [PROPOSAL].** A trusted writer keeps an authoritative selection row in the destination database (selection id, epoch, status, `valid_from`/`valid_until`, record digest, evaluator build, and the allowed adapter/action/unit sets). Under `BEGIN IMMEDIATE`, after `_validate_claim_state`, the destination re-checks identity, interval against the lock-time clock, and evaluates the three memberships against the stored sets (the `effective_grant` subset pattern, item 6).
- **Owner.** Runtime (destination) with the Control Plane claim model; OCS Architect decides. The registry supplies data only.
- **Interface changes (names).** New table (for example `authority_selections_v1`) and trusted writer (`set_selection_state`); new `execute_claim_atomic` input naming the expected selection; successor profile URN and marker (items 5, 3 of section 5); in-transaction membership predicates.
- **Concurrency.** Writer and effect serialize on `BEGIN IMMEDIATE`; whoever commits first wins. Single SQLite database only; no cross-domain atomicity.
- **Revocation race.** Revocation committed first: effect refused before insert. Effect committed first: no rollback (CA22); the receipt's `checked_at` shows the order.
- **Selection expiry at commit.** Closed for this route: `now` is taken under the lock (line 800) and compared with the stored interval.
- **Grant/selection separation.** Separate table and writer; a grant row never stands in for a selection. A passing grant does not satisfy the selection check or the reverse.
- **Evidence commitments.** Committed in the transaction: a selection-row commitment in the receipt (extends line 839), the consumed claim, the effect. Recorded only: refusal rows.
- **Refusal/HOLD.** Crosswalk of `04` section 4.3: selection row absent, unreadable or not current maps to HOLD (existing `denied` + `authority_hold` + `current_authority_rejected`, free-text detail); membership failure maps to DENY (`policy_denial` class). Mapping stays decision LD-02; no new reason code is assumed.
- **Failure recovery.** Pre-commit refusal leaves the claim `issued`; recovery is a new attempt under a fresh evaluation and, if the selection changed, a new claim. Post-commit ambiguity uses existing `unknown` + `reconcile_claim` (line 958); unchanged.
- **Qualification scope.** In-transaction membership, expiry boundary, revocation race with deterministic barriers (item 7), seeding hazard (a selection row must pre-exist; the existing seed-from-claim pattern, item 5, must not apply), mutation of the new check must fail the test.
- **Compatibility.** Route B only. Route A has no atomic read, so it is not closed. Needs successor claim/profile (the claim commitment covers `policy_state`; the marker table refuses other profiles); Control Plane `verify_local_execution_claim` requires the profile constant (line 549), so **both repositories change**.
- **Costs and risks.** (i) Membership logic must come from the same registered evaluator. Extracting predicates from `LocalExecutionPolicy` changes `safe_executor.py`, i.e. the **frozen evaluator blob `2fc880da` pinned by every S03/R08 record and selection**, forcing re-pinning; leaving it untouched means a second copy of the membership test in the destination, which is a second evaluator definition. (ii) `LocalExecutionPolicy.__post_init__` refuses empty sets, so an explicit deny-all dimension cannot be constructed there; the destination would need its own deny rule. (iii) Only the registry-derived sets are covered; caller-owned fields (target, amount, effects) stay host-evaluated pre-claim.

### Option B: bind an immutable policy evaluation and its exact selection identity, revalidated at commit
- **Idea [PROPOSAL].** Before claim issuance the verified consumer evaluates once (verified selection, record bytes by digest, `compose_f1a`) and produces an immutable **evaluation binding**: selection id, epoch, selection digest, record id/version/digest, evaluator build, `valid_until`, the operation commitment, and a digest of the enforced effective sets. The claim carries it (covered by the claim commitment). At commit the destination compares it with an authoritative selection row (identity equal, status current, not revoked, `now < valid_until`) under `BEGIN IMMEDIATE`. The executor passes the digest of the sets its own `policy` enforced so the destination can require equality with the bound digest.
- **Why widening is prevented [PROPOSAL, argument not test].** The operation is fixed by the claim (item 2) and the record bytes are fixed by digest; a wider policy needs a different record or selection, which changes the bound identity and refuses. This holds only if the authoritative row is written by the trusted writer and the evaluation was honest at issuance.
- **Owner.** Control Plane (claim issuance carries the binding) and Runtime (destination compare), with the host as the evaluation producer; OCS Architect decides.
- **Interface changes (names).** Successor claim fields (for example `registry_binding`) and commitment; destination selection row and trusted writer (as A); `execute_claim_atomic` input for the enforced-policy digest; receipt additions.
- **Concurrency / revocation / expiry.** As Option A for identity, status and interval (all under the lock with lock-time clock). Expiry is closed on Route B.
- **Grant/selection separation.** As A; the binding is a separate claim member from `policy_state`.
- **Evidence commitments.** Committed: claim (with binding), selection-row commitment and the compared binding in the receipt, effect. Recorded only: refusals; the offline replay of the evaluation from retained bytes.
- **Refusal/HOLD.** As A for identity/status/interval; a mismatch between enforced-policy digest and bound digest refuses (REFUSE class: contract cannot be accepted). The destination does **not** re-evaluate membership, so it proves "the selection that produced this evaluation is still current", not "the evaluation was correct".
- **Failure recovery.** As A.
- **Qualification scope.** As A, plus: tampered binding in a provisioned claim, selection swap between issuance and commit, enforced-digest mismatch, and an independent replay of the evaluation from retained record bytes.
- **Compatibility.** Route B only; successor claim profile; both repositories change. **Does not touch `safe_executor.py`**, so evaluator identity and every existing pin stay valid, and no second evaluator is introduced.
- **Costs and risks.** Trust in the issuance-time evaluator is not atomic-checked; a compromised host that can write authority rows is outside the guarantee in either option (item 5). The enforced-policy digest needs a Runtime interface addition. The caller-owned fields remain host-evaluated pre-claim.

### Option C (partial, near-zero change): clamp claim expiry to the selection interval
- **Idea [PROPOSAL].** Pass `expires_at = selection.valid_until` into claim provisioning (existing parameter, Control Plane lines 337, 388-391). The destination then enforces expiry atomically through the existing claim-interval check (line 707) with trusted time.
- **Coverage.** Closes selection expiry on Route B with no schema or profile change. **Does not** detect revocation, supersession or a swapped selection after issuance (the destination does not know the selection); the destination cannot verify the host actually clamped; a short TTL narrows but does not close the revocation window. **Insufficient alone** under C-03/LD-01. Useful as a component of A or B and as the cheapest answer to LD-09.

### Rejected for this purpose
- **Registry check at `observe()` or in a pre-dispatch step, or a registry call inside the commit transaction:** a competing authority check with a window (item 1) that would be read as authorization.
- **Modelling the selection as a grant `policy_versions` / `PolicyStatus.digest` row:** contrary to the Architect ruling; also leaves F1 membership unevaluated at commit (item 3).
- **Evidence-only attachment:** records, does not prove (Architect ruling).

## 4. Comparison

| Concern | A | B | C |
|---|---|---|---|
| Closes selection expiry at commit (Route B) | Yes | Yes | Yes |
| Detects revocation/swap between issuance and commit | Yes | Yes | No |
| Re-evaluates F1 memberships atomically | Yes (second membership copy or evaluator change) | No (identity-bound; evaluation trusted from issuance) | No |
| Touches frozen evaluator blob `2fc880da` | Likely (or duplicates logic) | No | No |
| Repositories changed | Runtime, Control Plane | Runtime, Control Plane | None (host configuration) |
| Closes Route A | No | No | No |
| New schema/profile | Yes | Yes | No |

## 5. Recommendation for Architect adjudication [PROPOSAL]

1. Treat **Route B (`AtomicLocalControlPlaneExecutor`) with the authoritative-row mechanism** as the only route this gap can be closed on; scope the R10 emulator profile to it (decision C-06). Route A can only be narrowed.
2. Prefer **Option B**, with **Option C adopted as a stopgap** for LD-09 until a successor profile exists. Rationale: B closes the revocation/swap/expiry races atomically without modifying the frozen evaluator or adding a second evaluator, and meets the Architect's "independently defensible binding protocol that prevents policy changes from widening the executable operation between check and effect". Choose **A** instead only if the Architect requires the destination itself to re-derive F1a memberships, and then decide first how to avoid a second evaluator definition.
3. Whichever is chosen, the guarantee stays **UNQUALIFIED** until an independent qualifier runs the barrier-based battery in section 3 against an exact-source integration candidate.
4. Both options need a **successor local-authority-effect profile** in the Runtime and Control Plane; neither can be done from the registry repository.

## 6. Remains unqualified

F1 authority-to-effect consistency; the issuance-time evaluation honesty (B); Route A entirely; any non-SQLite or remote destination; same-host bypass; loaded-code integrity; all claims in this report beyond source reading (no test was run); the closed-code mapping (LD-02).

## 7. Decisions needed

| ID | Decision | Owner | Blocking consequence |
|---|---|---|---|
| R10-F-01 | Choose A, B, or B with C as a stopgap; confirm Route B only | OCS Architect with Runtime and Control Plane owners | R10 has no defined binding; F1 stays UNQUALIFIED |
| R10-F-02 | Approve a successor local-authority-effect profile (claim fields, destination table, receipt) | Runtime and Control Plane owners, OCS Architect | No source change can begin |
| R10-F-03 | Select the exact-source integration candidate (pin vs head; terminal approval revocation exists only at the head) | Runtime and Control Plane integration owners; operator for scope | Interfaces cannot name a revision (S-01, LD-06) |
| R10-F-04 | Who writes the authoritative selection row, and how selection withdrawal reaches it | OCS Architect; operator | Revocation race has no source of truth (LD-04) |
| R10-F-05 | Whether the evaluator blob may change (Option A) and the re-pin policy | OCS Architect; operator | A cannot avoid a second membership definition |
| R10-F-06 | Name the production host integrator (emulator profile uses a synthetic adapter) | Operator | No production claim can be made (C-01) |
| R10-F-07 | Independent qualifier for the effect-time path | Operator | No QUALIFIED label (D13, F-01) |
