"""Experimental aggregate encoding over an existing VeriEQL Environment.

Known ingredients: factorized bags and finite-domain multiplication selectors.
This is an unvalidated implementation increment, not a novelty claim. No network,
credentials, schema/gold inference, or imports with model-client side effects.
The official parser, base variables, exact row counts, and all DBMS_facts are
shared with the baseline. Unsupported ASTs must take the original fallback.
"""
from dataclasses import dataclass
from itertools import product
import re


class Ineligible(ValueError):
    pass


@dataclass(frozen=True)
class Column:
    alias: str
    name: str


@dataclass
class Plan:
    tables: dict
    root: str
    leaves: list
    operation: str
    argument: object
    root_predicates: list
    leaf_predicates: dict


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


def recognize(ast, schema):
    """Fail-closed recognizer for official mo-sql-parsing ASTs.

    Initial fragment is deliberately narrower than all linear expressions:
    SUM(column), COUNT(column), COUNT(*); integer comparisons and NULL tests.
    No inferred keys, join truth, defaults or extra constraints are introduced.
    """
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
        argument = column(arg)
        if argument.alias != root:
            raise Ineligible("aggregate_not_root_only")
    root_predicates, by_leaf, equijoin = [], {a: [] for a in leaves}, set()
    for raw in predicates:
        if not isinstance(raw, dict) or len(raw) != 1:
            raise Ineligible("unsupported_predicate")
        operator, args = next(iter(raw.items()))
        if operator in {"missing", "exists"}:
            args = [column(args)]
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
    return Plan(tables, root, leaves, op, argument, root_predicates, by_leaf)


def encode(plan, env, mode, prefix):
    """Return (is_null, value, auxiliary_definitions, encoding_counts).

    `flat` is a local diagnostic emitter, NOT the official strong baseline.
    `product` is known factorization; `selector` eliminates bounded products.
    All table rows/attribute functions and ICs remain from the same Environment.
    """
    # Use the upstream wrappers, including their explicit shared context.
    # Upstream fast bindings require splatted, typed Z3 operands. In particular,
    # IntVal takes a decimal string; Python integer coercion was removed.
    from constants import And, Not, If, Sum, Int, IntVal, Z3_0, Z3_1, Z3_TRUE, Z3_FALSE

    if mode not in {"flat", "product", "selector"}:
        raise ValueError(mode)
    zero, one = Z3_0, Z3_1
    yes, no = Z3_TRUE, Z3_FALSE
    definitions, stats = [], {"match_terms": 0, "flat_rows": 0, "selectors": 0}
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
