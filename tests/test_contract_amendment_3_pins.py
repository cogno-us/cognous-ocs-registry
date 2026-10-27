"""Integrity test for r08-v2 Amendment 3 (documentation only): the frozen contract is unchanged, the quoted excerpts exist in it, and the
normative section names the five F1a sets, the existing reason codes and the fail-closed rules. It does not modify any module."""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/r08-v2-contract.md"
AMEND = ROOT / "docs/r08-v2-contract-amendment-3.md"
BLOB, SHA = "ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f", "64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01"
FIVE = ("allowed_actions", "allowed_adapters", "allowed_units", "allowed_institutions", "allowed_authority_domains")


def test_frozen_contract_is_unchanged_and_quoted():
    data = CONTRACT.read_bytes()
    assert hashlib.sha256(data).hexdigest() == SHA, "frozen contract changed: add a new amendment instead"
    assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == BLOB
    text = AMEND.read_text(encoding="utf-8")
    assert BLOB in text and SHA in text


def test_excerpts_of_the_supersession_table_exist_in_the_frozen_contract():
    frozen = CONTRACT.read_text(encoding="utf-8")
    amend = AMEND.read_text(encoding="utf-8")
    excerpts = re.findall(r"\| F-01 \| `r08-v2` section 7\.4, item 3 \| `([^`]+)` \|", amend)
    assert len(excerpts) == 2
    for e in excerpts:
        assert e in frozen


def test_normative_section_covers_the_invariant_and_adds_no_reason_code():
    amend = AMEND.read_text(encoding="utf-8")
    for name in FIVE:
        assert f"`{name}`" in amend
    for needle in ("policy_identity_mismatch", "store_unknown", "verifier_unavailable", "no new reason code", "inside the same atomic transaction",
                   "HOLD", "A claim with a binding and no executor sets is refused"):
        assert needle in amend
    assert "RELEASE: HOLD" in amend and "PRODUCTION: HOLD" in amend
