"""Read-only receipt derivation. No scientific imports, SQL, solver or retries.

Run only after root authorizes postrun aggregation. Writes a fresh output directory.
"""
from pathlib import Path
import argparse
import collections
import datetime
import hashlib
import json
import math
import re


ROOT = Path(__file__).resolve().parents[1]
FINAL_BATCH = {'REGISTERED_SEQUENCE_FINISHED', 'STOPPED_REMAINDER_NOT_RUN',
               'BATCH_PRECHECK_OR_MONITOR_FAILED'}
BUDGET_REASONS = {'timeout', 'out of memory'}
STAGE_FIELDS = ('name', 'status', 'cpu_seconds', 'wall_seconds',
                'actual_check_cpu_seconds', 'actual_check_wall_seconds',
                'answer', 'reason_unknown', 'timeout_ms', 'error_type')


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def reject_nonfinite_json(_value):
    raise ValueError('NONFINITE_JSON_NUMBER')


def load(path):
    path = Path(path).resolve()
    reference = {'path': str(path), 'sha256': None, 'read_status': 'MISSING'}
    try:
        if not path.is_file():
            return None, reference
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('RECEIPT_SIZE_LIMIT')
        raw = path.read_bytes()
        reference['sha256'] = hashlib.sha256(raw).hexdigest()
        value = json.loads(raw, parse_constant=reject_nonfinite_json)
        if not isinstance(value, dict):
            raise ValueError('RECEIPT_NOT_OBJECT')
        reference['read_status'] = 'READ'
        return value, reference
    except (OSError, ValueError, UnicodeError) as exc:
        reference.update(read_status='INVALID', error_type=type(exc).__name__)
        return None, reference


def select(obj, fields):
    return {key: obj.get(key) for key in fields} if isinstance(obj, dict) else None


def reason(value):
    if value is None:
        return None
    text = str(value)
    if len(text) > 256 or re.search(r'\b(SELECT|INSERT|CREATE TABLE|UPDATE|DELETE FROM)\b', text, re.I):
        return 'REDACTED_TEXT_SHA256:' + hashlib.sha256(text.encode()).hexdigest()
    return text


def opaque_error(value):
    return None if value is None else {'sha256': hashlib.sha256(str(value).encode()).hexdigest(),
                                      'characters': len(str(value)), 'text_in_raw_receipt_only': True}


def stages(value):
    output = []
    for item in value if isinstance(value, list) else []:
        if isinstance(item, dict):
            row = select(item, STAGE_FIELDS)
            row['reason_unknown'] = reason(row['reason_unknown'])
            output.append(row)
    return output


def phase(items, field, complete):
    if not items:
        return {'value': None, 'status': 'NOT_REACHED' if complete else 'UNKNOWN_OR_CENSORED'}
    values = [item.get(field) for item in items]
    if not all(finite(value) for value in values):
        return {'value': None, 'status': 'UNMEASURED_OR_CENSORED'}
    return {'value': sum(values), 'status': 'MEASURED', 'stage_statuses': [x.get('status') for x in items]}


def replay_summary(replay, control=False):
    if not isinstance(replay, dict):
        return None
    result = select(replay, ('status', 'full_C_status', 'original_sql_unchanged', 'query_rewrites',
                            'original_sql_sha256', 'sqlite_version', 'generated_official_model',
                            'model_origin', 'query_sat_witness', 'comparison'))
    result['reason'] = reason(replay.get('reason'))
    result['error_type'] = replay.get('error_type')
    result['error'] = opaque_error(replay.get('error'))
    result['phase_costs'] = stages(replay.get('phase_costs'))
    outputs = replay.get('original_sql_results')
    result['original_query_execution_count'] = len(outputs) if isinstance(outputs, list) else None
    result['output_row_counts'] = [len(x) if isinstance(x, list) else None for x in outputs] if isinstance(outputs, list) else None
    result['outputs_hash'] = hashlib.sha256(json.dumps(outputs, sort_keys=True, allow_nan=False).encode()).hexdigest() if outputs is not None else None
    bags_valid = (isinstance(outputs, list) and len(outputs) == 2 and all(isinstance(part, list)
                  and all(isinstance(row, (list, tuple)) and all(x is None or type(x) is int for x in row) for row in part)
                  for part in outputs))
    result['output_bags_differ'] = (collections.Counter(map(tuple, outputs[0])) != collections.Counter(map(tuple, outputs[1]))) if bags_valid else None
    result['concrete_database_present'] = isinstance(replay.get('concrete_database'), dict)
    result['scope'] = 'C_MODEL_SANITY_ONLY_NOT_QUERY_SAT' if control else 'RECORDED_ORIGINAL_SQL_REPLAY_EVIDENCE_ONLY'
    result['raw_scope'] = replay.get('scope')
    result['raw_query_sat_witness'] = replay.get('query_sat_witness')
    if control:
        result['query_sat_witness'] = False
    return result


def cost_view(worker, attempt, supervisor, complete):
    all_stages = stages(attempt.get('stages'))
    parsed = [s for s in all_stages if (s.get('name') or '').startswith('OFFICIAL_PARSE_QUERY_')]
    analyzed = [s for s in all_stages if s.get('name') == 'OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE']
    query = [s for s in all_stages if s.get('name') == 'OFFICIAL_QUERY_SOLVER_CHECK']
    parse_cpu, analyze_cpu = phase(parsed, 'cpu_seconds', complete), phase(analyzed, 'cpu_seconds', complete)
    scope = {'value': None, 'status': 'NOT_REACHED' if complete and not analyzed else 'UNMEASURED_OR_CENSORED'}
    if finite(parse_cpu['value']) and finite(analyze_cpu['value']):
        scope = {'value': max(0, analyze_cpu['value'] - parse_cpu['value']), 'status': 'DERIVED_ANALYZE_MINUS_PARSE'}
    comparison = select(attempt.get('comparison_formula_encode'), ('cpu_seconds', 'wall_seconds'))
    comparison_status = attempt.get('comparison_formula_encode_status')
    if comparison_status is None:
        comparison_status = ('MEASURED_LEGACY' if comparison else
                             'UNMEASURED_OR_CENSORED' if attempt.get('failure_stage') == 'OFFICIAL_COMPARISON_FORMULA_ENCODING' else
                             'UNKNOWN_OR_CENSORED')
    return {'worker_wait4_usage': select(supervisor.get('worker_wait4_usage'),
                ('exit_code', 'user_cpu_seconds', 'system_cpu_seconds', 'cpu_seconds', 'maxrss_bytes_darwin')),
            'supervisor_worker_wall_seconds': supervisor.get('wall_seconds'),
            'sampled_peak_rss_bytes': supervisor.get('sampled_peak_rss_bytes'),
            'worker_usage_before_final_exit': select(worker.get('worker_usage'),
                ('cpu_user_seconds', 'cpu_system_seconds', 'peak_rss_bytes_macos', 'wall_from_main_seconds')),
            'source_and_structure_admission': select(worker.get('record', {}).get('source_and_structure_admission_cost'),
                ('status', 'cpu_seconds', 'wall_seconds')),
            'runtime_stages': stages(worker.get('runtime', {}).get('stages')),
            'runtime_stage_receipt_status': 'PRESENT' if worker.get('runtime', {}).get('stages') else 'NO_COMPLETE_RUNTIME_RECEIPT_NOT_PROOF_OF_NONENTRY',
            'last_worker_stage_evidence': select(worker.get('record'), ('active_stage', 'latest_stage')),
            'attempt_stages': all_stages,
            'parse_cpu_seconds': parse_cpu, 'analyze_including_parse_cpu_seconds': analyze_cpu,
            'scope_encode_cpu_seconds': scope,
            'comparison_formula_encode': {'status': comparison_status, 'cost': comparison},
            'query_check_cpu_seconds': phase(query, 'actual_check_cpu_seconds', complete),
            'query_check_wall_seconds': phase(query, 'actual_check_wall_seconds', complete),
            'legacy_or_source_exclusive_phase_cpu': attempt.get('exclusive_phase_cpu'),
            'source_exclusive_phase_cpu_status': attempt.get('exclusive_phase_cpu_status'),
            'attempt_cost': select(attempt.get('attempt_cost'), ('cpu_seconds', 'wall_seconds', 'worker_peak_rss_bytes_macos')),
            'cleanup_cost': select(attempt.get('cleanup_cost'), ('cpu_seconds', 'wall_seconds')),
            'non_additivity': 'Parse is inside analyze; replay inner costs are inside outer stages; attempt is inside worker; wait4 workers are inside batch CHILDREN. No phase or overlapping lifecycle sum is a full cost.'}


def derive_slot(index, planned, batch_slot, batch_final, batch_bound, planned_bound,
                batch_budget_valid, run, protocol_hash, input_spec, frozen_files, worker_directory):
    supervisor, sref = load(run / f'case_{index:02d}' / 'supervisor_receipt.json')
    worker, wref = load(run / f'case_{index:02d}' / 'results.json')
    supervisor, worker = supervisor or {}, worker or {}
    record = worker.get('record') if isinstance(worker.get('record'), dict) else {}
    attempts = record.get('attempts') if isinstance(record.get('attempts'), list) else []
    attempt = attempts[0] if len(attempts) == 1 and isinstance(attempts[0], dict) else worker.get('latest_attempt_snapshot', {})
    attempt = attempt if isinstance(attempt, dict) else {}
    problems = []
    for valid, label in [
        (batch_bound, 'BATCH_PROTOCOL_BINDING_INVALID_OR_MISSING'),
        (isinstance(batch_slot, dict) and batch_slot.get('case_id') == planned['id'] and batch_slot.get('slot') == index, 'BATCH_SLOT_IDENTITY'),
        (sref['read_status'] == 'READ', 'SUPERVISOR_RECEIPT_MISSING_OR_INVALID'),
        (wref['read_status'] == 'READ', 'WORKER_RECEIPT_MISSING_OR_INVALID'),
        (supervisor.get('registered_slot') == planned and supervisor.get('case_index') == index and supervisor.get('case_id') == planned['id'], 'SUPERVISOR_IDENTITY'),
        (worker.get('registered_slot') == planned and record.get('id') == planned['id'] and record.get('case_index') == index, 'WORKER_IDENTITY'),
        (worker.get('protocol_sha256') == protocol_hash, 'WORKER_PROTOCOL_HASH'),
        (worker.get('input') == input_spec, 'WORKER_INPUT_PIN'),
        (supervisor.get('worker_results_sha256') is not None and supervisor.get('worker_results_sha256') == wref['sha256'], 'WORKER_RECEIPT_HASH'),
    ]:
        if not valid:
            problems.append(label)
    code_hashes = worker.get('code_sha256')
    required_code = {'generation_common.py', 'official_generation_worker.py', 'official_generation_backend.py',
                     'official_contract_admission.py', 'safe_sqlite_replay.py'}
    if (not isinstance(code_hashes, dict) or set(code_hashes) != required_code
            or any(frozen_files.get(str(worker_directory / name)) != digest for name, digest in code_hashes.items())):
        problems.append('WORKER_CODE_HASHES_NOT_BOUND_TO_RUNTIME_FREEZE')
    if 'repeat_id' in planned and record.get('repeat_id') != planned['repeat_id']:
        problems.append('WORKER_REPEAT_ID')
    if supervisor.get('worker_record_unmodified') is not None and supervisor['worker_record_unmodified'] != record:
        problems.append('SUPERVISOR_RECORD_COPY_MISMATCH')
    if supervisor.get('worker_result_unmodified') is not None and supervisor['worker_result_unmodified'] != worker:
        problems.append('SUPERVISOR_RESULT_COPY_MISMATCH')
    bslot = batch_slot or {}
    if supervisor and bslot.get('worker_exit_code') != supervisor.get('worker_exit_code'):
        problems.append('BATCH_SUPERVISOR_EXIT_MISMATCH')
    identity_valid = not problems
    completed = (identity_valid and batch_final and supervisor.get('cleanup_wait_complete') is True
                 and supervisor.get('worker_exit_code') == 0
                 and worker.get('status') == 'REGISTERED_GROUP_ATTEMPT_RETURNED' and len(attempts) == 1)
    not_run = (batch_final and planned_bound and bslot.get('status') == 'NOT_RUN'
               and sref['read_status'] == 'MISSING' and wref['read_status'] == 'MISSING')
    disposition = 'NOT_RUN' if not_run else 'RECORDED_COMPLETED' if completed else 'UNKNOWN_INVALID_OR_CENSORED'
    raw_stages = attempt.get('stages') if isinstance(attempt.get('stages'), list) else []
    qstages = [s for s in raw_stages if isinstance(s, dict) and s.get('name') == 'OFFICIAL_QUERY_SOLVER_CHECK']
    calls = record.get('solver_calls') if isinstance(record.get('solver_calls'), list) else []
    qcalls = [s for s in calls if isinstance(s, dict) and s.get('stage') == 'OFFICIAL_QUERY_SOLVER_CHECK']
    q = qstages[0] if len(qstages) == 1 else {}
    cstages = [s for s in raw_stages if isinstance(s, dict) and s.get('name') == 'FULL_C_NONEMPTY_CHECK']
    ccalls = [s for s in calls if isinstance(s, dict) and s.get('stage') == 'FULL_C_NONEMPTY_CHECK']
    matching_C = (len(cstages) == len(ccalls) == 1 and cstages[0].get('status') == 'RETURNED'
        and cstages[0].get('answer') == attempt.get('full_C_nonempty')
        and finite(cstages[0].get('actual_check_cpu_seconds'))
        and cstages[0].get('actual_check_cpu_seconds') == ccalls[0].get('actual_check_cpu_seconds')
        and cstages[0].get('actual_check_wall_seconds') == ccalls[0].get('actual_check_wall_seconds'))
    verdict = attempt.get('raw_query_verdict')
    matching_query = (len(qstages) == len(qcalls) == 1 and q.get('status') == 'RETURNED'
        and finite(q.get('actual_check_cpu_seconds')) and finite(q.get('actual_check_wall_seconds'))
        and q.get('actual_check_cpu_seconds') == qcalls[0].get('actual_check_cpu_seconds')
        and q.get('actual_check_wall_seconds') == qcalls[0].get('actual_check_wall_seconds')
        and q.get('answer') == verdict and record.get('query_solver_called') is True)
    eligible = (completed and batch_budget_valid and matching_C and matching_query and attempt.get('full_C_nonempty') == 'sat'
                and not supervisor.get('violations') and not supervisor.get('stop_remainder'))
    control = attempt.get('contract_model_sanity') or {}
    replay = replay_summary(attempt.get('replay'))
    witness = bool(eligible and verdict == 'sat' and isinstance(attempt.get('witness'), dict)
        and replay and replay['status'] == 'REPLAY_CONFIRMED_DIFFERENCE'
        and replay['full_C_status'] == 'COMPLETE_ORIGINAL_OPERATIONAL_C_TRUE'
        and replay['original_sql_unchanged'] is True and replay['query_rewrites'] == 0
        and replay['generated_official_model'] is True and replay['concrete_database_present']
        and replay['output_bags_differ'] is True
        and attempt.get('SAT_all_original_facts_and_actual_assertions_true') is True
        and replay['original_query_execution_count'] == 2
        and replay['original_sql_sha256'] == record.get('original_sql_sha256'))
    return {'slot': index, **planned, 'evidence_disposition': disposition,
            'receipt_integrity_valid': identity_valid, 'integrity_problems': problems,
            'attempt_evidence_kind': 'COMPLETED_ATTEMPT_ARRAY' if completed else 'PARTIAL_OR_UNVALIDATED_SNAPSHOT',
            'batch_budget_evidence_valid': batch_budget_valid,
            'batch_slot_status': bslot.get('status'), 'not_run_reason': reason(bslot.get('not_run_reason')),
            'supervisor_status': supervisor.get('status'), 'worker_exit_code': supervisor.get('worker_exit_code'),
            'worker_report_status': worker.get('status'), 'record_status': record.get('status'),
            'engineering_class': record.get('engineering_class'), 'strict_class': record.get('strict_class'),
            'C_status': attempt.get('full_C_nonempty'), 'query_verdict': verdict,
            'query_unknown_reason': reason(q.get('reason_unknown')),
            'query_reach_status': ('NOT_RUN' if not_run else 'RECORDED_CHECK'
                if qcalls or any(finite(s.get('actual_check_cpu_seconds')) for s in qstages)
                else 'STAGE_ENTERED_CHECK_UNPROVEN' if qstages else 'NOT_REACHED' if completed else 'UNKNOWN_OR_CENSORED'),
            'C_check_evidence_consistent': matching_C,
            'query_check_evidence_consistent': matching_query,
            'scientific_pattern_eligible': eligible, 'failure_stage': attempt.get('failure_stage'),
            'error_type': attempt.get('error_type') or worker.get('error_type'),
            'error': opaque_error(attempt.get('error') or worker.get('error')),
            'resource_reason': reason(attempt.get('reason')),
            'resource_stop_phase': attempt.get('resource_stop_phase'),
            'stop_remainder': reason(supervisor.get('stop_remainder')), 'violations': supervisor.get('violations'),
            'solver_calls': [select(x, ('attempt', 'stage', 'actual_check_wall_seconds', 'actual_check_cpu_seconds', 'timeout_ms')) for x in calls if isinstance(x, dict)],
            'costs': cost_view(worker, attempt, supervisor, completed),
            'contract_model_sanity': {'status': control.get('status'), 'query_sat_witness': False,
                'scope': 'C_MODEL_SANITY_ONLY_NOT_QUERY_SAT', 'replay': replay_summary(control.get('replay'), True)},
            'query_sat_replay': replay, 'recorded_valid_distinguishing_witness': witness,
            'witness_label_scope': 'Receipt conditions only; independent raw audit still required',
            'provenance': {'worker': wref, 'supervisor': sref}}


def aggregate(protocol_path, run, expected_count, freeze_path):
    protocol, pref = load(protocol_path)
    if not protocol or protocol.get('status') != 'REGISTERED':
        raise ValueError('A readable registered protocol is required; draft is not an executed denominator')
    planned = protocol.get('registered_cases')
    if (not isinstance(planned, list) or len(planned) != expected_count
            or any(not isinstance(s, dict) or not isinstance(s.get('id'), str) for s in planned)
            or len({s['id'] for s in planned}) != expected_count):
        raise ValueError('INVALID_COMPLETE_PLANNED_DENOMINATOR')
    batch, bref = load(run / 'batch_receipt.json')
    batch = batch or {}
    freeze, fref = load(freeze_path)
    entries = (freeze or {}).get('files')
    frozen_files = {str(Path(x['path']).resolve()): x['sha256'] for x in entries
                    if isinstance(x, dict) and isinstance(x.get('path'), str) and isinstance(x.get('sha256'), str)} if isinstance(entries, list) else {}
    worker_directory = Path(protocol['worker_paths']['official']).resolve().parent
    freeze_bound = (fref['sha256'] is not None and batch.get('freeze_sha256') == fref['sha256']
                    and frozen_files.get(str(protocol_path.resolve())) == pref['sha256']
                    and frozen_files.get(str(Path(protocol['input']['path']).resolve())) == protocol['input']['sha256']
                    and frozen_files.get(str(worker_directory / 'generation_supervisor.py')) == batch.get('supervisor_sha256'))
    raw_slots = batch.get('slots') if isinstance(batch.get('slots'), list) else []
    ordered = (len(raw_slots) == len(planned) and all(isinstance(b, dict) and b.get('slot') == i
               and b.get('case_id') == s['id'] and (b.get('registered_slot') or b.get('planned_slot')) == s
               for i, (b, s) in enumerate(zip(raw_slots, planned))))
    bound = (ordered and freeze_bound and batch.get('protocol_sha256') == pref['sha256']
             and batch.get('registration_validated') is True)
    final = batch.get('status') in FINAL_BATCH and isinstance(batch.get('finished_utc'), str)
    accounting = batch.get('cpu_accounting') if isinstance(batch.get('cpu_accounting'), dict) else {}
    charge = accounting.get('conservative_charged_total_seconds')
    budget_valid = final and finite(charge) and charge <= protocol['total_parent_cpu_limit_seconds'] and batch.get('violations') == []
    rows = []
    for i, slot in enumerate(planned):
        try:
            row = derive_slot(i, slot, raw_slots[i] if i < len(raw_slots) else None,
                              final, bound, ordered, budget_valid, run, pref['sha256'],
                              protocol['input'], frozen_files, worker_directory)
        except (AttributeError, KeyError, TypeError, ValueError, IndexError) as exc:
            row = {'slot': i, **slot, 'evidence_disposition': 'UNKNOWN_INVALID_OR_CENSORED',
                   'receipt_integrity_valid': False, 'scientific_pattern_eligible': False,
                   'integrity_problems': ['MALFORMED_NESTED_RECEIPT_' + type(exc).__name__],
                   'C_status': None, 'query_verdict': None, 'query_unknown_reason': None,
                   'error_type': None, 'costs': None,
                   'known_costs_scope': 'Malformed receipt; costs require raw independent audit, never assumed zero',
                   'provenance': {'worker': load(run / f'case_{i:02d}' / 'results.json')[1],
                                  'supervisor': load(run / f'case_{i:02d}' / 'supervisor_receipt.json')[1]}}
        rows.append(row)
    return {'planned_denominator': len(planned), 'registered_denominator_reported': batch.get('registered_denominator'),
            'batch_status': batch.get('status'), 'batch_final_evidence_present': final,
            'batch_protocol_binding_valid': bound, 'batch_halt_reason': reason(batch.get('halt_reason')),
            'batch_budget_evidence_valid': budget_valid, 'runtime_freeze_binding_valid': freeze_bound,
            'batch_violations': batch.get('violations'), 'batch_cpu_accounting': batch.get('cpu_accounting'),
            'counts_by_evidence_disposition': dict(collections.Counter(r['evidence_disposition'] for r in rows)),
            'counts_by_recorded_query_verdict': dict(collections.Counter(r['query_verdict'] or 'NO_RECORDED_VERDICT' for r in rows)),
            'rows': rows, 'provenance': {'protocol': pref, 'batch': bref, 'runtime_freeze': fref}}


def paired_patterns(rows):
    sources = list(dict.fromkeys(r['source_case_id'] for r in rows))
    output = []
    for source in sources:
        group = [r for r in rows if r['source_case_id'] == source]
        table = {(r.get('repeat_id'), r['exact_rows']): r for r in group}
        if len(table) != 6 or set(table) != {(rep, n) for rep in (1, 2) for n in (2, 3, 4)}:
            raise ValueError('REGISTERED_PAIRING_NOT_EXACT_TWO_REPEATS_TIMES_THREE_BOUNDS')
        comparisons = []
        for low, high in ((2, 3), (2, 4), (3, 4)):
            pairs = [(table[(rep, low)], table[(rep, high)]) for rep in (1, 2)]
            complete = all(r['scientific_pattern_eligible'] for pair in pairs for r in pair)
            same_low = pairs[0][0]['query_verdict'] == pairs[1][0]['query_verdict'] and pairs[0][0]['query_verdict'] in ('sat', 'unsat')
            reason0 = pairs[0][1]['query_unknown_reason']
            repeated = bool(complete and same_low and all(h['query_verdict'] == 'unknown' for _, h in pairs)
                            and reason0 in BUDGET_REASONS and pairs[1][1]['query_unknown_reason'] == reason0)
            comparisons.append({'low_N': low, 'high_N': high, 'repeat_case_ids': [[l['id'], h['id']] for l, h in pairs],
                                'same_reason_repeated_cost_pattern': repeated,
                                'status': 'REPEATED_TOOL_COST_PHENOMENON_WITHIN_THIS_BUDGET' if repeated else
                                          'INSUFFICIENT_OR_INVALID_RECEIPTS' if not complete else 'CRITERION_NOT_MET',
                                'shared_budget_reason': reason0 if repeated else None,
                                'scientific_mechanism': 'NONE'})
        output.append({'source_case_id': source,
                       'repeat_bound_case_ids': {str(rep): {str(n): table[(rep, n)]['id'] for n in (2, 3, 4)} for rep in (1, 2)},
                       'comparisons': comparisons})
    return output


def outer_numeric_fields(value, prefix=''):
    result = {}
    if isinstance(value, dict):
        for key, item in value.items():
            result.update(outer_numeric_fields(item, prefix + ('.' if prefix else '') + key))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            result.update(outer_numeric_fields(item, f'{prefix}[{i}]'))
    elif type(value) in (int, float) and math.isfinite(value):
        result[prefix] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--outer', action='append', type=Path, default=[])
    parser.add_argument('--freeze', type=Path, help='Defaults to the protocol directory/generation_replay.freeze.json')
    parser.add_argument('--historical-root', type=Path, default=ROOT.parent / 'calibergraph_next_20261011_06')
    args = parser.parse_args()
    current = aggregate(args.protocol.resolve(), args.run.resolve(), 24,
                        args.freeze or args.protocol.parent / 'generation_replay.freeze.json')
    historical = aggregate(args.historical_root / 'protocols/generation_replay.registered.json',
                           args.historical_root / 'runs/generation_replay_01', 12,
                           args.historical_root / 'protocols/generation_replay.freeze.json')
    external = []
    for path in args.outer:
        value, ref = load(path)
        external.append({'reference': ref, 'numeric_fields': outer_numeric_fields(value),
                         'schema_validation': 'NOT_PERFORMED_REQUIRES_ROOT_AND_INDEPENDENT_AUDIT'})
    report = {'schema': 'calibergraph.round16.readonly_derived.v1',
              'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'decision': 'NONE_NO_GO', 'new_validated_mechanism': None,
              'scope': 'Exposed development tool diagnostic only; exact N domains are not nested; no baseline runtime or independent test claim.',
              'current_round16': current, 'paired_diagnostics': paired_patterns(current['rows']),
              'historical_round06_separate_not_pooled': historical,
              'outer_time_exit_evidence': external,
              'whole_launch_cost_validation': 'PENDING_ROOT_AND_INDEPENDENT_OUTER_RECEIPT_AUDIT',
              'cost_accounting_note': 'Use raw batch SELF+all reaped CHILDREN plus separately identified observation CPU/reserves, prep10 and batch tail. Do not add worker wait4 or phases to batch CHILDREN. Outer scopes can overlap. Missing values stay null; no total inferred from phase sums.',
              'analysis_cpu_in_scientific_batch_ledger': False,
              'original_sql_or_database_values_exported': False,
              'scientific_code_imported_or_run': False, 'independent_result_review': 'PENDING',
              'aggregator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    lines = ['# 第16阶段收据派生（待独立核对）', '',
             '结论范围：NONE / NO_GO，仅已暴露开发集的工具成本诊断。新24槽与旧12槽分别列示，未合并独立样本。', '',
             '|槽|repeat|N|收据状态|C|query|UNKNOWN原因|异常类型|', '|---|---:|---:|---|---|---|---|---|']
    for row in current['rows']:
        values = [row['id'], row.get('repeat_id'), row['exact_rows'], row['evidence_disposition'],
                  row['C_status'], row['query_verdict'], row['query_unknown_reason'], row['error_type']]
        lines.append('|' + '|'.join(str(x).replace('|', '\\|').replace('\n', ' ') if x is not None else 'null' for x in values) + '|')
    lines += ['', '两遍各N的配对和所有预定高低界比较见JSON paired_diagnostics；缺收据/阶段未到不补0。',
              'C-model sanity永远不作query-SAT见证；重放仅记原收据证据，独立验证尚待完成。',
              '完整成本查看JSON逐槽成本、batch账与外层path/hash；phase嵌套、worker/CHILDREN及outer范围不重复相加。',
              '外层time/exit收据未在此工具内做schema认证，最终生命周期成本结论仍待root及独审。', '',
              '## 旧第06轮完整12槽（历史，未与新槽合并）', '',
              '|槽|N|C|query|收据状态|', '|---|---:|---|---|---|']
    for row in historical['rows']:
        lines.append('|'+ '|'.join(str(row[k]) if row[k] is not None else 'null' for k in ('id','exact_rows','C_status','query_verdict','evidence_disposition'))+'|')
    output = args.out.resolve()
    if output.parent != (ROOT / 'analysis').resolve() or output.exists():
        raise ValueError('OUTPUT_MUST_BE_A_FRESH_DIRECT_CHILD_OF_ROUND16_ANALYSIS')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'derived_results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    (output / 'RESULTS.zh.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'output': str(output), 'planned_current': 24, 'planned_historical_separate': 12,
                      'independent_review': 'PENDING'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
