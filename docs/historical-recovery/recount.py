#!/usr/bin/env python3
"""Read-only recount for docs/historical-recovery (non-authorizing).

Usage: python3 -I recount.py SOURCE_REPO_ROOT REGISTRY_REPO_ROOT

SOURCE_REPO_ROOT   clone of cogno-us/cognous-open-control-stack (catalogue + its validator)
REGISTRY_REPO_ROOT clone of cogno-us/cognous-ocs-registry (docs/s02-evidence/W*.md)

It decodes the committed catalogue with the catalogue's own validator code (read-only),
recomputes every number quoted in this directory and prints them as JSON.
It executes no rule, scenario or test and writes nothing.
"""
import collections, glob, json, os, re, sys

src, reg = sys.argv[1], sys.argv[2]
cat = os.path.join(src, 'docs/mvp-recovery/registry/catalogue-v0.1')
sys.path.insert(0, os.path.join(src, 'docs/mvp-recovery/registry/tools'))
import validate_registry as v  # the catalogue's own decoder (read-only use)

rep = v.Report()
manifest, L = v.load_registry(cat, rep, v.load_schemas(cat, rep))
R, S, T, F, E = (L[k] for k in ('rules', 'scenarios', 'tests', 'fixtures', 'evidence'))
C = collections.Counter
out = {'manifest_digest': manifest['digest'], 'decode_problems': len(getattr(rep, 'items', []) or [])}
out['layer_counts'] = {k: len(x) for k, x in L.items()}
out['layer_counts_match_manifest'] = out['layer_counts'] == manifest['layer_counts']

# --- eight-category mapping (DERIVED here; catalogue attributes are not source-verified) ---
def category(x):
    nt, ad = x['normative_type'], x['adoption_status']
    if nt == 'reason_code_or_refusal_vocabulary': return 'C4 reason codes / refusal vocabulary'
    if nt in ('constitutional_floor', 'principle', 'requirement_row', 'advisory'): return 'C1 governance policy rules (as stated)'
    if nt in ('mandatory', 'validator_rule'): return 'C2 mandatory / enforcement candidates (source-stated; enforcement NOT established)'
    if nt == 'decision' or ad == 'proposed_not_adopted': return 'C7 historical proposals / decisions'
    return 'C8 unresolved / unattributed (normative strength not stated)'
out['rules_by_category'] = dict(C(category(x) for x in R))
out['rules_by_category']['C3 configurable policy parameters'] = 0
out['rules_by_normative_type'] = dict(C(x['normative_type'] for x in R))
out['rules_by_adoption'] = dict(C(x['adoption_status'] for x in R))
out['rules_by_release_scope'] = dict(C(x['release_scope'] for x in R))
out['rules_by_mvp_applicability'] = dict(C(x['mvp_applicability']['value'] for x in R))
out['rules_by_repo'] = dict(C(x['source']['repo'].split('/')[1] for x in R))
out['non_rule_layers'] = {
    'scenarios': len(S), 'scenario_release_scope': dict(C(x['release_scope'] for x in S)),
    'scenario_class': dict(C(x['scenario_class'] for x in S)),
    'tests': len(T), 'parametrized_instances': sum(t.get('parametrized_instance_count') or 0 for t in T),
    'fixtures': len(F), 'evidence_records': len(E), 'evidence_kind': dict(C(e.get('evidence_kind') for e in E)),
    'coverage_rows': len(L['coverage'])}
reg_label = lambda x: x['annotations'].get('normative_subtype', '')
r01 = [x for x in R if reg_label(x).startswith('runtime-authority-reasons/0.1')]
r02 = [x for x in R if reg_label(x).startswith('runtime-authority-reasons/0.2')]
out['runtime_authority_reasons'] = {'0.1_entries': len(r01), '0.2_entries': len(r02)}
out['reason_code_entries'] = sum(1 for x in R if x['normative_type'] == 'reason_code_or_refusal_vocabulary')
out['reason_code_distinct_names'] = len({i for x in R if x['normative_type'] == 'reason_code_or_refusal_vocabulary' for i in x['native_ids']})
out['rules_with_program_v0_2_source_path'] = sum(1 for x in R if 'program-v0.2' in x['source']['path'])
stm = collections.defaultdict(list)
for x in R: stm[x['statement_verbatim'].strip()].append(x['source']['repo'])
dg = {k: v_ for k, v_ in stm.items() if len(v_) > 1}
out['duplicate_statement_groups'] = {'groups': len(dg), 'entries': sum(len(v_) for v_ in dg.values()),
                                     'cross_repo_groups': sum(1 for v_ in dg.values() if len(set(v_)) > 1)}
nid = collections.defaultdict(set)
for x in R:
    for i in x['native_ids']: nid[i].add(x['source']['repo'])
out['native_ids_in_more_than_one_repo'] = sum(1 for s in nid.values() if len(s) > 1)
out['rules_with_alias_candidates'] = sum(1 for x in R if x['alias_candidates'])
out['rules_with_aliases'] = sum(1 for x in R if x['aliases'])
out['unresolved_accounting'] = manifest['unresolved_accounting']

# --- S02 (620 rows) ---
cls = ('MANDATORY-INVARIANT', 'SERIALIZATION-OR-EVIDENCE', 'INCIDENTAL-CONDITIONAL',
       'REFUSAL-OR-REASON-VOCABULARY', 'CONFIGURABLE-CANDIDATE', 'UNRESOLVED')
rows = []
for f in sorted(glob.glob(os.path.join(reg, 'docs/s02-evidence/W*.md'))):
    for line in open(f, encoding='utf-8'):
        m = re.match(r'\|\s*(W\d-\d+)\s*\|', line)
        if m:
            cells = [c.strip() for c in re.split(r'(?<!\\)\|', line.strip().strip('|'))]
            k = [c for c in cells if c in cls]
            if len(k) == 1: rows.append({'id': m.group(1), 'cls': k[0], 'cells': cells})
out['s02_rows'] = len(rows)
out['s02_by_class'] = dict(C(r['cls'] for r in rows))
out['s02_unresolved_ids'] = sorted(r['id'] for r in rows if r['cls'] == 'UNRESOLVED')
tok = re.compile(r'([a-z][a-z0-9]*(?:_[a-z0-9]+)+)')
names = {i for x in R if x['normative_type'] == 'reason_code_or_refusal_vocabulary' for i in x['native_ids']}
ov = collections.defaultdict(set)
for r in rows:
    for t in set(tok.findall(' '.join(r['cells'][1:4]))):
        if t in names: ov[r['cls']].add(t)
out['code_name_string_overlap_by_s02_class'] = {k: len(s) for k, s in ov.items()}
out['code_name_string_overlap_distinct'] = len(set().union(*ov.values())) if ov else 0
out['s02_unresolved_rows_with_overlap'] = sorted(r['id'] for r in rows if r['cls'] == 'UNRESOLVED'
        and any(t in names for t in tok.findall(' '.join(r['cells'][1:4]))))
paths = {x['source']['path'] for x in R}
out['catalogue_paths_by_basename_in_s02_sources'] = sorted({p for p in paths if p.endswith('manifest_validation.py')})
lead = {
 'F1': r'allowed_units|allowed_adapters|allowed_actions|allowed_institutions|authority_domains|max_amount|max_effects|allowed_target_prefixes|LocalExecutionPolicy',
 'F2': r'target_match|legacy-prefix',
 'F3': r'max_text|MAX_|max_nodes|timeout',
 'F4': r'max_age|stale|status age|observation window|ObservationPolicy|freshness',
 'F5': r'on_unreadable|revocation assurance|holder inventory|runtime_authority',
 'F6': r'permissions\.json|agent permission',
 'F7': r'dedupe',
 'F8': r'demo_policies|demo polic',
 'F9': r'tenant.{0,20}length',
 'F10': r'rule_revision|trend',
 'F11': r'redact'}
out['lexical_leads_not_matches'] = {}
for f, p in lead.items():
    rx = re.compile(p, re.I)
    h = [x for x in R if rx.search(x['statement_verbatim'] + ' ' + ' '.join(x['native_ids']) + ' ' + (x.get('title') or ''))]
    out['lexical_leads_not_matches'][f] = {'pattern': p, 'entries': len(h), 'by_normative_type': dict(C(x['normative_type'] for x in h))}
print(json.dumps(out, indent=1, sort_keys=True))
