# 2. Exact V1 capability profile

Status: **proposed, not adopted.** It becomes the V1 scope only on the operator's approval ([09](09-operator-scope-decision.md)). The baseline classification (mandatory F1a+F1b; conditional F1c `max_amount`, F4 selected ages, F5 selected age; deferred F6, F1d, F7, F3, F8, F9, F10, F11) is the planning baseline from the brief; it is an analytical recommendation, not an adopted scope.

## Customer capabilities V1 is proposed to provide (none is built yet)

| ID | Capability | Fields | Owner of enforcement |
|---|---|---|---|
| CAP-1 | Centrally govern which actions, adapters and units a Runtime may execute. A registry value can only narrow the caller's own policy | `allowed_actions`, `allowed_adapters`, `allowed_units` (F1a) | Execution Runtime (`LocalExecutionPolicy.check`) |
| CAP-2 | Centrally govern which institutions and authority domains a Runtime may execute for, narrow-only, with the independent trusted-context check still in force | `allowed_institutions`, `allowed_authority_domains` (F1b) | Execution Runtime |
| CAP-3 | Centrally tighten how old a grant, conflict, policy or approval status may be before the Control Plane refuses | `status_max_age_seconds`, `approval_max_age_seconds` (F4); `ActionClass.max_status_age_seconds` (F5) | Control Plane (`_fresh`, class bound) |
| CAP-4 | Authenticated selection: a forged, replayed, expired, revoked or unselected record cannot govern an operation | n/a (governance) | Registry verification; consumer activation |
| CAP-5 | Consumer-owned activation with anti-rollback (strictly increasing epoch per scope key, external floor) | n/a | Enforcing component (Runtime destination) |
| CAP-6 | Exact effective-policy identity (selection, epoch, record digest, evaluator build, trust snapshot, caller and effective policy digests) in committed receipts and failure rows | n/a | Registry identity; Runtime carriage |
| CAP-7 | Required versus optional participation: a required policy that is missing or invalid never falls back to a wider caller policy; optional non-application is reported as "not applied", never as compliance | n/a | Registry decision; Runtime guard |
| CAP-8 | Revocation, withdrawal and expiry rechecked under the destination lock at the effect commit (Route B) | n/a | Runtime destination |
| CAP-9 | Durable negative evidence for refusals, holds and deny-all | n/a | Runtime failure records |
| CAP-10 | Documented restore and rollback behaviour: a lost or restored high-water store fails closed until re-baselined | n/a | Runtime destination; runbook |

Conditional (decision-gated, not in the recommended V1 acceptance scope): **CAP-11** centrally tighten the spend ceiling `max_amount`, single declared unit only, caller value stays authoritative.

## What V1 is designed to guarantee, and what it does not

Nothing in this section is built or tested yet: the only verifier today is the `FakeVerifier` test double, and the commit-time mechanism is an untested source reading.

- Narrow-only: the effective policy is never wider than the caller's. Unsupported or widening values are refused, never applied.
- Code keeps: check order and reason texts, `__post_init__` validation, exactly-one-effect, `max_effects`, target well-formedness, trusted-context binding, claim-versus-operation equality, single-effect gate, authorization/evidence separation, approval and grant binding.
- The effect-time guarantee is **identity binding under the lock**: the selection that produced the enforced policy was current and unexpired when the commit lock was held. It does not prove the evaluation was correct, and it does not cover Route A, same-host file access, loaded-code integrity, non-SQLite destinations or database restore.
- Every statement of capability is "developer-tested, not independently qualified" until a designated independent lead executes the gates at exact pins ([07](07-independent-qualification-matrix.md)).

## Explicit exclusions (as lost customer capability)

| Excluded | Customer capability not available in V1 | Why |
|---|---|---|
| `max_amount` (unless added) | Cannot centrally lower the spend ceiling; it stays a host literal (the caller's ceiling still enforces) | D6 ruling and numeric encoding open; unit-less single ceiling; single-unit rule needed |
| `max_effects` (RT-F1c-02) | Cannot centrally govern the per-policy effect-count ceiling | Source cannot decide it; atomic budget is a separate mechanism |
| F1d `allowed_target_prefixes`, `target_match` | Cannot centrally govern target scope for local execution; the manifest's `allowed_targets` still applies | Mode ordering never toward `legacy-prefix` is unruled; low benefit |
| F6 agent permissions | No central agent least-privilege file; the supported path governs this through grants | Only the unsupported legacy shell is file-driven |
| F7 dedupe/TTL/horizon, `funded_authorities` | No central duplicate-delivery windows | Unresolved and low benefit; the default-off identity issue (GAP-G1-01) is not a registry remedy |
| F3 lease timeout, OpenShell timeout/profile | No central operational tuning | Low benefit, operational |
| F4 identity/mandate ages, clock tolerance, outage extension, `anchor_deadline_to_inputs` | "Central freshness control" covers **status and approval ages only** | No scenario varies them; keep host-owned |
| F5 `requires_revocation_assurance` and relaxing toggles | No central switch | Needs holder-inventory profile; relaxing toggles never registry-reachable |
| F8, F9, F10, F11 | No central tool lists, redaction or other controls | Guardrail or not relevant to V1 (F11 low) |
| Route A commit-time guarantee | A registry-selected policy on Route A is not rechecked at the commit boundary | Cannot be closed with the available mechanism (GAP-G3-03); scoped out and disclosed |
| Operational trust root, key ceremony, production host, GCR consumer | No operational authenticated selection; the emulator proves nothing about production | Operator-gated; release, publication and production on HOLD |

These are not automatically permanent exclusions. The typed-adapter architecture (one adapter per owner, field manifest, `min` composition) extends to any of them without redesign once its ruling exists.
