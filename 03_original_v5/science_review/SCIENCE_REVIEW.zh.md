# CaliberGraph 今日科学审阅与 H1 改稿依据

2026-10-11，独立 AI 审阅者 `/root/independent_review`。本轮只读现有稿件、真实评审、代码和已保存运行结果；未联网、访问 MOSS、执行或导入目标/native、重跑实验、修改原稿。所有新文件只写本目录。来源逐文件哈希与读取范围见 `SOURCE_SNAPSHOT.json`；结构化判断见 `SCIENCE_REVIEW.json`。

**最新执行方向是继续 CaliberGraph 十页 DKE 主线：真实实验 → 稿件 → 不同独立审阅者。** 我最初建议退出“今天可投稿”的资源主线，理由是现有科学证据不足；该初始意见保留于 `INITIAL_SCIENCE_JUDGMENT_0221UTC.json`，不是作者最终决定。作者随后明确继续，并声明与 SIGMOD847 无重复。本报告记录该声明，不再把历史谱系疑问或私有 business gold 作为整条新 SQL 研究的阻塞，也不冒称重新独立认证了无重叠。官方第一作者确认沿用。

当前证据尚不足以给新方法或论文放行；这与继续完成授权主线并不矛盾。SQL/VeriEQL 接通能够关闭工程缺口，不能独自关闭新颖性、语义保持、强对照和实际适用性。没有性能胜利也不自动排除严谨负结果或系统贡献，关键是是否产生了可复用、可证伪的新认识。

## 1. 原稿问题：方法、实现和证据分别判断

正式32719题名为 *CaliberGraph: Coverage-Caliber Witness Compilation for Multi-Business-Domain Governed Metrics*；109为 *NL2Metric: Production-Grade Business Metric Compilation with Scoped-Ratio Semantics and Cross-Caliber Routing*。二者按一条研究线处理。正式稿、内部修订稿和当前 H1 不是同一个冻结版本，不能互相继承未经验证的结论。

|问题类别|直接证据|当前判断与验收方式|
|---|---|---|
|原方法主张超出实现|正式32719抽取稿77–124行定义八槽 witness、完整条件与存在性判定；修订稿 `manuscript_v1/main.tex:59–63,87–92`、实际 compiler `:473–486,528–591` 明确只是依赖存在、成员关系、词法政策、active-check 合取|修订撤回过强主张是正确修复。要恢复物理 SQL、join、interval-time、授权或完整 witness，必须分别有实现与对应语义证明/执行证据；不能把返回 `answer` 的控制流不变量当成这些性质。|
|可修实现缺陷|`work_contract/CONTRACT_MAPPING.md:23–29,35–49`：必需覆盖空源曾被降成 inactive、显式空维度限制、坏层级；现15构造例3/15→15/15|`Fixed-with-evidence`，可作为可靠性修复，不是15个新真实事件或泛化样本。全量1485投影结果修前修后均1479，六失败仍保留。|
|评分与分母缺陷|`manuscript_v1/audit_results_v1.tex:32–36`；`independent_review/FINAL_REVIEW.zh.md:51–59`|1108唯一SQL属于1488个DeepSeek A/B/C记录；1074超时、34缓存首标量，无同快照完整参考执行。1488 semantic UNKNOWN、accuracy undefined 是正确结论。接通新本地SQL不能追溯恢复旧生产真值。|
|评价对象不覆盖原主张|`audit_results_v1.tex:19–30`：time182/326，144空值；其余无time标签；1507 trace是接口自洽|高 action/metric/dimension 分数不证时间、SQL或真实合同。应逐语义对象给分母，或者从新主张删去未覆盖维度。|
|技术增量未隔离|ICDE原review80–105行及meta：两个反事实未测、五消融混合预期/观察、A/B同分不检验编译机制、159缺失且demo不能重算；AAAI拒绝review要求定义/实现与实验选择依据|这些是方法和实验设计缺口，非换模板即可修。相同候选与信息的独立声明式validator、实际semantic-layer/rewrite强对照仍必要。|
|已有反证必须保留|`main.tex:185–211`；`DKE_SCOPE_AND_CONTRIBUTION.zh.md`|private156/159 prompting >147/159 CG；dbt longest-alias122/122与prompt平，另一linker120/122。不能宣称总体准确率优越；历史LLM成本与deterministic局部耗时也不是本轮公平端到端优势。|
|可外推范围有限|AAAI真人正面review仍指出同治理引擎和外部适配/噪声合同缺口；`main.tex:132–152`|多模板、多变异或同作者converter/gold不产生独立组织。若新稿不主张自然业务缺陷或跨组织适配，可诚实缩到公开形式SQL对象，无需强加这些外部证据。|

真实评审确有正负分歧：我读取了 AAAI `note_CmribIcaKL.txt`（3分）与 `note_2JLYgUAeAg.txt`（7分），以及 ICDE109三份真人review/meta，没有把自动AI review当真人拒因。正式稿的旧人类研究声称仅有文件和统计尚不能认证参与者独立性；这不是指控造假。若不保留真人研究主张，就无需为新的形式实验补造人。

## 2. 今天已新增的实际证据及其边界

只读 `today_20261011/runs/dev_first2_01/{supervisor_report.json,case_00/worker_report.json,case_01/worker_report.json}` 后确认：

- 固定官方 Environment 和 solver 已实际运行。S01重排合取为 bounded UNSAT；S02 nullable COUNT 为 SAT，完整三表反例的 SQLite 标量结果为4与2，确实不等。
- 两例完整合同可满足、任一基表行被删除为UNSAT；输入schema/IC/exact-row来源保留。相比昨天仅native/16构造，这是真正推进。
- flat/product/selector共六个候选槽均为 `INELIGIBLE: ambiguous_or_unknown_column`；候选固定point检查全部NOT_RUN。六例×四臂总分母24保留，另四例与七个拒绝路由未执行。因此这次没有完成H1 kernel编码，也没有否证其代数原理。
- 当前适配阻塞首先应查官方 parser 输出到识别器/字段表的映射；不能以删掉失败样本、改成弱schema或读取gold恢复所谓成功。首轮结果原样保留。
- official5秒、candidate2秒求解子预算和共享Environment只用于诊断；记录的毫秒耗时不可相除写成速度优势。线程采样曾为2，最终Python线程为1，不能把它说成全程单线程。

本次快审 `runtime/case_worker.py` 和 `supervisor.py` 没有新发现足以撤销上述有限实例结果的P0。**当前query-pair判定一致加每例一个point，仍可能漏掉两条查询共同误算。** 后续须加逐查询输出语义差分与限定语义证明；不能把smoke的一致率当成正确性定理。已向实现者和父任务发送此边界，没有改运行文件或要求重跑。

## 3. 形式同保证：精确对象、引理及未闭合映射

当前应以实际代码最窄范围写论文：整数 `SUM(root_column)`、`COUNT(root_column)`、`COUNT(*)` 或非NULL整数常量COUNT；单事实根、不同物理叶表、inner equijoin；谓词为root-only或单leaf+root原子的合取。排除GROUP BY、DISTINCT、外连接、跨叶原子/OR、窗口、相关子查询及一般仿射表达式。`aggregate_kernel.py:51–57,78–83,119–154` 不支持宽泛方法筛查曾设想的所有线性表达式；不得据设想扩写实现。当前零基表行数在 `:175–177` 退出候选，完整fallback仍必须保留该输入；匹配后零行与基表零行不同。

**语义前提。** 同一SQL、schema、类型、每表exact大小向量、基表tuple/NULL/VALUE变量和所有原IC。遵循已核引擎的数学整数及INT输入界，不声称通用DBMS溢出语义。给定完整数据库赋值D，定义root有效指示 \(R(f)\)，leaf匹配指示 \(I_j(f,d)\) 当且仅当行存活且该leaf的ON/WHERE谓词在SQL三值逻辑下为TRUE。unknown不匹配。\(C_j(f)=\sum_{d\in D_j}I_j(f,d)\in[0,N_j]\)，不是自由计数。

**引理1：袋重数保持。** 对每个固定D与f，可分离的匹配叶集合是各leaf匹配集合的笛卡尔积，故该root的输出重数为 \(R(f)\prod_j C_j(f)\)。这是逐赋值有限和的分配律，不要求不同leaf在概率意义独立；跨leaf的IC可以相关，但必须全部保留，它们只限制允许的D。若查询本身有跨leaf谓词，则积式可能失效，必须识别为不适用。

**引理2：value与NULL保持。** COUNT(*)的root贡献数为上述重数；COUNT(x)再乘 \(1[x\ne NULL]\)。令非NULL贡献总数为n，则SUM(x)的值为 \(\sum_f R(f)1[x\ne NULL]x\prod_j C_j(f)\)，且NULL标志恰为n=0。COUNT永非NULL；scalar SUM在空/全NULL时是一行NULL，不是0或零行。负数和重复匹配仍受同一等式覆盖。

**引理3：selector等价与辅助变量保守扩展。** 已知整数C在0..N且fresh变量s绑定上一步表达式，则
\[
s'=\sum_{c=0}^{N}\operatorname{If}(C=c,c\cdot s,0)=C\cdot s.
\]
恰一分支成立。每层fresh变量用等式绑定且无名称捕获，对任何原数据库赋值恰有对应辅助赋值；不缩小、不扩大原IC允许的数据库域。逐层归纳得到与raw product相同的NULL/value。`aggregate_kernel.py:211–221,239–256` 实现了这种结构，但本段只证明该抽象构造，**不宣称整个parser与实际emitter已经通过证明**。selector仅消除这一重数乘法的变量乘变量，不能把任意原IC/UF或其他算术都称为纯QF_LIA。

**尚须闭合的映射义务：** (a) 原SQL AST与别名/字段/类型的解析守恒，包括今日失败；(b) eligibility充分性，拒绝无法证明可分离的形式，且拒绝不丢原输入；(c) 官方Scope/analyze前后base事实及属性应用不变；(d) 实际辅助名称fresh、每条定义全部进入solver、NULL/value公式与上述引理对应；(e) 对每个query独立比较官方输出与候选输出，而不只比较一对query的SAT/UNSAT；(f) decoded SAT数据库满足全部IC且原SQL完整bag结果不同。完整输入先SAT guard，防止以矛盾合同造成的vacuous UNSAT通过。

有限构造和具体执行能检验映射、发现反例，不能代替无限整数取值上的语义证明；UNSAT也只是声明的tuple大小域，不是无界SQL等价。未导出独立可检查proof object时，应写“bounded solver verdict”，不称八槽witness或机械可验证证明证书。

## 4. 可证伪H1与最小关键实验

**H1拆成三项，避免必须赢性能才能写论文。**

1. **H1-S：同语义。** 上述受限片段中，输入和IC不变时，factorized/selector编码与声明SQL袋语义保持NULL/value；其余完整fallback。任一合法反例即可否证当前实现/识别边界，修正后重新冻结，旧失败保留。
2. **H1-C：成本机制。** 相比展开，匹配项由约 \(N_f\prod_jN_j\) 转为 \(N_f\sum_jN_j\)，selector分支为 \(N_f\sum_j(N_j+1)\)，依赖fresh DAG共享。此项只约束局部编码项，不推导solver wall必降，也不省略全部IC或frontend成本。高arity、小bound可能受益；低arity、大bound或强IC可能被selector/求解成本抵消，均可测。
3. **H1-U：实际用途。** 未触碰来源家族上存在非零且可说明的eligible任务；在同预算下获得成本/可决定覆盖改善，**或**得到稳定可解释的适用/失效边界。系统贡献需可复用模块、明确定义的输入输出与失败合同和真实对照；“我实现了已知技巧”或“没有跑赢”本身均不够。

最小关键实验按以下顺序冻结、执行；本审阅不替作者运行或改方法：

|阶段|必须完成的工作|允许得出的结论|
|---|---|---|
|A：实现与语义关口|修今日parser映射；原六个DEV全部保留；每query官方↔候选NULL/value差分；NULL、空聚合、重复匹配、负数、完整IC可满足/约束效应；所有SAT反例独立SQL回放；非反身性fallback样例|限定实现诊断、被发现并修复的bug；不是新测试集或泛化。数学引理与实际映射单独记证据状态。|
|B：真实适用性普查|对事先固定的合法公共query-pair清单全量识别，只统计不按表现筛选；按来源与近重复family分组；冻结真正未触碰测试；公布eligible/fallback/error全部数量及拒绝原因|若eligible太少，收窄适用性，不能补大量合成来冒充公共覆盖。具体n目前未知，不捏造一个满足门槛的数。|
|C：最小四臂配对|完整官方原路径；已验证的通用SQL/SMT等价预处理后官方路径；已知raw-product factorization；selector。相同schema/全IC/exact-row向量、native、单求解线程、每实例总wall/CPU/内存与调参预算。独立进程/对称初始化，固定顺序或预先随机顺序；相同重复规则|分离“分配律收益”与“selector额外收益”；仅赢未优化flat不足以证明selector贡献。若某控制尚未实现，表中标未运行，不能写成被击败。|
|D：机制与外推|不同每表大小向量、join数和匹配重数、选择性、NULL与IC层；编码节点/内存、解析/识别/改写/编码/求解/反例核验/fallback分项与总和；全部timeout/error/unknown纳入分母|区分减表达式与求解更快；使用family为独立单位，不能把同模板多个bound当独立泛化样本。构造压力只解释机制。|

“强预处理”不能只随意调用一个 `simplify` 就宣布闭合：须说明官方默认已做什么、额外等价rewrite/共享/常量消除/等式替换实际用了什么；SQL层的合法聚合下推/按join-key预聚合若适用于该片段，应正面比较或解释实现限制。每个rewrite先证明或验证其袋/NULL前提，不能引入主键/唯一性假设换速度。相关系统应按其真实完整能力运行；SpotIt代码闭包不全时不能用四个同源算子冒称完整SpotIt+复现。

**停止的是不成立的主张，而非自动停止整篇工作。** 语义反例否证H1-S；同机制已被先例覆盖则撤回原创机制说法；同全成本后优势消失则撤回速度优势。若负结果在预先分层的真实任务和机制控制上稳定，能解释为何节点减少却求解更慢、给出可复用选择准则，仍可能成为诚实结果。仅两个DEV、964已暴露构造点或一次依赖故障不能承担这样的新认识。

## 5. 新稿如何收窄，先例如何正面比较

今天最可审查的主线是“给定声明的SQL/合同，受限聚合的有界验证与编码权衡”，而非“已证明企业NL请求/授权/完整八槽见证正确”。原CaliberGraph可作为动机和调用边界；H1是新增验证模块，不能拿旧1479/1485或private/人标统计支撑H1。业务合同是输入，当前不证明其组织真值。形式SQL正确性可以由数学推导、原SQL在完整具体数据库上的独立执行及受限证明关闭，不需要真人business gold。执行oracle证明那些实例，不单独证明普遍等价。

最近邻必须承认：factorized databases/FAQ已有因子化，Cosette已有符号重数，有限域selector为通用编码，VeriEQL已有有界验证与反例；固定版本未实现相同优化只是工程差异，不等于学术首次。`METHOD_SCREENING.zh.md:7–11,19–29` 和 `BASELINE_AUDIT.zh.md:7–9` 已有这一边界。

新增必读 **Thanisch et al. (2019), Detecting measurement issues in SQL arithmetic expressions and aggregations, DOI 10.1016/j.datak.2019.06.001**。本审阅只收到父任务核得的metadata与“expression-tree单位/尺度/分组规则静态检查”摘要，未读全文、未联网。可暂作比较轴：测量单位/尺度/分组合法性，与固定schema/IC/tuple域下关系结果等价、反例及重数编码，证明对象不同；两者可能互补。不能说对方“只是语法”、不处理语义，或未经全文断言完全不重叠。稿中相关表应分别列输入、规则/语义、输出、保证域、聚合/NULL支持、成本；未读到项写未核，而不是no。

十页内容预算建议（作者长度目标，不是本轮认证的DKE格式规定）：1页问题与诚实贡献；1页先例/比较；1.5页任务与语义；2页引理、识别器和编码；1页实现/失败合同；2页真实实验和负结果；0.5页局限/复现/真实AI用途；其余约1页参考文献，实际按图表和来源调整。方法用当前支持范围和真实输入输出；结果表只放实际运行且可追溯的项。若只完成A，稿应保留“内部研究稿/未完成实验”状态，不将空表、待跑计划或已有机制计成完成贡献。

AI用途按真实过程披露：代码、形式推导辅助、分析、文稿及不同AI审阅；作者监督/核验只有实际发生才写。独立AI审查不是人类同行评审，不复写不存在的作者验证。最新作者无重复声明与官方第一作者确认单独记录，避免在科学证据表中混成新方法支持。

## 6. 本轮结论与后续审查入口

已有可靠进展是Phase1纠错、完整分母、有限native兼容，以及今日两例官方SQL验证/一个具体反例回放。当前最紧要缺口已从依赖安装转为识别器映射与H1实际运行；再往后是语义保持与强控制。应继续作者选定主线，优先解决这些可检验义务，并根据结果写稿；不能预设最终必须得到性能胜利或“可投稿”结论。

下次独立科学复核只需交：冻结源码/输入hash、完整逐项运行结果及失败、上述A的语义对应、真实适用分母、实际运行的强对照与总预算、更新稿逐项claim→evidence映射。公开形式对象无需等待旧生产gold；若仍保留自然业务/真人参与主张，则对应来源仍需真实证据，或删去这些主张。

本轮遵循本地 `paper-audit` 技能：区分官方既有评审、已存同领域参照、内部科学判断，并给出可检查的关闭条件。因明确不联网，没有重验DKE现行rubric/格式或新增先例全文，不声称目标期刊合规或预测录用。用户禁止上传/push优先于上级备份默认要求：`BACKUP_BLOCKED_BY_EXPLICIT_NO_UPLOAD_NO_PUSH_SCOPE`。
