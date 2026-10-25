# R08 contract `r08-v2`: Amendment 1 (versioned clarification; documentation only)

Status: **AMENDMENT 1 to [`docs/r08-v2-contract.md`](r08-v2-contract.md), effective on merge of this file.** Decision record: [`docs/decisions/2026-10-25-adr-ext-s1-1-amendment-1.md`](decisions/2026-10-25-adr-ext-s1-1-amendment-1.md) (cited as `A1-nn`). Documentation only. It adds no code, changes no behaviour of any evaluator, and authorizes no implementation by itself. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD. Nothing here is "qualified".

Authorization: the Architect authorized one small documentation amendment covering the D-27 `AGE_MAX` decision, the effective-policy digest preimage, a canonical worked example, versioned identifier rules, and source and decision provenance, with the instruction "Do not rewrite previously frozen historical records. Add a versioned clarification." The Architect further ruled (N-4) that the three proposed reason codes carry semantic distinctions that are required and may enter the versioned v2 reason registry through an explicit additive amendment, without changing the closed v1 vocabulary and without overloading an existing code where that would erase an authority-relevant distinction. N-3 is recorded as a clarification (section 7).

## 0. Frozen records stay frozen

The following files are hash-pinned by tests and are **not edited** by this amendment. They remain the historical record of what was proposed and accepted at the time. This amendment is a separate, later, versioned document; where it differs, the table in section 1 says exactly which frozen wording is clarified, and a reader applies the amendment on top of the frozen text.

| Frozen file | git blob (`git hash-object`) | sha256 (pinned by `tests/test_r08v2_f1ab_family.py` unless noted) |
|---|---|---|
| `docs/r08-v2-contract.md` | `ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f` | `64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01` |
| `docs/decisions/2026-10-25-adr-ext-s1-1-v1-contract.md` | `f5ca77f9d21689f28066b62b1aba8587102c9cba` | `b9ad06be559bfb99c5e669ca7217d2ee28b62cda7738206c31fd8e6866233b67` |
| `docs/p1-extraction-plan/data/ld02-outcome-map.json` (48-code outcome map; pinned, unchanged) | `2752800d240d4255af3e62d2e911b0821c8e2af4` | `dcb14ec1067ccf3218949de57312040dad9df926b134a67f2826e3f0c37d535c` |
| `docs/conformance/README.md` (four-verdict vocabulary; read, not amended) | `ec03cd26fab0b2f5a7421484ec3f5d065a932454` | `ffa04af23daf9baa4369261627932da16321c9f9ab1e2fd970444b336aae175f` |

Observed at repository head `f618cdf` (`origin/main`, merge of PR #29). `tests/test_contract_amendment_1_pins.py` recomputes these values and the section anchors below against the checkout; if a frozen file ever changes, that test fails and this amendment must be re-anchored by a new amendment, never by silent edit.

## 1. Supersession table: frozen text to clarification

Reading rule: a row says "where the frozen section says X, read Y". Rows never delete the frozen text. The `Frozen anchor` is the heading (or decision id) in the pinned blob; `Frozen text` is a verbatim excerpt (tested as a substring of the pinned file).

| # | Frozen doc and anchor (blob) | Frozen text (verbatim excerpt) | Clarification (this amendment) |
|---|---|---|---|
| S-1 | contract `### 2.1 Safety bounds belong to the Control Plane (D-27)` (`ab66cc0e`) | `` `AGE_MAX = 2678400` is **not adopted** `` | Section 2: `AGE_MAX = 2147483647` is adopted as a V1 technical representation ceiling. `2678400` stays not adopted (it was never a candidate the evidence supported). |
| S-2 | contract `### 2.1 ...` (`ab66cc0e`) | `**Interim supported range: `1 <= value <= MAX`, with `MAX` pending.**` | Section 2: the supported ranges are in the section 2 table; `MAX = 2147483647`. The interim wording is read as replaced. |
| S-3 | contract `## 2. Families (D-10, D-11)`, F4/F5 bullet (`ab66cc0e`) | `at most the Control Plane maximum (section 2.1; **pending**, not adopted)` | Section 2: the maximum is `2147483647`; not pending. |
| S-4 | contract `## 10. What this contract does not decide` (`ab66cc0e`) | `the numeric `AGE_MAX` (Control Plane owner, D-27)` | Section 2: decided (A1-01). |
| S-5 | ADR `D-27 Control Plane owns safety bounds` (`f5ca77f9`) | `**`AGE_MAX = 2678400` is NOT adopted.**` and `with `MAX` **pending**` | Section 2 (ADR-side row in the ADR amendment, A1-01). |
| S-6 | ADR `## 6` open item 1 (`f5ca77f9`) | `**AGE_MAX value** (D-27): the Control Plane owner records the evidence-supported maximum` | Closed by A1-01. |
| S-7 | contract `## 4. Canonical policy binding (D-14, D-15)`, `effective_policy_digest` row (`ab66cc0e`) | `` `digest` of the canonical composed effective payload (record payload composed with the caller policy by `min`) `` | Section 3: the canonical definition is the domain-separated preimage of section 3. The words are a description of intent; the section 3 bytes are the definition. |
| S-8 | contract `## 9. Wire shapes`, completed binding example (`ab66cc0e`) | `"effective_policy_digest": "sha256:0f51b95ddc52a51b78e718e46cca42b9e0d000740443904c1378da2db828197b"` | Section 4: stays valid as a historical example (opaque member); Example 2 is the example of the new preimage and supersedes it as the example of how `effective_policy_digest` is computed. |
| S-9 | contract `### 4.1 Serialization and digest`, identifiers paragraph (`ab66cc0e`) | `must match, on the raw string with no normalization and no case folding, the regular expression` | Section 5: restated as the V1 identifier rule set `ocs-identifier-rules/1`, with the version tag rule. |
| S-10 | contract `### 4.1 ...` (`ab66cc0e`) | `v1 scope tokens may carry Unicode, which `r08-v2` refuses` | Section 5.3: refusal happens at binding projection (identity or refusal), not at statement validation; the signed statement stays valid and its original bytes stay committed by `selection_digest`. |
| S-11 | contract `### 3.3 Closed codes (D-02)` (`ab66cc0e`) | `` `CODES_V2` = the 46 `r08-v1` `CODES` entries (unchanged, same layers and meanings) plus exactly two additions `` | Section 6: `CODES_V2` (48) is unchanged. Revision 2 of the same Registry v2 vocabulary (`r08-v2-reasons/2`, symbol `CODES_V2_REV2`, 51 codes) is declared (section 6.4). Not an edit of `CODES_V2` and not a second registry. |
| S-12 | ADR `D-02` (`f5ca77f9`) and `ld02-outcome-map.json` (`2752800d`) | `"code_count": 48` (map `meta`) | Unchanged. The 51-code vocabulary needs its own outcome map in the implementation PR (section 6.5); the pinned 48-code map is not edited. |

Items the frozen text leaves open and this amendment does **not** decide are listed in section 9.

## 2. D-27 `AGE_MAX` (A1-01)

Decision (Architect rulings recorded in the OCS Project, Batch 3 and Batch 4; the detailed record is `DR-CP-AGE-1`, registry PR #31, head `17d50c3443ccd96ab95d5c1a0a925845ff1c6f7b`, **pending, not merged**; this amendment states the decision, `DR-CP-AGE-1` carries the measurement and the probe evidence):

| Field class | Lower | Upper | Type |
|---|---|---|---|
| Registry-managed age value (`status_max_age_seconds`, `approval_max_age_seconds`, `class_status_max_age_seconds.<class>`) | `AGE_MIN = 1` | `AGE_MAX = 2147483647` | strict integer |
| Caller age value | 0 | 2147483647 | strict integer |
| Effective value (`min(caller, registry)`) | 0 | 2147483647 | strict integer |

Rules:

1. `AGE_MIN = 1` and `AGE_MAX = 2147483647`, strict integers: `bool`, floats (including nonfinite), strings, `null` and any non-`int` type are invalid; zero and negatives are invalid for registry input; anything above `2147483647` is invalid.
2. `AGE_MAX` is a **technical representation ceiling, not an operational freshness setting.** About 68 years is functionally no freshness bound. The amendment asserts no operational maximum, infers no production requirement from fixture values (largest fixture value 3600 s, synthetic), and does not claim a bound near the ceiling is safe or useful.
3. `effective = min(caller, registry)` per scalar (per class for F5). It can only narrow. A registry value above the caller value leaves the caller value (reported `registry_value_not_narrowing`, unchanged from contract 2). A caller value of 0 stays 0.
4. **Invalid values are never clamped, coerced, defaulted or replaced.** An invalid registry value refuses; an invalid caller value refuses and is never replaced by the registry value.
5. **Source characterization supports but does not prove every environment.** The ceiling was measured clean through the real Control Plane decision path at the characterized source head in the modes tried (`DR-CP-AGE-1`, pending). That is a source reading and builder test. It does not prove that every timestamp, deployment environment, consumer integer width or clock source is safe. The ceiling is valid only while `observed_at + age` is representable in the enforcing component's time arithmetic; a component must refuse, fail closed, a value for which that arithmetic would fail, and must never clamp it.
6. **Component-owned operational limits remain binding.** A valid registry value, however large (up to and including `2147483647`), validates registry input only. It can never silently disable, relax or override a stricter bound the enforcing component owns (a code-owned safety floor, a narrower component default, a host-configured limit or a clock-tolerance rule). Because the registry can only narrow, the component's own bound and the registry-narrowed value compose by taking the stricter; a very large registry value is a no-op against a stricter component bound.
7. The registry validator carries no private bound: its constants are a copy of this table with a citation and a test that fails if the copy and the table differ (frozen D-27 mechanism, unchanged). Out of scope, unchanged: `identity_max_age_seconds`, `mandate_max_age_seconds`, `clock_tolerance_seconds` and the evidence-obligation ages.
8. Lowering the maximum later breaks stored registry values; raising it does not. An operational ceiling may be recorded later with evidence, as a new amendment.

## 3. Effective-policy digest preimage (A1-02)

This section is the **canonical definition** of `effective_policy_digest` once PR #30 (a specification-and-vectors PR with no source change; cited as of its head `ad95f27201e46b2c838741915aee17d7cc2e5c28`, which has since moved; **pending, not merged**) lands; the later `EXT-S1-5` source PR is the implementation. The definition itself is effective with this amendment. It supersedes the frozen contract section 4 wording that describes the preimage only in words (row S-7).

```
effective_policy_digest = "sha256:" + lowercase_hex( SHA-256( E || canonical_bytes(preimage) ) )
E        = the ASCII text  ocs-reg/r08-v2/effective-policy  followed by one LF (0x0a)   (32 bytes)
E (hex)  = 6f63732d7265672f7230382d76322f6566666563746976652d706f6c6963790a
preimage = {
  "effective_policy_profile": "ocs-effective-policy/1",
  "contract_version":         "r08-v2",
  "family":                   <the binding `family` identifier>,
  "family_version":           <closed table tag of the registered family contract: "v1" for f1a, "v2" for f1ab, f4, f5>,
  "deny_all":                 <sorted list of the payload dimensions whose effective set is the explicit empty set; [] for F4 and F5>,
  "effective":                <the composed effective payload: exactly the family payload keys of contract section 2, nothing else>
}
```

Rules:

1. `canonical_bytes` is the contract 4.1 serializer: JSON, keys sorted at every level, separators `,` and `:`, `ensure_ascii=True`, UTF-8. `E` is not JSON and is never emitted. Hashing without `E`, without its LF, or with the binding prefix `ocs-reg/r08-v2/policy-binding\n` gives a different digest.
2. `effective` is the **narrowed result** (per-key intersection for F1a and F1ab, per-scalar and per-class `min(caller, registry)` for F4 and F5). The registry and caller inputs are not in the preimage, so two routes to the same effective sets give the same digest.
3. `deny_all` is derived from `effective` and checked: a presented preimage whose list does not equal the dimensions whose effective set is empty is refused `field_invalid`. An omitted dimension refuses `field_missing`; omitted never means empty.
4. `family`, `family_version`, `contract_version` and `effective_policy_profile` are the **versioned policy context**: the same effective data under another family, family version, contract version or preimage profile has a different digest. `family_version` is a closed enumeration taken from the registered family contract (section 7), never from caller input.
5. Not in the preimage: display names, titles, descriptions or any metadata (adding one refuses `field_unknown`), selection id, epoch or digest, the record triple, the caller policy digest, the validity window, `activation_ref`, trust snapshot identity, and every other binding member.
6. **The digest is claim-carried, caller-dependent EVIDENCE.** Narrowing depends on the caller policy, so the digest legitimately differs per caller under one unchanged selection epoch. It is bound by the claim commitment and checked only for self-consistency with the claim. It is **never compared to durable selection state** (as if selection state alone determined it), never authority, and never widens what the selection permits (contract 4 and 7.4 line 3, unchanged).
7. The binding digest (contract 4.1) treats `effective_policy_digest` as an opaque member checked only for the format `sha256:` plus 64 lowercase hex characters. Changing how this member is derived therefore does not change the binding serialization or the binding prefix, and every previously printed `binding_digest` that embeds an older member value stays reproducible as a value (section 4).

## 4. Canonical worked examples (A1-03)

Three digests appear below. State which supersedes which:

| Example | What it is | Status |
|---|---|---|
| **Example 1** (frozen contract section 9) | `effective_policy_digest = sha256:0f51b95d...197b`, the plain `digest` (no prefix, no context) of the canonical composed effective payload; embedded in the frozen completed binding whose `binding_digest` is `sha256:e1619450a5f57341b735b78293bfa8fdaca4d5414816c16e5eb62f8114c79bfd` | **Historical.** Stays valid as a worked example of the binding digest because `effective_policy_digest` is an opaque member (section 3, rule 7). **Superseded as the example of how `effective_policy_digest` is computed.** |
| **Example 2** (this amendment) | The same composed effective policy as Example 1 under the section 3 preimage | **Canonical** worked example of the new preimage. |
| **Example 3** (this amendment) | A five-set non-empty F1ab effective policy, no deny-all | Canonical second example. It equals the PR #30 draft vector `EP-001` (pending provenance, not a merged fact). |

### 4.1 Example 1 (historical, recomputed)

Input: the frozen contract section 9 composed effective policy (family `f1ab-local-execution-allowlist`, caller allows `action-a` only, `allowed_units` an explicit deny-all):

```json
{"allowed_actions":["action-a"],"allowed_adapters":["adapter-a"],"allowed_institutions":["inst-a"],"allowed_authority_domains":["domain-a"],"allowed_units":[]}
```

`sha256(canonical_bytes(that object))` (no prefix, no context) = `sha256:0f51b95ddc52a51b78e718e46cca42b9e0d000740443904c1378da2db828197b`, which is exactly the value printed in the frozen binding. Under the section 3 preimage this digest is **not** the effective-policy digest of that policy; it is retained only as an opaque member value.

### 4.2 Example 2 (canonical, new preimage)

Preimage object (the Example 1 effective policy plus context; `allowed_units` is empty, so `deny_all` names it):

```json
{
  "effective_policy_profile": "ocs-effective-policy/1",
  "contract_version": "r08-v2",
  "family": "f1ab-local-execution-allowlist",
  "family_version": "v2",
  "deny_all": ["allowed_units"],
  "effective": {
    "allowed_actions": ["action-a"],
    "allowed_adapters": ["adapter-a"],
    "allowed_institutions": ["inst-a"],
    "allowed_authority_domains": ["domain-a"],
    "allowed_units": []
  }
}
```

Canonical text (346 bytes, 7-bit ASCII, no trailing newline):

```
{"contract_version":"r08-v2","deny_all":["allowed_units"],"effective":{"allowed_actions":["action-a"],"allowed_adapters":["adapter-a"],"allowed_authority_domains":["domain-a"],"allowed_institutions":["inst-a"],"allowed_units":[]},"effective_policy_profile":"ocs-effective-policy/1","family":"f1ab-local-execution-allowlist","family_version":"v2"}
```

Canonical bytes (hex, `canonical_bytes(preimage)`, 346 bytes):

```
7b22636f6e74726163745f76657273696f6e223a227230382d7632222c2264656e795f616c6c223a5b22616c6c6f7765645f756e697473225d2c22656666656374697665223a7b22616c6c6f7765645f616374696f6e73223a5b22616374696f6e2d61225d2c22616c6c6f7765645f6164617074657273223a5b22616461707465722d61225d2c22616c6c6f7765645f617574686f726974795f646f6d61696e73223a5b22646f6d61696e2d61225d2c22616c6c6f7765645f696e737469747574696f6e73223a5b22696e73742d61225d2c22616c6c6f7765645f756e697473223a5b5d7d2c226566666563746976655f706f6c6963795f70726f66696c65223a226f63732d6566666563746976652d706f6c6963792f31222c2266616d696c79223a22663161622d6c6f63616c2d657865637574696f6e2d616c6c6f776c697374222c2266616d696c795f76657273696f6e223a227632227d
```

Digest: `sha256( E || bytes )` = `sha256:a81e892c5d7b2bc3da4651bcece0131e84aaa165bb4823fd10ad8514578f1332`.
Control (hashing the same bytes without `E`): `sha256:366bbe1d4cd8561d7ed9237207ff32c1891bbe910197d9110997f816fdaf6ae2` (different, as required).

Re-based completed binding. If the frozen section 9 binding is rebuilt with this value as `effective_policy_digest` (every other member exactly as printed in the frozen contract), its `binding_digest` is `sha256:003fae5669a77ed3cc5e903d21c14037d9c011889ef16d18a291b96bae114b42` (prefix `ocs-reg/r08-v2/policy-binding\n`, contract 4.1). The frozen binding digest `e1619450...79bfd` is unchanged and still reproduces.

### 4.3 Example 3 (canonical, five non-empty sets)

Effective policy: `allowed_actions` `["transfer","view"]`, `allowed_adapters` `["adapter-a"]`, `allowed_units` `["eur","usd"]`, `allowed_institutions` `["inst-a"]`, `allowed_authority_domains` `["domain-a"]`; family `f1ab-local-execution-allowlist`, `family_version` `v2`, `deny_all` `[]`.

Canonical text (349 bytes):

```
{"contract_version":"r08-v2","deny_all":[],"effective":{"allowed_actions":["transfer","view"],"allowed_adapters":["adapter-a"],"allowed_authority_domains":["domain-a"],"allowed_institutions":["inst-a"],"allowed_units":["eur","usd"]},"effective_policy_profile":"ocs-effective-policy/1","family":"f1ab-local-execution-allowlist","family_version":"v2"}
```

Digest: `sha256:d38925d9f3daf876c7d7bb9bf74947b3b11da83c363b9c3de795b3595688649f` (control without `E`: `sha256:2d4f58db5bb3756886b06026ecf77b92f496ebb2facb812989e6c7fc17622614`).

### 4.4 Proof by recomputation (Python and Node, independent serializers)

Both recomputations were run on 2026-10-25 at repository head `f618cdf` and agree on the canonical bytes, length and digest of Examples 2 and 3, and on the Example 2 re-based binding digest. Python uses `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)`; Node uses a hand-written serializer (sorted keys, `\uXXXX` lowercase escapes outside U+0020 to U+007E, surrogate pairs above U+FFFF) and `crypto.createHash`, so the two share no serializer code. Commands (copy and run; each prints the canonical length, hex and digest of Example 2):

```bash
python3 - <<'EOF'
import hashlib, json
eff = {"allowed_actions": ["action-a"], "allowed_adapters": ["adapter-a"], "allowed_institutions": ["inst-a"],
       "allowed_authority_domains": ["domain-a"], "allowed_units": []}
pre = {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v2",
       "family": "f1ab-local-execution-allowlist", "family_version": "v2",
       "deny_all": ["allowed_units"], "effective": eff}
b = json.dumps(pre, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
print(len(b)); print(b.hex())
print("sha256:" + hashlib.sha256(b"ocs-reg/r08-v2/effective-policy\n" + b).hexdigest())
EOF
```

```bash
node - <<'EOF'
const crypto = require('crypto');
function ser(v) {
  if (typeof v === 'number') return String(v);
  if (typeof v === 'string') {
    let s = '"';
    for (const ch of v) {
      const c = ch.codePointAt(0), e = u => '\\u' + u.toString(16).padStart(4, '0');
      if (ch === '"') s += '\\"'; else if (ch === '\\') s += '\\\\';
      else if (c >= 0x20 && c <= 0x7e) s += ch;
      else if (c > 0xffff) { const x = c - 0x10000; s += e(0xd800 + (x >> 10)) + e(0xdc00 + (x & 0x3ff)); }
      else s += e(c);
    }
    return s + '"';
  }
  if (Array.isArray(v)) return '[' + v.map(ser).join(',') + ']';
  return '{' + Object.keys(v).sort().map(k => ser(k) + ':' + ser(v[k])).join(',') + '}';
}
const eff = {allowed_actions: ['action-a'], allowed_adapters: ['adapter-a'], allowed_institutions: ['inst-a'],
             allowed_authority_domains: ['domain-a'], allowed_units: []};
const pre = {effective_policy_profile: 'ocs-effective-policy/1', contract_version: 'r08-v2',
             family: 'f1ab-local-execution-allowlist', family_version: 'v2',
             deny_all: ['allowed_units'], effective: eff};
const b = Buffer.from(ser(pre), 'utf8');
console.log(b.length); console.log(b.toString('hex'));
console.log('sha256:' + crypto.createHash('sha256')
  .update(Buffer.concat([Buffer.from('ocs-reg/r08-v2/effective-policy\n', 'utf8'), b])).digest('hex'));
EOF
```

Expected output of both: `346`, the hex above, and `sha256:a81e892c5d7b2bc3da4651bcece0131e84aaa165bb4823fd10ad8514578f1332`. The throwaway scripts that produced the Example 3 and re-based binding values were run outside the repository and are not committed; `tests/test_contract_amendment_1_pins.py` recomputes the Example 1, 2 and 3 digests and the re-based binding digest in Python from the text of this file.

Status of the evidence: builder-computed, recomputed by two independent implementations. Not independently qualified. No Runtime or Control Plane implementation has been run against these values.

## 5. Versioned identifier rules (A1-04)

### 5.1 Rule set `ocs-identifier-rules/1`

1. **Binding identifiers.** The members `record_id`, `selection_id`, `family`, `consumer_id`, `operation`, `scope.tenant`, `scope.institution` and `scope.authority_domain` of a completed policy binding (`ocs-policy-binding/1`) must match, on the raw string, `\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z` (Architect accepted). The classes are the explicit ASCII ranges: no `\w`, `\d`, locale, `re.IGNORECASE` or Unicode-aware class; end-of-string is `\Z` or full-match, never `$` (Python `$` accepts a trailing newline).
2. **ASCII only; exact bytes.** No normalization (no NFC, NFKC, NFD, NFKD), no case folding, no trimming, no transcoding, no truncation, no percent-encoding, no hashing into an equivalent-looking identifier. Comparison anywhere is exact equality of the UTF-8 bytes. Case is significant and preserved (`tenant-a` and `Tenant-a` are distinct valid identifiers). Both NFC and NFD forms of the same non-ASCII text are refused, so no component can conflate them. Refusal code `field_invalid`.
3. **Payload entries keep the contract section 2 opaque token rule** (Architect confirmed): allowed actions, adapters, units, institutions and authority domains are sorted, duplicate-free, at most 256 entries, each 1 to 128 characters, no control, separator or `*` characters, exact-string membership, no case folding, no wildcard. They are **not** held to the rule 1 grammar; the serializer escapes them (`ensure_ascii`), it never rejects them.
4. **Scope tokens in statements** are retained as provenance and refused only at projection (section 5.3).
5. This is a V1 interoperability restriction on canonical identity members only; it does not restrict human-readable policy metadata, which is never a binding member.

### 5.2 Version tag and succession

`ocs-identifier-rules/1` is the version label of rules 1 to 5 above and is **bound to** `binding_profile = ocs-policy-binding/1` (and, for the digest members, to the effective-policy profile `ocs-effective-policy/1`). It is a specification label, **not a new wire member**: the binding keeps exactly the members of contract section 4, and no field is added. A different identifier grammar (wider character set, longer length, any normalization) is an **explicit successor**: it requires a new identifier-rules tag (`ocs-identifier-rules/2`), a new `binding_profile` value (for example `ocs-policy-binding/2`) and its own domain-separation prefix, and an amendment. It is **never** an in-place change to the V1 grammar. A V1 component never accepts a binding with another `binding_profile` as if it were V1.

### 5.3 Scope-token projection (OQ-4)

Registry statement validators accept scope tokens (1 to 128 characters, no control, separator or `*` characters), which admits Unicode and ASCII characters such as `/`, `%`, `@` and a leading `_`. The projection from a verified statement scope into the binding `scope` is **identity or refusal, nothing else**: a token that is a string, is ASCII and matches the rule 1 grammar is copied byte for byte; otherwise binding creation is refused (`field_invalid`, layer `shape`, stage `projection`, member `scope.<name>`, first failing member in sorted path order). A refused projection produces no binding, and binding creation is refused for **every** participation mode (required and optional alike). A refused projection is **never** by itself sufficient to return the unchanged caller policy or to report `overlay_not_applied`: a required scope yields `required_policy_unavailable` (never a fall back to the caller policy), and an optional scope may fall back only through the separate authenticated durable-state determination of frozen contract 7.4 item 8 (the PR #30 ruling N-5 and section 5.6), and only when the activation state permits absence; that fallback is recorded as an absence or withdrawal evidence record that preserves the original `field_invalid` projection refusal code. Which activation states permit absence is the durable-state determination owned by the guard (`EXT-S4-2`); this amendment does not enumerate them. Two points remain **open for the Architect** and this amendment takes **no position** on either: (a) the rule for optional scopes under an unknown store (contract 8.3 item 3 says `overlay_not_applied`; the conformance README and contract 7.4 item 8(b) say HOLD; PR #30 only proposes HOLD), and (b) whether a refused projection may count as `never_activated`; see PR #30 section 12, questions N-12(a) and N-12(b). The same participation effect applies to every projection-stage refusal PR #30 section 5.6 lists (not only scope tokens), and the layout of the absence or withdrawal evidence record is open (PR #30 N-7, `EXT-S4-0`/`EXT-S4-2`). The token rule's dependence on the platform Unicode database is inherited from the shipped validator and is open (PR #30 N-13). The original statement scope bytes stay in the signed statement and are committed by `selection_digest` (a binding member); no separate provenance digest is defined. A verified statement with an unprojectable scope remains a verified statement. Row S-10: the frozen sentence "v1 scope tokens may carry Unicode, which `r08-v2` refuses" is read as "refused at binding projection".

## 6. Additive reason codes (N-4) (A1-05)

### 6.1 Definitions

Three causes in the guard path have no existing code. The semantic distinctions are required (Architect, N-4). Each code names **exactly one** verdict class of the four-verdict vocabulary of [`docs/conformance/README.md`](conformance/README.md) (`ACCEPT`, `REFUSE`, `REFUSE_STALE`, `UNKNOWN_FAIL_CLOSED`); none is `ACCEPT`, none authorizes anything, none sets `can_authorize_action`. Verdict classes are assigned per the PR #30 draft mapping (spec section 8; as of head `ad95f272...`, which has since moved; pending) and justified here.

| Code | Layer | Verdict class | Retry | Definition |
|---|---|---|---|---|
| `not_activated` | `selection` | `REFUSE` | fresh statement required | The enforcing component's **known, authoritative** durable state has no row for the scope key: this selection (or any selection) was never activated here for this scope. |
| `policy_identity_mismatch` | `identity` | `REFUSE` | never same input | Layer `identity` and class `REFUSE` are agreed by the implemented kit and by PR #30. A **binding is presented**, the known store has a row for it, and a well-formed claim-carried member differs from the durable activation row; a claim epoch **behind** the row is `selection_epoch_stale` (`REFUSE_STALE`) in both. **The member set is OPEN: divergence between implemented kit behavior and the PR #30 mapping, Architect decision required.** The kit (`registry_conformance/highwater.py:999-1001`, after the stale-epoch return at `:997-998`) compares `selection_epoch` (which at that point can only be ahead), `selection_digest`, the record triple and `activation_ref`. PR #30 (spec section 8.2 and `MP-policy_identity_mismatch`) lists scope key, `selection_id`, `selection_digest`, the record triple and `activation_ref`, with no epoch. This amendment does not choose between them. The differing member is proposed to travel as a structured evidence member (`member`, a PR #30 draft term that does not exist in the shipped kit today, see section 6.2a). |
| `store_unknown` | `trust` | `UNKNOWN_FAIL_CLOSED` | after authoritative state is available | The enforcing component's authoritative durable state is unavailable, lost, torn, rolled back, tampered or otherwise indeterminate. Maps to the ADR HOLD (D-21): no effect may proceed; never success, never optional fallback. Finer causes (`state_lost`, `state_malformed`, `state_older_than_anchor`, `anchor_head_mismatch`, `state_log_mismatch`, `log_chain_broken`) are **proposed** to be sub-causes in an evidence field `unknown_cause` (a PR #30 draft term, not a kit member today), not further registry codes. The shipped conformance kit instead returns the finer cause as the verdict `code` (kit-local conformance vocabulary, `registry_conformance/highwater.py`, with the reason in `unknown_reason`) and uses `store_unknown` only when no finer cause applies; the registry-code view of all of them is `store_unknown`. |

Layers are the layers of the PR #30 draft; all three already exist among the layers of `CODES_V2` (`selection`, `identity`, `trust`), so no new layer is introduced.

### 6.2 Verdict class justification

- `not_activated` is `REFUSE`: the store is **known**, so the answer is definitive ("no activation exists"). It is not `REFUSE_STALE` (nothing shows an epoch or activation that was once newer, so it is not a stale or rolled-back claim) and not `UNKNOWN_FAIL_CLOSED` (the state is not indeterminate). The remedy is a fresh authoritative selection activated by the consumer, which is why the retry is "fresh statement required".
- `policy_identity_mismatch` is `REFUSE`: store and claim are both known and they disagree. The same claim does not become acceptable by retrying, so the retry is "never same input". A stale epoch, withdrawal or revocation that is determinable keeps its own code and class (`selection_epoch_stale`, `selection_withdrawn`, `selection_revoked`); this amendment does not reorder the guard comparison lines of contract 7.4, which stay owned by the guard (`EXT-S4-2`).

### 6.2a Boundaries of the three definitions (review disposition)

- `not_activated` is reported when a binding is presented and the known store has no row for its scope key. The qualifier "only when a binding is presented" is this amendment's **proposal**, taken from the implemented kit; PR #30's mapping row says only "no state row for the scope key" and does not state it. With no binding presented, the kit keeps an optional scope with no row and no history on the existing definite fallback (`never_activated`, `overlay_not_applied`, `applied=false`) and refuses a required scope `required_binding_missing` (`highwater.py` guard, no-binding path). That records kit behavior; it is not a position on N-12(b) (whether a **refused projection** may count as `never_activated`), which stays open.
- An absent **row in a known store** is a definitive `REFUSE` (`not_activated`). An absent or unreadable **store** is `UNKNOWN_FAIL_CLOSED` (`store_unknown`). The kit README lists "absent" among the indeterminate states; read that as an absent store, not an absent row. This amendment does not edit the merged kit documents.
- `member` and `unknown_cause` are proposed evidence names from the PR #30 draft. They are **not** defined by this amendment's repository state and the shipped kit does not implement them (it uses `unknown_reason` and verdict codes). Until a contract defines them they carry no normative weight.
- `store_unknown` is `UNKNOWN_FAIL_CLOSED`: authority state is indeterminate. By the kit's definitive-versus-indeterminate rule, a claim that would be a definitive `REFUSE` or `REFUSE_STALE` against a known store is `UNKNOWN_FAIL_CLOSED` against an unknown one. No step recovers an unknown store by itself.

### 6.3 Disjointness from the existing 48 codes

`registry_successor/v2_codes.py` declares `CODES_V2` (48 = the 46 `r08-v1` `CODES` entries plus `trust_snapshot_version_stale` and `selection_withdrawn`). The check below is read-only and was computed at head `f618cdf` (no module is mutated; the amendment does not import anything into a production path):

```bash
# from the repository root
python3 - <<'EOF'
from registry_successor import common as c
from registry_successor.v2_codes import CODES_V2
new = ("not_activated", "policy_identity_mismatch", "store_unknown")
print(len(c.CODES), len(CODES_V2), set(new) & set(CODES_V2), len(set(CODES_V2) | set(new)))
print(sorted({v[0] for v in CODES_V2.values()}))
EOF
```

Result: `46 48 set() 51`. The intersection is empty; the union is 51; the layers `selection`, `identity` and `trust` are all present in the existing layer set. `tests/test_contract_amendment_1_pins.py` re-runs this check.

### 6.4 Revision 2 of the ONE Registry v2 reason vocabulary (declared, not implemented)

There is **one** Registry reason registry per contract: the Registry v2 vocabulary of contract `r08-v2`, whose single home is `registry_successor/v2_codes.py`. This amendment does not create a second registry, a second file or a parallel label scheme. It declares **revision 2** of that same vocabulary; the existing 48-code set is **revision 1** and stays pinned.

| Revision | Designation (documentary; not a wire value) | Symbol | Codes | Status |
|---|---|---|---|---|
| `r08-v1` closed vocabulary | (contract `r08-v1`) | `common.CODES` | 46 | **Unchanged.** |
| Registry v2 vocabulary, revision 1 | `r08-v2-reasons/1` | `v2_codes.CODES_V2` | 48 | **Unchanged**, pinned (section 6.7). |
| Registry v2 vocabulary, revision 2 | `r08-v2-reasons/2` | `CODES_V2_REV2` (declared in `v2_codes.py` by the implementation PR, beside `CODES_V2`) | 51 = revision 1 plus exactly the three codes above; revision 2 is a strict superset of revision 1 | **Declared by this amendment, effective on merge; not implemented.** |

The earlier draft designation `r08-v2.1` / `CODES_V2_1` of this amendment is **withdrawn** (the Architect treated it as a proposed designation; it read like a contract version). The designation scheme follows the one existing reason-registry versioning pattern in the program (Control Plane `runtime-authority-reasons/0.1` and `/0.2`: a name, a slash and a revision, the older revision pinned and the newer a strict superset), so no new scheme is invented. `r08-v2-reasons/<n>` is **never** a `contract_version`: the wire value stays exactly `r08-v2`, `table_for_contract_version` accepts exactly `r08-v1` and `r08-v2` and refuses every other string (including `r08-v2.1`, `r08-v2-reasons/2`) with `contract_unsupported`, and no dispatch is keyed on the revision. No existing registry document or evidence record carries a vocabulary designation today (the 48-code outcome map `meta` has no such field), so this amendment adds no wire field; whether a later detail record carries one is the implementation PR's decision, and if it does the Control Plane rule applies (carry revision 1 unless a revision-2-only code is present).

### 6.5 Obligations placed on the implementation PR

The `EXT-S1-5` implementation PR (not this PR) declares `CODES_V2_REV2` in `registry_successor/v2_codes.py` (the single home; no new file), adds a new outcome map for 51 codes (the 48-code map stays pinned) with `can_authorize_action: false` for every new code, extends the completeness test to iterate all 51 (revision 2) while keeping the revision-1 completeness test over 48, and fail on any unmapped code, and tests that `CODES` (46) and `CODES_V2` (48) are byte-for-byte unchanged and that no v1 entry point can emit a new code. Until that PR merges, components keep the three names as component-local reason names in `detail`, never as `registry_code` of the 48-code map.

### 6.6 Why none may be overloaded (which existing code would erase which distinction)

| New code | Closest existing code(s) | Distinction erased if overloaded |
|---|---|---|
| `not_activated` | `selection_missing` ("no selection was supplied or none is effective"); `selection_withdrawn`; `trust_snapshot_missing` | `selection_missing` is about a Registry-side input that was absent or not effective. A verified, effective selection can exist and still never have been activated by this consumer (activation is consumer state, ADR-REG-TR01). Merging them hides whether the failure is "authority never issued/effective" or "this consumer never activated". `selection_withdrawn` states that an authenticated withdrawal exists; the absence of a row is no authority act at all. `trust_snapshot_missing` concerns a verification input. |
| `policy_identity_mismatch` | `record_identity_mismatch` ("selection pins a different record id or version"); `digest_mismatch` (a digest does not match its canonical content); `selection_scope_mismatch`, `selection_consumer_mismatch`, `selection_operation_mismatch`; `selection_conflict`; `participation_mismatch` | `record_identity_mismatch` compares a selection statement with a record at verification time. `digest_mismatch` is document integrity (tamper or malformation); here every digest may be internally valid while the claim names a policy other than the one activated. Collapsing them erases the difference between "corrupt evidence" and "well-formed evidence about a non-active policy". The scope, consumer and operation codes compare a statement with the consumer's own scope; here the comparison is claim against durable row. `selection_conflict` is two statements in conflict; `participation_mismatch` is optional versus required class. |
| `store_unknown` | `trust_snapshot_missing`, `trust_snapshot_expired`, `time_unavailable`, `verifier_unavailable`, `lineage_authority_unavailable`; any definitive `REFUSE` or `REFUSE_STALE` code such as `selection_epoch_stale` | Those name the absence of a supplied verification input, which the caller can supply. `store_unknown` names loss, rollback or tampering of the consumer's own authoritative state, which nothing supplied by the caller can repair. Overloading would erase the HOLD versus REFUSE distinction (indeterminate versus definitive; kit VD-04 to VD-06) and the recovery path (an operator procedure outside the registry). Mapping it to a stale-epoch or withdrawn code would turn an indeterminate state into a definitive refusal that wrongly signals the state is known. |

### 6.7 Compatibility and migration (evidence at head `f618cdf`)

**Existing convention (file and line evidence).**

- Code sets are named by contract version and held as module symbols, with no label string: `registry_successor/common.py:17` `CONTRACT_VERSION = "r08-v1"`, `:31` `CODES` (46); `registry_successor/v2_codes.py:1-9` (docstring: "Closed refusal-code set `CODES_V2` for contract `r08-v2`", "DECLARED here by EXT-S1-2 and nothing reaches the new codes yet", "a code is added by a contract change, never at run time") and `:21` `CODES_V2 = MappingProxyType({**c.CODES, **V2_ADDED_CODES})` (a successor is a separate read-only mapping built from its predecessor).
- Dispatch is by `contract_version` only: `registry_successor/families.py:108` `CONTRACT_V2 = "r08-v2"`; `:120-129` `table_for_contract_version` accepts an exact `str` equal to `r08-v1` or `r08-v2`, everything else refuses `contract_unsupported` ("no fallback, no implicit upgrade and no default"). Contract `docs/r08-v2-contract.md` line 11 (`contract_version` = `r08-v2`) and section 3.3 (lines 63 to 72, "closed codes").
- ADR D-02 (`docs/decisions/2026-10-25-adr-ext-s1-1-v1-contract.md` lines 22 to 26): "`CODES_V2` is the 46 `r08-v1` codes plus exactly `trust_snapshot_version_stale` and `selection_withdrawn` (48). `CODES` stays 46 and byte-identical"; "Owner: declared in `EXT-S1-2`; mapped in `EXT-S1-5` (completeness test iterates all 48)". The pinned map `docs/p1-extraction-plan/data/ld02-outcome-map.json` `meta.code_count` is 48 and `code_count_note` states the completeness rule; it carries no vocabulary-label field.
- Other registries, for comparison (read-only): Control Plane `src/agent_control_plane/runtime_authority.py:18-19` `VOCABULARY_VERSION = "runtime-authority-reasons/0.1"` and `"runtime-authority-reasons/0.2"`, `:75-80` `vocabulary_for` (0.1 unless a code only 0.2 registers; 0.2 is a superset), `schemas/runtime_authority_reasons_0_1.json` pinned byte-identical and `_0_2.json` the full set, tests in `tests/test_reason_registry_labels.py`. The Control Plane and Runtime consume Registry causes through the structured failure detail (`registry_code` in `ocs-registry-failure-detail/1`) and their own `registry_*` codes, not by importing the Registry code set, so a Registry revision adds no Control Plane or Runtime label.

**Evaluation of the declaration.**

- (a) A documentary designation distinct from `contract_version` is consistent: the Registry convention has no wire label for code sets at all, and `table_for_contract_version` refuses any other string. The integrity test asserts `r08-v2.1` and `r08-v2-reasons/2` refuse. The original `r08-v2.1` form was ambiguous (it reads like a contract version); it is withdrawn and replaced by the Control-Plane-shaped `r08-v2-reasons/<n>` (section 6.4).
- (b) With the correction no string in the `r08-v2.x` form is declared anywhere; the designation cannot be mistaken for a dispatch value and is never accepted as one.
- (c) Existing pins that this amendment does **not** alter (it edits no file): `tests/test_r08v2_family_dispatch.py:290-303` (`len(CODES)==46`, `len(CODES_V2)==48`, `set(CODES_V2)-set(CODES)` equals exactly the two v2 codes, `CODES_V2` begins with the 46 in order, immutability), `tests/test_r08v2_f1ab_family.py:347` (46 and 48), the sha256 pins of the contract and ADR (`tests/test_r08v2_f1ab_family.py:26-27`), the 48-code outcome map (`meta.code_count` 48), and `registry_successor/decision.py:34` `assert code in c.CODES` (the 46-code assertion in the existing refusal helper). Revision 2 is a separate mapping, so none of these changes; each would still hold after the implementation PR as long as it adds `CODES_V2_REV2` instead of editing `CODES_V2`. The implementation PR must itself update the consumer paths listed in (e); that is code and outside this amendment. The pin that forbids `CODES_V2_REV2` is **not** kept: the implementation PR declares it, so the pin test accepts either absence (this PR) or a declaration equal to `CODES_V2` plus exactly the three codes (the implementation PR).
- (d) Migration. A consumer holding 48-code (revision 1) expectations that receives one of the three codes must **fail closed**: an unrecognized `registry_code` is never success, never an optional fallback and never mapped to an existing code by message text. Concretely: a decision or evidence record carrying a revision-2-only code is a refusal (`UNKNOWN_FAIL_CLOSED`/HOLD for `store_unknown`, `REFUSE` for the other two) and a component that does not know the code treats it as an unmapped code, which the completeness rule makes a failing condition, never an implicit allow. The 48-code outcome map and conformance kit keep their current meaning; the kit already uses these names as kit-local conformance vocabulary that is "not an addition to `CODES_V2`" (`docs/conformance/README.md` line 39), and the revision-2 outcome map in the implementation PR is what maps them. Until a component implements revision 2 it keeps the three names as component-local reason names in `detail`, never as `registry_code`.

- (e) What the implementation PR must do in `registry_successor/decision.py` (the full set, not only line 34). Evidence at head `f618cdf`:
  1. `decision.py:34` (`_refusal`) asserts `code in c.CODES` (46). It must accept a code of the revision-2 vocabulary (`CODES_V2_REV2`) when, and only when, the caller is handling a revision-2 decision; no such path exists at `f618cdf`, so the implementation PR introduces it explicitly and keeps the revision-1 path asserting `CODES` (46) or `CODES_V2` (48) as it does now.
  2. `decision.py:52`, `:60` and `:97` rewrite an unrecognized code to an existing one (`selection_missing`, `composition_record_invalid`). A revision-2 code must **never** be rewritten to an existing code: that changes the verdict class (a `store_unknown` HOLD would become a `selection_missing` REFUSE). The implementation PR must route revision-2 codes through unchanged.
  3. `decision.py:35-38` (`_refusal`) applies the optional-participation fallback (`overlay_not_applied`, caller policy unchanged) to **any** code. It must not apply it to an `UNKNOWN_FAIL_CLOSED` code: `store_unknown` is never an optional fallback. Merely widening the assertion at :34 would make `store_unknown` under optional participation fall back to the caller policy, which this amendment forbids.
  4. Audit of the other `assert code in c.CODES` sites at `f618cdf`: `common.py:98` (`fail`), `record.py:35`, `selection.py:53`, `compose.py:25`, `families.py:149`, `v2_f1ab.py:73` and `verify.py:222` (`mark`). Each is a producer helper for verification-time or composition-time causes and asserts the 46-code set. None of the three revision-2 codes is a verification-time or composition-time cause (they are guard and store causes owned by `EXT-S4-2`), so these sites are **unaffected as long as no helper is made to emit a revision-2 code**. If the implementation PR makes one emit a revision-2 code it must widen that helper's assertion explicitly and test it. This is an audit of the assertion sites, not a proof that no other path exists.
  5. `verify.py:230` (`given if given in c.CODES else "field_invalid"`, in the structural branch when the selection is missing or not structurally valid) is the same remap hazard as `decision.py:52`, `:60` and `:97`: a code that is not in the 46-code set is rewritten to `field_invalid`. Today it can only receive codes produced by selection parsing, which are revision-1 causes, so no revision-2 code reaches it. If the implementation PR lets a revision-2 code arrive there (for example a refusal object carrying `store_unknown`), it must pass that code through unchanged and must not rewrite it to `field_invalid`, for the same verdict-class reason as item 2.
- (f) Declaring before implementing is the precedent of `CODES_V2` itself: ADR D-02 proposed it, the outcome map recorded the two codes as `in_CODES false until EXT-S1-2 declares CODES_V2`, and EXT-S1-2 (commit `aa97053`, "family dispatch table and CODES_V2 declaration (behaviour-preserving)") declared it with "nothing reaches the new codes yet"; the mapping completed in `EXT-S1-5`.
- (g) Order of the additions is normative. `CODES_V2_REV2` is `CODES_V2` (48, in its existing order) followed by exactly `not_activated`, `policy_identity_mismatch`, `store_unknown`, in that order; the integrity test pins the tail order and the layers. Any change of the tail order, or of a revision-1 entry, is a new revision, never an edit of revision 2.

**One registry rule.** The three codes may enter the Registry reason vocabulary **only** as revision 2 of the Registry v2 vocabulary in `registry_successor/v2_codes.py`. No parallel code file, no second registry, no per-component copy under a different label, and no edit of `CODES` or `CODES_V2` is permitted. A component-local name for the same cause is not a registry code. This amendment alters no implemented reason-code contract: it edits no source file and no pinned artifact.

## 7. N-3: family-version identity (A1-06)

The `family_version` of the effective-policy preimage comes from the **registered, authenticated family contract** (the contract section 2 table tag, a closed enumeration: `v1` for `f1a-local-execution-allowlist`, `v2` for `f1ab-local-execution-allowlist`, `f4-control-plane-age-bounds` and `f5-action-class-age-bounds`). It is derived from the identity module's own `r08-v2` dispatch table of four rows (PR #30 section 6), keyed on `contract_version` `r08-v2` and the verified family id; it is not read from the shipped `FAMILIES` tables and is not obtained through `lookup_for("r08-v1")`. The tag is derived from the authenticated family id and the `contract_version` of the verified record; it is never an input. Three cases are distinct (PR #30 section 6, ruling N-3, is the normative source for these terms; a divergence is resolved by a new amendment, not silently, see the ADR amendment section on precedence): (1) a **caller-supplied or payload-supplied** `family_version` is refused `field_unknown` at member `family_version` whatever its value, **even the registered tag**; (2) a **presented preimage** (claim evidence) is only compared with the preimage rebuilt from the registered table, and a `family_version` that is not the registered tag refuses `field_invalid`; (3) a family that is not in the dispatch table refuses `family_unsupported`, and a registered family under a `contract_version` not registered for it refuses `contract_unsupported`. There is no fallback tag.

## 8. Explicit non-goals

- **No implementation.** No file under `registry_successor/`, `registry_consumer/`, `registry_records/`, `registry_contract/`, `registry_adapters/` or `registry_conformance/` is added or edited; `v2_codes.py` is not touched; no workflow is edited.
- **No change to frozen evaluator semantics** (`LocalExecutionPolicy.check`, the Control Plane decision path, `registry_consumer`), to composition, or to any signing input, digest profile or golden output other than the new `effective_policy_digest` derivation defined in section 3.
- **No change to v1.** `r08-v1`, `common.CODES` (46), `r08-s01-contract.md` and every v1 golden stay as they are.
- **No change to `CODES_V2` (48)** or to the pinned outcome map.
- **No rewrite of frozen records.** The contract, the ADR and the outcome map are not edited; this amendment is additive and is read on top of them.
- It decides no operational age maximum, no `trust_snapshot_version` ceiling, no scope-key serialization, no per-field binding integer ranges beyond the age fields, no approval-generation derivation and no activation, release or trust-root matter.
- **Effective on merge.** Once merged, implementation PRs cite it (by file path and `Amendment 1`). PR #30 and PR #31 are referenced only as pending or proposed provenance by number and head SHA; nothing in this amendment depends on their merge for its own validity, and none of their text is treated as merged fact.

## 9. Items the amendment leaves open (for the Architect or the owning PR)

1. Per-field integer ranges of the binding (`record_version`, `selection_epoch`, `trust_snapshot_version`) and the scope-key serialization are carried by the PR #30 draft only (OQ-1, OQ-5); they are outside this amendment's authorization and are not recorded here.
2. The designation `r08-v2-reasons/2` and symbol `CODES_V2_REV2` are proposed under the existing convention (section 6.4); the Architect may rename them before the implementation PR merges, by a one-line amendment.
3. The exact guard precedence among `policy_identity_mismatch`, `selection_epoch_stale`, `selection_withdrawn` and `selection_revoked` is owned by the guard design (`EXT-S4-2`), not fixed here.
4. The member set of `policy_identity_mismatch` (implemented kit `highwater.py:999-1001` against the PR #30 mapping row and section 8.2) is a recorded divergence; the Architect decides, then one document is aligned to the other (section 6.1).
5. PR #30 section 12 questions N-10 to N-13 (parse order and ceiling, `trust_snapshot_missing` dual meaning, optional scope under an unknown store and a refused projection read as `never_activated`, platform Unicode dependence) are open there; this amendment takes no position on any of them (sections 5.3, 6.2a, 7).
