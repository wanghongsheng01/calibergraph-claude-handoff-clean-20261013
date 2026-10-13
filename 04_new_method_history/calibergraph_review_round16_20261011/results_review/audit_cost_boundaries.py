"""Independent JSON/hash arithmetic audit only; never imports scientific code."""
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

WORK = Path(__file__).resolve().parents[2]
ROOT = WORK / 'calibergraph_next_20261011_16'
OUT = Path(__file__).resolve().parent
issues = []
inputs = {}

def raw(path):
    path = Path(path)
    data = path.read_bytes()
    inputs[str(path)] = hashlib.sha256(data).hexdigest()
    return data

def read(path):
    return json.loads(raw(path))

def check(condition, label):
    if not condition:
        issues.append(label)

def same(a, b, label):
    check(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9), label)

def stamp(value):
    return datetime.fromisoformat(value).timestamp()

schedule = read(ROOT/'scheduling/waiting_schedule.json')
observer_source_sha = hashlib.sha256(raw(ROOT/'scheduling/resource_observer.py')).hexdigest()
observations = []
for index in (1, 2):
    p = ROOT/f'resource_observations/obs_{index:04d}/receipt.json'
    o = read(p)
    outer = read(ROOT/f'observer_outer/obs_{index:04d}.outer.json')
    stdout = raw(ROOT/f'observer_outer/obs_{index:04d}.stdout.txt')
    stderr = raw(ROOT/f'observer_outer/obs_{index:04d}.stderr.txt')
    check(json.loads(stdout) == o and not stderr, f'obs{index}:stdout/stderr')
    for k, data in [('receipt', p.read_bytes()), ('stdout', stdout), ('stderr', stderr)]:
        check(outer[k+'_sha256'] == hashlib.sha256(data).hexdigest(), f'obs{index}:{k}_sha')
    check(outer['source_sha256'] == observer_source_sha and outer['exit_code'] == 0, f'obs{index}:source_exit')
    check(o['observation_number'] == index and o['scientific_runs'] == o['query_calls'] == 0, f'obs{index}:identity')
    check(o['schedule_sha256'] == inputs[str(ROOT/'scheduling/waiting_schedule.json')], f'obs{index}:schedule_sha')
    check(o['checks']['nice'] >= 15 and o['checks']['cpu_limit'] == [1,1], f'obs{index}:limits')
    sample = o['usage_before_receipt']['self_cpu_s'] + o['usage_before_receipt']['reaped_children_cpu_s']
    same(sample, o['measured_cpu_sample_s'], f'obs{index}:sample')
    same(sample + .2, o['cpu_charge_s'], f'obs{index}:charge')
    same(sum(x['cpu_charge_s'] for x in observations), o['previous_observation_charge_s'], f'obs{index}:prior')
    same(o['previous_observation_charge_s'] + o['cpu_charge_s'], o['cumulative_observation_charge_s'], f'obs{index}:cumulative')
    check(10 + o['previous_observation_charge_s'] + 1.2 <= 50, f'obs{index}:start_budget')
    check(o['started_unix'] >= schedule['first_observation_not_before_unix'], f'obs{index}:first_due')
    eligible = o['checks']['load_1m'] <= 4 and o['checks']['memory_free_percent'] >= 25
    check(o['status'] == ('ELIGIBLE' if eligible else 'WAIT_RESOURCE'), f'obs{index}:threshold')
    observations.append(o)
check(len(list((ROOT/'resource_observations').glob('obs_*'))) == 2, 'observation_directory_count')
interval = observations[1]['started_monotonic'] - observations[0]['started_monotonic']
check(interval >= 900, 'observation_monotonic_interval')
check(observations[1]['started_unix'] - observations[0]['started_unix'] >= 900, 'observation_wall_interval')
obs_measured = sum(o['measured_cpu_sample_s'] for o in observations)
obs_tail = sum(o['unmeasured_final_receipt_exit_tail_reserve_s'] for o in observations)
obs_charge = sum(o['cpu_charge_s'] for o in observations)

protocol = read(ROOT/'protocols/generation_replay.registered.json')
batch_path = ROOT/'runs/diagnostic_01/batch_receipt.json'
batch = read(batch_path)
outer = read(ROOT/'outer_launch/OUTER_RECEIPT.json')
lock = read(ROOT/'EXECUTION_ONCE.lock')
read(ROOT/'FINALIZATION_RECEIPT.json')
freeze_path = ROOT/'protocols/generation_replay.freeze.json'
freeze = read(freeze_path)
stdout = raw(ROOT/'outer_launch/stdout.txt')
stderr = raw(ROOT/'outer_launch/stderr.txt')
for field, path in [('batch_receipt',batch_path), ('finalization_receipt',ROOT/'FINALIZATION_RECEIPT.json'),
                    ('registered_protocol',ROOT/'protocols/generation_replay.registered.json'), ('freeze',freeze_path)]:
    check(outer[field+'_sha256'] == inputs[str(path)], 'outer_'+field+'_sha')
check(not stdout and outer['exit_code'] == 0, 'outer_exit_stdout')
check(outer['stdout_sha256'] == hashlib.sha256(stdout).hexdigest(), 'outer_stdout_sha')
check(outer['stderr_sha256'] == hashlib.sha256(stderr).hexdigest(), 'outer_stderr_sha')
timing = re.search(rb'([\d.]+) real\s+([\d.]+) user\s+([\d.]+) sys',stderr)
check(timing is not None, 'outer_time_parse')
real, user, system = map(float, timing.groups())
same(real,outer['time_real_s_rounded'],'outer_real')
same(user+system,outer['time_cpu_s_rounded'],'outer_cpu')
fresh = stamp(batch['created_utc']) - observations[-1]['finished_unix']
check(0 <= fresh <= 60, 'eligible_freshness_upper_bound')
check(observations[-1]['finished_unix'] <= outer['lock_created_unix'] <= stamp(batch['created_utc']), 'lock_chronology')
check(outer['scientific_batch_attempts'] == 1 and outer['automatic_retries'] == 0, 'outer_attempt_once')
check(batch['registered_denominator'] == batch['planned_denominator'] == batch['registered_attempts'] == 24, 'denominator24')
check(batch['registration_validated'] and batch['status'] == 'REGISTERED_SEQUENCE_FINISHED', 'batch_finished')
check(not batch['violations'] and batch['halt_reason'] is None, 'batch_no_stop')
check(batch['protocol_sha256'] == inputs[str(ROOT/'protocols/generation_replay.registered.json')], 'batch_protocol_sha')
check(batch['freeze_sha256'] == inputs[str(freeze_path)], 'batch_freeze_sha')
same(protocol['supervisor']['prior_resource_observation_cpu_charge_seconds'],obs_charge,'protocol_obscharge')
same(protocol['supervisor']['prior_resource_observation_measured_cpu_seconds'],obs_measured,'protocol_obsmeasured')
same(protocol['supervisor']['prior_resource_observation_tail_reserve_seconds'],obs_tail,'protocol_obstail')

accounts_checked = 0
def account(a,label):
    global accounts_checked
    accounts_checked += 1
    own = a['parent_user_cpu_seconds'] + a['parent_system_cpu_seconds']
    children = a['all_reaped_children_user_cpu_seconds'] + a['all_reaped_children_system_cpu_seconds']
    same(a['pre_registered_prior_cpu_seconds'],10,label+':prep')
    same(a['prior_resource_observation_cpu_charge_seconds'],obs_charge,label+':obs')
    same(a['prior_resource_observation_measured_cpu_seconds'],obs_measured,label+':obsmeasured')
    same(a['prior_resource_observation_tail_reserve_seconds'],obs_tail,label+':obstail')
    same(a['supervisor_plus_reaped_cpu_seconds'],own+children,label+':subtotal')
    same(a['observed_total_cpu_seconds'],10+obs_charge+own+children,label+':observed')
    same(a['conservative_charged_total_seconds'],10+obs_charge+own+children+.2,label+':total')
    return own,children

own,children = account(batch['cpu_accounting'],'batch')
rows=[]
monitor_count=0
monitor_max_load=0
monitor_max_account=0
monitor_max_with_live=0
monitor_max_solver_watchdog=0
last_finished=None
stages_summary=Counter()
actual_check_over_parameter=[]
for i,slot in enumerate(batch['slots']):
    d=ROOT/'runs/diagnostic_01'/f'case_{i:02d}'
    s=read(d/'supervisor_receipt.json')
    w=read(d/'results.json')
    events=[json.loads(line) for line in raw(d/'supervisor_events.jsonl').splitlines()]
    record=w['record']
    a=record['attempts'][0]
    identity=protocol['registered_cases'][i]
    check(slot['registered_slot']==s['registered_slot']==w['registered_slot']==identity,f'slot{i}:identity')
    check(s['case_index']==i and s['case_id']==identity['id'],f'slot{i}:index_id')
    check(slot['status']==s['status']=='RETURNED' and s['worker_exit_code']==0,f'slot{i}:returned')
    check(s['violations']==slot['violations']==[] and s['stop_remainder'] is None,f'slot{i}:stop')
    check(s['worker_result_unmodified']==w and s['worker_record_unmodified']==record,f'slot{i}:embedded_copies')
    check(s['worker_results_sha256']==inputs[str(d/'results.json')],f'slot{i}:result_sha')
    check(slot['worker_wait4_usage']==s['worker_wait4_usage'],f'slot{i}:wait4_copy')
    check(s['cleanup_wait_complete'] and s['cleanup_killpg_skipped_already_reaped'],f'slot{i}:reaped')
    usage=s['worker_wait4_usage']
    same(usage['cpu_seconds'],usage['user_cpu_seconds']+usage['system_cpu_seconds'],f'slot{i}:wait4_cpu')
    check(usage['pid']==s['pid']==s['owned_pgid'] and usage['exit_code']==0,f'slot{i}:pid_exit')
    check(usage['cpu_seconds']<=3 and s['wall_seconds']<=4,f'slot{i}:worker_cpu_wall')
    check(max(usage['maxrss_bytes_darwin'],s['sampled_peak_rss_bytes'])<=268435456,f'slot{i}:rss')
    gate=slot['gate_probe']
    check(gate['status']=='RETURNED' and gate['admitted'] and gate['memory_pressure_exit_code']==0,f'slot{i}:gate_returned')
    check(gate['load'][0]<=4 and gate['memory_available_percentage']>=25,f'slot{i}:gate_resources')
    account(gate['cpu_accounting_after_probe'],f'slot{i}:gate_account')
    _,before_children=account(s['cpu_accounting_before_launch'],f'slot{i}:before')
    _,after_children=account(s['cpu_accounting_after_reap'],f'slot{i}:after')
    check(s['cpu_accounting_before_launch']['conservative_charged_total_seconds']<=50,f'slot{i}:start50')
    check(after_children-before_children+1e-9>=usage['cpu_seconds'],f'slot{i}:worker_in_children')
    check(len(record['attempts'])==1 and a['attempt']==1 and not record['repeat_triggered'],f'slot{i}:single_attempt')
    check(w['protocol_sha256']==batch['protocol_sha256'],f'slot{i}:protocol_sha')
    for name,sha in w['code_sha256'].items():
        check(hashlib.sha256(raw(ROOT/'implementation'/name)).hexdigest()==sha,f'slot{i}:code_'+name)
    calls=record['solver_calls']
    solver_wall=sum(c['actual_check_wall_seconds'] for c in calls)
    solver_cpu=sum(c['actual_check_cpu_seconds'] for c in calls)
    same(solver_wall,record['solver_cumulative_wall_seconds'],f'slot{i}:solver_wall')
    same(solver_cpu,record['solver_cumulative_cpu_seconds'],f'slot{i}:solver_cpu')
    same(solver_wall,s['final_progress']['solver_spent_wall_seconds'],f'slot{i}:final_progress_solver')
    check(len(calls)<=2 and len(calls)==s['final_progress']['check_count'],f'slot{i}:check_count')
    check(solver_wall<=2 and not s['final_progress']['solver_check_active'],f'slot{i}:solver_limit')
    check(s['final_progress']['solver_watchdog_estimated_seconds']<1.5,f'slot{i}:final_watchdog')
    for c in calls:
        check(c['timeout_ms']<=({'FULL_C_NONEMPTY_CHECK':100,'OFFICIAL_QUERY_SOLVER_CHECK':700}[c['stage']]),f'slot{i}:timeout_parameter')
        if c['actual_check_wall_seconds'] > c['timeout_ms']/1000:
            actual_check_over_parameter.append({'slot':i,'case_id':identity['id'],'stage':c['stage'],
                                               'actual_check_wall_s':c['actual_check_wall_seconds'],'timeout_parameter_ms':c['timeout_ms']})
    phases=a['stages']
    parse=sum(x['cpu_seconds'] for x in phases if x['name'].startswith('OFFICIAL_PARSE_QUERY_'))
    analyze=sum(x['cpu_seconds'] for x in phases if x['name']=='OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE')
    query=[x['actual_check_cpu_seconds'] for x in phases if x['name']=='OFFICIAL_QUERY_SOLVER_CHECK']
    same(a['exclusive_phase_cpu']['parse'],parse,f'slot{i}:parse')
    same(a['exclusive_phase_cpu']['scope_encode'],analyze-parse,f'slot{i}:scope')
    check(analyze+1e-9>=parse,f'slot{i}:scope_nonnegative_without_clipping')
    if query:
        same(a['exclusive_phase_cpu']['query_check'],sum(query),f'slot{i}:query')
    else:
        check(a['exclusive_phase_cpu']['query_check'] is None and a['exclusive_phase_cpu_status']['query_check']=='NOT_REACHED',f'slot{i}:query_null')
    same(a['exclusive_phase_cpu']['compare_encode'],a['comparison_formula_encode']['cpu_seconds'],f'slot{i}:compare')
    runtime=sum(t['cpu_seconds'] for t in w['runtime']['stages'])
    admission=record['source_and_structure_admission_cost']['cpu_seconds']
    attempt=a['attempt_cost']['cpu_seconds']
    worker_sample=w['worker_usage']['cpu_user_seconds']+w['worker_usage']['cpu_system_seconds']
    check(worker_sample<=usage['cpu_seconds']+1e-9,f'slot{i}:worker_sample_before_wait4')
    check(runtime+admission+attempt<=worker_sample+1e-9,f'slot{i}:disjoint_scope_subtotals')
    started=[e for e in events if e['event']=='WORKER_STARTED']
    finished=[e for e in events if e['event']=='WORKER_FINISHED']
    check(len(started)==len(finished)==1,f'slot{i}:event_lifecycle')
    if last_finished is not None:
        check(started[0]['monotonic']>last_finished,f'slot{i}:single_worker_nonoverlap')
    last_finished=finished[0]['monotonic']
    monitors=[e for e in events if e['event']=='MONITOR']
    check(len(monitors)==s['sample_count'],f'slot{i}:sample_count')
    for e in monitors:
        monitor_count+=1
        check(e['group']['members'] and all(m['pid']==s['pid'] for m in e['group']['members']),f'slot{i}:owned_members')
        check(e['group']['rss_bytes']<=268435456 and e['group']['cpu_seconds']<3,f'slot{i}:sample_limits')
        check(e['load'][0]<=4,f'slot{i}:sample_load')
        account(e['accounting'],f'slot{i}:monitor{monitor_count}')
        charge=e['accounting']['conservative_charged_total_seconds']
        live=e['group']['cpu_seconds']
        check(charge<56 and charge+live<60,f'slot{i}:56_60_gates')
        monitor_max_load=max(monitor_max_load,e['load'][0])
        monitor_max_account=max(monitor_max_account,charge)
        monitor_max_with_live=max(monitor_max_with_live,charge+live)
        if e['progress'] is not None:
            estimate=e['progress']['solver_watchdog_estimated_seconds']
            check(estimate<1.5,f'slot{i}:monitor_solver_watchdog')
            monitor_max_solver_watchdog=max(monitor_max_solver_watchdog,estimate)
    stages_summary.update(a['exclusive_phase_cpu_status'].values())
    rows.append({'slot':i,'case_id':s['case_id'],'worker_wait4_cpu_s':usage['cpu_seconds'],
                 'worker_wall_s':s['wall_seconds'],'worker_peak_rss_bytes':max(usage['maxrss_bytes_darwin'],s['sampled_peak_rss_bytes']),
                 'solver_calls':len(calls),'solver_cumulative_cpu_s':solver_cpu,'solver_cumulative_wall_s':solver_wall,
                 'parse_cpu_s':parse,'analyze_including_parse_cpu_s':analyze,
                 'exclusive_phase_cpu':a['exclusive_phase_cpu'],'exclusive_phase_cpu_status':a['exclusive_phase_cpu_status'],
                 'runtime_cpu_s':runtime,'admission_cpu_s':admission,'attempt_cpu_s':attempt,
                 'worker_sample_cpu_s':worker_sample,'unattributed_worker_sample_residual_cpu_s':worker_sample-runtime-admission-attempt,
                 'worker_sample_to_wait4_delta_cpu_s':usage['cpu_seconds']-worker_sample,
                 'child_cpu_increment_during_slot_s':after_children-before_children,
                 'slot_nonworker_child_cpu_s':after_children-before_children-usage['cpu_seconds'],
                 'monitor_samples':len(monitors)})

workers=sum(r['worker_wait4_cpu_s'] for r in rows)
charged=10+obs_charge+own+children+.2
same(charged,outer['conservative_charged_total_cpu_s'],'outer_total')
check(charged<=60,'batch_cpu60')
check(abs((own+children)-(user+system))<=.01,'outer_two_rounded_fields_consistent')
data={
 'reviewer':'/root/round16_independent/wait_budget_criteria',
 'scope':'Independent read-only JSON/hash arithmetic; no scientific/SQL/SMT/import/target execution.',
 'issues':issues,'passed':not issues,'accounts_recomputed':accounts_checked,
 'observation':{'count':2,'monotonic_interval_s':interval,'unix_interval_s':observations[1]['started_unix']-observations[0]['started_unix'],
                'measured_cpu_s':obs_measured,'tail_reserve_s':obs_tail,'charge_s':obs_charge,
                'batch_created_seconds_after_eligible':fresh,'request_exact_time_known':False},
 'batch':{'parent_measured_cpu_s':own,'all_reaped_children_cpu_s':children,'workers_wait4_cpu_s':workers,
          'nonworker_reaped_children_cpu_s':children-workers,'current_internal_sample_cpu_s':own+children,
          'all_measured_samples_cpu_s':own+children+obs_measured,'prep_reserve_s':10,'batch_tail_reserve_s':.2,
          'conservative_total_s':charged,'remaining_to_60_s':60-charged,'outer_wall_s_rounded':real,
          'outer_cpu_s_rounded':user+system,'outer_minus_internal_sample_s':user+system-own-children,
          'outer_internal_wall_s':stamp(batch['finished_utc'])-stamp(batch['created_utc'])},
 'resources':{'workers':len(rows),'monitor_samples':monitor_count,'max_monitor_load1':monitor_max_load,
              'min_slot_memory_free_percent':min(s['gate_probe']['memory_available_percentage'] for s in batch['slots']),
              'max_worker_cpu_s':max(r['worker_wait4_cpu_s'] for r in rows),'max_worker_wall_s':max(r['worker_wall_s'] for r in rows),
              'max_worker_rss_bytes':max(r['worker_peak_rss_bytes'] for r in rows),'max_solver_cumulative_wall_s':max(r['solver_cumulative_wall_s'] for r in rows),
              'max_monitor_solver_watchdog_estimate_s':monitor_max_solver_watchdog,
              'max_monitor_account_s':monitor_max_account,'max_monitor_account_plus_live_s':monitor_max_with_live,
              'gate50_max_prelaunch_charge_s':max(read(ROOT/'runs/diagnostic_01'/f'case_{i:02d}'/'supervisor_receipt.json')['cpu_accounting_before_launch']['conservative_charged_total_seconds'] for i in range(24))},
 'solver_timeout_parameter_boundary':{'actual_checks_over_parameter':actual_check_over_parameter,
                                     'interpretation':'A solver timeout setting is not a hard elapsed-wall guarantee; all reported cumulative solver wall and watchdog bounds remained below the separate policy limits.'},
 'phase_boundaries':{'query_not_reached_null_count':sum(r['exclusive_phase_cpu']['query_check'] is None for r in rows),
                     'worker_unattributed_sample_residual_s':sum(r['unattributed_worker_sample_residual_cpu_s'] for r in rows),
                     'worker_samples_to_wait4_total_delta_s':sum(r['worker_sample_to_wait4_delta_cpu_s'] for r in rows),
                     'non_additivity':'Parse nested in analyze; solver actual checks nested in check stages; replay inner phases nested in outer sanity; attempt nested in worker; wait4 workers nested in CHILDREN; outer time overlaps all current children. Residuals are not proven causal phase attribution.'},
 'slots':rows,'input_sha256':inputs,
 'limits':'All measured values are receipt samples; reserves are not measured CPU. Static process CPU limit does not imply whole-tree instantaneous hard wall/RSS limit. Post-result review/analysis CPU is outside the completed science launch ledger.'}
(OUT/'COST_BOUNDARY_EVIDENCE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in data.items() if k not in ('slots','input_sha256')},ensure_ascii=False,indent=2))
