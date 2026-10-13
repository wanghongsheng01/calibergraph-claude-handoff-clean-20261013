# 第16轮私有作者备份选择

仅允许复制 `BACKUP_SELECTION.json` 的 `files` 中逐项列出的当前字节，以及本选择文件两份；不按目录整树复制，不递归展开任何路径、哈希清单或运行时依赖。当前纳入 **70 份现有文件**（1551334 bytes），另加两份选择文件。此处没有执行复制、commit 或 push，不表示 `BACKUP_OK`，也不代替独立结果审查。

- `AUTHOR_STATE_AND_ONCE_EVIDENCE`：3份。作者状态、单次执行已消耗证据和最终化收据；不授权再次运行。
- `AUTHOR_IMPLEMENTATION`：11份。作者编写的源代码、差异、说明和静态检查；运行时依赖不随文件引用递归纳入。
- `AUTHOR_DISABLED_SNAPSHOT`：12份。最终化前禁用执行的作者快照；保留历史版本，不能与当前启用版本混同。
- `AUTHOR_PROTOCOL_AND_PROVENANCE`：7份。作者预注册协议、分析计划、路径和哈希；引用原SQL/schema/C/native/upstream的路径不是纳入其字节。
- `SYSTEM_RESOURCE_METADATA`：11份。已逐文检查的观察与外层收据/输出；只有CPU、内存、load、时刻、状态、路径和哈希等系统元数据。
- `AUTHOR_SCHEDULING_AND_LEDGER`：5份。作者观察器源码、等待规则与封账；只备份既有文件，不创建或启用调度。
- `AUTHOR_ANALYSIS_AND_PROVENANCE`：8份。作者聚合器、结果解释、静态核验和原证据路径/哈希；不复制这些路径指向的原证据。
- `SANITIZED_DERIVED_RESULTS`：2份。派生状态、数值成本、引用哈希和计数；递归检查未发现完整原SQL、schema/fullC对象、数据库值或查询输出明文。
- `AUTHOR_SEMANTIC_RECONSTRUCTION`：3份。作者事实映射分析；含完整17列表列类型清单和/或11条C的语义信息，可重建schema/C；不是纯哈希元数据。依据本轮明确授权纳入，不含原source_record对象、完整原SQL或模型数据。
- `AUTHOR_SEMANTICS_PROVENANCE`：2份。作者语义分析的输入/输出哈希清单；不递归复制被引用输入。
- `AUTHOR_WAITING_ANALYSIS`：6份。作者静态边界诊断、数学证明及出处；可能含小段表达式、字段名或追踪摘录，不含完整原SQL或具体数据库/查询输出值。

`analysis/derived_once/derived_results.json` 已按全部 10992 个JSON节点递归核对键、类型、字符串和数组；未发现完整原SQL、schema/fullC对象、数据库单元格或查询输出明文。保留原SQL/输出哈希、输出行数、状态和成本。其SHA256为 `4e3f26724c0c702f20ed6233bcd29162866d58ad9dd9b7e673222179b5738414`。派生JSON中的12组嵌套数组都只是两遍case_id配对。

语义文件明确按 **AUTHOR_SEMANTIC_RECONSTRUCTION** 纳入：`four_source_identity_evidence.json` 含完整17列表列类型清单，`constraint_mapping_evidence.json` 含11条C的operator、字段与literal，`SEMANTICS_AUDIT.zh.md` 含同类解释。它们可重建schema/C信息，不能称为纯哈希数据；本轮已明确允许保留这类少量作者事实映射分析。它们不含完整原SQL、原source_record对象或具体模型/数据库单元格。waiting_audit为作者静态解释与证明，可能包含小段表达式、字段名或trace摘录。

资源观察和外层输出已逐文核对，只有CPU、内存、load、时刻、状态及路径/哈希元数据。作者程序中的一般SQL执行模板属于作者实现，不能据此递归复制第三方工作负载SQL或依赖库。

必须排除整个 `runs/**`（当前170个文件），包括其中看似干净的日志。该树承载原SQL、source_record、schema/C、具体模型与查询输出；只保留 `analysis/RAW_EVIDENCE_PROVENANCE.json` 的出处与哈希。排除临时空flock `.pilot_single_worker.lock`；永久 `EXECUTION_ONCE.lock` 保留为不得重试的证据。所有第三方upstream、数据集、原始来源对象、native二进制及`.venv`/安装依赖本体均排除。未列名的新文件、符号链接和二进制载荷默认排除。

清单只匹配读取时字节。root收尾后须重算全部哈希，并检查改变的CHECKPOINT、结果解释及新增独审文件，再逐项追加；不得为匹配本清单改动冻结产物。两份选择文件没有自指哈希，由root最终复制清单记录。作者文件成功进入私有仓库仍不解除历史原始证据与精确native环境清洁恢复的 `BACKUP_BLOCKED`，也不解除 `DATAHUB_REGISTRATION_BLOCKED`。

精确路径白名单（均相对于 `calibergraph_next_20261011_16/`；哈希见JSON）：

```text
CHECKPOINT.json
EXECUTION_ONCE.lock
FINALIZATION_RECEIPT.json
analysis/AGGREGATOR_STATIC_VALIDATION.json
analysis/AUTHOR_RESULTS_MANIFEST.json
analysis/POSTRUN_HASH_AUDIT.json
analysis/RAW_EVIDENCE_PROVENANCE.json
analysis/README.zh.md
analysis/RESULTS.zh.md
analysis/SHA256SUMS.outputs
analysis/aggregate_results.py
analysis/derived_once/RESULTS.zh.md
analysis/derived_once/derived_results.json
author_snapshot_disabled/generation_replay.draft.json
author_snapshot_disabled/implementation/AUTHOR_DISABLED_MANIFEST.json
author_snapshot_disabled/implementation/README.zh.md
author_snapshot_disabled/implementation/SHA256SUMS.outputs
author_snapshot_disabled/implementation/STATIC_VALIDATION.json
author_snapshot_disabled/implementation/generation_common.py
author_snapshot_disabled/implementation/generation_supervisor.py
author_snapshot_disabled/implementation/official_contract_admission.py
author_snapshot_disabled/implementation/official_generation_backend.py
author_snapshot_disabled/implementation/official_generation_worker.py
author_snapshot_disabled/implementation/round15_to_round16.diff
author_snapshot_disabled/implementation/safe_sqlite_replay.py
implementation/AUTHOR_DISABLED_MANIFEST.json
implementation/README.zh.md
implementation/SHA256SUMS.outputs
implementation/STATIC_VALIDATION.json
implementation/generation_common.py
implementation/generation_supervisor.py
implementation/official_contract_admission.py
implementation/official_generation_backend.py
implementation/official_generation_worker.py
implementation/round15_to_round16.diff
implementation/safe_sqlite_replay.py
observer_outer/obs_0001.outer.json
observer_outer/obs_0001.stderr.txt
observer_outer/obs_0001.stdout.txt
observer_outer/obs_0002.outer.json
observer_outer/obs_0002.stderr.txt
observer_outer/obs_0002.stdout.txt
outer_launch/OUTER_RECEIPT.json
outer_launch/stderr.txt
outer_launch/stdout.txt
protocols/ANALYSIS_PLAN.zh.md
protocols/ANALYTIC_CONTROLS.round06_verbatim.zh.md
protocols/ANALYTIC_CONTROLS.zh.md
protocols/RUNTIME_INPUT_CARRY_FORWARD.json
protocols/generation_replay.draft.json
protocols/generation_replay.freeze.json
protocols/generation_replay.registered.json
resource_observations/obs_0001/receipt.json
resource_observations/obs_0002/receipt.json
scheduling/CLOSED_OBSERVATION_LEDGER.json
scheduling/OBSERVER_STATIC_FREEZE.json
scheduling/WAITING_RULES.zh.md
scheduling/resource_observer.py
scheduling/waiting_schedule.json
semantics/SEMANTICS_AUDIT.zh.md
semantics/SHA256SUMS.inputs
semantics/SHA256SUMS.outputs
semantics/constraint_mapping_evidence.json
semantics/four_source_identity_evidence.json
waiting_audit/BASELINE_IDENTITY_PROOF.SHA256SUMS.inputs
waiting_audit/BASELINE_IDENTITY_PROOF.SHA256SUMS.outputs
waiting_audit/BASELINE_IDENTITY_PROOF.metadata.json
waiting_audit/BASELINE_IDENTITY_PROOF.zh.md
waiting_audit/ENGINEERING_BOUNDARY_DIAGNOSIS.json
waiting_audit/ENGINEERING_BOUNDARY_DIAGNOSIS.zh.md
analysis/BACKUP_SELECTION.json
analysis/BACKUP_SELECTION.zh.md
```
