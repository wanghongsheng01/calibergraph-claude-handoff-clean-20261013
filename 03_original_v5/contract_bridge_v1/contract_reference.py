"""Narrow independent contract reference. No target/native import at import time.

This module neither calls Environment.add_constraints nor imports the upstream
constraint parser. All unsupported clauses fail closed. A runtime bridge check
is evidence for its exact input; no general certificate has been implemented.
"""
from copy import deepcopy
from dataclasses import dataclass
import re


class UnverifiedContract(ValueError):
    status = "UNVERIFIED_CONTRACT"


@dataclass(frozen=True)
class Column:
    table: str
    name: str


@dataclass(frozen=True)
class Node:
    kind: str
    args: tuple
    path: str


@dataclass(frozen=True)
class Contract:
    original_ast: object
    normalized_ast: object
    root: Node
    schema: dict
    ledger: tuple


COMPARISONS = ("lt", "lte", "gt", "gte", "eq", "neq")
REVERSE = {"lt": "gt", "lte": "gte", "gt": "lt", "gte": "lte", "eq": "eq", "neq": "neq"}


def _schema(schema):
    if not isinstance(schema, dict) or not schema:
        raise UnverifiedContract("nonempty complete schema dictionary required")
    groups = [list(schema)]
    for columns in schema.values():
        if not isinstance(columns, dict) or not columns:
            raise UnverifiedContract("nonempty columns required")
        groups.append(list(columns))
        if any(str(t).upper() != "INT" for t in columns.values()):
            raise UnverifiedContract("bridge v1 physical schema is INT only")
    for names in groups:
        if any(not isinstance(n, str) or not re.fullmatch(r"[A-Z_][A-Z0-9_]*", n) or "__" in n for n in names):
            raise UnverifiedContract("uppercase simple schema names without __ required")


def prepare(original_ast, schema):
    """Accept explicit None, root conjunction list, not_null, comparisons, AND.

    An unsupported node anywhere rejects the entire contract. The source AST is
    copied and retained. Only the normalized copy swaps literal-left comparisons.
    """
    _schema(schema)
    names = {}
    for table, fields in schema.items():
        for name in fields:
            encoded = table + "__" + name
            if encoded in names or encoded.split("__", 1) != [table, name]:
                raise UnverifiedContract("nonunique or noninvertible upstream column encoding: " + encoded)
            names[encoded] = Column(table, name)
    ledger = []

    def col(raw, path):
        if isinstance(raw, dict) and set(raw) == {"value"}:
            raw = raw["value"]
        if not isinstance(raw, str) or raw not in names:
            raise UnverifiedContract(path + ": unknown/unsupported single-column reference")
        return names[raw]

    def ref_ast(column):
        return {"value": column.table + "__" + column.name}

    def visit(raw, path):
        if not isinstance(raw, dict) or len(raw) != 1:
            raise UnverifiedContract(path + ": one operator required")
        op, operands = next(iter(raw.items()))
        if op == "and":
            if not isinstance(operands, list):
                raise UnverifiedContract(path + ": AND requires a list")
            children = [visit(child, path + "/and/" + str(i)) for i, child in enumerate(operands)]
            return Node("and", tuple(node for node, _ in children), path), {"and": [ast for _, ast in children]}
        if op == "not_null":
            column = col(operands, path + "/not_null")
            node = Node(op, (column,), path)
            normal = {op: ref_ast(column)}
        elif op in COMPARISONS:
            if not isinstance(operands, list) or len(operands) != 2:
                raise UnverifiedContract(path + ": comparison requires two ordered operands")
            literal_indices = [i for i, item in enumerate(operands) if type(item) is int]
            if len(literal_indices) != 1:
                raise UnverifiedContract(path + ": exactly one Python int literal and one column required")
            li = literal_indices[0]
            column = col(operands[1 - li], path + "/operand/" + str(1 - li))
            literal = operands[li]
            ordered = (literal, column) if li == 0 else (column, literal)
            node = Node(op, ordered, path)
            normal = {REVERSE[op] if li == 0 else op: [ref_ast(column), literal]}
        else:
            raise UnverifiedContract(path + ": unsupported operator " + str(op))
        ledger.append({"source_path": path, "source_ast": deepcopy(raw), "normalized_ast": deepcopy(normal),
                       "source_operator": op, "null_policy": "STRICT_TRUE_ALL_ROWS_OF_REFERENCED_TABLE"})
        return node, normal

    if original_ast is None:
        root, normal = Node("and", (), "$"), None
    elif isinstance(original_ast, list):
        children = [visit(raw, "$/" + str(i)) for i, raw in enumerate(original_ast)]
        root = Node("and", tuple(node for node, _ in children), "$")
        normal = [ast for _, ast in children]
    else:
        raise UnverifiedContract("root must be explicit None or a conjunction list")
    return Contract(deepcopy(original_ast), deepcopy(normal), root, deepcopy(schema), tuple(ledger))


def _ordered_compare(op, left, right):
    # Operand order here is the ORIGINAL source order, never normalized order.
    if op == "lt":
        return left < right
    if op == "lte":
        return left <= right
    if op == "gt":
        return left > right
    if op == "gte":
        return left >= right
    if op == "eq":
        return left == right
    if op == "neq":
        return left != right
    raise UnverifiedContract("unknown comparison operator")


def emit_reference(contract, env, constants):
    """Use shared base variables, without upstream IC compiler/normalizer logic."""
    if set(env.base_databases) != set(contract.schema):
        raise UnverifiedContract("base table inventory differs from complete schema")
    attributes = {}
    for table, fields in contract.schema.items():
        attrs = list(env.base_databases[table].attributes)
        if [a.name.upper() for a in attrs] != list(fields):
            raise UnverifiedContract("base attribute order/name mismatch: " + table)
        for name, attr in zip(fields, attrs):
            attributes[Column(table, name)] = attr

    def conjunction(expressions):
        return constants.And(*expressions) if expressions else constants.Z3_TRUE

    def emit(node):
        if node.kind == "and":
            return conjunction([emit(child) for child in node.args])
        column = next(arg for arg in node.args if isinstance(arg, Column))
        attr = attributes[column]
        terms = []
        for row in env.base_databases[column.table]:
            nonnull = constants.Not(attr.NULL(row.SORT))
            if node.kind == "not_null":
                terms.append(nonnull)
            else:
                operands = [attr.VALUE(row.SORT) if isinstance(arg, Column) else constants.IntVal(str(arg))
                            for arg in node.args]
                terms.append(constants.And(nonnull, _ordered_compare(node.kind, *operands)))
        return conjunction(terms)

    return emit(contract.root)


def evaluate_reference(contract, database):
    """Independent concrete contract check, not a SQL-output correctness oracle."""
    if set(database) != set(contract.schema):
        raise UnverifiedContract("concrete database must include full physical schema")
    values = {}
    for table, fields in contract.schema.items():
        names = list(fields)
        for row in database[table]:
            if not isinstance(row, list) or len(row) != len(names):
                raise UnverifiedContract("row width/type mismatch")
            if any(value is not None and type(value) is not int for value in row):
                raise UnverifiedContract("concrete cells must be int or None")
        for i, name in enumerate(names):
            values[Column(table, name)] = [row[i] for row in database[table]]
    observations = []

    def evaluate(node):
        if node.kind == "and":
            children = [evaluate(child) for child in node.args]
            return all(children)
        column = next(arg for arg in node.args if isinstance(arg, Column))
        rows = []
        for value in values[column]:
            if value is None:
                rows.append(False)
            elif node.kind == "not_null":
                rows.append(True)
            else:
                left, right = [value if isinstance(arg, Column) else arg for arg in node.args]
                rows.append(bool(_ordered_compare(node.kind, left, right)))
        answer = all(rows)
        observations.append({"source_path": node.path, "row_results": rows, "all_rows": answer})
        return answer

    answer = evaluate(contract.root)
    return {"status": "EVALUATED_SUPPORTED_REFERENCE", "holds": answer, "clauses": observations,
            "scope": "explicit narrow reference contract only; no SQL CHECK/DDL convention inferred"}
