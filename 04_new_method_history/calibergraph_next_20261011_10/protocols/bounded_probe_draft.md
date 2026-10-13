# Round 10: bounded common-body count probe — DRAFT, NOT FROZEN

Status: **STATIC IMPLEMENTATION ONLY / NOTRUN**. This document is a protocol
draft, not a completed preregistration. Independent pre-execution review and a
root-authored freeze are still required. The default execution flag is false.
No scientific program, module import, compile check, test, tiny probe, or model
enumeration was run while preparing this draft. Source hashing is metadata.

## Question and limits

For a common conjunctive body with self-joins, unit head, set relation semantics,
and distinct projected-assignment counts, examine the following structural
condition after a complete primary-key chase. With count-variable sets M and N,
there must exist independent endomorphisms alpha and beta of the chased body
such that:

```
N ⊆ cl(alpha(M))     and     M ⊆ cl(beta(N)).
```

Closure uses every chased R(a,b) as the functional dependency a → b. The first
direction is the proposed certificate for count(N) ≤ count(M); the reverse
direction supplies the other inequality. Neither map must be injective; neither
must be an automorphism. The head is empty, so there is no additional head-fixing
condition. This is a known-style sufficient-condition hypothesis under the
specified semantics; this finite probe is not its proof and necessity is not
assumed. This is not a new-method comparison or a benchmark claim.

The sole scientific outputs are a search for a **SUFFICIENCY_FALSIFIED** case
(cover says equal but a legal bounded model distinguishes) and records of
**BOUNDED_INCONCLUSIVE_CANDIDATE** cases (not covered but indistinguishable on
this complete fixed small domain). The latter are obligations for separate hand
proof or larger-domain reasoning, never counterexamples to necessity. A failure
of the sufficient-condition implementation may be a semantic, chase, cover, or
implementation defect; preserve the evidence before drawing a theorem claim.

## Fixed schema and denominators

Exactly one set-valued relation `R(k PRIMARY KEY, v)`, with both columns NOT NULL,
the same equality domain, no constants in query bodies, and no foreign keys.
Only variables `x < y < z` are used. The nine possible ordered binary atoms are
the lexical Cartesian product of these variables with themselves. Bodies are
all combinations of one, two, or three distinct atoms, ordered first by atom
count and then lexically. Original bodies are never deduplicated by chase,
isomorphism, result, cover, or signature.

- Original-body denominator: `C(9,1)+C(9,2)+C(9,3) = 129`.
- For each body, list subsets of its original active variables in cardinality
  order, with lexical order inside a cardinality and the empty set first.
  Enumerate every unordered pair of **different** subset indices in increasing
  index order. No same-subset pairs, result filtering, or selection.
- Active-variable counts 1/2/3 occur in 3/36/90 original bodies. Thus the fixed
  query-pair denominator is `3*C(2,2)+36*C(4,2)+90*C(8,2) = 2739`.
- Alternative static count by atom number: 39/612/2088 pairs for 1/2/3 atoms.
- The equality domain is `D={0,1,2}`. For key 0, then 1, then 2, choose from
  `[-1,0,1,2]`, with -1 denoting an absent row; lexical product order fixes model
  indices. This enumerates **all 4^3=64 partial functions**, including the empty
  database and all zero-to-three-row tables. Row-count strata are 1/9/27/27.
- Fixed logical pair-model denominator: `2739*64 = 175296`.

These are static combinatorial calculations, independently checked by another
agent without execution. For a chosen two-variable alphabet there are
`C(4,1)+C(4,2)+C(4,3)=14` nonempty bodies of at most three atoms; removing its
two one-variable singleton bodies leaves 12, and there are three such alphabets.
Therefore 36 bodies use exactly two variables, 3 use exactly one, and the
remaining 90 use all three. The per-atom-size cross-check follows the same
inclusion-exclusion. No generated result was used to obtain these numbers.

## Separate branches and fixed order

1. Create exclusive fresh `runs/only_attempt` under round 10. The one-shot
   `runs/attempt.lock` is created with exclusive mode and must never be deleted
   to obtain another run. Write all original body metadata, all 2739 NOTRUN pair
   slots with original signatures and SHA-256 hashes, and all 64 model slots
   **before** host-resource prechecks. This preparation is charged guard work.
2. Complete primary-key chase: repeatedly unify value variables of atoms whose
   current canonical keys coincide, until a complete pass makes no union.
   Lexically smallest representatives are deterministic. Save the original
   body, full original-to-chased map, each union, final chased atom set, scan
   count, and original pair count. Map M and N through this map and take sets.
3. Enumerate every map from the chased active-variable set to itself. Check
   every mapped atom for membership in the chased atom set, with no early
   stop. Save all accepted endomorphisms and the counts of maps/atom checks.
4. For every original query pair, inspect every accepted endomorphism in both
   cover directions; compute FD closures to a fixed point; record counts and
   the first lexical witness per direction. Mapping construction, map tests,
   closure scans, FD-edge tests, and serialization are charged, not treated as
   free hints. Alpha and beta may be different maps.
5. Independently, directly enumerate every assignment of the **original active
   variables** to D on every model. Check membership of every original atom;
   collect distinct projected tuples for all original subsets. The evaluator
   neither calls nor consumes chase, FD closure, or cover outputs. Its only
   inputs are the original body, original projections, and actual model rows.
   Empty projection counts 1 iff the body is satisfiable, otherwise 0.
6. Write both length-64 count vectors, the 64 equality bits in model order,
   cover booleans/witnesses, original signature/hash, classification, and first
   distinguishing model when any. All 64 models are evaluated even when an
   early model distinguishes. Model counts may be shared across different
   pairs of one original body; logical pair-model comparisons still account for
   every pair and model. No body-to-body scientific result caching is used.
7. After completing each body, check the relevant in-universe controls and stop
   on any failed expectation or SUFFICIENCY_FALSIFIED record. Preserve completed
   records. Unfinished pairs remain NOTRUN; truncation is never completion.

The code computes evaluator vectors before per-pair cover results for one body;
this order cannot influence which bodies, pairs, maps, or models are included.

## Controls and the pre-run schema correction

All executable controls are references to already included cases; they add no
body, pair, or model to the denominator. Their original requested semantics and
the correction below are preserved before any run.

1. **Same-key chase**: `R(x,y) ∧ R(x,z)`, M=`{y}`, N=`{y,z}`. Complete chase must
   unify y and z. Both counts must agree on every model and cover must be true.
2. **Triangle under the actual single-column PK**:
   `R(x,y) ∧ R(y,z) ∧ R(z,x)`, M=`{x}`, N=`{x,y}`. All 64 legal models must give
   equal counts and cover must be true. Under the PK, x determines y and z;
   identity is already a witness in both cover directions.
3. **Legal projection distinction**: `R(x,y)`, M=`{x}`, N=`{y}`, and the existing
   model `R={(0,0),(1,0)}`. Counts must be 2 and 1, respectively, and cover_EQ
   must be false. This tests that the evaluator can distinguish.

**CONTROL_SPEC_INVALID_REJECTED — original request retained:** the earlier
triangle request proposed `R={(0,0),(0,1),(1,0)}` with counts 2 and 3 and stated
that all tables of at most two rows were expected to agree. That three-row
relation violates `k PRIMARY KEY` because key 0 has values 0 and 1. It is not a
model of this schema and cannot be inserted into the 64-model denominator. The
2-vs-3 hand calculation is meaningful only after dropping that PK or changing
the key semantics. The root authorized this correction **before any execution**;
the universe, original case ordering, and all denominators remain unchanged.
The rejected request is a historical specification error, not a counted outcome.

**Late static control specifications within the unchanged fixed universe:**
the following are hand-review anchors, not extra executed cases or separately
selected result subsets. No claim below came from a run.

- Three rows matter: for `R(x,x) ∧ R(y,x) ∧ R(z,y)`, M=`{x}`, N=`{y}`, all legal
  tables with at most two rows give equal counts. With the legal three-row table
  `{(0,0),(1,0),(2,1)}` the counts are 1 and 2. Thus stopping the model universe
  at two rows would miss a distinction already in the fixed denominator.
- Iterated chase: `R(x,x) ∧ R(x,y) ∧ R(y,z)` first forces x=y and then x=z.
  Scanning only the original key grouping would miss the second consequence.
  A stronger pass-order anchor is lexical `R(x,z),R(y,x),R(y,y)`: the first pass
  merges x=y only after the earlier R(x,z) was visited; the second must merge
  x=z, and the third observes stability. This is a static anchor, not an added case.
- Noninjective maps: `R(x,x) ∧ R(y,y) ∧ R(z,x)`, M=`{x}`, N=`{y}`, counts the
  same self-loop set on either projection. The constant maps onto y and onto x
  give the two endomorphism witnesses even though no automorphism swaps x/y.

## Resource envelope, accounting, and stopping

Only this Darwin host is supported. Standard-library Python plus explicitly
listed read-only Darwin resource calls are used. There is no external data read,
network request, installation, database/SQL/parser, GPU, model API, subprocess
queue, worker pool, or thread pool. The supervisor forks exactly one scientific
worker and execs the pinned Python executable with `-B -E -s -S`; that worker
stays single-process and single-threaded. Both have nice at least
15. The resource supervisor is not hidden from the cost ledger.

- Aggregate nominal CPU hard budget: **2 seconds**, conservatively allocated as
  supervisor `RLIMIT_CPU=(1,1)` plus worker `RLIMIT_CPU=(1,1)`. Budgets are never
  transferred, increased, or repeated if too small. POSIX CPU limit enforcement
  has kernel accounting granularity; no exact sub-tick guarantee is claimed.
- Wall budget: **3 seconds from supervisor entry**, including freeze hash
  verification, inventories, prechecks, worker, recovery, and finalization.
  Python interpreter startup/import before that entry is outside this internal
  timer and must be included in the root's external launch accounting. Both
  parent and child have wall timers; parent has a finalization reserve and
  prioritizes terminating/reaping its exact owned child.
- Aggregate RSS ceiling: **128 MiB** for parent plus worker, sampled about every
  10 ms with Darwin `proc_pidinfo`. Shared pages are double-counted, conservatively.
  This is sampled enforcement, not an instantaneous kernel RSS hard limit;
  sub-sample peaks can escape observation. Parent RSS is measured before fork
  and doubled as a conservative initial admission check.
- Start only when 1-minute host load is **≤4** and a conservative available-memory
  proxy `(free_count + inactive_count) * page_size / hw.memsize` is **≥25%**.
  Speculative, purgeable and compressed memory are omitted. Native telemetry
  failure rejects the run; no shell or alternative sampling path is attempted.
- All source hashing, metadata generation, chase, self-map enumeration, closure,
  assignment enumeration, projection insertion, comparison, control checks,
  native monitoring, logging and finalization are charged. Per-phase CPU and
  operation counts supplement supervisor SELF and child `wait4` usage. The last
  tiny accounting write and interpreter exit remain outside its own self-report;
  the root must retain the observed outer process exit and elapsed time.
- On resource pressure, timeout, CPU signal, telemetry failure, exceptions,
  failed controls, or a possible false positive, stop without a budget increase
  or rerun. Only owned child PID / verified owned process group may be signalled.
  An unreaped child prevents PID reuse while ownership is checked.

The runtime executable's resolved path, SHA-256, version, implementation and
exact flags must be recorded by root in the freeze, and verified before use.
The same two-process design records `worker_exec_lifecycle_wall` from a
supervisor monotonic sample immediately before fork to the stored wait4 reap
sample. It includes worker interpreter startup/import, exit and polling latency;
it is **not** supervisor-startup or entire-chain wall. The worker inherits CPU
and remaining-wall limits across exec and validates the owned handoff. There is
no third Python launcher, new CPU allotment or subprocess task queue. A future
root-approved `/usr/bin/time -l` launch may supplement entire-chain observation;
its costs cannot be silently omitted or used to add a budget. It is not run now.

Freeze verification happens only after niceness, CPU limit and wall timer are
established. On the hard wall alarm, the parent terminates/reaps its owned child
and exits 124 immediately; it cannot catch the exhausted alarm and then continue
finalization. Fork/ownership and wait4/ownership updates mask SIGALRM, and the
wait4 receipt is retained before unmasking. Detected RSS overage stops bulk
recovery; peak SELF+wait4 RSS is also conservatively checked before zero exit.

Unexpected parent SIGKILL may prevent cleanup and any final receipt. The child
has its own remaining-wall timer and 1-second CPU limit. Missing receipts,
incomplete accounting, nonzero outer exit, or an exceeded outer resource budget
are failures/truncation, **never success**, even if a partial log looks complete.
The code cannot guarantee receipt finalization after an OS hard kill. Original
NOTRUN slots and immutable partial logs are the recovery evidence.

## Output and decision rules

`pair-slots-notrun.jsonl` is the immutable denominator ledger. Complete worker
rows overlay it by exact pair ID and signature hash; duplicates, unknown IDs,
malformed/torn rows, or signature mismatch invalidate successful completion.
`pair-slots-final.jsonl` retains all 2739 slots if finalization completes. An
interrupted finalization leaves the original ledger and append logs intact.
The raw body inventory retains all 129 original cases, including those merged
by chase, and all 64 models are explicitly listed.

The denominator contract is written before materialization. A kill during slot
materialization can leave an incomplete baseline; known mathematical denominators
must not be confused with all slots having reached disk. Recovery validates the
baseline count/uniqueness/hashes and reports incomplete materialization as failure.
It also checks result signature digests, count types, equality bits and class
consistency. No claim of successful recovery is made after an interrupted write.

Final classifications are only:

| cover_EQ | Some legal model differs | Classification |
|---|---|---|
| true | true | SUFFICIENCY_FALSIFIED; stop and inspect |
| false | false | BOUNDED_INCONCLUSIVE_CANDIDATE |
| true | false | COVER_EQ_BOUNDED_CONFIRMED |
| false | true | NONCOVER_BOUNDED_DISTINGUISHED |

`COMPLETE_BOUNDED_PROBE` requires every denominator, all three controls, a zero
worker exit, readable receipts, no recovery errors, terminal accounting within
the approved resource envelope, and a zero supervisor exit observed by the
external caller. Merely finding no false positives is not a necessity theorem.
No performance comparison, asymptotic conclusion, natural-corpus applicability,
or unbounded equivalence/necessity statement follows from this protocol.

## Freeze requirements still outstanding

An independent reviewer must inspect the exact source and protocol, including
native ABI definitions, resource race windows, cost boundaries, control repair,
count semantics, and recovery. Root must save the review receipt, resolve any
blockers, enable the source flag, hash the final sources, and write a matching
`protocols/freeze.json` marked `FROZEN_AFTER_INDEPENDENT_PRE_REVIEW`. The enabling
one-line change and exact frozen hashes must be covered by that review. The
draft provides no executable permission receipt and no automatic enable path.

Root has paused the execution freeze pending round 11's review of potentially
covering prior constraint/normalization theory. This is an additional scientific
gate, not a reason to execute this probe opportunistically. The disabled static
snapshot is the current deliverable even if its implementation review passes.
