"""CP-1 differential on COPIES: old _verified / inline preamble vs a prototype shared helper. Repo files are only read."""
import sys, types, importlib, re, json, itertools
sys.dont_write_bytecode=True
SRC="/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/cognous-control-plane/src"
sys.path.insert(0,SRC)
from agent_control_plane.registry_governed_lifecycle import GovernedScope, Refusal, SelectionMaterial
import agent_control_plane.registry_revocation_governance as rev
import agent_control_plane.registry_irreversibility_governance as irr
import agent_control_plane.registry_final3_governance as f3
import agent_control_plane.registry_f4_age_governance as f4
import agent_control_plane.registry_f5_class_age_governance as f5a
import agent_control_plane.registry_f5_class_unreadable_governance as f5u

# ---------------- prototype helper (this is the NEW abstraction)
HELPER_SRC='''
def verify_required(modules, decide_name, scope, institution_id, authority_domain, caller, material, verifier, now):
    """One Registry `required` verification through the family's own module loader. Returns `((identity, decision), None)` or `(None, Refusal)`; applies the shared decision-shape checks."""
    if type(material) is not SelectionMaterial or type(material.record_text) is not str or type(material.selection_text) is not str:
        return None, Refusal("material_invalid")
    try:
        base, common, decision_mod, identity, verifier_cls = modules()
    except Exception:
        return None, Refusal("registry_unavailable")
    if type(verifier) is not verifier_cls:
        return None, Refusal("verifier_not_admitted")
    try:
        context = common.ExpectedContext(scope.consumer_id, scope.tenant_id, institution_id, authority_domain, scope.operation_id)
        decision = getattr(decision_mod, decide_name)("required", caller, material.record_text, material.selection_text, context, material.trust, verifier, now)
    except Exception:
        return None, Refusal("registry_call_failed")
    if not isinstance(decision, base.PolicyDecision) or type(decision.kind) is not str or decision.operationally_authorized is not False:
        return None, Refusal("registry_decision_invalid")
    kind = decision.kind
    if kind in ("required_policy_unavailable", "overlay_not_applied"):
        return None, Refusal("registry_not_applied", decision.code, kind)
    if kind != "applied" or decision.deny_all is not False:
        return None, Refusal("registry_decision_invalid", None, kind)
    return (identity, decision), None
'''
print("helper physical lines:",len(HELPER_SRC.strip("\n").split("\n")))
ns={"SelectionMaterial":SelectionMaterial,"Refusal":Refusal}
exec(HELPER_SRC,ns); verify_required=ns["verify_required"]

# ---------------- fake Registry
class PolicyDecision:
    def __init__(s,kind,code=None,op=False,deny=False,eff=None): s.kind,s.code,s.operationally_authorized,s.deny_all,s.effective=kind,code,op,deny,eff
class ExpectedContext:
    def __init__(s,*a): s.a=a
class Ed25519Verifier: pass
SCEN={"cur":None}
def decide(*a, **k):
    r=SCEN["cur"]
    if isinstance(r,Exception): raise r
    return r
class Mod(types.SimpleNamespace): pass
base=Mod(PolicyDecision=PolicyDecision,verify_and_decide_v2=decide)
common=Mod(ExpectedContext=ExpectedContext)
ident=Mod(effective_policy_digest=lambda fam,payload,*c:"sha256:"+json.dumps([fam,payload],sort_keys=True),registered_family_version=lambda f,c:1)
FAKES={"registry_successor.decision":base,"registry_successor.common":common,"registry_adapters.ed25519_verifier":Mod(Ed25519Verifier=Ed25519Verifier),
 "registry_successor.v2_age_bounds":Mod(FAMILY_F4="f4-control-plane-age-bounds"),"registry_successor.v2_policy_identity":ident}
for n in (5,6,7,8):
    FAKES[f"registry_successor.v{n}_decision"]=Mod(**{f"verify_and_decide_v{n}":decide})
    FAKES[f"registry_successor.v{n}_policy_identity"]=ident
MODE={"fail":False}
real_import=importlib.import_module
def fake_import(name,*a,**k):
    if name.startswith(("registry_successor","registry_adapters")):
        if MODE["fail"]: raise ImportError(name)
        return FAKES[name]
    return real_import(name,*a,**k)
importlib.import_module=fake_import

SC=GovernedScope("c","t","act","op")
good=SelectionMaterial("{}","{}",None)
def scenarios():
    v=Ed25519Verifier()
    S=[]
    S.append(("material None",dict(material=None,verifier=v,res=None)))
    S.append(("record non-str",dict(material=SelectionMaterial(1,"{}",None),verifier=v,res=None)))
    S.append(("selection non-str",dict(material=SelectionMaterial("{}",b"x",None),verifier=v,res=None)))
    S.append(("import failure",dict(material=good,verifier=v,res=None,fail=True)))
    S.append(("foreign verifier",dict(material=good,verifier=object(),res=None)))
    S.append(("verifier subclass",dict(material=good,verifier=type("V",(Ed25519Verifier,),{})(),res=None)))
    S.append(("call raises",dict(material=good,verifier=v,res=RuntimeError("x"))))
    S.append(("non-PolicyDecision",dict(material=good,verifier=v,res={"kind":"applied"})))
    S.append(("kind non-str",dict(material=good,verifier=v,res=PolicyDecision(5))))
    S.append(("op auth True",dict(material=good,verifier=v,res=PolicyDecision("applied",op=True))))
    S.append(("op auth None",dict(material=good,verifier=v,res=PolicyDecision("applied",op=None))))
    S.append(("required_policy_unavailable",dict(material=good,verifier=v,res=PolicyDecision("required_policy_unavailable",code="R1"))))
    S.append(("overlay_not_applied",dict(material=good,verifier=v,res=PolicyDecision("overlay_not_applied",code="R2"))))
    S.append(("other kind",dict(material=good,verifier=v,res=PolicyDecision("weird",code="R3"))))
    S.append(("applied deny_all True",dict(material=good,verifier=v,res=PolicyDecision("applied",deny=True))))
    S.append(("applied deny_all None",dict(material=good,verifier=v,res=PolicyDecision("applied",deny=None))))
    S.append(("applied ok",dict(material=good,verifier=v,res=PolicyDecision("applied",eff={}))))
    return S
S=scenarios()

# ---------- stage A: _verified of rev / irr / f3 versus wrapper over helper
def run(fn,sc):
    SCEN["cur"]=sc["res"]; MODE["fail"]=sc.get("fail",False)
    try: out=fn(sc["material"],sc["verifier"])
    except BaseException as e: return ("EXC",type(e).__name__)
    MODE["fail"]=False
    got,ref=out
    return (None if got is None else (got[0] is ident, got[1] is SCEN["cur"]), ref)
bad=0; n=0
for mod,vn in ((rev,"verify_and_decide_v6"),(irr,"verify_and_decide_v7"),(f3,"verify_and_decide_v8")):
    old=lambda m,v,mod=mod: mod._verified(SC,"inst","dom",{"k":1},m,v,"NOW")
    new=lambda m,v,mod=mod,vn=vn: verify_required(mod._registry_modules,vn,SC,"inst","dom",{"k":1},m,v,"NOW")
    for name,sc in S:
        a,b=run(old,sc),run(new,sc); n+=1
        if a!=b: bad+=1; print("DIFF",mod.__name__,name,a,b)
print("stage A (3 modules x",len(S),"verdict shapes): comparisons",n,"differences",bad)

# ---------- stage B: rewrite the inline preamble in derive_* / verify_scope_selection and compare the FULL function output
import inspect
def rewrite(mod, funcname, start_marker, end_marker, replacement, extra_ns=None):
    src=inspect.getsource(getattr(mod,funcname))
    i=src.index(start_marker); j=src.index(end_marker)+len(end_marker)
    new=src[:i]+replacement+src[j:]
    d=dict(mod.__dict__); d.update(verify_required=verify_required); d.update(extra_ns or {})
    exec(new,d); return d[funcname]
# f5u
f5u_new=rewrite(f5u,"derive_unreadable",
 '    if type(material) is not SelectionMaterial','        return None, Refusal("registry_decision_invalid", None, kind)\n',
 '    got, refusal = verify_required(_registry_modules, "verify_and_decide_v5", scope, institution_id, authority_domain, {FIELD: dict(host_values)}, material, verifier, now)\n    if refusal is not None:\n        return None, refusal\n    identity, decision = got\n    kind = decision.kind\n',
 {"_registry_modules":lambda: (importlib.import_module("registry_successor.decision"),importlib.import_module("registry_successor.common"),importlib.import_module("registry_successor.v5_decision"),importlib.import_module("registry_successor.v5_policy_identity"),importlib.import_module("registry_adapters.ed25519_verifier").Ed25519Verifier)})
from types import SimpleNamespace as NS
host=NS(actions={"act":NS(class_id="c1",irreversible=False,on_unreadable="refuse")})
def runB(fn,sc,hv,**kw):
    SCEN["cur"]=sc["res"]; MODE["fail"]=sc.get("fail",False)
    try: out=fn(scope=SC,institution_id="i",authority_domain="d",host=host,host_values=hv,material=sc["material"],verifier=sc["verifier"],now="N",**kw)
    except BaseException as e: return ("EXC",type(e).__name__)
    finally: MODE["fail"]=False
    return repr(out)
bad=n=0
SB=list(S)
# add applied scenarios with effective maps
v=Ed25519Verifier()
rec=json.dumps({"payload":{"class_on_unreadable":{"c1":"refuse"}}})
for eff in ({"class_on_unreadable":{"c1":"refuse"}},{"class_on_unreadable":{"c1":"bounded_tolerance"}},{"class_on_unreadable":{"c1":"zzz"}},{"x":1},None):
    SB.append((f"applied eff={eff}",dict(material=SelectionMaterial(rec,"{}",None),verifier=v,res=PolicyDecision("applied",eff=eff))))
for hv in ({"c1":"refuse"},{"c1":"bounded_tolerance"}):
    for name,sc in SB:
        a,b=runB(f5u.derive_unreadable,sc,hv),runB(f5u_new,sc,hv); n+=1
        if a!=b: bad+=1; print("DIFF f5u",name,a,b)
print("stage B f5u full-function: comparisons",n,"differences",bad)
