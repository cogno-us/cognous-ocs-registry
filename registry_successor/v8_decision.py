"""`r08-v8` verify-and-decide entry point (docs/r08-v8-contract.md). A thin public binding of the parameterised engine to the `V8` profile.

Same signature and result type as `v6_decision.verify_and_decide_v6`; there is no `contract_version` parameter (hardwired `r08-v8`). The engine
implements verification and decision once; this module adds nothing to it. APPROVED CANDIDATE. Non-authorizing; unqualified.
"""
from typing import Any

from registry_successor import v2_codes
from registry_successor.decision import PolicyDecision
from registry_successor.engine import decide as _decide
from registry_successor.engine import profiles as _profiles

CODES = v2_codes.CODES_V2


def verify_and_decide_v8(participation: Any, caller: Any, record_text: Any, selection_text: Any, context: Any, trust: Any, verifier: Any,
                         now: Any, key_admission: Any = None) -> PolicyDecision:
    """The single public r08-v8 verify-and-decide entry point. Pure: takes raw record and selection TEXT, parses and verifies both at one `now`, and
    composes only on success. A withdrawal is never an application (the engine refuses it with its own typed code)."""
    return _decide.verify_and_decide(_profiles.V8, participation, caller, record_text, selection_text, context, trust, verifier, now, key_admission)
