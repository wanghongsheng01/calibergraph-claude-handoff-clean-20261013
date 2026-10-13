# VeriEQL / SQLSolver：真实 SQL 验证范围核验（阶段 15）

审计日期：2026-10-11。本文只读核验原文与官方源码；**未运行 solver 或 SQL，全部性能数字均为论文报告、NOTREPRODUCED**。结构化证据、精确路径及代码哈希见 [evidence.json](evidence.json)。

| 维度 | VeriEQL | SQLSolver |
|---|---|---|
| 科学任务（PAPERCLAIM） | IC 下有限输入域的等价证明；SAT 可提取数据库反例 | 无行数界的等价证明；sound、incomplete，过近似 SAT 不足以证明不等价 |
| SQL / NULL | bag；ORDER BY 用 list；3VL；joins/grouping/aggregates/CASE/WITH/IN。论文排除 correlated subqueries、window、LIMIT | bag / ordered bag；COUNT 的 NULL 建模见 Table 4；不能据局部证据声称所有 NULL 组合均受支持 |
| IC | 论文：PK/FK/NOT NULL/CHECK/逐一自增；冻结代码有对应多种分支 | 固定代码明确有 Unique / NotNull / Reference；不能说“无 IC”，也不能推为任意 CHECK/fullC |
| bound | **论文：每表至多 N；当前 inspected 建表路径：每表恰好 N 个存活基础元组** | U-expression 求和无固定数据库行数界；没有找到全局 two-variable 限制 |
| 贡献与成熟机制 | 贡献在实用 SQL/IC 语义及算子编码；BMC、SMT、反例提取、multiplicity 比较本身已成熟 | 贡献在嵌套/参数化/非线性求和处理及排序分解；U-expression、既有 LIA*→LIA、Z3 已有 |

原文定位：[VeriEQL v2](https://arxiv.org/html/2403.03193v2)，§3–§5、Def.3.5、Thm.4.8、§7、Appendix C.1；[SQLSolver 作者 PDF](https://www.cs.yale.edu/homes/piskac/papers/2024SIGMOD.pdf)，§2.2 pp.227:5–6、§§3–5 pp.227:7–21、Table 4。以上分别是作者主张，未独立证明论文定理。

| 数据集 | VeriEQL：总数 / checked / refuted | SQLSolver：等价对总数 / proved / unproved |
|---|---:|---:|
| LeetCode | 23,994 / 14,905 / 3,586 | — |
| Calcite | 397 / 261 / 4 | 232 / 232 / 0 |
| Literature | 64 / 34 / 29 | — |
| Spark SQL | — | 127 / 114 / 13 |
| TPC-C | — | 19 / 19 / 0 |
| TPC-H | — | 22 / 19 / 3 |

VeriEQL 的 LeetCode 是公开 accepted SQL 对作者参考 SQL；Calcite 是规则测试；Literature 是 38+26 既有对。其 600 秒从 bound 1 递增，checked 只要求至少完成 1；Literature 的 34 个 checked 中作者仍判定 7 个不等价。SQLSolver 的 TPC 对由 Spark 计划人工转 SQL；总数 400、证明 384，摘要 346/359 仅含 Calcite+Spark。两工具的 Calcite 分母和成功含义均不同。[VeriEQL §6.1–6.4](https://arxiv.org/html/2403.03193v2#S6)；[SQLSolver §6 pp.227:21–23](https://www.cs.yale.edu/homes/piskac/papers/2024SIGMOD.pdf)。

VeriEQL Table 1 的 2/3/4 行界成本只在终止样本取均值，分母是已 checked 子集；SQLSolver Table 6 则逐对系统用共同成功子集。精确数值见 JSON。SQLSolver 实验用 Java 17.0.4 / Z3 4.8.9 / ANTLR 4.8、EC2 c5a.8xlarge；其论文统一 timeout 未找到。VeriEQL 硬件未找到。两者全量实验总成本均未核定。

有两个必须进入后续实验清单的代码事实：

1. [VeriEQL 固定提交 environment.py](https://github.com/VeriEQL/VeriEQL/blob/3b99928bf976c11cb59c9db6a177adba21f75798/environment.py#L584) 第 518、584 行生成 N 行并强制 Not(DELETED)。`verifiers/verifier.py:83` 把这些约束加入求解前提；`parallel/cli_within_bound.py:38–39,97` 对所有表用同一标量，并只遍历 1..N。这个路径没有覆盖空表及大小不同的表组合；不能借论文的 up-to 保证。这里只静态确认路径，未宣称发现运行时 bug，也未证明任何补齐定理。
2. [SQLSolver 固定提交 Constraint.java](https://github.com/SJTU-IPADS/SQLSolver/blob/dcc2a91d8971a4c4d30b055f99d7d8428a1b754b/superopt/src/main/java/sqlsolver/superopt/constraint/Constraint.java#L14) 与 [UExprTranslator.java](https://github.com/SJTU-IPADS/SQLSolver/blob/dcc2a91d8971a4c4d30b055f99d7d8428a1b754b/superopt/src/main/java/sqlsolver/superopt/uexpr/UExprTranslator.java#L957) 实现上述三类 IC 重写；Reference 分支有目标唯一性、源非 NULL 条件。当前配置 Z3 timeout 为 10,000 **毫秒**，API timeout 为**秒**；不得回填为论文参数。[官方 API](https://github.com/SJTU-IPADS/SQLSolver#api) 还说明等价对可返回 NEQ/UNKNOWN，故这两种状态都不能当有效反例。

当前 [VeriEQL README](https://github.com/VeriEQL/VeriEQL#benchmarks) 写 LeetCode 23,224，论文写 23,994；README 总结果 5,636+15,200+3,619 仍是 24,455。差额 770 尚未解释，当前数据文件未重新计数。README 还注明约束更新与 `literature-rewrite.jsonlines` 的去相关改写。**不要混用当前源码、改写文件与旧汇总的分母。**

对当前公开 SQL、fullC、bound 2/3/4 的判断（INFERENCE）：

- 可以诊断真实查询是否在各个明确的基础表基数下出现可重放反例；定位 unsupported/error/unknown 的具体 SQL 或 IC；比较相同语义下编码、求解与总成本。
- 先固定原始 query/schema/fullC 哈希，并确认 fullC 本身可满足；否则 UNSAT 可能只是空输入域。分别记录 bag/list、NULL、类型、标量函数、各表基数向量、工具版本、预算与状态。
- exact-live 2→3→4 的输入域不具有 up-to 的包含关系。统一每表跑 1..N 也不能替代所有 `0..N` 基数向量。有限 UNSAT 不推出无界等价。
- “两变量克隆”计逻辑变量副本，“两行 bound”计基础元组，两者无同义关系。未经独立定理不能互相替代。
- SQLSolver 若在弱于 fullC 的前提下取得无界 EQ，可单向支持 fullC 下等价（还须查询语义一致）；其失败不构成 same-semantics 负结果。需要验证 fullC 的逐项映射，不能凭“有 IC”笼统认定支持。
- 这类有界诊断不能自动支撑全工作负载覆盖率、SOTA 或新方法贡献；仅重命名 BMC/SMT、约束开关、计数比较与变量复制也不构成新机制。

未决项：论文/源码的 up-to 衔接；当前公开数据分母；论文未定位参数；完整 NULL/fullC 兼容性；全部运行与重放。DataHub 注册因规范目录不在本任务写权限内为 `DATAHUB_REGISTRATION_BLOCKED`（父任务已完成 list）；私有备份由父任务统一完成，本子任务尚不声称 `BACKUP_OK`。
