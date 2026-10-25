# S02 worker evidence (raw, unverified except where docs/s02-inventory.md says otherwise)

Raw per-worker inventory tables W1 to W9 (620 rows), produced by builder-coordinated Claude workers with disjoint file ownership against exact pins (Runtime `ec728da6dc301a664b331ac8986afd6e850a1273`, Control Plane `0a41faa972699f7ec3063967a14cd9bdd3e67d27`). Preserved as evidence (Constitution CA06); not independently reviewed. Row classes and risk tiers are worker-assigned and provisional; several workers did not read the Constitution text. The integrated, builder-verified view is `docs/s02-inventory.md`. Nothing here is qualification.

## Citation errata (added after Copilot review of PR #3; raw tables above are unchanged)

- W8 FR/HI/OI/WI coordinates are cumulative across files, not file-relative. Example: `FR:460` is `freshness.py:62` (offset 398 for FR). Per-file lines were re-read only for the fields cited in `docs/s02-inventory.md` (`freshness.py:62-72`; W8-040 line 62, W8-041 line 64, W8-042 line 66). Treat other W8 coordinates as unverified.
- W7-057..063 anchors are imprecise. At Control Plane `0a41faa9`, `bounded.py`: target checks `2636-2645`; payload checks `2647-2661`; block gate `2663-2667`; proposal validity window `2708-2711`. The ranges `2747-2753` cited for W7-063 contain permission helpers.
- W7-059 block gate: the check is `(action.default_action or manifest.default_action) == "block"` (`bounded.py:2663-2667`). A truthy action default takes precedence over the manifest default, so an action default of `escalate` overrides a manifest default of `block`; it is not "either default is block". The tool `allowed` not-boolean-true condition is an additional blocker.
