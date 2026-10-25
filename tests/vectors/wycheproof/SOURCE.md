# Vendored Project Wycheproof vector file

- File: `ed25519_test.json`, copied byte-for-byte (no modification) from `testvectors_v1/ed25519_test.json`.
- Upstream: https://github.com/C2SP/wycheproof (Apache License 2.0; the unmodified upstream `LICENSE` is `LICENSE` in this directory).
- Source commit (HEAD at retrieval, 2026-10-25, `git clone --depth 1`): `d17cc89fa5c8f4f4d378b5385ebf75da5d0926c9` ("go.mod: bump go directive to 1.27.3", 2026-10-23); the same commit last touched this file.
- sha256 of `ed25519_test.json`: `ea80ffebac085e21cb9d3e903e7fa2b448d96702da5b31f061d0b83b430b74b3` (checked by `tests/test_adapter_ed25519.py`).
- Content: algorithm EDDSA, schema `eddsa_verify_schema_v1.json`, source `google-wycheproof` 0.9rc5, 210 tests in 111 groups (117 valid, 64 invalid, 29 acceptable).
- Used only as untrusted test data (parsed with `json`); nothing here is a key, a trust root or operational material.
