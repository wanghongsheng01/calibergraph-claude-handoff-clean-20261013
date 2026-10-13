# 外部 v5 / statusfix 实际回归身份核对

结论：**外部实际测试的原 v5 五源、statusfix 六源与我们冻结版本全部逐字节一致。** 两轮各 24 个注册 job 的原始 worker 回执已逐项核对：每轮 6 SAT、6 UNSAT、12 正确合同停止；子进程退出分别为 12 个 exit 0、12 个 exit 2，无资源停止或 NOT_RUN。不是每轮 24 个 SQL 等价证明。

本审阅只读文件、哈希与已发生的回执，没有重新运行任何 target/native/SQL。外部根目录为：

`/Users/loctek/Documents/Codex/2026-10-10/task-3/calibergraph_audit_20261011/integration_review_v5/`

## 实际运行对象

原轮 `independent_run_01/SUPERVISION.json` 的 argv 直接运行我们原目录 `today_20261011/runtime_fair_v5/worker.py`，沿用锁 `4221081d…`，853 个文件。外部冻结清单 21 项与对应副本、现有原件全部一致。

statusfix 轮实际运行的是外部 `statusfix_review/frozen/worker.py`。其六个程序与我们 `runtime_fair_v5_statusfix` 完全相同，但使用**审阅方生成的独立锁** `statusfix_review/AUDITOR_RUNTIME_LOCK.json`，SHA `9b6b03b43c67f320243f5fe439a9ad369862c82215280b01ab9806da364b2dfc`。该锁的 854 个文件均核对；848 个非程序依赖与原锁完全相同，只替换五个原程序路径并加入六个冻结程序路径。它不是我们的 future/release lock，不能据此把本地 pending 锁说成已执行。

| 文件 | 原 v5 SHA 前缀 | statusfix SHA 前缀 | 核对结果 |
|---|---|---|---|
| common.py | 460b81bf | aad39a0f | 均与对应原件/实际锁一致 |
| worker.py | e4d6f8d0 | 5848538a | 均为真实子进程入口 |
| supervisor.py | bde829b8 | 5f78c983 | 字节匹配，均不是外部子进程入口 |
| query_differential.py | 747fcc77 | 747fcc77 | 未变；此次没有执行 differential job |
| contract_reference.py | fdcee3a9 | fdcee3a9 | 当前 v5 版本，不继承更早参考模块结论 |
| pair_status.py | 不适用 | 65edfe93 | 新 helper 字节一致 |

完整 SHA、实际路径、48 个原始 worker 路径与哈希见同名 JSON。旧 `e574…` 或 `781ce…` 窄参考版本的测试没有当作本轮覆盖。

外部两轮均使用自己的 `run_independent_entry_regression.py` 协调器，SHA 分别为 `9f9fc9b68b89fc59ed48339356f2a067cb44cd917c14a1359ee0cee5a28b130c` 和 `e0e052ef7e6e91198b57ddab7302c0c51933dcadaecfbe0b30f291f9fd1344c4`。它们不是我们新版 supervisor，也不是当前汇总器。外部 FINAL_REVIEW_STATUS 记录协调器 session 18584/57840 exit 0；本次可核该记录和每个 child 的 wait4 回执，不能独立重放平台历史。

## 本轮实际证据及边界

两轮 suite SHA 都是 `e0dae36b1c1a8cfccce8468c8656c9e9624ffce1a42b37a10c8938cad9b9d56e`，即四个构造合同 × 六臂，与我们的 28 配置主 suite 不同。literal-left 的六个真实 witness 均为 A=6，外部直接 SQLite 原谓词结果 TRUE，原 SQL 输出 NULL/6；column-left 六个反向控制均 UNSAT；矛盾/OR 各六个完整合同正确停止。

原 v5 的 12 个正常 SQL 结果仍记录 ATTEMPTED_EFFECT_UNKNOWN；statusfix 对应 12 个为 RETURNED，12 个合同提前停止为 NOT_RUN_CONTRACT_STOP。新回执明确科学有效性不从执行状态推出、资源验收仍待 supervisor。本次外部真实 worker 证据补足此前我们纯日志/静态审阅的时间截面，旧报告保持原样。

仍未覆盖新版原生 supervisor 进程集成、强杀/cleanup/磁盘失败竞态或完整故障注入；不证明方法新颖性、强基线优势、自然泛化或论文科学录用标准。外部 41 项纯日志探针与其 24 个 SQL/合同 job 分开计数。

## 给下一位独审的当前同哈希对象

外部交接所述“已有回归只绑定 ad83485…”属于其早期截面；当前已有回归 02 精确绑定最终导出器，并经本地另一审阅逐行核对。不能用外部旧回归替代，也不声称外部审阅者已验收这些新对象：

- 导出器 `experiments/BUILD_FINAL_V5_EXECUTION_CUT.py`：`83a23fc07b0185f39bd106be2a4c1d893c5c18a4a99592012ca6ed098275fe32`。
- 同哈希 16 项回归 `V5_AGGREGATOR_CLASSIFICATION_REGRESSION_02.json`：`2d1e1697c55898e1bbcc9b3abdb2782859c8b4a623d3f4120d273e545332cd1d`。
- 最终主实验截面 `FINAL_V5_EXECUTION_CUT.json`：`1d6d0291fda36937a26da6b46c9d07b18899a21686708fa4279c7a814e48b95c`。
- 逐槽 selector `V5_SLOT_SELECTION_FINAL.json`：`791693b25afdbae2be4143dadac51cf9a2af315417086ca56a96a3d9076f9e1b`。
- 我们的状态/逐槽独审 `science_review/PAIR_WORK_STATUS_FIX_INDEPENDENT_REVIEW.json`：`8df48aa798c9422cef6bc92a8c169b7a612bd0a88dba582394d21c6164bb4d5d`。

外部 statusfix 清单 SHA `50c0278a7edc4b8365e66b688dee75fb08e7cd9e03bd51496745ef5736a1bb21`、实际回执 SHA `c4d91aad3e0d34c72e7567eb99b36b0c2a6bb175761e67162d12286b3496a02c` 均已核实。本身份审阅 JSON SHA：`621719a9f639d87ec114101bb7f4e7898fc069e6dcb29cc6ac8b6eea31c1e962`。原件未改，未执行目标。
