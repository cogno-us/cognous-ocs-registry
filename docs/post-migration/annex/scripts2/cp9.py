import ast, glob, os, collections, sys
T="/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/cognous-control-plane/tests/"
groups=collections.defaultdict(list); nfun=0
class Strip(ast.NodeTransformer):
    def visit_FunctionDef(self,n):
        self.generic_visit(n); n.name="F"
        if n.body and isinstance(n.body[0],ast.Expr) and isinstance(getattr(n.body[0],"value",None),ast.Constant) and isinstance(n.body[0].value.value,str):
            n.body=n.body[1:] or [ast.Pass()]
        return n
    visit_AsyncFunctionDef=visit_FunctionDef
for f in sorted(glob.glob(T+"*.py")):
    src=open(f).read()
    try: tree=ast.parse(src)
    except Exception as e: print("parse fail",f); continue
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            nfun+=1
            L=n.end_lineno-n.lineno+1
            if L<4: continue
            import copy
            m=Strip().visit(copy.deepcopy(n))
            key=ast.dump(m,annotate_fields=False)
            groups[key].append((os.path.basename(f),n.lineno,L,n.name))
tot=0; gs=[]
for k,v in groups.items():
    files={x[0] for x in v}
    if len(v)>1:
        red=sum(x[2] for x in v[1:])
        gs.append((red,v)); tot+=red
gs.sort(key=lambda x:-x[0])
print("functions",nfun,"identical groups",len(gs),"redundant lines",tot)
# restrict to groups spanning >=2 files, and to governed-layer test files
gov=("test_f4_age","test_f5_class","test_governed_policy","test_revocation_fam","test_irreversibility","test_final3","test_effective_configuration","d06_","final3_")
cross=0; govcross=0
for red,v in gs:
    files={x[0] for x in v}
    if len(files)>1:
        cross+=red
    if len(files)>1 and all(x[0].startswith(gov) for x in v): govcross+=red
print("cross-file redundant",cross,"governed-only cross-file redundant",govcross)
for red,v in gs[:20]:
    print(red,[ (a,b,c,d) for a,b,c,d in v])

print("---- free-name analysis (names read that are not params/locals/builtins/self.attr)")
import builtins, copy
def free(n):
    assigned=set(a.arg for a in n.args.args+n.args.kwonlyargs+n.args.posonlyargs)
    if n.args.vararg: assigned.add(n.args.vararg.arg)
    if n.args.kwarg: assigned.add(n.args.kwarg.arg)
    loads=set()
    for x in ast.walk(n):
        if isinstance(x,ast.Name):
            if isinstance(x.ctx,ast.Store): assigned.add(x.id)
            else: loads.add(x.id)
        elif isinstance(x,(ast.FunctionDef,ast.Lambda)) and x is not n:
            if isinstance(x,ast.FunctionDef): assigned.add(x.name)
            for a in x.args.args: assigned.add(a.arg)
        elif isinstance(x,ast.ExceptHandler) and x.name: assigned.add(x.name)
        elif isinstance(x,ast.comprehension):
            for t in ast.walk(x.target):
                if isinstance(t,ast.Name): assigned.add(t.id)
    return sorted(l for l in loads if l not in assigned and not hasattr(builtins,l))
trees={}
for red,v in gs:
    f,ln,L,name=v[0]
    t=trees.setdefault(f,ast.parse(open(T+f).read()))
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.lineno==ln:
            print(red,name,"free:",free(n)); break
