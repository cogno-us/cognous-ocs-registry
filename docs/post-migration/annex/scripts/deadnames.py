import ast,glob,re,collections,os
prod=[p for p in glob.glob('registry_*/**/*.py',recursive=True)]
tests=glob.glob('tests/**/*.py',recursive=True)+glob.glob('tools/*.py')+glob.glob('docs/**/*.py',recursive=True)
def words(p): return re.findall(r'[A-Za-z_][A-Za-z0-9_]*',open(p,encoding='utf8',errors='ignore').read())
pc=collections.Counter(); tc=collections.Counter()
pw={p:collections.Counter(words(p)) for p in prod}; tw={p:collections.Counter(words(p)) for p in tests}
for p in prod: pc.update(pw[p])
for p in tests: tc.update(tw[p])
out=[]
for p in prod:
    if not p.startswith('registry_successor'): continue
    t=ast.parse(open(p).read())
    for n in t.body:
        names=[]
        if isinstance(n,(ast.FunctionDef,ast.ClassDef)): names=[n.name]
        elif isinstance(n,ast.Assign): names=[x.id for x in n.targets if isinstance(x,ast.Name)]
        for nm in names:
            if nm.startswith('__'): continue
            ins=pw[p][nm]  # occurrences in own file (incl def)
            others=pc[nm]-ins
            tcount=tc[nm]
            if others==0 and ins<=1:   # only the definition, nowhere else in prod
                out.append((p,n.lineno,nm,'prod_refs_elsewhere=0','own_refs=%d'%ins,'test/tool/doc_refs=%d'%tcount))
for o in sorted(out): print(*o)
