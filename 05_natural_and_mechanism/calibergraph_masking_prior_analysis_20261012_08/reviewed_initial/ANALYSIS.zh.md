# DISTINCT 掩盖条件与先例核对：新机制 NO_GO

结论：本例证明了当前一次 ParSEval 生成覆盖遗漏一个合法区分数据库，不支持把“防掩盖／无补偿记录约束”作为新科学机制。已有完整聚合语义加最终输出不等约束已覆盖该目标。本轮只读保存结果、冻结源码及一手文献；新增基线、生成器、求解器、SQL 执行均为 **0**。不修改原稿、旧冻结输入、启动标记或 unrelated_project。

## 精确条件，而非“有边界元组即可”

固定案例 `thrombosis_prediction/1172` 的两查询均将 Patient 与 Laboratory 按 ID 内连接、筛男性，再计算 `COUNT(DISTINCT Patient.ID)`；唯一谓词差别是 `T-BIL >= 2.0` 与 `T-BIL > 2.0`。

令 A 为有至少一条等于 2.0 化验记录的男性患者 ID 集合，B 为有至少一条大于 2.0 记录的男性患者 ID 集合。根据这两条原查询及原约束直接推导：

\[
Q_{\ge}(D)=|A\cup B|,\quad Q_>(D)=|B|,\quad Q_{\ge}(D)-Q_>(D)=|A\setminus B|.
\]

因此必要且充分条件是：存在男性患者 ID，有边界记录，并且该 ID **不存在任何**大于 2.0 的连接记录。只需排除被选中 ID 的严格侧成员资格，不应禁止数据库所有大于 2.0 的记录。Laboratory 的 `(ID, Date)` 主键允许同 ID 多条化验记录；ID 非空，NULL 化验值两侧都不满足，NULL/非男性 SEX 也不会贡献计数。

必须区分三层：谓词判定不同的连接元组；去重后的 ID 集合不同；最终聚合值不同。本例两集合嵌套，所以第二层差异足以造成第三层差异。对任意非嵌套集合 S1/S2，计数差是 `|S1\\S2| - |S2\\S1|`，相反方向的不同 ID 可抵消；上述单 ID 条件不能推广成所有 DISTINCT 聚合的充分条件，也不覆盖 SUM/AVG。

保存候选及此前独立 SQLite 复算如下，本轮没有再执行这些 SQL：

| 保存候选 | A | B | A\\B | 原查询输出 |
|---|---|---|---|---|
| 0 | 空 | 空 | 空 | 0/0 |
| 1 | {1} | {1,29} | 空 | 2/2 |
| 2、3 | {1} | {1,29,48} | 空 | 3/3 |
| 4 | 空 | {1,38} | 空 | 2/2 |
| 5、6、7 | 空 | {1,38,58} | 空 | 3/3 |
| 8 | {38} | {1,38,58} | 空 | 3/3 |

全部 9 个保存数据库符合原完整 DDL。此前自构造控制有 A={1}、B=空，输出 1/0；它不是作者原始见证、未注入生成器、不是独立测试。边界已在四个候选中出现，不能把问题描述成“没有生成 2.0”。证据来自 `sampled_diagnostic_20261012_07/independent_review/INDEPENDENT_REVIEW.json` 与 `run/AUDIT_RESULT.json`。

## 真实代码与一手先例

**ParSEval：比较已存在，搜索目标不同。** 固定 commit `88cfe245bcf249a5b0df561a6b09c116ff2a2896` 的 [main.py:111](https://github.com/sfu-db/ParSEval/blob/88cfe245bcf249a5b0df561a6b09c116ff2a2896/src/parseval/main.py#L111) 已在每个接受候选上运行并比较两条查询；第137行分别调用单查询生成。 [generate.py:246](https://github.com/sfu-db/ParSEval/blob/88cfe245bcf249a5b0df561a6b09c116ff2a2896/src/parseval/generator/generate.py#L246) 构造目标与既有覆盖要求，第374行后的求解和接受逻辑保持覆盖；未把 pair 最终输出差异作为此处求解目标。论文的去重覆盖包括重复值和多个不同值，不等于本例的 A\\B 非空。[原论文，表1](https://dbgroup.cs.tsinghua.edu.cn/jnwang/papers/vldb2025-parseval.pdf)

这是源码结构和已保存行为的对应解释；没有反事实实验，不能断言保留覆盖、只增行、seed 或某个具体内部策略是唯一因果根因。也不能把当前源码与论文历史版本视为逐项相同。解析、完整目录加载、lowering、查询执行和最终比较已在这次运行实际完成，故本例不是已观察到的前端拒绝或比较器错误。

**Polygon：完整语义已经表达该目标。** 固定 commit `5e18237394d025dbb805cf833b4f54c321470774` 的 [Count_Distinct，第99–120行](https://github.com/polygon-sql/polygon/blob/5e18237394d025dbb805cf833b4f54c321470774/polygon/visitors/expression_encoder.py#L99) 仅计未删除、非空且与此前有效值不同的值；[environment.py:220](https://github.com/polygon-sql/polygon/blob/5e18237394d025dbb805cf833b4f54c321470774/polygon/environment.py#L220) 加入两个最终输出不等约束。这与论文的联合查询语义及输出差异目标一致。[Polygon 原论文，§3](https://arxiv.org/html/2504.06542v1)

静态推论是：在上述语义正确、完整约束与方言被准入时，掩盖候选不能满足最终 NEQ 目标；无需存在字面名为 anti-masking 的模块。这足以否决把目标本身声称创新，**不等于**已实测 Polygon 能在本例完整 SQLite 约束和给定预算内找到见证。本轮没有做它的 full-C 准入或运行。

**XData：已有差异传播与聚合先例，但不冒认实现实测。** 原论文 §2/§3.5 要求目标节点差异影响最终结果；§4.3 用去重投影再聚合处理 COUNT(DISTINCT)；§7 描述有界最终结果差异目标，且说明该直接 pair 方案留待后续评测。§5.2 的 SELECT DISTINCT 增删 mutation 不能单独当成本例的精确实现证据。[XData 原论文 v1](https://arxiv.org/html/2409.18821v1)

固定仓库 commit `a86031197fd1b572bd7782431331e8cb15554f88` 的先前 wrapper/运行日志证据保留。本轮访问固定树失败，API 未提供可核读正文；核心 Java 与实际 classpath 仍 **UNVERIFIED**，未下载或运行 JAR。因此仅确认论文已有目标与语义先例，不确认 XData 中存在逐字的“同 ID 无 >2 行”约束，也不声称它杀掉本例。§9 mutation 成绩不能作为 §7 native-pair 的实测成绩。

## 最多一个自动修改：仅保留为覆盖修复建议

唯一建议是一个**可关闭的、仅用于可证明嵌套谓词与同一 COUNT(DISTINCT key) 的 pair 目标编译规则**：从原查询和键约束自动导出“存在宽侧独有 key，且严格侧无该 key”的有界公式。常量、表名、键与过滤条件来自 AST/目录，不手写患者案例，不改变 SQL/DDL，不以预设控制数据库作 seed。完整约束 C 必须保留；不满足语义准入条件则报告 unsupported。

这个规则只是已知最终 NEQ 条件的特化，不应包装为新机制。本轮不实现、不运行；也不建议为论文创新继续投入该方向。

若未来仅为工程修复做最小验证，单因素对照应在相同 fresh bounded encoder、完整 C、行界、种子、求解配置下比较：

- off：存在宽侧独有的连接元组；
- on：保留同一元组目标，仅增加该 key 在严格侧不存在的约束。

两侧均只允许一次相同预算求解和原 SQL 复核，不允许 on 重启而 off 保留旧已掩盖数据库。这是一个目标公式消融，**不是官方 ParSEval 未修改版对照**。预注册预测：on 的 SAT 且合法复核结果必须是最终 NEQ；off 允许产生掩盖模型。若 on 的合法模型输出仍相等，编码正确性预测即失败；UNSAT、timeout 或 unsupported 分列，不能算赢。若 off 同样 NEQ，不能声称经验修复收益；没有任何结果会自动形成新颖性。

强基线仍应冻结为官方 ParSEval 与 Polygon 的最终输出 NEQ 方法，保留 commit、完整 C、输入与资源计数。上述消融不能代替强基线比较；Polygon 的方言/完整约束准入和同预算实测尚缺，因此任何优于强基线的主张继续 NO_GO。XData 当前不作为已准入实测基线。

## 独立来源、成本与停止线

需要来自与既有 BIRD/1172 开发数据独立的原始公开查询对与完整 DDL。可先核对 Polygon 论文使用的 LeetCode 原始查询对 artifact；这只是候选来源，不是已取得、已合法重放或已确认有此结构的新案例。禁止自行把 >= 改成 > 后称自然缺陷。[来源说明：Polygon §6](https://arxiv.org/html/2504.06542v1)

未来预案：固定一个 artifact commit 后，最多只读前20个确定排序的来源记录，先按来源/问题/模式和既有清单去重，再做结构准入；所有缺 DDL、不可解析、约束不全、结构不符或语义不明记录保留分母。目标仅两例、不同问题：一例外部开发、一例交另一任务封存为独立测试。封存分配在运行前固定，作者不得依据结果挑例。找不到两例就停止，不扩大搜索、不造例补齐。已有1172及反复开发集永不升级为新 test。

此预案尚未执行、未形成测试集，也不是启动授权。若另行决定验证：两例×两消融臂，最多4次求解、每次5秒、总 solver timeout 预算20秒；整个串行 pilot 父进程墙钟上限90秒，自身累计 CPU 上限60秒，1GiB采样停止阈值（允许超冲）、50ms名义采样、单科学进程、0重试。检查新的机器/unrelated_project状态与独占锁；不可沿用旧负载读数。记录 SAT/UNSAT/unknown/timeout、准入失败、合法复核失败、实际调用/检查次数、CPU/墙钟/RSS及候选数。此成本只覆盖目标消融，**不含且不能伪称完成官方强基线运行**。

## 原回放错误与审核边界

原 `science/RESULT.json` 的 `ERROR_NOT_ALGORITHM_FAILURE`、traceback、时间线均保留。官方 disprove 已返回 EQ 后，我方回放用 `Patient` 索引规范化为 `patient` 的快照，导致 `KeyError('Patient')`。这是 Python 映射大小写问题；SQLite 标识符解析不能用该大小写敏感字典索引替代。先前独审只对自己读入快照的名称解析作修正，并复算既有数据；未重跑生成器。该错误不能导致更早的基线 EQ，也不能悄悄把原运行改写为全程无错。

之前独审仅覆盖原运行和保存数据库。本文件是新的作者静态分析，其单独审核另存，不继承原独审背书。历史第三方 raw/native 恢复 `BACKUP_BLOCKED` 与研究源 `DATAHUB_REGISTRATION_BLOCKED` 仍保留；本包作者成果的私有备份单独核验。
