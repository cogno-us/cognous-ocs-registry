"""Static-harness measurement (not a test run): count canonical-JSON commitment() calls per decide/execute of a composed governed workflow.
Run: cd cognous-control-plane; PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:<registry pin a40fe75> OCS_REGISTRY_PIN_DIR=<pin> python count_commitments.py"""
import sys, tempfile, collections, pathlib
sys.path.insert(0, ".")
import tests.d06_support as S
import agent_control_plane.bounded as b
import agent_control_plane.effective_configuration_binding as ecb
import agent_control_plane.registry_f5_class_age_governance as agemod
import agent_control_plane.registry_governed_lifecycle as lc
import agent_control_plane.registry_governed_policy as pol
import agent_control_plane.registry_effective_policy as ep
counts = collections.Counter()
orig = b.commitment
def counting(v):
    counts["commitment"] += 1
    f = sys._getframe(1)
    caller = f.f_globals.get("__name__", "?").split(".")[-1]
    if caller == "agent_control_plane": caller = "?"
    counts["by:" + caller] += 1
    return orig(v)
for m in (b, ecb, agemod, pol, ep):
    if hasattr(m, "commitment"):
        setattr(m, "commitment", counting)
def wrap(mod, name, label):
    o = getattr(mod, name)
    def w(*a, **k):
        counts[label] += 1
        return o(*a, **k)
    setattr(mod, name, w)
wrap(ecb, "mint", "ecb.mint"); wrap(ecb, "members_defect", "ecb.members_defect"); wrap(ecb, "digest_of", "ecb.digest_of")
wrap(agemod, "profile_digest", "profile_digest")
orig_dp = pol.derive_policy
def dp(*a, **k):
    counts["derive_policy"] += 1
    return orig_dp(*a, **k)
pol.derive_policy = dp
tmp = pathlib.Path(tempfile.mkdtemp())
def snap(): return collections.Counter(counts)
def delta(a): return {k: counts[k]-a.get(k,0) for k in counts if counts[k]-a.get(k,0)}
import pytest
mp = pytest.MonkeyPatch(); S.patch_clock(mp)
try:
    for label, kw in (("A+U (class_age, class_unreadable)", dict(f=False, a=True, u=True)), ("F+A+U (adds f4_ages)", dict(f=True, a=True, u=True))):
        d = tmp / label[:3].replace(" ", "_").replace("+", "")
        d.mkdir(parents=True, exist_ok=True)
        c0 = snap(); p, res, cfg, srcs, flow = S.ready(d, **kw); print(label, "CONSTRUCT", delta(c0))
        c0 = snap(); dec = flow.decide(p, now=S.NOW); print(label, "DECIDE", dec.result, delta(c0))
        c0 = snap(); out = flow.execute(p, flow.records.decision(dec.decision_id), adapter_id=p.adapter_id, now=S.NOW); print(label, "EXECUTE", delta(c0))
finally:
    mp.undo()
