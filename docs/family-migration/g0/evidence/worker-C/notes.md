# G0 Worker C notes (Control Plane d66ae07fa240510efdcc11ed4b3e1189dcefc822)

## Scope covered
Read in full or in the relevant ranges: policy_gate, policy_config, demo_policies, records (gate/trace), rule_revision, reason_vocabulary, manifest_validation, strict_json,
validation (actor warning), runtime_authority, freshness (profile + extension helpers), holder_inventory, operation_identity, policy_binding, dedupe (profile), merge (profile
+ outcome defs), reversibility (effective value), cli_run, cli, models (RedactionConfig), redaction, local_authority_effect (claim window, effective cap), microsoft_agt
(warning branch, tenant), decision_input_profile (vocabularies), and the bounded.py regions that consume ages, policies, limits and observation (about 1260-1360, 1840-1970,
2010-2030, 2100-2200, 2340-2610, 2655-2756). Schemas, examples, tools, conformance and workflows were grepped for maximum/minimum/default/environ/argparse values.

## Not read / only grepped
canonical_policy_binding and authorization_pin_export (only constants and structure; no tunable found), witness, signing, persistence, atomic_write, replay, tools.py, frame.py,
time_instant (read-only skim), the bulk of bounded.py (record store, journal, lease code), all test bodies (names and greps only, no test run), docs/ other than
bounded_authorization_effect.md 245-290 and docs/README.md, .github/workflows (CI config only; pinned reusable-workflow SHAs do not reach runtime behaviour), tests/fixtures,
conformance JSON (opened head only). No test was executed; "existing_tests" are names, not results.

## Method
git/diff between old_control_plane_0a41faa9 and current (diff -rq), ripgrep for Field(...), defaults, frozenset/constant literals, os.environ/getenv (NONE in src/), argparse
defaults, schema default/minimum/maximum/maxLength, plus cross-reference greps for consumers of each value.

## Surprises
1. bounded.py is BYTE-IDENTICAL to the old pin (2756 lines, no diff). The brief says it grew; it did not. Only runtime_authority.py and local_authority_effect.py changed;
   policy_binding.py, canonical_policy_binding.py and authorization_pin_export.py are new; freshness.py is unchanged, so historical "FR" coordinates are simply the file's own lines
   (61-72), and W8 RA coordinates shifted by +44 lines (policy_binding additions).
2. There is NO environment-variable read anywhere in src/. All values are literals, constructor/profile arguments, CLI flags or caller JSON.
3. 60 vs 300 (see below): different decisions, no code relates them.
4. Two separate 5 s clock tolerances exist: workflow.clock_tolerance_seconds (authority-input reads, `_fresh`) and ObservationPolicy.clock_tolerance_seconds (destination observation).
5. Under a runtime-authority profile the class bound replaces the global status bound ONLY for grant status; conflict status and policy status still use workflow.status_max_age_seconds
   (bounded.py 2445, 2469). Registry F4 `status_max_age_seconds` would therefore map to conflict/policy status, not grant status, once a profile is set. Needs a mapping decision.
6. policy_config.default_action is declared and validated but has no consumer (inert).
7. authority_records_from_policy_config ignores the action_type key and turns every listed scope into a live grant (name 'authority_required' is misleading).
8. tenant_id max 128 is repeated at 5 Python sites + 1 JSON schema; canonical_policy_binding additionally restricts scope.tenant to [A-Za-z0-9][A-Za-z0-9._:-]{0,127}, so a valid proposal tenant may
   be unrepresentable in a canonical binding (fails closed).
9. UNKNOWN_BEHAVIORS lists three values but only hold_effect has a gate branch (bounded.py 2551); the other two are accepted with no age/currency check.
10. EvidenceCriterion thresholds arrive inside the approved authority context, not the host profile (S02 W8-011 treated them as host config).

## The 60 versus 300 relationship (all current consumers)
| Value | Kind | Where | Governs |
|---|---|---|---|
| 60 status/identity/mandate/approval max age | HARD_CODED_LITERAL defaults of BoundedAuthorizationWorkflow.__init__ (bounded.py 1271-1274); HOST_OWNED_CONFIG if passed; acp run passes none | `_fresh` at 2352, 2366, 2398-2399 (only without runtime profile), 2445, 2469, 2505 | age of AUTHORITY INPUT reads (grant status, identity, mandate, conflict, policy, approval) at decide and effect time |
| 60 ActionClass.max_status_age_seconds | HARD_CODED_LITERAL default (runtime_authority.py 131), HOST_OWNED_CONFIG per class | grant status (bounded.py 2398), purpose status (runtime_authority.py 412-415), cached purpose bound, AttemptJoin.class_max_age (1623), extension base, policy_binding ceilings | replaces ctor status bound for grant status under a profile |
| 300 / 5 ObservationPolicy | HARD_CODED_LITERAL at cli_run.py 510; HOST_OWNED_CONFIG elsewhere (tests pass 300 or 60); max_age has NO default, tolerance default 5 | `_reconcile_observation` 1890-1968 | age/future of the DESTINATION OBSERVATION used before first dispatch (observed absence), after dispatch and in reconcile() |
| freshness profile: lease 5.0, reaper 30, nonce True, extension 0, anchor False | defaults on FreshnessProfile, host-owned, opt-in; absent in acp run | bounded 2063, freshness.py 281-295 | liveness / deadline mechanics, not the 60 or 300 values |
| obligation.max_age_seconds | CALLER/issuer-supplied in authority context (exact int, else authority_limit_malformed) | bounded 2545-2556; local_authority_effect 381 (`.get(..., 0)`) | evidence currency |
| reaper_interval 30, cache bounds | see candidates | | |
60 and 300 govern DIFFERENT decisions (authority inputs vs destination observation). Nothing in code compares or orders them; an observation may be older (300) than an authority input
is allowed to be (60). On the `acp run` path both are literal-derived (ctor defaults + cli_run literal). Registry F4 carries only status and approval (60-type) scalars.

## Architect decisions needed
- Whether F4 status scalar should be applied to conflict/policy status when a profile exists (surprise 5).
- Whether Registry ever narrows effect caps/amount (Registry declined an amount slot) - G0-C-033.
- Whether to retire inert policy_config.default_action and the demo helpers, or guard them.
- Whether DedupeProfile (G0-C-022) is policy or provider fact.
- No migration is implemented or proposed as done; all dispositions are proposals.

## Not in my scope list
W3-063 and W1-029 do not appear in scope_rows_C.json (belong to worker B). Runtime-side recovery_resolution.py 86400 literal (F4) NOT READ.
