# CaliberGraph 第四轮独立审查

**结论：可采纳本阶段严格限定的问题证据；方法仍为 UNCOMMITTED，研究继续。** 本结论是阶段主张审查，不是论文录用判断，也不授权扩展实验。

审查作者报告：`FOURTH_ROUND_REPORT.zh.md`，SHA-256 `67699010beb50164542b16d821dc7a631b097f03716ddeeb00a2a05342afb859`。作者重计：`analyses/pilot_recount.json`，SHA-256 `3629e64101ce66f2f47e2b8a9762890a470902c400fc67a699745c9dd1df44b7`。全部实际审过的作者文件、审查方式和 SHA 见本目录 `REVIEW_MANIFEST.json`。

## 审查范围与独立性

审查者未参与作者协议设计、编码或运行；只写本独立审查目录。使用 `paper-review` 的主张／证据／判断分层。读取两版协议及冻结清单、七份当前 Python 源、启动例外及标准库诊断、两批保存工件、作者报告与重计；独立文献辅助审阅八份 literature 文件并复核一手论文。没有导入或执行作者代码，没有运行 SQL、SQL parser、SMT parser、solver 或 DBMS，没有访问 reserve、test、凭据或 unrelated_project 进程。

`audit_saved_evidence.py` 是审查者自己的标准库脚本，仅对保存的 JSON/text 做哈希、结构、袋输出、主键值和数值对账。其通过结果 `saved_evidence_audit.json` 属于**保存证据复算**，不是独立科学复现实验。原始公共 JSONL、第三轮数据与全部上游运行时文件未重新打开；861→868 是冻结清单全映射比较，不能冒称再次独立重哈希了全部外部依赖。作者关于未修改系统、未接触最终测试及远端备份的全会话断言，也不由本次文件审查认证。

## 关键主张与证据

| 主张 | 独立审查证据 | 判断 |
|---|---|---|
| N=5 全 NULL CLASS 构造实例区分原 pair | `runs/boundary_pilot_02/case_08/results.json` 中 Q1 为 `[[null]]`、Q2 为 `[]`，袋重计一致；原查询字节哈希与协议相同 | 可采纳为保存的 SQLite 3.53.3 观测 |
| N=1…4 两种 fixture 均相等，N=5 非空对照相等 | 五个 concrete results 的全部十个 fixture、20 个原 query 输出与事件核对通过 | 可采纳；不是对所有数据库的穷举 |
| 完整显式 C 未删减 | 保存 source 只有 `primary(COURSES__STUDENT)`；所有 fixture 的 STUDENT 非空且互异；schema/C canonical SHA 与协议一致 | 可采纳为该显式 C 的检查；不能认证自然业务 C 完整 |
| 官方运行是 exact N | 五份 `contract_assertions.smt2` 各有恰 N 条 `(assert (not (DELETED ti)))`，原 schema/C 调用保留，完整 C 模型含 N 行 | 可采纳为本冻结路径的 exact N；不能称 ≤N |
| 官方查询结果 | 五个 official results 的唯一 solver call 是 `FULL_C_NONEMPTY_CHECK`；均 C SAT，随后 `CorrelatedQueryError`，query verdict 为 null | 仅可报告前端覆盖边界；没有官方查询等价或反例 verdict |
| 原始分类与派生解释相容 | raw engineering/strict 均 `INCONCLUSIVE`；作者重计另设 `FRONTEND_CORRELATED_SUBQUERY_REJECTION`，原结果与 supervisor 内嵌副本逐字节/结构一致 | 派生标签可用，必须与 raw 类别同时保留 |
| 预算与分母守恒 | 两批保留相同十个科学 slot；首批 1 个 preexec 失败＋9 NOT_RUN，恢复 10 RETURNED；独立算术对账通过 | 不得将首批删除或把两批当 20 个独立科学 slot |

锚点：作者报告第 7–21、27、48–65 行；`code/pilot_common.py:75–150`、`concrete_boundary_worker.py:19–97,195–245`、`official_boundary_backend.py:300–408,417–475`；各 case 的 results、events 与 supervisor_receipt。

**两类模型必须分开。** 官方保存的 SAT 是 C 非空性的编码模型，VARCHAR 仍是整数符号；此次模型 CLASS 也不是 SQLite 的全 NULL fixture。SQLite fixture 是独立手工构造的机制实例，不是该官方模型的解码回放。作者没有把它们合称一个被跨系统验证的反例，这一界限必须保持。官方前端已成功产生两份 AST，拒绝发生于相关子查询分析/作用域编码；不能简单改写成“SQL 语法错误”。

## SQL 语义纸面检查

【声称】作者报告第 21 行给出实例等价条件 `n_NULL < 5`。

【证据·静态推导】保存的原 SQL 分别为：

```sql
SELECT CLASS FROM COURSES GROUP BY CLASS HAVING COUNT(*)>=5
SELECT CLASS FROM COURSES AS CS GROUP BY CLASS HAVING
  (SELECT COUNT(DISTINCT STUDENT) FROM COURSES CP
   WHERE CP.CLASS= CS.CLASS) >=5
```

在报告明确限定的通常 SQL NULL／分组／袋语义及 STUDENT 非空互异主键 C 下，对任意非 NULL 班级组，相关等号选出同组所有行，`COUNT(DISTINCT STUDENT)=COUNT(*)`，所以两查询同时输出或同时不输出该班级。NULL 组的普通等号不为 TRUE，相关子查询计数为 0，Q2 不输出 NULL；Q1 当且仅当该组行数≥5 输出一行 NULL。两查询均有外层 GROUP BY，每组至多输出一行，无需给 Q2 添加 DISTINCT。因此两者袋相等当且仅当 `n_NULL<5`。空库也满足该条件；少于五行不可能区分，而五个合法 NULL 行给出可达见证。

【判断】该推导支持本原 pair 在这些明示前提下的最小区分总行数为 5；强于五个样例的枚举结论，但属于静态论证。它不是官方 SMT 证明，不是一般 SQL 定理，也不是新算法。未知业务是否另有 `NOT NULL(CLASS)`；不能据此输出自然缺陷标签。

## 启动例外与资源账

【证据·保存工件复算】首批结束于 `13:28:33.193557 UTC`，`preexec_fn` 抛 `SubprocessError`；worker events/progress 不存在，阶段序列为空，结果为 supervisor 占位。仅从无日志不能排除任意执行，但结合 Popen 的 preexec 异常、冻结 `child_setup` 在 exec 前仅调自身优先级及资源限制、独立标准库 `setpriority` 拒绝证据，支持**已 fork、未 exec worker、零目标 SQL/parser/solver 执行**这一窄解释。

显式 amendment 在 `13:30:29.275365 UTC`，恢复 freeze 在 `13:30:46.021566 UTC`，恢复 batch 在 `13:31:01.347081 UTC` 开始。其时间次序和保存记录支持“首次失败后、首次科学执行前登记的一次例外”，不支持“原协议原本就允许重试”。两版 supervisor 的完整差分仅为 prior charge `1.0→3.408329`；两协议保留原 SQL/schema/C、N=1…5、concrete→official 顺序及所有数值资源限制。宿主执行审批由作者/主代理工具上下文报告，本审查未重做权限操作。

【判断】**可采纳这一次有完整保留、零目标执行依据且不放宽科学选择或资源的 prospective 例外**。它不形成事后重试惯例；首次失败仍必须报告。不得删除初次失败成本，不能重置分母，也不允许在看到科学结果后借同一例外继续重试。

| 成本组成 | 秒 | 性质 |
|---|---:|---|
| 首次失败批含原预检与收尾 | 1.408329 | 保守计费，含原预留 |
| 标准库诊断 | 1.000000 | 预留；保存 CPU 快照合计 0.089348 |
| 恢复冻结核查 | 1.000000 | 预留；保存 CPU 快照 0.116638 |
| 恢复父进程＋全部回收子进程 | 5.927557 | rusage 保存值的独立加总 |
| 恢复收尾 | 0.200000 | 预留 |
| 合计 | **9.535886 / 60** | 保守总账，不能称全部实测 CPU |

恢复批内 `4.429287 worker + 1.196587 monitor children + 0.301683 parent = 5.927557`。worker wait4 已包含在全部子进程 rusage 内，未重复加到总账。最大 worker CPU 0.923918 秒、生命周期 wall 0.975177750 秒、wait4 RSS 110886912 字节；十槽启动 load1 3.197265625–3.21484375，可用内存 32–33%。保存 guard violations 均为空；这些是本次观测和采样守卫，不等于精确硬 RSS 保证。60 秒账仅覆盖登记执行阶段及相应预留，不覆盖全部文献、写作与本次审查。

## 先例核查与新颖性界限

【证据·一手文献复核】独立文献辅助确认：[VeriEQL](https://arxiv.org/html/2403.03193v2) 的论文描述含从 1 增界与 up-to slots；[Polygon](https://arxiv.org/html/2504.06542v1) §3.3 与 Theorem 3.12 的完备性是相对其有界语义；[有限模型查找](https://arxiv.org/html/1604.08040v1) §5.2–5.3、§6 已包含基数区域与单射/满射不等式推导。普通 bound/shape/PK-FK 剪枝不能据本例重获新颖性。

[WeTune](https://ipads.sjtu.edu.cn/_media/publications/wetune_final.pdf) §4.2–4.3、[cvc5 getAbduct](https://cvc5.github.io/docs/cvc5-1.1.2/api/cpp/solver.html)、[CoVeriTeam](https://www.sosy-lab.org/research/pub/2022-TACAS.CoVeriTeam_On-Demand_Composition_of_Cooperative_Verification_Systems.pdf) 已覆盖约束枚举/消减、一致且充分的逻辑假设、类型化证据组合。它们不认证业务真值；接口兼容也不是跨前端语义等价。任何蕴含跳检仍须核清方向：从已证明 `C_proved` 的充分性迁移到 `C_new` 需要 `C_new ⇒ C_proved`。

[XData](https://arxiv.org/html/1411.6704v5) §5.3、§6.1、Appendix A 已覆盖 NULL/COUNT 区分造数、count 搜索和目标基数分配；[BAPA](https://people.csail.mit.edu/rinard/paper/jar06.pdf) §3.4、§6 已给基数公式投影/量词消去。它们足以阻止把本例一元 `n_NULL<5` 消元包装为新机制；**并不证明一般 SQL 聚合最弱合同 abduction 已被完整解决**。主键值擦除/重数恢复的当前窄例也可由既有 DISTINCT 消除、袋投影和基数具体化解释；跨表 FK、键比较、重复 join 的一般保真尚无此轮证据。

作者报告第 42 行新增 [XData 2024 复杂查询预印本](https://arxiv.org/pdf/2409.18821) 的 CNT／结果表／聚合与相关子查询处理，独立辅助已核对对应章节。正式版全文未审，不能将预印本限制或性能推给最终版本；此轮没有复现其代码或 benchmark。

【判断】允许否定**当前所述宽机制和两个窄候选的晋升**，不允许断言所有相关机制或整个研究方向均已穷尽。[Few Rows Tell Them Apart](https://arxiv.org/html/2609.09978) §7 仍保留阈值阶数问题；开放问题本身也不是本项目已经获得的新颖性。当前 `hypothesis=null`、`overall_research_terminated=false` 与证据一致。

[SpotIt+ v3](https://arxiv.org/html/2603.04334v3) §II/II-A 采用每表至多 K 行与 set equivalence，§V 的 K=5／600秒是实验设置，不能当 bag SQL 的完备阈值；§IV、Appendix A/B 的样例与 LLM 约束挖掘也不构成业务合同认证。§V-A 的编码覆盖仅及所评估预测子集，不能推出全部 SQL 覆盖。该一手复核进一步支持保留本轮 bounded／业务真值界限。

## P0／P1／P2 与主张门禁

- **P0：0。** 未发现足以推翻本次严格限定问题证据的错误或隐去的科学运行。
- **阻断 P1：0。** 官方没有 query verdict、没有业务 C 真值、没有方法创新/性能优势，是已正确承认的边界，不是在当前报告中尚未纠正的夸张主张。若以后跨越这些边界，它们立即成为 P1 主张阻断项。
- **P2：2，均已有报告旁注。** 恢复日志 `measurement_note` 写旧 `1.0s prior`，数值账正确为 3.408329；原 freeze prose 写七个 Python 文件，清单实际六个，恢复后七个。作者报告第 65 行明确纠正，保留冻结证据而非改写历史，当前不阻断。

允许写：

1. 原 `dev03_18` 在显式 PK 与所述 SQL 语义下存在五行 NULL 区分实例，匹配非空控制与保存记录一致；实例等价条件可静态推导为 `n_NULL<5`。
2. 本冻结官方路径在 N=1…5 对 C 均给 SAT、相关子查询作用域编码均拒绝、query solver 调用为零；这是具体前端覆盖边界。
3. 科学分母十槽完整保留，一次零 exec 启动例外独立登记并计费；保守执行总账 9.535886 秒低于登记 60 秒。
4. 当前机制不晋升，继续受先例和可证伪条件约束的探索。

禁止写：官方确认 N=5 反例；SQLite 回放了该官方 SAT 模型；query SMT 难度或随 N 的成本增长；速度优势／新方法胜出；一般无界 SQL 等价结论；自然业务缺陷；新独立 test；没有 fork 子进程；原协议无例外执行；所有研究方向均已被否定。不得以修前端、放大 COUNT 常数或筛选超时案例为本轮的新颖性证据。

## 12 项红旗快检

| 红旗 | 状态 | 本轮依据 |
|---|---|---|
| 1 摘要数字无表格支撑 | 未命中 | 作者报告表格、重计与本次保存证据复算一致 |
| 2 散文与表相反 | 未命中 | N=5／官方零 query check 描述一致；P2已旁注 |
| 3 最强基线缺席 | 无法判断方法优劣 | 本轮非方法赛跑；未来不得只比较冻结前端短板 |
| 4 换指标反转 | 无法判断 | 无方法排名／头条改进指标 |
| 5 额外预算伪称相同设置 | 未命中 | 不宣称同一竞赛，首次失败和监控成本保留 |
| 6 登记未交付未声明 | 未命中 | 十槽交付；官方 query artifact 因明确前端拒绝不存在，未冒充交付 |
| 7 便宜基线吃掉优势 | 无法判断方法优劣 | 没有已宣称优势；当前候选被既有简单机制否定 |
| 8 跨数据集方向相反 | 无法判断 | 只有已曝光单个 source pair |
| 9 verifier效果归给模型 | 未命中 | C checker、SQLite、官方模型明确分开 |
| 10 新模块删除不变/无消融 | 无法判断 | 当前没有获得新颖性晋升的模块 |
| 11 只报成功样例 | 未命中 | 首次失败＋九 NOT_RUN、恢复十槽及五前端拒绝均保存 |
| 12 受限结果外推 | 未命中 | 当前报告承认构造实例、业务合同、exact N与无方法结论 |

重要性：这个例子足以反驳“少量 exact2 快速检查能关闭所有研究”的推断，尚无代表性效应估计。新颖性：当前候选不成立为新机制。可信度：本阶段数字与工件内部一致，静态语义论证成立于明示前提。可复现性：输入/代码/结果绑定可追踪，但本审查不等于独立重跑或远端恢复验证。

后续任何科学执行应另立协议；本审查不替作者设计新算法或扩大运行。远端私有备份、DataHub 治理状态由主代理另行处理；本审查者未确认远端备份完成，不能在交付中替其背书。
