import sys, json, random
sys.dont_write_bytecode=True
sys.path.insert(0,"/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/cognous-control-plane/src")
import agent_control_plane.registry_revocation_governance as rev
import agent_control_plane.registry_f5_class_age_governance as f5a
import agent_control_plane.registry_f5_class_unreadable_governance as f5u
import agent_control_plane.registry_effective_policy as eff
SCALAR_MAX=f5a.SCALAR_MAX
def new_age(t):
    m=rev._record_payload(t,f5a.FIELD)
    if type(m) is not dict or not m or not all(type(k) is str and type(v) is int and 1<=v<=SCALAR_MAX for k,v in m.items()): return None
    return m
def new_unr(t):
    m=rev._record_payload(t,f5u.FIELD)
    if type(m) is not dict or not m or not all(type(k) is str and f5u._value(v) for k,v in m.items()): return None
    return m
def parse_accept(ph,rn,t):
    try: return ("ok",json.loads(t,object_pairs_hook=ph,parse_float=rn,parse_constant=rn))
    except BaseException as e: return ("err",type(e).__name__ if isinstance(e,RecursionError) else "x")
seeds=['{"payload":{"class_status_max_age_seconds":{"a":1,"b":60}},"x":1}',
 '{"payload":{"class_on_unreadable":{"a":"refuse","b":"bounded_tolerance"}},"statement":{"epoch":1}}',
 '{"payload":{"class_status_max_age_seconds":{"a":1,"a":2}}}','{"payload":{"class_status_max_age_seconds":{"a":1.0}}}',
 '{"payload":{"class_status_max_age_seconds":{"a":NaN}}}','{"payload":{"class_status_max_age_seconds":{"a":1e2}}}',
 '{"payload":{"class_status_max_age_seconds":{"a":99999999999999999999999}}}','{"payload":{"class_status_max_age_seconds":{"a":-0}}}',
 '{"payload":{"class_status_max_age_seconds":{}}}','{"payload":{"class_status_max_age_seconds":{"a":1},"extra":1}}','{"payload":[]}','[]','null','', '﻿{"payload":{}}',
 '{"payload":{"class_on_unreadable":{"\\ud800":"refuse"}}}','{"payload":{"class_on_unreadable":{"a":"refuse"}}}  trailing', "[" * 100000]
corpus=list(seeds)+[None,b"{}",5,{"payload":1}]
rnd=random.Random(20261029)
alphabet='{}[]":,. 0123456789eE+-NaInfty\\ud800abclspayoadfuse_'
for _ in range(30000):
    s=list(rnd.choice(seeds[:2]+seeds[2:9]))
    for _ in range(rnd.randint(1,4)):
        op=rnd.random(); i=rnd.randrange(len(s)+1)
        if op<.4 and s: s[min(i,len(s)-1)]=rnd.choice(alphabet)
        elif op<.7: s.insert(i,rnd.choice(alphabet))
        elif s: del s[min(i,len(s)-1)]
    corpus.append("".join(s))
bad=0
for t in corpus:
    if f5a.registry_class_map(t)!=new_age(t): bad+=1; print("DIFF age",repr(t)[:80])
    if f5u.registry_unreadable_map(t)!=new_unr(t): bad+=1; print("DIFF unr",repr(t)[:80])
    a=parse_accept(f5a._strict_pairs,f5a._reject_number,t) if isinstance(t,str) else None
    b=parse_accept(rev._strict_pairs,rev._reject_number,t) if isinstance(t,str) else None
    c=parse_accept(eff._strict_pairs,eff._reject_number,t) if isinstance(t,str) else None
    d=parse_accept(f5u._strict_pairs,f5u._reject_number,t) if isinstance(t,str) else None
    if not (a==b==c==d): bad+=1; print("DIFF parser",repr(t)[:80],a,b,c,d)
    sa,sb=eff.selection_ref(t),None
print("corpus",len(corpus),"parser/extractor comparisons x4 each: differences",bad)
