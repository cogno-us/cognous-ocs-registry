# Crosswalk rows 17-19 after implementation (supersedes the BLOCKED status of `01-crosswalk-update-...`)

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified. Nothing is merged. Independent Tier 1 qualification DEFERRED, NOT WAIVED. Appended as new text; `01-...` stays as written.

| # | Parameter | Registry family (r08-v8, PR #77 head a40fe755e2384a99c37016fa9ad59396f1835900) | Control Plane enforcement | Status |
|---|---|---|---|---|
| 17 | P-RG-C-020-anchor_deadline_to_inputs | `f5-anchor-deadline-to-inputs-policy` | D-07 correction CP #95 (b8fbe957f0e7b93b64679ebda03acfc11660f1d7, predecessor evidence #94 061a986563768f2f8f9f6c0861647a3c5b1935be) + consumer CP #97 (a1de48c04b051899dc051d205246e5084501fb1d) | IMPLEMENTED, UNMERGED, NOT INDEPENDENTLY QUALIFIED (F3-B pending) |
| 18 | P-RG-F4-OBS-max_age_seconds | `f5-observation-max-age-policy` | D-06 binding CP #96 (4adb84b92edce7aea8e38ab1defa4668586503d8) + consumer CP #97 | IMPLEMENTED, UNMERGED, NOT INDEPENDENTLY QUALIFIED (F3-A pending) |
| 19 | P-RG-F4-OBS-clock_tolerance_seconds | `f5-observation-clock-tolerance-policy` (AR-1: distinct from the held constructor tolerance) | D-06 binding CP #96 + consumer CP #97 | IMPLEMENTED, UNMERGED, NOT INDEPENDENTLY QUALIFIED (F3-A pending) |

Accounting: 16/19 integrated (rows 1-16 merged). Rows 17-19 become integrated only when #75, #77, CP #94, #95, #96 and #97 are merged by the Architect in dependency order; independently accepted: 0. Do not claim 19/19 before that.

Known limits carried: DEF-OBS-TOL-OVERFLOW-1 (`04-...`) is unfixed and needs its own decision; binding has no anti-rollback and legacy_cutoff has no durable provenance (hold retained); a host change fully masked by a narrower Registry value is not refused; the anchor guarantee depends on D-07; Registry CI pin on CP #97 targets the unmerged #77 head.

Holds unchanged: Registry #58/#59 HELD; Control Plane #87 HELD; constructor tolerance NOT AUTHORIZED; Ed25519 #26/#34 HELD; V09 SEPARATE; publication, release, production HOLD.
