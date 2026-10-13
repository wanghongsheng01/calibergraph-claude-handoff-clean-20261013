# CaliberGraph：强先例机制核查与一个候选的否决

2026-10-12。**本轮仅定向文献、固定源码和旧结果分析；实验 0，新增独立 test 0。** 作者分析与独立审核分开保存。范围是 ParSEval、Polygon、XData 及直接相关 EvoSQL，未重开已否证方向、扩大扫描或启动数据库/求解器。

**判断：本轮不把“覆盖后补两查询的聚合差异目标”交付为新方法。** 这不是从“旧实验没有赢”推出研究无望：新的负证据是该目标与主要搜索手段已有直接先例，而唯一具体的新失败线索还没有证明当前版本的机制缺口。可以吸收以下设计作为强基线；当前没有应交 high 实现的科学实验。

## 机制比较：论文证据与本地核查分开

| 方法 | 原问题、机制和分布选择 | 原论文局部证据；本次核查边界 |
|---|---|---|
| ParSEval | 让数据库触发计划的正、负分支，再在真实后端比较查询。混合具体/符号执行降低表达式复杂度；不是学得的生成分布。 | 作者 Table 5：PositiveOnly / OneNegative / 标准 / Complete 分别区分 48/53/58/58%，均时 4.92/6.11/7.62/20.83 秒。扩大组合覆盖未在该评测增加区分率。Sym→Hybrid 表头是 **support** 49→98%、超时 222→30，不能写成 NEQ 准确率。旧论文不是当前 CSP 版本的逐组件消融。[论文 §4.3、§5.3–5.5](https://dbgroup.cs.tsinghua.edu.cn/jnwang/papers/vldb2025-parseval.pdf) |
| Polygon | 完整有界编码代价大；为各算子选下近似，跨查询共同编码输出 property。用冲突核定位需调整的算子，在下近似格中搜索并学习冲突；全族覆盖是给定边界及支持语义内的性质。 | 作者消融：暴力组合明显更弱；第二组除 MinUAsCover 外在 ER、D-50 接近完整方法，在 D-100 更差。不能据此宣称每个局部组件对双查询都有巨大收益。固定代码已存在 `Not(o1_eq_o2)`，并按冲突回退；未运行、未建立本任务 fullC 准入。[论文 §3、§4.3](https://arxiv.org/html/2504.06542v1)，[差异目标](https://github.com/polygon-sql/polygon/blob/5e18237394d025dbb805cf833b4f54c321470774/polygon/environment.py#L209)，[搜索/回退](https://github.com/polygon-sql/polygon/blob/5e18237394d025dbb805cf833b4f54c321470774/polygon/smt/formula.py#L129) |
| XData | 非空不足以杀 mutant；修改目标节点的约束，并使局部差异传播到最终结果。新版以结果表、计数和去相关处理复杂嵌套，不是训练一个取值分布。 | v1 §7 已写跨查询输出计数不等的有界目标，但明确待评测；不能把 §9 的 378/407 归给 native pair 模式。量词展开只有定性对照，没有完整隔离消融。固定公开 wrapper 接收 query/mutant，核心 Java 与论文映射未核实。[论文 §3.5、§5、§7、§9](https://arxiv.org/html/2409.18821v1)，[本轮源码和日志证据](XDATA_EVIDENCE.zh.md) |
| EvoSQL（邻近目标） | GA 用真实执行的路径 fitness 搜索，另有随机/偏置随机对照。 | 作者摘要的覆盖结果不等于任意 query pair 的区分率。静态复核 `calculateFitness`、`hasOutput`，未执行，也未读到完整论文消融；“增加真实反馈”不能单独构成新机制。[官方摘要](https://research.tudelft.nl/en/publications/search-based-test-data-generation-for-sql-queries/)，[源码证据](XDATA_EVIDENCE.zh.md) |

应吸收的是：有明确语义目标的低成本初始化、原输出契约下的差异检查、按冲突局部精化，以及把求解开销与生成覆盖分开计量。**这组组合本身不是贡献。** Polygon 的 nullable UNIQUE/完整约束适配仍有缺口，不能让它在被收紧或删减的 C 上失败，再算作新方法优势；相关静态限制见旧 [Polygon 审计](../calibergraph_strong_baseline_prep_20261011_02/literature/POLYGON_STATIC_AUDIT.zh.md)。

当前 ParSEval `88cfe245bcf249a5b0df561a6b09c116ff2a2896` 已对两查询分别生成并共同回放，已有 NULL/reuse/differ 目标、FK 闭包、候选行增长和覆盖保护。因此“双导向”“新鲜键”“再补一行”“保持先前覆盖”均不能作为本轮新增功能。这里的判断来自静态源码及旧成功记录，不把源码存在等同于任意输入正确。[双导向入口](https://github.com/sfu-db/ParSEval/blob/88cfe245bcf249a5b0df561a6b09c116ff2a2896/src/parseval/main.py#L68)，[取值目标](https://github.com/sfu-db/ParSEval/blob/88cfe245bcf249a5b0df561a6b09c116ff2a2896/src/parseval/speculate/speculate.py#L699)，[目标与覆盖保护](https://github.com/sfu-db/ParSEval/blob/88cfe245bcf249a5b0df561a6b09c116ff2a2896/src/parseval/generator/generate.py#L246)。

## 唯一候选卡：联合聚合差异补偿——否决其当前创新表述

**来源线索。** 冻结 ParSEval README 明确把当时结果中的误判归于 DISTINCT 聚合。它比“猜某类 JOIN 应该难”具体，但没有给出本轮已取得的逐例 fullC、完整查询、合法反例和失败调用链；不能归因成覆盖算法缺陷。旧论文另有 9 个 NULL 聚合漏检，并已提出 NULL 重数约束；它们不是新的待发明机制，也不能假定在 2026 代码中仍失败。[冻结 README](https://github.com/sfu-db/ParSEval/blob/88cfe245bcf249a5b0df561a6b09c116ff2a2896/README.md#L150)，[论文 §5.3](https://dbgroup.cs.tsinghua.edu.cn/jnwang/papers/vldb2025-parseval.pdf)。

**最小改动设想（未实现）。** 计划覆盖结束仍未区分时，把一组聚合输出的计数/去重差异作为共同约束，求合法数据库，再按原 typed bag/ordering 契约回放。原始可证伪预测是：在双方算子语义已正确、同预算的实例上，它能找到普通覆盖没找到的合法差异，或减少首个差异的总成本。

**否决依据。** Polygon 已有共同输出差异目标；XData 已有定向杀 mutation 与计数差目标。仅新增目标、将其接到 ParSEval 后面、增加 NULL/重复取值或让求解器多跑一次，都没有额外的机制预测。即使超过 ParSEval，也不能区分“新搜索算法有效”与“调用了已知更强目标/增加计算”。本轮尚未取得能排除普通语义修复、现有目标及现有搜索解释的局部残差证据；这是证据缺口，不代表已逐项排除所有残差。不能以尚未适配的 Polygon 代替公平强基线。组合方案的性能未经本轮实测，这个创新表述的否决不是性能失败结论。

要成为新方向，必须提出可独立检验的机制改动及额外预测，例如改变搜索空间、等价类表示或冲突复用规则，并说明相较现有目标求解为何少做哪些工作；这些只是示例，不是穷尽的创新类型。再让“取消该改动但保留同一目标”的消融检验它。当前尚无这样的机制，不以换名补齐。

## 这轮新证据留下什么，缺什么

XData 固定仓库日志还有 Q14 的 NULL 计数改动、Q17 的分组改动 `NotKilled`。这些是作者数据上的真实日志线索，但不是本地已确认非等价/已定位算法失败；Q26 `Unsupported` 应排除，部分 Q8 `NotKilled` 可能因下游 JOIN 消除 NULL 扩展而本就等价。详见 [定向证据](XDATA_EVIDENCE.zh.md)。它们是 mutation benchmark，不冒称新发现的自然应用缺陷。

下一步的最小缺失证据不是再运行旧 Discourse on/off，而是 **1 个固定版本、公开原始输入的已知漏检包**：两条原 SQL、全部 schema/C、绑定、dialect/观察契约、原合法反例（或完整 SQL/C 下可靠的数学非等价证据）、该版本逐阶段失败或实质成本记录。非等价证明本身不定位工具失败原因。优先取 README 对应的一个 DISTINCT 聚合记录；在这个包出现前不扩大采样。Issue #9 讨论区的作者曾指向 Actions，随后澄清人工标签的问题，最后回复已邮件提供；这既不是本轮持有人工标签的证据，也不能写成数据不存在。[完整讨论](https://github.com/sfu-db/ParSEval/issues/9)。本轮未下载大批 artifact、未联系作者、未获取邮件。

拿到包后仍须先区分：前端拒绝 → 工程准入；concrete/symbolic 语义错误 → 普通修复；真实 EQ/违法 witness → 排除；共同支持且有合法差异但未找到，或已有实质成本 → 才能讨论搜索机制。当前不冻结空壳实验协议、不把一个未定位的缺陷先宣告为方法贡献。若只修 bug、现有基线即解决，或找不到独立可检验改动，应停止该候选。

已有本地分母保持：50 来源中 1 个准入执行且被基线解决，49 NOT_RUN；独立新 test 0；没有新的 natural JOIN 开发/最终测试集。GitLab #47 的 fullC 非空成功与 Discourse #3 的 fullC 差异见证仍是旧开发证据，不再转称测试。此前 exact-live SMT 未找到 SAT 且有编码错误/超时，也不变为新方法需求。没有证据说所有其余来源都被解决。

本轮结论是 **REJECT_THIS_PROPOSAL / NO_IMPLEMENTATION_HANDOFF**，不证明所有未来方向不可能。独立审核另存；后续若上述证据补齐，再由父任务按 high 启动有限准入诊断。未修改原稿、旧冻结结果、unrelated_project；未启动科学进程。DataHub 通用公开 SQL 研究源登记仍为 `DATAHUB_REGISTRATION_BLOCKED`：缺少适配模块及本轮修改外部 canonical checkout 的授权范围；沿用旧阻塞，不碰另一个项目。

独立非作者审核结论为 **PASS，必需整改 0**；作者采纳三处不阻塞的措辞/证据一致性建议，未声称二次审核。见 [独立审核](INDEPENDENT_REVIEW.zh.md) 与 `AUTHOR_ACCEPTANCE.json`。独立审核访问 XData 原日志/DDL 返回 403，故这部分具体行未获二次确认，仍只作作者读取的线索。
