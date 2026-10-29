# OCS P1 — Controlled Private Technical Preview: Static Plan v1.0

**Status:** PROPOSED, DOCUMENTATION ONLY, NON-AUTHORIZING. No deployment, live execution, third-party access, expenditure or relaxation of holds is authorized by this document.  
**Date:** 2026-10-29  
**Sequence:** Complete 19/19 Registry integration → R1 refactoring, equivalence and engineering freeze → P1 preview qualification → explicitly authorized limited evaluator runs → later independent Tier 1 and production decisions.  
**Governing:** Cognous Engineering Constitution and ADOPTION.md at `cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; Registry Static Migration Plan v1.1 §12; Engineering Plan v1.5; Registry audit #60, consolidation #65/#67, architecture #68/#72; companion `docs/plans/REGISTRY-R1-POST19-CONSOLIDATION-PLAN-v1.0.md` (PR #73, pending adoption at plan creation). OCS central qualification hub and component engineering/release holds continue to apply.

## 1. Objective and preview boundary

Establish a **low-cost, GitHub-native, operator-run, synthetic-only private engineering preview** for a small number of invited technical evaluators. The evaluator receives a reproducible human-readable decision/evidence/replay report, not direct access to production OCS, cloud accounts or real systems. A Cognous operator triggers an approved fixed workflow and shares sanitized artifacts after review. No public web UI, managed SaaS, Kubernetes cluster or persistent multi-tenant service is required.

**Not a production or enterprise pilot.** No real customer data, real transaction, production credentials, live third-party agent connections, mutable enterprise infrastructure, or unbounded agent/tool execution. External reviewers initially have no GitHub write or workflow-dispatch privileges. No open public invitation or publication is authorized.

**Engineering acceptance is bounded:** P1 establishes only that the named scenarios ran correctly in the approved runner/configuration; it does not assert enterprise-wide durable activation, transaction-atomic enforcement, broad operational security assurance or Tier 1 qualification.

## 2. Entry gates (all mandatory)

P1 execution preparation starts only when: (a) all 19 parameters are integrated and independently reconciled to the source/consumer ledger; (b) R1 refactor and differential developer verification have finished; (c) R1 engineering freeze pins exact cross-repository source and dependency SHAs and documents known limitations; (d) a qualified isolation configuration and preview-risk owner are identified; and (e) Architect explicitly authorizes the P1 engineering build. The static plan can be adopted earlier. If 19/19 cannot be completed safely, do not silently redefine completion or bypass R1.

A separate **P1 GO** decision is required after the build and sandbox security review, before an outside evaluator receives results or is invited. No P1 GO implies neither independent Tier 1 acceptance nor authorization of production use.

## 3. Architecture and trust boundaries

1. **Controller:** Cognous operator dispatches a manually invoked GitHub Actions workflow from a dedicated preview package/repository or a clearly isolated workflow under central qualification, scoped to a protected, pinned preview tag/commit; no untrusted arbitrary scenario input.
2. **Execution:** Disposable GitHub-hosted VM with pinned toolchain, immutable source checkout SHAs, tightly scoped `GITHUB_TOKEN` permissions, no self-hosted runner and no production environments. The job has no production or cloud secret exposures, no default user tokens or unreviewed reusable workflows.
3. **Containment:** Synthetic fixtures, deterministic mocked destinations and fake identities/keys. Disable real adapters, external effects, deploy permissions and paid LLM/provider calls. Treat runners as ephemeral *not inherently network-isolated*; verify network-egress controls or an effective fail-closed network policy before accepting the environment as isolated. Dependency fetching must be resolved via verified artifacts, pinned actions and least-privileged allowed routes. If reliably blocking outbound traffic is not feasible on the selected runner, P1 must be redesigned to prebuilt offline artifacts or a separately approved locked-down sandbox; do not describe it as isolated.
4. **Governance:** Registry → Control Plane → Runtime → governed exchange/action boundary → evidence/attestation → replay, only to the extent wired and proven in the frozen preview composition. No unsupported claim that an individual repo's isolated tests prove end-to-end integration.
5. **Reports:** Per-run manifest identifying exact source and fixture hashes, scenario ID, expected/actual disposition, authority inputs, selected policy, decisions, refusals, attempted mock effects, observation, evidence lineage, integrity checks, replay result and known limits. No credentials, personal data or unnecessary sensitive logs.
6. **Access:** Invited evaluators get reviewed sanitized reports through controlled distribution, initially **without repository access**. Any later evaluator self-service dispatch, external repository access or live integration is a separately authorized expansion.

## 4. Fixed synthetic scenario suite

Define a small immutable test catalogue, each with a successful baseline plus adversarial or failure variants where useful:

| ID | Scenario | Minimum expected proof |
|---|---|---|
| PP-01 | Authorized action within a fixed policy | Exact permission and scope; mock destination only; complete decision→effect→evidence chain |
| PP-02 | Over-limit or out-of-scope request | Refusal before effect, precise evidence and unchanged mock state |
| PP-03 | Grant revocation or withdrawal between decision and dispatch | Effect-boundary revalidation denies, negative record retained |
| PP-04 | Stale observation / future clock / deadline | Appropriate hold/refusal at precise boundary; no stale effect |
| PP-05 | Recovery and replay from sealed evidence bundle | Fresh-process integrity verification and deterministic admissible reconstruction, with limitations labeled |

A fixed-scenario candidate may be excluded only with a documented unsupported path and Architect approval. Scenarios must use the exact frozen 19-parameter policy carriers where appropriate, not simulation of a policy result with a hand-written success flag.

## 5. Static work packages

| Stage | Work package | Required deliverable | Exit condition |
|---|---|---|---|
| P0 | Scope and source readiness | Freeze SHA index, preview boundary statement, dependency/authority/secret inventory, scenario support matrix | Entry gates satisfied |
| P1 | Sandbox construction | Reviewed workflow, immutable checkouts, deterministic fixtures, fake keys, no-effect adapters, network and credential controls | Isolation evidence, not mere VM ephemerality |
| P2 | End-to-end harness | Fixed scenario runner and pinned manifest for Registry/Control Plane/Runtime/evidence/replay | All required components observed on supported interfaces |
| P3 | Evaluator experience | Concise README, scenario glossary, per-run artifact index, evidence/replay walk-through, limitations and feedback template | Independent person can interpret results without developer support |
| P4 | Security and negative testing | Permission/secret/egress inspection, attempted unauthorized action, hostile inputs, runner isolation, artifact leakage, replay/rollback | No unmitigated critical/high preview-reachable finding |
| P5 | Preview qualification | Repeatable runs at exact freeze heads, scenario result ledger, CI and artifacts, independent read-only challenge review | P1 GO/NO-GO dossier |
| P6 | Bounded evaluator exercise | Operator runs scenarios for specifically approved evaluators, reviews reports, gathers structured feedback | Explicit Architect P1 GO and per-evaluator access approval |
| P7 | Feedback and closeout | Findings triage, defects, provenance-preserving issues, updated preview status and next decision | No automatic expansion to live systems |

Prefer one lead builder with short-lived nonoverlapping workers for workflow isolation, scenario engineering, evidence/replay, and independent adversarial review. Use GitHub-native PRs and records; no downloadable ZIP handoff or manual local infrastructure work required of the Architect.

## 6. Security acceptance tests and stop conditions

Required evidence includes: exact `GITHUB_TOKEN` permissions, absence of repository/org/environment secrets on the preview run, denied cloud credentials and deployment rights, offline/egress-deny validation, no untrusted executable PR code, pinned actions and dependency hashes, deterministic mock-effect audit, artifact privacy/redaction, safe retention expiration, negative test proving no real external effect, and a reproducible fresh-run replay.

**STOP** on any verified real networked destination, credential-bearing execution, secret leak, out-of-scope data exposure, uncontrolled workflow dispatch, unrestricted egress that defeats the chosen isolation claim, unauthorized mutable dependency, bypass of required governance policy, widening due to failure, broken negative evidence or a preview-reachable critical/high security finding. Do not accept simple 'GitHub-hosted = isolated' reasoning.

If the test harness requires network for artifact upload to GitHub, define the permitted destination narrowly and prove no unapproved egress; never claim total network denial when using that permitted route.

## 7. Economics and operational limits

Default paid LLM/API calls: **OFF**. Use free/included GitHub Actions where available; verify actual plan, runner and artifact billing before authorizing use. For the first preview, cap scenarios, CI concurrency, artifact retention and run count; add a budget guardrail and stop on unexpected costs. No claim of a guaranteed monthly dollar amount without usage evidence. Cognous operator controls dispatch and distribution; invited reviewers need only read reports and provide feedback.

## 8. Acceptance dossier and freeze handling

Publish one GitHub-native index in the qualification hub referencing: frozen source/dependency commits, runner/workflow SHA, signed or hashed manifest, scenarios and expected oracle, test log, denial/no-effect proof, replay validation, network/secret controls, security findings, evaluator README, documented limitations, reviewer dispositions, and risk-owner approval. Freeze and rerun only the updated candidate when a code change occurs; preserve failed raw evidence rather than overwrite it.

**P1 GO criteria:** all scoped scenarios pass at pinned heads; mock destinations and withheld credentials verified; no preview-reachable critical/high findings; network containment demonstrated; evidence and replay are inspectable; independent reviewer confirms observed claims and stated limits; Architect explicitly approves specified individuals, distribution channel and duration.

**P1 NO-GO:** failed isolation, unresolved authority/commitment defect, real-effect possibility, missing evidence or unreviewed external access. Full Tier 1 remains deferred, not waived.

## 9. Relationship to existing holds and roadmap

The P1 technical preview is a **separate constrained authorization** and cannot silently override existing Registry/OCS release, publication or production holds. Private distribution to named evaluators is still external disclosure and needs security/IP and confidentiality review. Ed25519 #26/#34 SECURITY-HELD, V09 separate, held constructor tolerance/PRs #58/#59/#87 excluded. P1 GO cannot confer authorization for real customer workflows, deploy runtime, production data, external agent APIs, or publishing the open stack.

**Sequence:** complete 19 → R1 structural refactor → R1 freeze → P1 sandbox build/qualification → restricted operator-run preview → independent full Tier 1 and separate eventual broader-release decisions. If full Tier 1/security findings block safe external disclosure, maintain HOLD irrespective of P1 technical results.

## 10. Architect decision and handoff contract

At P1 preparation gate, present one concise approval package containing: exact repo heads, R1 completion and 19/19 evidence, expected infrastructure spend and stop guardrail, scenario list, security/isolation implementation, remaining controls, builder PRs, measured runtime cost, independent review, and a GO/NO-GO recommendation. Architect approval of *this plan* is not approval of preview execution or third-party access.

No automatic merges, no release, no activation of unapproved cloud integrations, no changes to security holds. Maintain the static plan as the single reference for any future builder handoff.
