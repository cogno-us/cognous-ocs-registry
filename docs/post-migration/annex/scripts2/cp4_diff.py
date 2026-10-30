import sys, itertools, importlib.util
from types import SimpleNamespace as NS
sys.dont_write_bytecode=True
sys.path.insert(0,"/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/cognous-control-plane/src")
import agent_control_plane.registry_governed_policy as pol
from agent_control_plane.registry_governed_lifecycle import Refusal
spec=importlib.util.spec_from_file_location("proto_pol","/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/out/proto_cp4b.py")
proto=importlib.util.module_from_spec(spec); sys.modules["proto_pol"]=proto; spec.loader.exec_module(proto)
SLOTS=["class_unreadable","class_revocation_assurance","class_irreversible"]
def stubs(log,beh):
    def mk(slot,dn,cn):
        def derive(**kw):
            log.append(("derive",slot,tuple(sorted(kw)),kw["host_values"],kw["scope"]))
            if beh[slot][1]=="refuse": return None,Refusal("boom_"+slot,"RC","k")
            return ({"c":slot[:3]},"dig_"+slot),None
        def compose(base,eff):
            log.append(("compose",slot,base,tuple(eff.items())))
            if beh[slot][2]=="raise": raise ValueError("x")
            return base+"+"+slot[:3]
        return dn,derive,cn,compose
    ns={}
    for slot,mod,dn,cn in (("class_unreadable","unr","derive_unreadable","compose_unreadable"),("class_revocation_assurance","rev","derive_assurance","compose_assurance"),("class_irreversible","ir","derive_irreversible","compose_irreversible")):
        a,d,b,c=mk(slot,dn,cn); ns[mod]=NS(**{a:d,b:c})
    return ns
def run(m,beh):
    log=[]; ns=stubs(log,beh)
    m.unrmod,m.revmod,m.irmod=ns["unr"],ns["rev"],ns["ir"]
    m.agemod=NS(profile_digest=lambda b:"PD("+str(b)+")"); m.final_composition_defect=lambda *a,**k: None
    fam=NS(f4_ages=None,class_age=None,anchor_deadline=None,observation_max_age=None,observation_clock_tolerance=None,terminal_revocation=None,
           **{s:(NS(scope="SC_"+s) if beh[s][0] else None) for s in SLOTS})
    try:
        out=m.derive_policy(families=fam,host="H",host_scalars={},host_ages=None,host_values="HV",materials={s:"M_"+s for s in SLOTS},verifier="V",institution_id="i",authority_domain="d",now="N",
                            host_assurance="HA",host_terminal=None,host_irreversible="HI",host_observation=None)
    except BaseException as e: out=("EXC",type(e).__name__)
    return repr(out),log
states=[(False,None,None)]+[(True,"refuse",None),(True,"ok","ok"),(True,"ok","raise")]
n=bad=0
for combo in itertools.product(states,repeat=3):
    beh=dict(zip(SLOTS,combo))
    a,b=run(pol,beh),run(proto,beh); n+=1
    if a!=b: bad+=1; print("DIFF",combo,a,b)
print("CP-4b scripted differential: combos",n,"differences",bad,"(declared/undeclared x derive-refusal x compose-raise per slot; compares result tuple AND full ordered call log with kwargs)")
