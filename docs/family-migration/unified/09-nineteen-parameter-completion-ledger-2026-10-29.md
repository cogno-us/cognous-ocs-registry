# 19-parameter completion ledger (2026-10-29)

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (DEFERRED, NOT WAIVED). Governing: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`, Static Plan v1.1 s.12, Engineering Plan v1.5, audit #60, #65/#67, architecture v1.0 (#68, `d7eb6be`). Axes are kept separate. Open PRs are NOT counted as merged and developer tests are NOT independent acceptance.

| Axis | Count | Detail |
|---|---|---|
| Eligible (audit) | 19 | catalogue `manageable_parameters` |
| Consumer-integrated AND merged | **13** | rows 1-13 of the crosswalk (unchanged since #91/#67) |
| Implemented on open PRs, enforcement not merged | 3 | row 14 requires_revocation_assurance and row 15 terminal revocation (Registry #69 / CP #92); row 16 ActionClass.irreversible (Registry #71 / CP #93) |
| BLOCKED by decision record | 3 | row 17 anchor_deadline_to_inputs; rows 18, 19 ObservationPolicy max_age_seconds, clock_tolerance_seconds |
| Independently accepted | **0** | Tier 1 DEFERRED, NOT WAIVED |

## Accounting
| State | Integrated | Remaining |
|---|---|---|
| Actual today | 13/19 | 6 |
| Conditional: #69 + #92 merge | 15/19 | 4 |
| Conditional: also #71 + #93 merge | **16/19** | **3** (all BLOCKED pending Architect decisions D-06 / D-07 / AR-1) |

The three blocked parameters have NO Registry family, no placeholder and no claim. The four directive parameters resolved as: irreversible implemented; anchor and both ObservationPolicy fields blocked, with exact reasons and options in `07-commitment-binding-decisions-2026-10-29.md`.

## Holds (unchanged)
Registry #58/#59 and Control Plane #87: HELD. Constructor clock tolerance: NOT AUTHORIZED. Independent Tier 1 qualification: DEFERRED, NOT WAIVED. V09 assurance: SEPARATE. Ed25519 #26/#34: SECURITY-HELD. Release, publication, production: HOLD.
