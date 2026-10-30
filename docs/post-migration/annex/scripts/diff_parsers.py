"""Differential check (not a test-suite run) of the four private strict-int JSON parsers and the three record-map extractors.
Compares: registry_effective_policy._strict_pairs/_reject_number, f5age, unreadable, revocation copies on a corpus; and f5age.registry_class_map / unreadable.registry_unreadable_map
against registry_revocation_governance._record_payload plus the family's value predicate."""
import sys, json, random, itertools
sys.path.insert(0, "src")
import agent_control_plane.registry_effective_policy as ep
import agent_control_plane.registry_f5_class_age_governance as a
import agent_control_plane.registry_f5_class_unreadable_governance as u
import agent_control_plane.registry_revocation_governance as r
mods = {"effective_policy": ep, "f5age": a, "unreadable": u, "revocation": r}
def parse(m, text):
    try:
        return ("ok", json.loads(text, object_pairs_hook=m._strict_pairs, parse_float=m._reject_number, parse_constant=m._reject_number))
    except Exception as e:
        return ("err", type(e).__name__)   # exception TEXT differs ("non-integer"/"non-string"); callers catch Exception and discard it
base = ['{"payload":{"class_status_max_age_seconds":{"a":30}}}', '{"payload":{"x":1.5}}', '{"payload":{"x":NaN}}', '{"a":1,"a":2}', '{"payload":{"x":1e2}}', '[1,2]', '', '{"payload":{"class_on_unreadable":{"c":"refuse"}}}',
        '{"payload":{"class_on_unreadable":{"c":"refuse","c":"refuse"}}}', '{"payload":{"x":-0}}', '{"payload":{"x":Infinity}}', '{"payload":{"x":1E5}}', '{"payload":{"x":"\\ud800"}}']
random.seed(1)
def mutate(s):
    s = list(s)
    for _ in range(random.randint(1, 3)):
        if not s: break
        i = random.randrange(len(s)); op = random.choice("dir")
        if op == "d": del s[i]
        elif op == "i": s.insert(i, random.choice('{}[]",:.0123456789eEnNaIf-+ '))
        else: s[i] = random.choice('{}[]",:.0123456789eE-+ ')
    return "".join(s)
corpus = list(base) + [mutate(random.choice(base)) for _ in range(20000)]
bad = 0
for t in corpus:
    outs = {k: parse(m, t) for k, m in mods.items()}
    if len({json.dumps(v, sort_keys=True, default=str) for v in outs.values()}) != 1: bad += 1
print("parser corpus", len(corpus), "disagreements among the 4 private parsers:", bad)
# extractors
dis = 0
for t in corpus:
    got_a = a.registry_class_map(t)
    pay = r._record_payload(t, a.FIELD)
    ref_a = pay if (type(pay) is dict and pay and all(type(k) is str and type(v) is int and 1 <= v <= a.SCALAR_MAX for k, v in pay.items())) else None
    got_u = u.registry_unreadable_map(t)
    pay_u = r._record_payload(t, u.FIELD)
    ref_u = pay_u if (type(pay_u) is dict and pay_u and all(type(k) is str and u._value(v) for k, v in pay_u.items())) else None
    if got_a != ref_a or got_u != ref_u: dis += 1
print("extractor corpus", len(corpus), "disagreements (registry_class_map / registry_unreadable_map vs _record_payload + predicate):", dis)
