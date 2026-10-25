"""Integrity test for r08-v2 Amendment 1 (docs only).

Verifies only that the amendment's quoted provenance matches the checkout: the sha256 and git blob ids of the frozen
documents it amends, the section anchors and verbatim excerpts of its supersession table, the recomputable worked-example
digests, and that the three additive reason codes do not overlap the existing 48 `CODES_V2` codes. It also pins the revision-2 declaration
rules once a `CODES_V2_REV2` exists (51 codes, the 48 first, the three additions in order with their layers) and that no
module other than `v2_codes.py` defines it. It does not modify any module.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/r08-v2-contract.md"
ADR = ROOT / "docs/decisions/2026-10-25-adr-ext-s1-1-v1-contract.md"
OUTCOME_MAP = ROOT / "docs/p1-extraction-plan/data/ld02-outcome-map.json"
README = ROOT / "docs/conformance/README.md"
AMEND = ROOT / "docs/r08-v2-contract-amendment-1.md"
AMEND_ADR = ROOT / "docs/decisions/2026-10-25-adr-ext-s1-1-amendment-1.md"

FROZEN = {
    CONTRACT: ("ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f", "64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01"),
    ADR: ("f5ca77f9d21689f28066b62b1aba8587102c9cba", "b9ad06be559bfb99c5e669ca7217d2ee28b62cda7738206c31fd8e6866233b67"),
    OUTCOME_MAP: ("2752800d240d4255af3e62d2e911b0821c8e2af4", "dcb14ec1067ccf3218949de57312040dad9df926b134a67f2826e3f0c37d535c"),
    README: ("ec03cd26fab0b2f5a7421484ec3f5d065a932454", "ffa04af23daf9baa4369261627932da16321c9f9ab1e2fd970444b336aae175f"),
}
NEW_CODES = ("not_activated", "policy_identity_mismatch", "store_unknown")
E_PREFIX = b"ocs-reg/r08-v2/effective-policy\n"
B_PREFIX = b"ocs-reg/r08-v2/policy-binding\n"


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _cb(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _digest(prefix: bytes, data: bytes) -> str:
    return "sha256:" + hashlib.sha256(prefix + data).hexdigest()


def test_amendment_files_exist_and_name_the_frozen_pins():
    text = AMEND.read_text(encoding="utf-8") + AMEND_ADR.read_text(encoding="utf-8")
    for path, (blob, sha) in FROZEN.items():
        assert blob in text and sha in text, f"amendment does not quote the pins of {path.name}"


def test_frozen_documents_match_quoted_pins():
    for path, (blob, sha) in FROZEN.items():
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == sha, f"{path.name} changed: frozen record, add a new amendment instead"
        assert _git_blob(data) == blob, f"{path.name} git blob id differs"


# row id -> (source, heading that must exist in the frozen file, verbatim excerpt that must exist in the frozen file)
ANCHORS = {
    "S-1": ("contract", "### 2.1 Safety bounds belong to the Control Plane (D-27)", "`AGE_MAX = 2678400` is **not adopted**"),
    "S-2": ("contract", "### 2.1 Safety bounds belong to the Control Plane (D-27)", "**Interim supported range: `1 <= value <= MAX`, with `MAX` pending.**"),
    "S-3": ("contract", "## 2. Families (D-10, D-11)", "at most the Control Plane maximum (section 2.1; **pending**, not adopted)"),
    "S-4": ("contract", "## 10. What this contract does not decide", "the numeric `AGE_MAX` (Control Plane owner, D-27)"),
    "S-5": ("adr", "**D-27 Control Plane owns safety bounds", "**`AGE_MAX = 2678400` is NOT adopted.**"),
    "S-6": ("adr", "## 6. Architect round-2 rulings: provenance, and items still open", "**AGE_MAX value** (D-27): the Control Plane owner records the evidence-supported maximum"),
    "S-7": ("contract", "## 4. Canonical policy binding (D-14, D-15)", "`digest` of the canonical composed effective payload (record payload composed with the caller policy by `min`)"),
    "S-8": ("contract", "## 9. Wire shapes", '"effective_policy_digest": "sha256:0f51b95ddc52a51b78e718e46cca42b9e0d000740443904c1378da2db828197b"'),
    "S-9": ("contract", "### 4.1 Serialization and digest", "must match, on the raw string with no normalization and no case folding, the regular expression"),
    "S-10": ("contract", "### 4.1 Serialization and digest", "v1 scope tokens may carry Unicode, which `r08-v2` refuses"),
    "S-11": ("contract", "### 3.3 Closed codes (D-02)", "`CODES_V2` = the 46 `r08-v1` `CODES` entries (unchanged, same layers and meanings) plus exactly two additions"),
    "S-12": ("map", "", '"code_count": 48'),
    "S-13": ("contract", "## 8", "optional scopes report `overlay_not_applied` with the cause"),
}


def test_supersession_rows_are_anchored_to_frozen_text():
    amend = AMEND.read_text(encoding="utf-8")
    sources = {"contract": CONTRACT.read_text(encoding="utf-8"), "adr": ADR.read_text(encoding="utf-8"),
               "map": OUTCOME_MAP.read_text(encoding="utf-8")}
    rows = {ln.split("|")[1].strip(): ln for ln in amend.splitlines() if re.match(r"\| S-\d+ \|", ln)}
    assert set(rows) == set(ANCHORS)
    plain = lambda t: t.replace("`", "")
    for rid, (which, heading, excerpt) in ANCHORS.items():
        src = sources[which]
        assert excerpt in src, f"{rid}: excerpt is not verbatim in the frozen file"
        if heading:
            assert any(line.startswith(heading) for line in src.splitlines()), f"{rid}: heading not found in the frozen file"
        # the amendment row quotes the same excerpt and names the section it anchors to
        assert plain(excerpt.replace('\\"', '"')) in plain(rows[rid]) or plain(excerpt) in plain(rows[rid]), f"{rid}: row does not quote the excerpt"


def test_worked_examples_recompute_from_the_document():
    amend = AMEND.read_text(encoding="utf-8")
    assert hashlib.sha256(E_PREFIX).hexdigest() and len(E_PREFIX) == 32
    assert E_PREFIX.hex() == "6f63732d7265672f7230382d76322f6566666563746976652d706f6c6963790a"
    assert E_PREFIX.hex() in amend

    # Example 1 (historical): plain digest of the frozen section 9 composed effective payload
    eff = {"allowed_actions": ["action-a"], "allowed_adapters": ["adapter-a"], "allowed_institutions": ["inst-a"],
           "allowed_authority_domains": ["domain-a"], "allowed_units": []}
    ex1 = _digest(b"", _cb(eff))
    assert ex1 == "sha256:0f51b95ddc52a51b78e718e46cca42b9e0d000740443904c1378da2db828197b"
    assert ex1 in CONTRACT.read_text(encoding="utf-8") and ex1 in amend

    # Example 2: new preimage over the same effective policy
    pre2 = {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v2",
            "family": "f1ab-local-execution-allowlist", "family_version": "v2", "deny_all": ["allowed_units"], "effective": eff}
    b2 = _cb(pre2)
    assert len(b2) == 346 and b2.hex() in amend and b2.decode("ascii") in amend
    d2 = _digest(E_PREFIX, b2)
    assert d2 == "sha256:a81e892c5d7b2bc3da4651bcece0131e84aaa165bb4823fd10ad8514578f1332" and d2 in amend
    assert _digest(b"", b2) == "sha256:366bbe1d4cd8561d7ed9237207ff32c1891bbe910197d9110997f816fdaf6ae2" and _digest(b"", b2) in amend
    assert _digest(B_PREFIX, b2) != d2

    # Example 3: five non-empty sets
    eff3 = {"allowed_actions": ["transfer", "view"], "allowed_adapters": ["adapter-a"], "allowed_units": ["eur", "usd"],
            "allowed_institutions": ["inst-a"], "allowed_authority_domains": ["domain-a"]}
    pre3 = dict(pre2, deny_all=[], effective=eff3)
    b3 = _cb(pre3)
    assert len(b3) == 349 and b3.decode("ascii") in amend
    d3 = _digest(E_PREFIX, b3)
    assert d3 == "sha256:d38925d9f3daf876c7d7bb9bf74947b3b11da83c363b9c3de795b3595688649f" and d3 in amend
    assert _digest(b"", b3) == "sha256:2d4f58db5bb3756886b06026ecf77b92f496ebb2facb812989e6c7fc17622614" and _digest(b"", b3) in amend

    # The frozen binding still reproduces, and the re-based binding digest is the one printed
    binding = {"binding_profile": "ocs-policy-binding/1", "record_id": "rec-example-f1ab", "record_version": 2,
               "record_digest": "sha256:a9dcd70e716cf681dc8e1becd59ebd48efff4da695dfabf7b68873579e6e40e8",
               "selection_id": "sel-example-f1ab", "selection_epoch": 3,
               "selection_digest": "sha256:070413bf1b87859ccf447b183abb26b487184ec1d33ef52dc47dea64ac930be3",
               "family": "f1ab-local-execution-allowlist", "consumer_id": "runtime-emulator",
               "scope": {"tenant": "tenant-a", "institution": "inst-a", "authority_domain": "domain-a"},
               "operation": "op-transfer", "effective_policy_digest": ex1,
               "activation_ref": "sha256:7f5cc397f3a75d7eb167f54d7aaac9b7b0aa0a43c7830a12e1717c39a1ff4c2a",
               "trust_snapshot_version": 7,
               "trust_snapshot_fingerprint": "sha256:7a8c10fa61aeac5423592bcb437e26875238614c16ef9a0b8c056b6100f5aefe"}
    frozen_bd = "sha256:e1619450a5f57341b735b78293bfa8fdaca4d5414816c16e5eb62f8114c79bfd"
    assert _digest(B_PREFIX, _cb(binding)) == frozen_bd and frozen_bd in CONTRACT.read_text(encoding="utf-8")
    rebased = _digest(B_PREFIX, _cb(dict(binding, effective_policy_digest=d2)))
    assert rebased == "sha256:003fae5669a77ed3cc5e903d21c14037d9c011889ef16d18a291b96bae114b42" and rebased in amend


def test_additive_codes_are_disjoint_and_counts_hold():
    from registry_successor import common as c
    from registry_successor.v2_codes import CODES_V2

    assert len(c.CODES) == 46 and len(CODES_V2) == 48
    assert not (set(NEW_CODES) & set(c.CODES)) and not (set(NEW_CODES) & set(CODES_V2))
    assert len(set(CODES_V2) | set(NEW_CODES)) == 51
    layers = {v[0] for v in CODES_V2.values()}
    assert {"selection", "identity", "trust"} <= layers
    amend = AMEND.read_text(encoding="utf-8")
    for code in NEW_CODES:
        assert f"`{code}`" in amend
    # the pinned outcome map stays the 48-code map
    assert json.loads(OUTCOME_MAP.read_text(encoding="utf-8"))["meta"]["code_count"] == 48


def test_verdict_classes_belong_to_the_four_verdict_vocabulary():
    readme = README.read_text(encoding="utf-8")
    for verdict in ("ACCEPT", "REFUSE", "REFUSE_STALE", "UNKNOWN_FAIL_CLOSED"):
        assert f"`{verdict}`" in readme
    amend = AMEND.read_text(encoding="utf-8")
    assert re.search(r"\| `not_activated` \| `selection` \| `REFUSE` \|", amend)
    assert re.search(r"\| `policy_identity_mismatch` \| `identity` \| `REFUSE` \|", amend)
    assert re.search(r"\| `store_unknown` \| `trust` \| `UNKNOWN_FAIL_CLOSED` \|", amend)


def test_adr_amendment_provenance_pins():
    text = AMEND_ADR.read_text(encoding="utf-8")
    for needle in ("ad95f27201e46b2c838741915aee17d7cc2e5c28", "17d50c3443ccd96ab95d5c1a0a925845ff1c6f7b", "f618cdf",
                   "d2c472e4a09543228bad62235e07a0dedfd7f48b"):
        assert needle in text
    assert "d2c472e4a09543228bad62235e07a0dedfd7f48b" in ADR.read_text(encoding="utf-8")


def test_revision_designation_is_not_a_contract_version_and_no_second_registry():
    from registry_successor import families

    for bogus in ("r08-v2.1", "r08-v2-reasons/2", "r08-v2-reasons/1", "r08-v2.0"):
        sel = families.table_for_contract_version(bogus)
        assert not sel.ok and sel.code == "contract_unsupported", bogus
    assert families.table_for_contract_version("r08-v2").ok and families.table_for_contract_version("r08-v1").ok
    for path in (AMEND, AMEND_ADR):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "r08-v2.1" in line or "CODES_V2_1" in line:
                assert "withdrawn" in line, f"withdrawn draft label used as live: {line[:80]}"
        assert "r08-v2-reasons/2" in text and "CODES_V2_REV2" in text
    amend = AMEND.read_text(encoding="utf-8")
    assert "### 6.7 Compatibility and migration" in amend and "One registry rule." in amend
    # one registry rule: no module other than v2_codes.py may define a revision-2 symbol or the withdrawn draft symbol
    for src in list((ROOT / "registry_successor").rglob("*.py")) + list((ROOT / "registry_conformance").rglob("*.py")):
        if src.name == "v2_codes.py":
            continue
        body = src.read_text(encoding="utf-8")
        assert not re.search(r"^\s*CODES_V2_(REV2|1)\s*[:=]", body, re.M), f"parallel registry symbol in {src}"
    import registry_successor.v2_codes as v2c
    from registry_successor import common as c

    # the withdrawn draft symbol must never exist; the revision-2 symbol may be absent (this PR) or, once the EXT-S1-5
    # implementation PR declares it, must be exactly CODES_V2 plus the three documented codes with the documented layers
    assert not hasattr(v2c, "CODES_V2_1")
    assert len(v2c.CODES_V2) == 48 and list(v2c.CODES_V2)[:46] == list(c.CODES)
    rev2 = getattr(v2c, "CODES_V2_REV2", None)
    if rev2 is not None:
        assert len(rev2) == 51
        assert list(rev2)[:48] == list(v2c.CODES_V2), "revision 2 must begin with revision 1, in order"
        assert all(rev2[k] == v2c.CODES_V2[k] for k in v2c.CODES_V2), "revision 1 entries must be unchanged"
        assert tuple(list(rev2)[48:]) == NEW_CODES
        assert [rev2[k][0] for k in NEW_CODES] == ["selection", "identity", "trust"]
