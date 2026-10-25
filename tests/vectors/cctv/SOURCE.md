# Vendored C2SP CCTV Ed25519 edge-case vectors

- Upstream repository: https://github.com/C2SP/CCTV (Community Cryptography Test Vectors), directory `ed25519/`.
- Upstream commit: the retained bytes were introduced by `3eed101b4a65ab84118491cfb91e76c5a3582e8c` (2022-08-30, "ed25519vectors: add reencoded_k vectors", then at path `ed25519vectors/ed25519vectors.json`)
  and carried unchanged by `0fb2c3b5dc50437ce3272abcbec7567dde497047` (2023-04-01, "all: strip -vectors suffix (#4)"), which renamed the path to `ed25519/ed25519vectors.json` and is
  the commit that last touched the file. The file has not changed since; the earlier version at `a3fbec0a...` (2022-08-21) has a different hash and is NOT what is retained.
  Pin for re-verification: `0fb2c3b5dc50437ce3272abcbec7567dde497047`. Verified 2026-10-25 by a full clone: `git show 0fb2c3b5...:ed25519/ed25519vectors.json | sha256sum`
  equals the retained copy, and so does the file at upstream `main` (`50a8ecf2a220f4c8bdc4f085789b8e85c26829e7`, 2026-09-25, HEAD at verification).
- Files here, all byte-for-byte copies of upstream (none modified):
  | File | Upstream path | sha256 |
  |---|---|---|
  | `ed25519vectors.json` (351077 bytes, 914 vectors) | `ed25519/ed25519vectors.json` | `b38e84caf3e7e89170ff520292dbeae421b0a794c27408ce5ce973018fe3d7f9` |
  | `UPSTREAM-README.md` | `ed25519/README.md` (last changed in `3ec4d716e80597545ed285cf62af3dded3a14f65`, 2024-03-06) | `12889cbe441ce9da56fc65aa00b9d16f02ecdbcb8bb19d706ac35e92380d93d0` |
  | `LICENSE` | `ed25519/LICENSE` (present at `0fb2c3b5...`, unchanged at `main`) | `9fe727c21f00a770a683a4c8491bf24203ec839628bad09b026258c5afc17076` |
  These hashes are asserted by `tests/test_adapter_ed25519_cctv.py`. A later upstream change must be reviewed, never silently accepted.
- **License: BSD-3-Clause** (SPDX `BSD-3-Clause`; text above is the upstream `ed25519/LICENSE`, "Copyright 2019 Google LLC / Copyright 2022 Filippo Valsorda",
  three conditions: retain the copyright notice, conditions and disclaimer in source redistributions; reproduce them in binary redistributions;
  no use of the name of Google LLC or its contributors to endorse or promote derived products without written permission).
  The license file sits in the same directory as the vectors and the sibling `ed25519vectors.go` states "governed by a BSD-style license that can be found in the LICENSE file".
  The unmodified `LICENSE` is kept next to the vectors (this directory) and `NOTICE` carries the attribution. This imported license is preserved and is NOT replaced by
  this repository's Apache-2.0; Apache-2.0 applies only to Cognous-authored material.
- **Licensing status, stated plainly:** upstream author confirmation that the BSD-3-Clause directory licence applies at file level to the vectors was NOT obtained.
  The file sits inside the licensed `ed25519/` directory and its notices are retained here. The upstream top-level README names no license, and the LICENSE text speaks of
  "source and binary forms" without naming data files. This is not legal advice; the Architect decides whether that scope is acceptable (fallback: docs/adapters/ed25519.md).
- Content: 914 vectors, fields `number`, `key` (hex), `sig` (hex), `msg` (UTF-8 text), `flags`. Flags used upstream:
  `low_order_A`, `low_order_R`, `low_order_component_A`, `low_order_component_R`, `low_order_residue`, `non_canonical_A`,
  `non_canonical_R`, `reencoded_k`. Exactly one vector (number 305) has no flags.
- Used only as untrusted test data (parsed with `json`). Nothing here is a key, a trust root or operational material.

History: an earlier revision recorded no upstream commit and an unresolved license, because the build environment could not reach the GitHub API and looked for a top-level LICENSE only. Both are resolved above.
