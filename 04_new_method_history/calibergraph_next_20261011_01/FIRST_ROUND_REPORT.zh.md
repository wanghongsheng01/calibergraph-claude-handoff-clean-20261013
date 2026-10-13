# CaliberGraph 新机制研究第一轮

**已实际启动并完成第一轮轻量诊断；结果是 HOLD，无可晋级的新机制。** 旧科学 NO_GO 不变，旧冻结目录与原稿未改。研究代码、数据注册、文献核验和理论否证由四个 `gpt-6-astra / ultra` 研究子任务承担；结果将另交独立任务检查，不把作者侧交叉核对称为独审。

## 真实的零 JOIN 原因

旧 48,910 查询槽的公开扫描根本没有调用 solver。完整分母是 47,431 INELIGIBLE、1,246 parser/AST 错误、189 前端不支持、38 UNKNOWN、6 eligible；6 个 eligible 全无 JOIN。不能由此推断求解代价导致自然 JOIN 失败。

首次拒绝标签有遮蔽：6,889 个 `unsupported_identifier` 全带顶层派生表；1,453 个 `unknown_table_or_repeated_relation` 中，1,441 个含显式重复基表。按既有 AST 结构计数，顶层单 SUM/COUNT 且有 JOIN/逗号 FROM 的槽只有 23 个；排除额外顶层子句后剩 12 个，其中 9 个有派生表，1 个有 LEFT JOIN/窗口，1 个为无 ON 自连接且含 DISTINCT/NOT IN。另一个直接基表标量 COUNT JOIN 使用字符串等值连接，被 INT-only 列检查拒绝。这是对冻结语料的诊断，不能外推全部真实 SQL 的分布。

更重要的是 query eligibility 不等于完整合同准入。旧 v5 的 `contract_reference.prepare` 要求完整 schema 全为 INT，且不支持 PK/FK 合同。删掉非 INT 列或 PK/FK 才运行，不能称无损适配。精确入口、行号、哈希与重叠特征分母见 [代码诊断](audits/code_diagnosis.zh.md) 和 [完整聚合](audits/code_diagnosis_log_aggregate.json)。

## 原公开查询开发集和实际短测

[开发集](data/development.jsonl) 固定 6 个来源组、6 个上游原始 pair、12 条 SQL，来自 VeriEQL 冻结 LeetCode 文件的指定 commit。原 SQL、完整 schema 和 constraints 保留；按来源与结构选择，未用 solver 结果选样，失败后不换样。另有 4 个来源组仅作有历史曝光的确认候选。所有这些都曾进入旧全量适用性筛查，**没有真正独立、未暴露的最终测试集，也没有确认自然缺陷 gold**。作者代理未打开本轮 reserve 文件。角色分离不是 OS 隔离。

自然查询与人工数据库分开记录。冻结后，对每个 pair 在空库和一个显式人工微型库上执行原 SQL，共 24 个查询尝试；完整源约束在这些无 NULL 输入上逐条检查，全部通过。结果：

| 诊断 | 固定分母与结果 | 能说明什么 |
|---|---|---|
| 旧完整合同入口 | 6/6 拒绝：4 INT-only，2 primary 不支持 | 原入口的语义支持边界 |
| SQLite 原 SQL 回放 | 24/24 返回，0 SQL 错误 | 这些固定输入上的绑定和执行可行性 |
| 输出差异 | dev_03 微型库中 AVG 为 1.5、SUM/COUNT 为 1.0 | SQLite 整数除法差异；不是上游自然缺陷标签 |

SQLite DDL 是回放适配，约束由另一个显式检查器在固定输入上验证；它不是通用源方言 verifier。其他输入相等也不证明 pair 等价。见 [预注册协议](protocols/natural_replay.json)、[冻结](protocols/natural_replay_freeze.json)、[逐次结果](runs/natural_replay_01/results.json)。

## 唯一方向的可证伪结论

没有重启 selector/product 或廉价 AND 控制。先例核对覆盖 VeriEQL、SpotIt+、Polygon、Few Rows、WeTune、OOPSLA 2018，并补查 PODS 2009、RATest。扩大 parser、加入约束/NULL、条件合同合成和普通来源缩减均不能独立作为贡献。文献范围、版本、定理条件和获取失败见 [先例报告](literature/primary-prior-art-audit.md)。

本轮只考察单个树形非键正 EXISTS、set 基表、键与无环 FK、外层 bag/count，无 NULL/SUM/HAVING/否定。对“每个外层键保留一个 witness 后同步克隆”的具体策略，预先固定 18 个合法微型数据库，Python 与 SQLite 双实现核对。原查询有 4 个区分实例，缩减后 4 个差异全部消失；同步单 witness seed 克隆分别给 1/1、2/2，仍不区分。最小例是一个 R 根、两个 W witness：EXISTS count=1，JOIN count=2；删一个 witness 后变为 1/1。**REJECT 这个策略**，不把人工例计为自然数据或泛化结论。见 [协议](opportunities/theory_protocol.json)、[冻结](protocols/theory_fixture_freeze.json)、[实测](runs/theory_fixture_01/results.json)。

同时，固定叶型可定义集合关系 `E(r)=π_r(W)`，加入 `W(w,r)→E(r)` 与 `E(r)→∃w W(w,r)`。在仅 `W.r→R.r` 的固定 schema 下，扩张保合法模型与两查询重数，依赖位置图弱无环；可归约到已有 sound bag-set chase。作者侧已交叉核对先例条件，因此**否定“该固定片段可判定／存在可计算完整界”作为新意**。这是纸面归约核验，仍需另任务独审；不声称已有新的实用紧界。一般树形和更多 FK 下的归约、紧闭式界均未证明，不强行增列第二方向。

## 成本、停止和后续边界

机器实际为 10 核、16 GiB，启动时压缩内存约 7.4 GiB。计算任务串行、nice=15、线程变量=1；每次运行前读机器负载，运行中仅观察自己的 worker RSS。自然回放整个子进程 0.186 秒、worker 峰值 RSS 28.6 MB；理论短测整个子进程 0.119 秒、worker 峰值 23.7 MB。另有静态日志聚合约 1.40 秒、数据注册约 0.477 秒，均单进程。数值分别来自回执，不把 wall、CPU、采样 RSS 和 worker 最大 RSS 混作同一口径。没有 SMT 队列、GPU、付费模型 API；没有调整或终止 unrelated_project。没有因果实验可以保证“零性能影响”，这里只陈述已采取的资源边界和实际轻量开销。

强基线、同前端要求、消融、成本、失败分母、停止条件及最终测试门写入 [科学比较门](protocols/scientific_comparison_gate_v1.json)。VeriEQL/Few Rows/Polygon/SpotIt+ 此轮没有完成公平性能复现，不能声称超越。朴素机制已被否定、固定叶型存在性被先例包含，所以按协议停止，不启动候选 solver，不开 reserve，不筛出胜出配置。

下一步是审核上述否证与证据，而不是扩队列。只有出现不被经典归约涵盖的明确新命题、同时证明合法性与双查询重数保持，并找到同域自然材料，才应新建后续机会版本。此轮不改原稿、不投稿、不读取凭据、不购买资源或更改系统安全。

所有交付目前仅在新目录。本轮未尝试远程备份；DataHub 已查目录但未修改新目录外的 canonical 注册。相关范围措辞见 [追加勘误](governance/registry_scope_erratum.zh.md)，不把旧任务的 no-upload 约束虚构为这次用户原话。
