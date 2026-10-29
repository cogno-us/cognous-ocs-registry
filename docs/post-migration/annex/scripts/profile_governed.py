"""Trivial profile (not a benchmark claim): cumulative-time share of governed-layer functions during repeated decide() of a composed workflow (class_age + class_unreadable).
Run from cognous-control-plane with PYTHONPATH=src:<registry pin a40fe75> OCS_REGISTRY_PIN_DIR=<pin>."""
import sys, tempfile, pathlib, cProfile, pstats, io, time
sys.path.insert(0, ".")
import tests.d06_support as S
import pytest
mp = pytest.MonkeyPatch(); S.patch_clock(mp)
d = pathlib.Path(tempfile.mkdtemp())
p, res, cfg, srcs, flow = S.ready(d)
N = 4
t0 = time.perf_counter()
for _ in range(N): flow.decide(p, now=S.NOW)
wall = time.perf_counter() - t0
pr = cProfile.Profile(); pr.enable()
for _ in range(N): flow.decide(p, now=S.NOW)
pr.disable()
st = pstats.Stats(pr); st.sort_stats("cumulative")
rows = {}
for (fn, ln, name), (cc, nc, tt, ct, callers) in st.stats.items():
    rows[(fn.split("/")[-1], name)] = (nc, ct)
tot = sum(v[1] for k, v in rows.items() if k[1] == "decide" and k[0] == "registry_governed_lifecycle.py")
print(f"{N} decides wall (unprofiled) {wall*1000/N:.2f} ms/decide")
want = [("registry_governed_lifecycle.py","decide"),("registry_governed_lifecycle.py","_gl_reverify"),("registry_governed_policy.py","derive_policy"),("registry_governed_policy.py","_gl_held_defect"),
        ("registry_f5_class_age_governance.py","profile_digest"),("effective_configuration_binding.py","mint"),("registry_governed_lifecycle.py","_resolve"),("registry_governed_policy.py","final_composition_defect"),
        ("registry_f5_class_age_governance.py","derive_effective"),("registry_f5_class_unreadable_governance.py","derive_unreadable"),("verify.py","verify_record"),("bounded.py","decide"),("bounded.py","_resolve")]
for k in want:
    if k in rows: print(f"{k[0]}:{k[1]:28s} calls/{N}={rows[k][0]/N:6.1f}  cum {rows[k][1]*1000/N:7.3f} ms/decide ({rows[k][1]/tot:5.1%} of lifecycle.decide)")
mp.undo()
