# v5 主入口合同修复：36 槽实际回执独立核验

结论：**Fixed-with-executed-evidence，仅限 D01–D06 × 六臂的 36 个已注册、已暴露构造控制。** 未发现本次回执与注册输入、源锁或预期合同语义之间的实质不一致。本结论不证明方法新颖性、真实业务缺陷覆盖、自然数据泛化或性能优势，也不外推其他成本、差分或 SpotIt 槽。

审阅者为不同 AI agent `/root/independent_review`，不是真人审稿人。审阅者曾编写旧窄合同桥模块，未编写本轮 v5 主入口集成，也未执行这 36 个目标；因此本报告是集成回执、源码和独立具体整数运算核验，不应称整个参考模块完全独立于作者。本轮没有导入目标、加载 native、运行求解器或 SQLite。

## 实际分母与结果

| 注册控制 | 槽数 | 实际结果 | 独立核验重点 |
|---|---:|---|---|
| D01 literal-left，强制 A=6 | 6 | SAT，exit 0 | 原 C 为 `5<A AND A<=6`；完整数据库 `T=[[6]]`；原 SQL 回放 NULL/6 |
| D02 同 SQL、同 C | 6 | pair UNSAT，exit 0 | 非空可满足合同；canonical 路由也先经过公共合同门 |
| D03 无附加 C | 6 | SAT，exit 0 | 实际数据库均为 `T=[[5]]`，回放 NULL/5；不误写成注册的可选 A=6 固定点 |
| D04 矛盾 `5<A AND A<=5` | 6 | CONTRACT_UNSAT_REJECTED，exit 2 | 查询解析、查询求解、fallback 未运行；不能计为 pair UNSAT |
| D05 `A BETWEEN 6 AND 5` | 6 | CONTRACT_UNSAT_REJECTED，exit 2 | 原上下界顺序未调整；不能把矛盾合同的拒绝当查询正确性 |
| D06 含不支持 OR 的完整 C | 6 | UNVERIFIED_CONTRACT，exit 2 | 整体拒绝；base 求解、IC 编译、XOR 与查询工作均未运行 |

36/36 均为 PROCESS_EXITED、无 `stop_reason`、cleanup COMPLETE。18 个查询槽 `valid_completed_result=true`；18 个预期合同停止槽保持 `false`。队列的 ALL_SELECTED_BATCHES_RETURNED 仅表示均返回；12 个 supervisor 批次实际为 6 个 exit 0 和 6 个 exit 2，不能汇总成全部正常查询成功。

D01–D05 共 30 槽保留 base SAT 和 normalized/reference XOR UNSAT；base 中没有混入被测 IC，exact rows 均为 T=1。原始合同 AST 与注册值逐字结构相同，哈希一致；实际编译的是 normalized copy，literal-left 严格比较转换为等价 column-left 方向。合同 guard 与桥记录的完整 facts SHA 相同。D01–D03 guard SAT，D04–D05 guard UNSAT。后者的 exact-row UNSAT 不构成合同非空性证据，报告没有据此放行查询。

12 个实际 SAT 路由均保留原 SQL、完整一行数据库、原合同真值及 SQLite 全形状结果。审阅者使用独立标准库整数运算重新计算具体原合同与这两个固定 SQL 的值，均与记录一致；没有重跑 SQLite。D01/D03 canonical 首尝试不相同后保留官方 fallback 及其 SAT 回执，没有省略该路径。

## 来源链与范围

- 原始队列：`experiments/QUEUE_V5_main_cost_132_168.json`。
- 12 个 supervisor：`runs/fair_v5_main_cost_{132,135,138,141,144,147,150,153,156,159,162,165}_01/supervisor_report.json`；36 个 worker 位于各目录 `job_0132` 至 `job_0167`。
- READY lock：`experiments/v5_registration_01/runtime_paths_v5.json`，SHA256 `4221081d3c63096841a902f1c8f70ac16f5d967c08476f26f8377d6bb4924443`。本轮独立读取并核对其 **853 个锁定文件全部字节哈希**，无不符。
- 注册 suite SHA256：`9db84350b498c3e5f37b06adf5868fa0e0429a81a2ebff65f930f78bd8b36485`。
- 实际参考模块为 v5 `fdcee3a919930013945c571e64b7d4b478186c93ceee4546ff520879e99680e0`，不是旧 bridge `781ce…`；五个程序源、queue driver、全部报告、stdout/stderr 与 emergency 日志的完整 SHA 见同名 JSON。
- 关键源索引：`runtime_fair_v5/common.py:137` 原 AST/独立参考/normalized XOR；`:227` 同 Environment 与完整 facts 绑定；`:238` 具体原合同检验。`worker.py:107` 公共桥、`:114` 合同门、`:333` typed stop 与 cleanup；`supervisor.py:151` 无 stop 的严格完成条件。

记录的最大子进程 wall 为 1.413750375 秒，CPU 为 1.349048 秒；最大采样 RSS 为 117456896 字节，worker 的 ru_maxrss 最大值为 118587392 字节。所有槽观察到的最大原生 OS 线程数均为 2，虽然 solver_threads=1；不能写成全进程单线程。RSS 为软采样，不是连续硬上限。本报告不比较各方法速度。

## 明确保留的边界

这 30 个 XOR 是本地求解回执，不是可移植证明证书或一般正确性定理。桥中 `no_pair_oracle_run=true` 描述桥子阶段；成功 worker 的 `pair_work_status` 仍保留 ATTEMPTED_EFFECT_UNKNOWN 子阶段文字。不能单读这两个字段判断最终结果；本次依据最终 COMPLETE、实际 attempt、退出码、cleanup 与回放交叉核定。

D06 已完成 native/Environment 导入后才拒绝合同，不能声称它没有任何 native 效果。支持范围仅为已注册 AST 的窄严格谓词语义；不声明任意原合同文本解析完整、SQL CHECK/DDL NULL 约定、OR/PK/FK 支持或完整 SQL 证明。

本轮只追加审查文件，原件未改。全量 campaign、先前资源异常及未冻结稿件均不在本结论范围。依用户禁止上传/push的指令，本交付仅本地保存，未声称远程备份。

机器可读证据：`MAIN_ENTRY_REPAIR_EXECUTED_REVIEW.json`，SHA256 `25c475126d49a1c659e90eb870227a18faa9b4ee13dbbf9b838b1da8ef3b9d66`。独立核验程序：`audit_main_entry_36_receipts.py`，只用标准库读取/哈希/具体运算，拒绝覆盖既有报告。
