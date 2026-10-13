本报告是研究作者对第三轮既有结果的阶段诊断，不是独立审稿。只读取已注册的原始记录、batch_02 的 results/events/receipts 和冻结代码；本次分析没有执行 SQL、parser、solver、重测、扩大扫描或修复冻结文件。机器可读明细见 [official_bounded_diagnosis.json](/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_03/analyses/official_bounded_diagnosis.json)，其 SHA-256 为 `5681be6ab7d82647c950a68dfb36a6d79826dc34e10f888f7315e67eddc19f57`。

21 个已注册来源组中，17 组返回结果：10 个 `SUPPORTED_FAST`、4 个 `SCHEMA_UNSUPPORTED`、1 个 `CONTRACT_INCONSISTENT_EXACT2`、2 个原始 `INCONCLUSIVE`。第 18 组在导入期间因监控命令超时被终止，后 3 组保留 `NOT_RUN`。10 次查询检查的 CPU 为 **7.908–60.638 ms**，合计 **261.677 ms**；13 次完整 operational C 检查加 10 次查询检查总 CPU **319.461 ms**、wall **320.043 ms**。没有 solver UNKNOWN/timeout，没有触发独立重复，没有稳定成本候选。这个结论只适用于已到达查询 solver 的 10 组、共同 exact2 形状；不证明其他来源、较大或混合基表基数没有瓶颈，也不构成新方法收益证据。

**分母、来源与两条证据轴。** 实际注册 21 组 / 42 个原 SQL 槽，容量上限 32 的其余 11 槽是 `NOT_REGISTERED`。没有为失败或未运行组补样。来源均为同一已曝光 LeetCode JSONL，按原始 CSV 文件标签去重；这不是统计独立性证明，也不是未曝光测试集。20 组 C 字段为 `PRESENT_JSON`，仅表示上游声明了非空 operational C 列表；dev03_20 是 `NULL_UNSPECIFIED`，不能解释为“明确无约束”，并且本轮没有运行至其合同准入。所有组的业务约束真值、SQL 语义忠实性、原 pair 标签真值均未验证，`semantic_admission` 为空。工程上快或可编码，不能因此升级为真实业务问题已认证。

下表的 L 是原 JSONL 的 1-based 行，index 是原记录索引；完整 schema、原始 C、原 SQL、各自哈希及源定位均原样收录于 JSON 明细。C 列是顶层操作符计数，不是删减后的合同。S1–S6 是注册时词法分层：集合操作、派生表聚合、IN/EXISTS/相关提示、外连接、自连接/重复关系、至少三表多连接；只作来源选择提示，不作 AST 语义真值。每组原始记录路径为 `benchmark/leetcode/raw_data/<file>`。

|组|原 file / L / index|词法层|原 C 顶层计数|原始结果 / 派生解释|C / query 检查数|累计 solver wall ms|
|---|---|---|---|---|---:|---:|
|dev03_01|1127.csv / 9581 / 171|S1|primary×1, gt×1, in×1|SCHEMA_UNSUPPORTED|0 / 0|0.000|
|dev03_02|584.csv / 2421 / 48|S1|primary×1, foreign×1, neq×1|C_UNSAT_EXACT2|1 / 0|3.827|
|dev03_03|1693.csv / 20110 / 64|S1|neq×1|SUPPORTED_FAST|1 / 1|22.014|
|dev03_04|1468.csv / 17255 / 250|S1|primary×1, gt×1|INCONCLUSIVE / UF 标记分支退出|1 / 0|4.276|
|dev03_05|1132.csv / 10021 / 292|S2|primary×1, in×1, foreign×1, imply×2|SCHEMA_UNSUPPORTED|0 / 0|0.000|
|dev03_06|1783.csv / 21931 / 41|S2|primary×2, foreign×4|SUPPORTED_FAST|1 / 1|65.721|
|dev03_07|1173.csv / 11415 / 34|S2|primary×1, lte×1|SUPPORTED_FAST|1 / 1|13.549|
|dev03_08|183.csv / 580 / 197|S2|primary×2, foreign×1|SUPPORTED_FAST|1 / 1|18.793|
|dev03_09|1747.csv / 21639 / 410|S3|lt×1|SCHEMA_UNSUPPORTED|0 / 0|0.000|
|dev03_10|1264.csv / 13041 / 25|S3|primary×2, neq×1|SUPPORTED_FAST|1 / 1|30.219|
|dev03_11|511.csv / 673 / 67|S3|primary×1, gte×1|SUPPORTED_FAST|1 / 1|12.026|
|dev03_12|577.csv / 2173 / 88|S3|primary×2, foreign×1, neq×1, gte×2|SUPPORTED_FAST|1 / 1|32.228|
|dev03_13|1677.csv / 19915 / 344|S4|primary×3, foreign×1, gte×4|SUPPORTED_FAST|1 / 1|63.617|
|dev03_14|613.csv / 4513 / 45|S4|primary×1|SUPPORTED_FAST|1 / 1|12.161|
|dev03_15|1421.csv / 15534 / 21|S4|primary×2, foreign×1, gte×1|SUPPORTED_FAST|1 / 1|37.523|
|dev03_16|1777.csv / 21819 / 95|S4|primary×1, in×1, gt×1|SCHEMA_UNSUPPORTED|0 / 0|0.000|
|dev03_17|1211.csv / 12206 / 390|S5|between×2|INCONCLUSIVE / parser 拒绝|1 / 0|4.089|
|dev03_18|596.csv / 2924 / 73|S5|primary×1|STARTED / 导入阶段监控中止|0 / 0|0.000|
|dev03_19|1683.csv / 20022 / 14|S5|primary×1|NOT_RUN / 批次中止|0 / 0|0.000|
|dev03_20|1149.csv / 11280 / 221|S5|NULL_UNSPECIFIED|NOT_RUN / 批次中止|0 / 0|0.000|
|dev03_21|607.csv / 4241 / 751|S6|primary×3, gte×3, foreign×2, imply×1|NOT_RUN / 批次中止|0 / 0|0.000|

**分阶段 CPU 与原始 verdict。** 单位为 ms。C 列为实际 `check`，不是包含 setup 和模型验证的外层 stage 时间；query 列同样只计实际 `check`。parse 为两条 query 的已记录解析 CPU 之和；scope 是外层 analyze 减去 parse 的残差，包含 scope 编码与其周边工作。compare 是比较公式生成至进入 solver 前的已记录时间。`—` 表示未到达或未形成该独立计时，不能当作零成本。总失败成本另由父进程 wait4 全额计入。

|组|C verdict / CPU|parse CPU|scope CPU|compare CPU|query verdict / CPU|说明|
|---|---:|---:|---:|---:|---:|---|
|dev03_02|unsat / 3.835|—|—|—|未检查 / —|C 已 UNSAT；没有查询解析/编码/检查|
|dev03_03|sat / 5.345|65.889|18.143|5.912|sat / 16.657||
|dev03_04|sat / 4.284|73.121|22.946|—|未检查 / —|两个 Scope 完成；compare 抛异常，耗时未独立落字段|
|dev03_06|sat / 4.992|66.800|30.599|6.652|unsat / 60.638||
|dev03_07|sat / 4.757|63.102|6.441|4.878|unsat / 8.797||
|dev03_08|sat / 4.308|62.258|16.502|5.377|unsat / 14.500||
|dev03_10|sat / 4.498|67.043|12.783|5.025|unsat / 25.726||
|dev03_11|sat / 4.131|62.456|7.699|4.857|unsat / 7.908||
|dev03_12|sat / 4.621|62.735|13.917|7.969|unsat / 27.605||
|dev03_13|sat / 4.643|66.714|70.125|6.033|unsat / 58.423||
|dev03_14|sat / 3.931|61.278|10.145|4.249|unsat / 8.241||
|dev03_15|sat / 4.342|62.729|16.363|8.889|unsat / 33.182||
|dev03_17|sat / 4.097|65.460|3.488|—|未检查 / —|q1 解析失败；scope 残差为外围/异常记账，不是完成的 Scope 编码|

实际 C 检查 13 次，其中 SAT 12、UNSAT 1；查询检查 10 次，其中原始 SAT 1、UNSAT 9。events 中 `SOLVER_CHECK_START` 和 `SOLVER_CHECK_END` 各 23 条，与 results 的每组调用数一致，没有隐去失败检查。24 个解析调用中 23 个成功返回 AST、1 个抛异常；23 个成功 AST 都有 lossless canonical JSON 和哈希，已保留在各 attempt 的 `parsed_asts` / parse stages 中。11 组完成双 query 解析及 Scope，其中 dev03_04 在其后比较公式阶段退出。未完成或尚未运行的 SQL 没有虚构 AST。

**可确定的失败机制。** 四个 schema 拒绝发生在本轮结构准入，分别是 dev03_01 的 `SPENDING.PLATFORM=ENUM,DESKTOP,MOBILE`、dev03_05 的 `ACTIONS.ACTION=ENUM,VIEW,LIKE,REACTION,COMMENT,REPORT,SHARE`、dev03_09 的 `LOGINFO.LOGIN=TIME`、dev03_16 的 `PRODUCTS.STORE=ENUM,STORE1,STORE2,STORE3`。冻结官方 [environment.py:555](/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/sources/verieql_v1/environment.py:555) 的类型分支只对 BOOL/BOOLEAN、DATE、INT、VARCHAR 建相应界，至 578 行其余类型进入 pass；本轮保守拒绝，未将 ENUM/TIME 静默当成已编码类型。这四项不是四次官方 SQL parser 失败。只报告首拒绝：修好这一项后会不会继续失败没有测量；例如 dev03_05 原 C 的 imply 仍原样保留，不能把尚未执行的后续阶段当成成功。

dev03_02 的原完整 C 是 CUSTOMER.ID 主键、REFEREE_ID→ID foreign、REFEREE_ID 与 ID 的 neq。在固定官方操作语义下，[foreign 分支 environment.py:646](/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/sources/verieql_v1/environment.py:646) 到 656 行要求每个源 REFEREE_ID 非 NULL 且等于某个非 NULL 目标 ID；[跨列比较 environment.py:695](/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/sources/verieql_v1/environment.py:695) 到 750 行的 neq 遍历两列笛卡尔积，要求每个 REFEREE_ID 与每个 ID 都不同。因此任何非空 CUSTOMER 都矛盾，主键不是推导所需条件。观测是 exact2 的 C UNSAT；静态推导进一步说明此例不能仅归于“2 行太小”，但该推导只针对官方 operational C，不能断言业务合同本身错误。空的抽象关系可使这两类约束真空成立，不代表本轮已运行或证明官方零行支持。该组完全没有 query 检查，不应算查询等价成功。

dev03_04 的 C 为 SAT，两条 query 的解析和 Scope 已完成。原 traceback 经 environment.py:942、verifier.py:103、bag_semantics_verifier.py:116，终止于 [verifier.py:53](/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/sources/verieql_v1/verifiers/verifier.py:53)。触发条件是对应输出属性 `is_uninterpreted_func` 布尔标记的 XOR，即一侧有该标记、另一侧没有；不是仅凭异常文本猜测的函数名不匹配。它发生在 environment.py:951–952 的 solver.add/check 之前，查询检查数为 0。原始 `NotEquivalenceError: Symbolic reasoning: NOT EQUIVALENT.` 及工程 `INCONCLUSIVE` 原样保留；派生类别为 `NON_SMT_COMPARISON_SHORTCUT_UF_FLAG_MISMATCH`。触发的具体输出属性未在日志中定位，不猜测其列；这一提前退出没有提供原始 SAT、模型或 DBMS 回放，也没有证明 frontend bug 或原 SQL 真实不等价。

dev03_17 失败阶段为 `OFFICIAL_PARSE_QUERY_1`，异常是 `ParserSyntaxError`。底层 ParseException 在 char 69 / line 1 column 70 遇到 `( (SELECT`，位置对应第二条 SQL 中带两个标量子查询的 ROUND 表达式。[sql_parser.py:322](/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/sources/verieql_v1/parsers/sql_parser.py:322) 将该解析异常包装后向上传递。第一条 AST 已保留；官方 analyze 在生成 Scope 前先解析输入列表，故不能把外围残差计时说成第二条 SQL 的 Scope 成功编码。原始分类器给 `INCONCLUSIVE`，分析派生为 `OFFICIAL_PARSER_REJECTION`，不修改原结果、不认定原 SQL 无效。由此可派生 5 个前端覆盖边界（4 schema + 1 parser）；dev03_04 单独列为比较阶段非 SMT 退出。

**中止与未运行。** dev03_18 已启动 worker，最后进度是 `NATIVE_AND_OFFICIAL_IMPORT`，solver active=false、spent=0、check_count=0。监督器的 `/bin/ps -A -o pid=,pgid=,rss=,time=` 命令在 0.05 s 超时，记录 `TimeoutExpired`，随后 killpg 并 wait4 完成，exit=-9；worker CPU 0.137996 s、生命周期 wall 0.170882 s、峰值 RSS 53,952,512 B。原 results 仍为 STARTED / NOT_RUN，派生为导入期间监控中止。证据不支持将其写作 solver timeout、导入代码故障或未启动任何进程。dev03_19–21 因 `MONITOR_OR_LAUNCH_EXCEPTION` 保留 NOT_RUN，未恢复、替换或补跑。

**raw SAT 的验证边界。** 唯一 raw SAT 是 dev03_03。结果记录 `SAT_all_original_facts_and_actual_assertions_true=true`、`complete_operational_C_check=ALL_ORIGINAL_SUBMITTED_FACTS_MODEL_TRUE`，并导出完整两行 DAILYSALES 的物理模型。DATE_ID 原编码为 2、1，解为 1970-01-02、1970-01-01；VARCHAR MAKE_NAME 保留编码符号 2147483648、2147483649，LEAD_ID 为 -3、-2，PARTNER_ID 均 -1。这是对官方提交事实与实际断言在同一模型中的满足性检查。`independent_concrete_C_checker=NOT_IMPLEMENTED_FOR_GENERAL_OFFICIAL_C`；没有通用独立 C 判定、字符串/排序规则完整解码、原 SQL DBMS/SQLite 回放或业务 gold。不能把该 raw SAT 叫作已确认自然 SQL 缺陷。九个查询 UNSAT 同样只覆盖官方编码、完整原 C 与统一 exact2 形状。

**预算与成本账。** 每组上限 CPU 4 s、wall 5 s、外部监控 RSS 256 MiB；每次独立 Environment 的 C/query 名义 timeout 为 100/800 ms，至多两次，累计实际 solver wall 上限 2 s、watchdog 1.9 s。首次 query CPU≥250 ms 或 UNKNOWN 才允许复核；稳定计时信号要求两次已知同 verdict、两次 CPU 都≥250 ms 且 max/min≤2。此轮最大每组 solver wall 65.721 ms（dev03_06），所有实测调用远低于 2 s；重复次数为 0，不存在重复成本稳定性证据。采样监控不是绝对零超调的内存分配证明，回执没有记录预算违例。

完整导入阶段 CPU 合计 7.825540 s、依赖锁/哈希阶段 0.535301 s；父进程 wait4 的 18 个 worker CPU 合计 11.001694 s，含被中止与失败 worker，峰值 RSS 118,259,712 B。可观测的查询 check 成本很小，端到端主要开销包含冷启动、导入、监控及其他工作；不能据此在一般数据库规模上断言 solver 不会成为瓶颈。

|累计账项|CPU 秒|口径|
|---|---:|---|
|原扫描及首次 bootstrap 失败后的累计债务|6.876722|其中已含原扫描 6.708655，不重复加|
|stdlib 启动诊断预留|1.000000|实际诊断观察 0.148206，保守全额预留|
|batch_02 开始前冻结债务|7.876722|保留首次失败，不删除|
|batch_02 parent SELF|0.536861|user + system|
|batch_02 全部 reaped CHILDREN|16.181631|含 worker、ps、资源探测；worker wait4 11.001694 为其子集|
|累计观察 CPU|24.595214|以上有效债务 + 本批 parent/children|
|最终报告退出预留|0.100000|保守计入|
|最终保守收费|24.695214|相对于全局 120 s 上限；批次因监控故障提前结束|

batch_01 在 preexec 阶段失败，0 target exec、0 SQL、0 solver。已有同环境 stdlib 诊断把原因定位到 Darwin 的 RLIMIT_RSS 设置抛出 `current limit exceeds maximum limit`；一次预注册 bootstrap v2 仅移除该 advisory 调用，保留外部 256 MiB 监控，21 IDs、顺序、输入、frontend 与预算不变。本报告只读取该诊断与恢复回执，没有复现实验。批次开始/结束为 2026-10-11 12:41:17.484188 / 12:41:29.365968 UTC；不能把因故障提前停止说成跑完全部注册组。

**结论范围。** 全部源 schema/原 C 保留，未为准入删表、删列或删合同；类型与语法边界、C 操作语义冲突、比较阶段提前退出、监控故障与未运行分别记账。统一 exact2 指每个原物理表恰 2 个 live rows；不是至多 2 行，也不覆盖空表、单行、不同表混合基数或更大数据库。阈值聚合、连接重数等随行数变化的行为可能不能在这个形状出现，UNSAT 不提供无界等价证明。词法分层与 23 个成功 AST 的保存改善了可追溯性，但没有补齐语义认证或统计泛化。此轮支持“已测到达 solver 的 exact2 子集很快，并记录了工程覆盖边界”，不支持新的算法机制、性能收益或一般问题无瓶颈的声明。

**来源与冻结哈希。** JSON 的 `evidence` 保存全部读取的原始结果、事件、监督器回执、相关代码和协议路径、字节数与 SHA-256；`records` 保存每条原 SQL/schema/C/源行哈希。关键摘要如下。

|证据|SHA-256|
|---|---|
|[data/development_stratified.jsonl](/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_03/data/development_stratified.jsonl)|`ab80ebcf869015d324af3e35b9dd8352013e0037dec6922e7788f4cf366e4ffb`|
|[runs/batch_01/batch_receipt.json](/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_03/runs/batch_01/batch_receipt.json)|`e35ec10ed4aa6f438a5d52f3cbe3cec61eee3a16d942b39551cd0432e8b30c81`|
|[runs/batch_02/batch_receipt.json](/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_03/runs/batch_02/batch_receipt.json)|`69fb5f0d11662e2587c18ea800826abfaf234375e004eed5434c14f0b93f8878`|
|[protocols/official_diagnostic.registered_v2.json](/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_03/protocols/official_diagnostic.registered_v2.json)|`065f8574563a3cb0fab2dd98a4e64fd44fe17f66f4b32ec73a2bee9bb39b8a55`|
|[governance/BATCH_FREEZE_V2.json](/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_03/governance/BATCH_FREEZE_V2.json)|`10ebe2cbfd883a0a7f19985e0e461f9c31279ae98d7f1fe5bffe056396cfdeb7`|
|[decisions/bootstrap_amendment_01.json](/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_03/decisions/bootstrap_amendment_01.json)|`1c4b24306dc9e911e64aa6d6e87d34e5830c570aa2d5dd70410089d31cc2048d`|
|[code/official_diagnostic_backend.py](/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_03/code/official_diagnostic_backend.py)|`b599f04890b8d7cbf5b12b872a8cbf8a97a0fa74f2ac49ec9eb88fa48e115e5e`|
|[sources/verieql_v1/environment.py](/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/sources/verieql_v1/environment.py)|`99302725b9373ba91f72850790c7eb061e60d08ae1b1413f102c83bf334a9dc8`|
|[sources/verieql_v1/verifiers/verifier.py](/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/sources/verieql_v1/verifiers/verifier.py)|`9c8e51d9623ee8109afb7737e12446d7241b38c78e3723e0c13235ea4481aa07`|
|[sources/verieql_v1/parsers/sql_parser.py](/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/sources/verieql_v1/parsers/sql_parser.py)|`21867cb828df1ab5aa5b360874f93768e5fcfb7a902b1989b16ddd8fa6fd3200`|

原上游 JSONL SHA-256：`b97fc1293701682a25a2f6345f3630b3482ce49912463a7f4b76ab52665a13c9`；声明的 upstream commit：`3b99928bf976c11cb59c9db6a177adba21f75798`。本报告未重新扫描该上游文件。
