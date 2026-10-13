"""Draft ordinary PostgreSQL t/f literal compatibility adapter; NOT RUN.

Reviewed target: ParSEval 88cfe245bcf249a5b0df561a6b09c116ff2a2896.
The runner must separately verify the official source lock and sqlglot==23.12.1.
This module imports no target library, edits no SQL, and installs nothing itself.
It repairs only PostgreSQL t/f aliases in an already known BOOLEAN context.
It is deliberately not a complete implementation of PostgreSQL boolean input.
"""

from contextlib import contextmanager


PATCH_ID = "postgres_boolean_tf_literal_aliases_v1"
TARGET_COMMIT = "88cfe245bcf249a5b0df561a6b09c116ff2a2896"
VALIDATION_STATUS = "DRAFT_NOT_RUN"


@contextmanager
def postgres_tf_literal_aliases(dialect, boolean_kind):
    """Temporarily adapt one Catalog.dialect instance.

    Pass the real parseval.terms.sorts.TypeKind.BOOLEAN as boolean_kind.
    A string such as 'BOOLEAN', SQLGlot's enum, and a test double are not evidence
    that the real lowering path was exercised. The caller owns this dialect
    instance for the whole context; do not share it with concurrent workers.

    All other values, SQL types and dialects delegate to the saved bound method.
    SQL NULL remains on ScalarCompiler's separate exp.Null path.
    """
    attribute = "parse_string_cast_literal"
    absent = object()
    previous_override = vars(dialect).get(attribute, absent)
    original = getattr(dialect, attribute)

    def adapted(value, sql_type):
        if dialect.name == "postgres" and sql_type.kind is boolean_kind:
            normalized = value.casefold()
            if normalized == "t":
                return True
            if normalized == "f":
                return False
        return original(value, sql_type)

    setattr(dialect, attribute, adapted)
    try:
        yield dialect
    finally:
        if previous_override is absent:
            delattr(dialect, attribute)
        else:
            setattr(dialect, attribute, previous_override)
