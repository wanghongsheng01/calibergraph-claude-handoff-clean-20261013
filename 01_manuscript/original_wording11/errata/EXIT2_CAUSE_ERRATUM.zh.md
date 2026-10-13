# Session 56495 exit2 原因勘误（追加记录）

本记录只修正文案解释，原回收回执、嵌入它的审查 JSON、旧冻结包及科学结果均不改写。

原文错误地把“ten not-selected slots”列入 exit2 原因。正确解释是：14 个选中槽中的 7 个 typed contract STOP 返回 child exit2，且 `valid_completed_result=false`；这 7 个槽使 selected-slice 的 `all(...)` 为假，supervisor 因而返回 exit2。另 10 个未选中 NOT_RUN 槽完全不参与该退出状态聚合，不能列作其原因。

英文替代解释：

> Exit2 is expected because seven of the fourteen selected slots ended with typed contract stops (child exit2 and valid_completed_result=false). The ten unselected NOT_RUN slots do not participate in the selected-slot status aggregation and are not a cause of exit2. Per-slot correctness/resource/cleanup requires independent review; no scientific or timing replacement is inferred.

覆盖的 2 个原 JSON 位置与 2 个同字节冻结副本：

| 记录角色 | 原路径 | JSON pointer / 位置 | 原 SHA-256 |
|---|---|---|---|
| `original_workspace_record` | `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/experiments/STATUSFIX_SUPERVISOR_SESSION56495_REAP_RECEIPT.json` | `/interpretation`；第12行 | `c6f70a9942508dfee0d2f16136fd8086c2018830f17158e2a8412a278563c201` |
| `frozen_package_copy` | `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/final_package_20261011_v5_01/workspace/calibergraph_revision_20261009/today_20261011/experiments/STATUSFIX_SUPERVISOR_SESSION56495_REAP_RECEIPT.json` | `/interpretation`；第12行 | `c6f70a9942508dfee0d2f16136fd8086c2018830f17158e2a8412a278563c201` |
| `original_workspace_record` | `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/science_review/STATUSFIX_SUPERVISOR_EXECUTED_REVIEW.json` | `/external_execution_receipt/interpretation`；第18行 | `7c8d23d8cfb0f2734051ca517c66880d1062eb3e3a7bb5724b6d3e8ad2829903` |
| `frozen_package_copy` | `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/final_package_20261011_v5_01/workspace/calibergraph_revision_20261009/today_20261011/science_review/STATUSFIX_SUPERVISOR_EXECUTED_REVIEW.json` | `/external_execution_receipt/interpretation`；第18行 | `7c8d23d8cfb0f2734051ca517c66880d1062eb3e3a7bb5724b6d3e8ad2829903` |

代码证据为 `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/runtime_fair_v5_statusfix/supervisor.py`（SHA-256 `5f78c98371ba255dcf97c46f298c23ae9af0fcbb2861d7e1745052be06e6b295`）：第 90–91 行仅派发选中范围；第 151–152 行要求 child exit0 才可完成；第 156–161 行只对 `jobs[5:19]` 聚合，再决定 supervisor exit0/2。

已有 `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/runs/statusfix_supervisor_integration_01/supervisor_report.json`（SHA-256 `ec1836bdab9b3f7980fb7a209a9a9d83bc1ddcd575e4b9e354633987197605de`）显示：索引 5–11 为 7 个 exit0 正常返回；12–18 为 7 个 exit2 合同 STOP，其中 6 个 `CONTRACT_UNSAT_REJECTED`、1 个 `UNVERIFIED_CONTRACT`；索引 0–4、19–23 为未选择 NOT_RUN，无 child exit。此处仅静态读取现存回执，没有重跑或重分类。

结构化勘误：`EXIT2_CAUSE_ERRATUM.json`（SHA-256 `bd07ccfd1f9b7cfeeb6fefac741d46efa3b3cf55f275fe81cc5086a04067e8fc`）。追加写入前后整包哈希核验见 `APPEND_ONLY_INTEGRITY_RECEIPT.json`。旧包 1723 个清单载荷文件及 3 个元数据文件均保留。

本轮实验关闭。科学判定仍为 **SCIENCE_NO_GO**；后续科学问题需要新研究，本勘误不提供新增实验证据。自动 bbox 检查仍为 **UNAVAILABLE**（SIGABRT），不得称自动通过。未上传、push 或提交；遵从用户禁止外传的限制，远端备份未执行。
