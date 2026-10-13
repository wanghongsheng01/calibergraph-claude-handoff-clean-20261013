# 第16轮原四来源：exact-live、fullC 与来源保留审计

结论：本轮静态审计未发现这四个实际输入的 SQL、schema 或 constraint 被删减；固定路径仍为 **EXACT_LIVE_PER_TABLE**。没有建立由 exact2/3/4 推出 up-to4 的补齐或单调性证书。11 条原 C 都有官方编码分支；独立 SQLite 回放只覆盖两个 INT pair 的 7 条 C，另两个来源整组保留未认证边界。上述事实不代替本轮运行结果，也不授予科学执行权限。

2026-10-11，只读一手代码、已有记录和原文；未执行 SQL、SMT、目标 import/compile、数据库枚举或科学测试。未改冻结旧根。仅按已有偏移定点读取四条原始行，未扫描 48,910 条查询。所有输出为审计说明、字段清单、来源与哈希，不包含第三方原始 SQL。私有备份由 root 统一完成；本审计不声称 BACKUP_OK。DataHub 沿用父任务路由与注册阻塞记录。

## 1. exact-live 的真实执行链和可推出的结论

官方固定提交为 `3b99928bf976c11cb59c9db6a177adba21f75798`。以下官方相对路径均位于冻结旧根的 `sources/verieql_v1/`；哈希见 `SHA256SUMS.inputs`。

| 路径 | 静态事实 |
|---|---|
| `environment.py:518,580–591` | 生成 N 个基表符号元组，584 对每个加入 `Not(DELETED)`。NULL 单元格不等于不存在的行。 |
| `verifiers/verifier.py:79–91,127` | `DBMS_facts`、查询编码及附加界进入前提，并构成前提蕴含输出等价。 |
| `environment.py:942–952` | 否定上述蕴含后调用 solver；因此搜索满足前提的输出差异。 |
| `parallel/cli_within_bound.py:35–43,97,139–140` | 所查无已有 states 的路径对所有表使用同一标量，遍历 1…N，并在非 EQUIV 时停止；不是逐表基数向量遍历。 |
| `verifiers/bag_semantics_verifier.py:110–159` | 比较输出大小与 NULL-aware 值重数，新增活行不能自动视为没有影响。 |
| 第16轮 `implementation/official_generation_backend.py:279–289` | 对原 schema 每张表传同一 exact_rows_per_table，并将完整原 constraint 传入 add_constraints。 |

论文 Def.3.5 的定义量化每关系至多 N 个元组；Thm.4.8 针对论文 Verify 给出保证。这是论文主张，不能直接替代上述固定路径的代码覆盖审计。[VeriEQL v2，§3.5、§4.5](https://arxiv.org/html/2403.03193v2#S3.SS5)。本轮重读原文，只据其界定义与定理对象作区分，没有复算或独立证明定理。

| 来源 | 物理表数 | 完整运行官方 1…N 标量 driver 仍缺什么 | 本轮仅 2/3/4 还缺什么 |
|---|---:|---|---|
| dev03_07 / 1173 | 1 | 空表 | 基数 1，以及空表 |
| dev03_10 / 1264 | 2 | 含空表及两表不等基数 | 基数 1、含空表与不等基数向量 |
| dev03_15 / 1421 | 2 | 含空表及两表不等基数 | 基数 1、含空表与不等基数向量 |
| dev03_04 / 1468 | 1 | 空表 | 基数 1，以及空表 |

这张表说明计划输入域，而不是声称未运行的单元已经完成。原 C 不要求 1264 或 1421 的两表等基数；1421 的部分键 FK 也不蕴含该条件。exact2、exact3、exact4 的输入域本身不嵌套。有限 UNSAT 只能标为该 exact 向量下的官方编码结果；UNKNOWN、超时、编码错误或未执行均不是不等价。若出现 SAT，仍须完整原 C 验证与原 SQL 同语义回放才能提升为有效具体反例。独立 C-check 先行可避免把空前提下的 UNSAT 误作有内容的等价证据。

## 2. 现成补齐理由核查

所查代码和既有四 pair 控制没有提供统一补齐证书。这里既不证明补齐不可能，也不编造其存在。

- 四来源均有 PK，简单复制旧行会破坏唯一性，添加 NULL 主键会破坏非空。使用新键仍可能改变连接、聚合及输出重数。
- 1173 的计数比率与 ROUND、1468 的分组 MAX/连回/UNION/ROUND 均使“添行不影响差异”需要针对原式论证；不能用普通数据扩展直觉替代。
- 1264 的 NOT IN、1421 的外连接及引用约束也没有通用差异保持填充依据。此句是证明义务提示，不是对每个 pair 的形式化不可能结论。
- `environment.py:607` 取全部槽位；PK `627–645`、FK `646–656`、比较 `695–750` 无 live guard。**仅删除 584 的存活事实不足以声称 up-to**：还须证明可选槽位下 IC 和查询编码保持所要语义。

若要以补齐支持 exact-N 完备性，至少须针对每个 pair 证明：任何满足原 fullC、类型和 NULL/方言约定的较小或混合基数区分数据库，都能变为目标统一 exact-N 的数据库，并保留 fullC 和查询差异。当前没有该证书；本轮也不改变编码或新增测试来追求它。

既有 `protocols/ANALYTIC_CONTROLS.round06_verbatim.zh.md` 对 1264 保留 CASE 默认 NULL、内连接换序等解析依据；对 1421 保留 LEFT/RIGHT 保留侧反转、行相等与分量 AND、限定整数的 IFNULL/COALESCE 恒等式。这些是已知 pair 级强控制。本次没有重新展开 SQL 作独立逐式证明；即使完成它们的任意基数等价证明，也只直接解决这两个 pair，不能证明 frozen encoder 的空表/混合基数覆盖，更不能移用于另外两个 pair。

## 3. 原始记录和 provenance 是否完整

原21 registry 是 `03/data/development_stratified.jsonl`，新核 SHA256 为 `ab80ebcf869015d324af3e35b9dd8352013e0037dec6922e7788f4cf366e4ffb`。只检查既定 indices `[6,9,14,3]`。每个原 source_record 恰有 `constraint,file,index,pair,schema` 五个字段；四个字段树清单、17 个 schema 列及类型、11 个顶层 C 节点均记录在 `four_source_identity_evidence.json`。没有用省略字段后的对象冒充完整输入。

| registry index / ID | 原 source_record.index | 来源行（继承） | 定点 byte_offset / length | 本次核验 |
|---|---:|---:|---|---|
| 6 / dev03_07 | 34 | 11415 | 10281770 / 696 | raw SHA、完整对象、两 SQL、schema、C 哈希全部一致 |
| 9 / dev03_10 | 25 | 13041 | 11740517 / 992 | 同上 |
| 14 / dev03_15 | 21 | 15534 | 14576795 / 678 | 同上 |
| 3 / dev03_04 | 250 | 17255 | 16536488 / 1232 | 同上 |

定点四个不同切片合计 3598 字节，重复用于哈希/对象比较但未向备份写入 raw。上游整文件 SHA 与 line_1based 保留为**继承、未整文件重哈希/未重新数行**；本次独立确认的是保存偏移处原始字节和完整 JSON 对象。不能把它扩大为重新认证整个上游文件、全部行号、LeetCode 接受标签或业务合同真值。

第06轮 `selected_source_groups.jsonl` 的全部 source_record 与 source 均 4/4 等于原 registry；其新核 SHA 为 `7f69acd83f3e18cd4a1daae6c00eb909209948f7dfd7e219fd3456b1c3b1b668`。但它是选择投影，未复制原 registry 的顶层 `exposure,provenance_eligibility,selection,status`；不能说整个 registry 记录逐字段复制。上述元数据仍保留在原21文件。第16轮 `generation_common.py:90–122` 直接加载原21 registry、核其全文件 SHA 和所选 SQL/schema/C；worker `67–80` 记录完整 original_source_record、source 与 provenance_eligibility。因此未发现实际运行输入丢原 C 或丢物理字段。所有来源仍是已暴露开发集；业务真实性、标签真值和 SQL 编码忠实性保持原未知/未证明标签。

## 4. 每一条 C 的 admission → 官方编码 → replay 映射

`official_contract_admission.py` 和 `safe_sqlite_replay.py` 第16轮分别与第15轮逐文件 SHA 相等。此处“支持”只表示静态分支与原操作数匹配；没有执行 admission 或 replay，也不声称其一般实现已形式化验证。

| pair / clause index | 原约束含义（字段完整） | admission / 官方操作语义 | 独立回放边界 |
|---|---|---|---|
| 1173 / 0 | DELIVERY.DELIVERY_ID 主键 | primary：所有槽位该列非 NULL且唯一 | 整组未准入；不单独跳过 DATE 后校验 |
| 1173 / 1 | DELIVERY.ORDER_DATE ≤ DELIVERY.CUSTOMER_PREF_DELIVERY_DATE | lte：每个 ORDER_DATE 与每个偏好日期比较，双方非 NULL；并非仅同行 | 整组未准入：DATE、除法、ROUND 未认证 |
| 1264 / 0 | FRIENDSHIP.(USER1_ID,USER2_ID) 主键 | 两列均非 NULL；复合元组唯一，不加强为各列分别唯一 | checker primary 完整两列 |
| 1264 / 1 | LIKES.(USER_ID,PAGE_ID) 主键 | 同上，完整复合键 | checker primary 完整两列 |
| 1264 / 2 | FRIENDSHIP.USER1_ID ≠ FRIENDSHIP.USER2_ID | neq：两列全笛卡尔组合非 NULL且不相等，强于同行 neq | checker product 完全沿用该 operational C |
| 1421 / 0 | NPV.(ID,YEAR) 主键 | 完整复合键非 NULL且唯一 | checker primary 完整两列 |
| 1421 / 1 | QUERIES.(ID,YEAR) 主键 | 完整复合键非 NULL且唯一 | checker primary 完整两列 |
| 1421 / 2 | QUERIES.ID → NPV.ID | 每个源 ID 非 NULL且有非 NULL等值目标；不要求 NPV.ID 单列唯一、不要求 YEAR 匹配 | checker foreign 原样存在性；没有补复合 FK |
| 1421 / 3 | NPV.NPV ≥ 0 | gte：逐值非 NULL且 ≥0 | checker scalar comparison |
| 1468 / 0 | SALARIES.(COMPANY_ID,EMPLOYEE_ID) 主键 | 完整复合键非 NULL且唯一 | 整组未准入；不删 EMPLOYEE_NAME 绕过 VARCHAR |
| 1468 / 1 | SALARIES.SALARY > 0 | gt：逐值非 NULL且 >0 | 整组未准入：VARCHAR 解码与小数 ROUND 未认证 |

来源定位：admission `151–179,203–227`；官方 `environment.py:627–656,695–750,779–782`，`utils.py:42–46` 的 equality/inequality 要求两端非 NULL；replay `25–44,47–120`。官方 operational C 的全列比较和不可空 foreign 与通常同行 CHECK/可空 SQL DDL FK 的区别有意保留，不能默默换成“业务应该如此”。没有原始业务合同认证，本轮仍为 UNKNOWN。

schema 还隐含类型界：官方 `environment.py:555–578`、`constants.py:49–57` 分别给 INT32、日期区间、VARCHAR 的整数编码；这些不计入原11条显式 C。回放 `55–68` 检查完整表集合、exact 行数、完整列集合及 INT32/NULL；两个准入 pair 的 9 列全部 INT。它对 DATE/VARCHAR fail closed，不提供一般字符串/日期翻译承诺。`in/between/inc` 等较宽 admission 分支不在本四 pair 的 C 中，不能据此声称 replay 也支持它们。

回放 `147–157` 先匹配完整 pair/schema/C 哈希再独立验证 C；`168–175` 创建每个原物理字段；`193–213` 原样执行两 SQL，按 INT/NULL 的 bag 重数比较。两个 profile 无 ORDER BY；此处不授予任意 ORDER BY/list 回放能力。1264 要求 SQLite≥3.8.3，1421 的 RIGHT JOIN 要求≥3.39。未建立“整个官方编码对所有可能输入与 SQLite 一致”的一般证明。

## 5. 结果标签与恢复

`C_MODEL_SANITY_ONLY_NOT_QUERY_SAT` 来自单独 C-check 的模型，即使回放满足全部 C 且输出相同，也只检查生成/回放链。它不是 query-SAT、不是真实缺陷、更不是新机制效果。第16轮 backend `273–275,308–329` 明示该标签；只有 query-SAT 导出经完整验证和回放差异后才可提升为具体见证，来源真实性还须另证。

本审计交付 `SEMANTICS_AUDIT.zh.md`、`four_source_identity_evidence.json`、`constraint_mapping_evidence.json` 和输入/输出哈希。复核时从原21已冻结文件取上述四记录；只 seek 四个已保存 byte slice，核 SHA 后比较完整对象，核各 SQL UTF-8 与 canonical JSON schema/C 哈希。重开文中固定提交代码和论文定位。不要恢复或备份第三方 raw SQL 数据副本；缺本地来源时使用上游受许可来源恢复、核 pin/hash，缺失则记录 UNKNOWN/BLOCKED，不能构造替代数据。历史 raw evidence/native runtime 恢复与 DataHub 注册阻塞由 root 保持原状态。
