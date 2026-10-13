# DISTINCT 线索取证：取得具体官方漏检记录，根因仍未定位

2026-10-12。只读公开源、文本检索、ZIP/JSON 读取及哈希；**SQL/模型/求解器实验 0**，未安装、未联系作者、未读凭据、未修改旧结果或 unrelated_project。

**结论：值得后续一次有上限的 ParSEval 基线诊断；不构成新方法方向。** 已找到冻结版本上具体的官方 `EQ` 记录及原 SQL/完整模式，并可对该原输入给出静态非等价证明。没有取得作者原始见证或逐阶段轨迹，故不能把漏检归因于 DISTINCT、覆盖策略或求解成本，也不能说 Polygon/XData 已在此例失败。

## 找到的原始证据

README 中 DISTINCT 聚合误判说明由 [36cee474 的 README diff](https://github.com/sfu-db/ParSEval/commit/36cee4744f3eada41365a18c7ed63d84e7ebca77) 加入，直接父提交 `a48892ca` 尚无这段文字。当前冻结版本仍为 `88cfe245bcf249a5b0df561a6b09c116ff2a2896`。说明没有列出具体 query ID，因此下面是从同版本结果中找出的匹配线索，**不是作者明确标注的“该说明所指案例”**。

| 项目 | 已取得的证据 |
|---|---|
| 官方运行 | [BIRD SQLite run 37547685455](https://github.com/sfu-db/ParSEval/actions/runs/37547685455)，job `112555512740`，head 与冻结 commit 完全一致，branch=`dev`。 |
| 结果包 | artifact `11452059162`，87,085 字节；下载 SHA-256=`dc967b50b776d01faf4177f406fb25618218ed0d36bd893ef64797008010c5cf`，与 API digest 相同。仅下载这个 SQLite 包，未下载 MySQL 分片。 |
| 具体记录 | `thrombosis_prediction/1172`，JSONL 第 1173 行：`EQ`，作者 end-to-end=2.727 秒，reason/results 均为 null；独立读取的该 job 日志也有同一结果。时间是作者运行记录，非本地实测。 |
| 原 SQL | [gold](sources_local/case1172.gold.sql)、[predicted](sources_local/case1172.predicted.sql)，均逐字取自结果包。两侧都有 `COUNT(DISTINCT T1.ID)`；实质差别为 `T-BIL >= 2.0` 与 `> 2.0`，另有谓词次序变化。未编造或改写 SQL。 |
| 模式 C | [完整三表 DDL](sources_local/case1172.full-schema.sql)，按官方脚本从同 commit 的 [schema.json](https://github.com/sfu-db/ParSEval/blob/88cfe245bcf249a5b0df561a6b09c116ff2a2896/data/sqlite/schema.json) 的 `thrombosis_prediction` 项以 `;\n` 拼接。保留 Patient、Laboratory、Examination 的全部列、默认值、PK/NN/FK 和级联条款，没有裁掉未被查询的表。 |

结果包共 1534 条；仅作字面筛选，含聚合 DISTINCT 的 138 条中为 NEQ 101、EQ 26、SYNTAX_ERROR 11。**26 个 EQ 不等于 26 个误判**：其中有字面相同、别名变化或键约束下合理等价的查询。不对其余记录作失败分类，也不扩展新数据集。选 #1172 是因为原差别及约束最便于核查，不是依据新运行的优劣筛选。它属于公开 BIRD 预测查询对，不冒称自然生产缺陷或独立最终测试。

## 非等价可确认到哪一步

**以下是本轮针对原 SQL/C 的静态数学反例构造，不是从作者包中找到的见证，也没有执行。** 取一条 Patient：ID=1、SEX='M'，其余可空列为 NULL；一条 Laboratory：ID=1、Date 为合法非空日期、T-BIL=2.0，其余可空列 NULL；Examination 为空。Patient 主键、Laboratory 复合主键与非空约束成立，两条已声明 FK 均满足；原 DDL 没有禁止该取值的 CHECK。原 gold 的聚合结果为 1，predicted 为 0。因此在公开模式允许的数据库域内，原查询对不等价。

这把状态从“README 泛称误判”推进到 **官方固定版本 EQ 记录＋原输入下可证明的漏检**。它仍不能说明工具在哪一步错失边界值。官方 [run_case 输出](https://github.com/sfu-db/ParSEval/blob/88cfe245bcf249a5b0df561a6b09c116ff2a2896/scripts/disprove_bird.py#L35)只保存结论、理由、截断的最终结果和耗时；本例 results=null，没有候选数据库、reached/covered/failed targets、CSP/Z3 请求或逐次阶段记录。可观察的阶段只有“整个 disprove 返回 EQ”；不能把它写成 parser 拒绝、SMT UNSAT，或 DISTINCT 语义已确定有 bug。README 的整体原因说明也不替代本例调用链。

## 对照先例与一次诊断的价值

Polygon 固定源码已有 [Count_Distinct](https://github.com/polygon-sql/polygon/blob/5e18237394d025dbb805cf833b4f54c321470774/polygon/visitors/expression_encoder.py#L99) 及其调用分支 L525–528，并以共同输出不等为目标。XData v1 [§4.3、§5.2](https://arxiv.org/html/2409.18821v1)描述去重后聚合与选择条件 mutation 的定向约束。因而本例的操作组合与边界差异已有直接先例；**没有证据表明它是这些基线未覆盖的新问题**。但也未做三表原 C、SQLite 类型和完整输入的共同准入及实测，不能声称两者已经在本例成功。

建议仅在父任务下一轮确认后做 **1 次基线诊断，0 次新方法实验**：原样锁定 #1172 两条 SQL、三表 C、当前 ParSEval commit；保持官方参数（solver 5000ms、generation 每查询 360s、后端查询 15s），外加整次诊断 **60 秒 wall / 60 CPU 秒 / 1 GiB RSS、单 worker** 的保护上限。这个外部上限不等于作者完整预算；触发即记 RESOURCE_STOP/CENSORED，不能算复现 EQ。运行前负载门槛 load1≤2、可用内存≥3 GiB，不能满足则不启动、不排队、不重试，避免影响 unrelated_project。

一次诊断中仅调用一次官方双导向 `disprove`；被动记录阶段、官方回调候选及成本，不增加候选回调、不改目标或预算分配。数学反例只在独立回放控制中核验，不作为生成器种子。成本包含 lowering、CSP、Z3 与 SQLite；不能只计 Z3 次数。若 NEQ 成功，记录旧漏检未重现并结束；若复现 EQ，再依记录区分普通实现缺陷与搜索缺口；若不支持、错误或触发保护上限，停止归因，不加 seed/预算追结果。现在**未写运行器、未执行、未创建任务或队列**。

## 已查位置与未取得项

已查：GitHub 全部返回的 12 个 issue/PR 摘要及 issue #9 的全部 3 条评论；最新 30 个 commit、README 路径最新 20 个 commit及说明引入 diff；冻结完整 tree；测试/相关 docs；官方两类 workflow、同版本 SQLite job 日志和一个结果 ZIP、MySQL artifact 元数据第一页；10 个 release 元数据；2025 论文的 artifact availability 和失败讨论。论文指向仓库，已查位置未发现独立的 DISTINCT 回归补充包。issue #9 最后说已邮件提供人工标签，不能称其不存在，也未访问邮件。完整位置、哈希与边界见 [EVIDENCE.json](EVIDENCE.json)。

尚缺作者逐例标签映射、原始见证、逐阶段轨迹，以及三工具同原 C 的实际支持/行为。**已有证据足够提出一次受限诊断，不足以宣布强基线算法失败或新科学贡献。** 本轮取证到此结束，不重开被否决的组合机制。
