# Round 06 official generation and original-SQL replay interface

Status: **static preparation only; execution disabled**. No official module, SQL parser, SQL engine, solver, Java, installer, test or reserve corpus was executed/read for this adaptation. Python `ast.parse` checks only source syntax. Root must independently review this code, approve its execution boundary, change `generation_common.EXECUTION_ENABLED` from `False`, and then freeze the resulting files and protocol. This document is not an execution approval.

The path is source record → unchanged complete schema/C → independent official full-C SAT check → original official parse/encode/query check → validate every submitted base/C/query assertion → lossless raw physical model → independent concrete complete-C check → same original SQL pair in an in-memory SQLite database → bag comparison. No generated database is invented from the source labels; replay only consumes an actual official SAT model. Unknown, unsupported, zero-query-check, interrupted, UNSAT and NOT_RUN slots all remain in the registered denominator.

## Code and invocation contract

- `code/official_generation_backend.py`: copied Round 03 official diagnostics; changed exact-bound labels, removed independent retry, split export cost, appended strict replay hook. Official C and SQL/encoder calls remain unchanged.
- `code/official_generation_worker.py`: one frozen slot, one exact bound and one official attempt; no CLI for arbitrary source SQL or schema.
- `code/generation_common.py`: Round 04 guard adaptation plus pinned original 21-case Round 03 development registry and runtime-lock hashes. Default execution gate is false.
- `code/generation_supervisor.py`: copied Round 04 recovery supervisor, preserving single-worker monitoring, dedicated process-group kill/reap ownership, clean thread-limited environment, nice ≥15, resource accounting, sampled RSS and conservative CPU reserves; registration changed to generation slots.
- `code/official_contract_admission.py`: unchanged Round 03 whole-schema/whole-C structural admission.
- `code/safe_sqlite_replay.py`: narrow, source-hash-pinned independent C/replay support, with explicit refusals elsewhere.

After independent review and freezing, the intended launcher is `frozen-python3.12 -B -I -S code/generation_supervisor.py --protocol FILE --freeze FILE --out NEW_DIRECT_CHILD_OF_06_RUNS`. **Do not run this command during preparation.** The supervisor must be used; its process guard is part of the contract. Direct worker execution is outside the contract.

## Registration fields

Protocol `id` is `calibergraph-06-generation-replay-v1`; execution requires exact `status: REGISTERED` and a nonempty `registered_utc`. `input` is the existing Round 03 `development_stratified.jsonl`, sha256 `ab80ebcf869015d324af3e35b9dd8352013e0037dec6922e7788f4cf366e4ffb`. Its complete 21-record order and original record hashes are checked. No public source expansion is permitted.

Current fixed source index order (zero-based) is `[6, 9, 14, 3]`, i.e. `dev03_07`, `dev03_10`, `dev03_15`, `dev03_04`. `source_case_indices` records this order. `registered_cases` must be the Cartesian list of each source index followed by exact bounds `[2,4,8]`, retaining every slot. Each entry has `id`, `kind: official`, `source_case_index`, `source_case_id`, and `exact_rows`. Exact N means **exactly N live physical rows in every original table**; it is not ≤N.

Required fixed budgets: CPU 3 s, wall 4 s, RSS 268435456 bytes, C-check 100 ms, query-check 700 ms, solver cumulative wall 2 s, timeout reserve 0.1 s, supervisor solver trigger 1.5 s, internal Z3 memory parameter 128 MiB, one Environment attempt, one active worker, nice 15, parent total CPU 60 s. Existing supervisor start/active thresholds of 50/56 s and 0.2 s report tail remain. `supervisor.prior_preparation_cpu_charge_seconds` must be a positive registered charge covering source scan and preparation; no invented measurement is allowed. All parent and reaped child CPU, including imports, checks, failed launches and probes, is charged.

`worker_paths.official` is this directory's `official_generation_worker.py`. `supervisor.python_executable` must equal the pinned interpreter used to launch the parent; `required_flags` is `["-B","-I","-S"]`. `artifacts` is `{result: results.json, events: events.jsonl, progress: progress.json}`. The freeze manifest must cover protocol, all six local Python files, interpreter, input, runtime lock, and every dependency path/hash from that runtime lock. The source runtime lock itself is not modified.

## Current replay admission

| Fixed source | Static interface policy | Reason |
|---|---|---|
| 1173 / dev03_07 | INCONCLUSIVE; no SQLite replay | DATE schema plus division and ROUND lack established decoder/dialect parity. |
| 1264 / dev03_10 | INT-only replay candidate | Exact pinned pair uses CASE, equality join, DISTINCT, NOT IN. All physical fields INT; no arithmetic, string, date, ordering or collation. |
| 1421 / dev03_15 | INT-only replay candidate, SQLite ≥3.39 | Exact pinned pair uses left/right outer joins, row equality, IFNULL and COALESCE. No arithmetic/string/date/order. SQLite version checked at runtime. |
| 1468 / dev03_04 | INCONCLUSIVE; no SQLite replay | Decimal multiplication/ROUND semantics unproven; generic VARCHAR decoder also remains uncertified. |

“Candidate” means statically prepared, not tested or known to generate a witness. Source hashes bind the entire original pair/schema/C, with no SQL rewrite. For admitted models, independent Python C checks preserve official compound PK non-NULL/uniqueness, foreign non-NULL membership, comparisons including Cartesian column pairs and literal-left operand swap, not-null and AND/OR. Any unknown full clause, missing table/field, wrong exact cardinality, non-INT schema or invalid value refuses the **whole** replay. The generated C check is independent of model evaluation but verifies the pinned *operational C*, not unverified business truth.

SQLite receives parameterized inserts of actual model integers/None, then `query_only=ON`, an authorizer restricted to read/select/functions, and a budget progress handler. Both original SQL strings are executed byte-for-byte. Results are compared as bags with exact integer/NULL values. No order-sensitive query is admitted. A raw SAT with equal replay outputs is `REPLAY_DID_NOT_CONFIRM_DIFFERENCE`, never a promoted witness. A formal query-SAT model difference plus independent full C becomes `GENERATED_WITNESS_REPLAY_CONFIRMED_EXACT_N_OPERATIONAL_C`; it establishes only this generated database under SQLite's dialect. Raw official UNSAT remains `OFFICIAL_EXACT_N_UNSAT_ONLY`.

## Costs and remaining gates

Receipts include process CPU/wall/peak RSS, runtime import, original C admission and separate C check, parser and scope encoding, comparison encoding, query solver checks, model validation, raw export, independent C, SQLite load, each unchanged query and cleanup. Parse time is removed from its containing scope-encode subtotal; nested phase totals must not be summed twice. Interrupted phase times can be censored; supervisor snapshots/actual wait4 usage remain authoritative. Zero query-solver calls set `NOT_APPLICABLE_QUERY_SOLVER_ZERO_CALLS`; all single-attempt timing has `NOT_ESTABLISHED_SINGLE_ATTEMPT` hardness status.

Remaining pre-execution work: independent static review, exact protocol/manifest registration, actual prior CPU charge, and explicit root enablement before final freezing. No unit/runtime/SQL validation was run. VARCHAR equality-only decoding is **not** implemented as a generic fallback; the exact static requirements and source evidence are in `STATIC_ADAPTATION_REPORT.md`.

## Explicit C-model sanity control amendment

The protocol must explicitly register `contract_model_sanity_control: true`; common admission rejects its absence or any value other than Boolean true. Before query parsing, the two admitted INT cases (`dev03_10`, `dev03_15`) separately export the **same** model already validated by `FULL_C_SAT_MODEL_VALIDATION`. `contract_model_sanity` records `model_origin: FULL_C_NONEMPTY_CHECK`, `scope: C_MODEL_SANITY_ONLY_NOT_QUERY_SAT`, and `query_sat_witness: false`. Its unchanged original-SQL replay is an existing C-sampling sanity control, not an innovation, method win, generation benefit or query-SAT witness. The other two cases record `NOT_ADMITTED`. A difference in this control's nested replay does not affect official query verdicts or `strict_class`; the formal query-SAT export/replay path stays separate and unchanged. Control exceptions are recorded separately; resource guards still stop the shared worker budget. Export/replay have explicit `C_MODEL_SANITY_*` CPU/wall stages and share the original 3 s CPU/4 s wall limits; there is no extra solver call or budget extension.

The supervisor now writes all **12 planned NOT_RUN slots** before any lock/registration precheck, with `planned_denominator: 12` and `registration_validated: false`. These are planned slots when registration is invalid, not falsely registered observations. Complete validation changes the flag to true. The common validator requires the exact fixed source order `[6,9,14,3]`.

SQLite's progress callback stores any guard exception and returns interruption; the execute/fetch error path re-raises the original `BudgetStop`. Unknown callback failures become `BudgetStop` with their original cause preserved. This prevents CPython's callback-to-OperationalError conversion from hiding a resource stop as an ordinary query error.
