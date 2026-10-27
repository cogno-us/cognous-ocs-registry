# V09 security and limitation register; operational exclusion register

Non-authorizing. Items cite their source; none is a claim of safety. Severity vocabulary: CRITICAL / HIGH / MEDIUM / LOW / QUALIFICATION GAP.

## A. Findings and their disposition
| ID | Finding | Severity | Disposition | Source |
|---|---|---|---|---|
| F-01 | Runtime did not verify Registry policy narrowing at effect time (A08 BREACH at Runtime `4199a6c7`) | HIGH (Architect) | Remediated: Amendment 3, Runtime #148 `ac247daf`; requalified 8/8 HELD (same organization). Historical result preserved. | `results/v07-security/` |
| F-A1 | Operation substitution bypassed F-01 containment because the Registry operation label came only from the supplier-controlled binding | HIGH (proposed by lead; adjudicated by the Architect via Amendment 4) | Remediated: Amendment 4, Control Plane #86, Runtime #149; FA1-01/03/04 HELD. Historical BREACH preserved in #235 only. | #235 `7b72de9a`; `results/v08-fa1/` |
| No open CRITICAL or HIGH finding is known to this record. This is a statement about known findings from same-organization testing, not an assurance that none exists. | | | | |

## B. Open and characterized items (not remediated by any merged PR known to this record)
| ID | Item | Severity | Source |
|---|---|---|---|
| L-01 | F1: a non-canonical or unparseable log `entry_json` escapes the store verifier untyped (fail-closed, no effect) | LOW | #235 `results/v08-tier1/INDEX.md` |
| L-02 | B-11: a physically truncated database surfaces as an untyped `sqlite3.DatabaseError` (fail-closed) | LOW | #235 |
| L-03 | F2: with the binding validator unimportable the effect reports `unknown`/`dispatch_error`, not typed `verifier_unavailable` | LOW (informational) | #235 |
| L-04 | A09: `max_amount` and target prefixes are outside the F1AB payload and stay caller-owned | LOW | V07 FINDINGS |
| L-05 | D08: `execution_claims_v1.claim_json` is not authenticated at lock time (needs database write access, which also permits direct effect rows) | LOW / QUALIFICATION GAP | V07 FINDINGS |
| L-06 | `AtomicLocalControlPlaneExecutor.provision_claim` does not forward `policy_binding`; successor claims must use `provision_local_execution_claim` | LOW | #235 |
| L-07 | FA1-12: an effect passes under the old pin until the installer records its intent (revocation propagation delay) | CHARACTERIZED | `results/v08-fa1/` |
| L-08 | Consistent restore of both database and anchor is undetected (ADR 3.6, D01); anchor custody is operator-gated and not demonstrated | CHARACTERIZED / disclosed limit | V07, V08 |
| L-09 | Runtime wrapper workflows still call Stack Qualification reusable workflows at `1c1755ff` (older than the qualified revisions) | QUALIFICATION GAP (I01) | V07, V08 |
| L-10 | The F-A1 workflow runs on `pull_request` and `workflow_dispatch` only; no post-merge F-A1 run exists on `main`; the evidence is the PR-head run on a tree-identical commit | QUALIFICATION GAP | #237 workflow |
| L-11 | FA1-13 INCONCLUSIVE in the local record; the corrected case passed in CI only | QUALIFICATION GAP | `results/v08-fa1/README.md` |
| L-12 | V05 exceeded its 50-execution cap (about 58, last 7 authorized) | process exception, retained | Runtime #147 body |
| L-13 | Control Plane suite baseline reported 35 AGT failures (Plan v1.5 section 5); not re-verified for V09 | QUALIFICATION GAP | Plan v1.5 |
| L-14 | Runtime-side verification of successor claims under pydantic 2.11.9 untested (I03 weak); qualification pins pydantic 2.12/2.14 | QUALIFICATION GAP | V07 FINDINGS |
| L-15 | Runtime component CI lock lacked PyNaCl at V01, so the M1 module skips there (reported in Runtime #145; not re-verified at `main`) | QUALIFICATION GAP | Runtime #145 |
| L-16 | CCTV Ed25519 vector-license status open; synthetic keys imply no operational trust | open | Plan v1.5 section 5 |
| L-17 | Python 3.11/3.12 coverage is partial for several sprints (3.13 local, 3.12 CI) | QUALIFICATION GAP | V03, V06 |
| L-18 | Mixed licensing: Runtime root `LICENSE` is MIT (upstream); `engine/` and new files are Apache-2.0 under separate notices; Registry `baseline/` retains MIT and Apache notices | open (not legal advice) | repositories |

## C. Operational exclusion register (unsupported or unqualified claims)
| ID | Exclusion | Basis |
|---|---|---|
| X-01 | Production deployment of any component | Plan v1.5; HOLD |
| X-02 | Production cryptographic trust-root custody; synthetic Ed25519 keys only | Plan v1.5 section 5 |
| X-03 | External-anchor custody and rollback guarantees (see L-08) | ADR 3.6; V07 D01 |
| X-04 | Independent Ed25519 / canonical base64 security assessment (#26/#34 SECURITY-HELD) | Plan v1.5 |
| X-05 | Independent Tier 1 acceptance | Plan v1.5; NOT STARTED |
| X-06 | Real-world authority and effect dispatch: destination is synthetic SQLite only; no payment, network, subprocess or credentials | Runtime CLAUDE.md |
| X-07 | Cross-system revocation propagation (L-07) | FA1-12 |
| X-08 | Production OS privilege isolation: real-uid tests ran on ephemeral hosts as root with throwaway users; installer is a single process; a function boundary is not OS isolation | `results/v08-fa1/`; Runtime integration record |
| X-09 | Unqualified deployment environments: Linux x86-64 CPython 3.11-3.13, one synthetic tenant and one governed scope (MSOP-F1a-C11 slice, not full C11) | Plan v1.5 section 2 |
| X-10 | Unaddressed families and sets: F4/F5, EXT-S3-1..3, other tenants, universal policy interpreter; institutions and authority domains are carried unchanged, only units, adapters and actions are narrowed | Plan v1.5 section 2 |
| X-11 | Distribution, licensing and publication readiness (L-18); no version, tag or release exists | HOLD |
| X-12 | Power-loss and fsync durability; more than four concurrent processes; compromised-executor reporting; claim-level edits of grant, approval and budget rows | #235 unqualified boundaries |
| X-13 | Any statement that synthetic tests establish production safety | all |
