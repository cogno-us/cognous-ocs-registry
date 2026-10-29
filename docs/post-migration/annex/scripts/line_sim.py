"""Line-level similarity between files. For files A,B: shared = number of lines of A (stripped, >=25 chars) whose stripped text also occurs in B; ratio = shared / (A lines >=25 chars).
Also difflib SequenceMatcher ratio over the full normalized line lists. Usage: python line_sim.py A B [C ...] (all pairs)"""
import sys, difflib, itertools, collections
def load(p): return [l.strip() for l in open(p).read().splitlines() if l.strip()]
fs = sys.argv[1:]
L = {f: load(f) for f in fs}
for a, b in itertools.combinations(fs, 2):
    A, B = L[a], L[b]
    sb = set(x for x in B if len(x) >= 25)
    la = [x for x in A if len(x) >= 25]
    lb = [x for x in B if len(x) >= 25]
    sa = set(la)
    sh_a = sum(1 for x in la if x in sb); sh_b = sum(1 for x in lb if x in sa)
    r = difflib.SequenceMatcher(None, A, B, autojunk=False).ratio()
    print(f"{a} ({len(A)} nonblank) vs {b} ({len(B)}): shared-long-lines A->B {sh_a}/{len(la)} ({sh_a/len(la):.0%}); B->A {sh_b}/{len(lb)} ({sh_b/len(lb):.0%}); SequenceMatcher ratio {r:.3f}")
