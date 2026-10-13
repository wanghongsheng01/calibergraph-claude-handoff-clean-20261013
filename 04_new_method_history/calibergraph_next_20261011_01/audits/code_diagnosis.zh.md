# CaliberGraph 下一轮：真实代码与既有日志诊断

本报告是**研究作者诊断，不是独立审查**。结论是 **SCIENCE_HOLD / 继续维持上一轮 NO_GO**：公开无 JOIN 阳性首先来自入口覆盖与完整合同门，不能称为 solver 瓶颈；工程接入存在可改之处，但当前没有已确认的新科学机制。本轮没有运行 parser、recognizer、solver、SQL、负载实验、模型 API 或 GPU，没有改写旧根、原稿或冻结结果。

旧根记为 `OLD=/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011`。下文路径以 OLD 为基准；所有源文件及证据的 SHA-256 见 `code_diagnosis.json`。全分母新计数来自对既有 `public_v4_cached/runs/run_001/slots.jsonl` 的逐行标准库聚合：1.399 秒、峰值 RSS 20,692,992 字节；没有加载或调用目标实现。结构特征会重叠，不能相加为“可修复收益”。

## 1. 实际入口与三道不同的门

**公开 applicability 入口**：`public_leetcode/scan_chunk.py:381` 调用 `kernel.ensure_raw_identifiers`，`:383` 调用 `env.parse_sql_query`，`:384` 记录 AST，`:397` 调用 v3 `recognize`。正常 Environment 初始化确实创建 solver 对象，但文件 `:3–8`、`:306–313` 明确没有数据库创建、IC 断言、encode、add/check/solve；`:388–407` 分别记录原始前端拒绝、parse/AST 记录错误、识别器拒绝。开发集入口为 `public_dev/scan_eligibility_v3_all.py`。

`Environment.parse_sql_query` 只转发到 `SQLParser.parse`（`sources/verieql_v1/environment.py:834–835`）。不是自写 SQL parser 的扫描结果。LeetCode 使用原完整 23,994 对 / 47,988 槽；开发集为 461 对 / 922 槽。

**v4 cached-AST 入口**：`public_v4_cached/scanner.py:346–406` 的 `scan_slot`。依次保留原未运行/未知状态、运行 raw guard、保留原 parser error、检查缓存 AST 存在、保留 raw guard 拒绝、检查原 constraint 字段、拒绝非 JSON AST 节点（`:389–391`）、最后调用 v4 recognizer（`:394–395`）。没有重新解析，且 `:353` 明确 parser/solver 均未调用。38 个 `utils.ValuesTable` 缓存节点变为 UNKNOWN 是表示层拒绝，既不是新增 parser 错误，也不是新增可答样本。

**v5 真正比较入口**：`runtime_fair_v5/worker.py:93–128` 先进行 raw guard、`apply_contract_bridge`、base-only SAT、完整合同 XOR 审计、合同 SAT 与 exact-row 检查，之后才进入查询工作。candidate 路径在 `:266–270` 解析与识别，`:286–293` 编码和 solver check，`:302` 进行原合同/整数域/原 SQL 回放。query ineligible 可以进入完整输入不变的 official fallback（`:277–283`），但 raw name 信息损失和合同拒绝不能走 fallback。**公开 query ELIGIBLE 不等于完整 v5 输入可准入，更不等于已完成等价验证。**

## 2. 全分母与首拒绝遮蔽

以下 v4 数值由本轮对既有槽日志重新计数，与冻结最终截面一致：

| 位置 / 状态 | 槽数 | 含义 |
|---|---:|---|
| 原始前端拒绝 | 189 | 原因全部是 SQL 中的 `$` 全串拦截 |
| 原 parser/AST 记录错误 | 1,246 | LeetCode 1,229，开发集 17；没有删分母 |
| cached AST 特殊对象 UNKNOWN | 38 | 已知表示层边界 |
| 实际到达 v4 recognizer | 47,437 | 47,431 拒绝 + 6 ELIGIBLE |
| not_simple_select | 7,498 | 最早的顶层 AST 形状门 |
| extra_select_clause | 21,894 | 只准 select/from/where；早于 FROM/SELECT 内容审查 |
| FROM 形状/表身份相关拒绝 | 12,396 | unsupported_identifier 6,889；subquery_or_non_inner_join 4,006；unknown_table_or_repeated_relation 1,453；unsupported_join 48 |
| 单输出/单聚合相关拒绝 | 5,547 | multiple_output_columns 1,754；not_single_aggregate 2,698；unsupported_aggregate 1,095 |
| 后续类型/表达式/谓词首拒绝 | 96 | non_integer_column 90；non_column_expression 4；unsupported_predicate_operator 2 |
| ELIGIBLE | 6 | 全为 leaf_count=0；两对双侧阳性 |

v3 原始分布是 INELIGIBLE 47,469、FRONTEND_UNSUPPORTED 189、PARSE_OR_AST_RECORD_ERROR 1,246、ELIGIBLE 6。v4 只把其中 38 槽保守转 UNKNOWN，未增阳性。不得把“94% 等查询非适用”写成求解器失败率。

**首拒绝不是病因互斥分类。** 新结构计数显示：

- v4 的 **6,889 个 unsupported_identifier 全部含顶层派生表 `value=dict`**。识别器 `runtime_v4/aggregate_kernel.py:140–142` 将派生表对象直接传入只接收字符串的 `identifier`（`:97–100`）。这一标签主要掩盖的是派生表支持边界，不能解读成 6,889 个标识符词法错误。其中 2,857 槽还存在多个顶层输出，3,009 槽有顶层显式 JOIN，4,769 槽任意层有显式 JOIN。
- 1,453 个 `unknown_table_or_repeated_relation` 中，**1,441 槽可直接观察到顶层重复基表**；不能统称 schema 缺失。剩余 12 槽本次未逐项归因，不把残差猜成未知表。
- 21,894 个 `extra_select_clause` 中，18,768 槽还存在多个顶层输出、16,874 槽有顶层 GROUP BY/HAVING、11,118 槽有顶层显式 JOIN。这些特征可重叠；删除一个外层键不能据此恢复原片段。
- 保存的全体 AST 中，任意层显式 JOIN 28,448 槽，顶层显式 JOIN 23,054 槽。单顶层 SUM/COUNT 形状只有 **211 槽**，其中 204 槽无顶层 GROUP BY/HAVING；这不是整个数据集没有 JOIN，而是当前输出语义非常窄。
- 顶层单 SUM/COUNT 且顶层 JOIN 或逗号 FROM 只有 **23 槽**；其中 11 槽还被顶层额外子句挡住，剩下 12 槽分别是 9 个派生表、1 个字符串等值 JOIN、1 个 LEFT JOIN+窗口、1 个无 ON 的自连接+DISTINCT+NOT IN。这里没有“大量只因别名或常数投影被误拒的简单整数 JOIN”证据。

全部 12 槽的原 SQL、缓存 AST、槽位、SQL/AST SHA 与报告位置保存在 `code_diagnosis_log_aggregate.json`；这个结构筛选不是修复后的 eligibility 重跑。

## 3. 真实近邻与完整合同障碍

最接近现片段的原始查询是 **calcite:149 q0**：

```sql
SELECT COUNT(*) FROM EMP INNER JOIN DEPT ON EMP.JOB = DEPT.NAME
```

它的顶层、COUNT(*)、基表 INNER JOIN 和根—叶等值形式均匹配；原日志首拒绝为 `non_integer_column`，因为 JOB/NAME 是 VARCHAR。对应 q1 是分组后的 count 乘积与 COALESCE/SUM，带 `EXPR$0`，在 raw guard 就被拒。只接纳 q0 仍不会得到一个可完整比较的新自然 pair。

**完整合同门比 query recognizer 更窄**：`runtime_fair_v5/contract_reference.py:42–54` 要求整个物理 schema 每个字段严格是 `INT`、大写简单名称、无 `__`；不是只检查查询引用列。`:57–133` 只支持显式 None 或 conjunction list、AND、not_null、单列与一个整数常量的比较、列 BETWEEN 整数界；PK、FK、unique、跨列比较、OR 等整体拒绝（`:119–120`），不丢弃不支持条款。

公开 6 槽中的 **calcite:142 q0/q1、calcite:266 q1、calcite:335 q1** 的原完整 schema 包含 VARCHAR/DATE/BOOLEAN，原完整 C 含 primary/foreign。静态代码推导它们在 v5 `prepare._schema` 就会停止；本轮没有运行 v5 验证此推导。只有 **literature:25 q0/q1** 的 schema 全 INT、C=None 可避开该静态门，仍不能把它们升级为已运行 v5 的两槽。calcite:149 的字符串 JOIN 也有相同完整合同障碍。

未经扩展性证明不能删掉未引用字段、未引用表或 PK/FK：与查询表关联的外键、可满足性、exact-row 数量均可能改变允许数据库集合。即使把 string equality 编成共享值等价类，也必须处理 NULL、常量、排序/比较、原 DBMS 的字符语义及全部 IC；“改成整数 ID”不是自动无损适配。

## 4. 工程过严与不可直接无损化的分界

| 代码边界 | 工程判断 | 不能据此作的主张 |
|---|---|---|
| 第一项 FROM 固定为 root（kernel `:150`）；聚合只用 root（`:233–234`） | 对受限纯 INNER JOIN 星形图，可先找合适根并重排，属于识别器改进；需保持绑定和全部谓词 | 当前日志无 `aggregate_not_root_only` 首拒绝，不能宣称已回收自然 JOIN |
| JOIN 必須有 ON，拒绝 USING（`:132–137`） | 在方言和原 schema 明确时，INNER USING 可显式展开；无 ON+WHERE 的合法 INNER/CROSS 表达可规范化 | 无条件删 USING/ON 不安全；当前唯一单 SUM/COUNT 无 ON 例还含 self join、DISTINCT、NOT IN |
| 禁止重复物理基表（`:145–146`） | 因子化恒等式本身并不必然禁止 self join；须让别名共享同一物理 bag、保留相同元组可重复绑定以及全部同表约束 | 把各别名复制成独立表会改变语义；1,441 槽不是即时修复收益 |
| WHERE 只准 AND 下的比较/BETWEEN/NULL tests（`:235–266`） | 常量 TRUE/FALSE、纯根局部 OR/IN 的安全布尔编译可工程扩展 | 跨叶 OR/比较会破坏按 root 条件独立的乘积；不是换 parser 就能处理 |
| COUNT(column) 也强制 integer 类型（`:168–169`） | COUNT 对非 NULL 任意类型的计数可通过类型感知编译扩展；现限制偏保守 | 完整 schema/IC/字符串语义仍须保真，不是新理论 |
| TOP 只准 select/from/where（`:125–128`） | 已证明只有一行输出时某些 ORDER BY/LIMIT≥1 可冗余化；需确认合法性和错误语义 | GROUP BY、HAVING、窗口、LIMIT 0/OFFSET、一般 DISTINCT/多输出不能直接去掉 |
| 派生表 `value=dict` 报 unsupported_identifier | 可改诊断标签；纯投影/重命名/局部选择可在精确条件下下推或展开 | 聚合、DISTINCT、窗口、子查询反连接、outer join 的派生表不能统统 inline 成原片段 |
| raw guard 在原 SQL 任意位置看见 `$`/引号就拒绝（`:48–51`） | token-aware、双向绑定的名字编码能扩大前端，原文仍保留 | 不能从已变形 AST 猜回名称，也不能说189槽都可回收；许多 q1 是复杂聚合重写 |

简单表别名和输出别名本来就支持（`:140–142`、`:221`）；COUNT(非 NULL 整数常量) 在 v3 和 v4 都已支持（v3 `:178–179`，v4 `:229–230`）。v4 已扩展整数 +、−、× 和 BETWEEN；这些并没有给公开分母新增一个阳性。把已有支持说成新修复不准确。

源 parser 还有独立保真风险，不能用 raw-name guard 一概覆盖：`sql_parser.py:88–92` 是全串 `$` / IS TRUE/FALSE / SELECT ALL 替换，`:167` 整条 SQL upper-case（包括原字符串文字），`:108–159` 把一些数字样式字符串 literal 变成数值并抹去 literal 类型标签，`:150` 对普通字符串替换点。原始日志中 `calcite:52 q0` 的 `WHERE NULL = 1` 已记录成 `{"missing":1}`，最终因 non_column_expression 被拒绝；这是当前拒绝保守挡住的例子，不是这6个阳性的已证错误。扩大 strings/NULL/表达式之前须建立原文→AST 的带类型语义保真；只复用旧 AST 或作逆字符串替换无法保证无损。本轮不运行构造 SQL，也不声称已发现新的可接受错误样本。

## 5. 精确语义与成本边界

受限编码是数学整数、NULL-strict 的 scalar SUM/COUNT、root-local measure、每叶只与 root 相连且至少一个等值连接、没有跨叶谓词。`kernel.py:329–343` 将 WHERE/ON 的 true 定义为参与值非 NULL 且比较为真；`:390–393` 的 SUM null flag 是贡献数为0，COUNT 从不输出 NULL。`unequal :396–400` 比较 null flag，并仅在双方非 NULL 时比较值。

对 root 行数 n0、叶行数 n1…nk，flat `:366–373` 显式枚举 n0×∏nj 个绑定；product/selector `:375–387` 构造 n0×Σnj 个匹配项。product `:353–355` 保留变量乘积；selector `:356–358` 枚举 count 的 0…nj，使用常系数分支。这是已有乘积/有限域编码构件，不是新机制。root measure 的变量乘法、完整 IC 仍可引入非线性（`:76–82`、`:276–277`）；不能宣称完整公式变成 LIA。非星形 JOIN 需要新的条件分解或其他关系编码，不能只移除 cross_leaf 拒绝后继续用独立计数相乘。

v5 的每一次查询工作之前都可能有四次有界验证：base-only SAT 与 contract XOR UNSAT（common `:172–214`），以及完整 C SAT 与删除任一 base row 的 UNSAT（`:269–279`）；每次独立上限1秒但共享总预算。`budget_ms :255–259` 使用剩余 14 CPU 秒与24墙钟秒并留储备。candidate unknown 后只有至少500毫秒剩余才 official fallback（worker `:312–323`）。kernel `:295–296` 与 common `:319–322` 拒绝零 base rows，当前实验用正 exact rows，不是无界数据库完整性结果。

既有冻结 v5 六臂成本如下；均为每臂28个选定返回观察，包含失败与拒绝，没有重复试次。官方臂另有一个中断尝试，完整成本未知，不混入合计：

| arm | 严格结果 / 28 | 已知完整冷 CPU 秒 | semantic-e2e CPU 秒 | 解释 |
|---|---:|---:|---:|---|
| official | 20 | 62.612200 | 30.018551 | 另1次中断完整成本缺失 |
| official_generic_smt | 21 | 63.179959 | 29.601380 | 同完整输入 |
| flat | 23 | 37.110296 | 4.204929 | 不是 official 强基线 |
| product | 19 | 73.661139 | 40.454255 | 已知乘积控制 |
| selector | 22 | 36.793204 | 3.641322 | 和 flat 接近但结果混合不同 |
| cheap AND | 22 | 50.485388 | 17.247449 | AND 顺序控制 |

因此冷进程 CPU 不能直接充当 solver 用时；flat 的上述两个合计就相差32.905367秒，包含初始化/锁核验/导入等成本。现数据不能将 selector 的0.317092秒总差异解释为稳定加速。S01 N4 中 flat、selector、cheap AND 均严格 UNSAT，CPU 分别1.314、1.312、1.298秒；official/generic unknown；product原UNSAT伴随RSS观测失败，不能算严格成功。这个对照已经反驳“此例收益专属于selector”。

main_cost 的168槽最终派生为127严格结果、24合同类型拒绝、7 solver unknown、6 oracle域未证、4资源观测停止。全部阶段11个资源停止都是 `RSS_OBSERVATION_UNAVAILABLE`，不是 OOM 或实际内存上限。公开扫描没有调用 solver，只有开发控制上有这些真实 solver/成本记录；不能串联成“公开 JOIN 已证可接入、仅待 solver 提速”的论证。

## 6. 先验威胁与科学候选结论

本代码任务没有独立开展文献检索。父任务要求的威胁清单作为待严格比对的先验：Polygon 已处理 JOIN/OUTER JOIN 与欠近似冲突搜索；VeriEQL 处理丰富 IC 与 NULL；FewRows 的 key-anchorable 查询与 acyclic FK 可能已覆盖所设想的完整反例界；父任务另提示 WeTune 约束合成、OOPSLA 反例保持剪枝、PODS 2009 聚合等价。必须依据它们的真实定理假设比较，不能只比较标题或功能表。

**本轮确认的科学机制候选为0。** 父任务随后交叉核对后明确：固定 leaf EXISTS 经 E 投影及 weakly-acyclic chase 的方向已被 PODS 2009 覆盖；简单 one-witness 剪枝还会抹掉 EXISTS 返回1、对应 bag JOIN 返回2的实际差异。本代码任务没有重新证明该文献归属，其依据应由父任务的理论/文献材料绑定；这里不保留一个换名的 EXISTS 科学候选。现代码也没有给出超出这些先例的新支持界、剪枝保持定理或自然 JOIN 求解优势。

进入下一步前最小可审查材料应是：小规模自然 JOIN 原 pair 的完整 schema/C/SQL 绑定，逐条标明首拒绝与后续障碍；任何适配给出保真条件及不能适配的保留槽；文献逐假设碰撞检查通过后，再决定是否值得实现新机制。parser 修复、诊断拆分、类型放宽、AND 因式分解、selector/product 改名都不足以关闭科学 NO_GO。

## 7. 交付与边界

- `code_diagnosis_log_aggregate.py`：本轮唯一执行的全槽日志结构聚合器，纯标准库、流式、45秒硬性协作预算检查、不导入目标模块。
- `code_diagnosis_log_aggregate.json`：48,910槽状态复计、首拒绝交叉特征、12个自然近邻原SQL/AST及来源。
- `code_diagnosis.json`：源码行范围、冻结hash核对、原6阳性完整schema/合同静态障碍、既有成本摘要、资源回执与本轮文件清单。

后续独审由另一任务完成；本报告不预先声称通过。远程备份/上传未执行，沿父任务的本地隔离边界交付；不把本地新文件称为远程备份。
