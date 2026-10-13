# COUNT 加权连接候选：12 条原 SQL 的结构准入与证明边界

作者静态检查，2026-10-11。本文替代此前排程建议，作为父任务最新 COUNT 候选的适用性附件。只读允许暴露的 development.jsonl/source_record；未改原 SQL、未执行 parser、solver 或数据库、未读 reserve、未改第一轮文件。

**结论：12 条原 SQL 中 0 条满足指定星形 COUNT 准入条件，6 个 pair 中 0 个含适用查询。因此当前集不能提供该候选的自然正向适用性，更不能提供速度或研究新颖性证据。停止在这 12 条上测试候选；下一步是父任务已经安排的官方 bounded verifier 经同一完整合同进行 applicability probe。**

## 固定准入条件

该候选在一个聚合 query block 内要求：

- S1：一个根表出现 R，以及至少两个叶表出现 L1、L2；全为 INNER 等值连接，叶之间没有谓词、共享相关条件或其他跨叶依赖。别名是关系出现；同一物理表的不同别名可出现，但不能把一个叶别名数成两个。
- S2：每个叶只通过已解析的等值键列连接根；局部过滤要能在该叶及固定根行下独立判断。不能把 IN、derived group、LEFT/NATURAL LEFT JOIN 或某个子查询机械改写成额外叶来获得准入。
- S3：GROUP BY 包含完整的根唯一键；输出除聚合外只使用该根行确定的合法字段。复合键的严格子集不算完整根键。
- S4：本轮端到端只准入 COUNT(*) 或 COUNT(e)。e 为可判 NULL 的、确定性的根局部或单叶局部表达式；不准 COUNT DISTINCT、跨叶表达式、SUM、AVG、ROUND 或混合聚合。计数结果和中间乘积必须在目标整数语义内精确。
- S5：完整 PK/FK、字符串比较、NULL、方言、bag/list 结果比较合同不变；不能通过删除约束、修改字符串、添加 NOT NULL、重新解释 GROUP BY 来准入。

如下“机械结构检查表”是按上述确定规则对原文逐条做的人工静态核对，不冒称已运行 AST checker。这里只需 S1 的必要条件：聚合 block 内不足三个关系出现，就已经不可能是一个根加两个独立叶。所有 12 条都不满足它，故结果不依赖其他更细的准入选择。

## 逐原 SQL 的准入表

ID 固定为 development.jsonl 的行内 id 加 source_record.pair 的 1-based 位置。括号中给原 SQL SHA256 前 12 位作为核对提示；完整 hash 仍以冻结开发清单为准。

| 原 SQL ID | 原文的结构／聚合 | 首个必失败准入条件 | 其他显式障碍 | 判定 |
|---|---|---|---|---|
| dev_01:q1 (ed5bae22a37a) | PERSON 一表，GROUP BY EMAIL，COUNT(EMAIL)，HAVING | S1：没有 JOIN，更没有两个叶 | GROUP BY EMAIL 不是所声明 ID 键 | REJECT_NOT_APPLICABLE |
| dev_01:q2 (78adb202ca2f) | 外层 A JOIN derived B；B 内只有 PERSON 一表的 GROUP/HAVING COUNT | S1：不存在三关系星形 COUNT block；外层无聚合 | 外层与 B 内的关系出现不能跨 query block 拼成星形；SELECT * 的分组方言问题须保留 | REJECT_NOT_APPLICABLE |
| dev_02:q1 (996aab7968f8) | FOLLOW 一表＋IN 子查询，COUNT(FOLLOWEE)，GROUP/ORDER | S1：IN 不是两个独立 INNER 叶 | GROUP BY FOLLOWEE 未含完整 (FOLLOWEE,FOLLOWER) 键 | REJECT_NOT_APPLICABLE |
| dev_02:q2 (9bb6fc726f07) | FOLLOW A JOIN FOLLOW B，共两个别名；COUNT(DISTINCT B.FOLLOWER) | S1：只有一个可能叶 | S3：A.FOLLOWER 不是完整复合键；S4：COUNT DISTINCT | REJECT_NOT_APPLICABLE |
| dev_03:q1 (294782b91028) | PROJECT A JOIN EMPLOYEE B；ROUND(AVG(...),2) | S1：仅两个关系出现 | S4：AVG/ROUND；若根取 PROJECT，GROUP BY PROJECT_ID 也不是完整复合键 | REJECT_NOT_APPLICABLE |
| dev_03:q2 (4296723511c1) | PROJECT P JOIN EMPLOYEE E；ROUND(SUM(...)/COUNT(*),2) | S1：仅两个关系出现 | S4：SUM、除法、ROUND 不能因包含 COUNT 就准入 | REJECT_NOT_APPLICABLE |
| dev_04:q1 (5b93146ad5c4) | VISITS 一表＋NOT IN 子查询，GROUP BY CUSTOMER_ID，COUNT(*) | S1：不存在 INNER 两叶连接 | NOT IN 的 NULL 语义；CUSTOMER_ID 不是声明的 VISIT_ID 键 | REJECT_NOT_APPLICABLE |
| dev_04:q2 (6b052acc9c49) | VISITS NATURAL LEFT JOIN TRANSACTIONS；COUNT(1) | S1：仅两个关系出现且为 LEFT JOIN | GROUP BY CUSTOMER_ID 非根键；IS NULL 反连接行为不可改成 INNER | REJECT_NOT_APPLICABLE |
| dev_05:q1 (9cb094bbee54) | USERS U, TRANSACTIONS T，经 WHERE 等值连接；SUM/HAVING | S1：即使识别为 INNER，也只有两个关系出现 | S4：SUM；必须保留 ACCOUNT、NAME 两条键约束 | REJECT_NOT_APPLICABLE |
| dev_05:q2 (dfdfee4373f3) | USERS JOIN TRANSACTIONS USING ACCOUNT；SUM/HAVING | S1：仅两个关系出现 | S4：SUM；NAME 的键不能忽略 | REJECT_NOT_APPLICABLE |
| dev_06:q1 (b1eb63858598) | BOXES B LEFT JOIN CHESTS C；两项 SUM/IFNULL，无 GROUP BY | S1：仅两个关系出现且为 LEFT JOIN | S3 无按根键分组；S4 SUM | REJECT_NOT_APPLICABLE |
| dev_06:q2 (b6d8aed251d9) | 同上，连接写作 USING(CHEST_ID) | S1：仅两个关系出现且为 LEFT JOIN | S3 无按根键分组；S4 SUM | REJECT_NOT_APPLICABLE |

汇总：S1 通过 0/12；全部条件通过 0/12；至少一侧适用的 pair 0/6。不得为了获得正样本添加第二个叶、删除 DISTINCT、把 LEFT JOIN 换 INNER、把 GROUP BY 换成主键、把 SUM 改 COUNT，或把现有原 SQL 改成手工星形 fixture 后称自然适用。

## COUNT 恒等式、合法数据库不变量及数值边界

对任一固定合法数据库 D 和通过根局部过滤的根行 r，令 Ai(r) 是满足第 i 个独立叶连接和局部过滤的行出现集合，ni(r)=|Ai(r)|。在 SQL bag 语义下按行出现计数，即使投影值相同也不能去重。

独立 INNER 连接的根分组行出现集合恰为 A1(r)×…×Ad(r)，因此：

    COUNT(*) = ∏i ni(r)
    COUNT(root_expr) = 1[root_expr(r) IS NOT NULL] · ∏i ni(r)
    COUNT(leaf_j_expr) = mj(r) · ∏i≠j ni(r)

其中 mj(r) 是 Aj(r) 中 leaf_j_expr 非 NULL 的行出现数。非 NULL 的相同字符串仍须逐行计数；不能以 distinct 字符串数代替 mj。

这个 root group **只在所有 ni(r)>0 时存在**。某叶为空时，INNER JOIN 不产生该根分组；不能输出一行带 COUNT=0 的根。child→root FK 只保证每个非空引用有目标，绝不保证每个 root 有 child。根完整唯一键使每个输出 group 对应至多一根行；若 GROUP BY 是非键，需在多个根行之间再次合并，超出本轮固定准入。

证明只是有限笛卡尔积的基数公式，COUNT(e) 再按 e 是否为 NULL 做指示函数求和。它不要求物化每个笛卡尔积元素，但必须维持全部根与叶原行及原合同。符号编码中的 PK/FK 和字符串条件继续约束同一批原始输入变量；“加权”不授权删除外键闭包或替换原数据库。

**数值限制不能省略：** 数学自然数乘法与某 SQL 执行器的固定宽度整数表达式不自动相同。固定行数界及叶数量给出 ∏ni≤b^d；编译器必须证明此上界及所有中间乘积落在实际目标整数范围，或者使用与目标 COUNT 完全一致的精确整数表示并验证输出映射。COUNT(e) 的表达式求值本身也不能含未建模的溢出、错误或不确定行为。

本轮不推出 SUM 或浮点聚合规则。SUM 的中间溢出、数值类型提升、NULL/空集结果、浮点加法重排都可能改变语义。不能用数学加法分配律或 Python 大整数悄悄替代原 SQL 的实现合同。

## 对 bounded verifier 的证明增量与先例

若以后输入真的满足准入，编码器可把一个已支持的 query block 的显式连接输出枚举替换为上述计数公式。所需工程证明是：对每个相同 bounded 输入赋值，原表达式输出与新表达式输出一致；因此在完整约束 C 下替换 pair 一侧后，存在具体反例的可满足性保持。若 solver 使用完整编码，则得到同界的 SAT/UNSAT 对应；这是编码保语义，不是小模型定理，也不允许把无反例推广到无界。

理论增量不应宣称为新的 aggregation 方法。[Eager Aggregation and Lazy Aggregation](https://www.vldb.org/conf/1995/P345.PDF) 已讨论把分组和计数移到 join 之前；[FAQ: Questions Asked Frequently](https://arxiv.org/abs/1504.04044) 提供更一般的函数聚合与变量消去框架。上述 COUNT 公式属于这些已知分解思想的直接实例。完整 PK/FK 与字符串合同是可靠实现的要求，不能把它们的存在本身当成新定理。

若测工程收益，最强简单 baseline 至少要包含**标准 eager aggregation 后走同一个 verifier**，以及原始 flat 编码。只优于 flat 而与标准 eager 相同，说明收益由已有重写解释；此时研究机制仍应拒绝。三者必须使用同一 row bound、输入符号、完整合同、SQL 结果语义、缓存策略、求解器和端到端计时。

可能可记录的指标仅是统一前端后每次 query 的公式节点数、峰值内存、建模 CPU、solver CPU、验证/重放 CPU及真实合法反例数。只有数据支持时才能谈系统收益；目前准入为零，所有这些收益尚无自然实例可测。

## 下一步与工程 positive control

下一实际动作是父任务安排的官方 bounded baseline applicability probe：保留六组十二条原 SQL 和全部合同，分别记录支持、超时、unknown、bounded 无反例及经重放的合法反例。不能把前端支持率改善、排除不支持 SQL 或删除字符串/约束计作本候选收益。

父任务指定 Calcite 149 的原 pair q1 为 COUNT 字符串 JOIN 的标准 eager aggregation 工程 positive control。本文未读取该原记录，不替父任务制造其 SQL、schema 或标签。使用时应绑定其原始记录与 hash，核验 NULL 字符串及重复非 NULL 字符串的 COUNT 处理，并比较 flat 与标准 eager。它验证 COUNT／字符串／join 的端到端工程路径；若它不满足“两独立叶”条件，也不能把它记成此窄候选的自然正样本，更不构成新机制证据。

当前决策：REJECT_CURRENT_DATA_APPLICABILITY，NOVELTY_ABSORBED_BY_STANDARD_EAGER_AGGREGATION，工程工具链正向适用性待 probe。保留失败准入事实，不扩充手工星形、不改 query 来挽救候选。
