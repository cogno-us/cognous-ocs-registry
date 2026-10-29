# Parameter-to-source and consumer crosswalk: all 19 (2026-10-29)

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (DEFERRED, NOT WAIVED). Governing: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`, Static Plan v1.1 s.12, Engineering Plan v1.5, audit #60, #65/#67, architecture v1.0 (#68, `d7eb6be`). Parameter ids and source pins are the audit catalogue's (`docs/audit/registry-eligibility-2026-10-28/parameter-catalogue.json`). Merge state is as of Registry `main` `d7eb6be` and Control Plane `main` `4780abe`. "Integrated" means enforcement merged; open PRs are NOT counted.

| # | Catalogue id | Owner / consumer (source) | Registry contract / family | Narrowing | Binding | State |
|---|---|---|---|---|---|---|
| 1 | P-RG-F1A-allowed_actions | Runtime `engine/safe_executor.py:363` | r08-v2 f1ab (also v3, v4) | intersection | Runtime effective policy | integrated (merged) |
| 2 | P-RG-F1A-allowed_adapters | `safe_executor.py:362` | r08-v2 f1ab | intersection | same | integrated |
| 3 | P-RG-F1A-allowed_units | `safe_executor.py:365` | r08-v2 f1ab | intersection | same | integrated |
| 4 | P-RG-F1A-allowed_institutions | `safe_executor.py:360` | r08-v2 f1ab | intersection | same | integrated |
| 5 | P-RG-F1A-allowed_authority_domains | `safe_executor.py:361` | r08-v2 f1ab | intersection | same | integrated |
| 6 | P-RG-F1C-MAX-AMOUNT-max_amount | `safe_executor.py:366` | r08-v3 f1abc (v4) | numeric minimum | same | integrated |
| 7 | P-RG-F1C-MAX-EFFECTS-max_effects | `safe_executor.py:367` | r08-v3 f1abc (v4) | numeric minimum | same | integrated |
| 8 | P-RG-F1D-TARGET-PREFIXES-allowed_target_prefixes | `safe_executor.py:364` | r08-v4 f1abcd | joint containment | same | integrated |
| 9 | P-RG-F1D-TARGET-MATCH-target_match | `safe_executor.py:372` | r08-v4 f1abcd | joint containment | same | integrated |
| 10 | P-LR-F4-status_max_age_seconds | CP `bounded.py:1271,1295` | r08-v2 f4 | minimum | **workflow-local (D-06 open)** | integrated (binding limit recorded) |
| 11 | P-LR-F4-approval_max_age_seconds | CP `bounded.py:1274,1298` | r08-v2 f4 | minimum | **workflow-local (D-06 open)** | integrated (binding limit recorded) |
| 12 | P-LR-F5-class_max_status_age_seconds | CP `runtime_authority.py:131` | r08-v2 f5 | per-class minimum | profile commitment | integrated |
| 13 | P-RG-C-009-on_unreadable | CP `runtime_authority.py:132` | r08-v5 f5 | bounded_tolerance to refuse | profile commitment | integrated |
| 14 | P-RG-C-010-requires_revocation_assurance | CP `runtime_authority.py:135`, `holder_inventory.py` | r08-v6 (open #69/#92) | false to true | profile commitment | OPEN PRs, not merged |
| 15 | P-RG-C-TERMINAL-REVOCATION-enabled | CP `runtime_authority.py:182-191`, `bounded.py` recorded-grant denial | r08-v6 (open #69/#92) | off to on | profile commitment | OPEN PRs, not merged |
| 16 | P-RG-C-011-reversibility (`ActionClass.irreversible`) | CP `runtime_authority.py:130`, `bounded.py:2111,2189`, `reversibility.py` | r08-v7 irreversibility (proposed) | false to true, never repaired | profile commitment | IMPLEMENTED on open branches (pending PRs) |
| 17 | P-RG-C-020-anchor_deadline_to_inputs | CP `freshness.py:72`; `bounded.py` deadline collector | none | false to true | profile commitment | **BLOCKED** (purpose-observation residual, D-07) |
| 18 | P-RG-F4-OBS-max_age_seconds | CP `bounded.py:411-415`, `:1925` | none | minimum | **none: constructor-only (D-06)** | **BLOCKED** |
| 19 | P-RG-F4-OBS-clock_tolerance_seconds | CP `bounded.py:411-415`, `:1920-1924` | none | minimum | **none: constructor-only (D-06, AR-1)** | **BLOCKED** |

Rows 8 and 9 are one jointly narrowable unit but two counted parameters. Not conflated: constructor clock tolerance (catalogue `P-RG-C-006-clock_tolerance_seconds`, f4t, Registry #58 / Control Plane #87) stays HELD and NOT AUTHORIZED; `P-RG-C-005-identity_max_age_seconds` and `P-RG-C-005-mandate_max_age_seconds` are BLOCKED outside the 19.

## Ledger (separate axes)
Eligible 19; consumer-integrated and merged 13 (rows 1-13); rows 14-16 implemented on OPEN PRs only (not counted); rows 17-19 BLOCKED; independently accepted 0. Rows 10-11 are merged but carry the recorded workflow-local binding limit (D-06).
