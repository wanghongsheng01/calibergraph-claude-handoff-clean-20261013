"""Loss-aware structural admission for the pinned official VeriEQL encoder.

This module imports only the standard library and never imports target code.
It validates, but never rewrites, the complete physical schema or original IC.
Admission is not IC satisfiability, SQL validity, or a cross-dialect guarantee.
"""
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
import re


class AdmissionError(ValueError):
    def __init__(self, kind, reason):
        self.kind = kind
        self.reason = reason
        super().__init__(reason)


SCHEMA_TYPES = frozenset({'INT', 'BOOL', 'BOOLEAN', 'DATE', 'VARCHAR'})
OFFICIAL_OPERATORS = frozenset({
    'primary', 'foreign', 'inc', 'value', 'literal', 'boolean', 'int',
    'varchar', 'date', 'lt', 'lte', 'gt', 'gte', 'eq', 'neq', 'or',
    'and', 'not_null', 'in', 'between',
})
COMPARISONS = frozenset({'lt', 'lte', 'gt', 'gte', 'eq', 'neq'})
DATE_LITERAL = re.compile(r'^[0-9]{2,4}[-_:/][0-9]{1,2}[-_:/][0-9]{1,2}$')


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_schema_and_contract(schema, constraints):
    """Return a JSON-safe admission summary or raise AdmissionError.

    The caller must distinguish an absent constraint field from an explicit
    null before calling. None and [] are preserved as separate source states.
    Unrecognized schema types and malformed/unsupported IC reject the whole
    case; no clause, field, table, or operand is dropped or normalized.
    """
    def fail(kind, reason, path):
        raise AdmissionError(kind, path + ': ' + reason)

    if not isinstance(schema, dict) or not schema:
        fail('SCHEMA_UNSUPPORTED', 'schema must be a nonempty object', 'schema')
    names = {}
    refs = {}
    type_counts = Counter()
    for table, fields in schema.items():
        path = 'schema.' + str(table)
        if not isinstance(table, str) or not table.strip() or '__' in table:
            fail('SCHEMA_UNSUPPORTED', 'invalid table name or ambiguous __ table binding', path)
        upper = table.upper()
        if upper in names:
            fail('SCHEMA_UNSUPPORTED', 'table names collide after official uppercase conversion', path)
        names[upper] = table
        if not isinstance(fields, dict) or not fields:
            fail('SCHEMA_UNSUPPORTED', 'table must have a nonempty field object', path)
        columns = set()
        for column, typ in fields.items():
            cpath = path + '.' + str(column)
            if not isinstance(column, str) or not column.strip():
                fail('SCHEMA_UNSUPPORTED', 'column name must be a nonempty string', cpath)
            ckey = column.upper()
            if ckey in columns:
                fail('SCHEMA_UNSUPPORTED', 'column names collide after official uppercase conversion', cpath)
            columns.add(ckey)
            if not isinstance(typ, str) or typ.upper() not in SCHEMA_TYPES:
                fail('SCHEMA_UNSUPPORTED', 'official create_database does not encode this type: ' + repr(typ), cpath)
            type_counts[typ.upper()] += 1
            refs[upper + '__' + ckey] = (table, column)

    counts = Counter()
    reference_counts = Counter()
    notes = set()

    def reference(text, path):
        # Official _get_attribute performs a case-sensitive lookup using the
        # first __ separator after create_database uppercases physical names.
        if not isinstance(text, str) or text not in refs:
            fail('CONTRACT_UNSUPPORTED', 'reference does not bind exactly in official environment: ' + repr(text), path)
        reference_counts[text] += 1
        return ('column', refs[text][0])

    def date_literal(text, path):
        if not isinstance(text, str) or not DATE_LITERAL.fullmatch(text.strip()):
            fail('CONTRACT_UNSUPPORTED', 'date literal must be a supported date without dropped timestamp', path)
        year, month, day = re.split(r'[-_:/]', text.strip())
        if len(year) < 4:
            year = '20'[:4-len(year)] + year
            notes.add('OFFICIAL_SHORT_DATE_YEAR_EXPANSION')
        try:
            datetime(int(year), int(month), int(day))
        except ValueError:
            fail('CONTRACT_UNSUPPORTED', 'invalid calendar date', path)
        return ('scalar', None)

    def args_list(args, path, length=None):
        if not isinstance(args, list) or (length is not None and len(args) != length):
            fail('CONTRACT_UNSUPPORTED', 'expected operand list' + ('' if length is None else ' of arity ' + str(length)), path)

    def require(result, kind, path):
        if result[0] != kind:
            fail('CONTRACT_UNSUPPORTED', 'expected ' + kind + ', got ' + result[0], path)
        return result

    def scalar_or_column(expr, path):
        if isinstance(expr, list) and not expr:
            fail('CONTRACT_UNSUPPORTED', 'empty comparison operand silently becomes a vacuous TRUE conjunction', path)
        result = visit(expr, path)
        if result[0] not in ('scalar', 'column', 'scalar_list'):
            fail('CONTRACT_UNSUPPORTED', 'comparison operand is not a scalar or column', path)
        return result

    def visit(expr, path):
        if type(expr) is int:
            return ('scalar', None)
        if type(expr) is float:
            if not math.isfinite(expr):
                fail('CONTRACT_UNSUPPORTED', 'nonfinite numeric literal', path)
            return ('scalar', None)
        if isinstance(expr, str):
            if DATE_LITERAL.fullmatch(expr.strip()):
                return date_literal(expr, path)
            return reference(expr, path)
        if isinstance(expr, list):
            for i, child in enumerate(expr):
                require(visit(child, path + '[' + str(i) + ']'), 'scalar', path)
            return ('scalar_list', None)
        if not isinstance(expr, dict) or len(expr) != 1:
            fail('CONTRACT_UNSUPPORTED', 'IC nodes must be single-key objects or supported operands', path)
        op, args = next(iter(expr.items()))
        if op not in OFFICIAL_OPERATORS:
            fail('CONTRACT_UNSUPPORTED', 'unknown official operator: ' + str(op), path)
        counts[op] += 1
        if op == 'value':
            return reference(args, path + '.value')
        if op == 'literal':
            if not isinstance(args, str):
                fail('CONTRACT_UNSUPPORTED', 'literal wrapper requires a string', path)
            notes.add('OFFICIAL_STRING_LITERAL_INTEGER_ENCODING')
            return ('scalar', None)
        if op == 'date':
            if isinstance(args, str) and DATE_LITERAL.fullmatch(args.strip()):
                return date_literal(args, path + '.date')
            fail('CONTRACT_UNSUPPORTED', 'date(column) only constrains its first row in official code; unsupported full-column type contract', path)
        if op == 'primary':
            args_list(args, path)
            if not args:
                fail('CONTRACT_UNSUPPORTED', 'empty primary key silently becomes TRUE', path)
            columns = [require(visit(x, path + '.primary[' + str(i) + ']'), 'column', path)
                       for i, x in enumerate(args)]
            if len({x[1] for x in columns}) != 1:
                fail('CONTRACT_UNSUPPORTED', 'cross-table primary would use positional zip rather than a physical key', path)
            return ('predicate', None)
        if op == 'foreign':
            args_list(args, path, 2)
            for i, x in enumerate(args):
                require(visit(x, path + '.foreign[' + str(i) + ']'), 'column', path)
            notes.add('OFFICIAL_FOREIGN_REQUIRES_NON_NULL_SOURCE_AND_TARGET_MATCH')
            return ('predicate', None)
        if op in {'inc', 'boolean', 'int', 'varchar', 'not_null'}:
            require(visit(args, path + '.' + op), 'column', path)
            if op == 'inc':
                notes.add('OFFICIAL_INC_DEPENDS_ON_PHYSICAL_ROW_ORDER_AND_DROPS_AT_N_LE_1')
            return ('predicate', None)
        if op in COMPARISONS:
            args_list(args, path, 2)
            left = scalar_or_column(args[0], path + '.' + op + '[0]')
            right = scalar_or_column(args[1], path + '.' + op + '[1]')
            if left[0] == right[0] == 'column':
                notes.add('OFFICIAL_COLUMN_COMPARISON_USES_ALL_CARTESIAN_ROW_PAIRS')
            if left[0] != 'column' and right[0] == 'column' and op in {'lt','lte','gt','gte'}:
                notes.add('OFFICIAL_LITERAL_LEFT_ORDER_COMPARISON_REVERSES_OPERANDS_WITHOUT_REVERSING_OPERATOR')
            return ('predicate', None)
        if op in {'or', 'and'}:
            args_list(args, path)
            for i, x in enumerate(args):
                require(visit(x, path + '.' + op + '[' + str(i) + ']'), 'predicate', path)
            if not args:
                notes.add('EXPLICIT_EMPTY_' + op.upper() + '_PRESERVED')
            return ('predicate', None)
        if op == 'in':
            args_list(args, path, 2)
            require(visit(args[0], path + '.in[0]'), 'column', path)
            args_list(args[1], path + '.in[1]')
            require(visit(args[1], path + '.in[1]'), 'scalar_list', path)
            if not args[1]:
                notes.add('EXPLICIT_EMPTY_IN_CHOICES_PRESERVED')
            return ('predicate', None)
        if op == 'between':
            args_list(args, path, 3)
            require(visit(args[0], path + '.between[0]'), 'column', path)
            for i in (1, 2):
                require(visit(args[i], path + '.between[' + str(i) + ']'), 'scalar', path)
            return ('predicate', None)
        fail('CONTRACT_UNSUPPORTED', 'unhandled official operator', path)

    if constraints is not None:
        if not isinstance(constraints, list):
            fail('CONTRACT_UNSUPPORTED', 'constraint must be an explicit null or clause list', 'constraint')
        for i, clause in enumerate(constraints):
            path = 'constraint[' + str(i) + ']'
            require(visit(clause, path), 'predicate', path)
    return {
        'status': 'ADMITTED_STRUCTURALLY',
        'schema_sha256': _digest(schema),
        'constraint_sha256': _digest(constraints),
        'table_count': len(schema),
        'column_count': sum(len(fields) for fields in schema.values()),
        'schema_type_counts': dict(sorted(type_counts.items())),
        'constraint_source_state': ('EXPLICIT_NULL' if constraints is None else
                                    'EXPLICIT_EMPTY_LIST' if not constraints else 'EXPLICIT_CLAUSE_LIST'),
        'original_clause_count': None if constraints is None else len(constraints),
        'operator_counts': dict(sorted(counts.items())),
        'reference_counts': dict(sorted(reference_counts.items())),
        'full_preservation': True,
        'dropped_tables': 0,
        'dropped_fields': 0,
        'dropped_clauses': 0,
        'rewrites': 0,
        'operational_notes': sorted(notes),
        'scope': 'Structural admission only; complete unchanged source objects; official operational IC, not SQL-DDL or natural-language truth; satisfiability not checked.',
    }
