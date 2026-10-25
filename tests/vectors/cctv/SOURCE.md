# Vendored C2SP CCTV Ed25519 edge-case vectors

- File: `ed25519vectors.json`, copied byte-for-byte (no modification) from
  `https://raw.githubusercontent.com/C2SP/CCTV/main/ed25519/ed25519vectors.json` (HTTP 200).
- `UPSTREAM-README.md` is the unmodified `ed25519/README.md` from the same directory (flag definitions).
- Retrieved: 2026-10-25, branch `main`. **No upstream commit id is recorded**: the GitHub API was not reachable from the
  build environment (HTTP 403), so the commit that served the file could not be resolved. The sha256 below identifies exactly
  what was tested; a later re-fetch that differs must be reviewed, not silently accepted.
- sha256 of `ed25519vectors.json`: `b38e84caf3e7e89170ff520292dbeae421b0a794c27408ce5ce973018fe3d7f9` (351077 bytes, 914 vectors).
  sha256 of `UPSTREAM-README.md`: `12889cbe441ce9da56fc65aa00b9d16f02ecdbcb8bb19d706ac35e92380d93d0`.
  Both are checked by `tests/test_adapter_ed25519_cctv.py`.
- **License: not established.** No LICENSE file exists at the top level of the upstream repository's default branch (several
  common names returned HTTP 404), and none was vendored. The file is used only as untrusted test data. The Architect or the
  independent reviewer should confirm the redistribution terms before this PR can merge.
- Content: 914 vectors, fields `number`, `key` (hex), `sig` (hex), `msg` (UTF-8 text), `flags`. Flags used upstream:
  `low_order_A`, `low_order_R`, `low_order_component_A`, `low_order_component_R`, `low_order_residue`, `non_canonical_A`,
  `non_canonical_R`, `reencoded_k`. Exactly one vector (number 305) has no flags.
- Nothing here is a key, a trust root or operational material.
