# Parameter A: `requires_revocation_assurance` - decision and evidence

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (deferred, not waived). Governing documents: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (`ENGINEERING_CONSTITUTION.md`, `ADOPTION.md`), Static Migration Plan v1.1, Engineering Plan v1.5, audit #60, assessment #65, decision #67. Reconciliation: `01-...`.

**Decision: IMPLEMENTED (open PRs; not merged).**

| Item | Value |
|---|---|
| Registry PR / head | #69 / `42a666328b974a7581013358bcf8bc7b9eac7761` (base `e8b572cc669bee668abc88846f7b071a74f13440`) |
| Control Plane PR / head | #92 / `a62ca8d8e4088c95407c2000dcca081383d8dd4d` (base `4780abe0af54147c0770e98cb7b964b74b2008c4`) |
| Contract / family | `r08-v6` / `f5-action-class-revocation-assurance-policy`, member `class_requires_revocation_assurance` |
| Narrowing relation | `not_required < required`; operator intersection; effective value is the stricter of host and Registry per class; a Registry value never removes a host `true` |
| Enforcement boundary | `runtime_authority.validate_extensions` via `bounded._resolve` at decide and execute (existing, unchanged); the added consequence is the `holder_inventory_missing` hold |
| Effective policy identity | `v6_policy_identity.effective_policy_digest(family, payload, contract_version="r08-v6")`, domain `ocs-reg/r08-v6/effective-policy\n`; Control Plane binds the final `RuntimeAuthorityProfile` digest |
| Approval binding | The flag is inside the profile dump, so `approval_commitment` and the decision binding's `catalogue_digest` cover it. No preimage, persisted field or evaluator change |

## Limitations (not hidden)
- A requirement is not evidence. No assurance receipt exists or is invented. The only lifting condition is a host-declared holder inventory, which is an unverified host claim.
- Where the host has no inventory a Registry `required` holds every action of the class (self-inflicted denial; fail-closed, intended, tested).
- Selection-source custody, freshness, rollback protection are host duties; the commit gate runs before, not inside, the destination transaction.

## Tests and mutations
Revocation suite 141 passed (assurance alone a01-a11, composition, widening, replacement, withdrawal, between decision and effect, after execute entry, stale and cross-profile decisions, restart, protected-file pins). Mutation: 50 mutants over both families, 49 killed, A07 equivalent. Raw: `evidence-cp/`.
