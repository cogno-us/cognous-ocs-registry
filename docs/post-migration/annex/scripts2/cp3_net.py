import re, sys, os
sys.dont_write_bytecode=True
R="/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/cognous-control-plane/src/agent_control_plane/"
P="/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/out/proto_cp3/"; os.makedirs(P,exist_ok=True)
n=lambda t: len(t.rstrip("\n").split("\n"))
PARSER=re.compile(r"def _strict_pairs\(pairs\):.*?def _reject_number\(_\):\n    raise ValueError\(\"[^\"]*\"\)\n\n\n",re.S)
tot=0; pinned=0
for f,imp,dropjson in (("registry_effective_policy.py","from agent_control_plane.registry_revocation_governance import _reject_number, _strict_pairs\n",False),
                       ("registry_f5_class_unreadable_governance.py","from agent_control_plane.registry_revocation_governance import _record_payload\n",True),
                       ("registry_f5_class_age_governance.py","from agent_control_plane.registry_revocation_governance import _record_payload\n",True)):
    t=open(R+f).read(); new=PARSER.sub("",t,count=1)
    if "registry_effective_policy" not in f:
        new=re.sub(r"    try:\n        doc = json.loads\(record_text.*?    except Exception:\n        return None\n    if type\(m\)","    m = _record_payload(record_text, FIELD)\n    if type(m)",new,count=1,flags=re.S)
    if dropjson: new=new.replace("import json\n","",1)
    new=re.sub(r"(from agent_control_plane\.[a-z_]+ import )",imp+r"\1",new,count=1)
    open(P+f,"w").write(new); d=n(new)-n(t); tot+=d; print(f,n(t),"->",n(new),d)
    import ast; ast.parse(new)
print("CP-3 total",tot)
