# 第09轮文献判断更正（保留冻结原件）

2026-10-11。第09轮 THEORY.zh.md 的冻结 SHA 为 `e6cab30e1d9f06f619edcde7997f9a9e304ea8cc271ac69c94eb316a4bbee03a`。本文件是新增更正，不覆盖其快照。

**WITHDRAWN：** 第09轮 §5 的“四条已核谱系均没有给出本轮需要的一般PK/FK非anchorable完备迁移”。该句遗漏 DeHaan2009 thesis §6.2 印153/PDF173 的明确约束判等流程和 §6.3 印159/PDF179 的说明，不能保留为文献排除证据。

**WITHDRAWN／替换：** 第09轮表格及 references.json 中 DEHAAN2009_THESIS.transfer 的边界表述，如果被理解为“该论文没有 schema-dependency 扩展”，一并撤回。正确替换为：论文明确提出 FD＋acyclic IND 的 CEQ 判等扩展；单层 combined 编码直接落入它所声称的范围；本次复核没有把约束版一般必要性完整接成证明链。缺少本次证明复核不等于没有直接先例。

**保留但加限定：** 第09轮 theory_result.json 中“Necessity ... not_proved”只能表示该轮作者未证明，不能表示文献未提出或不存在。第11轮证明了完整 key-chase 后同 body 的双向 FD-cover 与双向 FD-closed index-cover 条件等价；这个连接消除了两种写法之间的未证明等同。

**不撤回：** 原始、未 chase 命题的两 atom 反例；FD-cover 的注入充分性；无约束成熟 renaming 对应；full-tuple PK 三角体的三行阈值；无实测和 NULL 结论。它们没有因新找到的章节变成新机制，也不构成针对 DeHaan 约束必要性的反例。

后续引用第09轮时应同时引用本更正和 [第11轮报告](THEORY.zh.md)，不得只引用第09轮的已撤回句子。第11轮状态：**NULL / STOP_NEW_MECHANISM；约束必要性证明审计 PARTIAL，独立审核 PENDING。**
