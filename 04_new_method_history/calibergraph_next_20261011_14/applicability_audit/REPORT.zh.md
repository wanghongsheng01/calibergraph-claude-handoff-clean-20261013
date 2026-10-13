# H14 对既有 21 对开发记录的整对静态适用性审计

作者结论：**直接适用 0/21，整对明确排除 21/21，UNCERTAIN 0/21。** 全部 21 对均逐对阅读，没有剔除、补采或替换。状态是作者冻结、待 root 或另一人复核；本报告不承担 H14 数学独审。

这是对给定理论片段与已有完整 SQL pair 的人工适用性判定，不是科学效果测试，不是新 test。业务自然性仍为 **UNKNOWN**；所有记录已经开发暴露，source group 只是文件标签，不提供统计独立保证。0/21 不意味着 H14 数学命题失败，也不能外推总体自然工作负载适用率。

## 输入与规则

本次读取 H14 `theory/theory.md`，SHA-256 为 `3925237a0f59110b505982187c56ee92656531d34b67184184f8b892b7d3ff03`。该片段要求共同有限、安全、纯变量 relational core body，且 End(B)=Aut(B)，基表为集合、仅满元组 PK、无 FK 或其他 FD/条件约束；共同 head H，M/N 属于 V 去 H 的子集，比较存在投影去重后的计数。常量、比较、NULL、算术、MIN/SUM 等额外值聚合、外连接及否定等完整操作没有在该声明中获得授权。

开发 registry 的 SHA-256 为 `ab80ebcf869015d324af3e35b9dd8352013e0037dec6922e7788f4cf366e4ffb`。逐对判定依据是 `source_record.pair/schema/constraint`；身份、source group 和 query SHA 用于溯源。42 条原始 query 字符串的 UTF-8 SHA 均与 registry 已记的 query SHA 一致，未据 pair 标签或任何执行结果挑选。

下列每行都给出至少一个整对的充分排除理由。原记录中的 PK/FK/值限制只作为记录所声称的 contract 阅读，业务真实性未核验；每行已有独立的完整查询算子排除理由，因此不靠把这些 contract 当成已验证事实来凑排除数。发现充分排除条件后不再假装证明 common-body/core promise。`COUNT` 或自连接本身不自动排除：H14 允许投影计数及自连接，排除的是表中列明的完整组合、阈值、其他聚合或比较语义。

直接适用判定保留原始整对。没有抽取、简化、修补、最小化或重写子式；即使可以提出某种未来的语义保持转换，也必须另行证明完整语义和所有 promise，不能把子式写成原自然整对已覆盖。本审计也不声称所有可能的语义保持转换均不可能。

## 全部 21 对

source group 均以 `leetcode:benchmark/leetcode/raw_data/` 为前缀；完整 group 和每对两个 query SHA 保存在 [applicability.json](applicability.json)，没有复制第三方 SQL 全文。

| ID | source 文件 | 整对排除的人工理由 |
|---|---|---|
| dev03_01 | 1127.csv | SUM 金额聚合、外连接、NULL 填补和平台常量 UNION。 |
| dev03_02 | 584.csv | 常量非相等比较、IS NULL、OR / UNION ALL；另记录非满元组 key 与 FK。 |
| dev03_03 | 1693.csv | 第二式含标识加一、零哨兵、UNION ALL 与 CASE/SUM；不能只取第一式的 distinct-count 子式。 |
| dev03_04 | 1468.csv | MAX、区间阈值比较、工资乘法、ROUND 及 UNION。 |
| dev03_05 | 1132.csv | 外连接、文本常量过滤、数量比值、AVG/ROUND；第一条原记录从 FROM 开始，本次未修补。 |
| dev03_06 | 1783.csv | CASE 指示量求和、SUM 后再用大于零条件筛选。 |
| dev03_07 | 1173.csv | 数量比值、百分比、ROUND 及布尔表达式 SUM。 |
| dev03_08 | 183.csv | NOT IN 与外连接后的聚合零筛选，表达缺失/反匹配。 |
| dev03_09 | 1747.csv | IP 不相等、时间 BETWEEN、OR；没有把合法的自连接本身当作排除理由。 |
| dev03_10 | 1264.csv | CASE 按用户常量选值并可能产生 NULL，再 NOT IN；两表满元组 PK 不能消除这些越界算子。 |
| dev03_11 | 511.csv | 分组 MIN 取最早日期及以该值子查询筛选，依赖次序决定的值。 |
| dev03_12 | 577.csv | 外连接、奖金阈值、IS NULL / NOT IN。 |
| dev03_13 | 1677.csv | 金额 SUM、保留未匹配产品的外连接、NULL 填零。 |
| dev03_14 | 613.csv | 坐标减法、ABS、MIN、不相等及外连接；单列 POINT 的 PK 本身确是满元组。 |
| dev03_15 | 1421.csv | 外连接和 IFNULL/COALESCE 填零；NPV 记录 key 也未覆盖值列。 |
| dev03_16 | 1777.csv | CASE/SUM 枢轴聚合、NULL、常量过滤及多个外连接。 |
| dev03_17 | 1211.csv | AVG、评级/位置比值、条件比例、ROUND 和评级阈值。 |
| dev03_18 | 596.csv | HAVING 把计数与常量阈值比较，进一步决定输出，而非直接比较投影重数。 |
| dev03_19 | 1683.csv | 字符串长度函数、常量大于比较及 HAVING；并非 opaque equality。 |
| dev03_20 | 1149.csv | 第一式用 distinct-count 阈值筛选，第二式要求 article 不相等；null contract 保留未指定。 |
| dev03_21 | 607.csv | 相关 count 的零测试、NOT IN 与固定公司文本值过滤。 |

## 证据边界、成本与交接

科学 query 执行 0、SQL parser 0、数据库/赋值枚举 0、SMT 0、模型/GPU 0。辅助操作只是源 JSON 读取、手工判断的 JSON/Markdown 整理与 hash/身份核对，没有关键词分类器或查询求值。作者人工阅读成本未量化，CPU/wall/RSS 字段为 null，不能当成零成本或实测性能。

本次没有获取新企业数据或外部数据集、没有核实业务来源或 pair label truth，也没有读取凭据。既有 DataHub registration blocker 不因这个本地静态适用性表而消失。本次只新写 `calibergraph_next_20261011_14/applicability_audit/`；第 13 轮及其他既有冻结文件未改。

待完成项是适用性报告独立复核与 root 统一 private backup。恢复只需取回该目录以及已 pin 的 H14 theory 和开发 registry，用 checksum、JSON 和身份核对确认字节；无需、也不由本报告授权执行任何 SQL、parser 或科学程序。备份交付中不复制第三方原 SQL 全文。
