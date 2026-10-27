# G0 source baseline (2026-10-27)

Non-authorizing, builder-side, read-only inventory. G0: AUTHORIZED. G1–G5: NOT AUTHORIZED. V09 independent qualification: OPEN. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

## 1. Current main of every examined repository

Resolved from each repository's default branch on 2026-10-27 before any worker started; historical commits are never used as current.

| Repository | Exact main SHA |
|---|---|
| cogno-us/cognous-ocs-registry | 317eb76acb2847c534c3ce7c2180b89b4aef987d |
| cogno-us/cognous-control-plane | d66ae07fa240510efdcc11ed4b3e1189dcefc822 |
| cogno-us/cognous-execution-runtime | 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491 |
| cogno-us/cognous-stack-qualification | bb9b08904192b5f50a49e00ed8de0cab80fd7c19 |

Registry baseline for this PR: `317eb76acb2847c534c3ce7c2180b89b4aef987d` (merge of PR #49, the approved static migration plan v1.0). The G0 branch is cut from that commit.

Repositories inspected by Worker D (anonymous shallow clones, one at a time; SHAs recorded by the worker from the clone):

| Repository | HEAD at clone | Relevant | Clone |
|---|---|---|---|
| cogno-us/cognous-action-manifest | fa170815ef96a54c233d0dd9da821b60debabf8b | YES | OK (shallow, /home/claude/g0/src/other/c |
| cogno-us/cognous-agent-control-plane (= cognous-control-plane, renamed) | d66ae07fa240510efdcc11ed4b3e1189dcefc822 | YES, but owned by worker C (not re-inventoried; HEAD equals /home/claude/g0/src/control_plane) | OK; redirects to the Control Plane check |
| cogno-us/cognous-open-control-stack (hub) | 51c579a3208149922649a31a6eb041106a4121c3 | YES (partly) | OK (shallow) |
| cogno-us/cognous-open-control-stack-verifier | 39d46b494558e271439966bec98b26dc4d040cc4 | CONTRACT-COUPLED ONLY | OK (shallow) |
| cogno-us/cognous-governance-evidence-pack | 7b9511f2c6d56d424f17b078826594abd29f6c96 | CONTRACT-COUPLED (producer revision pins; freshness/0.1 reimplementation) | OK (shallow) |
| cogno-us/cognous-replay-bundle (= cognous-agent-replay-bundle, renamed) | 40012b8c174c6f25685bd5d9bc93ff46cc9a5842 | CONTRACT-COUPLED | OK; cognous-agent-replay-bundle clone re |
| cogno-us/cognous-governed-exchange | 7f7569b02666b99669a9fca61117ca1f4bce5f0d | MARGINAL | OK (shallow) |
| cogno-us/open-decision-evidence-standard (ODES) | 1a5e1d300250d832e611633f0bf8f762e398c0ec | CONTRACT-COUPLED (normative shapes, almost no values) | OK (shallow) |
| cogno-us/cognous-evidence-registry (the_index) | b2485998b88256c2b322493800d1fba076814cbd | NO | OK (shallow) |
| cogno-us/cognous-evidence-attestation (BitRep) | 981036c315856c71207984797b0c4e48d3b3921d | NO | OK (shallow) |
| cogno-us/cognous-institutional-governance (Alvorada display alias) | 03a90c14c4a178997df2b6e527f67452b9c6bb7a | YES (contract + one value table) | OK (shallow) |
| cogno-us/moltbot-safe (= cognous-execution-runtime, renamed) | 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491 | YES, owned by worker B (not re-inventoried) | OK; resolves to the identical Runtime HE |
| cogno-us/cognous-stack-qualification (checked out) | bb9b08904192b5f50a49e00ed8de0cab80fd7c19 | PARTLY (pins, harness thresholds) | existing checkout |
| cogno-us/cognous-engineering-constitution | a4dd11115e47e27e8f0731a622fe950f7fbf2fc2 (checkout HEAD); plan pin 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b also present as an object | NORMATIVE | existing checkout /home/claude/cogno-us/ |

Renames resolve to the same HEAD as the primary repositories: `cognous-agent-control-plane` = Control Plane, `cognous-agent-replay-bundle` = Replay Bundle, `moltbot-safe` = Runtime. `cognous-evidence-registry` and `cognous-evidence-attestation` were judged not relevant from README and a literal grep only; they were **not audited**.

## 2. Historical pins used only for the S02 old-to-current crosswalk

| Component | S02 pin | Current main |
|---|---|---|
| Runtime | `ec728da6dc301a664b331ac8986afd6e850a1273` | `0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491` |
| Control Plane | `0a41faa972699f7ec3063967a14cd9bdd3e67d27` | `d66ae07fa240510efdcc11ed4b3e1189dcefc822` |

Source churn since the S02 pins (git diff --name-status): Control Plane `src/` 5 files (3 new: `authorization_pin_export.py`, `canonical_policy_binding.py`, `policy_binding.py`; 2 modified: `local_authority_effect.py`, `runtime_authority.py`); Runtime `engine/` + `host/` 9 files (new: `authorization_pin.py`, `authorization_pin_format.py`, `registry_f1a_narrowing.py`, `registry_selection_authority.py`, `host/authorization_pin/*`; modified: `local_authority_effect.py`, `atomic_local_control_plane_executor.py`). `bounded.py` is byte-identical to the S02 pin.

## 3. Pins deliberately NOT moved

- V09 candidate manifest `docs/v09/candidate-manifest.json` is unchanged (candidate pins: Registry baseline `1a4de326…`, Control Plane `d66ae07f…`, Runtime `b5605f52…`, Stack Qualification `bb9b0890…`). The Runtime main has since advanced to `0dde0ef7…` (merge of Runtime PR #150, the F3 acceptance record); that is recorded here as the current main and does not amend the V09 candidate.
- Constitution: pin `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (ADOPTION.md). The Constitution repository main is `a4dd1111…`; it is **not adopted**. Tier numbering is inverted between the pin and that HEAD (the pin has Tier 1 as critical); every tier in this G0 package uses the pin meaning (decision AD-15).
- Pinned reusable workflow SHAs in `.github/workflows/` are unchanged.

## 4. Method and limits

Four read-only workers (A Registry, B Runtime, C Control Plane, D other repositories and cross-component delta) inspected non-overlapping source in read-only checkouts; the lead reconciled. Workers cited test names but **executed no tests**. Not-read areas are listed in each `evidence/worker-*/notes.md`. In short: test bodies, golden vectors, most of `bounded.py` outside the consumers of policy values, hub docs/scenarios/fixtures, replay-bundle and evidence-pack validators, ODES RFCs, and most of Stack Qualification were grepped or sampled, not read.
