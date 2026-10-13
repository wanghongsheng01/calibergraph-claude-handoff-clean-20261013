# 公开 DEV、形式边界与共同前端反例：独立科学补充审查

本报告续接 `SCIENCE_REVIEW.zh.md`，不替换其冻结记录。审阅者为不同 AI agent，并非真人审稿人。本轮只读源代码、父任务真实运行的 JSON 回执及完整扫描结果；没有导入目标、执行 SQL/solver/native、联网或修改方法代码。事实证据与审阅判断分开列出；本报告没有作 DKE 录用或投稿就绪承诺。

**当前结论：继续作者指定的十页 DKE 主线，但现有公开 DEV 不能证明 H1 的连接因子化效用。已复现的共同前端信息损失说明，候选与官方编码一致也可能共同偏离原始 SQL。因子化恒等式和有限选择器本身仍是已知构件；可投稿贡献需要形成严格受限的保证、真实需求与有解释力的比较结果，不能用修 bug 或合成计数代替。**

## 1. 公开 DEV 的完整分母及其实际含义

证据：`../public_dev/runs/full_scan_01/scan_report.json`，SHA-256 `4ca6ee3e96465c719bb93dbe0b7ba4400a80ccc58ba71618044f180e1ffbf81b`。运行使用 v2 kernel `c5ef813532ad190c5af82e2255da973fe8bc469ab24aed7da304678edcd46c35`，角色是已暴露公共 DEV，执行正常 Environment 初始化、官方解析与 recognizer，没有求解或编码。

| 项目 | 实际计数 | 允许的解释 |
|---|---:|---|
| 原始 query pairs | 461 | Calcite 397、literature 64，保留全部原记录 |
| 原始 query slots | 922 | 7 ELIGIBLE + 807 INELIGIBLE + 108 PARSE_OR_AST_RECORD_ERROR |
| 两边均被识别的 pairs | 2 | 只是片段适用，不是等价正确率 |
| 含连接叶表的 eligible queries / pairs | 0 / 0 | 全部 7 条 plan 的 `leaves=[]` |
| VALUES 方言错误 | 80 / 108 解析错误 | MYSQL 模式不接收该 PostgreSQL VALUES；不能计为语义反例 |

两对都是单表：`calcite:142` 是相同 `SELECT SUM(SAL) FROM EMP`；`literature:25` 是 `COUNT(*)` 与 `COUNT(Y.B)`。其余三个 eligible 单边是单表 COUNT。所有 7 条都不进入 kernel 的 leaf multiplication 循环，因此这些查询上的耗时差不能归因于连接因子化或有限 multiplicity selector。

这个 7 是 **v2 历史扫描数**。其中 `calcite:187` 的 `SELECT COUNT(*) AS $f0 FROM EMP` 会被 v3 新的原始 `$` 安全门保守拒绝；此处没有证明该输出别名本身产生错误。不得把 7 直接标为 v3 覆盖率，也不能混同“共同前端不支持”与“算法片段不支持”。后续扩大公开语料扫描时须另冻结原文、版本和全部分母；新增语料尚未给本审阅者最终结果，不能预先宣称覆盖改善或 held-out 泛化。

## 2. 两个共同前端反例已真实复现，范围仍有限

发现来源是独立静态审阅构造的对抗例，不是企业自然缺陷或真人金标。父任务随后实际执行了原始 SQL 的 SQLite 重放、官方 parser 和 v2 recognizer；本人只读核对结果。

证据：`../frontend_diagnostic/RESULT.json`，SHA-256 `ee1c2da47104b6ce919ee5d2a0c23af266fa6199e338ea124ccefa1eea8c2127`；`SUPERVISION.json`，SHA-256 `7531b17e099936cc8a00e5e384cdd2806b2959fe2b53ecc60d014f735928151c`。监督回执为 exit 0、墙钟 1.3974449168890715 秒、采样 RSS 91,078,656 字节；worker 的 ru_maxrss 与该采样口径不同，不合并为同一测量。

两个数据库均为 F 与 D 各一行、连接键 K=1，F 的两个候选聚合列分别为 2 与 7：

| 原始物理列对 | 原始 SQL 的 SQLite 输出 | 官方 parser / v2 plan |
|---|---|---|
| `V$X` 与 `V_DOLLAR_X` | 分别 `[[2]]`、`[[7]]` | 两侧 AST 相同，均绑定 `V_DOLLAR_X` |
| `A.B` 与 `A____B` | 分别 `[[2]]`、`[[7]]` | 两侧 AST 相同，均绑定 `A____B` |

原始第一列在 SQL 中使用反引号。源码链分别包括 `sources/verieql_v1/parsers/sql_parser.py:88` 的全串 `$` 替换、`:149–150` 的点替换，以及 quoted-dot 的上游 literal-field 转义。完整原 SQL、schema、DB、AST、plan 都在 RESULT，不需要从标题推断。

这证明了 **已测原始 SQL 到官方 AST 的非单射信息损失**。没有执行 `Environment.analyze` 或 `solver.check`，因此不能称“已复现完整 VeriEQL 错判 UNSAT”。这也不是袋因子化代数错误。实质教训是：两个方法共享有损前端时，encoder-relative 差分通过不能单独构成原始 SQL 正确性证据。

v3 的 `ensure_raw_identifiers` 在 raw schema 与 SQL 上拒绝非 ASCII 简单名称、`__`、同命名空间大小写折叠冲突，以及原 SQL 中的反引号、双引号、`$`。`FrontendUnsupported` 与算法 `Ineligible` 分开；fair worker 对所有臂在新建 Environment/parse 前阻断，禁止回退到同一有损官方 parser，也不返回等价判断。独立只读核过 kernel `defa1812ec36c91a23d428f8d71d2070f808eddeb5f473748d3e7ac09fdfe5f3` 及配套四个 fair 文件。**已知两类缺口的拒绝路径静态成立；本报告未审阅新门控的实际运行回执。** 这不是整个 SQL parser 的语义完备证明。

## 3. 形式保证需要拆成三个层次

**受限袋代数。** 对一个完整数据库赋值和根元组 f，谓词必须可分为 root-only 与每个 root+single-leaf 条件，全部 leaf 都是 inner equijoin，聚合值只来自 root。满足条件的连接输出袋，条件于 f 后正是各 leaf 匹配袋的笛卡尔积，其重数为 `root_valid(f) × ∏j Cj(f)`。这不要求概率独立；跨表 IC 可以相关化数据值，但必须完整保留。若允许跨 leaf 原子/OR、外连接、DISTINCT、分组或 leaf 聚合值，不能套用这一定理。

**NULL 与选择器。** COUNT(*) 与 COUNT(expr) 分开；后者按 expr 非 NULL 计数，不按值非零计数。SUM 的 NULLness 取决于合格且 expr 非 NULL 的输出行数是否为 0，空集与全 NULL 都返回一个标量 NULL 行。对精确定义的 `Cj=Σ If(match,1,0)`，`0≤Cj≤Nj`，故 `Σc=0..Nj If(Cj=c,c*s,0)=Cj*s`。有序、全新整数辅助变量绑定这些定义，才能作为保守扩展；Cj 不能成为自由计数，不能丢 IC 或缩小同一 bound。

**原始 SQL 到 emitter。** 上述代数不自动证明 parser、recognizer、Scope 与官方聚合 emitter 的映射。当前 per-query 差分比只看 pair 的 SAT/UNSAT 更有信息：读取真实 Scope 全部输出 slots、证明恰有一行 alive、比较 NULL 与非 NULL 整数值，并检查候选定义的 freshness 与无环性。但是 `SAT(official_premise)` 只证明至少存在一个模型；它不证明 `∀合法基础 DB，∃官方辅助赋值`。在某个完整官方前提内证明 mismatch UNSAT，仍是 encoder-relative agreement。不能以 nonvacuity 的一次 SAT 代替官方辅助约束总定义或原始 SQL 正确性；SAT witness 可以独立数据库执行验证，UNSAT 的普遍性则需要受限证明/明确的可信前提。

在已声明普通唯一标识符、当前 scalar root-column SUM/COUNT、正 exact-row bounds 的片段下，本次未发现上述乘积/NULL/selector 恒等式的反例；这不等于完整实现已证明无错。零物理基表行在当前接口拒绝，过滤后零输出仍必须正确，不能混淆。

## 4. runtime_fair 的静态审查及公平性边界

旧四文件提供的 hash 已独立核对，逐文件只读审阅；raw-frontend 增量也已核。没有发现阻止普通已冻结 INT32 DEV 诊断的新增执行 P0/P1。每个成本 arm 独立新进程与 Environment、同完整 schema/IC/exact-row vector、共同 SAT/exact-row guard；剩余预算动态计算，候选不适用或 unknown 的官方 fallback 成本累计，错误与未运行槽保留。per-query 差分与成本实验分离是正确的证据组织方式。

但这些是运行设计的静态确认，不是性能结论。`simplify → propagate-values → solve-eqs → smt` 是一条明确控制，不能据此宣称已穷尽强 SQL 优化。必须对照可适用的 aggregate pushdown、join elimination、PK/FK 导出的 multiplicity 0/1 化，或明确这些未测。常见星型 schema 的 dimension key 唯一性可能把 `Cj` 限为 0/1；无筛选且 FK 总覆盖时甚至恒为 1。不得为了扩大倍数删除原始 key/FK，随后把性能收益当作真实 star 工作负载结论。

selector 的线性化只针对 multiplicity products。完整 IC 仍可能有别的算术；若下一版加入 root `x*y`，measurement seed 本身就是符号乘法。未证明其余公式全部线性时，不得称整个方法是 LIA 或消除了全部 NIA。

## 5. 今天还缺的最小非 toy 需求及可证伪实验

首先需要一份可追踪、原文不改、完整 schema/IC 保留的真实验证任务：某个现存 scalar aggregate 查询与一个有来源的待验证 rewrite/版本，至少确实进入 leaf 路径。要展示笛卡尔枚举相对因子化的结构优势，至少需要多 leaf 情形，而不是单表或恒等查询复制。一个独立来源的 family 只证明“存在这样的需求”，不证明普适；足量不同 family 才能支持更广主张。删除 GROUP BY、替换乘法或去掉真实约束后得到的是派生 workload，必须如此标注。

有限、可完成的下一轮证据应包含：

1. **语义最小闭合：**同一原始 SQL、schema、全部 IC 与 exact-N，分别证明/核查受支持映射；覆盖 zero-match、全 NULL、重复维行、负值、COUNT(*)/COUNT(expr)；所有 SAT 提取完整 DB 并执行原 SQL。人工构造边界例只能叫构造例。
2. **同保证成本：**在真正激活 leaf 路径的需求上，对完整官方、官方 generic SMT、local flat、product、selector 按同输入和总预算比较；记录编码规模、编码时间、求解时间、总进程成本、成功/unknown/timeout、fallback 以及全部分母。成本必须在语义证据合格范围解释。
3. **反机制控制：**保留真实 key/FK，检验计数是否已被约束到 0/1；对已有因子化/聚合下推/一般简化能消除的工作量给相应控制。若收益仅来自绕过官方通用框架开销，就报告该系统效应，不冠以新算法收益。
4. **反证条件预先固定：**若没有适用的原生需求，H1-U 目前无外部支持；若 product/通用优化取得同样结果，selector 的增量价值未立；若规模减少被编码或求解开销抵消，H1-C 速度优势不成立。若有严格同保证对照揭示稳定交叉点/失败机制，可转成有新认识的负结果，而不是删去失败或自动放弃作者主线。

现阶段最诚实的贡献候选是“一个边界显式、可复查的验证 kernel，以及它何时有效/失效的实证解释”。这仍是候选。袋因子化、符号 tuple multiplicity 和有限域选择器须署名既有工作；把三者接起来、修复上游适配、运行 964 个合成点并不能独立建立新颖性。新发现的 frontend 信任边界是有价值的系统观察，但两个有意构造例不足以支撑自然缺陷发生率或普遍工具质量结论。

## 6. 对拟议 v4 表达式扩展的前置意见（未审实现）

runtime_guard 通知拟加 root-only `+,-,*` 与 column/int BETWEEN；本报告没有把拟议实现当作已完成。递归 arithmetic 必须 strict NULL，SUM 的非 NULL 行计数不能被值抵消，COUNT(expr=0)仍要计数。BETWEEN 需同一 root/single-leaf 作用域、两端 inclusive、比较为 TRUE 才筛入；当前限定整数/列时不接收 NULL 端点。

SQLite signed-int64 oracle 与 Z3 数学整数模型必须有显式桥接。仅输入 INT32 不保证 root 乘法、中间加减或聚合累积 int64 安全；SQLite 可能转 REAL 或抛 overflow。应保守验证每步/总和的安全域，或保留 `UNKNOWN_ORACLE_DOMAIN`，不能将溢出当方法反例、偷偷截断、用 float 近似或丢掉失败。新 root 非线性表达式与 root 线性表达式须分层分析，selector 不能消除前者自带的 NIA。

## 7. 最终边界

作者继续十页 DKE 主线的决定保持。沿用此前官方第一作者确认；847 无重复是本轮作者声明，本补充没有新增独立排重结论，也没有把它设成阻断项。形式 SQL 研究可使用受限数学证明与独立数据库执行 oracle，不需要凭空添加真人业务 gold；原有真人/企业业务效果主张若保留，仍须各自真实来源。

本次关闭的是公开 DEV 计数核查、共同前端反例的有限复现证据核对，以及相应拒绝路径的静态检查。完整原始 SQL 保证、真实连接需求、强对照、总体效用、新颖性和最终新稿证据一致性仍需后续实际结果；不能因本审阅完成就标为科学验收通过。
