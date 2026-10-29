# Parameter B: terminal-revocation enablement - source reconciliation (B1) and disposition

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (deferred, not waived). Governing documents as in `01-...`. Control Plane source read at `main` `4780abe0af54147c0770e98cb7b964b74b2008c4`. Audit entry: `P-RG-C-TERMINAL-REVOCATION-enabled` (`NEW:terminal-revocation-marker`, discovered by audit pass 2), blocking decision: "approval_commitment coupling (AUD-D06)".

## The audited parameter and its canonical rule

`RuntimeAuthorityProfile.terminal_revocation: TerminalRevocationProfile | None` (`runtime_authority.py:182-191,214`). Absent = off; present = on (`terminal-revocation/0.1`). When on, a grant revision that a retained resolution check already observed `revoked` is refused `grant_revocation_recorded` at decision and at effect time, even if the status now reads `active` (`bounded.py:2390-2392`, `_recorded_grant_denial` at `bounded.py:1478`). `suspended` stays reversible; a new grant revision is the only way back (`reopen_conditions`, `runtime_authority.py:486-496`).

## Monotone direction (from source, not assumed)

`on` is the stricter value: it appends one refusal reason and removes none (the check is `if self._terminal_revocation is not None and self._recorded_grant_denial(...)`). Off cannot be reached from on by any Registry value in the adopted design (the effective value is the stricter of host and Registry).

## The four distinctions

| Concept | Where it lives | Touched here? |
|---|---|---|
| Permission to initiate terminal revocation | The grant authority's own status service (outside the Control Plane; the Control Plane only reads `grant_status`) | No |
| Obligation to enforce terminal revocation | This profile section (`on`) | Yes: a Registry `on` can only ADD the host's own obligation |
| Evidence that terminal revocation occurred | The host's retained `resolution_checks` (the record store); a revocation the control plane never observed cannot be remembered, and the store has no keyed integrity check (`runtime_authority.py:183-190`) | No: Registry never writes, edits or creates a record |
| Authority to reverse or supersede the terminal state | A new grant revision from the grant authority | No |

## Other required traces

- Persistence and replay: the memory is `records.load().resolution_checks`, appended by the existing resolution path regardless of this section; enabling it changes only how already-retained observations are READ. Prior negative records are never removed or rewritten.
- Binding: the section is in the profile dump while present, so `approval_commitment` and the persisted `catalogue_digest` change when it is forced on; an approval issued against the host profile is stale for the effective one, and a decision persisted under one profile is refused by a workflow whose effective profile differs (existing mismatch refusal).
- Relationship to `requires_revocation_assurance`: none in the evaluator. Both only add refusals/holds; they compose independently.
- No silent recovery: the Registry selection is a REQUIRED family, re-verified at every boundary; a withdrawn, revoked or expired selection refuses, it never falls back to off. (Rebuilding the workflow without Registry is a host configuration decision outside this adapter; there is no ratchet.)

## Disposition: IMPLEMENT

A defensible narrowing relation (`off < on`) and an existing enforcement boundary (`bounded.py:2390`) both exist, binding uses the existing profile commitment, and the parameter separates cleanly from every authority and state-machine concern: no new revocation authority, no implicit state transition, no widening of who may revoke, no weakening of irrevocability rules. No stop condition applies.
