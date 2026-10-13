# Static round-10 probe

**Prepared, not executed.** `code/run_probe.py` defaults to
`EXECUTION_ENABLED = False`. Import has no experiment, enumeration, native call,
file write, or launch side effect. Independent pre-review and root freeze are
required before any launch. No backup is claimed here; the parent/root owns
the project-wide private backup and its verification.

The fixed synthetic universe is 129 original common bodies, 2739 different
unordered projection pairs, and all 64 partial functions on a three-element
domain for `R(k PRIMARY KEY, v)`. This creates 175296 logical pair-model
comparisons. No private, public, development, held-out, or natural data is read.

- `code/finite_core.py`: canonical inventory, complete key chase, all
  endomorphisms, FD closure, bidirectional cover, and an independent evaluator
  over original bodies.
- `code/run_probe.py`: Darwin-only one-shot supervisor, initial NOTRUN ledger,
  resource checks, one worker, append logs, conservative recovery and receipts.
- `protocols/bounded_probe_draft.md`: draft semantics, denominators, rejected
  control/correction, control expectations, costs, stop rules and evidence limits.
- `docs/static_review_notes.md`: static-only checks, known limits and outstanding
  review gates. `docs/source_sha256.txt` is a metadata hash manifest, not a test.

## Interface after review only

The eventual single launch interface is:

```
<pinned-python> -B -E -s -S code/run_probe.py --freeze protocols/freeze.json
```

Do not run this command during preparation. The program rejects a false source
flag. After root enables the source flag under review, it also requires the
following root-authored freeze schema. This example is intentionally not saved
as `freeze.json` and does not authorize a run:

```json
{
  "status": "FROZEN_AFTER_INDEPENDENT_PRE_REVIEW",
  "execution_authorized": true,
  "independent_reviewer": "<review identity>",
  "review_receipt_relative_path": "docs/<review receipt>",
  "review_receipt_sha256": "<hash>",
  "runtime": {
    "executable": "<absolute resolved Python path>",
    "sha256": "<Python executable hash>",
    "version": "<sys.version first token>",
    "implementation": "cpython",
    "worker_flags": ["-B", "-E", "-s", "-S"]
  },
  "denominators": {"bodies":129,"pairs":2739,"models":64,"pair_models":175296},
  "sha256": {
    "code/finite_core.py": "<final hash>",
    "code/run_probe.py": "<final enabled hash>",
    "protocols/bounded_probe_draft.md": "<final hash>"
  }
}
```

Only `round10/runs/only_attempt/` is used, where `round10` is this artifact's
root, and `runs` must be its direct child. Every file uses exclusive creation.
An existing `runs/attempt.lock` prevents retry. The implementation provides no
force, resume, overwrite, random-seed, model-subset, budget, or host override.
Do not delete the lock to retry after a precheck rejection or truncation.

The supervisor forks and execs exactly one worker using that same pinned runtime
and flags. Its hidden `--owned-worker` continuation requires the inherited
handoff pipe, correct parent/process-group identity, inherited CPU/wall limits,
the already-consumed attempt lock, ready baseline, and exclusive worker claim.
It cannot create an independent attempt or overwrite an existing worker result.
`worker_exec_lifecycle_wall` covers the fork/exec through wait4 reap, including
worker interpreter startup/exit. It does not cover supervisor interpreter startup
wall. Supervisor startup CPU is included in SELF. No third Python launcher exists.

Expected files, when their producing stages finish:

| File | Meaning |
|---|---|
| `denominator-contract.json` | Fixed denominators before slot materialization |
| `body-inventory.jsonl` | 129 original bodies, original subset/pair metadata |
| `pair-slots-notrun.jsonl` | 2739 immutable signed NOTRUN pair slots |
| `model-inventory.json` | 64 model rows in fixed order |
| `initial-status.json` | Full denominators before host precheck |
| `control-slots-notrun.json` | Three in-universe control obligations |
| `host-precheck.json` | Admission telemetry, including rejected admission |
| `body-results.jsonl` | Original/chased mapping and structural/evaluator costs |
| `pair-results.jsonl` | Per-pair 64 count/equality entries and cover evidence |
| `worker-receipt.json` | Worker state, controls, counters, phase CPU times |
| `worker-error.json` | Exception record if that write can complete |
| `supervisor-failure.json` | Minimal failure when full recovery is unavailable |
| `pair-slots-final.jsonl` | Complete denominator overlay, if recovery finishes |
| `supervisor-receipt.json` | Stop reason, NOTRUN totals, partial results/accounting |
| `accounting-after-finalization.json` | Terminal accounting; outer exit still required |

A success-labelled supervisor receipt alone is insufficient: terminal accounting
and the observed zero outer exit within budget are also required. A kill can
leave only the raw denominator slots and partial append logs. Do not reinterpret
missing or partial files as zero failures. Do not rerun to improve completion.

Root has additionally paused the execution decision pending round 11's check
of existing constraint/normalization theory. Passing static pre-review alone
does not release that scientific-relevance gate; this snapshot stays disabled.

## Clean restore

Restore these source/protocol/docs paths from the parent-approved private backup,
verify the static source hash manifest against the restored files, and read the
draft plus the independent review receipt. Restoring does not authorize a run.
Preserve any `runs/attempt.lock` and run evidence from the backup. No dependency
installation is needed. The target is the existing Darwin Python environment
with the standard library and Darwin system libraries; no portable alternative
has been implemented or tested.
