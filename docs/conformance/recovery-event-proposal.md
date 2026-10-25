# Proposal: separate recovery event (NOT IMPLEMENTED / NOT AUTHORIZED)

Status: **NOT IMPLEMENTED. NOT AUTHORIZED.** Documentation only, written to record what a recovery contract would need if the Architect later authorizes one (ruling R4, 2026-10-25). The kit contains no code path, input kind, vector or state field for it. Nothing here extends the closed activation event vocabulary (`activate`, `withdraw`, `revoke`, `sync`), and `rebaseline` is not a synonym for it. Adopting any part of this needs an ADR amendment and operator authorization.

## Why a separate event

After loss of authoritative durable state the store is `unknown` (contract 8.3: lost state is unknown, never zero). Automatic re-baselining is rejected: the loss itself is the condition that removes the evidence a consumer would use to re-baseline, so the consumer cannot vouch for its own recovery. Recovery therefore needs an independently authenticated and authorized procedure with monotonic state continuity, outside the activation event stream.

## Proposed shape (illustrative, for review)

A `store_recovery` statement, in its own append-only recovery log chained to the externally held log-head anchor, never in the activation log:

| Member | Rule |
|---|---|
| `recovery_id` | unique, never reused |
| `recovery_generation` | integer strictly greater than the highest generation in the externally held recovery record |
| `store_id` | the store being recovered |
| `prior_anchor` | the externally held `{log_head, head_hash}` the recovered store must continue from |
| `continuity` | per-scope high-water, revoked set, revoked key, record and issuer sets, `min_epochs` and snapshot version that the recovered store must meet or exceed, taken from externally held evidence, never from the lost store or a caller |
| `authority` | a recovery grant held by an authority independent of selection issuers and of the enforcing component, naming `store_id` and the `prior_anchor`; a selection or snapshot key can never recover a store |
| `decision_ref` | operator-approved decision, as for `relax_scope_required` |
| `signature` | verified by the registry layers; the kit would only receive `verified: true/false` |

## Proposed effects

1. Verified recovery may move the store from `unknown` to `known` only when the recovered content is a verified copy whose log reaches `prior_anchor` and whose floors meet `continuity`. The new anchor continues the old one; no floor, high-water or revoked set is lowered or cleared.
2. If no such verified copy exists, the store stays `unknown`; the only way forward is a fresh selection at an epoch strictly above the externally held high-water for each scope, under the normal `activate` preconditions, after a recovery statement that declares the continuity floors. Previously revoked identities, records, issuers and keys stay revoked.
3. A recovery never activates, withdraws, revokes or clears the ratchet by itself, never supplies authorization, and is itself logged with negative evidence on refusal.
4. Recovery of a store with no externally held anchor is not defined: the host must hold the anchor and the continuity floors outside the store (contract 8.3).

## Open questions for the Architect

- Who is the recovery authority, and is a separate grant type acceptable?
- Is a recovery log a companion stream or a hash-chained extension of the evidence stream (the same question `EXT-S4-0` has for negative evidence)?
- Where are the continuity floors held, and who attests them?

Until these are ruled, every attempt to proceed after lost or absent durable state is `UNKNOWN_FAIL_CLOSED` (or `REFUSE` or `REFUSE_STALE` where the state is determinate), never `ACCEPT`.
