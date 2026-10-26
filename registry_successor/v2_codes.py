"""Closed refusal-code set `CODES_V2` for contract `r08-v2` (docs/r08-v2-contract.md section 3.3; ADR EXT-S1-1 D-02).

`CODES_V2` is the 46 `r08-v1` codes (same layers and meanings, taken from `common.CODES` so there is one definition) plus
exactly two additions. It is DECLARED here by EXT-S1-2 and nothing reaches the new codes yet:

  trust_snapshot_version_stale  layer `trust`        reached only by the snapshot-version floor (a later package).
  selection_withdrawn           layer `disposition`  reached only by the v2 disposition layer (a later package).

`common.CODES` (46) is not modified and no `r08-v1` entry point can emit a v2-only code. Read-only: a code is added by a
contract change, never at run time. Non-authorizing and unqualified.

Revision 2 of this ONE vocabulary (`r08-v2-reasons/2`, symbol `CODES_V2_REV2`; docs/r08-v2-contract-amendment-1.md section 6.4, Architect Batch 6
ruling 4.7) is `CODES_V2` (revision 1, 48 codes, unchanged and still pinned) followed by exactly three additive codes, in this order:

  not_activated              layer `selection`  REFUSE               known store, no row for the scope key.
  policy_identity_mismatch   layer `identity`   REFUSE               a claim identity member differs from the durable row (stale epoch is `selection_epoch_stale`).
  store_unknown              layer `trust`      UNKNOWN_FAIL_CLOSED  the authoritative durable state is unavailable or indeterminate (HOLD; never an optional fallback).

`r08-v2-reasons/2` is documentary only: `contract_version` stays exactly `r08-v2` and no dispatch is keyed on the revision. No `r08-v1` or
revision-1 entry point can emit a revision-2 code; the revision-2 codes are reached only through the explicit revision-2 paths.
"""
from types import MappingProxyType

from registry_successor import common as c

V2_ADDED_CODES = {
    "trust_snapshot_version_stale": ("trust", "snapshot version is below the supplied floor, or equals it with a different fingerprint"),
    "selection_withdrawn": ("disposition", "an authenticated withdrawal is the head statement for this scope"),
}

CODES_V2 = MappingProxyType({**c.CODES, **V2_ADDED_CODES})

REV2_ADDED_CODES = {
    "not_activated": ("selection", "the enforcing component's known authoritative durable state has no row for the scope key"),
    "policy_identity_mismatch": ("identity", "a claim-carried identity member differs from the authoritative durable activation row"),
    "store_unknown": ("trust", "the enforcing component's authoritative durable state is unavailable, lost, torn, rolled back or otherwise indeterminate"),
}

CODES_V2_REV2 = MappingProxyType({**CODES_V2, **REV2_ADDED_CODES})
