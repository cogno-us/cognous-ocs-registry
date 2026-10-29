# Revocation families: consolidated accounting and status (2026-10-28)

Status: documentation only; non-authorizing. Governing documents: Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`, Static Plan v1.1, Engineering Plan v1.5, audit #60, #65, #67.

## Baselines
Control Plane `main` `4780abe0af54147c0770e98cb7b964b74b2008c4`; Registry `main` `e8b572cc669bee668abc88846f7b071a74f13440`.

## Open PRs (none merged)
| PR | Head | CI at head |
|---|---|---|
| Registry #69 | `42a666328b974a7581013358bcf8bc7b9eac7761` | see PR checks |
| Control Plane #92 | `a62ca8d8e4088c95407c2000dcca081383d8dd4d` | test 3.11, test 3.12, manifest-validator-parity passed (push) |

## Results
- Registry v6 tests 543 passed; whole suite 1 failed / 8019 passed / 2 skipped vs main 1 failed / 7476 passed / 2 skipped (same failure on both, ed25519 lock check).
- Control Plane full suite, Python 3.11 and 3.12: branch 1359 passed / 102 skipped; main 1359 passed / 101 skipped. The extra skip is the new `PIN_V6` check in `test_f5_class_unreadable_governance.py`, run under pin by CI with a no-skip gate (>= 388 tests).
- Mutations: Registry 80 mutants / 79 killed (TR14 equivalent); Control Plane 50 mutants / 49 killed (A07 equivalent).

## Accounting
| State | Integrated | Remaining | Independently accepted |
|---|---|---|---|
| Actual today | 13/19 | 6 | 0 |
| Conditional, both enforcement PRs merged | 15/19 | 4 | 0 |

Open PRs are not counted. Each parameter counts only when its enforcement implementation is merged.

## Holds
Registry #58/#59 and Control Plane #87: HELD. Constructor clock tolerance: NOT AUTHORIZED. Other four parameters: NOT AUTHORIZED. Independent Tier 1 qualification: DEFERRED, NOT WAIVED. V09 assurance: SEPARATE. Ed25519 #26/#34: SECURITY-HELD. Release, publication, production: HOLD.
