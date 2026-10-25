# Architecture (S01)

Non-authorizing, builder-side. HOLD unchanged. This page describes what S01 contains and the one baseline behaviour it reproduces; it describes no future design and makes no qualification claim.

## Shape of the repository

```
README.md, docs/        mission, provenance, live status
baseline/execution-runtime/   pinned, read-only historical source (2 Python files + licenses)
tests/                  one behavioural fixture over that source
requirements-s01.lock.txt     hash-locked pytest
```

There is no registry, no rule data and no tooling yet. The imported source is a reference to compare against, not code this repository evolves.

## The baseline decision path

The imported module is `engine/safe_executor.py` from the Execution Runtime at `ec728da6` (v0.1 review tuple `g8-r10`). It is stdlib-only and defines the Runtime's local, synthetic execution boundary. The path used by the fixture is:

1. `snapshot_envelope(ExecutionEnvelope)` deep-copies and freezes the request (envelope version `0.2.0`, an `ExecutionOperation` with actor, institution, authority domain, adapter, action, target, amount, unit, effect counts, grant reference).
2. `LocalDestinationExecutor.execute_snapshot` first runs `validate_snapshot` (shape, types, payload commitment, strict numbers) and then `LocalExecutionPolicy.check`.
3. `LocalExecutionPolicy.check` is a fixed sequence of hardcoded local restrictions. Each refusal raises `PermissionError` with a stable reason text, in this order: institution, authority domain, adapter, action, target, unit, amount, exactly one effect, effective maximum effects. (The one-effect branch is not reachable through the real path, because validation refuses `effects != 1` first.) Allowed values come from the policy object the caller constructs (frozensets, a tuple of target prefixes, `max_amount`, `max_effects`, `target_match`); the order of checks, the reason texts, the one-effect rule and the target well-formedness and segment-matching rules are in code.
4. A refusal is written to the SQLite destination as a `policy_denial` failure record (`local_policy_rejected`, stage `pre_dispatch`) and re-raised; no attempt begins and no effect row is written.
5. On success the executor begins an attempt, observes the destination, commits the frozen operation to `DurableRefundDestination` (SQLite on disk, synthetic refunds) and returns an `ExecutionResult` (`executed`, observation `applied`).

The module does not establish institutional authorization. Per the hub's documentation (not re-verified here), the Control Plane is intended to call this module; S01 deliberately does not import the Control Plane (see provenance), so the fixture exercises the Runtime's local policy and destination only.

## Why this is a suitable first baseline

- It is a small family of hardcoded local restrictions with observable outcomes (reason text, failure record, effect count). Closure and determinism beyond the fixtures were not checked.
- The same file is byte-identical at the later MVP candidate Runtime `c5e97e87`, so the F3 repair does not alter it.
- It uses only the standard library and a local synthetic SQLite destination, with no network, subprocess or credential use observed in the fixture. Safety was not assessed.

## Boundaries

- Rules are not extracted or migrated in S01. The list of restrictions above is a description of existing code, not a schema.
- Constitutional floors, authority and revocation logic, and the Control Plane's reason-code and mandatory-check tables are outside this baseline.
- Existing OCS repositories remain authoritative; this repository does not duplicate them.
