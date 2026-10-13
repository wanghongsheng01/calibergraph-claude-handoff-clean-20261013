# 第三轮来源分层选样账本摘要

冻结静态扫描已完成：从 **24,455 个 pair / 48,910 个 SQL 槽**登记 **21 个不同来源标签组、21 个原 pair、42 个不同 SQL 字节哈希**。这是开发集，科学状态仍为 **HOLD**；不能把来源标签去重表述为语义或统计独立。

`COMPLETE_STATIC_SELECTION_NOT_EXECUTED` 表示选样已完成、该扫描没有执行 parser、SQL 或 solver，并非扫描未运行。本摘要只复算扫描账本与已选结果，不评价本轮其他运行。独立子审从三份账本复算得到相同计数。

## 全部分母与来源边界

| 来源 | pair 数 | 纳入主选样的边界 | C 状态 |
|---|---:|---|---|
| Calcite | 397 | 全部盘点；仅 benchmark/index，独立 rule/test 出处未建立，主选样排除 | PRESENT_JSON 397 |
| Literature | 64 | 63 个 name 标签的上游改写工程例，单列非自然控制，不填补空层 | PRESENT_JSON 6；NULL_UNSPECIFIED 58 |
| LeetCode | 23,994 | 按原 file 标签分组；56 标签减原开发6组、opaque reserve 4组后剩46标签，44标签出现候选 | PRESENT_JSON 23,037；NULL_UNSPECIFIED 957 |

| 互斥清单状态 | pair 数 |
|---|---:|
| `SOURCE_GROUP_NOT_ESTABLISHED` | 397 |
| `UPSTREAM_REWRITTEN_NONNATURAL_CONTROL_NOT_PRIMARY` | 64 |
| `STRATUM_CANDIDATE_BEFORE_GROUP_MEDIAN_AND_DEDUP` | 16,095 |
| `PREVIOUS_DEVELOPMENT_GROUP_EXCLUDED` | 3,256 |
| `NO_REGISTERED_LEXICAL_STRATUM` | 2,495 |
| `INVENTORY_FAILURE_RETAINED_NO_REPLACEMENT` | 16 |
| `KNOWN_RESERVE_GROUP_EXCLUDED_BEFORE_SQL_DECODE` | 2,132 |
| **合计** | **24,455** |

46 个剩余标签中，610.csv 和 627.csv 在本协议下没有分层候选；这不能推断其 SQL 不具备任何有用结构。候选共 16,095 pairs，其中 PRESENT_JSON 15,441、NULL_UNSPECIFIED 654。null 候选未因合同来源不足而替换或抹去。

## 分层结果与短缺

分层是预注册的词法近似，任一原 query 命中即按 S1→S8 首匹配；没有解析语义 AST，也没有确认相关性或关系绑定。优先级依次为集合操作、派生表内聚合、IN/EXISTS 或可能相关提示、outer join、自连接/重复关系、至少3张表、连接聚合、纯连接非聚合。复杂结构常先归入前层，后层空缺不是全源缺少该 SQL 语义结构的证据。

每个“来源标签×层”按 token 复杂度和固定哈希排序取下中位数；组顺序采用固定 seed 哈希。每层上限4且每标签只选1 pair。不以 solver 结果、SQL 可运行性或最短 pair 选样，也不从其他来源或层补足。

| 层 | 候选 pairs | 候选标签 | 选中 | 前层已选去重 | 达上限未选 | 缺口 |
|---|---:|---:|---:|---:|---:|---:|
| S1_SET_OPERATION | 2,374 | 29 | 4 | 0 | 25 | 0 |
| S2_DERIVED_TABLE_AGGREGATE | 5,756 | 30 | 4 | 1 | 25 | 0 |
| S3_IN_EXISTS_OR_CORRELATED_HINT | 4,385 | 30 | 4 | 1 | 25 | 0 |
| S4_OUTER_JOIN | 2,199 | 18 | 4 | 3 | 11 | 0 |
| S5_SELF_OR_REPEATED_RELATION | 1,377 | 13 | 4 | 5 | 4 | 0 |
| S6_MULTI_JOIN_3_TABLES | 3 | 1 | 1 | 0 | 0 | 3 |
| S7_JOIN_AGGREGATE | 1 | 1 | 0 | 1 | 0 | 4 |
| S8_PURE_JOIN_NONAGGREGATE | 0 | 0 | 0 | 0 | 0 | 4 |
| **合计** | **16,095** | **122 次组×层记录 / 44 不同标签** | **21** | **11** | **90** | **11** |

S1–S5 各满4组。S6只有 607.csv 的3个候选 pair，选其下中位数1个，缺3；S7唯一候选来自 1149.csv，该标签已在S5选中，故缺4；S8在前置排除和互斥首匹配后没有候选，缺4。没有发生“跨已选组 SQL 哈希重复”排除，已选42条 SQL 哈希均不同。

| 本层去重 | 原 file 标签 | 已在前层选中 |
|---|---|---|
| S2 | 1468.csv | S1 / dev03_04 |
| S3 | 1693.csv | S1 / dev03_03 |
| S4 | 1693.csv | S1 / dev03_03 |
| S4 | 1747.csv | S3 / dev03_09 |
| S4 | 1173.csv | S2 / dev03_07 |
| S5 | 584.csv | S1 / dev03_02 |
| S5 | 1747.csv | S3 / dev03_09 |
| S5 | 1777.csv | S4 / dev03_16 |
| S5 | 1173.csv | S2 / dev03_07 |
| S5 | 1693.csv | S1 / dev03_03 |
| S7 | 1149.csv | S5 / dev03_20 |

上述11次是实际发生的首个适用状态；层已满后，90条记录直接标为达上限，未再判断组重复或 SQL 重复，因此11不是所有潜在跨层重复的总数。哈希去重只消除完全相同的 SQL 字节，不消除语义等价、共同模板、题目相似或来源相关性。

## 16 条失败的具体账本原因

全部为 LeetCode、C 形状均为 PRESENT_JSON：7条 `UNBALANCED_LEXICAL_PARENTHESES`（词法括号计数不平衡），9条 `UNSUPPORTED_LEXICAL_CHARACTER`（预注册词法器不支持的字符）。这是盘点器失败，不是已经确认的 SQL 错误或自然缺陷。账本未记录出错字符、字符偏移或 pair 中哪一侧失败，本摘要不重新读原 SQL，因此不猜测这些细节。

| 原 JSONL 行号（1起） | 原 file 标签 | 上游 index（原值） | 词法失败原因 |
|---:|---|---:|---|
| 1682 | 550.csv | 326 | UNBALANCED_LEXICAL_PARENTHESES |
| 4593 | 613.csv | 125 | UNSUPPORTED_LEXICAL_CHARACTER |
| 5717 | 627.csv | 15 | UNSUPPORTED_LEXICAL_CHARACTER |
| 5725 | 627.csv | 23 | UNSUPPORTED_LEXICAL_CHARACTER |
| 5742 | 627.csv | 40 | UNSUPPORTED_LEXICAL_CHARACTER |
| 6136 | 1050.csv | 0 | UNSUPPORTED_LEXICAL_CHARACTER |
| 8537 | 1097.csv | 0 | UNBALANCED_LEXICAL_PARENTHESES |
| 9858 | 1132.csv | 129 | UNBALANCED_LEXICAL_PARENTHESES |
| 9859 | 1132.csv | 130 | UNBALANCED_LEXICAL_PARENTHESES |
| 11695 | 1173.csv | 314 | UNBALANCED_LEXICAL_PARENTHESES |
| 13051 | 1264.csv | 35 | UNBALANCED_LEXICAL_PARENTHESES |
| 15047 | 1398.csv | 168 | UNBALANCED_LEXICAL_PARENTHESES |
| 15381 | 1398.csv | 502 | UNSUPPORTED_LEXICAL_CHARACTER |
| 15509 | 1398.csv | 630 | UNSUPPORTED_LEXICAL_CHARACTER |
| 16883 | 1440.csv | 612 | UNSUPPORTED_LEXICAL_CHARACTER |
| 20037 | 1683.csv | 29 | UNSUPPORTED_LEXICAL_CHARACTER |

16条均保留在总分母，未修复、重扫或按可运行性补换。逐条原始行哈希、SQL 哈希、字节定位和错误类型完整保存在伴随 JSON；这也允许区分同一标签中失败记录与预定中位数选中的另一原 pair。

## 已选来源定位与合同状态

全部选自冻结 LeetCode JSONL，file 标签前缀均为 `benchmark/leetcode/raw_data/`。下表“行”定位该快照，“index”是未修改的上游字段。完整快照路径、source/rawline/schema/C/SQL 哈希和选样秩见伴随 JSON；原 schema、C、SQL 保存在冻结 `data/development_stratified.jsonl`，本摘要未改写。

| Case | 层 | file 标签 | index | 原 JSONL 行 | C 状态 | 下中位数秩/组层候选 |
|---|---|---|---:|---:|---|---:|
| dev03_01 | S1 | 1127.csv | 171 | 9581 | PRESENT_JSON | 160/319 |
| dev03_02 | S1 | 584.csv | 48 | 2421 | PRESENT_JSON | 1/1 |
| dev03_03 | S1 | 1693.csv | 64 | 20110 | PRESENT_JSON | 1/1 |
| dev03_04 | S1 | 1468.csv | 250 | 17255 | PRESENT_JSON | 1/2 |
| dev03_05 | S2 | 1132.csv | 292 | 10021 | PRESENT_JSON | 384/768 |
| dev03_06 | S2 | 1783.csv | 41 | 21931 | PRESENT_JSON | 140/280 |
| dev03_07 | S2 | 1173.csv | 34 | 11415 | PRESENT_JSON | 20/39 |
| dev03_08 | S2 | 183.csv | 197 | 580 | PRESENT_JSON | 2/3 |
| dev03_09 | S3 | 1747.csv | 410 | 21639 | PRESENT_JSON | 5/9 |
| dev03_10 | S3 | 1264.csv | 25 | 13041 | PRESENT_JSON | 111/222 |
| dev03_11 | S3 | 511.csv | 67 | 673 | PRESENT_JSON | 3/5 |
| dev03_12 | S3 | 577.csv | 88 | 2173 | PRESENT_JSON | 6/11 |
| dev03_13 | S4 | 1677.csv | 344 | 19915 | PRESENT_JSON | 202/404 |
| dev03_14 | S4 | 613.csv | 45 | 4513 | PRESENT_JSON | 5/10 |
| dev03_15 | S4 | 1421.csv | 21 | 15534 | PRESENT_JSON | 198/396 |
| dev03_16 | S4 | 1777.csv | 95 | 21819 | PRESENT_JSON | 18/35 |
| dev03_17 | S5 | 1211.csv | 390 | 12206 | PRESENT_JSON | 3/6 |
| dev03_18 | S5 | 596.csv | 73 | 2924 | PRESENT_JSON | 1/1 |
| dev03_19 | S5 | 1683.csv | 14 | 20022 | PRESENT_JSON | 1/1 |
| dev03_20 | S5 | 1149.csv | 221 | 11280 | NULL_UNSPECIFIED | 11/22 |
| dev03_21 | S6 | 607.csv | 751 | 4241 | PRESENT_JSON | 2/3 |

已选20组 C 为 PRESENT_JSON，仅表示 benchmark 声明了非空约束对象列表，未证明业务真实性或编码正确；dev03_20（1149.csv）为 NULL_UNSPECIFIED，表示上游未明确给出额外C，不能解释成已验证“无业务约束”。该 slot 保留，不换样。`[]` 的 EXPLICIT_EMPTY_OPERATIONAL、MISSING、INSUFFICIENT 在本次三源清单中均为0；这些状态不能与 null 合并。

## 可支持与不可支持的结论

21个不同 file 标签和42个 SQL 字节哈希提供可复算的工程去重；它们不足以证明21个语义或统计独立问题。Calcite 的每个 index 不视为独立出处，literature 的不同 name 也仅是标签近似分组。

已选原记录只有 constraint/file/index/pair/schema 五类字段；存在一个公开 pair 不等于存在可信的“正确 SQL—自然缺陷 SQL”业务金标。全部保持 `business_contract_truth=UNVERIFIED`、`pair_label_truth=UNVERIFIED`、`SQL_semantic_fidelity=UNPROVEN`、`natural_business_origin=UNKNOWN`。在声明C下考察官方运营编码性能是后续工程诊断范围，不能把它直接称为真实业务瓶颈。

49k全部槽已有历史 applicability 曝光，本轮又增加了词法开发选样；已选和既知 reserve 均不能宣称全新、完全未暴露的终测。本摘要只读取既有扫描中的 opaque reserve 排除记账，不打开 reserve 文件、不还原其身份或解码其 SQL。没有可信隐藏 gold 与操作系统隔离证明，状态维持 HOLD。

## 证据绑定

- 冻结选样协议 SHA-256：`7ec169d8764209be57a533cde6fd0a2dd425814b5772678d692820361534e121`。
- 两份选中 JSONL 字节一致，SHA-256：`ab80ebcf869015d324af3e35b9dd8352013e0037dec6922e7788f4cf366e4ffb`。
- 扫描 guard 返回 `RETURNED`、worker exit `0`；wall 6.411s，账面累计 CPU 6.609s；worker peak RSS 33.19 MiB。资源值仅为扫描回执，非方法性能结果。
- 本次新增工作仅为账本读取、计数、哈希绑定和这两份摘要；没有运行 parser、SQL、solver、重新扫描源快照或修改冻结文件。

机器可读摘要包含各证据文件完整路径与 SHA-256、全部16失败条目、122次组层记录的状态聚合、11次实际跨层去重及21条已选来源定位。
