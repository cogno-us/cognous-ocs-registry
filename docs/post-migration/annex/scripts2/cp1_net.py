import re, os, shutil, sys
sys.dont_write_bytecode=True
R="/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/cognous-control-plane/src/agent_control_plane/"
P="/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/out/proto_cp1/"
os.makedirs(P,exist_ok=True)
def rd(f): return open(R+f).read()
def n(t): return len(t.rstrip("\n").split("\n"))
exec(open("/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/out/scripts2/cp1_diff.py").read().split("HELPER_SRC='''")[1].split("'''")[0].join(["HELPER_SRC='''","'''"]))
HELP=HELPER_SRC.strip("\n")+"\n"
def wrap(fn,doc): 
    return f'def _verified(scope: GovernedScope, institution_id: str, authority_domain: str, caller: dict, material: Any, verifier: Any, now: datetime):\n    """{doc}"""\n    return verify_required(_registry_modules, "{fn}", scope, institution_id, authority_domain, caller, material, verifier, now)\n'
res={}
def stageA(f,ver,home):
    t=rd(f)
    m=re.search(r"def _verified\(.*?\n    return \(identity, decision\), None\n",t,re.S)
    new=t[:m.start()]+wrap(f"verify_and_decide_v{ver}",f"One Registry `r08-v{ver}` verification (shared checks in `verify_required`).")+t[m.end():]
    if home: new=new.replace("\n\ndef _registry_modules",  "\n\n"+HELP+"\n\ndef _registry_modules",1)
    return t,new
tot={}
for f,v,home in (("registry_revocation_governance.py",6,True),("registry_irreversibility_governance.py",7,False),("registry_final3_governance.py",8,False)):
    t,new=stageA(f,v,home)
    if not home:
        new=new.replace("import _record_payload","import _record_payload, verify_required",1)
    open(P+f,"w").write(new)
    tot[f]=(n(t),n(new))
    print(f,n(t),"->",n(new),n(new)-n(t))
print("stage A total delta (home = revocation module):",sum(b-a for a,b in tot.values()))
print("stage A delta without final3:",sum(b-a for k,(a,b) in tot.items() if "final3" not in k))

# ---- stage B' (f5 age, f5 unreadable); F4 excluded (needs age_mod from the same import try)
def stageB(f,ver,callhost,decmod,identmod,fn):
    t=rd(f)
    m=re.search(r"    if type\(material\) is not SelectionMaterial.*?        return None, Refusal\(\"registry_decision_invalid\", None, kind\)\n",t,re.S)
    call=(f'    got, refusal = verify_required(_registry_modules, "{fn}", scope, institution_id, authority_domain, {callhost}, material, verifier, now)\n'
          '    if refusal is not None:\n        return None, refusal\n    identity, decision = got\n    kind = decision.kind\n')
    loader=(f'def _registry_modules():\n    base = importlib.import_module("registry_successor.decision")\n    common = importlib.import_module("registry_successor.common")\n'
            f'    decision_mod = {"base" if decmod=="base" else "importlib.import_module(%r)"%decmod}\n    identity = importlib.import_module("{identmod}")\n'
            '    verifier_cls = importlib.import_module("registry_adapters.ed25519_verifier").Ed25519Verifier\n    return base, common, decision_mod, identity, verifier_cls\n\n\n')
    new=t[:m.start()]+call+t[m.end():]
    new=new.replace("def derive_",loader+"def derive_",1) if False else re.sub(r"(\ndef derive_(?:effective|unreadable)\()",lambda mm:"\n"+loader.rstrip("\n")+"\n\n"+mm.group(1),new,count=1)
    new=re.sub(r"(from agent_control_plane.registry_governed_lifecycle import \()",r"from agent_control_plane.registry_revocation_governance import verify_required\n\1",new,count=1)
    return t,new
for f,ver,callhost,decmod,identmod,fn in (("registry_f5_class_age_governance.py",2,"{FIELD: dict(host_ages)}","base","registry_successor.v2_policy_identity","verify_and_decide_v2"),
                                        ("registry_f5_class_unreadable_governance.py",5,"{FIELD: dict(host_values)}","registry_successor.v5_decision","registry_successor.v5_policy_identity","verify_and_decide_v5")):
    t,new=stageB(f,ver,callhost,decmod,identmod,fn)
    open(P+f,"w").write(new); print(f,n(t),"->",n(new),n(new)-n(t))
