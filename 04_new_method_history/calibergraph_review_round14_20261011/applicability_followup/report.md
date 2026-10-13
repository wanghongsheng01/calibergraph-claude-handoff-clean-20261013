# H14 已登记开发记录适用性的独立静态复核

日期：2026-10-11。审核人：`/root/round14_independent_two_corner_review`，不是适用性表作者 `/root/round13_sqlite_counterexample_replay`。本复核由父任务在原数学独审冻结后追加授权，只读全部 21 对原 SQL、schema／constraint 与身份哈希；原数学审核及其文档修订复核均保持冻结。

**结论：确认 0/21 原始整对直接适用 H14，21/21 有明确排除依据，UNCERTAIN 为 0。** 这是给定记录的语法范围筛查，不是查询效果测试，也不是自然总体的覆盖率估计。它说明当前 H14 定理尚未直接覆盖这批原始目标查询对；不推翻定理，不认定任何可能的语义保持转换都不存在。

【证据·完整性】先核作者 applicability_audit 的全部 4 个输出哈希，全部通过；随后读完整报告／JSON／清单。再独立核开发 registry `calibergraph_next_20261011_03/data/development_stratified.jsonl` SHA256 为 `ab80ebcf869015d324af3e35b9dd8352013e0037dec6922e7788f4cf366e4ffb`。逐条原 query 的 UTF-8 SHA 与 registry 和作者适用性表三方一致：42/42；21 个 ID 的顺序和 source group 也完全一致。未用 pair labels、运行结果或作者排除结论代替阅读原文。

【证据·独立人工阅读】下面理由来自逐对读取原始 source_record.pair；同时阅读 source_record.schema／constraint，但不假定这些 contract 已获业务核验。每行仅需一个语法越界理由即可排除整对直接使用 H14；发现该理由后不再给共同 body/core 出具虚假证书。COUNТ、DISTINCT、内连接、自连接或分组外观本身不作为自动排除理由。

| 记录 | 源文件 | 本审核独立确认的充分排除理由 |
|---|---|---|
| dev03_01 | 1127.csv | 两式对金额求 SUM，并保留外连接未匹配行且作零替换；第一式还构造带平台常量的 UNION。 |
| dev03_02 | 584.csv | 固定值不等比较及 IS NULL 已超出纯变量正 CQ；第二式使用 UNION ALL。 |
| dev03_03 | 1693.csv | 第二式对标识做加法、使用零哨兵和 CASE/SUM，并合并 UNION ALL；不能以第一式内部 count 子式替代整对。 |
| dev03_04 | 1468.csv | 分组 MAX、工资数值乘法及 ROUND，按常量区间选择。 |
| dev03_05 | 1132.csv | 固定文本筛选、数量除法和外连接；第二式又求 AVG/ROUND。第一条原文从 FROM 开始，按原样保留，不修复为新的查询。 |
| dev03_06 | 1783.csv | 多个 CASE 指示量经 SUM 累计后再作正值阈值筛选；额外聚合与输出筛选不属于本定理的直接重数比较。 |
| dev03_07 | 1173.csv | 最终输出数量之比及百分比 ROUND；第一式还对相等谓词的布尔值 SUM。 |
| dev03_08 | 183.csv | NOT IN 或外连接后的计数零过滤表达反匹配。 |
| dev03_09 | 1747.csv | IP 不相等和时间 BETWEEN；第二式还有 OR。越界在比较／析取，非自连接本身。 |
| dev03_10 | 1264.csv | CASE 依赖固定用户值并可产生 NULL，外层又有 NOT IN。 |
| dev03_11 | 511.csv | 两式均依赖日期 MIN，第二式以计算出的最小值筛选；不是不解释值含义的投影重数。 |
| dev03_12 | 577.csv | 外连接并按奖金阈值和 NULL／NOT IN 选择。 |
| dev03_13 | 1677.csv | 对多列金额 SUM，外连接保留产品并做缺失值填零。 |
| dev03_14 | 613.csv | 坐标减法、ABS、MIN 及不相等；单列 POINT 的 key 确为满元组，排除不依赖错误的 key 判断。 |
| dev03_15 | 1421.csv | 两式保留未匹配行，并以 IFNULL／COALESCE 输出零。 |
| dev03_16 | 1777.csv | 一式 CASE/SUM 枢轴且有 NULL；另一式用固定商店值筛选并多重外连接。 |
| dev03_17 | 1211.csv | AVG 评级／位置比值及条件比例，再 ROUND；不是两个投影重数本身。 |
| dev03_18 | 596.csv | 两式通过计数与常量阈值的比较决定 class 是否输出；不因 COUNT 本身排除。 |
| dev03_19 | 1683.csv | CHAR_LENGTH／LENGTH 解释字符串内容，并与固定长度阈值比较。 |
| dev03_20 | 1149.csv | 一式 distinct-count 阈值，另一式 article 不等比较；未知 constraint 仍保持未知，不当成排除必需依据。 |
| dev03_21 | 607.csv | 一式相关 count 等于零，另一式 NOT IN，且都过滤固定公司值。 |

【判断】21 项均在原始整对上具有上述明确语法障碍，故本次没有需要以 UNCERTAIN 标注的直接适用性案例。这个结论不需要预先认定每条原 SQL 合法、两式等价、约束为真或 body 为 core；这些问题均未由本静态复核认证。特别是 dev03_05 的不完整文本不能被偷偷修补或作为真实可执行 pair 背书。

【判断】原记录来自完全暴露的开发 registry，source group 仅为文件标签。没有新增样本、剔除或替换；业务自然性为 UNKNOWN，标签真值及 SQL 语义忠实性未核验，统计独立性未建立。因此不能把 0/21 称为自然总体适用率，不能将内部子查询经过变换后称为原始整对已覆盖，也不能用新合成 core 示例替代这个零直接覆盖结论。

【判断】理论的手工正确性和目标范围的直接适用性是不同结论：H14 在其显式片段内通过；此片段当前没有覆盖这 21 对 as-supplied 目标。没有证明总成本优势或生产价值，新颖性仍 HOLD，机会仍 NULL。

【证据·执行与恢复】仅有 JSON 文件读取、手工判别、身份／SHA 校验和本文档写入。未运行 SQL、parser、关键词分类器、数据库或赋值枚举、SMT、模型、GPU 或实验。人工成本未量化，不记成零。未复制第三方 SQL／schema／constraint 全文到交付；仅保留源身份、哈希和自写理由。DataHub 注册阻碍保持父任务既有状态，备份由父任务统一核验。本目录 input 清单从 workspace 根校验，output 清单从本目录校验；恢复也不需要运行查询。
