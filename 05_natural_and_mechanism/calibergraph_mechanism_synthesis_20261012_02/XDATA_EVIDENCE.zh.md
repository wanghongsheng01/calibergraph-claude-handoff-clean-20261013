# XData / EvoSQL 定向机制证据

2026-10-12；**READ_ONLY / NOT_RUN**。只读指定旧审计、官方论文、固定版本元数据与源码文本；未运行 SQL、SMT、parser、JAR、实验、安装或构建。未修改旧 freeze、未提交/备份，由根任务统一归档。`datahub list` 未见适配这些公开研究源的通用模块；本轮依父任务范围不修改 DataHub，登记缺口延续。所有实验数均是作者报告，非本地复算。

**判断：不推进“ParSEval 覆盖后，对两查询差异定向补一个约束/目标”作为独立新方法。** 它的核心目标已有直接先例。ParSEval 与特定后端的组合可以是实现方案，但还需要独立的机制贡献和未被有效基线解决的实例；当前证据不满足。

## 一手机制与证据边界

- **2011 论文主张**：输入单 query，产出合法数据库以杀死指定 mutation 空间；非空覆盖不足。已将定向杀 mutant 编成约束，用 CVC3 求值；问题含指数多 join-tree mutations，用少量数据覆盖。范围有明确限制。见[官方论文 PDF pp.1–2、§I–II](https://www.cse.iitb.ac.in/infolab/xdata/xdata-icde2011.pdf)。因此“比非空多一个区分条件”的思想至少不是新的。
- **2024 v1 论文主张**：复杂嵌套/相关查询是旧架构瓶颈；结果表、CNT 重数、去相关、Z3 是解决手段，非神经分布学习。§3.5、§5.2：非空后按目标节点改约束并传播差异；§7：`∃t: CNT_Q1(t) ≠ CNT_Q2(t)`，在 C 下有界求 witness；UNSAT 可能仅 bound 不足。§9 表2：378/407（XDataN）、244/407（旧版）、230/407（VeriEQL）、320/407（手工数据）。表3相关子查询79/80。**§7明确该pair方式未来待评测**；上述数字不能归给native pair合成。§9.2只有展开量词对照的定性描述，无详细消融表；整系统比较不是CNT/去相关的隔离消融。见[§3.5、§5、§7、§9及附录A](https://arxiv.org/html/2409.18821v1)。
- **我的解释**：非空条件 `Q(D)≠∅` 只保证执行路径上有结果；区分目标要求固定观察契约下 `Q1(D)≠Q2(D)`。例如原创教学例 `x>10` 与 `x>=10`：`x=11` 能令二者非空却不能区分，`x=10` 才能。JOIN、聚合、DISTINCT 可能掩盖局部变化，所以“某节点不同”也不自动推出完整结果不同。这个解释说明候选目标的必要性，不证明它的新颖性。

## 固定代码证据

本轮补齐了旧审计未锁定的 XData SHA：[`a86031197fd1b572bd7782431331e8cb15554f88`](https://gitlab.com/xdata/xdatapublic/-/commit/a86031197fd1b572bd7782431331e8cb15554f88)，API记录提交时间2024-11-24。[官方 commit API](https://gitlab.com/api/v4/projects/xdata%2Fxdatapublic/repository/commits/main)；本轮读取时 main 指向它，不能称论文发布快照。

| 静态事实 | 固定锚 | 能支持什么 |
|---|---|---|
| `prepare_input` 拷贝 DDL/query/mutant；`run_tests` 启 JVM 调 `test.RegressionTests.main` | [execute_tests.py L8–31、L34–55](https://gitlab.com/xdata/xdatapublic/-/blob/a86031197fd1b572bd7782431331e8cb15554f88/xdata/execute_tests.py#L34) | 公开入口确实接收两侧；没有证明 mutant 直接驱动底层合成 |
| `xdata/jars/xdata.jar` Git blob=`05a92c0187e2ddccdc6f3fb332f3d4be9c991c9a` | [固定tree API](https://gitlab.com/api/v4/projects/xdata%2Fxdatapublic/repository/tree?path=xdata/jars&per_page=100&ref=a86031197fd1b572bd7782431331e8cb15554f88) | 锁定仓库对象；不是下载校验所得SHA256，也未读/运行JAR |
| 同目录有jsqlparser 0.9.7-SNAPSHOT与4.3等JAR名 | 同上 | 不能拿v1附录A写的jsqlparser-5.0直接断言此artifact版本；类加载实际选择未知 |

核心Java函数 **未取得源码核实**。`generateDatasetsToKillMutations`、`generateDatasetForNonEmptyDataset`、`generateConstraintsToKillMutations`、`generateDatasetForSpecificMutation`、`cutRequiredOutputForSMTWithAPI` 是 **v1附录A的作者实现说明**，不能写成“已静态审源码确认”。代码许可、核心JAR与论文版本映射仍未确认。终端`git ls-remote`因DNS失败；网页API可读，不作工具能力失败。

## 官方失败线索：真实日志，不升格为机制结果

以下均来自该固定SHA的[作者XData-BM结果文件](https://gitlab.com/xdata/xdatapublic/-/blob/a86031197fd1b572bd7782431331e8cb15554f88/results/XData-BM-mutant-result.out)；文件行号按1开始。日志状态不是本地执行证据，也没有逐例根因、seed、完整产出/solver日志。

| 线索 | 官方状态与定位 | 当前可作的判断 |
|---|---|---|
| Q14，按dept_name分组时 `count(id)` 改 `count(dept_name)` | `NotKilled`，L81 | DDL中id为PK、dept_name可NULL；差异与NULL计数相关，非单纯非空。根因可能是约束生成、取值策略或实现问题，尚不能命名为算法缺口。 |
| Q17，从按id,name分组改为只按name分组 | `NotKilled`，L98 | DDL的name不唯一；需要同name多id使组大小改变。是已有group-by mutation目标域，不能包装成新类型。 |
| Q26，FROM子查询的natural full outer join变体 | `Unsupported`，L130 | 明确排除出有效方法失败。 |
| Q8，前一层改LEFT JOIN、随后INNER JOIN course | `NotKilled`，L59/L61 | 我的静态语义判断：后续course匹配可淘汰NULL扩展行，局部改动可能等价；不得把NotKilled全算漏检。 |

DDL核查见[student L60–68、instructor L24–32](https://gitlab.com/xdata/xdatapublic/-/blob/a86031197fd1b572bd7782431331e8cb15554f88/benchmarks/XData-BM/DDL.sql#L24)：name NOT NULL但非唯一，dept_name nullable且为可空FK。本轮没有构造或执行fixture，因此不新增test。另有论文报告的solver timeout类，可成为成本瓶颈线索；但公开逐例根因不足以建立“支持范围内、合法C、非等价、无实现bug”的可复现失败类。

## EvoSQL 只保留直接相关先例

**论文摘要**报告随机、偏置随机、GA三种对照；GA用执行计划fitness，2135条查询、98.6%完全覆盖是作者结果。[官方元数据/摘要，ICSE2018 pp.1220–1230](https://research.tudelft.nl/en/publications/search-based-test-data-generation-for-sql-queries/)。这是覆盖证据，不是pair区分率；全文旧审计403，本轮不冒充逐节重读，也不称三方案比较为完整机制消融。

**本地静态源码复核**属于 `5a90e4d4a360642c160013a049d8532c43962c3c`，不是ICSE tag `1015196397e376deb203c0e2ee6dc019be289613`：

- [`StandardGA.calculateFitness` L212–239](https://github.com/SERG-Delft/evosql/blob/5a90e4d4a360642c160013a049d8532c43962c3c/ga/src/main/java/nl/tudelft/serg/evosql/metaheuristics/StandardGA.java#L212)：清空/插入fixture，instrument执行目标path，再取fitness。
- [`Approach.hasOutput` L116–143](https://github.com/SERG-Delft/evosql/blob/5a90e4d4a360642c160013a049d8532c43962c3c/ga/src/main/java/nl/tudelft/serg/evosql/metaheuristics/Approach.java#L116)：实际executeQuery并res.next检查非空。

因此“利用真实执行反馈搜索联合条件”也已有先例。搜索未找到不等于UNSAT；该目标本身不保证区分两个任意query。原C提取不完整的旧静态审计仍保留；不能用删C后的覆盖率作本任务有效胜利。

## 作者侧短结论

当前应否决泛化的“覆盖+差异目标”创新表述。若保留研究候选，必须先给出一个具体机制为何优于已有目标约束/反馈搜索的可证伪解释，并在有效基线、原SQL、完整C与完整观察契约上体现；官方不支持项、实现bug、未运行样本都不能充当此证据。任务给定状态保持：Discourse #3 fullC NEQ已被ParSEval解决；GitLab #47 fullC非空已解；50source仅1 eligible / 1 solved，49 NOT_RUN，0新test。本轮不改变分母、不增加实验结论。
