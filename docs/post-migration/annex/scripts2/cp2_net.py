import re, sys
sys.dont_write_bytecode=True
R="/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/cognous-control-plane/src/agent_control_plane/"
n=lambda t: len(t.rstrip("\n").split("\n"))
HELP='''def narrowing_defect(effective, host_values, registry, value_ok, rank, stricter):
    """Refusal code (or None) for a Registry effective class map: same classes as the host, closed vocabulary, never above the host, the stricter of host and record for every class the record names, the host value for every other class."""
    if set(effective) != set(host_values) or not all(value_ok(v) for v in effective.values()):
        return "effective_policy_invalid"
    if any(rank[effective[k]] > rank[host_values[k]] for k in host_values):
        return "effective_policy_widens_host"
    if registry is None or not set(registry) <= set(host_values) or any(effective[k] != stricter(host_values[k], registry[k]) for k in registry):
        return "effective_policy_invalid"
    if any(k not in registry and effective[k] != host_values[k] for k in host_values):
        return "effective_policy_invalid"
    return None
'''
print("helper lines",n(HELP))
tot=0
for f,ok,rank,st,mapfn in (("registry_revocation_governance.py","_ra_value","_RANK_RA","stricter_assurance","registry_assurance_map"),
                           ("registry_irreversibility_governance.py","_ir_value","_RANK_IR","stricter_irreversible","registry_irreversible_map"),
                           ("registry_f5_class_unreadable_governance.py","_value","_RANK","stricter","registry_unreadable_map")):
    t=open(R+f).read()
    m=re.search(r"    if set\(effective\) != set\(host_values\).*?    if any\(k not in registry and effective\[k\] != host_values\[k\] for k in host_values\):\n        return None, Refusal\(\"effective_policy_invalid\", None, kind\)\n",t,re.S)
    new=f"    registry = {mapfn}(material.record_text)\n    code = narrowing_defect(effective, host_values, registry, {ok}, {rank}, {st})\n    if code is not None:\n        return None, Refusal(code, None, kind)\n"
    nt=t[:m.start()]+new+t[m.end():]
    print(f,"replaced",n(m.group(0)),"->",n(new)); tot+= n(new)-n(m.group(0))
print("call-site delta",tot,"net after helper(+2 blank)",tot+n(HELP)+2, "net rev+irr only", None)
