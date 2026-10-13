"""Per-query official-output/candidate differential; never a cost arm.

The caller owns source/hash locks, the fresh Environment, full schema/exact row
bounds/IC construction, resource supervision, and SQLite replay of SAT witnesses.
No target import, solver, or native load occurs merely by importing this module.
All target operations are inside compare_query.  Only the admitted SUM/COUNT
integer scalar fragment is compared; unknown shapes fail closed.

This proves bounded agreement relative to the official encoder's full premise.
It is not a proof of official SQL semantics or official auxiliary totality, a
held-out result, or evidence of performance/novelty.  SAT of the joint premise
alone is explicitly not used to prove candidate auxiliary conservativity.
"""

import hashlib
import itertools
import json
import time


_CALL_IDS = itertools.count(1)
_GATES = (
    "full_contract_sat", "exact_rows_no_deletion", "official_premise_sat",
    "official_scalar_shape", "joint_premise_sat", "output_mismatch",
)


class UnsafeComparison(ValueError):
    """The observed representation is outside the reviewed comparison shape."""


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def compare_query(env, sql, schema, mode, z3, constants, kernel, solver_ms,
                  checkpoint, *, record=None, contract_bridge=None):
    """Compare the same SQL through actual Scope and the candidate kernel.

    Pass a mutable ``record`` already attached to the caller's report so its
    one-argument checkpoint(phase) can persist every ATTEMPT/RETURNED state.
    Each gate uses a separate one-thread solver; the caller must bound the whole
    job, not multiply a per-solver timeout into an unbounded experiment.  This
    function does not add a scalar-shape or exact-row assumption to a solver.

    SAT differences include all base tables/columns in schema order, all tuple
    NULL/value/deletion evaluations, and actual official/candidate outputs. The
    worker must run original ``sql`` in SQLite; no result here claims that replay.
    """
    result = {} if record is None else record
    if result:
        raise ValueError("record must be an empty, caller-owned dictionary")
    result.update(
        status="NOT_RUN", sql=sql, mode=mode, correctness_only=True,
        solver_timeout_ms="DYNAMIC_REMAINING_BUDGET" if callable(solver_ms) else solver_ms,
        solver_threads=1,
        gates={name: {"status": "NOT_RUN"} for name in _GATES},
        counts={"planned_solver_checks": len(_GATES), "attempted_solver_checks": 0,
                "completed_solver_checks": 0},
        candidate_auxiliary_extension={"status": "NOT_CHECKED"},
        sqlite_replay={"status": "NOT_RUN_BY_THIS_MODULE", "required_for_sat_witness": True},
        proof_boundary=[
            "Same full DBMS_facts, existing bound_constraints and base mappings; no IC inferred or removed.",
            "Exact row counts mean the caller-created physical slots, independently checked all alive.",
            "Joint SAT demonstrates nonvacuity only; auxiliary totality uses a separate acyclic fresh-definition check.",
            "Official encoding totality/correctness for every base model is not established by this diagnostic.",
            "An UNSAT difference is bounded encoder-relative agreement, not unbounded SQL correctness.",
            "No q1/q2 equivalence result, cost measurement or SQLite oracle is substituted for this single-query comparison.",
        ],
    )
    started = time.monotonic()

    def mark(phase):
        result["phase"] = phase
        result["elapsed_wall_seconds_before_checkpoint"] = time.monotonic() - started
        checkpoint("QUERY_DIFFERENTIAL_" + phase)

    def formula_text(items):
        return [item.sexpr() for item in items]

    def bool_expr(expr):
        if not z3.is_bool(expr):
            raise UnsafeComparison("non-Boolean formula or NULL/deletion flag")
        return expr

    def int_expr(expr):
        if not z3.is_int(expr):
            raise UnsafeComparison("non-integer scalar output or base value")
        return expr

    def bool_value(model, expr):
        val = model.eval(expr, model_completion=True)
        if z3.is_true(val):
            return True
        if z3.is_false(val):
            return False
        raise UnsafeComparison("model did not give a Boolean value")

    def int_value(model, expr):
        val = model.eval(expr, model_completion=True)
        if not z3.is_int_value(val):
            raise UnsafeComparison("model did not give an integer numeral")
        return val.as_long()

    def assert_model(model, formulas):
        if not all(bool_value(model, f) for f in formulas):
            raise UnsafeComparison("SAT model fails a submitted premise/goal")

    def solve(name, premises, goal=None):
        gate = result["gates"][name]
        milliseconds = solver_ms() if callable(solver_ms) else solver_ms
        if type(milliseconds) is not int or not 1 <= milliseconds <= 60000:
            raise ValueError("remaining solver budget must be integer 1..60000 ms")
        expressions = list(premises) + ([] if goal is None else [goal])
        for expression in expressions:
            bool_expr(expression)
        gate.update(status="ATTEMPT", premise_count=len(premises),
                    timeout_ms=milliseconds,
                    goal=None if goal is None else goal.sexpr(),
                    assertions_sha256=_digest(formula_text(expressions)))
        result["counts"]["attempted_solver_checks"] += 1
        mark(name + "_ATTEMPT")
        solver = z3.Solver(ctx=constants.Z3_CONTEXT)
        solver.set(timeout=milliseconds, threads=1)
        solver.add(*expressions)
        tick = time.monotonic()
        answer = str(solver.check())
        gate.update(status=answer, check_wall_seconds=time.monotonic() - tick)
        result["counts"]["completed_solver_checks"] += 1
        if answer == "unknown":
            gate["reason_unknown"] = solver.reason_unknown()
        elif answer == "sat":
            assert_model(solver.model(), expressions)
            gate["model_satisfies_all_submitted_formulas"] = True
        elif answer != "unsat":
            raise UnsafeComparison("unrecognized solver result: " + answer)
        mark(name + "_RETURNED")
        return solver, answer

    def finish(status, reason=None):
        result["status"] = status
        if reason is not None:
            result["reason"] = reason
        result["counts"]["not_run_solver_checks"] = sum(
            gate["status"] == "NOT_RUN" for gate in result["gates"].values())
        mark("FINISHED")
        return result

    def declarations(expressions):
        """Uninterpreted decl IDs of a quantifier-free expression DAG."""
        found, seen, stack = set(), set(), list(expressions)
        while stack:
            node = stack.pop()
            if not z3.is_app(node):
                raise UnsafeComparison("non-application/quantified expression in extension audit")
            identity = node.get_id()
            if identity in seen:
                continue
            seen.add(identity)
            if len(seen) % 512 == 0:
                mark("EXPRESSION_DAG_AUDIT")
            declaration = node.decl()
            if declaration.kind() == z3.Z3_OP_UNINTERPRETED:
                found.add(declaration.get_id())
            stack.extend(node.children())
        return found

    try:
        from common import require_contract_bridge
        if contract_bridge is None:
            raise UnsafeComparison("explicit verified same-Environment original-AST contract bridge required")
        require_contract_bridge(env, contract_bridge)
        result["source_ast_bridge"] = {key: contract_bridge[key] for key in
            ("status", "original_ast_sha256", "normalized_ast_sha256", "complete_facts_sha256")}
        kernel.ensure_raw_identifiers(schema, sql)
        result["raw_frontend_guard"] = "ADMITTED"
        if not callable(solver_ms) and (type(solver_ms) is not int or not 1 <= solver_ms <= 60000):
            raise ValueError("solver_ms must be 1..60000 or callable remaining-budget provider")
        if mode not in {"flat", "product", "selector"}:
            raise ValueError("unsupported candidate mode")
        if env._script_writer is not None:
            raise UnsafeComparison("requires generate_code=False")
        if not schema or set(schema) != set(env.base_databases):
            raise UnsafeComparison("schema must cover every actual base database exactly")
        if not set(schema) <= set(env.checkpoints["databases"]):
            raise UnsafeComparison("caller must save base checkpoints before Scope cleanup")
        # Uses the caller's already locked official package.  No independent
        # reimplementation of projection or aggregation is imported here.
        from scope import Scope
        from visitors.dump_tuple import DumpTuple
        from formulas.columns.attribute import FAttribute

        facts = list(env.DBMS_facts)
        bounds = sorted(env.bound_constraints, key=lambda expression: expression.sexpr())
        facts_before, bounds_before = formula_text(facts), formula_text(bounds)
        base_mapping, base_terms, deleted_terms = {}, [], []
        for name, table in env.base_databases.items():
            if not len(table):
                raise UnsafeComparison("zero physical base slots outside admitted kernel shape")
            attrs = list(table.attributes)
            names = [attr.name.upper() for attr in attrs]
            if names != list(schema[name]) or len(set(names)) != len(names):
                raise UnsafeComparison("base attribute order/names differ from full schema: " + name)
            if any(str(kind).upper() not in {"INT", "INTEGER", "BIGINT"} for kind in schema[name].values()):
                raise UnsafeComparison("only complete integer base schemas can be decoded")
            rows = []
            for row in table:
                deleted = bool_expr(env.DELETED_FUNCTION(row.SORT))
                deleted_terms.append(deleted)
                base_terms.extend([row.SORT, deleted])
                cells = []
                for attr in attrs:
                    null, value = bool_expr(attr.NULL(row.SORT)), int_expr(attr.VALUE(row.SORT))
                    base_terms.extend([null, value])
                    cells.append([attr.name, null.sexpr(), value.sexpr()])
                rows.append([row.SORT.sexpr(), cells])
            base_mapping[name] = rows
        mapping_before = _digest(base_mapping)
        result["contract"] = {
            "dbms_fact_count": len(facts), "bound_constraint_count": len(bounds),
            "facts_sha256": _digest(facts_before), "bounds_sha256": _digest(bounds_before),
            "base_mapping_sha256": mapping_before,
            "exact_rows": {name: len(table) for name, table in env.base_databases.items()},
            "column_order": {name: list(fields) for name, fields in schema.items()},
        }
        contract = facts + bounds

        def decode(model):
            database, rows_audit, alive_counts = {}, {}, {}
            for name, table in env.base_databases.items():
                values, audit = [], []
                for row in table:
                    deleted = bool_value(model, env.DELETED_FUNCTION(row.SORT))
                    cells, cells_audit = [], []
                    for attr in table.attributes:
                        null = bool_value(model, attr.NULL(row.SORT))
                        raw = int_value(model, attr.VALUE(row.SORT))
                        cells.append(None if null else raw)
                        cells_audit.append({"column": attr.name.upper(), "is_null": null,
                                            "integer_payload": raw})
                    audit.append({"tuple": row.SORT.sexpr(), "deleted": deleted, "cells": cells_audit})
                    if not deleted:
                        values.append(cells)
                database[name], rows_audit[name], alive_counts[name] = values, audit, len(values)
            return {"database": database, "base_rows": rows_audit,
                    "column_order": result["contract"]["column_order"], "alive_counts": alive_counts,
                    "exact_rows_match": alive_counts == result["contract"]["exact_rows"],
                    "sql": sql, "sqlite_replay_status": "REQUIRED_NOT_RUN"}

        _, answer = solve("full_contract_sat", contract)
        if answer != "sat":
            return finish("CONTRACT_NOT_ESTABLISHED", "complete contract SAT gate: " + answer)
        solver, answer = solve("exact_rows_no_deletion", contract, constants.Or(*deleted_terms))
        if answer != "unsat":
            if answer == "sat":
                result["gates"]["exact_rows_no_deletion"]["witness"] = decode(solver.model())
            return finish("EXACT_ROWS_NOT_ESTABLISHED", answer)
        mark("OFFICIAL_PARSE_ATTEMPT")
        parsed = env.parse_sql_query(sql)
        # Keep the unmodified actual parser AST before Scope/recognizer use it.
        result["parsed_ast"] = json.loads(json.dumps(parsed))
        plan = kernel.recognize(parsed, schema, identifier_encoding="verieql_double_underscore", original_sql=sql)
        mark("OFFICIAL_SCOPE_ATTEMPT")
        with Scope(env, "QUERY_DIFFERENTIAL") as scope:
            context = scope.analyze(parsed)
            table, snippets = scope.visit(context)
            if scope.orderby_constraints is not None:
                raise UnsafeComparison("ordered output outside admitted scalar fragment")
            if not isinstance(table, dict) or not table:
                raise UnsafeComparison("official output is not a nonempty DumpTuple mapping")
            formulas = [bool_expr(snippet.code) for snippet in snippets]
            slots = []
            for key, row in table.items():
                if not isinstance(row, DumpTuple) or row.name == "DELETED_TUPLE":
                    raise UnsafeComparison("official sentinel or unknown tuple representation")
                attrs = list(row.attributes)
                if len(attrs) != 1 or not isinstance(attrs[0], FAttribute):
                    raise UnsafeComparison("official output is not one FAttribute column per slot")
                attr = attrs[0]
                if getattr(attr, "is_uninterpreted_func", False):
                    raise UnsafeComparison("uninterpreted output attribute outside fragment")
                deleted = bool_expr(env.DELETED_FUNCTION(row.SORT))
                null, value = bool_expr(attr.NULL(row.SORT)), int_expr(attr.VALUE(row.SORT))
                slots.append((str(key), row.SORT, deleted, null, value))
            if formula_text(env.DBMS_facts) != facts_before or sorted(
                    formula_text(env.bound_constraints)) != sorted(bounds_before):
                raise UnsafeComparison("official Scope changed the shared DBMS/bound contract")
        result["official"] = {
            "physical_output_slots": len(slots), "column_count_per_slot": 1,
            "result_formula_count": len(formulas), "result_formulas": formula_text(formulas),
            "result_formulas_sha256": _digest(formula_text(formulas)),
            "slots": [{"key": key, "tuple": sort.sexpr(), "deleted": deleted.sexpr(),
                       "is_null": null.sexpr(), "value": value.sexpr()}
                      for key, sort, deleted, null, value in slots],
        }
        official_premise = contract + formulas
        _, answer = solve("official_premise_sat", official_premise)
        if answer != "sat":
            return finish("OFFICIAL_PREMISE_NOT_ESTABLISHED", answer)
        alive = [constants.Not(slot[2]) for slot in slots]
        alive_count = constants.Sum(*[constants.If(flag, constants.Z3_1, constants.Z3_0) for flag in alive])
        solver, answer = solve("official_scalar_shape", official_premise, alive_count != constants.Z3_1)
        if answer != "unsat":
            if answer == "sat":
                result["gates"]["official_scalar_shape"]["witness"] = decode(solver.model())
            return finish("OFFICIAL_SCALAR_SHAPE_NOT_ESTABLISHED", answer)
        # Valid only after proving exactly one alive slot, without adding that
        # fact as an assumption.  Null payloads and deleted payloads are ignored.
        official_null = constants.Or(*[constants.And(flag, slot[3]) for flag, slot in zip(alive, slots)])
        official_value = constants.Sum(*[
            constants.If(constants.And(flag, constants.Not(slot[3])), slot[4], constants.Z3_0)
            for flag, slot in zip(alive, slots)])
        prefix = "CALIBER_QUERY_DIFF_" + hashlib.sha256(sql.encode()).hexdigest()[:16] + "_" + mode + "_" + str(next(_CALL_IDS))
        mark("CANDIDATE_ENCODING_ATTEMPT")
        candidate_null, candidate_value, definitions, counts = kernel.encode(plan, env, mode, prefix)
        bool_expr(candidate_null)
        int_expr(candidate_value)
        definitions = list(definitions)
        result["candidate"] = {"prefix": prefix, "encoding_counts": counts,
                               "is_null": candidate_null.sexpr(), "value": candidate_value.sexpr(),
                               "definition_count": len(definitions), "definitions": formula_text(definitions)}
        if formula_text(env.DBMS_facts) != facts_before or sorted(
                formula_text(env.bound_constraints)) != sorted(bounds_before):
            raise UnsafeComparison("candidate changed the shared DBMS/bound contract")
        current_mapping = {
            name: [[row.SORT.sexpr(), [[attr.name, attr.NULL(row.SORT).sexpr(), attr.VALUE(row.SORT).sexpr()]
                                      for attr in table.attributes]] for row in table]
            for name, table in env.base_databases.items()}
        if _digest(current_mapping) != mapping_before:
            raise UnsafeComparison("official/candidate changed shared base mapping")
        result["contract"]["unchanged_after_both_encoders"] = True

        # A finite ordered system fresh_int_i = total_term(base, earlier_ints)
        # has exactly one extension for each base interpretation.  Check each
        # emitted equation, never infer this obligation from a single SAT model.
        base_decls = declarations(contract + base_terms)
        original_decls = declarations(official_premise + base_terms + [part for slot in slots for part in slot[1:]])
        allowed, new_decls, audited = set(base_decls), set(), []
        for index, definition in enumerate(definitions):
            bool_expr(definition)
            if not z3.is_eq(definition) or definition.num_args() != 2:
                raise UnsafeComparison("auxiliary constraint is not a binary equality")
            lhs, rhs = definition.children()
            if not z3.is_const(lhs) or not z3.is_int(lhs) or lhs.decl().kind() != z3.Z3_OP_UNINTERPRETED:
                raise UnsafeComparison("auxiliary lhs is not a fresh integer constant")
            identity = lhs.decl().get_id()
            if identity in original_decls or identity in new_decls:
                raise UnsafeComparison("auxiliary lhs collides with original/repeated declaration")
            used = declarations([rhs])
            if not used <= allowed:
                raise UnsafeComparison("auxiliary rhs has forward/self/non-base dependency")
            int_expr(rhs)
            allowed.add(identity)
            new_decls.add(identity)
            audited.append({"index": index, "lhs": lhs.sexpr(), "rhs_sha256": _digest(rhs.sexpr())})
        if not declarations([candidate_null, candidate_value]) <= allowed:
            raise UnsafeComparison("candidate output contains unaccounted declarations")
        result["candidate_auxiliary_extension"] = {
            "status": "CHECKED_ACYCLIC_FRESH_TOTAL_INT_DEFINITIONS",
            "method": "Quantifier-free AST audit, not a quantified SMT proof or SAT-only inference.",
            "definition_count": len(definitions), "ordered_definitions": audited,
            "obligation": "Every interpretation of the original base symbols uniquely extends to these auxiliary constants.",
            "scope": "Emitted definitions only; does not establish aggregate expression semantics.",
        }
        joint = official_premise + definitions
        _, answer = solve("joint_premise_sat", joint)
        if answer != "sat":
            return finish("JOINT_PREMISE_NOT_ESTABLISHED", answer)
        difference = constants.Or(
            official_null != candidate_null,
            constants.And(constants.Not(official_null), constants.Not(candidate_null),
                          official_value != candidate_value))
        solver, answer = solve("output_mismatch", joint, difference)
        if answer == "sat":
            model = solver.model()
            witness = decode(model)
            if not witness["exact_rows_match"]:
                raise UnsafeComparison("difference witness violated established exact-row contract")
            official_rows = []
            official_slot_audit = []
            for key, sort, deleted, null, value in slots:
                is_deleted, is_null = bool_value(model, deleted), bool_value(model, null)
                payload = int_value(model, value)
                official_slot_audit.append({"key": key, "tuple": sort.sexpr(), "deleted": is_deleted,
                                            "is_null": is_null, "integer_payload": payload})
                if not is_deleted:
                    official_rows.append([None if is_null else payload])
            candidate_rows = [[None if bool_value(model, candidate_null) else int_value(model, candidate_value)]]
            witness.update(official_rows=official_rows, candidate_rows=candidate_rows,
                           official_slots=official_slot_audit,
                           observed_output_difference=official_rows != candidate_rows)
            if len(official_rows) != 1 or not witness["observed_output_difference"]:
                raise UnsafeComparison("SAT output model does not decode to a scalar difference")
            result["witness"] = witness.pop("database")
            result["witness_metadata"] = witness
            return finish("SAT_OUTPUT_DIFFERENCE_REQUIRES_SQLITE_REPLAY")
        if answer == "unknown":
            return finish("UNKNOWN_OUTPUT_DIFFERENCE")
        result["agreement_scope"] = "BOUNDED_ENCODER_RELATIVE_NULL_AND_NON_NULL_INTEGER_VALUE"
        return finish("UNSAT_DIFFERENTIAL")
    except kernel.FrontendUnsupported as exc:
        result["raw_frontend_guard"] = "FRONTEND_UNSUPPORTED"
        return finish("FRONTEND_UNSUPPORTED", str(exc))
    except kernel.Ineligible as exc:
        return finish("INELIGIBLE", str(exc))
    except Exception as exc:
        result["exception_type"] = type(exc).__name__
        return finish("ERROR", str(exc))
