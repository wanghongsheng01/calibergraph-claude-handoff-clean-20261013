# 独立挑战补充证据

本文件在最终候选稿送审前记录新增原始文献与静态反例。根代理告知两篇候选最近邻后，本审查者亲自打开原文核对；不将根代理摘要当作证据。以下均未复算、未运行 SQL/solver。

## 更直接的有限值域先例

【论文报告】Cohen–Nutt–Sagiv, *Equivalences Among Aggregate Queries with Negation*, [arXiv:cs/0210028v2](https://arxiv.org/pdf/cs/0210028)：§4.1 定义 shiftability 为对严格单调注入，聚合结果的相等关系双向保持；Proposition 4.2 包括 count、cntd、max 等。Theorem 4.4 证明在完整排序固定时，一个满足赋值即可判定 shiftable 聚合的相等关系。Theorem 4.8 将以活动常量数为界的等价可判定性与 order-decidability 联系起来。§4.2 又明确 sum/avg 可以 order-decidable 而非 shiftable。这比“抽象解释早已存在”更直接冲击基于顺序关系和值域代表的宽泛创新主张。

【判断】不能把此处 active-constant bound 写成数据库每表 row bound；更不能把它直接当作 SQLite 存储类/亲和性/NULL 的定理。它确立的压力是：保持相等模式、顺序模式、聚合观察并选择有限代表并不是新的问题描述。新算法若真的改进了混合类型语义、构造复杂度或支持片段，仍需独立给出这一增量。

【论文报告】Cohen, *Few Rows Tell Them Apart: Equivalence of Queries Mixing Set and Bag Semantics*, [arXiv:2609.09978v1](https://arxiv.org/html/2609.09978v1)，本轮仅确认 PREPRINT：§5.1 按两查询常量建立 slots/regions；§5.2 为 position-groups 定义 directed/retained/isolated 等证书；§5.3 加入 key-determined 变量。§5 的域是无端点稠密全序（取 Q），先限 var-constant 比较和已 set-equivalent 的 combined-semantics 查询；§4 的约束结果有 key-anchorability、acyclic FK 等限制。

【判断】该稿是有限值观察和证书最直接的近期威胁，不能只列为“另一篇行界理论”；同时它没有自动完成 SQLite 的真实类型/三值逻辑及任意完整约束。若最终稿以“前人没有值槽/关系证书”作差异，证据反驳该差异；若仅声称要适配 SQLite，则仍缺足以形成方法贡献的构造/成本证据。

## 子审查静态反例的核对

窄任务子审查者 `/root/domain_independent_challenge/relational_collision_check` 只读冻结文件、没有候选方法著作或实验。其结果经本审查者静态检查如下。设 P=(ID,SEX)，L=(ID,Date,T-BIL)，其余可空列 NULL，Examination 空：

| 攻击 | 两个合法原实例或一个合法实例 | 直接后果 |
|---|---|---|
| JOIN 父行关系 | 固定 P={(10,M),(20,X)}；A:L={(10,1,2)}，B:L={(20,1,2)} | #1172 原输出 (1,0)/(0,0)，旧逐单元映射相同；扩展后的映射还破坏 Patient PK。 |
| COUNT DISTINCT | 固定 P={(10,M),(20,M)}；A:L={(10,1,2),(10,2,2)}，B:L={(10,1,2),(20,2,2)} | 同为 2 条合格 Lab 记录，#1172 输出为 (1,0)/(2,0)；必须保留实体相等模式。 |
| 复合主键 | P={(10,M)}，L={(10,1,2),(10,2,2)} | Date→0 后两条 Lab 具有同一 (ID,Date)，原完整 C 不再保持。 |
| raw 输出值 | P={(10,M)}；新增查询 SELECT ID 与 SELECT 1 | N=1 时原查询对不同，而统一重命名后相同；“冻结计数查询观察保持”不能扩成所有投影值保持。 |
| 新增跨行顺序 | 固定 P={(10,M),(20,X)} 和两条 Lab 的 ID/Date；T-BIL=(3,4) 与 (4,3) | unary above 类和相等关系均相同，但男性对应值是否小于另一值不同。原 #1172 没有该跨值观察，因此这不是它的反例。 |

锚点：`15/case1172_adapter.py:56–61,98–101`；`15/PROOF.zh.md:7,18,22,36`；`09/sources_local/thrombosis_prediction__1172/{gold.sql,full-schema.sql}`。冻结代码的 N≤1 拒绝是正确保护，不能将上述超界构造写成既有实现漏洞。

## 不夸大结论的判断边界

这些证据可以否定现成 unary 映射的泛化和宽泛机制新颖性，不能证明所有可能的自动 SQLite 值抽象研究都不值得做。单次评审要判的是送审候选是否已经留下具体方法增量；不能代替作者发明一个新的细化算法、复杂度定理或系统设计，然后以该补写方案放行。
