"""GitLab #47: source-declared full-column schema for a new PostgreSQL replay.

Importing this module uses only the standard library.  ``build_catalog`` is the
explicit, separately reviewed ParSEval entry point; it is never called by the
static CLI.  Queries remain in their original files and are never rewritten.
The source did not specify a collation.  PostgreSQL inherits the replay database
default, whose identity and equality semantics must be recorded by the runner.
This adapter does not claim to recreate the historical server or its session.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re


CASE = "gitlab#47"
WORKSPACE = Path(__file__).resolve().parents[2]
OLD = "calibergraph_trigger_generation_20261011_01"
NEW = "calibergraph_parseval_admission_20261011_03"
TABLE_COUNTS = {"projects": 42, "users": 67, "users_star_projects": 5,
                "project_authorizations": 3}
EXPECTED = {
    f"{OLD}/data/SOURCE_INPUTS.json": "9f35e5b1b293455f21e4d4427d6df72f08d397dc2ba97da6cde31c8942ad9d92",
    f"{OLD}/data/REPLAY_SCHEMA.json": "fdd8b509e0321dfe98d598ccc02caa50c9c686e2443482ff201f7e7203e55132",
    f"{OLD}/sources_local/selection/gitlab/47_parent_db__schema.rb": "988b32f89adb6c93c74bf9a3c077807faa05b6fadeb402d85d8fa0b5d18c750e",
    f"{OLD}/sources_local/selection/gitlab/g47_original_before.sql": "36b253319cf60145d752be6cb4ed42daeffd7398881cde2c02d09353cdea75d7",
    f"{OLD}/sources_local/selection/gitlab/g47_original_after.sql": "1ca3717156b1dd7bc3f4eb30a9ec998034da18492b6b0bc05d66d3f600c40de2",
    f"{NEW}/sources_local/gitlab_mapping/g47_parent_Gemfile.lock": "52e68c71ebfa857bd1706563157d961a76d3728594eb6976d28e2fc2b788e1b4",
    f"{NEW}/sources_local/gitlab_mapping/g47_parent_database.yml.postgresql": "b94ef6809ac5ac6d357803fff9598fe1067af8c16804611b8c6af19c878d1a99",
    f"{NEW}/sources_local/gitlab_mapping/rails_4_2_8_postgresql_adapter.rb": "8e0bd59434d11a15d8ce8c51c4df8de92067c712c5beb6d0fdc65ed2cfc40704",
    f"{NEW}/sources_local/gitlab_mapping/rails_4_2_8_abstract_schema_statements.rb": "da538327481faa2862a49e6216a5cdc946ade5bf21248c4f8bfe99f4494592df",
    f"{NEW}/sources_local/gitlab_mapping/rails_4_2_8_postgresql_schema_statements.rb": "944439b6347892c237757f1f30e9a74d39f1b1f83fdace93c91bf72bd9ebb224",
}
PG_TYPES = {"integer": "INTEGER", "boolean": "BOOLEAN", "string": "VARCHAR",
            "text": "TEXT", "datetime": "TIMESTAMP WITHOUT TIME ZONE", "date": "DATE"}


class MappingError(ValueError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_case(workspace=WORKSPACE):
    """Hash-pin sources, then cross-check JSON metadata against Ruby declarations.

    This is a deliberately narrow line-oriented source check, not a Ruby or SQL
    parser.  It rejects unrecognized changes rather than guessing their meaning.
    """
    workspace = Path(workspace)
    for path, expected in EXPECTED.items():
        if digest(workspace / path) != expected:
            raise MappingError(f"Frozen input changed: {path}")
    record = json.loads((workspace / f"{OLD}/data/REPLAY_SCHEMA.json").read_text())["cases"][CASE]
    record = deepcopy(record)
    lines = (workspace / record["source_schema"]["path"]).read_text().splitlines()
    if list(record["tables"]) != list(TABLE_COUNTS):
        raise MappingError("Table closure/order changed")
    for name, table in record["tables"].items():
        cols = table["columns"]
        if len(cols) != TABLE_COUNTS[name]:
            raise MappingError(f"Column count changed: {name}")
        start = table["source_start_line"] - 1
        end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "end")
        declarations = [re.fullmatch(r'    t\.(\w+) "([^"]+)"(.*)', line)
                        for line in lines[start + 1:end]]
        if not all(declarations):
            raise MappingError(f"Unrecognized column declaration in {name}")
        actual_names = [m.group(2) for m in declarations]
        implicit_id = "id: false" not in lines[start]
        if [c["name"] for c in cols] != (["id"] if implicit_id else []) + actual_names:
            raise MappingError(f"Column names/order changed: {name}")
        for c in cols:
            if c.get("implicit"):
                if c["name"] != "id" or c["nullable"] or c["source_type"] != "integer":
                    raise MappingError("Invalid implicit ID")
                continue
            m = re.fullmatch(r'    t\.(\w+) "([^"]+)"(.*)', lines[c["source_line"] - 1])
            if (m.group(1), m.group(2), "null: false" not in m.group(3)) != (
                    c["source_type"], c["name"], c["nullable"]):
                raise MappingError(f"Source column mismatch: {name}.{c['name']}")
            opts = m.group(3)
            if c["limit"] is not None or any(x in opts for x in ("limit:", "precision:", "scale:", "collation:")):
                raise MappingError("New type option requires explicit review")
            match = re.search(r'default: ("(?:[^"\\]|\\.)*"|true|false|-?\d+)(?:,|$)', opts)
            if (match is not None) != ("default" in c):
                raise MappingError(f"Default metadata mismatch: {name}.{c['name']}")
            if match and json.loads(match.group(1)) != c["default"]:
                raise MappingError(f"Default value changed: {name}.{c['name']}")
        actual_unique = []
        for line in lines:
            m = re.fullmatch(r'  add_index "' + re.escape(name) + r'", (\[[^\]]+\]), (.*)', line)
            if m and "unique: true" in m.group(2):
                actual_unique.append(json.loads(m.group(1)))
        if table["unique_keys"] != actual_unique:
            raise MappingError(f"Source UNIQUE mismatch: {name}")
        if table["primary_key"] != (["id"] if implicit_id else []):
            raise MappingError(f"Source PK mismatch: {name}")
        actual_fks = [line for line in lines if line.startswith(f'  add_foreign_key "{name}",')]
        expected_fks = [f'  add_foreign_key "{name}", "{fk["ref_table"]}", on_delete: :cascade'
                        for fk in table["foreign_keys"]]
        if actual_fks != expected_fks:
            raise MappingError(f"Source FK closure mismatch: {name}")
    # SQLite's earlier t/f encoding is not used for this PostgreSQL adapter.
    record.pop("bool_representation", None)
    return record


def ident(value):
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", value):
        raise MappingError(f"Unexpected identifier: {value!r}")
    return '"' + value + '"'


def load_schema(workspace=WORKSPACE):
    """Return source-checked ordered tables for the replay worker."""
    return load_case(workspace)["tables"]


def make_ddl(tables=None, *, serial_defaults=True):
    """Worker entry point; retain SERIAL defaults in the PostgreSQL backend."""
    case = None if tables is None else {"tables": tables}
    return postgres_ddl(case, serial_defaults=serial_defaults)


def default_sql(column):
    if "default" not in column:
        return None
    value = column["default"]
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    raise MappingError("Unsupported source default")


def postgres_ddl(case=None, *, serial_defaults=True):
    """Return new-engine DDL, preserving every declared column and constraint.

    serial_defaults=True preserves Rails implicit ID sequence behavior.  The
    explicit-row-only form uses INTEGER for Catalog storage range recognition;
    this form must never be used to test omitted-ID insertion/default behavior.
    No COLLATE clause, CHECK, extra FK, or replacement UNIQUE is introduced.
    Nonunique performance indexes/extensions are outside static instance C.
    """
    case = load_case() if case is None else case
    statements = []
    for name, table in case["tables"].items():
        definitions = []
        for c in table["columns"]:
            sql_type = "SERIAL" if serial_defaults and c.get("implicit") else PG_TYPES[c["source_type"]]
            definition = f"{ident(c['name'])} {sql_type}"
            value = default_sql(c)
            if value is not None:
                definition += " DEFAULT " + value
            if not c["nullable"]:
                definition += " NOT NULL"
            definitions.append(definition)
        if table["primary_key"]:
            definitions.append("PRIMARY KEY (" + ", ".join(map(ident, table["primary_key"])) + ")")
        for columns in table["unique_keys"]:
            definitions.append("UNIQUE (" + ", ".join(map(ident, columns)) + ")")
        for fk in table["foreign_keys"]:
            definitions.append("FOREIGN KEY (" + ", ".join(map(ident, fk["columns"])) + ") REFERENCES "
                               + ident(fk["ref_table"]) + " (" + ", ".join(map(ident, fk["ref_columns"]))
                               + ") ON DELETE CASCADE")
        statements.append(f"CREATE TABLE {ident(name)} (\n  " + ",\n  ".join(definitions) + "\n);")
    return "\n\n".join(statements) + "\n"


def build_catalog(case=None):
    """Execute only after review: create real ParSEval Catalog and audit full C.

    Catalog INTEGER for implicit IDs preserves PostgreSQL SERIAL's int32 value
    domain. Sequence allocation is outside explicit complete-row generation;
    backend DDL retains SERIAL. No collation is invented for an unspecified source.
    """
    from parseval.catalog import Catalog, ColumnDecl
    from parseval.identifiers import Identifier
    from parseval.terms.constraints import NullConflictPolicy, ForeignKeyMatch
    from parseval.terms.sorts import ScalarSort, INTEGER, BOOLEAN, STRING, TIMESTAMP, DATE

    case = load_case() if case is None else case
    types = {"integer": INTEGER, "boolean": BOOLEAN, "string": STRING,
             "text": STRING, "datetime": TIMESTAMP, "date": DATE}
    catalog = Catalog(dialect="postgres")
    for name, table in case["tables"].items():
        columns = [ColumnDecl(Identifier(c["name"]), ScalarSort(types[c["source_type"]], c["nullable"]),
                              declared_type=PG_TYPES[c["source_type"]], default_sql=default_sql(c))
                   for c in table["columns"]]
        catalog.register_table(name, columns)
    for name, table in case["tables"].items():
        target = catalog.resolve_table(name)
        if table["primary_key"]:
            catalog.register_primary_key(target, table["primary_key"])
        for key in table["unique_keys"]:
            catalog.register_unique(target, key, null_policy=NullConflictPolicy.NULLS_DISTINCT)
    for name, table in case["tables"].items():
        for fk in table["foreign_keys"]:
            catalog.register_foreign_key(catalog.resolve_table(name), fk["columns"],
                                         catalog.resolve_table(fk["ref_table"]), fk["ref_columns"],
                                         match=ForeignKeyMatch.SIMPLE)
    audit_catalog(catalog, case)
    return catalog


def audit_catalog(catalog, case=None):
    """Reject silently dropped, added, inactive, mistyped, or misbound constraints."""
    case = load_case() if case is None else case
    if catalog.dialect.name != "postgres" or len(catalog.tables()) != 4:
        raise MappingError("Wrong dialect or table closure")
    observed = Counter()
    for name, source in case["tables"].items():
        table = catalog.resolve_table(name)
        if [c.name.text for c in table.columns] != [c["name"] for c in source["columns"]]:
            raise MappingError(f"Catalog columns/order differ: {name}")
        for binding, original in zip(table.columns, source["columns"], strict=True):
            spec = table.column_spec(binding.id)
            if spec.sort.nullable != original["nullable"] or binding.declared_type != PG_TYPES[original["source_type"]]:
                raise MappingError(f"Catalog type/nullability differs: {name}.{original['name']}")
            expected_kind = {"integer": "INTEGER", "boolean": "BOOLEAN", "string": "STRING",
                             "text": "STRING", "datetime": "TIMESTAMP", "date": "DATE"}[original["source_type"]]
            if spec.sort.sql_type.kind.name != expected_kind or binding.storage_type.kind.name != expected_kind:
                raise MappingError(f"Catalog native type differs: {name}.{original['name']}")
            if spec.collation is not None:
                raise MappingError("Unexpected explicit collation; source inherits database default")
            if original["source_type"] == "integer" and binding.storage_type.integer_bits != 32:
                raise MappingError("INTEGER storage lost signed int32 domain")
            if original["source_type"] in ("string", "text") and binding.storage_type.max_length is not None:
                raise MappingError("Invented string length limit")
            if binding.default_sql != default_sql(original):
                raise MappingError("Catalog explicit default mismatch")
        def names(ids):
            return tuple(catalog.resolve_column(table, i).name.text for i in ids)
        keys, fks, nn = [], [], []
        for c in table.constraints:
            kind = type(c).__name__
            observed[kind] += 1
            if not c.metadata.proof_active:
                raise MappingError(f"Inactive constraint: {name}:{kind}:{c.metadata}")
            if kind == "NotNullDecl":
                nn.append(catalog.resolve_column(table, c.column).name.text)
            elif kind in ("PrimaryKeyDecl", "UniqueDecl"):
                keys.append((kind, names(c.columns)))
                if kind == "UniqueDecl" and c.null_policy.value != "nulls_distinct":
                    raise MappingError("Nullable UNIQUE lost NULLS DISTINCT")
            elif kind == "ForeignKeyDecl":
                if c.match.value != "simple":
                    raise MappingError("Source foreign key lost MATCH SIMPLE")
                target = next(t for t in catalog.tables() if t.relation == c.target_relation)
                fks.append((names(c.source), target.name.qualified_name,
                            tuple(catalog.resolve_column(target, x).name.text for x in c.target)))
            else:
                raise MappingError(f"Unexpected constraint: {kind}")
        expected_keys = [("UniqueDecl", tuple(k)) for k in source["unique_keys"]]
        if source["primary_key"]:
            expected_keys.append(("PrimaryKeyDecl", tuple(source["primary_key"])))
        expected_fks = [(tuple(f["columns"]), f["ref_table"], tuple(f["ref_columns"])) for f in source["foreign_keys"]]
        if sorted(keys) != sorted(expected_keys) or sorted(fks) != sorted(expected_fks):
            raise MappingError(f"Catalog key/FK signature differs: {name}")
        if sorted(nn) != sorted(c["name"] for c in source["columns"] if not c["nullable"]):
            raise MappingError(f"Catalog NOT NULL set differs: {name}")
    expected = {"NotNullDecl": 32, "PrimaryKeyDecl": 3, "UniqueDecl": 6, "ForeignKeyDecl": 2}
    if dict(observed) != expected:
        raise MappingError(f"Catalog constraint census differs: {dict(observed)}")
    return {"status": "FULL_DECLARED_C_ACTIVE", "columns": 117, "constraints": dict(observed),
            "proof_active_count": sum(observed.values()), "inactive_count": 0,
            "historical_engine_replay": False, "source_collation": "UNSPECIFIED_UNKNOWN"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ddl", action="store_true", help="Print derived PostgreSQL DDL; do not execute it")
    args = parser.parse_args()
    case = load_case()
    if args.ddl:
        print(postgres_ddl(case), end="")
    else:
        print(json.dumps({"case": CASE, "status": "STATIC_SOURCE_CHECK_PASS",
                          "tables": TABLE_COUNTS, "columns": 117,
                          "target_imported": False, "sql_executed": False}))
