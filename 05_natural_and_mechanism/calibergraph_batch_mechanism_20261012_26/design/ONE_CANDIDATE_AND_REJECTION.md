# Author design: one simultaneous-witness candidate, rejected

Date: 2026-10-12. Role: mechanism author, not independent reviewer.

**Decision: REJECT this candidate as a new scientific method.** A safe, implementable cross-query construction exists on a narrow certified region, but its useful step is elementary polynomial nonvanishing. A legal-grid random baseline obtains the same simultaneous coverage guarantee, and Polygon already accepts several queries with arbitrary conditions on their outputs. No current evidence isolates a new mechanism from these controls. This is not a claim that every future batch-audit method is impossible. No second candidate is proposed here.

No new SQL, solver, benchmark, model, training, or manuscript operation was performed. This directory contains design reasoning only. Existing exposed evidence retains its old status.

## Initial design statement and changes in judgment

The initial question was whether one *generative evidence object* could discharge several different audit obligations, rather than cache the result of an already solved obligation. The sole candidate examined is a certified legal relational region together with exact polynomial output differences. Instead of independently asking a solver for each counterexample, it would construct one assignment avoiding all relevant polynomial zeros.

Two subsequent observations defeat a positive proposal at this point:

1. The literature agent reports Polygon's explicit multi-query, arbitrary-output-condition interface. Thus simultaneous witness synthesis is already expressible by the direct baseline. The only prospective difference is how the joint goal is solved inside a certified region.
2. The algebra below supplies an equally strong guarantee to elementary random sampling on that same legal region. Choosing a large legal grid and avoiding polynomial zeros does not establish a new SQL or verification mechanism. Existing aggregate ordered-identity results and Few Rows' multiplicity polynomials make this an especially exposed prior-art boundary.

The existing cost inventory also rules out claiming a large gain merely by amortizing schema construction and encoding. These observations narrow and reject the original candidate; they do not motivate a second renamed mechanism.

## The exact audit problem

A batch contains M requested obligations i with original SQL pair (q_i, r_i). A shared context is not just a database name. It contains complete schema S with source type spellings, complete declared contract C, bound semantics N, dialect and engine semantics delta, and the frontend/encoding/adapter identities on which symbolic reasoning depends. Let V_K(D) mean that a concrete database belongs to this exact context K. Let Delta_i(D) be the declared original-query output mismatch, using the requested bag/list/scalar semantics.

The pairwise bounded problem is

    exists D: V_K(D) and Delta_i(D).

A positive audit decision is a concrete legal D with a checked mismatch. A negative result excludes a mismatch only over its explicitly covered domain, conditional on exact query/contract encoding. Inconsistent C must retain its own result; it is not a successful audit of query equivalence.

The candidate would change the optimization objective to constructing a *single* D witnessing a set J of obligations:

    exists D: V_K(D) and AND_{i in J} Delta_i(D).

There is no guarantee that this joint goal is satisfiable even when every individual goal is satisfiable. This conjunction is an existing Polygon-expressible objective, not a novelty claim. Choosing J by weights, solving a MaxSMT objective, or selecting databases by a coverage matrix would be ordinary maximum coverage/set cover machinery and is excluded as a proposed contribution.

## The one candidate, fully specified

The evidence object would be a tuple R = (T, X, pi_legal, {pi_i, P_i}).

* T maps a vector x of integer parameters to a complete concrete database. T fixes row-occurrence identities and counts, physical storage tags, NULL flags, and every nonvarying cell. It may copy a parameter into several cells to retain a required equality. It does not deduplicate stored rows or discard unused tables.
* X is a finite Cartesian grid S_1 x ... x S_d. The parameter sets are explicit and nonempty. Integer input ranges and all relevant engine intermediate-overflow limits must hold throughout the grid. The minimal tractable version admits only exact integer arithmetic with a supported, certified scalar fragment. Rational arithmetic is a mathematical variant, not automatic SQLite support.
* pi_legal proves for **every** x in X that T(x) satisfies the entire original C and the declared bound and type semantics. It also proves that the required query branch decisions are constant on X: tuple liveness, NULL cases, filter/join truth, and any admitted grouping/equality distinctions. This is a universal statement, not merely a successful check of one anchor database.
* pi_i derives each selected scalar query output from the original admitted AST on T(x). For two non-NULL scalar aggregate outputs it derives the exact polynomial P_i(x) = q_i(T(x)) - r_i(T(x)). A fixed NULL mismatch can be represented by constant P_i=1. Two always-NULL outputs provide no mismatch residual. COUNT gives a constant after all contributor choices are fixed. Each row occurrence contributes separately, so bag multiplicities are retained.
* Exact sparse polynomial normalization may identify P_i identically zero. This means equality **on this region only**, not global bounded or unbounded equivalence. A circuit that would require uncontrolled expansion is refused or handled by the baseline; there is no assumed general efficient deterministic polynomial-identity oracle.

General SQL result bags do not automatically reduce to one scalar subtraction. A fixed group/output correspondence and exact NULL/multiplicity semantics would need an additional proof. The minimal candidate therefore does not advertise support for arbitrary GROUP BY, DISTINCT, outer joins, LIMIT, collations, floating aggregates, division, UDFs, or mixed-type coercions. A region with frozen noninteger cells can be considered only if all affected primitive semantics and full-C legality are certified; the ability to retain a mixed-type database as bytes is not a theorem for its expressions.

### How the region would be obtained

An implementable restricted front end can start from an already legal symbolic skeleton, tie parameter cells required to be equal, and propagate interval bounds through admitted comparisons. It emits elementary interval/equality derivations for all primitive contract and query-branch predicates. It must reject non-Cartesian dependencies it cannot certify. An alternative universal SMT check has the obligation

    UNSAT(x in X and NOT(legal_and_branch_conditions(T(x)))).

That check is charged to the candidate and is not presumed cheaper than the original task. Existing Polygon under-approximation choices are potential inputs to this region construction, but a feasible choice assignment alone does not prove that every point in a Cartesian box is legal. A singleton anchor always exists after a successful witness solve; it supplies essentially no new cross-query search power.

This is a concrete implementation boundary, not an unimplemented assertion that arbitrary full C can be generalized into a useful box.

### Deterministic root avoidance

Let J contain only obligations with certified nonzero P_i over the rational polynomial ring. For each coordinate j define

    D_j = sum_{i in J} degree_{x_j}(P_i).

If each |S_j| > D_j, one assignment x* in X makes every P_i(x*) nonzero. A simple constructive procedure is:

    residuals := exactly normalized nonzero P_i
    for coordinate j:
        scan values a in S_j
        specialize every residual at x_j = a
        choose the first a for which every specialized polynomial is nonzero
        retain those specialized residuals
    materialize D := T(x*)
    independently check complete original C and engine domain
    execute each distinct original query once on D, memoizing only identical queries
    attach a mismatch check to each requested pair

No product polynomial need be expanded. With explicit sparse residuals this is implementable by integer coefficient arithmetic, substitution and zero checking. Bit growth, expression size, branch certification, and all failed attempts count toward cost.

### Why it is safe, and why this is not a new theorem

For a nonzero polynomial P, at most degree_{x_j}(P) constants a can make P restricted to x_j=a identically zero in the remaining variables. To see this, take any nonzero coefficient polynomial in x_j after collecting the other variables' monomials; every bad a is one of its roots. The union of bad constants over the current residuals has size at most D_j. Therefore one scanned value preserves nonzeroness of every residual. Induction leaves nonzero constants at the final step. Universal legality of T(X) and exact residual semantics then give one legal database distinguishing every selected pair.

This is an elementary polynomial-grid argument. It is neither a new complexity theorem nor a SQL completeness theorem. The region and residual compiler have most of the SQL proof burden.

If grids all have size L and D_total=sum_i total_degree(P_i), ordinary independent uniform legal-grid sampling has

    Pr(any selected P_i(x)=0) <= D_total/L.

Thus L >= 2 D_total gives simultaneous success probability at least one half per draw, with expected at most two draws before all selected residuals are nonzero. Candidate outputs are still checked exactly, so random generation creates no false NEQ verdict. Failure to find a point stays unresolved. The candidate's deterministic guarantee could matter under a stated deterministic requirement, but no such workload requirement or practical advantage is established here. A generic hitting-set or polynomial-identity-testing result is not a new batch SQL mechanism.

## SAT/UNSAT asymmetry and context changes

| Evidence | Safe transfer | Unsafe shortcut |
|---|---|---|
| Concrete SAT witness D | For every new obligation, validate D against the new complete context and evaluate the new original queries. A proved implication C_old => C_new can discharge legality for a weakened contract when other semantics agree. | Treating a witness for one query pair as a witness for another, or assuming a stronger C still accepts it. |
| Certified region T(X) | Transfer legality to weaker C only with a checked implication and unchanged semantics. Under stronger C, prove all T(X) satisfies the new clauses or certify a new subregion and recheck grid capacity. | Keeping the box because its anchor point satisfies the new clauses. |
| Region P_i = 0 | Equality throughout that exact region under the same original-query semantics. | Returning bounded EQ without proving that certified regions cover all legal databases. |
| Global bounded UNSAT for old pair | Transfer only if every new valid database maps into the old domain and new mismatch implies old mismatch under a checked map. For identical query semantics, a genuinely smaller domain suffices. | Transferring to a different pair using a hash similarity, transferring to a weaker C, or increasing the bound. |
| At-most-row bound | A checked witness remains admissible at a larger cap; UNSAT transfers toward a smaller cap, given identical semantics. | Applying these monotonicities to exact-row domains. |
| Exact-row bound | An unchanged complete database retains its original exact vector. Different vectors require an explicit embedding and semantic proof. | Treating exactly N as including all smaller databases, or padding rows while ignoring C/aggregates. |

For a new contract stronger than C_old, a concrete old witness may remain valid after checking it, while a prior bounded UNSAT result for the same pair can transfer through domain inclusion. For a weaker contract the directions reverse: old witnesses remain legal if weakening is proved, while old UNSAT generally does not transfer. This asymmetry is part of every baseline too.

Under-approximation failure, timeout, unsupported syntax, failed legality certification, unavailable domain proof, and unknown remain unresolved/refused. None is a negative theorem. Query-specific UNSAT cores may be transported with their assumption/proof dependencies by established proof-caching methods; this candidate does not add an UNSAT mechanism.

## Complete reuse-validity rule and invalidation list

The reusable object is valid only while its checked premises remain true. Operationally, reject reuse by default after a dependency change unless a checked transport certificate establishes the same premises. Required dependencies include:

1. Original SQL bytes for every covered query, successful parse provenance, parser version/configuration, AST and name resolution, parameter bindings, and every transformation/adapter version. AST equality alone is insufficient because the prior project has demonstrated distinct original SQL collapsing to the same normalized representation.
2. The complete original schema, table/column identity map, source type spellings, actual storage-class rules, nullability, collation, affinity/coercion, engine version/configuration, arithmetic/overflow behavior, time zone and deterministic-function assumptions where relevant.
3. Every original C clause, including clauses on tables/columns unused by a selected query, and the C semantics. A NULL-failing custom conjunction is not interchangeable with SQL CHECK acceptance. A bridge under old C does not automatically certify modified C.
4. Exact versus at-most bound mode, complete per-table vector, liveness conventions, symbolic cell universe and its map to physical tuple occurrences. No hidden removal, deduplication, extra row, or changed FK universe.
5. The complete T, all parameter domains, all frozen cell values/tags/NULL flags, equality ties, and every primitive branch/legality certificate. Resizing or narrowing a grid requires checking the required cardinalities; widening requires legality/branch recertification.
6. Each original-output observation mode: bag, set, ordered list, scalar row presence, NULL equality, group matching, and duplicate handling. A one-row scalar argument does not authorize set equality for a general query.
7. Exact residual derivation, symbol namespace/definition map, canonicalization arithmetic and proof checker versions. All auxiliary definitions must remain total, acyclic and query scoped. A digest authenticates identity, not semantics.
8. The provenance and verification state of stored artifacts. Incomplete, interrupted, monitored, corrupted or only partially validated records cannot become strict results by cache presence. A changed budget does not falsify a mathematical certificate, but it does invalidate an unqualified performance comparison and may make its verification incomplete.

These rules are dependency based: an irrelevant byte change can be accepted only after its semantic irrelevance is certified. The list is not permission to silently ignore an unlisted runtime dependency. Concrete witnesses are more portable than proofs: after a frontend or engine change they can be rerun, but they then acquire a new validation record rather than inheriting the old one.

## Strong matched baseline, with the same information

The required baseline receives the whole batch in advance, all original SQL, full S/C/types/N, the same accepted input fragment and context semantics, the same query graph and weights if any, the same available old witnesses, and the same resource envelope. Give it all of the following:

* A persistent worker, exact source/parse cache, hash-consed shared encodings, and query-output memoization by complete identity.
* Incremental SMT with a shared legal base and per-query assumptions; reusable learned clauses or proof records subject to complete dependency checks.
* Concrete witness replay across **all** outstanding pairs, with cost-aware stopping and coverage accounting. A witness discovered by any arm is evaluated under the same validation rules; candidate-specific witnesses are not preloaded only into its arm.
* Polygon's multi-query output condition for the same joint target; no artificially pairwise-only Polygon control.
* Query-aware test-suite generation/distillation or its faithful admitted analogue, with coverage selection if used.
* Most decisively, the same certified region and residuals in an isolation control, followed by uniform legal-grid generation and exact replay. In the end-to-end control, grant the same region-construction information/opportunities and charge its cost symmetrically; do not pretend the candidate's computed region is free.

The isolation control prevents attributing shared-region preprocessing to deterministic root avoidance. If the benefit comes entirely from extracting a useful legal region, a *new* region-synthesis mechanism and comparison against existing under-approximation/predicate abstraction would be needed. That is not supplied here and is not a second candidate hidden in this proposal.

## Economic headroom and lower bounds

The completed static workload inventory establishes public benchmark batching: ParSEval has 1,534 pairs in 11 complete supplied DDL contexts, all multi-record; VeriEQL has 24,455 pairs in 87 complete schema-plus-IC contexts, with 61 multi-record contexts containing 24,429 pairs. This is a real opportunity to test *batch economics*, not evidence that this candidate succeeds. LeetCode's 23,994 pairs contain only 56 distinct left SQL strings, making exact left-query encoding/output reuse a mandatory baseline. Context identity must include complete schema/IC and source/version lineage; a random pair split would leak the repeated source queries and shared contexts. The public and legacy inventories are development exposure, not a new held-out test. Independent production business-version lineage remains unverified; the legacy A/B/C rows are conditions on the same questions, not three independent evolving workloads. See `workload/README.md`, `inventory.json`, and `schema_ic_batches.csv`.

The root's saved eight-slot inventory (four previously exposed pairs, two modes, bounds at most one in the natural adapters) reports worker wall sum 4.860539542 s. Imports are 1.258085125 s (25.8837%); parse is 1.605593832 s (33.0332%); direct schema/C construction is 0.015804332 s (0.3252%); encoding is 0.060268170 s (1.2399%); search including solver is 1.130921416 s (23.2674%); decode plus replay is 0.024500836 s (0.5041%). Solver-call time is nested inside search and must not be added again.

Only 0.076072502 s, or 1.5651% of these recorded slots, lies in the explicit schema/C-plus-encoding segments. This is a retrospective timing partition, **not** a causal Amdahl bound for future batches; constraint-solving cost also occurs in search. Startup and parsing already belong to the strong engineering baseline. These eight slots do not measure reuse, region availability, cross-query witness coverage, or post-cache solve costs.

The stronger precise-mode subset is an additional warning against a weak control: its four recorded slots total approximately 1.765915 s wall, with approximately 0.038520 s solver time (2.1813%) and 1.9292% in schema/C construction plus encoding. The UA subset's much larger solver share cannot be adopted as an unavoidable baseline cost. These retrospective four-slot numbers remain exposed, small-bound diagnostics, not a population estimate or a batch speedup ceiling.

Let s_i be the *residual* cost of obligation i after persistent-worker, exact-cache, incremental-solver and replay controls. Let H be region discovery and certification cost, A polynomial extraction/normalization cost, G witness construction cost, V validation cost, and F additional fallback cost caused by failed region attempts. A necessary break-even condition is

    sum_{newly closed i} s_i > H + A + G + V + F.

Avoided imports and parse work cannot be counted in s_i after granting those controls. Per-query replay is not erased: for K distinct original queries on one D, query-output memoization can reduce execution to K query evaluations, followed by at least M decision-record checks/output work. Both arms get this reuse. No generic positive CPU lower bound for an individual solver task can be inferred from syntax or an old process wall time.

There is also a coverage obstruction. With one integer x constrained to {0,1}, mismatch polynomials P_1=x and P_2=x-1 are individually satisfiable but never simultaneously nonzero. Pairwise distinct nonempty witness sets can similarly be disjoint, forcing one witness per obligation. Sharing S and C alone therefore yields no worst-case batch compression. In the proposed algorithm, required grid widths grow with the sum of residual degrees and can exceed contract/type limits as M increases.

Engineering effort is not free: even the restricted route needs a region parameterizer, a full-C/branch certificate checker, exact polynomial extraction with a size cap, one generation routine, and complete replay/dependency integration. These are at least five substantive components. No person-day estimate or expected speedup is justified by the current evidence. Implementing the generator alone is cheap; proving and finding a useful region is the bottleneck.

## Minimal falsifiable predictions and hard kills

No experiment is authorized or launched by this document. If a future decision reopens this exact candidate, freeze at most these predictions before any new execution:

1. After exact duplicates and all old-witness replay are removed, natural shared-context batches contain multi-pair regions with certified grid capacity. Report the full input denominator, admitted obligations, distinct pairs/queries, and covered pairs per newly constructed witness. Shared database names or repeated modes are not independent batches.
2. Total saved residual cost exceeds H+A+G+V+F on the declared batch metric. Count full C checks, failed regions, normal-form expansion, fallback and original SQL replay. Report process-startup savings separately.
3. Any claimed *root-avoidance* benefit remains over the same-region random-generation control and Polygon's joint condition, with the same fixed budget and validation. A deterministic preference without demonstrated cost/coverage significance is insufficient.

Kill this candidate immediately if any of the following holds:

* Region/residual construction is already an existing admissible prior method and root avoidance is the only added step.
* Legal-grid random sampling matches the useful coverage/cost, so the elementary genericity argument explains the gain.
* A generic joint Polygon goal, test-suite distillation, or MaxSMT/coverage policy explains the gain.
* Exact caching, incremental SMT and old-witness replay exhaust the apparent improvement.
* Only singleton or one-obligation regions are admitted; strict full-C/type handling removes the alleged batch advantage; or region finding costs at least the saved work.
* A success requires omitting C, changing bag/NULL/type semantics, silently increasing bounds/budget, using unsupported query normalization, or interpreting region equality as global EQ.

The present author judgment rejects a novel-mechanism claim because the only specified new solving step reduces to elementary polynomial nonvanishing and its basic random control has the same coverage bound. This is not an empirical statement that the random control has been run, nor a claim that one prior paper already implements the exact full-C region compiler. A useful new region compiler has not been supplied here. Reopening requires a specific new construction or a sharply defined deterministic requirement with economic significance, not a new method name or a larger synthetic example. Independent review may challenge this judgment, but no implementation or new experiment is warranted merely to decorate the same mechanism.

## Source and evidence anchors

* Existing full-context, scalar, NULL/bag and exact-row scope: `calibergraph_candidate_dke_20261012_24/manuscript/main.tex`, lines 59–83, 109–113, 194–211; IC bridge: `manuscript/contract_bridge_v5.tex`, lines 3–15.
* Existing negative decision: `calibergraph_candidate_dke_20261012_24/GO_NO_GO.zh.md`. Selector 22 versus flat 23 strict outcomes, no median advantage, cheap-AND explanation, and public eligibility boundary remain unchanged.
* Saved costs: `calibergraph_batch_mechanism_20261012_26/SAVED_COST_INVENTORY.json`. The author read the derived inventory; no new timings were collected.
* Polygon, PLDI 2025, [primary paper](https://arxiv.org/abs/2504.06542), [official venue record](https://pldi25.sigplan.org/details/pldi-2025-papers/54/Polygon-Symbolic-Reasoning-for-SQL-using-Conflict-Driven-Under-Approximation-Search). Multi-query output-objective capability was communicated by the current prior-audit agent; its detailed source audit should be read alongside this note.
* Cohen, Nutt, Sagiv, *Equivalences Among Aggregate Queries with Negation*, [author paper](https://arxiv.org/abs/cs/0210028), especially ordered identities and bounded equivalence. Local audited source analysis is `calibergraph_value_abstraction_review_20261012_21/literature_formal/formal_prior_audit.md`. Do not extend its original model to arbitrary SQL/NULL/SQLite coercions.
* Cohen, *Few Rows Tell Them Apart*, [2026 preprint](https://arxiv.org/abs/2609.09978), multiplicity-polynomial and comparison-region constructions. Locally inspected text includes polynomial differences and grid nonvanishing around lines 1870–2175 and 4890–4935; `literature_sql/NEAREST_WORK.md` preserves the scope limits. It is a PREPRINT here; no implementation claim is made.
* The earlier finite-value direction already found certified abstraction and ordering-region threats in Cosette, Polygon and other systems. `calibergraph_value_abstraction_review_20261012_21/RESULT.zh.md` and `literature_sql/NEAREST_WORK.md` are supporting context, not evidence that all possible batch designs are ruled out.

This author record is a formal design/rejection argument. It does not establish literature completeness, prove a general SQL compiler correct, report natural-batch gains, or replace the independent nonauthor challenge.
