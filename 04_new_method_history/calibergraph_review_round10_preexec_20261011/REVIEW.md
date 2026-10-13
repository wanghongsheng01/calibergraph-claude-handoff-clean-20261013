# Round 10 independent pre-execution review

Status: **HOLD — DISABLED STATIC REVIEW; NOT EXECUTION-READY**.

Reviewer: `/root/round10_independent_preexec`; resource second reader:
`/root/round10_independent_preexec/resource_static`. Both are separate from the
round-10 author. The exact final disabled source hashes are recorded below.

The mathematical implementation passed the checks described here, but the full
pre-execution gate has **not** passed: P1-R05 remains open. The root explicitly
stopped further guard engineering while round 11 assesses potentially covering
prior theory. This technical HOLD and the independent knowledge gate both
remain binding. No experiment was run; execution stays disabled.

## Scope and method

This review covers only the new round-10 `finite_core.py`, `run_probe.py`,
protocol, and associated preparation documentation. No older-round raw corpus,
results, or tests were read. No scientific program, candidate-module import,
SQL, SMT, model call, or scientific enumeration was executed. Text inspection,
permitted AST/JSON inspection, file metadata/hashing, and hand reasoning are the
only permitted audit methods. A static PASS, if issued, is not empirical
validation and does not turn the source execution lock on.

Applicable instructions were read from `/Users/loctek/.codex/AGENTS.md` and the
workspace ancestors. There is no external dataset in this synthetic task;
DataHub data access is not needed. The root owns the durable private backup gate.

## Independent semantics check

- The schema is the set relation `R(k PRIMARY KEY, v)` with NOT NULL columns and
  a common three-value equality domain. Choosing absent/0/1/2 once for each key
  enumerates precisely the 64 legal partial functions, including the empty DB.
- Nine ordered atoms give `C(9,1)+C(9,2)+C(9,3)=129` original bodies. There are
  3 bodies with one active variable, 36 with two, and 90 with three. Thus the
  different unordered projection-pair count is `3*1+36*6+90*28=2739`, giving
  175296 logical pair-model comparisons. Original bodies and projection pairs
  survive even when chase produces equal bodies or equal projection images.
- A separate hand cross-check by atom size gives 39, 612, and 2088 pairs.
  All counts in this paragraph are algebraic calculations, not run outputs.
- The chase unifies values of atoms with equal current keys, uses deterministic
  representatives, and repeats until a pass has no union. A stale grouping
  within one pass can only postpone a consequence: another pass rebuilds all
  key groups. A no-union terminal pass sees fixed representatives throughout.
- The structural branch maps each original count set through the full chase,
  takes a set of representatives, enumerates every chased-variable self-map
  (including noninjective maps), and tests all mapped atoms. Both cover
  directions iterate all accepted endomorphisms and use fixed-point FD closure.
  The two witnesses may differ.
- The evaluator receives only the original body, original projections, and
  actual model rows. It checks every assignment of the original active variables
  and inserts distinct projected tuples into sets. Empty projection is 1 iff a
  satisfying assignment exists. It consumes no chase or cover results.
- A cover-positive pair with any differing legal-model count must be
  `SUFFICIENCY_FALSIFIED`. A cover-negative pair equal on all 64 models is only
  `BOUNDED_INCONCLUSIVE_CANDIDATE`; it establishes neither unbounded equivalence
  nor a failure of necessity. No natural-data or novelty claim follows.

## Hand controls and operation-count cross-checks

1. `R(x,y),R(x,z)` forces y=z under the key. Projections {y} and {y,z} have
   equal counts, and chase maps both to the same count set.
2. In `R(x,y),R(y,z),R(z,x)`, x determines y,z. Projections {x} and {x,y}
   have equal counts on all legal databases; the identity witnesses both cover
   directions. The old proposed rows `{(0,0),(0,1),(1,0)}` violate the single
   key and are correctly recorded as `CONTROL_SPEC_INVALID_REJECTED`.
3. In `R(x,y)` on `{(0,0),(1,0)}`, projections {x}/{y} count 2/1. The only
   endomorphism is identity; y's FD closure does not contain x, so cover_EQ is
   false. This legal control is already in the fixed denominator.
4. The additional hand anchor `R(x,x),R(y,x),R(z,y)` needs three distinct
   keys to admit a non-loop y. The legal chain `{(0,0),(1,0),(2,1)}` gives
   counts 1/2 for {x}/{y}; no two-row legal DB can realize this distinction.
5. `R(x,x),R(x,y),R(y,z)` requires iterated chase: x=y then x=z. A stronger
   cross-pass anchor is lexical `R(x,z),R(y,x),R(y,y)`: the first pass merges
   x=y after the earlier R(x,z) was visited; the second must merge x=z, and
   the third observes stability. The implementation has the required loop.
6. `R(x,x),R(y,y),R(z,x)` admits the constant endomorphisms onto y and x
   as opposite cover witnesses for {x}/{y}, although an automorphism cannot
   exchange x and y while preserving z's incoming structure.

If a complete run finishes, direct evaluation has exactly
`64*(3*3+36*9+90*27)=176832` original assignments and
`64*(63+1296+6156)=480960` original-atom membership checks. These differ from
the 175296 logical pair-model comparisons. Before chase, self-map attempts are
bounded by `3*1+36*4+90*27=2577`, and mapped-atom checks by 7119; chase can only
reduce these upper bounds. These are hand-derived audit expectations, not
results or runtime predictions.

## Resource findings and repair acceptance

| ID | Priority | Final disposition | Reason / repair |
|---|---|---|---|
| R01 | P1 | RESOLVED | The hard wall handler terminates/reaps the owned child then uses `os._exit(124)`, so a caught one-shot alarm cannot resume finalization. |
| R02 | P1 | RESOLVED | An RSS excess detected after overlay reading raises immediately; a detected live aggregate RSS excess skips bulk recovery. |
| R03 | P1 | RESOLVED | Niceness, CPU limit, and wall timer are installed before freeze verification and source hashing. |
| R04 | P1 | RESOLVED | `poll_owned` and `terminate_owned` store `last_wait4` and the reap clock before unmasking SIGALRM; the receipt is not lost between reap and return. |
| R05 | P1 | **OPEN — EXECUTION BLOCKER** | Preparation and recovery do not maintain the required RSS guard across their loops. See the precise scope below. |
| R06 | P2 | RESOLVED | The parent tolerates post-exec `setpgid` PermissionError only after verifying the child's group equals its owned PID. |
| R07 | P2 | **OPEN** | `run_probe.py:695` cancels its wall timer before stdout/interpreter flushing. A blocked output flush can outlive the three-second timer. Leave the timer armed through natural process exit in a future revision. |

**R05 evidence.** The approximately 10 ms aggregate RSS loop in `supervise`
covers the active worker phase. `verify_freeze`/`file_sha256`,
`prepare_notrun_slots`, `read_result_overlay`, and the baseline serialization
loop in `finalize` have no corresponding periodic own-RSS check. A check after
the complete overlay and the final SELF-plus-wait4 peak comparison can reject
success, but do not provide timely stopping during those phases. In addition,
an RSS telemetry `RuntimeError` during monitoring takes the generic failure
path and may enter bulk `finalize`; guard failure should not launch more bulk
recovery. Fixed data dimensions do not prove an exact Python RSS bound.

The root explicitly requires RSS/CPU/wall protection throughout the work, while
load <=4 and the >=25% memory proxy are **startup admission checks** only. Merely
rewording the RSS claim to describe the gap cannot satisfy that requirement.
If round 11 later justifies an experiment, a new revision should reuse a small
cooperative own-RSS check in all preparation/recovery loops, skip bulk recovery
on sampling failure/excess, and retain final peak accounting. It needs no new
process or thread. Even then it must disclose that long native calls and
signal-masked regions can extend sampling intervals; sampled RSS is not an
instantaneous kernel hard limit. This repair is intentionally **not** implemented
or authorized by this review.

The resource second reader initially returned PASS_WITH_P2 for the earlier
snapshot, then explicitly corrected that conclusion after checking the root's
throughout-the-work RSS requirement. That earlier preliminary PASS is withdrawn
and must not be used as authorization. **HOLD is the consolidated decision.**

## Resource and receipt properties that were confirmed statically

- There is one scientific child, not a worker pool. The supervisor and worker
  each receive `RLIMIT_CPU=(1,1)`, preserving the nominal aggregate two-second
  allocation. CPU limits have kernel granularity; the final receipt separately
  checks the measured sum. Nice is at least 15. No extra Python launcher or
  new CPU allocation was added.
- The supervisor's cumulative SELF usage includes its interpreter startup CPU;
  it is not reduced by subtracting `self_usage_at_entry`. The owned child's
  wait4 usage includes its fork/exec/startup, work, and termination. Phase timers
  are supplemental and do not erase metadata, monitoring, controls, logging,
  or recovery costs. The last accounting write and interpreter exit are still
  outside that final self-report and require outer evidence.
- The new worker uses the pinned interpreter and `-B -E -s -S`, verifies the
  source/runtime freeze, inherited timer/limits/nice, parent, process group,
  handoff pipe, and exclusive worker claim. The source's `False` gate precedes
  both entry paths. The hidden continuation does not create another attempt.
- The resource second reader checked the local Darwin SDK
  `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/share/man/man2/execve.2`
  (lines 125–127 and 150–163): signal-mask behavior and inheritance of interval
  timers, resource usage/limits, and process group support the exec design.
  No candidate code or native resource function was called to test it.
- Native APIs are limited to read-only `sysctlbyname(hw.memsize)`,
  `mach_host_self`, `host_statistics64(HOST_VM_INFO64)`, and
  `proc_pidinfo(PROC_PIDTASKINFO)`, plus release of the acquired host port.
  RSS reads target only the supervisor and its owned child. No external `ps`,
  process inventory, network, installation, SQL, or model queue is present.
  ABI choices remain statically inspected, not experimentally validated.
- Signal cleanup targets the unreaped owned child and only a group verified to
  have that PID as group ID. Fork/ownership and reap/ownership changes mask
  SIGALRM. Unreaped ownership prevents PID reuse between validation and cleanup.
- Known denominators are written before slot materialization. All 2739 NOTRUN
  slots are generated and flushed before load/memory admission and any science.
  The immutable baseline is never replaced by a filtered completed-only table.
- Overlay recovery rejects duplicate/unknown IDs, malformed rows, mismatched
  signatures, incomplete count vectors, invalid counts, and inconsistent bits
  or classifications. A partial baseline is distinguished from the known
  mathematical denominator; a partial write is not declared complete.

| Failure point | Required interpretation |
|---|---|
| Before/during baseline materialization | Known denominators remain 129/2739/64/175296; full slot persistence cannot be claimed. No science has begun. |
| Load/memory admission rejects | Entire scientific denominator remains NOTRUN; the attempt is consumed. |
| Worker timeout, control failure, falsifier, or exception | Retain complete rows already written; unfinished rows remain NOTRUN or explicitly unrecovered. No retry. |
| Torn overlay/final ledger or unreadable worker receipt | Failure/truncation; original baseline and raw logs remain evidence. |
| RSS excess or unavailable telemetry | Stop science; R05 records why all recovery paths do not yet fully satisfy the immediate-stop requirement. |
| Parent hard kill or missing terminal receipt | No success, even if partial outputs look complete; finalization/cleanup cannot be guaranteed after SIGKILL. |
| Terminal budget excess or nonzero outer exit | No success regardless of an earlier success-labeled supervisor receipt. |

## Wall-clock and future launch boundary

`worker_exec_lifecycle_wall` correctly measures immediately before fork through
the stored wait4 reap clock, including worker interpreter startup/import, exit,
and polling delay. It is **not** the supervisor startup or whole-chain wall
time. The supervisor's own three-second timer starts at function entry. The
source and protocol explicitly preserve this distinction.

The root rejected adding a third Python wrapper as unnecessary complexity.
A future, separately authorized launch may use normal `/usr/bin/time -l` as
outer observation, but must specify the measurement boundary and charge its
costs without creating extra budget. Tool `wall_time_seconds` is not by itself
exact process-launch evidence. The concrete interpreter pin, enabled-source
diff, execution freeze, and outer success criteria still need review at that
time; this disabled-source review cannot pre-approve them.

An absent/torn terminal receipt, nonzero outer exit, missing wait4 cost, budget
excess, or failed guard precludes success. A complete-looking partial output is
insufficient. There is one attempt, no retry, no budget relaxation, and no
second scientific run to repair accounting.

## Static evidence and remaining gates

`STATIC_CHECKS.json` records syntax-only AST parsing and source metadata. Both
candidate files parsed; neither was imported or run. File hashes matched the
author's stopped-edit snapshot and `docs/source_sha256.txt`. The execution flag
was false, `runs/` did not exist, and `protocols/freeze.json` did not exist.

The root confirmed that the existing author snapshot is the final disabled
snapshot for this review. No later repair revision or `draft_snapshot_01`
directory was created. `SOURCE_SNAPSHOT_SHA256.txt` contains the following
author-relative paths and hashes:

| Author-relative file | SHA-256 |
|---|---|
| `code/finite_core.py` | `599bee07c1aa6e43cc4fd5656e6a5f7e32e5feb3408846d313eba01692c4afa9` |
| `code/run_probe.py` | `20ebe5e77696bbd2b8e5fbe007e13796b4ed20a1e6fcce8d728b1be63b8dce16` |
| `protocols/bounded_probe_draft.md` | `58764a18253fe65980cf5266f6143738532c0ad76abe9d1389612a28079b079e` |
| `docs/README.md` | `1ccb8e0959488d137868b37d8c9dcca1ec041e5ba44a761e375ca397939206c2` |
| `docs/static_review_notes.md` | `60cc6d3352d86b45a725de2c57b5f3c2d8a31cd8cf00420f6bf48a6d0cc5e089` |

The author root is
`/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_10`.
The manifest is metadata, not a new runnable snapshot or an execution freeze.
Root backup verification is delegated to the root and is not claimed here.

Execution requires all of the following, none waived by this review: resolve
R05 and R07 in a new revision; independently review that revision and the enabling diff;
clear round 11's knowledge/relevance gate; freeze the actual runtime, sources,
review receipt, and complete launch/accounting plan; obtain the root's actual
run decision; and retain the one-attempt/no-relaxation discipline.

**Current result: HOLD / NOTRUN / EXECUTION_ENABLED=False.**
