"""One parameterised contract engine for the registry successor contracts (docs/r08-v7-contract.md section 3).

The engine implements record validation, selection parsing, the signing input, layered verification, the decision step and effective-policy identity
ONCE, as functions of an immutable `profile.ContractProfile`. Two profiles are shipped (`profiles.V7`, the unified successor with one family, and
`profiles.V6_COMPAT`, the exact frozen `r08-v6` constants, built from the existing v6 family specs). The frozen `v1`..`v6` modules are not edited and do
not import this package. Non-authorizing; BUILDER_TESTED, not independently qualified.
"""
