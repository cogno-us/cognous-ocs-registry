"""M12 Phase-1 source probes (deterministic, synthetic). Run (repo root of the Control Plane checkout at 673ef09): PYTHONPATH=src:. python probe1.py"""
import sys, tempfile, pathlib, json
from datetime import timedelta
import agent_control_plane.bounded as bounded
from tests.test_bounded_authorization import NOW, PROFILE
from tests.test_runtime_authority import setup_flow, bind_approval
from agent_control_plane.runtime_authority import approval_commitment, RuntimeAuthorityProfile
from agent_control_plane.freshness import FreshnessProfile, effective_age_bound, extension_defects
bounded._now = lambda: NOW
tmp = pathlib.Path(tempfile.mkdtemp())
p, r, f, cfg = setup_flow(tmp)
ctx = r.contexts[PROFILE]
def narrowed(cfg, v, **extra):
    d = cfg.model_dump(mode="json")
    for a in d["actions"].values(): a["max_status_age_seconds"] = v
    d.update(extra)
    return RuntimeAuthorityProfile.model_validate(d)
base = approval_commitment(cfg, ctx)
print("P1 equal  ->", approval_commitment(narrowed(cfg, 60), ctx) == base)
print("P1 narrow ->", approval_commitment(narrowed(cfg, 30), ctx) == base)
# round trip identity
print("P1b roundtrip dump equal ->", RuntimeAuthorityProfile.model_validate(cfg.model_dump(mode="json")).model_dump(mode="json") == cfg.model_dump(mode="json"))
# P2: approval bound to baseline, workflow with narrowed profile
n = narrowed(cfg, 30)
f2 = bounded.BoundedAuthorizationWorkflow(manifest=f.manifest, resolver=r, destination=f.destination,
        records=bounded.BoundedRecordStore(tmp/'run2.json', 'run-2'), observation_policy=bounded.ObservationPolicy(max_age_seconds=300),
        allow_test_time=True, runtime_authority_profile=n)
d = f2.decide(p, now=NOW); print("P2 old approval vs narrowed profile ->", d.result, d.reasons)
bind_approval(r, n); d = f2.decide(p, now=NOW); print("P2 re-issued approval ->", d.result, d.reasons)
print("P3 catalogue_digest differs:", d.binding.runtime_authority["catalogue_digest"] != bounded.commitment(cfg.model_dump(mode="json")))
# P4: extension limit widening past narrowed base
fr = n.model_copy(update={"freshness": FreshnessProfile(max_age_extension_seconds=300)})
from agent_control_plane.freshness import AgeBoundExtension
row = AgeBoundExtension(extension_id="e1", class_id="synthetic-irreversible", from_max_age_seconds=30, to_max_age_seconds=330,
        not_before=NOW.isoformat(), expires_at=(NOW+timedelta(hours=1)).isoformat(), outage_ref="o", requested_by="a", signer="b", recorded_at=NOW.isoformat())
from agent_control_plane.rule_revision import RuleRevisionProfile
rp = RuleRevisionProfile(signers=["b"])
print("P4 narrowed base 30, limit 300, ext to 330 defects:", extension_defects(rp, row, max_extension_seconds=300, base_seconds=30), "bound:", effective_age_bound(rp,[row],class_id="synthetic-irreversible",base_seconds=30,now=NOW,max_extension_seconds=300)[0])
row60 = row.model_copy(update={"from_max_age_seconds":60,"to_max_age_seconds":120})
print("P4b old row (from 60) vs narrowed base 30 defects:", extension_defects(rp, row60, max_extension_seconds=300, base_seconds=30))
print("P4c composed limit 0 on ext to 40 defects:", extension_defects(rp, row.model_copy(update={"to_max_age_seconds":40}), max_extension_seconds=0, base_seconds=30))
