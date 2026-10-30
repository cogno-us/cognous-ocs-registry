"""Physical lines, and code lines (lines holding at least one non-docstring, non-comment token) per module. Usage: python loc.py files..."""
import sys, tokenize, ast, io
tot_p = tot_c = 0
for f in sys.argv[1:]:
    src = open(f).read()
    doc_lines = set()
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str):
            d = n.body[0]
            doc_lines.update(range(d.lineno, d.end_lineno + 1))
    code = set()
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER, tokenize.ENCODING): continue
        for ln in range(tok.start[0], tok.end[0] + 1):
            if ln not in doc_lines: code.add(ln)
    p = src.count("\n") + (0 if src.endswith("\n") else 1)
    tot_p += p; tot_c += len(code)
    print(f"{len(code):5d} code / {p:5d} physical  {f}")
print(f"{tot_c:5d} code / {tot_p:5d} physical  TOTAL")
