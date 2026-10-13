# 本轮完成：拒绝当前有限值域抽象候选

**最终判定：REJECT_CURRENT_CANDIDATE。保留候选 0 个，不进入实现。** 非作者独立审核同意该判定；送审文档审核通过，无必须修复项。这是当前新颖性与机制证据不足，不是断言自动 SQLite 抽象不可行。

决定性证据有三项：

- [Cohen–Nutt–Sagiv](https://arxiv.org/pdf/cs/0210028) 已研究聚合相等关系在重命名下的保持及完整序型代表。
- [Cosette OOPSLA 2018](https://chenglongwang.org/data/oopsla18.pdf) 已自动推导查询相关缩减，并证明保留区别见证的存在。
- [Few Rows §5](https://arxiv.org/html/2609.09978v1#S5) 已包含查询常量分区、保区域映射与认证；不能仅将其归为行界论文。

这些工作没有共同解决任意 SQLite 类型、NULL、日期和完整 DDL。可是本轮也没有给出超出它们的自动构造、片段定理或成本优势；语义适配清单不足以构成新机制。

本轮得到的实质分析是：明确了联合查询区别 Δ、完整 C、正反向覆盖与总成本的证书契约；给出了跨行连接、复合键、DISTINCT 遮蔽和聚合失真的纸面反例；并推导 #1172 对固定 N 可用单射父键、新鲜 Date 和谓词类别保留两个 COUNT DISTINCT 结果。独审确认这个**逐例数学构造**在声明范围内成立；它不是已实现算法，也不是新颖性或性能证据。旧 adapter 仍严格限定 N≤1。

交付材料：

- [完整作者分析](DIRECTION_REVIEW.zh.md)：保留送审时原文与 SHA，故开头仍记录当时的“待独立挑战”状态；最终状态以本文件及独审为准。
- [独立最终裁决](review_local/FINAL_INDEPENDENT_VERDICT.zh.md)：一次最终送审；非作者，但审查者曾提供前置威胁模型，因此不声称盲审。
- [SQL 先例与固定代码版本](literature_sql/NEAREST_WORK.md)、[形式方法先例](literature_formal/formal_prior_audit.md)。
- [最终事实](FINAL_FACTS.json)、[旧输入保全核对](INPUT_PRESERVATION.json)、[归档文件清单](DELIVERY_MANIFEST.json)。

本轮新 SQL/solver/benchmark 执行均为 0，无实现、无计算队列、无提交或推送。已记录的 16 个旧输入哈希全部匹配；该核对不冒称扫描了整个工作区。旧暴露样本仍只算开发证据，没有建立或消耗新确认集。剩余的是科学证据缺口，当前任务没有执行阻塞，也不需要继续补实验。
