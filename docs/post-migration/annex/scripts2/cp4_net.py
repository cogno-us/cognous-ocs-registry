import re, sys, os
sys.dont_write_bytecode=True
R="/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/cognous-control-plane/src/agent_control_plane/"
n=lambda t: len(t.rstrip("\n").split("\n"))
t=open(R+"registry_governed_policy.py").read()
i=t.index("    if families.class_unreadable is not None:"); j=t.index("    if families.anchor_deadline is not None:")
old=t[i:j]; print("old blocks lines",n(old))
newblk='''    parts = {}
    for slot, derive, compose, host_arg in (("class_unreadable", unrmod.derive_unreadable, unrmod.compose_unreadable, host_values),
                                            ("class_revocation_assurance", revmod.derive_assurance, revmod.compose_assurance, host_assurance),
                                            ("class_irreversible", irmod.derive_irreversible, irmod.compose_irreversible, host_irreversible)):
        if getattr(families, slot) is None:
            continue
        derived_x, refusal = derive(scope=getattr(families, slot).scope, institution_id=institution_id, authority_domain=authority_domain, host=host,
                                    host_values=host_arg, material=materials[slot], verifier=verifier, now=now)
        if refusal is not None:
            return None, _prefixed(slot, refusal)
        effective, digest = derived_x
        try:
            base = compose(base, effective)
        except Exception:
            return None, Refusal("effective_profile_invalid")
        parts[slot] = (dict(effective), digest)
    unreadable, assurance, irreversible = (parts.get(s) for s in ("class_unreadable", "class_revocation_assurance", "class_irreversible"))
'''
print("new blocks lines",n(newblk),"delta",n(newblk)-n(old))
new=t[:i]+newblk+t[j:]
import ast; ast.parse(new)
open("/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/out/proto_cp4b.py","w").write(new)
# 4a
print("FAMILY_NAMES now 2 lines; after: 1 line; comment kept")
