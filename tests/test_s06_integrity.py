"""S06 integrity pins: the frozen artifacts and recorded evidence of S01 to S05 are unchanged.

Plan: OCS-REG-PLAN v1.1 S06 (blob 6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2). Authorization: docs/decisions/2026-10-24-s06-authorization.md.
These are git blob ids captured at `main` 091355fd0abc368d07c71bfa0673f25feaa97979, before any S06 change. A failure means a frozen
artifact was modified; it is not fixed by editing this table. Changing a pinned file needs a new operator decision and a recorded
amendment. This test checks bytes only; it adds no behavior and does not qualify anything.
"""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BASE_MAIN = "091355fd0abc368d07c71bfa0673f25feaa97979"

PINNED = {
    # governing plan
    "docs/plans/PROJECT_PLAN-v1.1.md": "6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2",
    # historical baseline (Runtime ec728da6)
    "baseline/execution-runtime/engine/safe_executor.py": "2fc880dae37eac76e5074533435740ce0684209d",
    # S03 frozen contract and validator
    "registry_contract/validator.py": "afee88b37197ca4aa3842b228fbc348f585b937a",
    "registry_contract/__init__.py": "5d8e9e69697fae3bc027666541a36379ce299d9f",
    # S04 consumer and candidate fixtures
    "registry_consumer/consumer.py": "bf382d00cb275fa056d60713bf8fc119e9bee7da",
    "registry_consumer/__init__.py": "22df0efa26bbed8f56cb354111bd7f2d0bf4f68b",
    "registry_records/local-execution-allowlist.synthetic.manifest.json": "524b260bfc2c83f4f6630c22a6eda3ae81567e61",
    "registry_records/local-execution-allowlist.synthetic.record.json": "d651509b996d69130ec00a86026bb34bd4975df3",
    # S05 frozen expectations, oracle, comparison spec, raw results and report
    "tests/s05_expectations.json": "37a68275c8c2b932d7a47adac43c05ec802d0081",
    "tests/s05_oracle.py": "503851c4ffa989a213c7dfb4d8957d0d540cb73c",
    "docs/s05-comparison-spec.md": "fe6472776e109b89c5ca0b7278dca064e3969213",
    "docs/s05-results/differential-raw.json": "acb0e6903e725766b39c541acba8dc25a4154b57",
    "docs/s05-results/pytest-output.txt": "04c3be500d2d2464e21d0a3e0e51ca0f033d2525",
    "docs/s05-equivalence-report.md": "2a8f0999b40fe4cf32225b52c2c514d7ee79ee9c",
    # prior test batteries (left unchanged by S06; see docs/s06-consolidation-report.md)
    "tests/test_s01_baseline_local_policy.py": "0ce3ee14b0e015f65955c66bfe572b10aac7a899",
    "tests/test_s03_contract.py": "c0f47fd0f827ebfe8d0187df9f4c080ff3c3846a",
    "tests/test_s04_overlay.py": "91c1b96ad683a346eda0e01299308faa1f1a5d2a",
}


def blob_id(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


@pytest.mark.parametrize("rel", sorted(PINNED))
def test_frozen_artifact_unchanged(rel):
    assert blob_id(ROOT / rel) == PINNED[rel], "frozen artifact changed: " + rel


def test_baseline_sha256_unchanged():
    data = (ROOT / "baseline/execution-runtime/engine/safe_executor.py").read_bytes()
    assert "sha256:" + hashlib.sha256(data).hexdigest() == \
        "sha256:940e781934542a7acd7bbe2f6833f9d329325d94b49425afd9d2bedcf23c5b68"


def test_s05_recorded_results_still_say_what_they_said():
    raw = json.loads((ROOT / "docs/s05-results/differential-raw.json").read_text(encoding="utf-8"))
    totals = raw["totals"]
    assert totals["skipped"] == 3, "the three E05 behavioral SKIPs must stay SKIPs"
    assert sum(totals["failing_cases_by_group"].values()) == 0
    skipped = [r for r in raw["groups"]["representation"] if r.get("skipped_behavior_check")]
    assert sorted((r["id"], r["field"]) for r in skipped) == [
        ("E05", "allowed_actions"), ("E05", "allowed_adapters"), ("E05", "allowed_units")]
    assert raw["identities"]["base_commit"] == "4839747f409000651bf1a684e112b5552912fee1"


NEW_DOCS = ("docs/trust-limitations.md", "docs/s06-representation-and-e05.md", "docs/s06-next-family-recommendation.md",
            "docs/s06-consolidation-report.md", "docs/decisions/2026-10-24-s06-authorization.md")


@pytest.mark.parametrize("rel", NEW_DOCS)
def test_s06_document_relative_links_resolve(rel):
    import re
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        assert (path.parent / target).resolve().exists(), "%s links to a missing file: %s" % (rel, target)


def test_trust_limitations_names_the_governing_plan_blob():
    assert "6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2" in (ROOT / "docs/trust-limitations.md").read_text(encoding="utf-8")
