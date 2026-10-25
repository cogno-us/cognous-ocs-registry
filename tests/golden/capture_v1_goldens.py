"""Capture the r08-v1 golden outcomes (EXT-S1-2). Run ONCE against the unrefactored head; commit the output.

    python tests/golden/capture_v1_goldens.py

Writes tests/golden/r08_v1_golden.json. Never re-run it to make a failing replay pass: a replay diff is a changed v1
behaviour and stops the PR (card EXT-S1-2, element 8).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
import v1_corpus  # noqa: E402
import v1_runner  # noqa: E402


def main() -> None:
    records, selections, cases = v1_corpus.build()
    for i, case in enumerate(cases):
        case["id"] = i
        case["expected"] = v1_runner.execute(case, records, selections)
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=HERE).stdout.strip()
    out = {"golden_format": 1, "contract": "r08-v1", "captured_at_head": head,
           "note": "captured from the unrefactored registry_successor at the head above; developer evidence, not an oracle",
           "records": records, "selections": selections, "cases": cases}
    (HERE / "r08_v1_golden.json").write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(len(cases), "cases,", len(records), "records,", len(selections), "selections")


if __name__ == "__main__":
    main()
