# Independent Registry eligibility audit (2026-10-28)

Question: of all distinct Cognous OCS rules, how many can legitimately be managed through the Registry, how many already are, and how many remain?

This is an independent architecture/eligibility audit. It is NOT independent Tier 1 qualification, and it does not claim exhaustive coverage (see the coverage limits in `reconciliation-report.md` §7).

- Release: HOLD
- Publication: HOLD
- Production: HOLD

This audit does not modify production code, the frozen G0/S02 evidence, the active migration backlog or plan, or any builder PR. The audit PR is not to be merged automatically.

## Pass 2 (correction pass, 2026-10-28)

PR #60 was amended, not replaced. Pass 2 added parameter-level accounting (`parameter-catalogue.json`, `parameter-reconciliation.md`), resolved the DR-CP-AGE-1 / AD-07 decision reconciliation (`unresolved-architectural-decisions.md` §1b), re-examined the ten largest eligibility disagreements, closed part of the source-coverage gap, and subjected the lead's ledgers to an independent reconciliation worker. Raw pass-2 worker outputs are in `worker-evidence/pass2/` and `worker-evidence/I4.json`; the lead's rulings on them are in `lead-adjudications.json` (`pass2_resolutions`, `pass2_h_resolutions`). The pass-1 worker evidence, the 620-row crosswalk and the source pins are unchanged.

Regenerate in order: `python3 -I tools/reconcile.py && python3 -I tools/build_parameters.py && python3 -I tools/render_reports.py` (each accepts `--check`).

Notes on fields: `parameter_count` in `rule-catalogue.json` counts Registry-manageable parameters only and `configurable` is the pass-1 rule-level flag; for denominators use `parameter-catalogue.json`.

## Contents

| File | Purpose |
|---|---|
| `parameter-catalogue.json`, `parameter-reconciliation.md` | Parameter ledger and its reconciliation to rules, G0 groups and historical sites |
| `reconciliation-report.md` | Numerical reconciliation, counting rules, G0 movement, coverage limits |
| `crosswalk.json` | All 620 historical rows, each mapped to one canonical rule and one disposition |
| `rule-catalogue.json` | Canonical logical-rule catalogue |
| `source-site-map.json` | Current source-site mapping |
| `eligibility-decisions.md` | Registry eligibility decisions and reasons |
| `merge-and-split-explanations.md` | Duplicate, merge and split explanations |
| `omitted-rule-groups.md` | Rule groups absent from the 97-group G0 inventory |
| `unresolved-architectural-decisions.md` | Open owner decisions and observations |
| `proposed-backlog-additions.md` | Recommended backlog additions (proposals only) |
| `worker-cross-check-results.md` | Worker evidence and independent cross-check results |
| `worker-evidence/` | Raw worker outputs and shard inputs |
| `lead-adjudications.json` | Every lead override, merge, split and cross-check resolution, with reasons |
| `frozen-blob-pins.json` | Git blob ids of the frozen G0/S02 files |
| `tools/` | `reconcile.py` and `render_reports.py` (deterministic; `--check` recomputes) |

Integrity test: `tests/test_audit_registry_eligibility_integrity.py`.

## Method

Eligibility test used to separate the dispositions: REGISTRY-ELIGIBLE means a strictness-only, one-way change that only adds refusals, with a defined consumer and a design gate (for example the approval_commitment coupling). BLOCKED means an accepted decision or missing authorization stands in the way even though the shape is monotone. A selection among protocol profiles that changes semantics (for example operation-identity enablement) is not a narrowing and is not eligible.


Eight mutually exclusive dispositions: REGISTRY-GOVERNED, REGISTRY-ELIGIBLE, RETAIN-IN-CODE, CALLER-OR-ISSUER-OWNED, PROVIDER-OR-HOST-OWNED, OUT-OF-SCOPE, UNRESOLVED, BLOCKED. A rule is REGISTRY-GOVERNED only if it is implemented and integrated at an enforcement boundary; represented-only rules stay ELIGIBLE. Nothing is counted as independently accepted. Units (rule group, source site, configuration parameter) are kept separate.

Workers produced first-pass classifications; the lead reconciled them, and independent blind re-audit and falsification workers cross-checked them. Disagreements are recorded, not hidden.

Regenerate: `python3 -I tools/reconcile.py && python3 -I tools/render_reports.py`.
