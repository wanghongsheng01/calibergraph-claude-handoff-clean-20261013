# Constraint / polynomial SQL-equivalence neighbor audit

Audit date: 2026-10-11. Read-only primary-source literature inspection; no code, SQL, SMT, old directories, or benchmark execution. This is a scoped novelty audit, not an exhaustive absence proof.

## Main finding

Do not claim first constraint-aware algebraic query equivalence, first PK/FK-preserving counterexample generation, or first polynomial-based separating database. All have substantial predecessors. I did **not** locate a primary result that proves a finite-field, quotient-ring randomized tester with a quantitative success guarantee for arbitrary PK/FK-legal databases. That remaining sentence is a search outcome, not established novelty. A new theorem must distinguish random *tuple annotations*, random *data values*, and random *canonical-family cardinalities*: these are different probability spaces.

## Strong primary neighbors

### Chirkova and Genesereth, 2009: dependency-aware bag chase

Primary: https://arxiv.org/html/0812.2195v3 ; published DOI https://doi.org/10.1145/1559795.1559829 .

Theorem 6.1: for CQ inputs whose set chase terminates, bag equivalence under embedded dependencies is equivalent to equivalence of their sound bag-chase results, retaining set-enforcing constraints. Theorem 6.2 gives the analogous bag-set reduction without remaining dependencies. Theorem 5.3 establishes uniqueness of sound chase up to the appropriate isomorphism; Theorem 5.5 gives polynomial query-size / exponential dependency-size termination under weak acyclicity. Section 4 explains why ordinary set chase is unsound for bags and uses assignment-fixing TGDs. Section 5.1 explicitly compares and generalizes prior key-based TGDs.

**Novelty impact:** “chase away constraints then apply an unconstrained equivalence method” is an old architecture. A new PIT composition needs a new representation/complexity/witness guarantee, and a proof that its chase is sound for the declared semantics. This paper concerns CQ and certain aggregate extensions, not arbitrary nested mixed SQL; its claims must not silently be extended there.

### U-semiring / UDP, Chu et al., VLDB 2018

Primary: https://www.vldb.org/pvldb/vol11/p1482-chu.pdf ; https://arxiv.org/abs/1802.02229 .

Section 4, Definition 4.1 models keys by

`[t.k = t'.k] R(t) R(t') = [t = t'] R(t)`.

This already yields idempotence `R(t)^2 = R(t)` and annihilation for distinct same-key tuples. Definition 4.4 gives an algebraic foreign-key identity. Theorem 4.2 relates the key identity to standard keys over natural-number annotations. Section 5 canonicalizes U-expressions with constraint rewrites. Theorem 5.3 is soundness; Theorems 5.4/5.5 are completeness for unconstrained UCQs under bag/set semantics, not a general constrained completeness theorem.

**Novelty impact:** PK/FK encoded as algebraic equations is explicitly prior art. Merely calling the induced equations an ideal/quotient does not establish a new method. Random assignments of arbitrary finite-field weights also need not obey key idempotence, so unrestricted annotation PIT is not automatically a legal-database tester. The last observation is this audit's inference from their identities.

### Cosette, CIDR 2017

Primary: https://www.cidrdb.org/cidr2017/papers/p51-chu-cidr17.pdf . Official code: https://github.com/uwdb/cosette .

Combines proof-assistant equivalence reasoning and constraint-solver counterexample search, returning database instances for inequivalence. The paper includes correlated queries, outer joins, and aggregates in its supported examples. It is not a universal terminating decision procedure. The official repository now points to QED as its successor.

**Novelty impact:** the combined proof/refutation product shape is established. A new tool's contribution must be its algorithm or theorem rather than returning either proof or database.

### SQLSolver, PACMMOD 2023 / SIGMOD 2024

Primary author PDF: https://www.cs.yale.edu/homes/piskac/papers/2024SIGMOD.pdf . Official code: https://github.com/SJTU-IPADS/SQLSolver .

Sections 4.1–4.3 translate U-expression unbounded sums using LIA-star, additive closure and arithmetic generators, including nested sums. Theorem 5.1 establishes soundness for bag and ordered-bag equivalence. Section 5 explicitly explains incompleteness: some translations are overapproximations and SAT does not establish an actual inequivalence witness. The official API documentation similarly warns that NEQ/UNKNOWN can occur on equivalent pairs.

**Novelty impact:** arithmetic/algebraic reasoning over unbounded multiplicities is established; solver overapproximation and concrete witness generation remain different guarantees. I did not find a finite-field fingerprint or PK/FK-specific probability theorem here.

### VeriEQL, OOPSLA 2024

Primary: https://arxiv.org/html/2403.03193v1 ; DOI https://doi.org/10.1145/3649849 .

Section 3.4 supports PK, FK, NOT NULL, CHECK, and auto increment; Section 4.3 gives their symbolic encodings. SQL semantics includes outer joins, GROUP BY/HAVING, WITH, CASE/IF, set operations and ORDER BY; bag equality is replaced by list equality when order matters. Theorems 4.5/4.6 relate symbolic encodings to concrete executions. Theorem 4.8 provides sound bounded equivalence or a concrete distinguishing database, using a bound N.

**Novelty impact:** “find a constraint-valid counterexample rather than test the benchmark database” is directly covered. Its completeness scope is bounded, so it does not supply a universal finite-field success probability or a general global completeness threshold.

### SpotIt and SpotIt+, 2026

SpotIt primary: https://arxiv.org/html/2510.26840v2 . SpotIt+ latest inspected primary: https://arxiv.org/html/2603.04334v3 . Official code: https://github.com/ai-ar-research/SpotIt-plus .

SpotIt extends bounded verification for Text-to-SQL with string/date encodings and practical evaluation strategies. SpotIt+ Section IV mines example-data constraints and validates/repairs them with an LLM before bounded counterexample generation. Its five mined categories are ranges, categorical domains, NOT NULL, functional dependencies, and column-order dependencies. The motivating example explicitly shows that an overly restrictive mined range can exclude every useful witness.

**Novelty impact:** constraint-aware realistic counterexamples and constraint extraction are occupied. Mined constraints are hypotheses about intended admissible data, not automatically consequences of the declared schema; all equivalence claims remain relative to the constraints supplied and the size bound. Neither paper inspected gives the proposed finite-field probability theorem.

### Polygon, 2025

Primary: https://arxiv.org/html/2504.06542v1 .

Section 3 uses conflict-driven search over underapproximations of SQL operators; the family collectively covers the full encoded semantics. Theorem 3.9 establishes exact input/output behavior for each underapproximation, Theorem 3.11 soundness of generated inputs, Theorem 3.12 completeness relative to those semantics. **Section 3.3 explicitly says the full semantics is itself bounded by finite table size.** Its completeness must not be quoted as unbounded SQL-equivalence completeness. It supports multi-query input synthesis/disambiguation as well as pairwise refutation.

**Novelty impact:** semantics-aware search for a discriminating database is established, with a strong modern performance baseline. I did not verify an explicit PK/FK theorem in this paper; the text search found no “foreign”. Do not infer absent support solely from that search.

### DeHaan, 2009: polynomial random separation predates modern SQL tools

Primary dissertation: https://uwspace.uwaterloo.ca/bitstreams/75481061-96ae-4f14-89b7-44c6aab72683/download .

*Equivalence of Queries with Nested Aggregation*, Appendix A.2, especially printed pp.170–171 / PDF pages 190–191 (1-based), indices 189–190 (0-based): colour-diversification inflates domain cardinalities and expresses resulting multiplicities polynomially. Theorem A.2.5 states Schwartz–Zippel. Corollary A.2.6 bounds collision among m distinct degree-at-most-k polynomials at a random positive-integer grid point by `< k m^2/(2|S|)`. Corollaries A.2.7/A.2.8 establish distinguishing diversification points/databases. The construction serves nested aggregation / relational encoding equivalence arguments.

**Novelty impact:** “randomly evaluate multiplicity polynomials to get distinguishing databases with a probability bound” has a direct early predecessor. The inspected appendix does not establish that its diversification preserves arbitrary schema PK/FKs, nor is its stated sampling over finite-field-valued tuples. That extra legality issue needs a real theorem; do not dismiss this source as mere generic PIT.

## Additional urgent neighbor, separately audited by parent

Sara Cohen, *Few Rows Tell Them Apart*, September 2026: https://arxiv.org/html/2609.09978v1 . Canonical-family multiplicity polynomials, characteristic monomial, Combinatorial Nullstellensatz; Theorems 13/15 address keys and acyclic FKs subject to key-anchorability. This already blocks broad claims of first polynomial-based legal witness or first finite threshold under PK/FK. Parent is examining the exact restrictions and residual realizability gap.

## Safe remaining claim / proof obligations

The available evidence leaves a narrower question: a computationally useful, constraint-preserving random family with a quantified **semantic** distinguishing probability on a strictly specified fragment, beyond the canonical-family and bounded-SMT results above. Required pieces are (i) every sample is legal, (ii) every inequivalent pair has a nonzero residual on the family, (iii) the degree/support/density bound is not destroyed by equality, DISTINCT or constraints, and (iv) finite-field separation lifts to natural-number SQL multiplicities without modular cancellation. A ring identity alone proves none of these. Containment also cannot be replaced by equality PIT, because multiplicity inequality needs an order absent from a finite field.

No claim of exhaustive negative novelty is warranted: web keyword searches returned noisy results and did not settle the complete quotient-ring literature.
