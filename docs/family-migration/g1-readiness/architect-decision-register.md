# Architect decision register (Phase E)

Non-authorizing, documentation only. No oracle is implemented, executed or independent; nothing here is qualified or certified. Release, publication and production are not authorized.

G0: ACCEPTED AND FROZEN. G1: PREPARATION ONLY. G1 CONTRACT/ORACLE IMPLEMENTATION: NOT AUTHORIZED. G2–G5: NOT AUTHORIZED. V09 independent V07 review: OPEN. V09 independent V08 Tier 1: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

Distinction used: **FINAL** = the Architect's disposition in the 2026-10-27 directive, applied as stated. **PROVISIONAL** = a preferred direction or a prepared characterisation; not ratified. **PENDING** = no decision. **PREPARED FOR DECISION** = the builder supplies an evidence-based determination for the Architect to confirm.

| Id | Subject | Status | Disposition (directive) | Consequence recorded here | Oracle effect |
|---|---|---|---|---|---|
| PD-1 | Scope and payload relationship | FINAL (interim rule) | Preserve current scope/payload independence until a separate binding contract is approved. | No oracle may assert that allowed_institutions / allowed_authority_domains must contain, equal or exclude scope.institution / scope.authority_domain. The relation itself is NOT ratified. | E-12, E-33, E-34, F-08, F-09, F-14, F-30 are BLOCKED-SEMANTICS; they report BLOCK. |
| PD-2 | REFUSE/HOLD and reason semantics | FINAL | Preserve the committed REFUSE/HOLD classes and reason semantics; do not adopt the unratified outcome map (`ld02-outcome-map.json`). | Amendment 3's use of policy_identity_mismatch for containment is recorded as committed behaviour, not as a ratified mapping. | E-22, E-23, E-25, E-29 are CHARACTERISATION-ONLY. |
| PD-3 | Token rule: contract text versus code | PROVISIONAL (characterised; correction proposed, not applied) | Characterise the stricter current token validation; prepare a proposed documentation correction, not a behaviour change. | Contract section 2 (line 28) and Amendment 1 5.1(3) say 'no control, separator or `*` characters'. Code `registry_successor/common.py: valid_token` refuses every code point whose Unicode general category starts with C or Z, or `*`, and the frozen effective-policy-identity spec 6.1 (N-13) fixes a version-pinned table. Cf, Cs, Co and Cn are refused by code and table but are not 'control' or 'separator' in the contract wording. | E-04 CHARACTERISATION-ONLY. E-01 remains SPEC-READY with expected values taken from the N-13 table, not from contract prose. Proposed correction text is in section 3 below. |
| PD-4 | Amendment 4 status | FINAL | Amendment 4 remains DRAFT; no independently qualified pin-path closure claim. | Every pin-path oracle is DRAFT-DEPENDENT; results are labelled so. | E-35 CLAIM-CHECK; E-33, E-34, F-10, F-29, F-30 flagged DRAFT-DEPENDENT. |
| PD-5 | Registry pin for cross-repository assertions | PREPARED FOR DECISION (determination from the complete delta; not decided) | Determine suitability from the complete source delta. | Registry code is byte-identical across `943ab18`, `a1169a05`, `1a4de326`, `317eb76a` and main; pin suitability is therefore a question of document baseline and of one hard-coded commit-identity assertion (registry-pin-delta-assessment.md section 7). | No historical pin is replaced. |
| PD-6 | Independent oracle author and reviewer | PENDING (no designation) | Designation remains pending; no AI worker is assigned to an independent role. | AI workers, the Lead Builder and CI are never independent assessors. | Every oracle has authored_by = null and independent_author_designated = false. |
| PD-7 | Oracle home | PROVISIONAL (preferred direction) | Preferred home: a separately versioned package under Stack Qualification. | Not ratified; no package is created. | Spec carries the provisional placement in each oracle's preconditions. |
| PD-8 | Successor contract approach | PROVISIONAL (preferred direction) | Option B (one versioned successor contract) preferred; no contract drafting or implementation authorized. | Design direction only. | No contract text in this package. |
| PD-9 | Equality versus subset (G0 AD-06) | PROVISIONAL (source-enforced behaviour characterised; ratification pending) | Characterise source-enforced subset behaviour; contract ratification pending. | Amendment 3 and the engine enforce executor SUBSET-OF record (equal allowed). Equality of executor set and record is not required by any text. | F-06, E-21 carry the restriction in the specification. |
| PD-10 | G0 erratum | FINAL | Accepted as an additive correction; frozen G0 evidence unchanged. | `g1-preparation/g0-erratum.md` (EG-1 to EG-5) stands as additive text. | G0 evidence blobs unchanged (integrity test). |

## 3. PD-3: proposed documentation correction (NOT applied; frozen contract files are not edited)

Proposed additive note for a future amendment or erratum, to be adopted only by the Architect:

> In `r08-v2` section 2 and Amendment 1 5.1(3), "no control, separator or `*` characters" is to be read as: a token is refused if it contains `*` or any code point whose Unicode general category begins with `C` (Cc, Cf, Cs, Co, Cn) or `Z` (Zs, Zl, Zp), as fixed by the version-pinned membership table of the effective-policy-identity specification section 6.1 (N-13). The Registry validators implement this reading.

Evidence: `registry_successor/common.py` `valid_token` rejects category initial `C` or `Z` and `*`; contract line 28 and Amendment 1 line 224 use the shorter wording. No behaviour changes.

## 4. Open decisions that remain with the Architect

PD-5 confirmation; PD-6 designation; ratification of PD-3, PD-7, PD-8 and PD-9; the separate binding contract that would settle the PD-1 relation; the corrected Phase B end SHA; the profile choice per suite (environment-profile.md E-06); AD-04 to AD-24 from G0 remain as recorded in `g1-preparation/g0-freeze-record.md`.
