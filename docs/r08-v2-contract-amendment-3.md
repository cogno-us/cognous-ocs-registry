# R08 contract `r08-v2`: Amendment 3 (Runtime-side policy-narrowing containment at the effect boundary; versioned addendum)

Status: **AMENDMENT 3 to [`docs/r08-v2-contract.md`](r08-v2-contract.md), a versioned addendum, effective on merge of this file.** It is read on top of the frozen text together with [Amendment 1](r08-v2-contract-amendment-1.md) and [Amendment 2](r08-v2-contract-amendment-2.md). It is **not** an edit of any hash-pinned historical contract: the pinned files stay byte-identical and a reader applies this addendum on top of them. Documentation only: it adds no code and authorizes no implementation by itself (the Runtime change is a separate PR the Architect reviews). It changes no canonical binding member, no log schema, no policy-generation rule and no authority ownership. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD. Nothing here is "qualified".

Authorization: the Architect authorized one bounded contract amendment to close the V07 finding F-01 (HIGH): a claim with a recomputed commitment and a widened `effective_policy_digest`, supplied through a compromised or mis-composed claim supplier, let the Runtime commit an effect outside the activated Registry policy (V07 case A08, `cogno-us/cognous-stack-qualification` PR #234, FINDINGS.md at `878002c6`). Compromise of the normal Control Plane issuance workflow was **not** demonstrated; the finding is that the Runtime was not an independent enforcement point.

## 0. Frozen records stay frozen

| Frozen file | git blob (`git hash-object`) | sha256 |
|---|---|---|
| `docs/r08-v2-contract.md` | `ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f` | `64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01` |

`tests/test_contract_amendment_3_pins.py` recomputes these two values and checks the verbatim excerpt of section 1 against the frozen file. If the frozen file ever changes, that test fails and this addendum must be re-anchored by a new amendment, never by a silent edit.

## 1. Supersession table

| # | Frozen anchor | Frozen text (verbatim excerpt, tested as a substring) | Effect of this amendment |
|---|---|---|---|
| F-01 | `r08-v2` section 7.4, item 3 | `the narrowing itself is enforced by the evaluator on the policy the executor was given` | Superseded as the sole enforcement point. Narrowing is **also and independently** enforced by the destination guard under section 2. |
| F-01 | `r08-v2` section 7.4, item 3 | `checked only for self-consistency with the claim (it is never authority and never widens what the selection permits)` | Still true of the claim-carried member. The guard now additionally enforces containment against durable, authenticated state, so the effective policy can no longer widen what the selection permits even if the claim supplier is dishonest. |

The sentence "`effective_policy_digest` is **not** compared to durable state" stays true for the digest string: the guard does not compare digests to a stored value. It compares the **five sets** of the policy the executor evaluates with the five sets of the authenticated activated record (section 2). The ADR (`2026-10-26-adr-ext-s4-0-integration-contract.md`, section 7, "checked for self-consistency only") is read together with this section; where the ADR sentence would permit a claim supplier to be the only enforcement point of narrowing, this amendment governs.

## 2. Normative text: effect-time subset containment (replaces the reliance on claim-supplier honesty for narrowing)

For a claim that carries a binding, **after** items 1 to 7 of section 7.4 hold and **before** the effect is written, the guard MUST also hold, inside the same atomic transaction, under the same destination lock and lock-time clock, with no network or other I/O:

1. **Containment.** For each of the five F1a sets, `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions` and `allowed_authority_domains`, independently, the corresponding set of the **effective executor policy** is a subset of (or equal to) the set of the **activated Registry record payload**. A member present in the executor set and absent from the Registry set refuses the claim before effect commitment. A containment failure is a REFUSE with the existing typed code `policy_identity_mismatch` (no new reason code); the evidence cause names the first offending set.
2. **Authenticated record source.** The Registry sets are read from the record payload held in the Runtime's own authenticated store for the row the guard has just matched (item 3's record triple). The payload is trusted only because the store verification in the same transaction has established that the record bytes are canonical, that their digest equals the record pin of the matched statement, and that the statement is pinned by the logged `selection_digest`. A payload that is missing, not canonical, does not reproduce the pinned record digest, lacks one of the five sets, or whose sets are not well formed under the Registry value rules is **indeterminate authoritative state**: execution is prohibited (HOLD, typed `store_unknown`, never success). Nothing from the claim, the executor or a caller is a source for the Registry sets.
3. **Executor policy source.** The five executor sets reach the guard through the existing trusted executor-to-destination interface, derived by the executor from the same policy object it evaluates, at the same place and at the same time as the digest it already supplies. The guard recomputes the Registry effective-policy digest from those sets and requires it to equal the digest the executor supplied; it then requires that digest to equal the claim-carried `effective_policy_digest` (the existing self-consistency check, kept unchanged). Executor sets that are absent, malformed, or that do not reproduce the supplied digest refuse (an unavailable executor policy is `verifier_unavailable`; a mismatch is `policy_identity_mismatch`). A caller-supplied set unrelated to the evaluated policy is not accepted.
4. **Fail closed.** Any exception or inconsistency while performing this check refuses or HOLDs as above; it never skips the check. A claim with a binding and no executor sets is refused.
5. **No dependence on the claim supplier.** Items 1 to 4 do not read any claim member other than the already-validated `effective_policy_digest` self-consistency member and the record triple. A claim supplier that recomputes the commitment over a widened `effective_policy_digest` cannot cause an effect outside the activated record.
6. **Unchanged.** Claim with no binding (item 8), epoch, generation, activation, withdrawal, revocation, trust-snapshot and expiry checks, the canonical binding members, the log schema, the policy-generation rules, and authority ownership are unchanged. Legacy (ungoverned) execution is unchanged.

## 3. Residual limits (stated, not closed)

- The containment check trusts the executor to report the sets of the policy it evaluates (the same trust as the digest it already supplies). A compromised executor process that evaluates one policy and reports another is outside this guard; that is an executor-integrity question, not a claim-supplier one.
- `max_amount` and `allowed_target_prefixes` are outside the five Registry sets (F1AB payload) and remain caller-owned (V07 A09, LOW).
- Rows and records written by a party with direct write access to the database file are covered by the existing hash-chain and anchor verification, not by this amendment (V07 D08).
- This amendment is not evidence that F-01 is closed. Closure requires the Runtime change, its tests, and independent requalification of V07 case A08 against the patched Runtime.
