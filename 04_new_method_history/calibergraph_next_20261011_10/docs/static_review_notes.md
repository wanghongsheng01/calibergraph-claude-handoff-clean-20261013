# Static preparation record

Status: **NOTRUN / DRAFT / awaiting root-independent pre-execution review**.
Preparation used source editing and reading only. No Python invocation, module
import, `ast`/compile pass, test, synthetic scientific computation, external
dataset, model API, network request, dependency installation, or launch took
place. Source hashes are metadata, not execution or empirical validation.

Applicable instruction read: `/Users/loctek/.codex/AGENTS.md`. Its durable-output
backup gate is delegated explicitly to the parent/root. No source data access
occurred, so no DataHub path was invoked. unrelated_project and all prior rounds were untouched.
Only new round-10 code/protocol/docs paths were written by this agent.

## Static checks completed

- Original atom tuples are ordered binary atoms, so R(x,y) differs from R(y,x).
  `combinations` preserves the 129 fixed original bodies; chase deduplication is
  local only and cannot remove a body or pair.
- Subset pair enumeration uses original active variables; the empty set is first
  and retained. Distinct original subsets can become the same chased subset;
  their original pair is still retained.
- Full chase loops until a pass makes no union, with canonical representatives.
  The evaluator does not consume these representatives.
- Every self-map, including noninjective maps, and every mapped atom is checked.
  Both cover directions use the stated source and target. Alpha and beta need
  not agree. FD closure iterates; empty closure stays empty.
- The direct evaluator uses original variables/atoms and distinct projection
  tuples, and checks all 64 legal partial functions including the empty model.
- Fixed body/pair/model arithmetic was independently hand-checked by the static
  subagent: 129 / 2739 / 64 and 175296 logical pair-model comparisons.
- The invalid old triangle control was identified before execution, reported to
  root, retained explicitly, and corrected with root authorization without any
  denominator change. The legal projection distinction tests 2 vs 1.
- There is no CLI budget increase, run-subset selection, retry, overwrite, or
  auto-enable option. Output files use exclusive creation and the lock consumes
  the sole attempt even on host-precheck rejection.
- Resource helpers call only a native read-only whitelist. No process inventory
  is traversed and only the current supervisor/owned child PIDs are queried.
  Signals target the exact unreaped child and, if verified, its own group.

## Known boundaries for independent review

No syntax, runtime, native ABI, host-precheck, budget sufficiency, or numerical
result has been empirically validated. A static subagent's source audit is a
preparation check and does not replace the root's independent pre-review.

Preparation review identified and statically repaired: SIGALRM/PID reuse races
(blocked ownership transitions with saved wait4 tuples), incomplete baseline
accounting, weak overlay validation, missing final resource rejection, recovery
after an exhausted wall alarm, continuing bulk work after detected RSS overage,
and installing the resource envelope after freeze verification. These edits have
not been tried. The final independent reviewer must inspect the exact snapshot.

The native ABI assumptions are Darwin `HOST_VM_INFO64`'s first four uint32 words
and `PROC_PIDTASKINFO`'s first two uint64 words, plus `hw.memsize` as uint64. The
host-memory test is explicitly a conservative proxy. Native failure fails closed.
RSS is sampled and CPU has kernel enforcement granularity, so neither is an
infinitesimal continuous bound. The root approved the conservative 1+1 second
CPU split; insufficient budget is an intended recorded truncation outcome.

The internal wall clock begins at supervisor function entry, not interpreter
startup. Final accounting excludes writing itself and interpreter exit. Root
must retain outer wall/exit evidence before declaring success. An absent terminal
accounting file or a nonzero outer exit defeats any earlier success-labelled
receipt. Unexpected SIGKILL may prevent receipt/cleanup; child has independent
CPU and remaining-wall limits. No result is silently retried or repaired by a
second scientific execution.

Timing counters for chase, map tests, cover, evaluator and serialization are
supplementary and do not sum to all elapsed CPU: metadata enumeration, setup,
controls, function dispatch, monitoring and finalization remain in SELF/wait4
totals. All are charged. Saving model counts once per subset within a body is
intentional shared evaluation, while every original pair retains both vectors.

## Remaining gates

1. Independent pre-review of exact source and protocol, including correctness,
   process races, finalization, schema-specific controls and accounting.
2. Resolve any review blockers with static edits, not a prohibited trial run.
3. Root freezes final hashes and reviewed enable change; no freeze exists now.
4. Root decides the one permitted run using the external launch/accounting
   requirements. A blocked start or truncated run is recorded, never retried.
5. Root completes and verifies the private backup. This subtask cannot claim
   BACKUP_OK or remote recoverability.

Root has paused the execution decision until round 11 checks possibly covering
prior normalization/constraint theory. Source remains disabled. The existing
two-process design now fork/execs a pinned Python worker and records its full
`worker_exec_lifecycle_wall`; this includes worker startup/exit but explicitly
excludes supervisor interpreter startup wall. Runtime path/hash/version/flags
must be frozen by root. No extra launcher/process budget was introduced.
