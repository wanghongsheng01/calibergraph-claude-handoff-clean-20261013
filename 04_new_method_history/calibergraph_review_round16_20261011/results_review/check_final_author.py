"""Read-only final author hash/provenance checks; writes reviewer metadata only."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
NEW = ROOT / 'calibergraph_next_20261011_16'
REVIEW = OUT.parent
inputs = {}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    path = Path(path)
    inputs[str(path)] = digest(path)
    return json.loads(path.read_text())

def verify_manifest(path, count):
    data = read(path)
    files = data['files']
    assert len(files) == count
    assert len({x['path'] for x in files}) == count
    for item in files:
        p = Path(item['path'])
        if not p.is_absolute():
            p = Path(path).parent / p
        assert digest(p) == item['sha256'], str(p)
        if 'bytes' in item:
            assert p.stat().st_size == item['bytes'], str(p)
    return {'path': str(path), 'sha256': digest(path), 'verified_files': count, 'mismatches': []}

manifest = NEW/'analysis/AUTHOR_RESULTS_MANIFEST.json'
assert digest(manifest) == '76be43aff6f662cf913f9a4695ba36ad0d0fa43ceb5dcda0db8a341756726107'
author = verify_manifest(manifest, 7)
report = NEW/'analysis/RESULTS.zh.md'
assert digest(report) == 'd2609b50971c9237eb00fd8c07ecd2f0c8bed82d09942419c6adfbbdcd5728f8'
inputs[str(report)] = digest(report)

provenance_path = NEW/'analysis/RAW_EVIDENCE_PROVENANCE.json'
provenance = verify_manifest(provenance_path, 170)
raw = read(provenance_path)
assert {x['path'] for x in raw['files']} == {str(p) for p in (NEW/'runs/diagnostic_01').rglob('*') if p.is_file()}
assert raw['raw_payload_uploaded'] is False
assert raw['recovery_status'] == 'LOCAL_ONLY_HASH_IDENTIFIED_RAW_EVIDENCE'

frozen = verify_manifest(NEW/'protocols/generation_replay.freeze.json', 909)
old15 = verify_manifest(ROOT/'calibergraph_next_20261011_15/ROUND15_RESOURCE_STOP_MANIFEST.json', 37)
old13 = verify_manifest(ROOT/'calibergraph_next_20261011_13/ROUND13_FAILED_LAUNCH_MANIFEST.json', 30)

allow = read(REVIEW/'allowed_finalization_changes.json')
disabled_manifest = NEW/'implementation/AUTHOR_DISABLED_MANIFEST.json'
assert digest(disabled_manifest) == allow['author_disabled_manifest_sha256']
disabled = read(disabled_manifest)
assert digest(NEW/'author_snapshot_disabled/implementation/AUTHOR_DISABLED_MANIFEST.json') == digest(disabled_manifest)
source_differences = []
disabled_map = {x['path']: x['sha256'] for x in disabled['files']}
for item in disabled['old_source_hashes']:
    name = Path(item['path']).name
    before = NEW/'author_snapshot_disabled/implementation'/name
    after = NEW/'implementation'/name
    before_bytes, after_bytes = before.read_bytes(), after.read_bytes()
    inputs[str(before)], inputs[str(after)] = digest(before), digest(after)
    assert digest(before) == disabled_map[str(after)]
    if name == 'generation_common.py':
        assert before_bytes.count(b'EXECUTION_ENABLED = False') == 1
        assert after_bytes == before_bytes.replace(b'EXECUTION_ENABLED = False', b'EXECUTION_ENABLED = True')
    else:
        assert before_bytes == after_bytes
    source_differences.append({'file': name, 'before_sha256': digest(before), 'after_sha256': digest(after), 'allowed': True})
before_protocol_path = NEW/'author_snapshot_disabled/generation_replay.draft.json'
assert digest(before_protocol_path) == allow['disabled_protocol_sha256']
before_protocol = read(before_protocol_path)
after_protocol = read(NEW/'protocols/generation_replay.registered.json')

def differences(a, b, prefix=''):
    if isinstance(a, dict) and isinstance(b, dict):
        assert a.keys() == b.keys(), prefix
        return [p for k in a for p in differences(a[k], b[k], prefix+'.'+k if prefix else k)]
    return [] if a == b else [prefix]

changed = differences(before_protocol, after_protocol)
assert set(changed) == set(allow['permitted_protocol_changes'])
assert before_protocol['status'] == 'DRAFT_DISABLED' and after_protocol['status'] == 'REGISTERED'
assert before_protocol['registered_utc'] is None and after_protocol['registered_utc']
ledger = read(NEW/'scheduling/CLOSED_OBSERVATION_LEDGER.json')
for field, receipt_field in [
    ('prior_resource_observation_measured_cpu_seconds', 'measured_cpu_sample_s'),
    ('prior_resource_observation_tail_reserve_seconds', 'unmeasured_final_receipt_exit_tail_reserve_s'),
    ('prior_resource_observation_cpu_charge_seconds', 'cpu_charge_s')
]:
    assert abs(after_protocol['supervisor'][field] - sum(x[receipt_field] for x in ledger['observations'])) < 1e-9
original_freeze = read(ROOT/'calibergraph_next_20261011_06/protocols/generation_replay.freeze.json')
current_freeze = read(NEW/'protocols/generation_replay.freeze.json')
original_map = {x['path']: x['sha256'] for x in original_freeze['files']}
current_map = {x['path']: x['sha256'] for x in current_freeze['files']}
assert len(original_map) == 880 and len(current_map) == 909
assert all(current_map[p] == h for p, h in original_map.items())

sealed = []
for path, count in [(REVIEW/'SHA256SUMS.preexec_outputs', 9), (REVIEW/'waiting_followup/SHA256SUMS.outputs', 3)]:
    inputs[str(path)] = digest(path)
    lines = path.read_text().splitlines()
    assert len(lines) == count
    for line in lines:
        expected, p = line.split('  ', 1)
        p = Path(p)
        if not p.is_absolute():
            p = ROOT / p
        assert digest(p) == expected, str(p)
    sealed.append({'path': str(path), 'sha256': digest(path), 'files_unchanged': count})

independent = read(OUT/'INDEPENDENT_RAW_RESULTS.json')
cost = read(OUT/'COST_BOUNDARY_EVIDENCE.json')
assert independent['all_assertions_pass'] and cost['passed'] and not cost['issues']
assert independent['new_query_counts'] == {'unsat': 14, 'unknown': 4, 'NOT_REACHED': 6}
assert collections.Counter(r['query'] or 'NOT_REACHED' for r in independent['historical_rows_separate']) == {'unsat': 5, 'unknown': 4, 'NOT_REACHED': 3}
old_unknowns = collections.Counter(r['unknown_reason'] for r in independent['historical_rows_separate'] if r['query'] == 'unknown')
assert old_unknowns == {'timeout': 2, 'out of memory': 2}, old_unknowns
physical_rows = 0
for row in independent['current_rows']:
    if row['saved_C_sanity_values_independently_checked']:
        worker = read(NEW/'runs/diagnostic_01'/f"case_{row['slot']:02d}"/'results.json')
        db = worker['record']['attempts'][0]['contract_model_sanity']['replay']['concrete_database']
        physical_rows += sum(len(values) for values in db.values())
assert physical_rows == 72

result = {
    'schema': 'calibergraph.round16.final_author_crosscheck.v1',
    'reviewer': '/root/round16_independent',
    'decision': 'ACCEPT_FINAL_AUTHOR_READOUT_WITH_STATED_SCOPE',
    'issues': [],
    'author_manifest': author,
    'author_report_sha256': digest(report),
    'local_raw_provenance': provenance,
    'raw_directory_membership_exact': True,
    'runtime_freeze': frozen,
    'allowed_finalization': {
        'allowed_source_differences': source_differences,
        'only_protocol_fields_changed': changed,
        'observation_fees_match_complete_ledger': True,
        'round06_bindings_retained': 880,
        'new_bindings': 29
    },
    'old15': old15,
    'old13': old13,
    'prior_review_seals': sealed,
    'physical_rows_in_existing_C_sanity_models': physical_rows,
    'old06_unknown_reasons': dict(old_unknowns),
    'manual_readout_review': {
        'all24_and_old12_denominators_preserved': True,
        'valid_prequery_error_receipts_not_dropped': True,
        'null_not_reached_costs_not_zero': True,
        '700ms_parameter_distinguished_from_actual_wall': True,
        'cost_reserves_overlap_and_postanalysis_exclusion_explicit': True,
        'mature_source_SQL_identity_proof_not_timed_baseline_or_encoder_certification': True,
        'exact_not_up_to_and_exposed_dev_not_independent_test': True,
        'NONE_NO_GO_no_paper_method_promotion': True,
        'clean_restore_and_DataHub_blocks_remain': True
    },
    'evidence_limits': [
        'Local receipts/hash association does not by itself independently establish syscall O_EXCL or absence of all other tool calls; root retains original request/completion chunks d74bf2/93b879.',
        'Earlier literature/public corpus statements are carried with prior review provenance; no new literature retrieval or full corpus reexecution was performed.',
        'Raw payload upload status is the author declaration and local provenance policy; this review does not inspect remote Git contents or certify clean restore.',
        'No scientific code, SQL, SMT, new model, target import/compile or resource probe was executed.'
    ],
    'input_hashes': inputs
}
(OUT/'AUTHOR_REPORT_CROSSCHECK.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('input_hashes', 'manual_readout_review', 'evidence_limits')}, ensure_ascii=False, indent=2))
