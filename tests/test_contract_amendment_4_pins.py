"""Integrity test for r08-v2 Amendment 4 (documentation only): frozen files are unchanged, quoted excerpts exist in them,
and the draft names the roles, the three typed codes (no new reason code), the fence/anchor protocol and the stated residual limits."""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
AMEND = DOCS / "r08-v2-contract-amendment-4.md"
FROZEN = {
    "r08-v2-contract.md": ("ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f", "64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01"),
    "r08-v2-contract-amendment-1.md": ("081dae56b8fdd3736022900f8dc224eafcd96189", "dddc71ba19b2c853fea223cb3cd1ab0ed38ef606a55473381621f5581fbce0d0"),
    "r08-v2-contract-amendment-2.md": ("e082331d729a6b07b2210a4fd02a06bba3a393c6", "14f972f670892a60ebf2abeb354a644136b4544475afacd8b0e55738796e090c"),
    "r08-v2-contract-amendment-3.md": ("c9bf1d39d60c4f15962855aa39e5d814052f2e77", "e75b29125d71a922fc6f6087dfb10b7a50e2f7d714e6605b3575256a911e013f"),
    "decisions/2026-10-26-adr-ext-s4-0-integration-contract.md": ("86cfef73b6f5b9cdb98f5d60108ed2c8af5ac925", "d25af05dca5b466c5d274e1ca9e8085de727b13a1504356660f4b0e3f03f7e8c"),
}
SOURCE_OF = {
    "A-1": "r08-v2-contract.md", "A-2": "r08-v2-contract.md", "A-3": "r08-v2-contract.md",
    "A-4": "decisions/2026-10-26-adr-ext-s4-0-integration-contract.md", "A-5": "decisions/2026-10-26-adr-ext-s4-0-integration-contract.md",
    "A-6": "decisions/2026-10-26-adr-ext-s4-0-integration-contract.md", "A-7": "r08-v2-contract-amendment-3.md",
}


def test_frozen_files_are_unchanged_and_listed():
    text = AMEND.read_text(encoding="utf-8")
    for rel, (blob, sha) in FROZEN.items():
        data = (DOCS / rel).read_bytes()
        assert hashlib.sha256(data).hexdigest() == sha, f"frozen file changed: {rel}"
        assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == blob
        assert blob in text and sha in text


def test_supersession_excerpts_exist_in_their_frozen_source():
    rows = re.findall(r"\| (A-\d) \| [^|]+ \| `([^`]+)` \|", AMEND.read_text(encoding="utf-8"))
    assert {r[0] for r in rows} == set(SOURCE_OF)
    for key, excerpt in rows:
        assert excerpt in (DOCS / SOURCE_OF[key]).read_text(encoding="utf-8"), key


def test_roles_codes_protocol_and_limits_are_stated():
    t = AMEND.read_text(encoding="utf-8")
    for needle in ("Control Plane Authorization Authority", "Trusted Authorization Installer", "Runtime Effect Executor",
                   "claim supplier is none of these", "no new HMAC, signature or Ed25519 scheme",
                   "policy_identity_mismatch", "store_unknown", "verifier_unavailable", "no new reason code",
                   "journal_mode=DELETE", "mode=ro", "fence", "flock", "pin_epoch", "committed_epoch", "T_int", "T_c", "pin_transition_pending", "There is no degraded or unfenced mode", "no abandon operation", "admission barrier",
                   "UNDETECTED", "irreversible", "authorization state, not selection state", "inside the existing atomic effect transaction",
                   "does not claim instantaneous", "qualification blocker", "real OS privilege-isolation tests",
                   "RELEASE: HOLD", "PUBLICATION: HOLD", "PRODUCTION: HOLD", "NOT effective until the Architect merges it"):
        assert needle in t, needle
    for hold in ("DRAFT",):
        assert hold in t


def test_plan_and_proposal_exist_and_stay_within_budget():
    plan = (DOCS / "f-a1-authorization-pin/qualification-plan.md").read_text(encoding="utf-8")
    ids = re.findall(r"\| (FA1-\d\d) \|", plan)
    assert len(ids) == len(set(ids)) and sum(int(x) for x in re.findall(r"\| FA1-\d\d \| (\d+) \|", plan)) <= 30
    assert "NOT EXECUTED" in plan and "real OS identities" in plan
    prop = (DOCS / "f-a1-authorization-pin/implementation-proposal.md").read_text(encoding="utf-8")
    assert "NOT authorized" in prop and "no code" in prop


def test_revision_2_serialization_has_no_unfenced_terminal_commit():
    t = AMEND.read_text(encoding="utf-8")
    assert "fence_mode" not in t and "Degraded fence mode" not in t and "degraded mode" not in t.replace("no degraded or unfenced mode", "")
    for needle in ("not** committed", "does **not** advance", "pending_blocked", "Lock-free pre-check", "While holding the shared fence",
                   "never cleared without a verified completion", "No effect can commit using the previous active pin after T_c"):
        assert needle in t, needle
    plan = (DOCS / "f-a1-authorization-pin/qualification-plan.md").read_text(encoding="utf-8")
    assert sum(int(x) for x in re.findall(r"\| FA1-\d\d \| (\d+) \|", plan)) == 30
    assert "no unfenced commit" in plan and "does not complete while any earlier shared-fence effect is in flight" in plan
