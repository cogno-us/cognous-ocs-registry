"""`r08-v6` record validation (docs/r08-v6-contract.md). The same checks, order and codes as `record.validate_record_text` and
`decision.validate_record_text_v2` (shape, values, supersession and digest checks are reused from `record.py`), but the record must carry exactly
`contract_version` `r08-v6` and its family is looked up in the `r08-v6` table (`v6_families.FAMILIES_V6`, two families, each record for exactly one). A
document of any other contract version refuses `contract_unsupported` here; an `r08-v6` document refuses `contract_unsupported` at the v1..v5 validators.
No fallback or implicit upgrade. Pure; never raises. Non-authorizing; unqualified.
"""
import copy
from typing import Any

from registry_successor import common as c
from registry_successor import record as record_mod
from registry_successor import v6_families


def validate_record_text_v6(text: Any) -> "record_mod.RecordResult":
    try:
        loaded = c.load_document(text)
        if not loaded.ok:
            return record_mod._refuse(loaded.code, loaded.detail)
        body = loaded.value
        if not isinstance(body, dict):
            return record_mod._refuse("field_type_invalid", "document is not an object")
        version = body.get("contract_version")
        if type(version) is not str or version != v6_families.CONTRACT_V6:
            return record_mod._refuse("contract_unsupported")
        if body.get("kind") != "record":
            return record_mod._refuse("kind_unsupported")
        spec = v6_families.lookup_v6(body.get("family"))
        if spec is None:
            return record_mod._refuse("family_unsupported")
        code = record_mod._shape(body, spec) or record_mod._values(body, spec)
        if code:
            return record_mod._refuse(code)
        if not record_mod._supersession_ok(body):
            return record_mod._refuse("supersession_invalid")
        if body["payload_digest"] != c.digest(body["payload"]):
            return record_mod._refuse("digest_mismatch", "payload_digest")
        if body["record_digest"] != c.digest({k: v for k, v in body.items() if k != "record_digest"}):
            return record_mod._refuse("digest_mismatch", "record_digest")
        return record_mod.RecordResult(True, None, "", copy.deepcopy(body), body["record_digest"])
    except Exception:  # defensive: an unexpected shape error is a refusal, never an acceptance
        return record_mod._refuse("field_type_invalid", "unexpected structure")
