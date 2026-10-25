"""EXT-S1-4 evidence probe (NOT part of the test suite; never imported by registry code).

Re-measures (and, for date and C-int overflow, measures) for the Architect's condition on AGE_MAX = 2147483647, the real Control Plane `decide()` path at pin
7a4bcd40b3b49e61ff3c294dcca53b52f460b22c with the freshness profile ON, ON + anchor_deadline_to_inputs, and OFF, at 2**31-1
and 2**31 (and beyond), for the class base and for the two workflow scalars, plus the float-vs-int age comparison edge.

Run:  python3 -I ext-s1-4-age-bound-probe.py <control-plane-clone> <dir with pydantic etc.>
Read-only against the Control Plane clone; writes only temp dirs.
"""
import sys, pathlib, tempfile
from datetime import timedelta
CP, LIB = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
sys.path[:0] = [p for p in (LIB, CP + "/src", CP) if p]
sys.dont_write_bytecode = True
import platform, subprocess
import pydantic
import agent_control_plane.bounded as bounded
print("PROBE ENVIRONMENT: python", sys.version.split()[0], "|", platform.python_implementation(), "|", platform.platform(),
      "| pydantic", pydantic.VERSION, "| control-plane HEAD",
      subprocess.run(["git", "-C", CP, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() or "unknown")
from agent_control_plane.freshness import FreshnessProfile
from tests.test_bounded_authorization import NOW
import tests.test_freshness as tf
from tests.test_runtime_authority import setup_flow, bind_approval


class Clock:
    def __init__(s): s.now = NOW
    def __call__(s): return s.now
bounded._now = Clock()
TMP = tempfile.mkdtemp()


def flow(base=60, fresh=True, max_ext=0, **fr):
    d = pathlib.Path(tempfile.mkdtemp(dir=TMP))
    p, r, f, c = setup_flow(d)
    cl = next(iter(c.actions.values())).model_copy(update={"max_status_age_seconds": base})
    upd = {"actions": {p.action_id: cl}}
    if fresh:
        upd["freshness"] = FreshnessProfile(max_age_extension_seconds=max_ext, **fr)
    cfg = c.model_copy(update=upd)
    bind_approval(r, cfg)
    f.runtime_authority_profile = cfg.snapshot()
    tf.authority(f, r)
    return p, r, f, cfg


def decide(p, f):
    try:
        return "ok:" + f.decide(p, now=NOW).result
    except Exception as e:
        return "EXC:" + type(e).__name__ + ":" + str(e)[:50]


MODES = {"freshness-on": dict(fresh=True), "anchored": dict(fresh=True, anchor_deadline_to_inputs=True), "off": dict(fresh=False)}
print("== class base ActionClass.max_status_age_seconds, grant status age 0")
for base in (2**31 - 1, 2**31):
    for name, kw in MODES.items():
        p, r, f, c = flow(base, **kw)
        print(f"  base={base} {name}: {decide(p, f)}")
print("== class base far above the ceiling (date overflow search), grant status age 0")
for base in (2 * 10**11, 25 * 10**10, 3 * 10**11, 2**63, 2**64):
    row = []
    for name, kw in MODES.items():
        p, r, f, c = flow(base, **kw)
        row.append(f"{name}:{decide(p, f)}")
    print(f"  base={base}: " + " | ".join(row))
print("== class base MAX, grant status aged exactly MAX and MAX+1 (freshness on)")
for age in (2**31 - 1, 2**31):
    p, r, f, c = flow(2**31 - 1, True)
    tf.stale_grant(r, age)
    print(f"  grant age {age}: {decide(p, f)}")
print("== workflow scalars status_max_age_seconds / approval_max_age_seconds")
for attr in ("status_max_age_seconds", "approval_max_age_seconds"):
    for val in (2**31 - 1, 2**31, 2**34, 2**53, 2**62, 2**63, 2**64, 10**30):
        row = []
        for name, kw in MODES.items():
            p, r, f, c = flow(60, **kw)
            setattr(f, attr, val)
            row.append(f"{name}:{decide(p, f)}")
        print(f"  {attr}={val}: " + " | ".join(row))
print("== outage extension composed to the ceiling (base 60, limit MAX-60, extension to MAX), grant aged MAX")
p, r, f, c = flow(60, True, max_ext=2**31 - 1 - 60)
tf.request(f, to_max_age_seconds=2**31 - 1)
tf.stale_grant(r, 2**31 - 1)
print("  ", decide(p, f))
print("== float-vs-int comparison edge `(now - observed).total_seconds() <= max_age` (bounded.py _fresh): +1 microsecond")
p, r, f, c = flow(60, False)
for B in (2**31 - 1, 2**31, 2**33, 2**34):
    obs = (NOW - timedelta(seconds=B, microseconds=1)).isoformat()
    print(f"  B={B}: age=B+1us accepted={f._fresh(obs, NOW, B)} (must be False)")
