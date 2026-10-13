#!/usr/bin/env python3
"""Freeze a tiny, source-grouped JOIN development registry; never run SQL/solvers.

Only stdlib, offline, one process. Source SQL/schema/constraint values are copied
unchanged. The reserve selector and cases remain in data/reserve_private/.
That directory is a workflow boundary, NOT a security boundary or blind test.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
OLD = Path('/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011')
SOURCE = OLD / 'public_leetcode/leetcode.jsonlines'
COMMIT = '3b99928bf976c11cb59c9db6a177adba21f75798'
EXPECTED_SHA = 'b97fc1293701682a25a2f6345f3630b3482ce49912463a7f4b76ab52665a13c9'
URL = 'https://raw.githubusercontent.com/VeriEQL/VeriEQL/' + COMMIT + '/benchmarks/leetcode/leetcode.jsonlines'
DEV_GROUPS = ['182', '614', '1075', '1581', '1587', '1715']
ALLOWED_KEYS = {'file', 'index', 'schema', 'constraint', 'pair'}
MAX_RSS = 256 * 1024 * 1024
START = time.monotonic()

def digest(b):
    return hashlib.sha256(b).hexdigest()

def canonical(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def sha_file(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            h.update(block)
            guard()
    return h.hexdigest()

def guard():
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != 'darwin':
        peak *= 1024
    if peak > MAX_RSS:
        raise RuntimeError('RSS_OBSERVATION_EXCEEDS_256_MIB')
    if time.monotonic() - START > 50:
        raise RuntimeError('WALL_BUDGET_50_SECONDS')
    return peak

def write_new(p, b, private=False):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)
    if private:
        p.chmod(0o600)

def write_json(p, v, private=False):
    write_new(p, json.dumps(v, ensure_ascii=False, indent=2).encode() + b'\n', private)

def row_out(case, n, raw, split, ordinal, source_sha):
    return {
        'id': ('dev_' if split == 'DEVELOPMENT' else 'reserve_') + f'{ordinal:02d}',
        'split': split,
        'source_group_id': 'leetcode:' + case['file'],
        'source': {'dataset': 'VeriEQL LeetCode', 'repository': 'VeriEQL/VeriEQL',
                   'commit': COMMIT, 'url': URL, 'local_path': str(SOURCE),
                   'file_sha256': source_sha, 'line_1based': n,
                   'raw_line_sha256': digest(raw)},
        'source_record': case,
        'original_sql_sha256': [digest(q.encode()) for q in case['pair']],
        'schema_sha256': digest(canonical(case['schema'])),
        'constraint_sha256': digest(canonical(case['constraint'])),
        'selection_basis': 'predeclared source group; minimum (maximum SQL length, total SQL length, source line) among upstream pairs with JOIN and SUM/COUNT in the same query; no semantic result used',
        'taxonomy': {
            'query': 'UNMODIFIED_PUBLIC_BENCHMARK_QUERY',
            'pair': 'UNMODIFIED_UPSTREAM_PAIR_PAIR_CONSTRUCTION_NOT_REVALIDATED',
            'natural_defect': 'UNKNOWN_NO_HIDDEN_GOLD',
            'adversarial_fixture': False,
            'human_or_production_origin_per_query': 'NOT_INDEPENDENTLY_ESTABLISHED'},
        'exposure': 'PRIOR_FULL_V3_V4_APPLICABILITY_SCAN; CURRENT_SOURCE_STRUCTURE_SELECTION',
        'constraint_validation': 'NOT_RUN',
        'schema_replay': 'NOT_RUN',
        'semantic_label': None,
        'solver_verdict': None,
        'status': 'HOLD_NO_AUTOMATIC_PROMOTION'
    }

def build():
    out = ROOT / 'data'
    selector = json.loads((out / 'reserve_private/selection.private.json').read_text())
    reserve_groups = selector['source_problem_ids']
    if len(DEV_GROUPS) > 8 or len(reserve_groups) < 4 or set(DEV_GROUPS) & set(reserve_groups):
        raise RuntimeError('INVALID_GROUP_SPLIT')
    if len(set(reserve_groups)) != len(reserve_groups):
        raise RuntimeError('DUPLICATE_RESERVE_GROUP')
    source_sha = sha_file(SOURCE)
    if source_sha != EXPECTED_SHA:
        raise RuntimeError('SOURCE_IDENTITY_MISMATCH')
    selected = set(DEV_GROUPS + reserve_groups)
    best = {}
    counts = collections.Counter()
    group_counts = collections.Counter()
    eligible_groups = set()
    errors = []
    # This is JSONL/token inventory only, not SQL parsing/applicability.
    with SOURCE.open('rb') as f:
        for n, raw in enumerate(f, 1):
            counts['source_rows_seen'] += 1
            guard()
            try:
                r = json.loads(raw)
                if set(r) != ALLOWED_KEYS or not isinstance(r['schema'], dict):
                    raise ValueError('SOURCE_FIELDSET_OR_SCHEMA')
                if len(r['pair']) != 2 or not all(isinstance(q, str) for q in r['pair']):
                    raise ValueError('PAIR_STRUCTURE')
                group = Path(r['file']).stem
                group_counts[group] += 1
                qs = r['pair']
                structural = any(re.search(r'\bJOIN\b', q, re.I) and re.search(r'\b(?:SUM|COUNT)\s*\(', q, re.I) for q in qs)
                if not structural:
                    continue
                counts['token_candidate_pairs'] += 1
                eligible_groups.add(group)
                if group not in selected:
                    continue
                score = (max(map(len, qs)), sum(map(len, qs)), n)
                if group not in best or score < best[group][0]:
                    best[group] = (score, r, n, raw)
            except (ValueError, TypeError, KeyError) as e:
                errors.append({'line_1based': n, 'raw_line_sha256': digest(raw), 'error': type(e).__name__ + ': ' + str(e)})
    dev, reserve, attempts = [], [], []
    for split, groups, target in [('DEVELOPMENT', DEV_GROUPS, dev), ('RESERVE_CANDIDATE_HOLD', reserve_groups, reserve)]:
        for ordinal, group in enumerate(groups, 1):
            # Missing/invalid selected groups remain failures, never replacements.
            if group not in best:
                attempts.append({'split': split, 'ordinal': ordinal, 'status': 'FAILED_NO_STRUCTURAL_CANDIDATE', 'replacement_allowed': False})
                continue
            _, r, n, raw = best[group]
            item = row_out(r, n, raw, split, ordinal, source_sha)
            target.append(item)
            attempts.append({'split': split, 'ordinal': ordinal, 'status': 'REGISTERED_NOT_REPLAYED', 'case_sha256': digest(canonical(item)), 'replacement_allowed': False})
    dev_path = out / 'development.jsonl'
    reserve_path = out / 'reserve_private/candidates.private.jsonl'
    write_new(dev_path, b''.join(canonical(r) + b'\n' for r in dev))
    write_new(reserve_path, b''.join(canonical(r) + b'\n' for r in reserve), True)
    write_json(out / 'registration_attempts.json', attempts)
    write_json(out / 'source_json_errors.json', errors)
    manifest = {
        'status': 'HOLD_NO_AUTOMATIC_PROMOTION',
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'frozen_source': {'path': str(SOURCE), 'url': URL, 'sha256': source_sha, 'bytes': SOURCE.stat().st_size},
        'inventory': dict(counts, source_groups=len(group_counts), token_candidate_groups=len(eligible_groups), json_structure_errors=len(errors)),
        'development': {'path': str(dev_path.relative_to(ROOT)), 'source_groups': len(dev), 'pairs': len(dev), 'query_slots': len(dev)*2, 'sha256': sha_file(dev_path)},
        'reserve': {'path': str(reserve_path.relative_to(ROOT)), 'source_groups': len(reserve), 'pairs': len(reserve), 'query_slots': len(reserve)*2, 'sha256': sha_file(reserve_path), 'disclosure': 'NO SQL/GROUP IDENTITIES/LABELS/RESULTS IN AUTHOR SUMMARY; SAME UID AND SHARED WORKSPACE ARE NOT OS ISOLATION'},
        'group_unit': 'LeetCode original source problem file label; all belong to one upstream dataset family; not independently proven semantic independence',
        'selection': {'rule': 'Source groups fixed before examining selected SQL and before replay. Per-group choose shortest maximum pair member, then shortest total length, then earliest source line, satisfying JOIN+SUM/COUNT token predicate. This is a purposive development sample, not a random or representative estimate.', 'development_problem_ids': DEV_GROUPS, 'no_replacement_after_replay': True},
        'exposure': 'All 48910 frozen query slots were already inspected by prior v3/v4 applicability scans. This agent read handoff, source receipt, upstream README, final applicability markdown, and initially emitted the large final applicability JSON (truncated output included parser error SQL); these are exposure, not selection labels. No final test labels or solver per-case verdict files used.',
        'read_boundaries': 'Source file keys explicitly allowlisted. No .out, solver logs, hidden labels, credentials, or network downloads read. No parser/solver imported.',
        'schema_replay': 'NOT_RUN; original schema and constraint retained for independent replay. DDL translation must not be mislabeled an original schema file.',
        'promotion_conditions': ['Independent evaluator and trustworthy hidden gold required for accuracy/defect claims', 'Source-group disjointness must be audited beyond file labels', 'Author-accessible source and prior scan exposure must remain disclosed', 'Lock protocol/code before independent terminal evaluation', 'Original SQL and full schema/constraint must remain unchanged; preserve failed and unsupported rows', 'Use unseen independently controlled sources for an unseen-test claim'],
        'resources': {'one_process': True, 'wall_seconds': time.monotonic()-START, 'observed_peak_rss_bytes': guard(), 'rss_limit_bytes': MAX_RSS, 'wall_alarm_seconds': 55, 'enforcement': 'hard SIGALRM wall stop plus cooperative per-line/64KiB RSS observations; not OS hard memory isolation'},
        'code_sha256': sha_file(Path(__file__)),
        'backup': 'BLOCKED_BY_EXPLICIT_LOCAL_ONLY_NO_UPLOAD',
        'datahub': 'datahub list checked; no module for this frozen VeriEQL snapshot; canonical registration outside allowed write scope, DATAHUB_REGISTRATION_BLOCKED'
    }
    write_json(ROOT / 'governance/registry_manifest.json', manifest)
    print(json.dumps({'status': manifest['status'], 'development_groups': len(dev), 'reserve_groups': len(reserve), 'selected_registration_attempts': len(attempts), 'source_json_errors': len(errors), 'wall_seconds': manifest['resources']['wall_seconds'], 'peak_rss_bytes': manifest['resources']['observed_peak_rss_bytes']}))

def verify():
    m = json.loads((ROOT / 'governance/registry_manifest.json').read_text())
    checks = {'source_hash': sha_file(SOURCE) == m['frozen_source']['sha256']}
    selected = {}
    for role in ('development', 'reserve'):
        p = ROOT / m[role]['path']
        checks[role + '_hash'] = sha_file(p) == m[role]['sha256']
        with p.open() as f:
            rows = [json.loads(line) for line in f]
        checks[role + '_count'] = len(rows) == m[role]['pairs']
        for row in rows:
            selected[row['source']['line_1based']] = row
    with SOURCE.open('rb') as f:
        for n, raw in enumerate(f, 1):
            if n in selected:
                row = selected[n]
                checks['source_line_' + str(n)] = digest(raw) == row['source']['raw_line_sha256'] and json.loads(raw) == row['source_record'] and [digest(q.encode()) for q in row['source_record']['pair']] == row['original_sql_sha256']
            guard()
    # Never print reserve line numbers, group identifiers, SQL, or labels.
    print(json.dumps({'status': 'IDENTITY_VERIFIED' if all(checks.values()) else 'FAILED', 'checks': len(checks), 'failed_checks': sum(not v for v in checks.values()), 'peak_rss_bytes': guard(), 'wall_seconds': time.monotonic()-START}))
    return 0 if all(checks.values()) else 1

if __name__ == '__main__':
    signal.alarm(55)
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build', 'verify'])
    args = parser.parse_args()
    sys.exit(verify() if args.action == 'verify' else build())
