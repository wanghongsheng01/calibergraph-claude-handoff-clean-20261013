# GitLab #47 BOOLEAN literal admission

Status: **STATIC_SOURCE_CONFIRMED / TARGET_NOT_RUN**. Date: 2026-10-11.
This subtask performed no target import, parser/SQL/SMT/generator execution or installation. It did not modify either frozen root or the official ParSEval snapshot. This is author preparation, not the final independent review.

## Decision

For the original `projects.pending_delete = 'f'`, the identified defect is an ordinary PostgreSQL boolean-input compatibility omission in ParSEval's literal conversion. It does **not** establish a search limitation, unsupported JOIN/UNION/EXISTS, an original-query failure observed at runtime, or a new generation mechanism. If execution reaches the identified contextual-literal branch, the locked source deterministically raises `ValueError` for `f`. Earlier full-query qualification/lowering blockers remain possible until the authorized real parser check.

The smallest useful repair adds `t`/`f` recognition only when the dialect is PostgreSQL and the semantic target kind is BOOLEAN. The original query bytes, literals, clauses and C stay unchanged. A separate adapted baseline must be labeled as such; a parser pass is not NEQ, and absence of NEQ is not failure or an equivalence proof.

## Inputs and versions

- ParSEval: `88cfe245bcf249a5b0df561a6b09c116ff2a2896`; use the new [official source directory](../sources_local/parseval_official/) and its source lock, not patched old snapshots.
- SQLGlot: official lock requires **23.12.1**. Official tag resolves to `ba16401a9ea5eed8461d9bf386b1ba0f48df6fa3`. [Tag API](https://api.github.com/repos/tobymao/sqlglot/git/ref/tags/v23.12.1).
- Installed SQLGlot metadata found by text read at `/Users/loctek/Library/Python/3.9/lib/python/site-packages/sqlglot/_version.py` says **30.12.0**, commit `g64e268a5d`. It was not imported and is not a substitute for the locked dependency.
- Original before: SHA256 `36b253319cf60145d752be6cb4ed42daeffd7398881cde2c02d09353cdea75d7`, 873 bytes, two `pending_delete = 'f'` occurrences. Original after: `1ca3717156b1dd7bc3f4eb30a9ec998034da18492b6b0bc05d66d3f600c40de2`, 489 bytes, one occurrence.
- Historical schema declares `pending_delete` boolean, default false, nullable (schema.rb:1054). A default does not remove explicit NULL from its domain.

## Exact path and real types

The following is a source-derived expectation, **not an observed runtime AST dump**. Source line numbers below refer to the saved source files; web extraction may suppress blank lines.

| Stage | Actual class/type contract from source | Evidence |
|---|---|---|
| SQLGlot syntax | A quoted `f` is `exp.Literal(this="f", is_string=True)`; unquoted FALSE follows a distinct `exp.Boolean(this=False)` path. Newly built expression `.type` starts as None. | [parser:663–697](boolean_sources/sqlglot_v23.12.1_parser.py.txt), [expressions:100–108,243–253](boolean_sources/sqlglot_v23.12.1_expressions.py.txt); PostgreSQL tokenizer inherits ordinary quote handling. |
| SQLGlot annotation | String literal gets `exp.DataType(Type.VARCHAR)`. `pending_delete` gets BOOLEAN from the schema; `exp.EQ` has BOOLEAN result type. Annotating the comparison result does not turn its string operand into `exp.Boolean`. `.type` is a DataType object, `.type.this` is its enum. | [annotate_types:346–401,437–483](boolean_sources/sqlglot_v23.12.1_annotate_types.py.txt). |
| ParSEval entry | `lower_query` parses with catalog dialect, normalizes syntax, qualifies using catalog mapping, annotates types, then builds its own semantic IR. | [compiler.py:422–489](../sources_local/parseval_official/src/parseval/parser/query/compiler.py). |
| Equality operand planning | EQ → `_comparison` → `_operands` → `coercible_pair`. Right Literal and left Column cause the right plan to receive the left column's `binding.sort`. | [expression.py:130–147,313–330,1017–1024,1143–1156,1217–1228](../sources_local/parseval_official/src/parseval/parser/expression.py). |
| Semantic type override | For a Literal with `expected`, `expected.sql_type` takes priority over SQLGlot's VARCHAR annotation. Here it is `ScalarType(TypeKind.BOOLEAN)`; the emitted literal is nonnullable, while the column remains nullable. | [expression.py:187–216](../sources_local/parseval_official/src/parseval/parser/expression.py). |
| Defect | `literal_value` delegates string/non-STRING inputs to `parse_string_cast_literal`. BOOLEAN recognizes case-folded `true/1/false/0`; `f` falls through to ValueError. | [dialect.py:166–202](../sources_local/parseval_official/src/parseval/parser/dialect.py). |

The PostgreSQL tokenization source, expression API, annotation implementation and dialect subclass are preserved in [boolean_sources](boolean_sources/), with versions/URLs/hashes in [BOOLEAN_SOURCE_LOCK.json](BOOLEAN_SOURCE_LOCK.json). Official code links: [parser](https://github.com/tobymao/sqlglot/blob/ba16401a9ea5eed8461d9bf386b1ba0f48df6fa3/sqlglot/parser.py#L663), [type annotation](https://github.com/tobymao/sqlglot/blob/ba16401a9ea5eed8461d9bf386b1ba0f48df6fa3/sqlglot/optimizer/annotate_types.py#L472), [expression type API](https://github.com/tobymao/sqlglot/blob/ba16401a9ea5eed8461d9bf386b1ba0f48df6fa3/sqlglot/expressions.py#L243).

## PostgreSQL semantics

An untyped quoted constant is resolved using the other operand's known boolean type for this binary operator. PostgreSQL accepts `f` as false. Ordinary equality yields UNKNOWN for a NULL operand, and WHERE retains only TRUE. [Operator resolution](https://www.postgresql.org/docs/9.6/typeconv-oper.html), [boolean input](https://www.postgresql.org/docs/9.6/datatype-boolean.html), [comparison semantics](https://www.postgresql.org/docs/9.6/functions-comparison.html), [WHERE](https://www.postgresql.org/docs/9.6/queries-table-expressions.html#QUERIES-WHERE).

| pending_delete | `pending_delete = 'f'` | WHERE |
|---|---|---|
| FALSE | TRUE | retain |
| TRUE | FALSE | discard |
| NULL | UNKNOWN | discard |

Do not rewrite the original predicate to `IS FALSE`: its value for NULL is FALSE, not UNKNOWN. Do not use Python truthiness (`bool("f")` is True), raw text comparison, or SQLite's boolean/text behavior as the PostgreSQL semantics.

PostgreSQL's complete accepted spellings also include unique prefixes of true/false/yes/no/on/off and single-character 1/0, ignoring letter case and supported surrounding whitespace. The `o` prefix is ambiguous and rejected. The proposed minimal repair intentionally covers only t/f (and T/F); it is **not** a claim of complete boolin compatibility. Full alias/whitespace support is optional separate ordinary compatibility work and is unnecessary for the unchanged #47 input. [Fixed PostgreSQL bool.c](https://github.com/postgres/postgres/blob/REL9_6_24/src/backend/utils/adt/bool.c#L33).

## Reviewable ordinary adapter

[boolean_adapter.py](../implementation/boolean_adapter.py) is an unexecuted draft. It temporarily wraps the bound conversion method on **one** Catalog.dialect instance, recognizes t/f only for `dialect.name == "postgres"` and `sql_type.kind is TypeKind.BOOLEAN`, delegates every other case, and restores the original instance state in `finally`. It changes no source file or SQL AST, performs no automatic installation, and imports no target package. The runner must pass the real `parseval.terms.sorts.TypeKind.BOOLEAN` object; a SQLGlot enum or string is a different type domain.

The target SQLDialect has no slots restricting this instance override. Catalog constructs its own SQLDialect at catalog.py:111. Thus using `generate(original_sql, same_catalog, ...)` or `lower_query(original_sql, same_catalog)` within the wrapper reaches the adapted object. The stock `disprove` entry creates a fresh Catalog internally, so adapting an unrelated Catalog would have no effect. The parent runner must either use its reviewed generation/replay harness with the adapted Catalog, or explicitly instrument the Catalog actually used by disprove. Do not label an unadapted call as adapted. Do not share that Catalog concurrently.

## Proposed real validation without changing SQL

All below is pending the parent run plan and separate independent review. No step has been executed here.

1. Verify official source lock, locked dependency hashes/version, unchanged original SQL SHA256 and full historical C; stop on mismatch. Do not accept host SQLGlot 30.12.0 as an equivalent environment.
2. In the isolated locked environment, use the **original two SQL byte strings** and the real full Catalog. Record each matching EQ node's operand class, literal text/is_string and `.type.this` after actual annotation; expect three total original f occurrences, right Literal/VARCHAR and left Column/BOOLEAN. Record actual observations rather than substituting the source predictions above.
3. Call unmodified `lower_query` once per original query with no SMT/generation. Capture the exact exception/trace and furthest successful stage. Reaching `parse_string_cast_literal` with f/BOOLEAN confirms the concrete defect; an earlier failure stays an earlier admission blocker. Keep raw and adapted statuses separate.
4. On the same isolated source/dependencies and original SQL, activate only the instance adapter and repeat lowering; capture how many f→False conversions occurred and the real resulting `ScalarSort(BOOLEAN, False)` literal. A complete lowering pass confirms parser admission only, not query equivalence or generation success.
5. Use actual SQLGlot Literal objects and actual ParSEval BOOLEAN/STRING types for narrow regressions: f/F→False, t/T→True in postgres BOOLEAN context; original true/false/1/0 behavior delegates; STRING f stays text; unknown text remains rejected; other dialects do not acquire PostgreSQL aliases. Check wrapper restoration on normal and exceptional exit. Mock-only tests are insufficient.
6. Separately evaluate the predicate on FALSE/TRUE/NULL through the real semantic interpreter and isolated PostgreSQL backend, retaining UNKNOWN at the expression level and only TRUE at WHERE. Small predicate fixtures are calibration only; they do not replace either original query as the benchmark input. Once generation is authorized, validate candidates under original fullC and replay **both original SQL strings**, comparing the full projects projection, types, NULLs, row multiplicities and declared descending order.

Outcome vocabulary: SOURCE_CONFIRMED_COMPATIBILITY_DEFECT, PARSER_ADMITTED_RAW / PARSER_ADMITTED_ADAPTED, BLOCKED_EARLIER_STAGE, GENERATION_NOT_RUN, NO_NEQ_FOUND, or VALID_FULLC_NEQ. Keep timeout/unsupported/backend errors separate. Never convert NO_NEQ_FOUND into failure, EQ proof, or search hardness.
