# Static workload inventory — 2026-10-12

Repeated multiquery batches sharing the complete supplied schema/IC are established in the public artifacts. Independent production version lineage is **not** established. This inventory is development-data description, not a benchmark, held-out evaluation, scientific result, eligibility determination, or performance claim.

| Source | Pair records | SQL slots | Full supplied schema+IC contexts | Multi-record contexts | Records in those contexts | Unique ordered SQL-string pairs | Unique individual SQL strings |
|---|---:|---:|---:|---:|---:|---:|---:|
| ParSEval BIRD | 1,534 | 3,068 | 11 | 11 | 1,534 | 1,530 | 2,891 |
| VeriEQL LeetCode | 23,994 | 47,988 | 52 | 52 | 23,994 | 23,994 | 24,050 |
| VeriEQL Calcite | 397 | 794 | 1 | 1 | 397 | 388 | 740 |
| VeriEQL literature | 64 | 128 | 34 | 8 | 38 | 61 | 118 |
| VeriEQL combined | 24,455 | 48,910 | 87 | 61 | 24,429 | 24,443 | 24,908 |

The combined row is the union of the three VeriEQL rows, not another dataset to add. Global SQL counts identify strings only; context-sensitive counts are in `schema_ic_batches.csv`. Ordered/unordered pair unique counts happen to be equal in every dataset here. Exact duplicates remain in denominators.

ParSEval has 11 explicit dbids and 11 distinct complete DDL objects. All 11 have 64–191 pair records. ICs are embedded in the full DDL, so an IC-only count is unavailable without parsing; it is null, not “one IC.” The source pins commit `88cfe245bcf249a5b0df561a6b09c116ff2a2896`. There are 1,526 unique gold-field strings and 1,527 predicted strings: 8 repeated gold strings contribute 8 excess gold slots, and 7 repeated predicted strings contribute 7 excess predicted slots. Across both sides, 174 repeated distinct strings contribute 177 excess slots. These are literal repetitions, not independent versions or verified equivalent queries.

VeriEQL has no explicit dbid field. The combined sources contain 85 schema objects, 57 constraint objects, and 87 complete schema+constraint contexts. LeetCode alone has 51 schemas, 51 constraint objects and 52 joint contexts: schema identity alone is insufficient. All its contexts have 38–2,011 pairs. Its 56 `file` metadata values are problem-source keys. There are exactly 56 distinct left SQL strings and 23,994 distinct right SQL strings. Repetition largely reflects multiple candidate pairs sharing a left query, not 47,988 independent workload queries. Literature has 63 `name` values across 64 records; no production-version interpretation is justified. Calcite's per-case `benchmark` values are not treated as inferred version families.

The legacy source copies independently recount 496 questions under each A/B/C condition (T1=304, T2=128, T3=64), hence 1,488 generated-candidate rows over the same 496 questions. They contain 1,108 distinct candidate SQL strings, 496 distinct reference SQL strings, and 1,109 distinct ordered reference/candidate pairs. That last number can exceed 1,108 because a candidate string may be paired with different references. Pairings were established by exact question+task agreement in source order. The common frozen prompt is traceable; complete production schema/IC, authoritative gold lineage, independently evolved business versions, and production snapshot identity remain unknown. Legacy counts therefore reside in `legacy_prompt_batches.csv`; full production context counts are null. A/B/C conditions must not be relabeled as independent business-version batches.

Two cheap lexical overlap descriptions are included: SQL keyword-set signatures and literal-masked strings. ParSEval has 128 keyword-set signatures and 2,762 literal-masked strings; combined VeriEQL has 604 and 24,875. They are **not** AST patterns, reusable subgraphs, semantic overlap, or evidence of amortization. Regex matching can include words/numbers in comments or quoted identifiers. Their only use is a conservative pointer for a future explicitly authorized structural audit.

## Files and reproducibility

- `inventory.py`: standard-library-only reader, hashing and counting. Run `python3 calibergraph_batch_mechanism_20261012_26/workload/inventory.py` from the workspace.
- `inventory.json`: numerical summary, field-presence inventory, source paths, SHA-256 hashes, provenance assertions, definitions and limitations.
- `dataset_summary.csv`: full numerical table including exact repeats and lexical descriptors.
- `schema_ic_batches.csv`: each exact full public schema/IC signature and its SQL counts; complete schema and IC component hashes when separately represented.
- `dbid_batches.csv`: all 11 ParSEval dbids.
- `source_family_batches.csv`: only observed LeetCode file/literature name/legacy task keys; no invented families.
- `legacy_prompt_batches.csv`: prompt-bound legacy condition batches, with unknown production fields null.
- `artifact_manifest.json`: hashes of script and deliverables; excludes itself and redirected stdout.

All JSONL rows were read without outcome-based filtering. Initial file-format/location inspection incidentally displayed some existing outcomes, but the counting script does not inspect or aggregate outcome fields. It uses only schema, constraint, SQL and source/question/task metadata. All original records, including duplicates, remain in the counts. No SQL, parser, SMT, target package, model, benchmark, witness generation or network operation was executed; no raw SQL files were copied or uploaded. Source JSONL is streamed with a 1 MiB line cap, each source file is capped at 32 MiB, and CPU is capped at 45 seconds. Retained structures are hashes/counters; JSON documents are individually size bounded. Only this new `workload/` directory was written.

Source hashes match the prior final-cut manifest for all three public VeriEQL input files and the prior legacy input manifest for consumed legacy copies. Denominator assertions confirm ParSEval=1,534 pairs and VeriEQL=24,455 pairs/48,910 slots. The legacy lineage document is hashed as provenance, not adopted as a claim of verified production truth.
