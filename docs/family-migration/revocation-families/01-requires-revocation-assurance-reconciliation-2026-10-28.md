# Parameter A: `ActionClass.requires_revocation_assurance` - source reconciliation (A1) and disposition

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (deferred, not waived). Governing documents: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (`ADOPTION.md` at the same revision), Static Migration Plan v1.1, Engineering Plan v1.5, adopted audit (Registry PR #60), consolidation assessment (PR #65) and decision record (PR #67). Control Plane source read at `main` `4780abe0af54147c0770e98cb7b964b74b2008c4`. Audit entry: `P-RG-C-010-requires_revocation_assurance` (RG-C-010), blocking decision recorded by the audit: "is a Registry-forced True meaningful when it holds the class until a host HolderInventory exists (self-inflicted denial); setting True changes the profile dump and approval commitment".

## Answers to the ten reconciliation questions (each with its source)

| # | Question | Finding |
|---|---|---|
| 1 | Owner and domain | `ActionClass.requires_revocation_assurance: bool`, default `False`, `exclude_if` false (`runtime_authority.py:135`). Owner: the host `RuntimeAuthorityProfile.actions[...]`. Domain: `bool`. |
| 2 | Host default / required behaviour | Default `False` (omitted from dumps). `True` makes the class hold `holder_inventory_missing` unless `profile.holder_inventory` exists and enumerates at least one holder (`runtime_authority.py:430-433`, `holder_inventory.py:43-51`). |
| 3 | Reversibility / revocation interactions | None in the evaluator: the branch reads only this flag and `holder_inventory`. It is independent of `irreversible`/`reversibility` and of terminal revocation. |
| 4 | Is `True` at least as restrictive as `False` | Yes. `True` can only append one reason (`holder_inventory_missing`); with an inventory present it changes nothing; it never removes a reason or admits anything. `False -> True` is the only narrowing direction. |
| 5 | Consuming paths | `validate_extensions` (`runtime_authority.py:308`), called from `_resolve` (`bounded.py:2561`), which `decide` (`bounded.py:1635`) and `execute` (`bounded.py:1685`) both call, on the runtime-authority-profile path only. No other module reads the flag (`holder_inventory.py` documents it). |
| 6 | In `approval_commitment` | Yes, through the profile: `approval_commitment` hashes `profile.model_dump(mode="json")` (`runtime_authority.py:236-243`). The flag appears in the dump only while `True`. |
| 7 | In the persisted decision binding | Yes, through the same profile hash: the extension's `catalogue_digest` is `commitment(profile.model_dump(mode="json"))` (`runtime_authority.py`, `validate_extensions`). No new member is needed. |
| 8 | Selection withdrawal / revocation | Governed by the consolidated lifecycle: a mandatory family is re-verified at construction, decision entry, execute entry and the pre-dispatch gate; any failure refuses the whole workflow. |
| 9 | Is there a source of assurance, independently verifiable | No. The only satisfaction criterion in the source is the PRESENCE of a host `HolderInventory`, which `holder_inventory.py` itself describes as "a claim by whoever wrote it": the inventory cannot be checked for completeness and says nothing about whether a revocation reached any holder. |
| 10 | Can Registry narrow it without granting capability | Yes: a Registry `required` can only add the hold above. It cannot supply, create or verify an inventory. |

## Policy requirement versus evidence

`requires_revocation_assurance` is a POLICY REQUIREMENT. Nothing in the Control Plane (and nothing implemented here) produces EVIDENCE that the requirement was satisfied: no assurance receipt exists and none is invented. Setting the flag to `true` does not establish revocation assurance. The only enforced consequence is the existing hold, and the only thing that lifts it is a host-declared inventory (an unverified host claim). The Registry family therefore means "the host must have declared an inventory", never "revocation reaches all holders".

## Disposition: IMPLEMENT (smallest valid family and consumer integration)

Monotone narrowing (`not_required < required`), an existing enforcement boundary (`validate_extensions` at decision and execute), and binding through the existing profile commitment are all established. No protected evaluator, approval preimage, persisted-decision field or authority semantics change. Self-inflicted denial (a Registry `required` over a host with no inventory) is fail-closed and is the intended meaning of the requirement; it is documented, tested, and not repaired.
