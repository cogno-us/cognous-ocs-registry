# Typed eight-field assignment packets (schema-validated; NOT dispatched)

Each `*.assignment.json` validates against `schemas/orchestrator-assignment-v1.schema.json` at constitution `dcdbe3b76843d672ca3cfb1f000124ecd78ed03c` (Draft 2020-12; `build_assignments.py` extracts every clause cell programmatically from `ENGINEERING_COMPLIANCE_ADDENDUM.md` at that revision and validates before writing; it expects a local checkout of the constitution).

| Packet | Archetype / role / tier | Status |
|---|---|---|
| `R1-NEXT.assignment.json` | A / implementation_owner / T0 | the assignment record for OCS-REG-R1-NEXT (this work package) |
| `F3-A.assignment.json` | D / independent_qualification_owner / T4 | **READY FOR ASSIGNMENT / OWNER BLOCKED**: no independent owner designated; F3 execution not authorized |
| `F3-B.assignment.json` | D / independent_qualification_owner / T4 | **READY FOR ASSIGNMENT / OWNER BLOCKED** |

The packets contain no verdict and authorize nothing. `projectAdoption.status` is `CONFLICT` on purpose: OCS records pin different constitutional revisions and no formal adoption of `dcdbe3b…` was found (Architect decision D7).
