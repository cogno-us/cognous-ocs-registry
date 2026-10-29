import re,difflib,sys
def norm(p):
    t=open(p).read()
    t=re.sub(r'r08-v\d','r08-vN',t)
    t=re.sub(r'\b([vV])[3-8]\b',r'\1N',t)
    t=re.sub(r'\b([vV])[3-8]_',r'\1N_',t)
    t=re.sub(r'_([vV])[3-8]\b',r'_\1N',t)
    return [l.rstrip() for l in t.splitlines()]
a,b=sys.argv[1:3]
for l in difflib.unified_diff(norm(a),norm(b),a,b,lineterm='',n=0): print(l[:260])
