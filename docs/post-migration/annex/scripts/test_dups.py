"""Static duplicate-function finder over tests/ (no test is executed). Usage: python test_dups.py <tests dir>"""
import ast, sys, hashlib, collections, pathlib, difflib
root = pathlib.Path(sys.argv[1])
def strip_doc(n):
    if n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str):
        n.body = n.body[1:] or [ast.Pass()]
groups = collections.defaultdict(list)
total_funcs = 0
for f in sorted(root.glob("*.py")):
    t = ast.parse(f.read_text())
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total_funcs += 1
            nl = (n.end_lineno - n.lineno + 1)
            c = ast.parse(ast.get_source_segment(f.read_text(), n).lstrip()) if False else None
            m = ast.FunctionDef(name="_", args=n.args, body=list(n.body), decorator_list=[], returns=None, type_comment=None)
            strip_doc(m)
            body = ast.dump(ast.Module(body=m.body, type_ignores=[]))
            if nl >= 4:
                groups[hashlib.sha1(body.encode()).hexdigest()].append((f.name, n.name, n.lineno, nl))
dups = {k: v for k, v in groups.items() if len({x[0] for x in v}) > 1 or len(v) > 1}
print("functions (all, incl. nested):", total_funcs)
tot_extra = 0
rows = []
for k, v in dups.items():
    nl = v[0][3]; extra = (len(v) - 1) * nl; tot_extra += extra
    rows.append((extra, nl, v))
rows.sort(key=lambda r: -r[0])
print("groups of byte-AST-identical functions (>=4 lines, name-independent, docstring-independent):", len(rows), " redundant lines:", tot_extra)
for extra, nl, v in rows[:25]:
    print(f"  {nl:3d} lines x{len(v)}  redundant={extra:4d}  " + "; ".join(f"{a}::{b}@{c}" for a, b, c, _ in v))
