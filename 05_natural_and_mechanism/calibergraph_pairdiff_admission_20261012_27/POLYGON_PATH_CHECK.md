# Scoped Polygon path check

Pinned upstream commit: `5e18237394d025dbb805cf833b4f54c321470774`. Read the original `upstream_local` files, not the serial runtime overlay. File identities and comparison to the saved source receipt are in `POLYGON_CODE_RECEIPT.json`. No Polygon import or execution occurred.

* `polygon/environment.py:182–191` parses q1 and q2 separately; `:210–217` creates a QueryEncoder for each AST and retains the two outputs; `:220` adds output non-equivalence. In this inspected path there is no paired relational difference/cancellation pass before operator encoding.
* The commented Initializer calls in environment.py do **not** mean initialization is absent: `polygon/visitors/query_encoder.py:33–36` initializes each uninitialized query, and `:73–77` handles a union similarly.
* `polygon/visitors/initializer.py:49–60` assigns a fresh union label; `:73–101` assigns fresh join/product labels; `:157–177` assigns filter/project labels. `:69–71` deliberately gives base scans their table-size label. Hence base schema sharing already exists; the gap cannot be described as “Polygon shares nothing.”
* `polygon/smt/formula.py:526–544` caches SMT serializations by label and retains learned conflicts. This is different from merging equivalent relational subgraphs across two separately parsed queries before assigning operator labels. The inspected path does not demonstrate such a merge.

This scoped absence establishes a plausible implementation location only. It neither proves global repository absence nor supplies scientific novelty or expected speedup.

Known prior remains a strong control: [Wang, Cheung and Bodik, OOPSLA 2018](https://chenglongwang.org/data/oopsla18.pdf), §4–5, uses a distinguishing output tuple's multiplicities and provenance-based space refinement. [Green, Ives and Tannen, 2011](https://www.cs.ucdavis.edu/~green/papers/tocs11_differences.pdf), §3–5, develops integer-annotated relations and difference/cancellation rewriting. No claim of a new algebraic identity, new single-tuple observation, or first cancellation is justified.

Required prospective comparison: B0 unchanged pinned Polygon; B1 Polygon strengthened with common relational DAG sharing and a single symbolic output tuple's multiplicity-difference discriminator; C B1 plus only the candidate's pre-symbolic paired difference pass. B1 is a required **unbuilt adaptation**, not an already measured official feature. Full original schema/C, exact bound semantics, bag/NULL/types, replay, process/cache state and budgets must match. The current DAG counts model structural sharing only; they do not measure the complete B1 or claim fewer SMT variables/UA labels. The natural admission gate failed, so no arm is implemented or run.
