#!/usr/bin/env python3
"""Static stdlib inventory; never import a SQL parser, driver, solver, or target code."""
import csv, hashlib, json, re, resource
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('/Users/loctek/Documents/Codex/2026-10-11/task-3')
OLD = Path('/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009')
OUT = Path(__file__).resolve().parent
MAX_FILE = 32 * 1024 * 1024
MAX_LINE = 1024 * 1024
# Bound CPU and file reads; only digests/counters retained for JSONL records.
resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
provenance = {}

def digest(b): return hashlib.sha256(b).hexdigest()
def canon(x): return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
def sig(x): return digest(canon(x))
def register(p):
    p = p.resolve()
    if p.stat().st_size > MAX_FILE: raise ValueError('file size cap exceeded: '+str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(65536), b''): h.update(block)
    provenance[str(p)] = {'bytes': p.stat().st_size, 'sha256': h.hexdigest()}
    return p
def obj(p): return json.loads(register(p).read_text())
def records(p):
    with register(p).open('rb') as f:
        while True:
            line = f.readline(MAX_LINE+1)
            if not line: break
            if len(line)>MAX_LINE: raise ValueError('line size cap exceeded')
            if line.strip(): yield json.loads(line)
def summary(c):
    return {'unique':len(c), 'repeated_distinct':sum(n>1 for n in c.values()),
            'repeat_excess':sum(n-1 for n in c.values()), 'max_multiplicity':max(c.values(),default=0)}
class Group:
    def __init__(self):
        self.n=0; self.pairs=Counter(); self.unordered=Counter();self.sql=Counter();self.left=Counter();self.right=Counter()
        self.schema=Counter();self.ic=Counter();self.context=Counter();self.db=Counter();self.family=Counter()
        self.lex=Counter();self.literal_template=Counter();self.identical=0
    def add(self,a,b,schema,ic,context,db=None,family=None):
        self.n+=1
        ah,bh=digest(a.encode()),digest(b.encode())
        self.pairs[(ah,bh)]+=1;self.unordered[tuple(sorted((ah,bh)))]+=1
        self.sql.update([ah,bh]);self.left[ah]+=1;self.right[bh]+=1
        self.schema[schema]+=1;self.ic[ic]+=1;self.context[context]+=1
        if db is not None:self.db[db]+=1
        if family is not None:self.family[family]+=1
        self.identical += a==b
        for q in (a,b):
            # Deliberately lexical, not parsed/semantic structure. Keep raw spacing and case.
            masked=re.sub(r"'(?:''|[^'])*'", "'?'",q)
            masked=re.sub(r'\b\d+(?:\.\d+)?\b','?',masked)
            self.literal_template[digest(masked.encode())]+=1
            toks=set(re.findall(r'\b(?:SELECT|FROM|JOIN|WHERE|GROUP|HAVING|ORDER|LIMIT|UNION|DISTINCT|SUM|COUNT|AVG|MIN|MAX)\b',q.upper()))
            self.lex[' '.join(sorted(toks))]+=1
    def row(self):
        out={'records':self.n,'query_slots':2*self.n,'schema_signatures':len(self.schema),
             'ic_signatures':len(self.ic),'schema_ic_signatures':len(self.context),'dbids':len(self.db),
             'source_family_keys':len(self.family),'identical_sides_records':self.identical}
        for name,c in [('ordered_pair',self.pairs),('unordered_pair',self.unordered),('sql',self.sql),('left_sql',self.left),('right_sql',self.right),('lexical_keyword_set',self.lex),('lexical_literal_mask',self.literal_template)]:
            out.update({name+'_'+k:v for k,v in summary(c).items()})
        out['multi_record_schema_ic_groups']=sum(n>1 for n in self.context.values())
        out['records_in_multi_record_schema_ic_groups']=sum(n for n in self.context.values() if n>1)
        return out

datasets=defaultdict(Group); contexts=defaultdict(Group); dbgroups=defaultdict(Group); families=defaultdict(Group)
metadata_keys=defaultdict(Counter)
def add(ds,a,b,s,ic,db=None,family=None):
    sh,ih,ch=sig(s),sig(ic),sig([s,ic])
    for group in (datasets[ds],contexts[(ds,ch)]):group.add(a,b,sh,ih,ch,db,family)
    if db is not None:dbgroups[(ds,db)].add(a,b,sh,ih,ch,db,family)
    if family is not None:families[(ds,family)].add(a,b,sh,ih,ch,db,family)

parse=ROOT/'calibergraph_distinct_evidence_20261012_03'
schemas=obj(parse/'sources_local/schema.json')
ev=obj(parse/'EVIDENCE.json')
for r in records(parse/'sources_local/disprove-bird.jsonl'):
    metadata_keys['parseval_bird'].update(r.keys())
    # Full DDL strings include every declared IC; no IC extraction/normalization attempted.
    add('parseval_bird',r['gold'],r['predicted'],schemas[r['dbid']],{'IC_encoding':'embedded_in_full_DDL'},r['dbid'])

base=OLD/'today_20261011'
cut=obj(base/'experiments/PUBLIC_APPLICABILITY_FINAL_CUT.json')
source_rels={'verieql_leetcode':'public_leetcode/leetcode.jsonlines',
             'verieql_calcite':'sources/verieql_v1/benchmarks/calcite/calcite2.jsonlines',
             'verieql_literature':'sources/verieql_v1/benchmarks/literature/literature-rewrite.jsonlines'}
for ds,rel in source_rels.items():
    p=base/rel
    for r in records(p):
        metadata_keys[ds].update(r.keys())
        a,b=r['pair']
        family=r.get('file') if ds=='verieql_leetcode' else r.get('name') if ds=='verieql_literature' else None
        add(ds,a,b,r['schema'],r['constraint'],family=family)
        add('verieql_combined_48910_slots',a,b,r['schema'],r['constraint'],family=(ds+':'+family) if family else None)
    expected=cut['file_provenance'].get(str(p))
    if expected: assert provenance[str(p)]['sha256']==expected['sha256'],str(p)

# Legacy source copies are traceable via the prior manifest. No outcomes are inspected.
legacy=OLD/'work_failure'
manifest=obj(legacy/'input_manifest.json')
register(base/'FINAL_LINEAGE_AND_LEGACY_DENOMINATOR.zh.md')
gold=obj(legacy/'inputs/p08_gold_full.json')['cases']
prompt=register(legacy/'inputs/prompt_schema.sql').read_text()
legacy_tasks={};legacy_questions=Counter()
for condition in ['A','B','C']:
    rows=obj(legacy/f'inputs/raw_deepseek_deepseek-chat_{condition}.json')
    assert len(rows)==len(gold)==496
    tasks=Counter()
    for r,g in zip(rows,gold):
        assert (r['task'],r['question'])==(g['task'],g['question'])
        tasks[r['task']]+=1;legacy_questions[digest(r['question'].encode())]+=1
        # Only a common prompt is established, not a full production schema/IC snapshot.
        add('legacy_prompt_'+condition,g['gold_sql'],r['sql'],prompt,{'complete_production_IC':'unknown'},family=r['task'])
        add('legacy_prompt_ABC',g['gold_sql'],r['sql'],prompt,{'complete_production_IC':'unknown'},family=r['task'])
    legacy_tasks[condition]=dict(tasks)
for m in manifest:
    if m.get('copy') and m.get('copy_sha256'):
        p=str((legacy/m['copy']).resolve())
        if p in provenance: assert provenance[p]['sha256']==m['copy_sha256'],p
for m in ev['local_sources']:
    p=str((parse/m['path']).resolve())
    if p in provenance: assert provenance[p]['sha256']==m['sha256'],p

def csvwrite(name,rows):
    rows=list(rows)
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def scoped(ds,g):
    row=g.row()
    row['signature_scope']='complete_supplied_schema_plus_complete_supplied_constraint_object'
    row['prompt_context_signatures']=None
    if ds=='parseval_bird':
        row['signature_scope']='complete_DDL_including_embedded_IC; separate_IC_only_count_unavailable'
        row['ic_signatures']=None
    if ds.startswith('legacy_prompt'):
        row['signature_scope']='common_prompt_only; complete_production_schema_and_IC_unknown'
        row['prompt_context_signatures']=len(g.context)
        for k in ['schema_signatures','ic_signatures','schema_ic_signatures','multi_record_schema_ic_groups','records_in_multi_record_schema_ic_groups']:row[k]=None
    return row
summary_rows=[dict(dataset=k,**scoped(k,v)) for k,v in datasets.items()]
csvwrite('dataset_summary.csv',summary_rows)
csvwrite('schema_ic_batches.csv',(dict(dataset=ds,schema_ic_sha256=s,schema_sha256=next(iter(g.schema)),ic_sha256=next(iter(g.ic)) if ds!='parseval_bird' else '',**scoped(ds,g)) for (ds,s),g in sorted(contexts.items()) if not ds.startswith('legacy_prompt')))
csvwrite('legacy_prompt_batches.csv',(dict(dataset=ds,prompt_context_sha256=s,**scoped(ds,g)) for (ds,s),g in sorted(contexts.items()) if ds.startswith('legacy_prompt')))
csvwrite('dbid_batches.csv',(dict(dataset=ds,dbid=s,**scoped(ds,g)) for (ds,s),g in sorted(dbgroups.items())))
csvwrite('source_family_batches.csv',(dict(dataset=ds,source_family=s,**scoped(ds,g)) for (ds,s),g in sorted(families.items())))
result={'method':'static stdlib read/hash/count only; all source rows included; outcome fields neither used for grouping nor selection',
 'limits':{'max_source_file_bytes':MAX_FILE,'max_jsonl_line_bytes':MAX_LINE,'cpu_seconds':45,'retained':'hashes and counters; source JSONL streamed'},
 'signatures':'SHA256 of JSON sorted object keys, exact scalar strings, original list order retained; schema+IC includes complete supplied schema and constraint object; no semantic normalization',
 'sql_identity':'exact UTF-8 string SHA256; unordered pairs sort the two hashes; no whitespace, case, alias, or SQL-semantic normalization',
 'parseval_IC':'ICs embedded in full original DDL; separate IC-only signature unavailable without parsing. Schema+IC uses all DDL strings, not a case-selected subset.',
 'parseval_commit':ev['source_commit'],
 'source_family_definition':'LeetCode file = problem source key; literature name = published example key; neither denotes production version lineage. Calcite benchmark strings identify individual rules/cases and are not merged into inferred families.',
 'lexical_overlap_limit':'keyword-set and literal-masked-string counts only; quoted identifiers/comments can cause false matches. No AST/subgraph, semantic reuse, speedup, eligibility or outcome inference.',
 'legacy_scope':'traceable 496 question rows x conditions A/B/C; common frozen prompt only. Exact full production schema/IC, independently evolved versions and authoritative production lineage NOT established. Gold means source field name, not validated truth.',
 'legacy_tasks':legacy_tasks,'legacy_question_strings':summary(legacy_questions),
 'metadata_field_presence':{k:dict(v) for k,v in metadata_keys.items()},
 'dataset_summary':summary_rows,
 'verieql_declared_denominator':cut['full_denominators'],
 'initial_inspection_disclosure':'Some existing outcome values were incidentally displayed while locating/inspecting file formats; no label analysis, stratification, or outcome-based selection was performed. Counting script uses only source/schema/constraint/SQL/question/task metadata.',
 'conclusions':{'same_complete_supplied_schema_IC_multiquery_public_batches_established':True,'independent_real_business_version_batches_established':False,'new_experiments':0,'outcome_selection':False,'development_data_already_exposed':True},
 'provenance':provenance}
assert datasets['parseval_bird'].n==1534
assert datasets['verieql_combined_48910_slots'].n==24455
(OUT/'inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(OUT/'artifact_manifest.json').write_text(json.dumps({p.name:{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ['artifact_manifest.json','run_stdout.json']},indent=2)+'\n')
print(json.dumps(summary_rows,indent=2))
