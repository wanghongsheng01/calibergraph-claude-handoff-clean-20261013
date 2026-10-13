# 02 轻量融合原型：实现前方案

状态：**历史备选草案，已被父任务选定的更小范围覆盖；本文的60秒预算和多组件搜索方案均不构成执行授权。** 当前唯一已准备的可执行依赖门是 `official_smoke.json` 与 `../code/official_smoke_worker.py`：6组原pair、完整官方operational C、每表恰2行、总CPU≤10秒、wall≤25秒、RSS≤256 MiB、单worker，且必须由父进程强制监控RSS及wall；本任务尚未执行目标。依赖门之后再决定同一合法候选池的查询感知排序与官方fallback，强简单baseline共享该池；不先实现下述其余组件。原始材料为01冻结的6组12条 development SQL及完整schema/C；01文件不改。所有新机制均按已知技术融合处理，不作新颖性主张。

## 推荐范围

推荐先做 **SQLite 目标的有限域数据库反例搜索**，官方 VeriEQL parser 作为双方共享的前端和特征来源，原SQL由同一个 SQLite 引擎执行。明确称“复用官方 parser 的有限域 SQLite 搜索器”，不冒称复现了完整 VeriEQL symbolic evaluator。官方 `Scope.analyze/visit → compare` 另有真实可运行入口；若要比较其 solver，必须单列语义轨道，不能直接把其数学/方言判定和 SQLite 反例混算胜负。

共享前端只做忠实解析和静态特征记录，不调用旧 aggregate recognizer 或 v5 INT-only bridge。所有臂保留完整schema、完整C、原SQL、同一有限数据库宇宙和同样的CPU配额。没有找到反例只记预算内未发现；仅对确实穷尽的登记宇宙写 finite-universe exhausted，不写任意SQL等价。

## 官方真实入口与现成依赖

旧根 `today_20261011/runtime_v3/runtime_paths.json` 已给出官方源码、Z3 Python binding、support、9个依赖根与 `prepared/native/libz3.dylib`。原源码commit `3b99928bf976c11cb59c9db6a177adba21f75798`，当前native期望4.12.0.0；历史原native pin仍是UNKNOWN，不能改成完全原装复现。metadata/hash probe不导入任何目标，报告存在不等于ABI新验证。

官方 `sources/verieql_v1/__main__.py:7–15`：

```text
Environment → 每张完整物理表 create_database
→ add_constraints(原始完整constraint JSON)
→ save_checkpoints → analyze(原SQL1, 原SQL2)
```

`environment.py:860` 调官方parse；`:865–895` 调每侧 `Scope.analyze/visit`；`:942–952` 构造完整合同下的反等价公式并 `check()`。官方不是只能SUM/COUNT，也不是v5窄bridge。官方当前没有先验完整C可满足性检查（因此不能把矛盾C下UNSAT当有意义成功）；`add_constraints :779–782` 只是累积DBMS_facts；`reload_checkpoints :813–830` 会solver.reset，不是incremental IC API。新增早剪枝须计为新原型代码，不虚称复用现成官方增量算法。

## 必须先决定的合同语义

建议首轮固定 **OFFICIAL_OPERATIONAL_IC_V1**，即保留原始C并按锁定官方实现的精确定义解释。独立轻量验证器必须模拟以下语义，且以完整schema/C hash绑定。该名称只指当前编码，不代表自然题目意图已经核实。

| 节点 | 当前官方编码 | 对6组输入的影响 |
|---|---|---|
| primary | 所有键分量非NULL、组合键唯一 | dev01 EMAIL仍可NULL；ID不可NULL |
| foreign | 每个源值必须匹配某目标值，双方非NULL | dev03–06外键源不能NULL；dev06 BOXES必须匹配CHESTS |
| gte(col,0) | 每行非NULL且≥0 | dev03经验值、dev06四个数量字段均非NULL |
| neq(colA,colB) | 两列全部行的Cartesian product逐项非NULL不等 | dev02两列取值集合必须不相交；IN/self-JOIN匹配被合同排除 |

源码：`environment.py:627–656,695–750` 与 `utils.py:42–46`。这**不是**通常 SQL nullable FK、允许UNKNOWN的CHECK或同行neq。不能用dev04 NULL外键制造“满足官方C”的NOT IN反例。另一种常规SQL解释只能作为显式独立语义控制；没有依据时不能偷偷把它当原合同真值。若父任务不接受此operational profile，应先处理合同语义而不是直接跑性能。

`create_database` 在`:518`建立恰好n行，`:584`约束每行不删除；官方CLI只跑每表相同的正n。小有限域和各表0..n向量是02额外限制，须登记；不能说官方原先就覆盖它。`NULL_ratio=0`不保证所有列非NULL，`test_dbs`不接受None，不宜直接拿它灌入可空候选。

## 可比较的强简单baseline

推荐 B 为 **通用有限域CSP枚举+增量forward checking**，不是先随机填满再后验检查C：

- 相同预先登记的每列有限域、每表0..2行（首轮），按主键排序后的唯一数据库表示；未引用字段仍显式赋值并计入宇宙。NULL仅在完整operational C允许时保留。
- 预先按单列C过滤值；维护单列/组合PK已用键集合；FK源值用已声明目标值及剩余目标容量作forward checking；全交叉neq维持两列已用值集合互斥；发现必不可满足立即截断。
- 同样的最小剩余值/依赖顺序启发式；同样预编译SQLite建表/插入语句、复用连接、事务回滚和查询进度中断。不能让融合臂获得这些基础优化而baseline被故意削弱。
- 每个完成候选仍经独立完整C检查及原SQL双侧执行；只有完整C成立且两边都RETURNED并 bag结果不同时记反例。SQL错误、NULL/类型边界和资源停止全部记分母、计成本。

原始SQL的ORDER BY保留不改；比较器明确为输出bag，dev02的一侧ORDER BY不用于构造胜负。dev01有裸列GROUP BY的SQLite特定行为，固定SQLite版本及装载顺序，反例附反向装载复核；顺序依赖就记该范围的实现差异，不升格跨方言gold。dev03整数除法差异单列为已暴露dialect control，永远排除主要反例产出/优势计数。

## 最多三个可移除组件

**C1：编译后的依赖构造。** 对本六组的无环跨表FK，枚举父键后直接枚举合法子引用；PK/交叉neq使用专门的关系域迭代器，替代B的通用逐变量forward checking。必须证明/核对两者覆盖相同登记合法数据库，不能固定一个父键或只留一个witness。公平基线本来就早检查，C1测的是不同实现的节点/CPU成本，不把“避免全后验垃圾候选”作为创新。

**C2：查询特征候选排序。** 从双方官方AST共同提取NULL-sensitive COUNT、group collision、重复匹配、outer/anti支路、阈值邻域，生成一个确定且可回退至B枚举的优先顺序。它只能改变搜索顺序，不能删合法候选或偷看哪个原pair已产生反例。完整宇宙与预算相同。所有开发材料均已暴露，结果只属于开发诊断；只有dev01较早出现反例不会被写成自然缺陷泛化。

**C3：保双查询差异的依赖感知缩减。** 在公共反例池上比较B的强简单ddmin与依赖闭包排序的ddmin；每次接受删除/值简化都要求完整C成立且原SQL仍不同。不能按单查询存在witness随意删行。两臂允许相同的删除子集/值简化宇宙；C3只改候选顺序与检查缓存，不把更大操作集合偷偷只给一臂。无反例时该阶段记NOT_APPLICABLE，不能当零成本胜出。

缩减与搜索分开计分：缩减不能作为“更快找到反例”的证据，搜索臂不能因为各自产出的初始反例大小不同就直接比较缩减速度。首轮如果没有公共真实反例池，C3保留未运行而不是临时制造有利样本。

## 单次资源预算与矩阵

首轮不排大队列、不重复随机种子。建议分两段，一旦上段不足即停止后段并保留状态：

1. 一次共享官方前端预检：最多6 CPU秒、单worker256MiB、12条原SQL；不做solver。若导入/解析失败，逐槽保留并停止依赖该前端的性能比较。所有臂都使用同一份通过检查且绑定hash的AST，成本作为共享预处理单列并给每臂完整端到端摊入规则。
2. 一个纯标准库+SQLite worker顺序跑6组×4搜索臂（B、C1+C2、仅C1、仅C2），每格最多1.5 CPU秒、32MiB SQLite soft heap建议值、worker硬RSS128MiB/外部上限256MiB；搜索共≤36 CPU秒。每格最多256个完整合法候选；达到候选或CPU界均记截断，不得称穷尽。
3. 缩减≤6 CPU秒：只用上述全部臂的公共去重反例池，同一起点比较ddmin/C3；每份最多32次合法性+双SQL重放尝试。无可用池则不运行。
4. 留12 CPU秒给父监督、冷启动、日志、异常回收、最终只读核对；总启动前登记60 CPU秒硬上界及总墙钟90秒，至多一个worker同时活动。若共享前端超过预计或RSS不可可靠读取，则收缩后续格数并明确NOT_RUN，不能超支补齐。

这是上限分配，不是性能承诺；实现时以父子累计reaped CPU和实时RSS为准。每次失败、拒绝、超时、前端准备、候选构造、完整C复核、SQL运行、反例重放、缩减、清理都计入日志。不同臂的有限预算prefix可不同，但登记候选宇宙必须完全相同；为检验C1没有丢候选，另用不耗SQL的极小子宇宙完整枚举对照（占上述预算，不另开队列）。

## 结果指标与停止条件

逐格记录：源hash、前端hash、合同profile、列域、行界、arm组件、尝试部分节点、剪枝原因、生成/验证的完整合法候选数、SQL失败数、首次反例CPU、总CPU/墙钟/峰值RSS、是否穷尽、反例原DB及两侧结果、重放状态。只有同6组登记范围内的描述性对比；dev03单列，不展示掩盖它的汇总“胜率”。没有差异、比B更慢或剪枝数无差别也是有效结果。

若完整C解释仍不一致、同宇宙核对失败、某组件只能靠删约束/删列/改单边SQL生效、只有dev03获益、或新增组件每次仅改标签而没有可测执行路径，停止融合效果主张，提交失败/无收益结果。已知构件的拼接在此规模没有科学新意保证。

## 等待父任务决策的具体选项

推荐采用上面的 **OFFICIAL_OPERATIONAL_IC_V1 + SQLite有限域搜索**，只实现C1/C2搜索及准备C3接口，先做一次≤60 CPU秒诊断。如果父任务更希望检验完整官方symbolic comparator，应另起同约束有限域的official基线轨道，先用一组N1确认256MiB下可运行，再分配预算；不能把两条语义轨道的结果混合排序。本文件不是运行授权替代，也不预先声称实现已经完成。
