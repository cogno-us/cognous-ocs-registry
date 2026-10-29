# Crosswalk update: the final three parameters (2026-10-29)

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (independent Tier 1 qualification DEFERRED, NOT WAIVED). Governing: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (`ADOPTION.md`), Static Plan v1.1 s.12, Engineering Plan v1.5, audit #60, #65/#67, target architecture #68, architecture v1.1 and decision evidence #72. Baselines: Registry `main` `67512a71546748cd888e4cf790485ea0bef9199a` (#71 `04302e0334e8d9c8ad942be7ee9d9083d1163976`, #72 `67512a71546748cd888e4cf790485ea0bef9199a`); Control Plane `main` `b7eb11aaeed9c766ecaae7d22955093f7f7cd1aa` (#93). Supersedes only rows 17-19 and the accounting lines of `../unified/01-...` and `../unified/09-...` (those files stay as written).

| # | Catalogue id | Owner / consumer | Binding today | Registry family (proposed, not registered on main) | State |
|---|---|---|---|---|---|
| 17 | P-RG-C-020-anchor_deadline_to_inputs | `FreshnessProfile` (freshness.py:72); deadline collector bounded.py:2105; purpose observation runtime_authority.py:404-413 | profile commitment (flag is dumped while true) | `f5-anchor-deadline-to-inputs-policy` | BLOCKED: purpose-observation 2x residual reproduced; needs D-07 |
| 18 | P-RG-F4-OBS-max_age_seconds | `ObservationPolicy` bounded.py:414, check :1925 | **none** (constructor-only; recorded as evidence in `ReconciliationResult`) | `f5-observation-max-age-policy` | BLOCKED: needs D-06 |
| 19 | P-RG-F4-OBS-clock_tolerance_seconds | `ObservationPolicy` bounded.py:415, check :1922-1924 | **none** | `f5-observation-clock-tolerance-policy` | BLOCKED: needs D-06 and AR-1 |

Accounting: 16/19 integrated (rows 1-16 merged), 3 remaining, 0 independently accepted. Unchanged. The held constructor tolerance (`P-RG-C-006-clock_tolerance_seconds`, Registry #58/#59, Control Plane #87) is a different parameter and remains NOT AUTHORIZED.
