# CaliberGraph / NL2Metric 本地研究修订交接

**科学投稿判定仍为 NO_GO。** 本轮已完成冻结 v5 的授权本地实验与失败保留，修复合同入口和状态记录，完成全量分母与独立回执复核；不能把这些工程修正说成新的科学贡献。DKE 仍是 CCF B 候选，不承诺录用，不同时准备旧拒稿 venue 或重复稿投递。最终稿件编译与页审回执见本文件末尾。

## 正式材料与谱系

AAAI32719 正式题名为 *CaliberGraph: Coverage-Caliber Witness Compilation for Multi-Business-Domain Governed Metrics*，官方第一作者 Hongsheng Wang、第二作者 Dazhen Deng，存档决定为 Reject。ICDE109 正式题名为 *NL2Metric: Production-Grade Business Metric Compilation with Scoped-Ratio Semantics and Cross-Caliber Routing*，Wang 唯一作者，存档决定为 Reject。两稿属于同一研究线，未拆成两篇改名并投。

SIGMOD847 为 *DELTAGOV: Typed-Delta Incremental Materialization and Version-Consistent Switchover for Evolving Governance Semantic Layers*；2026-10-09 官方存档为 Not Yet Available，未声称今日门户已更新。取得其正式主稿、补充、作者回复和包，未取得原真人 review 正文。作者已声明新贡献不重叠；实际正式材料与 13 个 Python 文件的逐贡献对照未发现本轮受限 SUM/COUNT 重数编码的同一算法、定理或核心结果。当前仅在该已观察边界内继续修稿，不以改标题消除重复，不借用 847 的贡献或实验。

来源：[最终谱系与旧分母索引](FINAL_LINEAGE_AND_LEGACY_DENOMINATOR.zh.md)、[贡献范围判定](overlap/OVERLAP_DECISION.zh.md)。本轮最后再次核对同一 15 份原稿/评审/原始包，全部 SHA 不变：[原件完整性回执](ORIGINAL_INTEGRITY_FINAL_V5_20261011.json)。

## 已实际完成与可审查证据

1. **合同与实现入口**：原始 literal-left 比较方向错误已有实际 24 格诊断；v5 在每一臂的公共入口用独立原 AST 解释与实际归一化编译做 base-only SAT、XOR UNSAT 审计，再检查完整合同非空与 exact rows。任何不支持的完整合同整体拒绝；SAT 再核原合同、整数安全域和原 SQL。支持边界仍是显式窄 AST，不认证任意文本 parser 或业务合同真值。冻结代码及逐文件 diff 在 [runtime_fair_v5](runtime_fair_v5/SOURCE_AND_DIFF_MANIFEST.json)。

2. **实际完整运行**：旧 session49665 不存在且只读进程核验无旧目标后，按精确缺口恢复；session92082 已返回 exit0，四段队列全部返回。六臂为 28 配置 × 6；差分为 28 × 2 查询 × 3 编码；配置来自 22 个逻辑控制，均为已暴露开发材料。所有臂、行数和查询重复均不是独立实例。[最终结果](experiments/FINAL_V5_EXECUTION_CUT.zh.md)、[逐槽/逐尝试账本](experiments/FINAL_V5_EXECUTION_CUT.json)、[措辞勘误](experiments/FINAL_V5_EXECUTION_CUT_WORDING_ERRATUM.zh.md)、[进程回收回执](experiments/CAMPAIGN_V5_SESSION92082_REAP_RECEIPT.json)。

| 阶段 | 已返回/选中槽 | 严格有效查询结果 | 有效类型拒绝 | 求解未知 | oracle 域未证 | 资源观测停止 |
|---|---:|---:|---:|---:|---:|---:|
| 六臂主实验 | 168/168 | 127 | 24 | 7 | 6 | 4 |
| 单查询差分 | 168/168 | 115 | 24 | 23 | 0 | 6 |
| SpotIt 受控引擎 | 28/28 | 21 | 3 | 2 | 1 | 1 |

表为互斥派生类别；原始 verdict 全保留。主实验原始为 78 UNSAT、52 SAT、8 UNKNOWN、6 域未知、18 合同矛盾和 6 不支持合同；差分原始为 120 UNSAT、24 UNKNOWN、24 合同拒绝。11 个资源停止均为 RSS 观测不可用，不能写成实际内存超限，不能以 worker exit0 升格。主成本共 169 次已启动尝试，旧52中断仍保留，完整 CPU/墙钟未知；checkpoint 只是下界。SpotIt 仅选 28 个 official 槽，另 140 注册臂明确未选；使用实际 auto set verifier 和受控合同适配，不是完整 SpotIt+ 重现。

3. **状态缺陷修复**：`pair_work_status` 残留已在 [隔离状态修复副本](runtime_fair_v5_statusfix/SOURCE_AND_DIFF_MANIFEST.json) 修正，25 项纯标准库回执测试通过；去日志新增部分后 worker 控制流 AST 与原 v5 相同。历史 v5 原日志未改，最终账本逐行保留 raw 字段及回执支持的 derived 状态；RETURNED 仅表示分派返回，不表示科学正确或资源合格。[独立审查](science_review/PAIR_WORK_STATUS_FIX_INDEPENDENT_REVIEW.zh.md) 已检查 365 条观察、534 份来源及 1020 个唯一锁定文件，无剩余 P0/P1。

外部不同任务审阅者随后真实运行原 v5 与新 worker 各24个构造回归，每轮12查询判定、12合同前STOP均吻合；[外部身份对照](science_review/EXTERNAL_V5_STATUS_REGRESSION_IDENTITY.zh.md) 核对实际5/6源逐字节一致，且明确其使用审阅方协调器，不是本地新supervisor。外部早期指出旧ad83485分类回执不绑定当前导出器；本轮83a23fc版本已有同hash的16项regression02回归及完整逐行独审，旧截面保留。状态修复版计时不替换旧v5成本。自身 supervisor 已在独立 READY 身份审查后实际运行限定 14 槽（24 注册槽中预先选择索引5–18）：7个查询 RETURNED（1 SAT、6 UNSAT）、7个 NOT_RUN_CONTRACT_STOP（6合同矛盾、1不支持）；另10槽保留 NOT_RUN。session56495 已回收 exit2，此退出由所选7个合同拒绝子进程的exit2导致，与未选10槽无关；资源与回放需逐槽核验。[实际进程回执](experiments/STATUSFIX_SUPERVISOR_SESSION56495_REAP_RECEIPT.json)。[实际14槽独立复核](science_review/STATUSFIX_SUPERVISOR_EXECUTED_REVIEW.zh.md) 已核对854文件、55证据身份、14槽清理 COMPLETE 且无资源停止；唯一 SAT 的 canonical→official fallback 保存 A=6、原合同成立及原 SQL 的 NULL/6 回执，13槽 base SAT 与合同 XOR UNSAT。状态日志和 supervisor 正常/类型拒绝传播已通过这次限定集成；不替换原 v5 的168槽或成本，也不覆盖故障注入、硬中断与清理竞态。

4. **不同审阅者**：[36 主入口控制实审](science_review/MAIN_ENTRY_REPAIR_EXECUTED_REVIEW.zh.md) 核验 12 SAT、6 pair UNSAT 和18合同拒绝，其中原合同强制 A=6 的六臂均有 NULL/6 原 SQL 回放；[形式—代码静审](science_review/V5_FINAL_FORMAL_CODE_REVIEW.zh.md) 核对11项映射，并关闭标识符、方言与 SpotIt 范围措辞问题。审阅者均明确是不同 AI agent，披露先前参与范围，没有冒充真人盲审或独立金标。

5. **公开适用性与旧结果**：完整 48,910 查询槽中仅 6 个 eligible，两个可接纳 pair 都无 join；所有拒绝/错误/unknown留在分母。LeetCode 的 23,994 pairs 来自56个源问题标签，不是同数独立任务。[完整公开截面](experiments/PUBLIC_APPLICABILITY_FINAL_CUT.json)。旧 NL2Metric 1108 SQL 的日志实际是1074连接/查询超时与34首标量返回，不是1074 schema/join错误，更不是34正确；1488模型记录全部 semantic unknown，accuracy=null。完整 schema诊断为1002可绑定、43歧义列、63缺列，不能恢复生产真值。评分器、有限合同漏洞与全分母的修复/重跑及旧负结果均在上述谱系索引逐项链接，未对原生成 SQL 猜测补真值。

## 真实科学开放项与最小作者依赖

- 因子化、重数乘积和有限域 selector 已有先例；合同方向和日志修复是实现纠错。当前没有可确认的新科学机制或定理增量。
- 自然公开 join 适用性尚未建立。增加同生成器构造计数不能替代独立适配、明确损失和全失败报告。
- selector 尚无超越 flat、已知 product 与廉价结构控制的可信优势；单次冷进程总成本和不同 unknown/资源状态不能支持稳定加速。Polygon 的有界正向保证已正确纳入相关工作，但未完成同域公平性能比较。
- 今日数学 SQL 研究无需生产访问、真人金标或等待847终审；若作者选择恢复旧生产/人工/工时效果主张，才需相应合法离线快照、完整 oracle 与真实来源链。最终署名、机构/通信信息、贡献/资金/冲突及作者实质核验仍需真实确认；科学竞争力不能用签字或表面排版关闭。

所有工作限隔离本地副本和授权离线材料。未读取传送密钥，未重试被拒鉴权、调用付费 API、配置长期访问或使用未验证GPU；未执行49852安全工作、访问生产、修改其他稿件、上传/push或正式提交。

## 稿件交付状态

最终唯一交付稿为 [11页研究修订 PDF](manuscript_v2/build_final_v3review/main.pdf)，题名 *CaliberGraph: Bounded Verification of Scalar Aggregates through Join-Multiplicity Encodings*；PDF SHA-256 `d1b26713fdf5183b75d2ca0125856d65ea431a915024f1d637a9a50b1abb31ed`。当前 `main.tex` SHA `c974f02466638d525c75de88688eba149fccbe6d25098a4156743d7a112aa7e9`。11页为实际页数，未压缩字体或修改官方模板边距以追求10页内部目标；不作DKE页限/全部格式合规认证。

最终编译日志零 overfull、underfull、缺字、undefined 或 LaTeX warning。机制图在第6页展示限定的真实计数定义、乘积、有限选择器及标量NULL输出，用小例说明已知恒等式；它不增加实验证据或新意主张。作者代理已逐页查看11页，root再次实际查看第1、6、11页；[不同审阅者的全部11页最终审阅](science_review/V5_FINAL_VISUAL_TEXT_REVIEW.zh.md) 已完成，绑定同一PDF，在其已声明审查范围没有开放P0/P1。该审阅者曾参与支持闭包和部分代码检查，已披露，不能称真人盲审。对应JSON SHA `14a2029f2d307f893486be64ebf379a8b2056308c8891688c26edb23f10804e5`；[51项独立数值复计](science_review/V5_FINAL_NUMERIC_RECOUNT.json) 亦通过。

标准自动表面审计中的Poppler bounding-box提取曾 SIGABRT，保留实际失败；正常文本提取、渲染、日志、字体与逐页目视是分开的证据，不把脚本崩溃写成通过。早先“PDF漏SpotIt作者”的目视判定已撤回：原v1/v2文本、bbl及全页像素一致，均已含六名作者，未将误报记为修复成果。最终AI披露明确包括代码、数学草拟、本地实验执行、分析与稿件准备；真实作者核验仍待确认。

表面门依据 [toppaperos-submission-surface-audit/SKILL.md](/Users/loctek/.codex/skills/toppaperos-submission-surface-audit/SKILL.md) 的明确要求："Run `scripts/audit_pdf_surface.py` on every reviewer-visible PDF and its build log." 最终PDF已实际调用，结果是exit1和bbox SIGABRT，因此自动spacing验收仍为UNAVAILABLE，不报告整项自动PASS。这一工具限制、现行DKE细则核验与真实作者确认均继续保留，不能被人工目视或已完成的工程实验替代。

本地审查包不等同于远程备份。按本轮明确“不得上传/push”约束，未执行上级 AGENTS.md 的远程备份动作，状态记为 `BACKUP_BLOCKED_BY_EXPLICIT_NO_UPLOAD`；不请求重复授权。
