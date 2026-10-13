from pathlib import Path
import difflib,hashlib,json,shutil
H=Path(__file__).resolve().parent;P=H.parent/'calibergraph_polygon_pilot_20261012_13/runtime_local/polygon'
for version in ['p1','p2']:
 d=H/('patched_'+version)/'polygon';shutil.copytree(P,d,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 f=d/'visitors/expression_encoder.py';s=f.read_text();old='                            indicators.append(Not(deleted))\n';new='                        indicators.append(If(Not(deleted), Int(1), Int(0)))\n';assert s.count(old)==1;f.write_text(s.replace(old,new))
f=H/'patched_p2/polygon/visitors/group_expression_encoder.py';s=f.read_text()
old='''                    in_groups = [SMTGrouping(self.groupby_table.table_id, tuple_id, self.group_id)
                                 for tuple_id in range(self.input_table.bound)]
                    return Sum([If(in_group, Int(1), Int(0)) for in_group in in_groups]), Bool(False)
'''
new='''                    indicators = []
                    agg_exp_encoder = ExpressionEncoder(self.input_table, self.env)
                    for tuple_id in range(self.input_table.bound):
                        in_group = SMTGrouping(self.groupby_table.table_id, tuple_id, self.group_id)
                        if node.filter_clause is not None:
                            filter_val, filter_null = agg_exp_encoder.expression_for_tuple(node.filter_clause, tuple_id)
                            in_group = And([in_group, Not(filter_null), EnsureBool(filter_val)])
                        indicators.append(If(in_group, Int(1), Int(0)))
                    return Sum(indicators), Bool(False)
'''
assert s.count(old)==1;f.write_text(s.replace(old,new))
for ver in ['p1','p2']:
 patch=''
 for file in ['expression_encoder.py','group_expression_encoder.py']:
  a=(P/'visitors'/file).read_text();b=(H/('patched_'+ver)/'polygon/visitors'/file).read_text()
  patch+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/polygon/visitors/'+file,tofile='b/polygon/visitors/'+file))
 (H/('COUNT_'+ver.upper()+'.patch')).write_text(patch)
print('Prepared two isolated copies; no imports/execution of target.')
