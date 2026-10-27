# Independent-review handover (V07 security and V08 Tier 1)

Non-authorizing. Nothing in this repository designates an independent reviewer. Until the Architect does so, V07 and V08 independent gates stay OPEN.

## What the reviewer receives
- Exact pins: `candidate-manifest.json` (four `main` SHAs plus the Constitution pin). Pin the SHAs; do not resolve branch names.
- Contracts: Registry `docs/r08-v2-contract.md` and Amendments 1-4, ADR EXT-S4-0, `docs/f-a1-authorization-pin/`.
- Retained historical evidence, including failures: Stack Qualification `results/v06-e2e/`, `results/v07-security/` (historical and requalification), `results/v08-fa1/`, and #235 `7b72de9a` for the F-A1 BREACH and original failed gate.
- Registers: `limitations-and-exclusions.md`, `gate-matrix.md`.

## Scope the reviewer should cover (from Plan v1.5)
V07: Ed25519 and canonical base64, binding, Runtime atomicity and restore, the authorization pin (installer custody, fences, anchor). V08: Tier 1 scenarios with an independent oracle written from the contracts, not from the builder's harness.

## Reproducing the builder-side checks (no test campaign needed to start)
1. Clone the four repositories at the manifest SHAs.
2. `python tools/verify_v09_candidate.py --components-dir <dir containing the four clones>` checks that each commit exists, is the declared merge, has the declared tree, and that every blob and sha256 in the manifest matches. It performs no network access and executes no component code.
3. Registry: `pip install --require-hashes -r requirements-s01.lock.txt && python -m pytest` (hash-locked). Runtime pin tests need `OCS_REGISTRY_PIN_DIR` set to the Registry clone. Stack Qualification F-A1: see `.github/workflows/tier1-v08-fa1.yml` (runs as root with `useradd`/`setpriv`; no root means SKIP, which is INCONCLUSIVE, never PASS).
4. Re-pin the F-A1 harness to the `main` SHAs rather than the PR-head SHAs recorded in `conftest.py` (inventory section 2 explains the tree equivalence).

## Independence requirements the builder cannot satisfy
Independent human reviewer(s) designated by the Architect; an oracle and inventory frozen before they see the builder's results; scoped written verdict with negative evidence at exact pins. AI sessions, separate or not, and CI do not count (Constitution `ADOPTION.md` at `1c2e920f`).

## Questions to put to the reviewer first
FA1-12 propagation delay; anchor custody and the consistent-restore limit (L-08); single-process installer; the claim_json lock-time authentication gap (L-05); whether Amendment 4's stricter crash-state-E HOLD should be accepted as an interpretation.

## Standing holds
V09 acceptance NOT AUTHORIZED. Independent V07: OPEN. Independent V08: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release, publication, production: HOLD.
