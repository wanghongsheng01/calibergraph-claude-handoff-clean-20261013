"""Standard-library contract tests. No Polygon imports, SQL, solver, or child processes."""
import ast
import copy
import datetime
import io
import itertools
import json
from pathlib import Path
import random
import sys
import tempfile
import traceback
from types import SimpleNamespace
import unittest

from build_adapter import PINS, adapt_environment, adapt_formula, build, digest

HERE = Path(__file__).resolve().parent
SOURCE = (Path(sys.argv.pop(1)).resolve() if len(sys.argv) > 1 else
          HERE.parent / 'calibergraph_strong_baseline_prep_20261011_02/sources_local/polygon')
DENIED = []


def no_process_or_network(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.fork', 'os.forkpty',
                 'os.posix_spawn', 'os.exec', 'pty.spawn', 'socket.connect', 'socket.bind'}:
        DENIED.append(event)
        raise AssertionError('test attempted forbidden operation: ' + event)


sys.addaudithook(no_process_or_network)


def read(rel):
    p = SOURCE / (rel + '.txt')
    if not p.exists():
        p = SOURCE / rel
    data = p.read_bytes()
    assert digest(data) == PINS[rel]
    return data.decode()


ENV = read('polygon/environment.py')
FORMULA = read('polygon/smt/formula.py')
ADAPTED = adapt_environment(ENV)


def method(source, cls, name):
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == cls)
    return next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == name)


def load_method(source, cls, name, namespace):
    node = method(source, cls, name)
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), '<extracted-test-method>', 'exec'), namespace)
    return namespace[name]


def structure(node):
    return ast.dump(node, include_attributes=False)


class Clock:
    tick = 0

    @classmethod
    def now(cls):
        cls.tick += 1
        return datetime.datetime(2000, 1, 1) + datetime.timedelta(microseconds=cls.tick)


class Proxy(dict):
    """Copy-on-get/set models relevant Manager dict serialization, without IPC."""
    def __setitem__(self, key, value):
        super().__setitem__(key, copy.deepcopy(value))

    def __getitem__(self, key):
        return copy.deepcopy(super().__getitem__(key))


class Manager:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def dict(self):
        return Proxy()


class Process:
    """Task-body seam only, deliberately not a process/runtime equivalence model."""
    def __init__(self, target, args):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)

    def join(self, budget):
        pass

    def is_alive(self):
        return False


def fixture(outcome='NEQ', stage=None):
    trace = []
    class Parser:
        def parse(self, query):
            trace.append(('parse', query))
            if stage == 'parse':
                raise ValueError('parse fixture')
            return query

        def parse_query(self, query):
            trace.append(('parse_query', query))
            return AST(query)

    class AST:
        def __init__(self, query):
            self.query = query

        def accept(self, encoder):
            trace.append(('encode', self.query, encoder.curr_query_id, random.random()))
            if stage == 'encode':
                raise ValueError('encode fixture')
            return self.query

    class Prover:
        checking_time = 0.125

        def evaluate_table(self, table, db, env):
            trace.append(('evaluate', table))
            if stage == 'evaluate' and table == 'base':
                raise ValueError('evaluate fixture')
            return [['fixture_column'], [None], [7]]

    class Formula:
        timeout = 60

        def append(self, value, label):
            trace.append(('append', label, value))

        def solve(self, mode, ret):
            trace.append(('solve', mode, self.timeout))
            ret['iters'] = 1
            ret['solving_time_per_iter'] = [0.125]
            if stage == 'solve':
                raise ValueError('solve fixture')
            return None if outcome == 'EQU' else Prover()

        def search(self, outputs, ret):
            return self.solve('UA', ret)

        def solve_precise(self, ret):
            return self.solve('precise', ret)

    env = SimpleNamespace(formulas=Formula(), schema=[{'TableName': 'Fixture'}],
                          db=SimpleNamespace(schemas={0: 'base'}), initialized=False,
                          time_budget=60, clear=lambda: trace.append(('clear',)),
                          o1_eq_o2=lambda a, b: ('eq', a, b))
    namespace = {'SQLParser': Parser, 'datetime': SimpleNamespace(datetime=Clock),
                 'QueryEncoder': lambda env: env, 'Not': lambda value: ('not', value),
                 'traceback': traceback,
                 'logger': SimpleNamespace(error=lambda msg: None, debug=lambda msg: None),
                 'multiprocess': SimpleNamespace(Manager=Manager, Process=Process)}
    return env, namespace, trace


class Tests(unittest.TestCase):
    def test_task_body_byte_identical_and_other_methods_unchanged(self):
        old = method(ENV, 'Environment', 'check')
        new = method(ADAPTED, 'Environment', 'check')
        oldtask = next(n for n in old.body if isinstance(n, ast.FunctionDef))
        newtask = next(n for n in new.body if isinstance(n, ast.FunctionDef))
        self.assertEqual(ast.get_source_segment(ENV, oldtask), ast.get_source_segment(ADAPTED, newtask))
        oldclass = next(n for n in ast.parse(ENV).body if isinstance(n, ast.ClassDef))
        for node in oldclass.body:
            if isinstance(node, ast.FunctionDef) and node.name != 'check':
                self.assertEqual(structure(node), structure(method(ADAPTED, 'Environment', node.name)))
        self.assertFalse(any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                             and n.value.id == 'multiprocess' for n in ast.walk(new)))

    def test_solver_logic_ast_identical_except_precise_timeout(self):
        expected = ast.parse(FORMULA)
        precise = method(FORMULA, 'FormulaManager', 'solve_precise')
        for node in ast.walk(expected):
            if isinstance(node, ast.JoinedStr) and node.lineno >= precise.lineno:
                if ast.unparse(node) == "f'-T:300'":
                    node.values = ast.parse("f'-T:{self.timeout}'", mode='eval').body.values
        self.assertEqual(structure(expected), structure(ast.parse(adapt_formula(FORMULA))))

    def test_results_order_queries_and_random_trace_at_task_seam(self):
        for mode in [False, True]:
            for outcome, stage in [('NEQ', None), ('EQU', None), ('ERR', 'encode'),
                                   ('ERR', 'solve'), ('ERR', 'evaluate')]:
                with self.subTest(mode=mode, outcome=outcome, stage=stage):
                    runs = []
                    for source in [ENV, ADAPTED]:
                        env, namespace, trace = fixture(outcome, stage)
                        env.formulas.timeout = 3
                        fn = load_method(source, 'Environment', 'check', namespace)
                        random.seed(2718)
                        args = {'solver_timeout_seconds': 3} if source == ADAPTED else {}
                        result = fn(env, 'opaque original q1', 'opaque original q2', mode, **args)
                        ret = {k: v for k, v in result[4].items() if k not in {'total_time', 'complete_time'}}
                        runs.append((result[:3], ret, trace, random.getstate()))
                    self.assertEqual(runs[0], runs[1])

    def test_single_use_including_error_and_parse_failure(self):
        for stage in [None, 'parse', 'encode', 'solve', 'evaluate']:
            env, namespace, trace = fixture(stage=stage)
            fn = load_method(ADAPTED, 'Environment', 'check', namespace)
            if stage == 'parse':
                with self.assertRaises(ValueError):
                    fn(env, 'q1', 'q2', solver_timeout_seconds=3)
            else:
                fn(env, 'q1', 'q2', solver_timeout_seconds=3)
            before = copy.deepcopy(trace)
            with self.assertRaises(RuntimeError):
                fn(env, 'q1', 'q2', solver_timeout_seconds=3)
            self.assertEqual(before, trace)

    def test_timeout_required_and_invalid_values_fail_before_parse(self):
        for timeout in [0, -1, True, 3.5, '3', None]:
            env, namespace, trace = fixture()
            fn = load_method(ADAPTED, 'Environment', 'check', namespace)
            with self.assertRaises(ValueError):
                fn(env, 'q1', 'q2', solver_timeout_seconds=timeout)
            self.assertEqual(trace, [])
        with self.assertRaises(TypeError):
            fn(env, 'q1', 'q2')

    def test_precise_captures_same_timeout_and_unchanged_dump(self):
        for source, seconds in [(FORMULA, 300), (adapt_formula(FORMULA), 3)]:
            calls = []
            class Prover:
                def __init__(self, **kwargs):
                    calls.append(kwargs)

                def check(self, formula):
                    calls.append(formula)
                    return False
            fn = load_method(source, 'FormulaManager', 'solve_precise', {'SMTLIBv2': Prover})
            obj = SimpleNamespace(timeout=3, init_label_table_id_bidict=lambda: None,
                                  formulas={'ic': 1, 'neq': 2}, labels_considered=set(),
                                  dump=lambda: 'opaque unchanged SMT text')
            self.assertIsNone(fn(obj, {}))
            self.assertEqual(calls, [{'executable_path': 'z3',
                                     'executable_options': ['--in', f'-T:{seconds}']},
                                    'opaque unchanged SMT text'])

    def test_actual_cover_ua_generator_random_stream(self):
        values = []
        for source in [FORMULA, adapt_formula(FORMULA)]:
            fn = load_method(source, 'FormulaManager', 'cover_ua', {'random': random, 'itertools': itertools})
            obj = SimpleNamespace(label_to_table_id={'x': 0},
                                  env=SimpleNamespace(db=SimpleNamespace(schemas={
                                      0: SimpleNamespace(bound=4, lineage='Grouped')})))
            random.seed(99)
            values.append((list(fn(obj, 'x', tops_ratio=0.25)), random.getstate()))
        self.assertEqual(*values)

    def test_build_hash_gate_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'copy'
            manifest = build(SOURCE, dest)
            self.assertEqual(len(manifest), 3)
            self.assertEqual((dest / 'polygon/smt/provers/smtlibv2.py').read_text(), read('polygon/smt/provers/smtlibv2.py'))
            with self.assertRaises(FileExistsError):
                build(SOURCE, dest)
            bad = Path(tmp) / 'bad'
            for rel in PINS:
                p = bad / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(read(rel) + '\n')
            rejected = Path(tmp) / 'rejected'
            with self.assertRaises(ValueError):
                build(bad, rejected)
            self.assertFalse(rejected.exists())


if __name__ == '__main__':
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print(stream.getvalue())
    evidence = {'tests_run': result.testsRun, 'failures': len(result.failures),
                'errors': len(result.errors), 'successful': result.wasSuccessful(),
                'forbidden_audit_events': DENIED,
                'polygon_imports': 0, 'sql_executions': 0, 'solver_executions': 0,
                'test_created_child_processes': 0,
                'scope': 'AST and dependency-injected task seams, not real encoding or solving'}
    (HERE / 'TEST_RESULTS.json').write_text(json.dumps(evidence, indent=2) + '\n')
    (HERE / 'TEST_OUTPUT.txt').write_text(stream.getvalue())
    sys.exit(0 if result.wasSuccessful() and not DENIED else 1)
