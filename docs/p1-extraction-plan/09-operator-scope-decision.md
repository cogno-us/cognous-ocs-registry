# 9. Operator-facing scope decision (plain language)

This page is for the operator. It asks for one decision and flags one second item. Everything else in this plan is an engineering or architectural matter the Architect and component owners resolve, per the decision-rights table in plan v1.3. Nothing is authorized by reading this page; implementation starts only after the Architect accepts the plan and you approve a scope.

## What V1 would let your customers do

Today, the limits on what an agent runtime may do (which actions, which adapters, which units, which institutions, which authority domains) are written into each deployment by whoever builds it. V1 would let you set those limits centrally, in signed records that can **only make the limits tighter, never looser**. It would also let you tighten how old a status or approval may be before the Control Plane refuses to act on it. Every change would be signed, versioned, revocable, and recorded in the evidence with exact identity, and a missing or invalid required setting would stop the action instead of falling back to something wider.

## Decision 1 (needed): which settings are in V1?

| Option | Settings in V1 | What customers can do | Cost and risk |
|---|---|---|---|
| A | The five Runtime allow-lists | Centrally limit actions, adapters, units, institutions, authority domains | Smallest. Freshness limits remain set per deployment |
| **B (recommended)** | A plus three Control Plane freshness limits (status age, approval age, per-class status age) | Everything in A, plus centrally tighten how stale a status or approval may be | A modest increase (about 10 to 18 engineer-days of the total). The three are plain whole-second numbers that only tighten. One of them (the per-class one) requires approvals to be issued against the narrowed profile, so it is sequenced last |
| C | B plus a spend ceiling (`max_amount`) | Everything in B, plus centrally lower the amount an operation may spend, for a single currency/unit at a time | Needs an architect ruling and a numeric-format decision first; adds about 4 to 7 engineer-days and testing burden; does not support different ceilings per unit |

Recommendation: **B**. It covers the two things customers most plausibly ask to govern centrally (what a runtime may touch, and how fresh the information behind a decision must be) without reopening spend-ceiling semantics. The spend ceiling stays designed and ready to add. If your customer scenarios already depend on central spend limits, choose C.

What these options leave out is listed in [02](02-v1-capability-profile.md): central target scoping, agent permissions, duplicate-delivery windows, redaction switches and the other deferred settings. Choosing B or C does not rule any of them out later.

## Decision 2 (needed, short): does V1 cover both execution routes?

The Runtime has two routes to an effect. V1 can check, at the moment of commit, that the selected policy is still current only on one of them (the atomic route). The other cannot be closed with the available mechanism. **Recommended: V1 covers the atomic route only and says so plainly in its status report.** The alternative is to declare the other route part of V1, which would require a larger redesign than this plan covers.

## What you are not being asked

Field formats, validation rules, numeric encodings, reason codes, adapter design, expiry semantics, test infrastructure, key algorithms and sequencing are decided by the Architect and component owners. The three items below are flagged for awareness only and need no decision from you now:

- **Architect decision with a security flavour:** how the commit-time check is carried (a small additive change in the Runtime versus changing the claim in both repositories). If the Architect rejects the smaller option, it adds a Control Plane change and re-pinning both repositories.
- **Built but off:** the capability to make a policy *mandatory* (refuse to act without it) is built inactive. Turning it on later is yours to authorize.
- **Independent qualification:** no independent qualification lead is designated. If none can be secured by the end of S5, the result will be reported as "not independently qualified"; that single fact, not any technical detail, would come to you.

Release, publication and production remain on HOLD. No trust root, key ceremony, credentialed run or paid test is requested.
