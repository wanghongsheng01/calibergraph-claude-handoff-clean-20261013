"""Fresh per-slot interpreter; native Z3 is created and owned by the parent broker."""
import array
import json
import os
from pathlib import Path
import socket
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE/'runtime_local'),str(HERE/'dependencies_local')]
from owned_processes import OwnedCase, Stopped
from replay import replay


def main():
    case_id,mode,fd,outpath,deadline=sys.argv[1:]
    out=Path(outpath);sock=socket.socket(fileno=int(fd))
    stages={k:None for k in ['imports','schema_C','parse','encode','search_including_solver','solver_calls','decode','replay']}
    nesting={};calls=[];protocol=[];proxies=[]
    result={'case':case_id,'mode':mode,'status':'STARTED','stages_seconds':stages}
    def timed(stage,fn):
        def wrapped(*args,**kwargs):
            outer=nesting.get(stage,0)==0;nesting[stage]=nesting.get(stage,0)+1;t=time.monotonic()
            try:return fn(*args,**kwargs)
            finally:
                nesting[stage]-=1
                if outer:stages[stage]=(stages[stage] or 0)+time.monotonic()-t
        return wrapped
    class Reader:
        def __init__(self,stream):self.stream=stream
        def readline(self,*a):
            line=self.stream.readline(*a)
            if not line or line.strip() in ('unknown','timeout'):
                state=line.strip() or 'EOF';protocol.append(state)
                raise RuntimeError('Z3_PROTOCOL_'+state)
            return line
        def close(self):self.stream.close()
    def broker_popen(argv,**kwargs):
        sock.send(json.dumps({'op':'spawn_z3','argv':argv,'fixture':case_id=='fixture'}).encode())
        data,anc,flags,addr=sock.recvmsg(4096,socket.CMSG_SPACE(2*array.array('i').itemsize))
        record=json.loads(data);fds=array.array('i')
        for level,typ,payload in anc:
            if level==socket.SOL_SOCKET and typ==socket.SCM_RIGHTS:fds.frombytes(payload)
        if not record.get('ok') or len(fds)!=2:raise RuntimeError('broker refused: '+repr(record))
        obj=type('RemotePipes',(),{})()
        obj.stdin=os.fdopen(fds[0],'w',buffering=1)
        obj.stdout=Reader(os.fdopen(fds[1],'r'))
        proxies.append(obj);return obj
    try:
        with OwnedCase(max(.001,min(12,float(deadline)-time.monotonic()))) as guard:
            if case_id=='fixture':
                p=broker_popen(['z3','-version']);result['version']=p.stdout.readline().strip()
                result['status']='FIXTURE_OK'
            else:
                t=time.monotonic()
                import polygon.environment as environment
                import polygon.smt.provers.smtlibv2 as smt
                from polygon.smt.formula import FormulaManager
                from polygon.ast.node import Node
                from polygon.visitors.query_encoder import QueryEncoder
                from polygon.sql_parser import SQLParser
                stages['imports']=time.monotonic()-t
                smt.Popen=broker_popen
                for name in ['parse','parse_query']:
                    setattr(SQLParser,name,timed('parse',getattr(SQLParser,name)))
                original_accept=Node.accept
                def accept(node,visitor):
                    if isinstance(visitor,QueryEncoder):return timed('encode',original_accept)(node,visitor)
                    return original_accept(node,visitor)
                Node.accept=accept
                environment.Environment.o1_eq_o2=timed('encode',environment.Environment.o1_eq_o2)
                for name in ['search','solve_precise']:
                    setattr(FormulaManager,name,timed('search_including_solver',getattr(FormulaManager,name)))
                original_check=smt.SMTLIBv2.check
                def check(prover,formula):
                    index=len(calls);row={'index':index,'state':'STARTED'};calls.append(row)
                    (out/f'formula_{index}.smt2').write_text(formula)
                    t=time.monotonic()
                    try:
                        value=original_check(prover,formula);row['state']='SAT' if value else 'UNSAT';return value
                    except BaseException as e:
                        row['state']='ERROR';row['error']=repr(e);raise
                    finally:row['elapsed_s']=time.monotonic()-t
                smt.SMTLIBv2.check=timed('solver_calls',check)
                smt.SMTLIBv2.evaluate_table=timed('decode',smt.SMTLIBv2.evaluate_table)
                inventory=json.loads((HERE/'inputs_local'/f'{case_id}.json').read_text())
                schema=[]
                for table in inventory['tables']:
                    schema.append({'TableName':table['table'],'PKeys':[],'FKeys':[],
                                   'Others':[{'Name':c['name'],'Type':{'INTEGER':'int','TEXT':'varchar'}[c['source_type']]} for c in table['columns']]})
                constraints=inventory['proposed_polygon_constraint_entries']
                t=time.monotonic();env=environment.Environment(schema,constraints,bound=1,time_budget=3)
                stages['schema_C']=time.monotonic()-t
                result['schema_C']={'tables':len(schema),'columns':sum(len(t['Others']) for t in schema),
                                    'constraints':len(constraints),'all_source_columns_kept':True,
                                    'constraint_kinds':sorted({next(iter(c)) for c in constraints}),
                                    'auxiliary_integrity_list_not_appended':True}
                case_dir=HERE/'inputs_local'/case_id
                gold=(case_dir/'gold.sql').read_text();pred=(case_dir/'predicted.sql').read_text()
                raw=env.check(gold,pred,use_precise_encoding=mode=='precise',solver_timeout_seconds=3)
                result['raw_return']=raw;result['status']='PIPELINE_'+str(raw[4].get('status'))
                if protocol:result['status']='Z3_'+protocol[-1].upper()
                elif raw[4].get('status')=='EQU':result['status']='BOUNDED_SYMBOLIC_UNSAT'
                elif raw[4].get('status')=='NEQ':
                    (out/'witness.json').write_text(json.dumps(raw[1],indent=2)+'\n')
                    try:
                        result['replay']=timed('replay',replay)(case_dir,inventory,raw[1])
                        result['status']='VALIDATED_NEQ' if result['replay']['different'] else 'WITNESS_NOT_DISTINGUISHING'
                    except Exception as e:
                        result['replay_error']=repr(e);result['status']='WITNESS_REPLAY_INVALID'
                result['interpretation']='N=1 symbolic typed fragment; no whole SQLite-domain equivalence claim'
    except Stopped as e:result.update(status='CASE_STOP',error=str(e))
    except NotImplementedError as e:result.update(status='UNSUPPORTED',error=repr(e))
    except BaseException as e:result.update(status='ERROR',error=repr(e),traceback=traceback.format_exc())
    finally:
        for p in proxies:
            for stream in [p.stdin,p.stdout]:
                try:stream.close()
                except Exception:pass
        sock.close()
        result['solver_calls']=calls;result['protocol_events']=protocol
        if 'guard' in locals():result['self_guard']=guard.receipt()
        (out/'RESULT.json').write_text(json.dumps(result,indent=2,default=str)+'\n')


if __name__=='__main__':main()
