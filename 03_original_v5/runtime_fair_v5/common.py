"""Shared pinned-input and witness helpers; no third-party import at import time."""
import builtins
from collections import Counter
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sqlite3
import sys
import time

ARMS = ("official", "official_generic_smt", "flat", "product", "selector", "official_canonical_sql")
CANDIDATES = ("flat", "product", "selector")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(262144), b""):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    import os
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write("\n"); f.flush(); os.fsync(f.fileno())
    tmp.replace(path)


def verify_lock(path, expected_hash):
    if sha(path) != expected_hash:
        raise ValueError("runtime lock changed")
    lock = json.loads(Path(path).read_text())
    if lock.get("schema_version") != 1 or lock.get("status") != "STATIC_REVIEWED_READY_FOR_LOCAL_RUN":
        raise ValueError("runtime lock not reviewed/ready")
    if lock["expected_native_version"] != [4, 12, 0, 0] or not lock["files"]:
        raise ValueError("wrong native or empty file lock")
    for raw, expected in lock["files"].items():
        p = Path(raw)
        if not p.is_absolute() or p != p.resolve() or not p.is_file() or sha(p) != expected:
            raise ValueError("runtime file changed, missing, or symlinked: " + raw)
    for raw in [lock["source_root"], lock["binding_root"], lock["support_root"], *lock["dependency_roots"]]:
        root = Path(raw)
        actual = {str(p) for p in root.rglob("*") if p.is_file()}
        expected = {p for p in lock["files"] if Path(p).is_relative_to(root)}
        if actual != expected or any(p.is_symlink() for p in root.rglob("*")):
            raise ValueError("runtime inventory mismatch: " + raw)
    if lock["native_path"] not in lock["files"] or lock["kernel_path"] not in lock["files"]:
        raise ValueError("native/kernel missing from lock")
    required_programs = ("common.py", "worker.py", "supervisor.py", "query_differential.py", "contract_reference.py")
    expected_program_paths = {str(Path(__file__).parent / name) for name in required_programs}
    if set(lock.get("runtime_programs", {})) != expected_program_paths:
        raise ValueError("v5 runtime program inventory missing or wrong")
    for raw, expected in lock["runtime_programs"].items():
        if lock["files"].get(raw) != expected or sha(raw) != expected:
            raise ValueError("v5 program absent from unified source lock: " + raw)
    return lock


def load_runtime(lock, checkpoint, report):
    report["native_load"] = "ATTEMPTED_EFFECT_UNKNOWN"
    checkpoint("NATIVE_LOAD")
    library = ctypes.CDLL(lock["native_path"])
    report["native_load"] = "LOADED"
    builtins.Z3_LIB_DIRS = [str(Path(lock["native_path"]).parent)]
    sys.path[:0] = [lock["binding_root"], lock["support_root"], *lock["dependency_roots"], lock["source_root"]]
    report["environment_import"] = "ATTEMPTED_EFFECT_UNKNOWN"
    checkpoint("ENVIRONMENT_IMPORT")
    import z3
    from z3 import z3core
    defaults = z3core.Z3_get_version.__defaults__
    if len(defaults) != 1:
        raise ValueError("unexpected generated binding")
    binding_pointer = ctypes.cast(defaults[0].f, ctypes.c_void_p).value
    native_pointer = ctypes.cast(library.Z3_get_version, ctypes.c_void_p).value
    if not binding_pointer or binding_pointer != native_pointer:
        raise ValueError("native entry point identity mismatch")
    if list(z3.get_version()) != lock["expected_native_version"]:
        raise ValueError("native version mismatch")
    if not Path(z3.__file__).resolve().is_relative_to(Path(lock["binding_root"])):
        raise ValueError("Z3 binding origin mismatch")
    from environment import Environment
    import constants
    if not Path(sys.modules["environment"].__file__).resolve().is_relative_to(Path(lock["source_root"])):
        raise ValueError("Environment source origin mismatch")
    spec = importlib.util.spec_from_file_location("caliber_cost_kernel", lock["kernel_path"])
    kernel = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = kernel
    spec.loader.exec_module(kernel)
    z3.set_param("parallel.enable", False)
    z3.set_param("memory_max_size", 768)
    report["native_identity"] = {"pinned_path": lock["native_path"], "sha256": sha(lock["native_path"]),
                                 "version": list(z3.get_version()), "binding_pointer": binding_pointer,
                                 "pinned_pointer": native_pointer, "method": "same_process_function_identity_plus_locked_source"}
    report["environment_import"] = "IMPORTED"
    report["module_origins"] = {name: getattr(module, "__file__", None) for name, module in list(sys.modules.items())
                                if name.split(".")[0] in {"environment", "constants", "mo_sql_parsing", "mo_parsing", "mo_dots", "mo_imports", "mo_future", "ordered_set", "lark", "ujson", "yaml", "pkg_resources", "z3"}}
    checkpoint("RUNTIME_READY")
    return library, z3, constants, Environment, kernel


def ensure_raw_frontend(case, kernel):
    """Common gate for ALL arms; do not turn its rejection into fallback."""
    for sql in case["pair"]:
        kernel.ensure_raw_identifiers(case["schema"], sql)
    return {"status": "ADMITTED", "query_count": len(case["pair"]),
            "contract": "ASCII simple schema names without __ or case-fold collisions; raw SQL without backticks, double quotes or dollars",
            "scope": "conservative identifier-safety gate, not a proof of all upstream SQL semantics"}


class ContractStop(ValueError):
    """Typed no-pair outcome; the entire original contract is retained."""
    def __init__(self, decision, reason):
        super().__init__(reason)
        self.decision = decision


def new_env(case, Environment, constants):
    # Assign this object in the caller BEFORE any schema or IC work, so every
    # subsequent exception can clean it up. No raw IC compilation is permitted.
    return Environment(timer=False, generate_code=False, show_counterexample=False, dialect=constants.DIALECT.MYSQL)


def formula_sha(items):
    return hashlib.sha256("\n".join(item.sexpr() for item in items).encode()).hexdigest()


def json_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def apply_contract_bridge(env, case, z3, constants, start, checkpoint, record):
    """Original AST -> normalized copy -> actual upstream C, checked on BASE only.

    No original IC is ever passed to add_constraints. SAT/unknown XOR rejects the
    whole input. This establishes this bounded AST mapping, not source-text
    parser faithfulness or a general theorem about every upstream contract.
    """
    import contract_reference as reference
    if Path(reference.__file__).resolve() != Path(__file__).parent / "contract_reference.py":
        raise ValueError("contract reference module origin mismatch")
    record.update(status="ATTEMPTED_EFFECT_UNKNOWN", original_ast=case["constraint"],
                  original_ast_sha256=json_sha(case["constraint"]),
                  scope="registered source AST faithfulness; no source-text parser completeness claim",
                  base_only_sat={"status": "NOT_RUN"}, normalized_vs_reference={"status": "NOT_RUN"},
                  compilation={"status": "NOT_RUN"})
    checkpoint("CONTRACT_BRIDGE_PREPARE_ATTEMPT")
    try:
        prepared = reference.prepare(case["constraint"], case["schema"])
    except reference.UnverifiedContract as exc:
        record.update(status="UNVERIFIED_CONTRACT", reason=str(exc), unsupported_policy="WHOLE_CONTRACT_STOP_NO_DROP_NO_FALLBACK")
        raise ContractStop("UNVERIFIED_CONTRACT", str(exc)) from exc
    record.update(normalized_ast=prepared.normalized_ast, normalized_ast_sha256=json_sha(prepared.normalized_ast),
                  ledger=prepared.ledger, schema_roundtrip="SUPPORTED_UNIQUE_UPPERCASE_ENCODING",
                  reference_source_sha256=sha(Path(__file__).parent / "contract_reference.py"))
    checkpoint("CONTRACT_BRIDGE_PREPARED")
    if env.base_databases or env.DBMS_facts:
        raise ValueError("bridge requires a fresh empty Environment")
    for name, fields in case["schema"].items():
        env.create_database(attributes=fields, bound_size=case["exact_rows"][name], name=name)
    base_facts = list(env.DBMS_facts)
    bounds = sorted(env.bound_constraints, key=lambda term: term.sexpr())
    base = base_facts + bounds
    record["base_only"] = {"facts": [term.sexpr() for term in base], "sha256": formula_sha(base),
                           "tested_ic_included": False, "exact_rows": case["exact_rows"]}

    def check(slot, assertions):
        slot.update(status="ATTEMPTED_EFFECT_UNKNOWN", assertion_count=len(assertions), assertion_sha256=formula_sha(assertions))
        checkpoint("CONTRACT_BRIDGE_SOLVER_ATTEMPT")
        test = solver(z3, constants, start, maximum_ms=1000)
        test.add(*assertions)
        answer = str(test.check())
        slot["status"] = answer
        if answer == "unknown":
            slot["reason_unknown"] = test.reason_unknown()
        elif answer == "sat":
            model = test.model()
            if not all(z3.is_true(model.eval(term, model_completion=True)) for term in assertions):
                raise ValueError("contract bridge model violates submitted assertions")
        elif answer != "unsat":
            raise ValueError("unrecognized bridge solver answer")
        checkpoint("CONTRACT_BRIDGE_SOLVER_RETURNED")
        return answer

    if check(record["base_only_sat"], base) != "sat":
        record["status"] = "BASE_CONTRACT_UNVERIFIED"
        raise ContractStop("BASE_CONTRACT_UNVERIFIED", "base-only nonvacuity not established")
    try:
        intended = reference.emit_reference(prepared, env, constants)
    except reference.UnverifiedContract as exc:
        record.update(status="UNVERIFIED_CONTRACT", reason=str(exc))
        raise ContractStop("UNVERIFIED_CONTRACT", str(exc)) from exc
    record["compilation"]["status"] = "ATTEMPTED_EFFECT_UNKNOWN"
    checkpoint("NORMALIZED_CONTRACT_COMPILATION_ATTEMPT")
    env.add_constraints(prepared.normalized_ast)
    if [term.sexpr() for term in env.DBMS_facts[:len(base_facts)]] != [term.sexpr() for term in base_facts]:
        raise ValueError("upstream compilation altered base facts")
    if [term.sexpr() for term in sorted(env.bound_constraints, key=lambda term: term.sexpr())] != [term.sexpr() for term in bounds]:
        raise ValueError("upstream compilation altered base bounds")
    delta = list(env.DBMS_facts[len(base_facts):])
    actual = constants.And(*delta) if delta else constants.Z3_TRUE
    record["compilation"].update(status="COMPILED_NORMALIZED_COPY", original_ast_passed_to_upstream=False,
                                 delta_fact_count=len(delta), actual_formula=actual.sexpr(), reference_formula=intended.sexpr())
    xor = constants.Or(constants.And(actual, constants.Not(intended)), constants.And(constants.Not(actual), intended))
    answer = check(record["normalized_vs_reference"], base + [xor])
    if answer != "unsat":
        decision = "CONTRACT_BRIDGE_MISMATCH" if answer == "sat" else "CONTRACT_BRIDGE_UNVERIFIED"
        record["status"] = decision
        raise ContractStop(decision, "normalized upstream C versus original AST reference XOR: " + answer)
    if json_sha(case["constraint"]) != record["original_ast_sha256"]:
        raise ValueError("original contract input mutated")
    env.save_checkpoints()
    record.update(status="VERIFIED_BOUNDED_AST_BRIDGE", complete_facts_sha256=formula_sha(list(env.DBMS_facts) + bounds),
                  actual_contract="upstream compiler of normalized copy; same verified C for all six arms and differential",
                  no_pair_oracle_run=True)
    # This is a local object binding, not a portable cryptographic certificate.
    env._caliber_contract_bridge = {"record": record, "prepared": prepared, "schema": case["schema"]}
    checkpoint("CONTRACT_BRIDGE_VERIFIED")
    return record


def require_contract_bridge(env, record=None):
    attached = getattr(env, "_caliber_contract_bridge", None)
    if not attached or (record is not None and attached["record"] is not record):
        raise ContractStop("UNVERIFIED_CONTRACT", "same-Environment bridge record required")
    audit = attached["record"]
    current = list(env.DBMS_facts) + sorted(env.bound_constraints, key=lambda term: term.sexpr())
    if audit.get("status") != "VERIFIED_BOUNDED_AST_BRIDGE" or audit.get("complete_facts_sha256") != formula_sha(current):
        raise ContractStop("UNVERIFIED_CONTRACT", "audited complete contract facts changed or unavailable")
    return attached


def check_witness_contract(env, database):
    import contract_reference as reference
    if Path(reference.__file__).resolve() != Path(__file__).parent / "contract_reference.py":
        raise ValueError("contract reference module origin mismatch")
    attached = require_contract_bridge(env)
    result = reference.evaluate_reference(attached["prepared"], database)
    result["original_ast_sha256"] = attached["record"]["original_ast_sha256"]
    if result["holds"] is not True:
        raise ValueError("witness violates original source-AST contract reference")
    return result


def cpu_seconds():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime + r.ru_stime


def budget_ms(start):
    remaining = min(14 - cpu_seconds() - 0.35, 24 - (time.monotonic() - start) - 0.5)
    if remaining <= 0.05:
        raise TimeoutError("remaining shared CPU/wall budget exhausted")
    return max(1, int(remaining * 1000))


def solver(z3, constants, start, maximum_ms=None):
    result = z3.Solver(ctx=constants.Z3_CONTEXT)
    budget = budget_ms(start)
    result.set(timeout=min(budget, maximum_ms) if maximum_ms is not None else budget, threads=1)
    return result


def guard(env, z3, constants, start):
    facts = list(env.DBMS_facts) + sorted(env.bound_constraints, key=lambda expression: expression.sexpr())
    s = solver(z3, constants, start, maximum_ms=1000)
    s.add(*facts)
    consistency = str(s.check())
    alive = solver(z3, constants, start, maximum_ms=1000)
    alive.add(*facts)
    alive.add(constants.Or(*(env.DELETED_FUNCTION(row.SORT) for table in env.base_databases.values() for row in table)))
    deletion = str(alive.check())
    result = {"full_base_fact_count": len(facts), "consistency": consistency, "any_base_row_deleted": deletion,
              "base_fact_sha256": hashlib.sha256("\n".join(f.sexpr() for f in facts).encode()).hexdigest()}
    return facts, result


def decode(env, model, z3):
    database = {}
    for name, table in env.base_databases.items():
        rows = []
        for row in table:
            if z3.is_true(model.eval(env.DELETED_FUNCTION(row.SORT), model_completion=True)):
                raise ValueError("exact-row witness contains deleted base row")
            rows.append([None if z3.is_true(model.eval(attr.NULL(row.SORT), model_completion=True)) else
                         model.eval(attr.VALUE(row.SORT), model_completion=True).as_long() for attr in table.attributes])
        database[name] = rows
    return database


def replay(schema, queries, database):
    def quote(identifier):
        return '"' + identifier.replace('"', '""') + '"'
    with sqlite3.connect(":memory:") as conn:
        for name, fields in schema.items():
            conn.execute('CREATE TABLE ' + quote(name) + ' (' + ','.join(quote(c) + ' INTEGER' for c in fields) + ')')
            conn.executemany('INSERT INTO ' + quote(name) + ' VALUES (' + ','.join('?' for _ in fields) + ')', database[name])
        relations = [conn.execute(sql).fetchall() for sql in queries]
    result = {"relations": relations, "sqlite_version": sqlite3.sqlite_version,
              "scope": "current scalar INT32 diagnostic domain, complete relation and duplicate rows retained"}
    if len(queries) == 2:
        result["unequal_as_bags"] = Counter(relations[0]) != Counter(relations[1])
    return result


def jobs_for(suite, kind):
    if suite.get("schema_version") != 1 or not suite.get("data_role") or not suite.get("cases"):
        raise ValueError("suite registration/schema missing")
    ids = [case["id"] for case in suite["cases"]]
    if len(ids) != len(set(ids)):
        raise ValueError("suite case IDs must be unique")
    jobs = []
    for index, case in enumerate(suite["cases"]):
        if len(case["pair"]) != 2 or set(case["schema"]) != set(case["exact_rows"]):
            raise ValueError("invalid complete input contract")
        if any(type(n) is not int or n < 1 for n in case["exact_rows"].values()):
            raise ValueError("only positive exact-row bounds supported by this adapter")
        if any(str(t).upper() != "INT" for fields in case["schema"].values() for t in fields.values()):
            raise ValueError("registered diagnostic supports INT32 physical columns only")
        if kind == "cost":
            order = case.get("arm_order", list(ARMS))
            if len(order) != len(ARMS) or set(order) != set(ARMS):
                raise ValueError("registered arm_order must contain all six arms once")
            jobs.extend({"case_index": index, "case_id": case["id"], "arm": arm, "kind": kind} for arm in order)
        else:
            jobs.extend({"case_index": index, "case_id": case["id"], "arm": arm, "query_index": q, "kind": kind}
                        for q in (0, 1) for arm in CANDIDATES)
    return jobs


def verifier_semantics(env, lock):
    """Record actual wrapper and dispatch implemented in its locked run method.

    Reading the implementation is not runtime observation of a local callee.
    Report that boundary explicitly; never infer bag mode from scalar equality.
    """
    import ast
    method = env.verifier.run
    module = sys.modules[method.__module__]
    source = Path(module.__file__).resolve()
    if str(source) not in lock["files"] or sha(source) != lock["files"][str(source)]:
        raise ValueError("verifier implementation is not locked")
    tree = ast.parse(source.read_text())
    declaring_class = method.__qualname__.split(".")[0]
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == declaring_class)
    run = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "run")
    targets = sorted({node.func.id for node in ast.walk(run) if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Name)
                      and node.func.id in {"BagSemanticsVerifier", "SetSemanticsVerifier", "ListSemanticsVerifier"}})
    policy = {("SetSemanticsVerifier",): "AUTO_SET",
              ("BagSemanticsVerifier", "ListSemanticsVerifier"): "AUTO_BAG_UNORDERED_LIST_ORDERED"}.get(tuple(targets), "UNCLASSIFIED_DISPATCH")
    return {"requested_semantics": None, "observed_wrapper_class": type(env.verifier).__module__ + "." + type(env.verifier).__name__,
            "actual_run_method": method.__module__ + "." + method.__qualname__,
            "run_source": str(source), "run_source_sha256": sha(source),
            "dispatch_constructors_in_locked_run_ast": targets, "implemented_auto_policy": policy,
            "evidence_kind": "runtime wrapper identity plus static locked dispatch; local dispatch instance is not instrumented",
            "all_null_is_deleted": getattr(env, "all_null_is_deleted", "ATTRIBUTE_NOT_PRESENT"),
            "scalar_boundary": "Set and bag comparison agree for one live scalar output; this does not mean the engine implements bag semantics."}


def canonicalize_conjunctions(ast):
    """Only commute AND operands after pure-fragment admission."""
    if isinstance(ast, dict):
        result = {}
        for key, value in ast.items():
            normalized = canonicalize_conjunctions(value)
            if key == "and":
                if not isinstance(normalized, list):
                    raise ValueError("AND children must be a list")
                normalized = sorted(normalized, key=lambda child: json.dumps(child, sort_keys=True, separators=(",", ":")))
            result[key] = normalized
        return result
    if isinstance(ast, list):
        return [canonicalize_conjunctions(child) for child in ast]
    return ast


def guarded_replay(case, queries, database, env, kernel, plans=None):
    """Common SAT oracle contract; unproved integer domains cannot pass replay."""
    result = {"status": "ATTEMPTED_EFFECT_UNKNOWN", "domain_audits": [],
              "queries": list(queries), "sqlite": {"status": "NOT_RUN"}}
    result["original_ast_contract_validation"] = check_witness_contract(env, database)
    attached = require_contract_bridge(env)
    if attached["schema"] != case["schema"] or attached["record"]["original_ast_sha256"] != json_sha(case["constraint"]):
        raise ContractStop("UNVERIFIED_CONTRACT", "oracle input differs from audited original contract")
    if plans is not None and len(plans) != len(queries):
        raise ValueError("oracle plans/queries count mismatch")
    for index, sql in enumerate(queries):
        try:
            kernel.ensure_raw_identifiers(case["schema"], sql)
            if plans is None:
                parsed = env.parse_sql_query(sql)
                plan = kernel.recognize(parsed, case["schema"], identifier_encoding="verieql_double_underscore", original_sql=sql)
            else:
                plan = plans[index]
            audit = kernel.sqlite_integer_domain_audit(plan, case["schema"], database)
        except kernel.FrontendUnsupported as exc:
            audit = {"status": "FRONTEND_UNSUPPORTED", "reason": str(exc)}
        except kernel.Ineligible as exc:
            audit = {"status": "UNKNOWN_ORACLE_DOMAIN", "reason": "query outside reviewed integer-domain auditor: " + str(exc)}
        except Exception as exc:
            audit = {"status": "ERROR_ORACLE_DOMAIN_AUDIT", "error_type": type(exc).__name__, "reason": str(exc)}
        result["domain_audits"].append(audit)
    statuses = [item["status"] for item in result["domain_audits"]]
    if any(status != "SAFE_FOR_SQLITE_INT64" for status in statuses):
        result["status"] = ("FRONTEND_UNSUPPORTED" if "FRONTEND_UNSUPPORTED" in statuses else
                            "ERROR_ORACLE_DOMAIN_AUDIT" if any(status.startswith("ERROR") for status in statuses) else
                            "UNKNOWN_ORACLE_DOMAIN")
        result["sqlite"]["status"] = "NOT_RUN_ORACLE_DOMAIN_UNPROVED"
        return result
    try:
        result["sqlite"] = replay(case["schema"], queries, database)
    except Exception as exc:
        result.update(status="ERROR_ORACLE_REPLAY", error_type=type(exc).__name__, reason=str(exc))
        result["sqlite"] = {"status": "ERROR_ORACLE_REPLAY"}
        return result
    relations = result["sqlite"]["relations"]
    if any(len(rows) != 1 or len(rows[0]) != 1 for rows in relations):
        result["status"] = "ERROR_ORACLE_SCALAR_SHAPE"
        return result
    if any(value is not None and type(value) is not int for rows in relations for row in rows for value in row):
        result["status"] = "ERROR_ORACLE_NONINTEGER_OUTPUT"
        return result
    expected = [None if audit["mathematical_result_diagnostic_only"] is None else int(audit["mathematical_result_diagnostic_only"])
                for audit in result["domain_audits"]]
    result["sqlite"]["matches_audited_mathematical_values"] = [rows[0][0] == value for rows, value in zip(relations, expected)]
    if not all(result["sqlite"]["matches_audited_mathematical_values"]):
        result["status"] = "ERROR_ORACLE_MATHEMATICAL_VALUE_MISMATCH"
        return result
    result["status"] = "REPLAYED_WITHIN_INT64_DOMAIN"
    result["sqlite"]["status"] = "REPLAYED_WITHIN_INT64_DOMAIN"
    return result
