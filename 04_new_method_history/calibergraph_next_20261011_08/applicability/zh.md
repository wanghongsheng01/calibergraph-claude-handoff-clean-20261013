# Round 08：固定 21 组原始整对静态适用性

结论：**0/21 组原始整对被确认适用；21/21 均有文本中直接可见的语法排除证据。** 未产生候选，不改变分母，不另找来源，不改写原始 SQL。整体待决组为 0，但这不表示完整约束、类型或 NULL 的语义已经全部判定。

这是一份人工静态充分拒绝记录，**不是 parser-verified 结果**，也不是查询执行或等价性判定。没有新增自然缺陷证据、没有新 test、没有实测。

## 固定输入与适用域

唯一数据输入为 `calibergraph_next_20261011_03/data/development_stratified.jsonl`，共 21 个既已暴露的开发组。输入 SHA-256 为 `ab80ebcf869015d324af3e35b9dd8352013e0037dec6922e7788f4cf366e4ffb`。没有打开其 provenance 指向的公共全库文件，没有读取 finaltest、reserve 或 06 运行结果。该分层开发切片不能据此视为随机、独立或隐藏测试样本。

筛查目标为同一无比较、无 NULL、自连接自由且每表一个 atom、FK 显式闭合的 CQ body B；输出 H 相同，仅计数变量集合 M/N 可不同。SQL 正规形为外层 bag projection 包住内层 `DISTINCT H,M`，存在变量在内层投影去掉。每表须声明 PK、FK 须指向目标完整 PK，关系 FK 图须为森林。`SELECT DISTINCT H` 与 `SELECT H` 只在这些前提成立时可作特例。

只根据原始整对判断，不把 outer join、聚合、NOT IN 或其他形式经改写后的表达式冒认为原始整对命中。等值连接本身不是这里所称的比较排除项；表内自连接、聚合、反连接、集合并、非等值比较等已经提供充分拒绝。

## 四类证据的区分

- **语法不满足**：21 组均有直接原文证据，足够拒绝当前片段；未做解析器认证。
- **完整 C 不满足或未获认证**：02 的关系 FK 自环；03/09/17 无声明 PK；05 缺 ACTIONS PK 且 FK 目标完整键未建立；15 的 FK 只指向 NPV 复合 PK 的 ID 部分。20 的 `constraint:null` 是未指定，不能当作空 C。
- **类型/NULL 前提未建立**：类型标签不等于 SQL 方言、域或 NOT NULL 证明；FK 不自动推出非空。部分 SQL 还直接含 NULL 分支或可产生 NULL 的外连接。
- **无法仅文本判定**：不认证同 B/H、不运行规范化、不认证导入约束语义。06 的四条同源同目标 FK 需要明确关系图是否合并平行边；13 的两个 PRODUCT `primary` 条目需要明确约束格式解释。所有这些不确定项均不改变已有语法拒绝。

完整 C 中的范围、枚举、不等和蕴含条件全部保留。在精确定理只容许 PK/FK 的解释下，额外条件也在适用域外；若定理允许更广的 C，需要单独证明其不会改变精确充要判据。本报告不悄悄删去 C 的任何部分。

## 逐组记录（分母始终 21）

下表的开发行号指唯一允许输入；源行号仅是输入已有 provenance，并未打开源文件。JSON 中保存每组 SQL、schema、C 以及源行的已有 SHA-256，供私有作者恢复核对；不复制完整 SQL。

| 开发行 / ID | 原分组 / 源行 | 原始整对的充分语法排除 | 完整 C 记录 |
|---|---|---|---|
| 1 / dev03_01 | 1127.csv / 9581 | 两边均含聚合、集合并及外连接；输出含计算表达式，不是仅 M/N 不同的固定 CQ body 投影。 | SPENDING 有三列复合 primary；无 foreign 条目。 额外 C 运算符：gt, in。 |
| 2 / dev03_02 | 584.csv / 2421 | Q1 含不等比较、OR、IS NULL；Q2 含 UNION ALL 与 IS NULL。 | CUSTOMER.REFEREE_ID → CUSTOMER.ID 是关系 FK 图自环；完整 C 另含 neq。 额外 C 运算符：neq。 |
| 3 / dev03_03 | 1693.csv / 20110 | 两边均含聚合和 GROUP BY；Q2 另含 UNION ALL、NOT IN 与算术。 | 完整 C 仅声明 LEAD_ID 与 PARTNER_ID 的 neq，DAILYSALES 未声明 primary。 额外 C 运算符：neq。 |
| 4 / dev03_04 | 1468.csv / 17255 | Q1 含 MAX/GROUP BY、CASE/BETWEEN/ROUND；Q2 含 UNION、聚合及比较，SALARIES 多次出现。 | SALARIES 有 (COMPANY_ID, EMPLOYEE_ID) 复合 primary；无 foreign。 额外 C 运算符：gt。 |
| 5 / dev03_05 | 1132.csv / 10021 | Q1 原文以 FROM 开始，未呈现完整 SELECT 投影；两边还含 LEFT JOIN 和聚合。文本足以拒绝，未进行 SQL 语法错误诊断。 | 仅 REMOVALS.POST_ID 声明 primary；ACTIONS 无 primary。REMOVALS.POST_ID → ACTIONS.POST_ID 不能由当前 C 认证为指向完整已声明 PK。 额外 C 运算符：in, imply, eq, neq。 |
| 6 / dev03_06 | 1783.csv / 21931 | 两边含 SUM/CASE、GROUP BY 与结果比较；不能把聚合重写为 M/N 差异。 | 两表各有 primary，四个 CHAMPIONSHIPS 字段分别 foreign→PLAYERS.PLAYER_ID。若关系图合并平行边，它只有一条关系邻接；若保留 FK 边，则有四条平行边。图约定未明确；原文 CROSS JOIN 未显式给出这些 FK 目标等式闭合。 |
| 7 / dev03_07 | 1173.csv / 11415 | 两边均为计数/求和、除法及 ROUND 的聚合表达式；Q2 在两个派生子查询重复读取 DELIVERY。 | DELIVERY.DELIVERY_ID 声明 primary；无 foreign。 额外 C 运算符：lte。 |
| 8 / dev03_08 | 183.csv / 580 | Q1 为 NOT IN 反连接；Q2 含 LEFT JOIN、COUNT、GROUP BY、HAVING。 | CUSTOMERS.ID 与 ORDERS.ID 均有 primary；ORDERS.CUSTOMERID foreign→CUSTOMERS.ID，单条关系边。此观察不证明原始整对是同一 FK 闭合 CQ。 |
| 9 / dev03_09 | 1747.csv / 21639 | 重复 LOGINFO 自连接；不等比较、BETWEEN；Q2 还含 OR 与 IN 子查询。 | 完整 C 仅 LOGINFO.LOGIN < LOGINFO.LOGOUT，LOGINFO 无 primary。 额外 C 运算符：lt。 |
| 10 / dev03_10 | 1264.csv / 13041 | 两边均含 CASE 和 NOT IN；LIKES 在外层和子查询重复出现。Q1 显式 ELSE NULL，Q2 省略 ELSE。 | FRIENDSHIP 和 LIKES 分别有覆盖各自两列的复合 primary；无 foreign。 额外 C 运算符：neq。 |
| 11 / dev03_11 | 511.csv / 673 | 两边含 MIN 聚合与 GROUP BY；Q2 的 ACTIVITY 在外层及聚合子查询重复出现。 | ACTIVITY 有 (PLAYER_ID, EVENT_DATE) 复合 primary；无 foreign。 额外 C 运算符：gte。 |
| 12 / dev03_12 | 577.csv / 2173 | 两边均为 LEFT JOIN；Q1 含比较、OR、IS NULL，Q2 另含 NOT IN。 | EMPLOYEE.EMPID 和 BONUS.EMPID 各有 primary，BONUS.EMPID foreign→EMPLOYEE.EMPID；单条关系边。 额外 C 运算符：neq, gte。 |
| 13 / dev03_13 | 1677.csv / 19915 | 两边均为外连接加 SUM/GROUP BY、IFNULL 和 ORDER BY。 | PRODUCT 有 PRODUCT_ID、NAME 两个单独 primary 条目，INVOICE.INVOICE_ID 也有 primary；foreign 指向 PRODUCT_ID。两个 primary 条目是两组逻辑键还是 DDL 主键编码须由约束格式定义，不能静态补定。 额外 C 运算符：gte。 |
| 14 / dev03_14 | 613.csv / 4513 | POINT 自连接；两边均含 MIN、ABS、减法及不等比较，Q2 还有 LEFT JOIN。 | POINT.X 声明 primary；无 foreign。 |
| 15 / dev03_15 | 1421.csv / 15534 | 两边为 LEFT/RIGHT 外连接，并使用 IFNULL 或 COALESCE；不能改成内连接后算命中。 | NPV 的 primary 为 (ID, YEAR)，但 C 中 foreign 仅 QUERIES.ID→NPV.ID，未覆盖目标完整 PK；不得自行补 YEAR 外键。 额外 C 运算符：gte。 |
| 16 / dev03_16 | 1777.csv / 21819 | Q1 为 SUM/CASE/GROUP BY；Q2 为多次 PRODUCTS 读取及连续 LEFT JOIN，含筛选常量。 | PRODUCTS 有 (PRODUCT_ID, STORE) 复合 primary；无 foreign。 额外 C 运算符：in, gt。 |
| 17 / dev03_17 | 1211.csv / 12206 | 两边均含 AVG/SUM/COUNT、ROUND、除法及比较；Q2 在相关标量子查询重复 QUERIES。 | 完整 C 只有 RATING 和 POSITION 的 between 区间限制，没有 QUERIES primary。 额外 C 运算符：between。 |
| 18 / dev03_18 | 596.csv / 2924 | 两边均含 GROUP BY/HAVING 及 COUNT；Q2 重复读取 COURSES 并含相关子查询。 | COURSES.STUDENT 声明 primary；无 foreign。 |
| 19 / dev03_19 | 1683.csv / 20022 | Q1 含 CHAR_LENGTH 及 >；Q2 含 LENGTH、GROUP BY/HAVING 并重复读取 TWEETS。 | TWEETS.TWEET_ID 声明 primary；无 foreign。 |
| 20 / dev03_20 | 1149.csv / 11280 | Q1 含 GROUP BY/HAVING COUNT 和 ORDER BY；Q2 含 VIEWS 自连接、不等比较及 ORDER BY。 | constraint 字段为 null：C 未指定，不能解释为已验证空约束，也不能补一个 VIEWS PK。 |
| 21 / dev03_21 | 607.csv / 4241 | Q1 为相关 COUNT(*)=0 子查询，Q2 为 NOT IN；均含对 RED 的常量筛选，不是纯 CQ 计数变量差异。 | 三表均有 primary；ORDERS 分别 foreign→COMPANY.COM_ID 和 SALESPERSON.SALES_ID，关系图文本为三节点两边树。完整 C 另含薪酬/金额范围和跨表日期 imply；不能删去这些条件认证精确闭包。 额外 C 运算符：gte, imply, eq, lt。 |

## 各组类型/NULL 与短原文证据

这些片段只是最小定位线索；不以词法命中模拟 SQL parser。

- **dev03_01**：PLATFORM、SPEND_DATE、USER_ID 的非空性只能在 primary 被正确解释的条件下成立；AMOUNT 未声明 NOT NULL。IFNULL 与 LEFT JOIN 引入本片段未覆盖的 NULL 处理。 证据：Q1 `UNION`；Q1 `LEFT JOIN`；Q2 `SUM(AMOUNT)`。
- **dev03_02**：REFEREE_ID 未有 NOT NULL；IS NULL 分支显式涉及 NULL。INT/VARCHAR 标签不足以证明逻辑域及 SQL 类型解释。 证据：Q1 `REFEREE_ID <> 2 OR REFEREE_ID IS NULL`；Q2 `UNION ALL`。
- **dev03_03**：DATE_ID、MAKE_NAME、LEAD_ID、PARTNER_ID 均未声明 NOT NULL；COUNT DISTINCT 的 NULL 行为未建立。 证据：Q1 `COUNT(DISTINCT LEAD_ID)`；Q2 `UNION ALL`。
- **dev03_04**：SALARY 和 EMPLOYEE_NAME 未有 NOT NULL；ROUND/乘法/比较的类型语义及溢出规则未建立。 证据：Q1 `MAX(SALARY)`；Q2 `UNION`。
- **dev03_05**：EXTRA 的 ENUM 标签含 NULL，C 又出现字符串 NULL；它们与 SQL NULL 的对应未明确。POST_ID 等未有完整非空证明，且含外连接。 证据：Q1 `FROM (SELECT`；Q2 `ROUND(AVG(DAILY_PERCENT)*100,2)`。
- **dev03_06**：四个冠军 FK 字段未有 NOT NULL；SQL FK 本身不排除 NULL。PLAYER_NAME 未有 NOT NULL。 证据：Q1 `GRAND_SLAMS_COUNT > 0`；Q2 `SUM(CASE`。
- **dev03_07**：两个日期字段无 NOT NULL；日期比较和聚合/除法语义未建立。 证据：Q1 `SUM(ORDER_DATE = CUSTOMER_PREF_DELIVERY_DATE)`；Q2 `SELECT COUNT(*) AS TOT`。
- **dev03_08**：ORDERS.CUSTOMERID 与 CUSTOMERS.NAME 未有 NOT NULL；foreign 不等于非空，NOT IN 的 NULL 行为未排除。 证据：Q1 `ID NOT IN`；Q2 `HAVING FO=0`。
- **dev03_09**：各列均无 NOT NULL；TIME 类型及区间边界语义未建立。 证据：Q1 `JOIN LOGINFO AS I2`；Q2 `L1.IP_ADDRESS!=L2.IP_ADDRESS`。
- **dev03_10**：即使所有基表列因 primary 而非空，CASE 未匹配分支仍产生 NULL；原始查询不满足无 NULL 片段。 证据：Q1 `ELSE NULL END`；Q2 `PAGE_ID NOT IN`。
- **dev03_11**：使用字段 PLAYER_ID/EVENT_DATE 若确为 SQL PK 则非空；但 JSON primary 的执行语义、DATE 域和其余基表属性的非空性均未验证。 证据：Q1 `MIN(EVENT_DATE)`；Q2 `IN (SELECT PLAYER_ID, MIN(EVENT_DATE)`。
- **dev03_12**：BONUS.BONUS、EMPLOYEE.NAME 等无 NOT NULL；外连接能够产生 NULL，查询显式处理 NULL。 证据：Q1 `BONUS < 1000 OR BONUS IS NULL`；Q2 `EMPLOYEE.EMPID NOT IN`。
- **dev03_13**：发票金额字段与 INVOICE.PRODUCT_ID 未有 NOT NULL；外连接及 IFNULL 显式涉及 NULL。 证据：Q1 `RIGHT JOIN`；Q2 `LEFT OUTER JOIN`。
- **dev03_14**：基表唯一属性 X 若为实际 SQL PK 则非空；LEFT JOIN 仍可产生 NULL。INT 算术的范围/溢出及空聚合语义未建立。 证据：Q1 `POINT AS A, POINT AS B`；Q2 `LEFT JOIN POINT B ON A.X != B.X`。
- **dev03_15**：NPV.NPV 无 NOT NULL；外连接、IFNULL/COALESCE 本身属于 NULL 扩展/处理。 证据：Q1 `LEFT JOIN NPV N`；Q2 `COALESCE(NPV.NPV, 0)`。
- **dev03_16**：PRICE 无 NOT NULL；Q1 显式 ELSE NULL，Q2 的外连接产生 NULL。ENUM 与 SQL 字符串/比较规则未建立。 证据：Q1 `THEN PRICE ELSE NULL END`；Q2 `LEFT JOIN T1`。
- **dev03_17**：所有列均无 NOT NULL；between 的导入语义并非已验证的 SQL 非空约束；除法/舍入类型规则未建立。 证据：Q1 `ROUND(AVG(RATING/POSITION), 2)`；Q2 `SELECT COUNT(1) FROM QUERIES`。
- **dev03_18**：CLASS 无 NOT NULL；VARCHAR 等值、分组与 NULL 语义不由类型标签建立。 证据：Q1 `HAVING COUNT(*)>=5`；Q2 `COUNT(DISTINCT STUDENT)`。
- **dev03_19**：CONTENT 无 NOT NULL；字符/字节长度、编码和 SQL 方言并未给出，不能据文本将两函数视为同义。 证据：Q1 `CHAR_LENGTH(CONTENT) > 15`；Q2 `GROUP BY TWEET_ID HAVING LEN>15`。
- **dev03_20**：四列只有 INT/DATE 标签，无 NOT NULL 或已知 PK 非空保证。 证据：Q1 `HAVING COUNT(DISTINCT ARTICLE_ID) > 1`；Q2 `JOIN VIEWS T2`。
- **dev03_21**：NAME 和 ORDERS 的两个外键列无 NOT NULL；日期列标为 VARCHAR，其比较规则未建立；NOT IN 的 NULL 语义未排除。 证据：Q1 `0 = ( SELECT COUNT(*)`；Q2 `SALES_ID NOT IN`。

## 结论边界与恢复

0/21 表明这个固定开发切片没有提供当前严格片段的原始整对应用证据。它不反驳片段内定理，不衡量新颖性，不证明基准中的配对标签，不代表全公共库覆盖率，也不构成自然缺陷发现。

本次只进行标准库 JSON 读取、人工文本判断、报告序列化和 SHA-256；没有 SQL、parser、solver、科学计算、查询重写、数据增补、schema/C 修改或新的实验。类型/NULL 未建立不等于断言所有基表实际含 NULL；C 缺失不等于现实数据库没有键。

已读取 `/Users/loctek/AGENTS.md`。DataHub 目录及 `opensource +info` 中的条目只说明 Spider/BIRD，没有此固定 LeetCode 切片的对应读取接口；映射缺口已告知父任务，未修改全局注册，未调用别的数据源。仅写本目录；私有备份及其验证由父任务统一处理，本文不声称已完成备份。

恢复核对使用本目录 `input_output_sha256_manifest.json` 和 `manifest.sha256`：前者记录唯一输入与两份报告的 SHA-256，后者锚定前者自身。完整 SQL 仍只保留在父任务控制的既有固定输入中。

