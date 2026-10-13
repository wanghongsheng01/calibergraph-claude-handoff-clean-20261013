from pathlib import Path
import shutil,difflib
H=Path(__file__).resolve().parent
shutil.copytree(H/'patched_p2',H/'patched_p3')
f=H/'patched_p3/polygon/sql_parser.py';s=f.read_text()
for token in ["attr['filter']","select_clause['filter']","exp['filter']"]:
 old=f'self.parse_expression({token})';assert s.count(old)==1;s=s.replace(old,f'self.parse_aggregate_filter({token})')
needle='    def parse_expression(self, exp) -> Expression | Literal:\n'
assert s.count(needle)==1
s=s.replace(needle,"    def parse_aggregate_filter(self, predicate):\n        # Bare FILTER strings are column references; quoted literals remain dicts.\n        return Attribute(predicate) if isinstance(predicate, str) else self.parse_expression(predicate)\n\n"+needle)
f.write_text(s)
orig=H.parent/'calibergraph_polygon_pilot_20261012_13/runtime_local/polygon';patch=''
for rel in ['sql_parser.py','visitors/expression_encoder.py','visitors/group_expression_encoder.py']:
 a=(orig/rel).read_text();b=(H/'patched_p3/polygon'/rel).read_text();patch+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/polygon/'+rel,tofile='b/polygon/'+rel))
(H/'COUNT_P3.patch').write_text(patch)
s=(H/'parser_test.py').read_text()
s=s.replace("        ta,a=self.evaluate(n.a);tb,b=self.evaluate(n.b)\n        if k=='Implies':assert ta==tb=='Bool';return 'Bool',(not a) or b", "        if k=='Implies':\n            ta,a=self.evaluate(n.premise);tb,b=self.evaluate(n.conclusion);assert ta==tb=='Bool';return 'Bool',(not a) or b\n        ta,a=self.evaluate(n.a);tb,b=self.evaluate(n.b)")
s=s.replace('self.db=Database();self.formulas=Formulas();self.counter=0','self.db=Database();self.formulas=Formulas();self.counter=0;self.string_hash_table={};self.hash_string_table={}')
s=s.replace('    def next_table_id(self):', '''    def string_hash(self, string):
        # Verbatim behavior of frozen Environment.string_hash, no Environment import.
        if not isinstance(string,str):string=str(string)
        if string in self.string_hash_table:return self.string_hash_table[string]
        try:h=int(string)
        except:h=hash(string)
        self.string_hash_table[string]=h;self.hash_string_table[h]=string
        return h
    def next_table_id(self):''')
s=s.replace('p=SQLParser();raw=p.parse(sql);','p=CURRENT_PARSER();raw=p.parse(sql);')
s=s.replace("def classes(ver):\n", "def classes(ver):\n    global CURRENT_PARSER\n")
s=s.replace("    em=types.ModuleType('isolated_'+ver+'_expr');", "    pm=types.ModuleType('isolated_'+ver+'_parser');exec(compile((base/'sql_parser.py').read_text(),str(base/'sql_parser.py'),'exec'),pm.__dict__);CURRENT_PARSER=pm.SQLParser\n    em=types.ModuleType('isolated_'+ver+'_expr');")
s=s.replace("['original','p1','p2']","['original','p1','p2','p3']").replace("H/'PARSER_RESULTS.json'","H/'PARSER_RESULTS_V2.json'")
s=s.replace("'parser_source_unchanged':True","'parser_source_changes':'original/P1/P2 unchanged; P3 explicit aggregate FILTER bare identifier fix'")
(H/'parser_test_v2.py').write_text(s)
