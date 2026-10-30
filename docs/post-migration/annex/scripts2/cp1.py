import re, difflib, sys
R="/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/cognous-control-plane/src/agent_control_plane/"
def lines(f,a,b): return open(R+f).read().split("\n")[a-1:b]
def norm(ls):
    out=[]
    for l in ls:
        l=l.strip()
        l=re.sub(r"decision\d|v\d_decision|verify_and_decide_v\d|r08-v\d|base\.verify_and_decide_v2|\bv[5678]\b","X",l)
        l=l.replace("None, None, Refusal","None, Refusal")
        out.append(l)
    return out
sites={
 "rev":("registry_revocation_governance.py",150,172),
 "irr":("registry_irreversibility_governance.py",132,154),
 "f3":("registry_final3_governance.py",158,180),
 "f4":("registry_f4_age_governance.py",63,87),
 "f5a":("registry_f5_class_age_governance.py",139,162),
 "f5u":("registry_f5_class_unreadable_governance.py",158,181),
}
for k,(f,a,b) in sites.items(): print(k,f,a,b,b-a+1)
N={k:norm(lines(*v)) for k,v in sites.items()}
ks=list(N)
for i in range(len(ks)):
  for j in range(i+1,len(ks)):
    x,y=N[ks[i]],N[ks[j]]
    sm=difflib.SequenceMatcher(None,x,y,autojunk=False)
    same=sum(m.size for m in sm.get_matching_blocks())
    print(ks[i],ks[j],"matching norm lines",same,"of",len(x),len(y))
# lines common to all six after normalization (as set)
common=set(N["rev"])
for k in ks[1:]: common&=set(N[k])
print("lines in all 6 (set, normalized):",len(common))
for c in sorted(common): print("  ",c[:110])
