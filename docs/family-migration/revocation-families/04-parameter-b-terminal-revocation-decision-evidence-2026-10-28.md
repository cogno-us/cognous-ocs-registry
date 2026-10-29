# Parameter B: terminal-revocation enablement - decision and evidence

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (deferred, not waived). Governing documents as in `03-...`. Reconciliation: `02-...`.

**Decision: IMPLEMENTED (open PRs; not merged).**

| Item | Value |
|---|---|
| PRs / heads | Registry #69 `42a666328b974a7581013358bcf8bc7b9eac7761`; Control Plane #92 `a62ca8d8e4088c95407c2000dcca081383d8dd4d` |
| Contract / family | `r08-v6` / `f5-terminal-revocation-enablement-policy`, member `terminal_revocation` (`off|on`) |
| Narrowing relation | `off < on`; the stricter wins; a Registry `off` never removes a host section (`composed_widens_host`) |
| Enforcement boundary | `bounded._recorded_grant_denial` (existing, unchanged): a grant revision whose revocation a retained resolution check already observed stays refused (`grant_revocation_recorded`). `suspended` stays reversible |
| Four distinctions | Permission to initiate: untouched. Obligation to enforce: this is what `on` selects. Evidence of occurrence: the host's own retained checks, nothing new. Authority to reverse: unchanged; a new grant revision is the only way back |
| Effective policy identity / binding | As Parameter A; the `terminal_revocation` section is inside the profile dump, so the commitment covers it |

## Limitations
- The memory is the host's retained `resolution_checks`; a revocation never observed cannot be remembered, and the store has no keyed integrity check.
- No new revocation authority, state transition or reversal path. Registry `on` is not permission to revoke.

## Tests and mutations
Terminal alone b01-b10, composition c01-c08 (both families together and with F4/F5), persistence across restart, replay and stale state. Shared mutation battery as in `03-...`. Raw: `evidence-cp/`.
