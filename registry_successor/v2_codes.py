"""Closed refusal-code set `CODES_V2` for contract `r08-v2` (docs/r08-v2-contract.md section 3.3; ADR EXT-S1-1 D-02).

`CODES_V2` is the 46 `r08-v1` codes (same layers and meanings, taken from `common.CODES` so there is one definition) plus
exactly two additions. It is DECLARED here by EXT-S1-2 and nothing reaches the new codes yet:

  trust_snapshot_version_stale  layer `trust`        reached only by the snapshot-version floor (a later package).
  selection_withdrawn           layer `disposition`  reached only by the v2 disposition layer (a later package).

`common.CODES` (46) is not modified and no `r08-v1` entry point can emit a v2-only code. Read-only: a code is added by a
contract change, never at run time. Non-authorizing and unqualified.
"""
from types import MappingProxyType

from registry_successor import common as c

V2_ADDED_CODES = {
    "trust_snapshot_version_stale": ("trust", "snapshot version is below the supplied floor, or equals it with a different fingerprint"),
    "selection_withdrawn": ("disposition", "an authenticated withdrawal is the head statement for this scope"),
}

CODES_V2 = MappingProxyType({**c.CODES, **V2_ADDED_CODES})
