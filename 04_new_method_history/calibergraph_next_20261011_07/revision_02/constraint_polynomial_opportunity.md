# Round 07: constraint-preserving polynomial witnesses — reviewed wording revision 02

Date: 2026-10-11. Decision: **NULL / HOLD at theory gate**, not a method promotion. Scope: primary literature and hand proofs only. No benchmark, test, reserve, old project directory, parser, SQL engine, SMT solver, scientific program, GPU or model API was accessed or executed. The accompanying SQL is a materialized input artifact with manually derived answers, not an execution receipt.

The meaningful open step is a **separating family of realizable equality structures outside key-anchorability**, with a proved search cost. An unconstrained polynomial identity, an ideal of PK/FK equations, a fresh-key constructor, and a randomized grid do not establish that step. None of the two hypotheses below has passed it.

## 1. Primary-paper scope, without strengthening its claims

[Few Rows Tell Them Apart, arXiv v1, 9 Sep 2026](https://arxiv.org/html/2609.09978v1) is a preprint. Databases are sets; combined queries count selected variable assignments. Satisfiability and set-equivalence are standing assumptions. Theorem 7: total witness size ≤ `2^w max(|Q|,|Q'|)`; per relation p, ≤ `2^w_p max(sj(Q,p),sj(Q',p))`. Theorem 13 replaces w by key-width after key-reduction/chase, requiring key-anchorability. Theorem 15 additionally permits acyclic FKs and uses chased query sizes. These are not arbitrary-PK/FK results. Parameters in `{1,2}` mean **domain cardinalities**, not two physical rows. Theorem 18, over dense rational order, requires every position-group to be directed, retained or isolated after its boundary-free strictification. Theorem 23 requires all comparisons pinned and comparison-free bodies key-anchorable. §7 leaves nonanchorable keys, remaining comparison cases and tightness open. NULL and arbitrary stored bags are outside the theorem.

Operational interpretation: use the precise theorem predicates as a scope classifier, never interpret failure of classification as equivalence or an implementation defect. A finite witness bound is also not a fast witness-search theorem.

Source-audit caution derived independently: when schema size is variable, FK chase cost cannot be bounded merely by reference depth. A DAG with relations `R_i(k,l,r)`, key `k`, and two FKs `l,r -> R_(i+1).k` produces `2^i` distinct fresh-key chase atoms at depth i from one root under the ordinary fresh-witness chase. This challenges the unqualified depth-only sentence next to Theorem 15, not the entire witness theorem. Treat schema as fixed, or account for paths/branching and prove a compressed construction. In this example a single reused child can satisfy some concrete instances; that does not make the fresh symbolic chase small.

## 2. Exact target fragment C, and what is outside it

Fix a finite schema Σ. Every table has a declared, enforced, possibly composite PK; all columns are NOT NULL; every FK references a full PK; the relation-level FK graph is acyclic. Domains are unbounded opaque equality domains, with finitely many distinct named constants. Every table is therefore set-valued. Joins and result projection retain SQL bag multiplicity.

`C_Σ` consists of **all** safe combined conjunctive queries `(H <- A, M)`: A is any finite conjunction of relational atoms and equality-to-variable/constant conditions; H is the returned tuple, M any chosen subset of nonhead variables, and all remaining variables are existential. No key-anchorability restriction. Its SQL normal form is an outer bag projection of `SELECT DISTINCT H,M FROM ... WHERE conjunction`; existential variables are projected away inside that DISTINCT. Ordinary positive EXISTS can be flattened into the body. Constant Boolean heads are permitted. Grouped COUNT over the output may expose multiplicities but is not an arbitrary aggregate language.

Excluded: NULL, base duplicate rows, UNION/EXCEPT, negation/NOT EXISTS, outer join, ORDER/LIMIT, arithmetic, string LIKE, ordered comparisons, HAVING, SUM/AVG, and arbitrary nested aggregation. SQL CHAR padding/collation is not field arithmetic: a real frontend would need a specified injective encoding into a binary-collated domain, adequate finite capacity and exact engine semantics. A theorem over opaque values does not silently cover fixed-width integers, floating point, SQL collation or overflow.

`C_Σ` is a complete syntactically specified target, not a selection of favorable cases. The non-key-anchorable portion is exactly where this research attempt has no general theorem. Admitting nullable columns and `IS NULL`, `=`, `<>` gives a different fragment `C_NULL`; no claim for that extension is made here.

## 3. Hand-derived failures of the obvious transfers

### A. Large-domain IID sampling has the wrong probability

Table `P(k PK, v NOT NULL)`. Compare `SELECT DISTINCT v FROM P` with `SELECT v FROM P`. For two rows with distinct keys, let v-values be independent uniform elements of a q-element domain. The queries differ exactly when the two values collide, so distinguishing probability is **1/q**, not `1-O(1/q)`.

The concrete legal instance `(1,0),(2,0)` gives multiplicities 1 versus 2 for value 0. This calculation concerns random **data values**. It does not contradict Schwartz–Zippel, whose degree/nonzero-polynomial hypotheses have not been supplied for this probability space. When q is a prime power and values lie in F_q, encoding equality by `1-(a-b)^(q-1)` gives degree q−1. Schwartz–Zippel then provides only the weak success bound `1/q`, not a near-one `1-O(1/q)` guarantee. Declaring an injective random data encoding removes the useful collision altogether.

### B. A legal witness outside the paper's anchoring scope exists, but its repair is elementary

Schema: `Customer(cid PK)`, `Orders(oid PK, cid NOT NULL FK -> Customer.cid)`. Let A be `Customer(c), Orders(o,c)`. Compare a constant-head query counting distinct c with the same query deduplicating the constant head. The former has M={c}; c occurs off-key in Orders, so A's statically anchored counted-variable set is empty. The canonical rigid construction varies c while keeping existential o fixed and violates `Orders.oid` uniqueness.

Actual legal witness: `Customer={(1),(2)}`, `Orders={(11,1),(22,2)}`. First answer: `[1,1]`; second: `[1]`. Allowing o to depend on c repairs this case. Few Rows §4, “The residual open case,” already explicitly identifies counting customers who placed orders and the need for set/existential variables to depend on counted values; neither this gap nor this local repair direction is a new discovery here. It **does not prove** that these Skolem-style choices preserve a separating polynomial for all `C_Σ` pairs. Creating a different parent for every child is also unsound as a general recipe: for `COUNT(DISTINCT Orders.cid)` versus `COUNT(*)`, two children of one parent separate, while giving each child a fresh parent erases that difference.

### C. Field evaluation and legal row indicators are different objects

The combined-query cores `SELECT 1 FROM R` and `SELECT 1 FROM R a CROSS JOIN R b` have multiplicities n and n² for a unary PK table R of cardinality n. SQL COUNT is only an observer of these multiplicities, not an extension of C_Σ to arbitrary aggregates. Over F₂ their difference vanishes at every field point, although n=2 yields 2 versus 4 in SQL. More generally n^p−n vanishes on F_p. Avoiding this example requires degree/characteristic control; it does not solve equality-stratum sampling.

A fixed finite legal-row universe can instead use Boolean indicators x_t with `x_t²=x_t`, same-key conflict products, and FK support equations. Arbitrary field weights then are not database rows. On the Boolean cube, the nonzero degree-k polynomial `product(x_i)` is detected with probability `2^-k`; field size does not improve it. Any quotient-ring PIT proposal must establish a measure-specific density bound and an actual Boolean/database lift, not merely nonzero ideal residue. DISTINCT's zero/nonzero operation is another semantic boundary: a nonzero natural count divisible by p becomes field zero.

## 4. Two hypotheses examined, neither retained as a new mechanism

### H1 — nonanchorable legal polynomial atlas

Precise missing proposition: for every pair in `C_Σ`, compute finitely many templates `T_j(z)` such that (i) every positive-integer parameter vector materializes a legal database; (ii) each output multiplicity difference is an explicitly bounded-degree integer polynomial on a template; (iii) inequivalence implies at least one of these polynomials is nonzero; (iv) template count, construction, coefficients, row counts and witness reconstruction have computable bounds in the input sizes. These conditions alone do not define a nontrivial mechanism: if a fragment already has a computable global row bound, constant templates enumerating its legal finite types satisfy (i–iv) with degree zero. A reopening must specify a strict nonanchorable fragment and either prove a new small-model result there or prove an explicit template/search complexity bound better than that bounded enumeration, counting construction and reconstruction. No such result is supplied here.

The genuinely missing part is (iii) together with (i): the existential key values must vary as functions of counted values without either forbidding useful collisions or introducing additional satisfying assignments that cancel separation. Standard chase followed by PIT proves neither. Replacing all function values by fresh tagged keys can change the equality type. Reusing every function value can violate PK or suppress multiplicity. A piecewise atlas is plausible vocabulary, not a proof.

Novelty threats: [Chirkova–Genesereth 2009](https://arxiv.org/html/0812.2195v3) already gives sound-chase reductions for bag/bag-set CQ equivalence with terminating set chase; [U-semiring 2018](https://www.vldb.org/pvldb/vol11/p1482-chu.pdf) already encodes PK/FK by algebraic identities; [DeHaan 2009, Appendix A.2](https://uwspace.uwaterloo.ca/bitstreams/75481061-96ae-4f14-89b7-44c6aab72683/download) already derives probability bounds for random diversification points of multiplicity polynomials. Merely combining those components is rejected. H1 is an unsolved obligation, not an accepted opportunity.

### H2 — pair-driven equality/NULL partition compression

At a fixed total row-slot bound b with N typed cells and c constants, a database is described by row-presence bits and an equality partition of present cells/constants, plus a designated NULL class if allowed. A complete fixed type can be checked for PK/FK feasibility by scanning its classes, and assigned explicit small representatives. For opaque equality data, every DB of that type has the same answer equality/multiplicity structure. Therefore finite type enumeration is complete **at that bound**.

Crude cost is `2^b B_(N+c)` without NULL; with one distinguished NULL marker it is bounded by `2^b B_(N+c+1)` before typed/constant/PK filtering. This is just finite-model enumeration. It supplies no unknown global bound for `C_Σ`, and no improvement over existing search. Fixing equality only for selected query variables leaves existential witnesses, row identities and FK target choices unresolved: their feasibility cost must be paid too.

The possible new proposition would be a computable, pair-dependent distribution over feasible types, with guaranteed separating mass alpha and generation cost T substantially below full enumeration for a declared structural parameter. Both alpha and T must be proved, independently of q. A maximin LP whose columns already list all partitions costs the enumeration. Its separation oracle must not be hidden SMT equivalence search. Bell enumeration, standard set cover, union-find pruning, ordinary bounded-treewidth CSP dynamic programming, or weighting common mutation patterns are not a new theorem by themselves.

Own lower-bound sanity check: in `C_NULL` with one row per table and equality/disequality/IS NULL conjunctions, each realizable complete type τ has a predicate true exactly on τ. Compare that query with an always-empty query. These disjoint witness sets imply that **one query-independent distribution** over T types has worst-pair success at most `1/T`, by summing their probabilities. Even equality/disequality without NULL gives Bell-many patterns. This is not a lower bound against pair-driven algorithms: after reading the full type predicate, such an algorithm can construct that type immediately. The precise consequence is that no single query-independent distribution can guarantee a fixed positive constant uniformly as T grows. Uniform sampling over the T feasible types attains `1/T`, which is independent of value-domain size q once all those types are realizable; the argument therefore does not rule out q-independent guarantees. This type-space construction fixes one row per table and permits disequality/IS NULL, so it is not a lower bound for the equality-only C_Σ fragment either.

The trivial pair above is also not evidence for compressing arbitrary pairs. For arbitrary combined queries one must preserve projected distinct assignments as well as positive witness matches; local mutation coverage need not cover cancellations involving several differences. No sub-Bell pair-driven coverage theorem was found or proved in this round. H2 is **NULL**, unless that exact gap is closed.

## 5. Same-semantics controls and full cost ledger

Any future candidate must be compared with all applicable mechanisms below on the same declared schema and semantic fragment. IID large-domain sampling is only a failure demonstration.

| Strong control | Why it directly competes |
|---|---|
| [XData](https://arxiv.org/html/1411.6704), §§2.2–2.3, 5, 9.3 | Already generates duplicate/NULL mutation witnesses and enforces PK/FK; §2.2 uses duplicate aggregate values. Handles the motivating collision mechanisms directly. |
| Few Rows canonical corners | Complete finite family on its declared subfragment; integer domain sizes and physical rows must be costed separately. |
| Small-domain enumeration / equality-type enumeration | Obvious complete bounded baseline; includes collisions intentionally. |
| [VeriEQL](https://arxiv.org/html/2403.03193v1), [Polygon](https://arxiv.org/html/2504.06542v1), [SpotIt+](https://arxiv.org/html/2603.04334v3) | Modern semantic/SMT guided bounded generation; use declared constraints consistently and count unsupported cases. |
| Chirkova sound chase, U-semiring, SQLSolver, QED | Can close equivalent cases without random generation; do not treat their proof results as counterexample generation. |

Required cost terms: schema closure/chase size; number and construction cost of types/templates; failed realizability checks; solver calls if used; polynomial/circuit construction; coefficient bit lengths; prime selection and bad-prime probability; finite-field operations times their bit cost; SQL data loading and execution; projected-assignment enumeration; full output comparison or its sound fingerprint; witness reconstruction; and final exact constraint/output validation. For b rows and v query variables, naive assignment evaluation can already cost `b^v`; a finite polynomial description is not automatically efficiently obtainable. A materialized B-row witness alone costs Ω(B) writes. Choosing p large enough to avoid modular cancellation cannot erase these terms.

Nullable PK/FK must use exact SQL MATCH SIMPLE/FULL and NOT NULL rules; NULL is not an ordinary value equated by `=`. Nullable nonkey columns can be represented by a type marker, but each operator's three-valued semantics and DISTINCT NULL grouping must be proved separately. No nullability theorem is inherited from Few Rows or a field encoding.

## 6. Outcome and restart condition

`new_validated_mechanism = null`. The hand witnesses establish real semantic failures of naive constructions, not superiority over XData/FewRows/SMT. The next productive step is a proof or counterexample for H1(iii) on a named nonanchorable fragment, or a nontrivial pair-driven coverage theorem for H2 with explicit T and alpha. Without that, further random sampling experiments would test a heuristic combination of existing techniques rather than the proposed theoretical advance.

Supporting files: `neighbor_audit.md` (primary-source nearest-neighbor scope); `hand_witnesses.sql` and `hand_witnesses.json` (explicit legal instances and manually computed outputs). No scientific experiment is reported.


Revision provenance: the four original literature files are preserved unchanged. This revision incorporates independent review P1-01/P1-02/P2-01/P2-02/P2-03; it does not create a method or authorize experiments. Full review: `calibergraph_review_round07_20261011/`. Current revision still requires reviewer followup.
