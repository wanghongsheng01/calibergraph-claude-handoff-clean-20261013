"""Experimental aggregate encoding over an existing VeriEQL Environment.

Known ingredients: factorized bags and finite-domain multiplication selectors.
This is an unvalidated implementation increment, not a novelty claim. No network,
credentials, schema/gold inference, or imports with model-client side effects.
The official parser, base variables, exact row counts, and all DBMS_facts are
shared with the baseline. Algorithmically unsupported ASTs may take the original
fallback only after the raw frontend contract passes. Irreversible raw-name
transformations are FRONTEND_UNSUPPORTED for every arm, without fallback.
"""
from dataclasses import dataclass
from itertools import product
import re


class Ineligible(ValueError):
    pass


class FrontendUnsupported(Ineligible):
    """Raw identifiers cannot safely pass through the shared upstream parser."""


def ensure_raw_identifiers(schema, original_sql):
    """Conservative raw-name contract before ANY official parse or fallback.

    Upstream rewrites dollars and dots inside quoted names irreversibly. The
    recognized AST alone cannot detect their collisions. This gate is common to
    official and candidate arms; rejection is not an equivalence decision.
    """
    if not isinstance(original_sql, str):
        raise FrontendUnsupported("original_sql_required")
    if not isinstance(schema, dict) or not schema:
        raise FrontendUnsupported("raw_schema_required")
    groups = [list(schema)]
    for fields in schema.values():
        if not isinstance(fields, dict) or not fields:
            raise FrontendUnsupported("raw_schema_columns_required")
        groups.append(list(fields))
    for names in groups:
        for name in names:
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                raise FrontendUnsupported("schema_identifier_not_ascii_simple")
            if "__" in name:
                raise FrontendUnsupported("schema_identifier_contains_encoding_separator")
        if len({name.upper() for name in names}) != len(names):
            raise FrontendUnsupported("schema_identifiers_collide_after_case_fold")
    if "`" in original_sql or '"' in original_sql:
        raise FrontendUnsupported("quoted_identifier_not_in_fragment")
    if "$" in original_sql:
        raise FrontendUnsupported("dollar_rewrite_not_in_fragment")


@dataclass(frozen=True)
class Column:
    alias: str
    name: str


@dataclass(frozen=True)
class IntegerExpression:
    operator: str
    arguments: tuple


def expression_aliases(expression):
    if isinstance(expression, Column):
        return {expression.alias}
    if isinstance(expression, IntegerExpression):
        return set().union(*(expression_aliases(child) for child in expression.arguments))
    if expression is None or type(expression) is int:
        return set()
    raise Ineligible("unknown_integer_expression_node")


def expression_contains_variable_product(expression):
    """Conservative syntactic flag, without algebraic cancellation guesses."""
    if not isinstance(expression, IntegerExpression):
        return False
    if expression.operator == "mul" and sum(bool(expression_aliases(child)) for child in expression.arguments) >= 2:
        return True
    return any(expression_contains_variable_product(child) for child in expression.arguments)


@dataclass
class Plan:
    tables: dict
    root: str
    leaves: list
    operation: str
    argument: object
    root_predicates: list
    leaf_predicates: dict
    expression_contains_variable_product: bool = False


def identifier(x):
    if not isinstance(x, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", x):
        raise Ineligible("unsupported_identifier")
    return x.upper()


def conjunction(x):
    if x is None:
        return []
    if isinstance(x, dict) and set(x) == {"and"}:
        if not isinstance(x["and"], list):
            raise Ineligible("malformed_conjunction")
        return [p for child in x["and"] for p in conjunction(child)]
    return [x]


def recognize(ast, schema, *, identifier_encoding="dot", original_sql=None):
    """Fail-closed recognizer for official mo-sql-parsing ASTs.

    Scalar SUM/COUNT over root-only integer +, -, * expressions, COUNT(*),
    integer comparisons, BETWEEN and NULL tests. Arithmetic is strict in NULL.
    Variable products remain nonlinear even when multiplicities use selectors.
    No inferred keys, join truth, defaults or extra constraints are introduced.
    """
    if identifier_encoding not in {"dot", "verieql_double_underscore"}:
        raise Ineligible("unknown_identifier_encoding")
    if identifier_encoding == "verieql_double_underscore":
        ensure_raw_identifiers(schema, original_sql)
    if not isinstance(ast, dict) or not {"select", "from"} <= set(ast):
        raise Ineligible("not_simple_select")
    if set(ast) - {"select", "from", "where"}:
        raise Ineligible("extra_select_clause")
    tables, predicates = {}, conjunction(ast.get("where"))
    items = ast["from"] if isinstance(ast["from"], list) else [ast["from"]]
    for item in items:
        if isinstance(item, dict) and ("join" in item or "inner join" in item):
            kind = "join" if "join" in item else "inner join"
            if set(item) - {kind, "on"} or "on" not in item:
                raise Ineligible("unsupported_join")
            predicates += conjunction(item["on"])
            item = item[kind]
        if isinstance(item, str):
            table = alias = identifier(item)
        elif isinstance(item, dict) and "value" in item and not set(item) - {"value", "name"}:
            table = identifier(item["value"])
            alias = identifier(item.get("name", item["value"]))
        else:
            raise Ineligible("subquery_or_non_inner_join")
        if table not in schema or alias in tables or table in tables.values():
            raise Ineligible("unknown_table_or_repeated_relation")
        tables[alias] = table
    if not tables:
        raise Ineligible("empty_from")
    root, *leaves = tables

    def column(x):
        if not isinstance(x, str):
            raise Ineligible("non_column_expression")
        if identifier_encoding == "verieql_double_underscore":
            # VeriEQL SQLParser._remove_dots maps every qualified identifier
            # A.C to A__C. Do not blindly split/replace '__': it can also occur
            # in a legal alias or physical column. Enumerate schema-backed
            # qualified AND unqualified interpretations and require uniqueness.
            encoded = identifier(x)
            matches = {(a, c) for a, t in tables.items() for c in schema[t]
                       if encoded in {a + "__" + c, c}}
            if not matches:
                raise Ineligible("unknown_column")
            if len(matches) != 1:
                raise Ineligible("ambiguous_column_after_upstream_encoding")
            alias, name = next(iter(matches))
            if str(schema[tables[alias]][name]).upper() not in {"INT", "INTEGER", "BIGINT"}:
                raise Ineligible("non_integer_column")
            return Column(alias, name)
        parts = x.split(".")
        if len(parts) == 2:
            alias, name = map(identifier, parts)
            if alias not in tables or name not in schema[tables[alias]]:
                raise Ineligible("unknown_column")
        elif len(parts) == 1:
            name = identifier(parts[0])
            matches = [a for a, t in tables.items() if name in schema[t]]
            if len(matches) != 1:
                raise Ineligible("ambiguous_or_unknown_column")
            alias = matches[0]
        else:
            raise Ineligible("unsupported_qualified_name")
        # Environment supplies the exact type constraints. Do not broaden types.
        if str(schema[tables[alias]][name]).upper() not in {"INT", "INTEGER", "BIGINT"}:
            raise Ineligible("non_integer_column")
        return Column(alias, name)

    def operand(x):
        return x if type(x) is int else column(x)

    def expression(x):
        if type(x) is int:
            return x
        if isinstance(x, str):
            return column(x)
        if not isinstance(x, dict) or len(x) != 1:
            raise Ineligible("unsupported_integer_expression")
        operator, children = next(iter(x.items()))
        if operator in {"neg", "pos"}:
            # The pinned parser scrubs a unary argument list to its one value.
            children = children if isinstance(children, list) else [children]
            if len(children) != 1:
                raise Ineligible("malformed_unary_integer_expression")
        elif operator in {"add", "mul"}:
            # The pinned parser flattens associative operators into n-ary lists.
            if not isinstance(children, list) or len(children) < 2:
                raise Ineligible("malformed_associative_integer_expression")
        elif operator == "sub":
            if not isinstance(children, list) or len(children) != 2:
                raise Ineligible("malformed_subtraction")
        else:
            raise Ineligible("unsupported_integer_expression_operator")
        return IntegerExpression(operator, tuple(expression(child) for child in children))

    select = ast["select"]
    if isinstance(select, list):
        if len(select) != 1:
            raise Ineligible("multiple_output_columns")
        select = select[0]
    if not isinstance(select, dict) or "value" not in select or set(select) - {"value", "name"}:
        raise Ineligible("not_single_aggregate")
    agg = select["value"]
    if not isinstance(agg, dict) or len(agg) != 1:
        raise Ineligible("not_single_aggregate")
    op, arg = next(iter(agg.items()))
    if op not in {"sum", "count"}:
        raise Ineligible("unsupported_aggregate")
    if op == "count" and (arg == "*" or type(arg) is int):
        argument = None  # COUNT(non-null integer literal) is COUNT(*)
    else:
        argument = expression(arg)
        if expression_aliases(argument) - {root}:
            raise Ineligible("aggregate_not_root_only")
    root_predicates, by_leaf, equijoin = [], {a: [] for a in leaves}, set()
    for raw in predicates:
        if not isinstance(raw, dict) or len(raw) != 1:
            raise Ineligible("unsupported_predicate")
        operator, args = next(iter(raw.items()))
        if operator in {"missing", "exists"}:
            args = [column(args)]
        elif operator == "between":
            if not isinstance(args, list) or len(args) != 3:
                raise Ineligible("malformed_between")
            # No arithmetic/date/string/NULL-literal predicate operands inferred.
            args = [operand(x) for x in args]
        elif operator in {"eq", "neq", "gt", "gte", "lt", "lte"}:
            if not isinstance(args, list) or len(args) != 2:
                raise Ineligible("malformed_comparison")
            args = [operand(x) for x in args]
        else:
            raise Ineligible("unsupported_predicate_operator")
        aliases = {x.alias for x in args if isinstance(x, Column)}
        nonroot = aliases - {root}
        if len(nonroot) > 1:
            raise Ineligible("cross_leaf_predicate")
        pred = (operator, args)
        if nonroot:
            leaf = next(iter(nonroot))
            by_leaf[leaf].append(pred)
            if operator == "eq" and len(aliases) == 2 and all(isinstance(x, Column) for x in args):
                equijoin.add(leaf)
        else:
            root_predicates.append(pred)
    if equijoin != set(leaves):
        raise Ineligible("not_fact_rooted_equijoin")
    return Plan(tables, root, leaves, op, argument, root_predicates, by_leaf,
                expression_contains_variable_product(argument))


def encode(plan, env, mode, prefix):
    """Return (is_null, value, auxiliary_definitions, encoding_counts).

    `flat` is a local diagnostic emitter, NOT the official strong baseline.
    `product` is the known classic multiplicity-product factorization control.
    `selector` replaces multiplicity products with constant-coefficient terms;
    it does not remove variable products inside the root measure or other ICs.
    All table rows/attribute functions and ICs remain from the same Environment.
    """
    # Use the upstream wrappers, including their explicit shared context.
    # Upstream fast bindings require splatted, typed Z3 operands. In particular,
    # IntVal takes a decimal string; Python integer coercion was removed.
    from constants import And, Or, Not, If, Sum, Int, IntVal, Z3_0, Z3_1, Z3_TRUE, Z3_FALSE

    if mode not in {"flat", "product", "selector"}:
        raise ValueError(mode)
    zero, one = Z3_0, Z3_1
    yes, no = Z3_TRUE, Z3_FALSE
    definitions, stats = [], {"match_terms": 0, "flat_rows": 0, "selectors": 0,
                              "expression_contains_variable_product": plan.expression_contains_variable_product,
                              "arithmetic_semantics": "MATHEMATICAL_INTEGERS_STRICT_NULL",
                              "multiplicity_encoding": mode,
                              "full_formula_logic": "NOT_CLASSIFIED_IC_AND_ROOT_MEASURE_PRESERVED"}
    rows = {a: list(env.base_databases[t]) for a, t in plan.tables.items()}
    if any(not rs for rs in rows.values()):
        raise Ineligible("zero_base_rows_not_supported_by_upstream_attribute_accessor")
    attributes = {}
    for alias, table in plan.tables.items():
        for name in env.base_databases[table].attributes:
            attributes[(alias, name.name.upper())] = name

    def land(xs):
        return And(*xs) if xs else yes

    def total(xs):
        return Sum(*xs) if xs else zero

    def value(x, binding):
        if type(x) is int:
            return no, IntVal(str(x))
        if isinstance(x, IntegerExpression):
            children = [value(child, binding) for child in x.arguments]
            null = Or(*(child[0] for child in children))
            values = [child[1] for child in children]
            if x.operator == "neg":
                result = zero - values[0]
            elif x.operator == "pos":
                result = values[0]
            elif x.operator == "sub":
                result = values[0] - values[1]
            else:
                result = values[0]
                for term in values[1:]:
                    result = result + term if x.operator == "add" else result * term
            return null, result
        attr = attributes[(x.alias, x.name)]
        return attr.NULL(binding[x.alias].SORT), attr.VALUE(binding[x.alias].SORT)

    def true_predicate(pred, binding):
        op, args = pred
        a_null, a_val = value(args[0], binding)
        if op == "missing":
            return a_null
        if op == "exists":
            return Not(a_null)
        b_null, b_val = value(args[1], binding)
        if op == "between":
            c_null, c_val = value(args[2], binding)
            return And(Not(a_null), Not(b_null), Not(c_null), a_val >= b_val, a_val <= c_val)
        compare = {"eq": lambda: a_val == b_val, "neq": lambda: a_val != b_val,
                   "gt": lambda: a_val > b_val, "gte": lambda: a_val >= b_val,
                   "lt": lambda: a_val < b_val, "lte": lambda: a_val <= b_val}[op]()
        return And(Not(a_null), Not(b_null), compare)

    def alive(row):
        return Not(env.DELETED_FUNCTION(row.SORT))

    def bind(name, expr):
        variable = Int(f"{prefix}_{name}")
        definitions.append(variable == expr)
        return variable

    def multiply(acc, count, bound, name):
        if mode == "product":
            return bind(name, acc * count)
        stats["selectors"] += bound + 1
        constants = [IntVal(str(c)) for c in range(bound + 1)]
        return bind(name, total([If(count == c, c * acc, zero) for c in constants]))

    sums, counts = [], []
    for i, fact in enumerate(rows[plan.root]):
        binding = {plan.root: fact}
        root_ok = land([alive(fact)] + [true_predicate(p, binding) for p in plan.root_predicates])
        arg_null, arg_val = (no, one) if plan.argument is None else value(plan.argument, binding)
        contributes = And(root_ok, Not(arg_null))
        if mode == "flat":
            for combination in product(*(rows[a] for a in plan.leaves)):
                binding.update(zip(plan.leaves, combination))
                active = land([contributes] + [alive(row) for row in combination] + [
                    true_predicate(p, binding) for a in plan.leaves for p in plan.leaf_predicates[a]])
                counts.append(If(active, one, zero))
                sums.append(If(active, arg_val, zero))
                stats["flat_rows"] += 1
        else:
            count_acc, sum_acc = If(contributes, one, zero), If(contributes, arg_val, zero)
            for j, leaf in enumerate(plan.leaves):
                matches = []
                for row in rows[leaf]:
                    binding[leaf] = row
                    active = land([alive(row)] + [true_predicate(p, binding) for p in plan.leaf_predicates[leaf]])
                    matches.append(If(active, one, zero))
                stats["match_terms"] += len(matches)
                count = bind(f"c_{i}_{j}", total(matches))
                # Exact count definition supplies its 0..N_j range; it is not free.
                count_acc = multiply(count_acc, count, len(matches), f"n_{i}_{j}")
                if plan.operation == "sum":
                    sum_acc = multiply(sum_acc, count, len(matches), f"v_{i}_{j}")
            counts.append(count_acc)
            sums.append(sum_acc)
    count = total(counts)
    if plan.operation == "count":
        return no, count, definitions, stats
    return count == zero, total(sums), definitions, stats


def unequal(lhs, rhs):
    from constants import Or, And, Not
    ln, lv = lhs[:2]
    rn, rv = rhs[:2]
    return Or(ln != rn, And(Not(ln), Not(rn), lv != rv))


def sqlite_integer_domain_audit(plan, schema, database):
    """Conservative precondition for using SQLite as an integer witness oracle.

    This does NOT validate SQL/encoding correctness. It checks a concrete whole
    database using mathematical Python integers, before a separate raw-SQL replay.
    UNKNOWN retains the witness and denominator; it is neither a counterexample
    nor a successful replay. Associative AST flattening may have lost original
    parentheses, so all-subset bounds conservatively cover any evaluation order.
    """
    low, high = -(2 ** 63), 2 ** 63 - 1
    issues, issue_count = [], 0

    def issue(reason, location, value=None):
        nonlocal issue_count
        issue_count += 1
        if len(issues) < 40:
            item = {"reason": reason, "location": location}
            if value is not None:
                item["mathematical_integer"] = str(value)
            issues.append(item)

    def checked(value, location):
        if type(value) is not int:
            raise ValueError("non-integer non-NULL concrete cell/expression")
        if not low <= value <= high:
            issue("outside_sqlite_signed_int64", location, value)
        return value

    def atom(value, binding, location):
        if type(value) is int:
            return checked(value, location)
        if isinstance(value, Column):
            result = binding[value.alias][value.name]
            return None if result is None else checked(result, location)
        if not isinstance(value, IntegerExpression):
            raise ValueError("unknown expression node")
        children = [atom(child, binding, location + "/" + str(i))
                    for i, child in enumerate(value.arguments)]
        present = [child for child in children if child is not None]
        # These bounds deliberately ignore zero/NULL short-circuit opportunities:
        # the original SQL may have evaluated a risky parenthesized subtree first.
        if value.operator == "add":
            positive = sum(v for v in present if v > 0)
            negative = sum(v for v in present if v < 0)
            if positive > high or negative < low:
                issue("possible_associative_add_intermediate_overflow", location)
        elif value.operator == "mul":
            magnitude = 1
            for child in present:
                if child:
                    magnitude *= abs(child)
            if magnitude > high:
                issue("possible_associative_multiply_intermediate_overflow", location, magnitude)
        if any(child is None for child in children):
            return None
        if value.operator == "neg":
            result = -children[0]
        elif value.operator == "pos":
            result = children[0]
        elif value.operator == "sub":
            result = children[0] - children[1]
        else:
            result = children[0]
            for child in children[1:]:
                result = result + child if value.operator == "add" else result * child
                checked(result, location + "/left_fold_intermediate")
        return checked(result, location)

    def predicate(pred, binding, location):
        operator, arguments = pred
        values = [atom(value, binding, location + "/" + str(i))
                  for i, value in enumerate(arguments)]
        if operator == "missing":
            return values[0] is None
        if operator == "exists":
            return values[0] is not None
        if any(value is None for value in values):
            return False  # Only SQL TRUE selects a row; UNKNOWN is not TRUE.
        if operator == "between":
            return values[1] <= values[0] <= values[2]
        left, right = values
        return {"eq": lambda: left == right, "neq": lambda: left != right,
                "gt": lambda: left > right, "gte": lambda: left >= right,
                "lt": lambda: left < right, "lte": lambda: left <= right}[operator]()

    result = {"status": "NOT_CHECKED", "issues": issues, "oracle": "SQLite signed int64",
              "expression_contains_variable_product": plan.expression_contains_variable_product,
              "purpose": "domain guard only; not an independent SQL correctness oracle",
              "conservative_order_policy": "every associative root subexpression and every SUM row order must be safe",
              "arithmetic_semantics": "mathematical integers; no wrap, rounding, truncation or float tolerance"}
    try:
        if set(schema) != set(database):
            raise ValueError("concrete database must retain every schema table")
        rows = {}
        for table, fields in schema.items():
            names = list(fields)
            rows[table] = []
            for index, row in enumerate(database[table]):
                if len(row) != len(names):
                    raise ValueError("concrete row/schema width mismatch")
                for name, cell in zip(names, row):
                    if cell is not None:
                        checked(cell, f"base/{table}/{index}/{name}")
                rows[table].append(dict(zip(names, row)))
        positive_sum, negative_sum, nonnull_count = 0, 0, 0
        for index, root_row in enumerate(rows[plan.tables[plan.root]]):
            binding = {plan.root: root_row}
            location = f"root/{index}"
            value = 1 if plan.argument is None else atom(plan.argument, binding, location + "/measure")
            # Evaluate all predicates for domain checks, not short-circuiting them.
            root_results = [predicate(pred, binding, location + "/root_pred/" + str(i))
                            for i, pred in enumerate(plan.root_predicates)]
            multiplicity = 1
            for leaf in plan.leaves:
                matches = 0
                for row_index, leaf_row in enumerate(rows[plan.tables[leaf]]):
                    binding[leaf] = leaf_row
                    truth = [predicate(pred, binding, location + f"/leaf/{leaf}/{row_index}/{i}")
                             for i, pred in enumerate(plan.leaf_predicates[leaf])]
                    matches += int(all(truth))
                multiplicity *= matches
            if not all(root_results) or value is None:
                continue
            nonnull_count += multiplicity
            if plan.operation == "sum":
                weighted = value * multiplicity
                if weighted >= 0:
                    positive_sum += weighted
                else:
                    negative_sum += weighted
        checked(nonnull_count, "aggregate/count_nonnull")
        if plan.operation == "sum":
            if positive_sum > high or negative_sum < low:
                issue("possible_sum_accumulator_overflow_for_some_row_order", "aggregate/sum")
            mathematical = None if nonnull_count == 0 else positive_sum + negative_sum
        else:
            mathematical = nonnull_count
        result.update(status="SAFE_FOR_SQLITE_INT64" if not issue_count else "UNKNOWN_ORACLE_DOMAIN",
                      issue_count=issue_count, positive_sum=str(positive_sum), negative_sum=str(negative_sum),
                      nonnull_joined_row_count=str(nonnull_count),
                      mathematical_result_diagnostic_only=None if mathematical is None else str(mathematical))
        return result
    except Exception as exc:
        result.update(status="ERROR_ORACLE_INPUT", issue_count=issue_count,
                      error_type=type(exc).__name__, reason=str(exc))
        return result
