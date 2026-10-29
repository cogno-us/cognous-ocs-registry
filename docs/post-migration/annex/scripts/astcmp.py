import ast,re,sys,itertools,difflib
def code(p):
    t=ast.parse(open(p).read())
    for n in ast.walk(t):
        if isinstance(n,(ast.Module,ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef)) and n.body and isinstance(n.body[0],ast.Expr) and isinstance(getattr(n.body[0],'value',None),ast.Constant) and isinstance(n.body[0].value.value,str):
            n.body=n.body[1:] or [ast.Pass()]
    s=ast.unparse(t)
    s=re.sub(r'r08-v\d','r08-vN',s); s=re.sub(r'(?<![A-Za-z0-9])([vV])[3-8](?![0-9])',r'\1N',s); s=re.sub(r'([vV])[3-8]_',r'\1N_',s); s=re.sub(r'_([vV])[3-8](?![0-9])',r'_\1N',s)
    return s.splitlines()
fs=sys.argv[1:]
for a,b in itertools.combinations(fs,2):
    A,B=code(a),code(b)
    sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
    same=sum(s.size for s in sm.get_matching_blocks())
    print(a,b,len(A),len(B),'identical' if A==B else f'{same} common lines = {round(100*same/max(len(A),len(B)),1)}%')
