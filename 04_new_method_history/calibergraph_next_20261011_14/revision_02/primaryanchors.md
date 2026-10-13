# H14 原始来源、继承关系与未闭合入口

核验日期 2026-10-11。本轮文献阅读由作者辅助 agent `h14_primary_prior_art` 及其受托文献检索角色完成，报告返回给理论作者；这些角色不是数学独立审稿人。只读 primary sources，不保存第三方全文。

## 1. FewRows v1：构造已知，完整角点存在性已知

Sara Cohen, *Few Rows Tell Them Apart: Equivalence of Queries Mixing Set and Bag Semantics*, arXiv:2609.09978v1，2026-09-09，PREPRINT。[原文](https://arxiv.org/html/2609.09978v1)

本轮读完整 Appendix A、B.1、B.2、B.3（HTML 至行 594），并核 §3。A.1 为逐变量独立 Cartesian canonical family；A.3 将相关多项式结论归于 Cohen 2009 Lemma 5.2、Theorem 5.3。Proposition 5、Theorem 7 及 B.1 证明给某个 {1,2}^m 角点；B.2 Theorem 13 和 B.3 Theorem 18 的抽取步骤继续调用该存在性结果。所读文本未指定共同 core 的两个自身全 2 角点；这不证明其他文献没有该规则。H14 的库构造及一般二值角点强基线全部扣除该先例。

## 2. Cohen 2009：直接前身全文未核，novelty HOLD

Sara Cohen, *Equivalence of queries that are sensitive to multiplicities*, The VLDB Journal，DOI [10.1007/s00778-008-0122-1](https://doi.org/10.1007/s00778-008-0122-1)。这是 Springer 原始 DOI 对应的期刊题名。其 PODS 2006 前身另名为 *Equivalence of queries combining set and bag-set semantics*，不能把会议题名与期刊 DOI 混合。已核书目信息、摘要和其为 PODS 2006 扩展版的来源信息。官方 PDF 跳转到订阅预览，ACM PDF 未成功返回。

本轮**没有读到原始完整证明**。上节 Lemma 5.2 / Theorem 5.3 的继承关系只是 FewRows 的明文归属，不伪装成已独立核对 2009 正文。该入口未关闭，足以阻止新颖性完成状态。

## 3. Counting-CQ 的既有克隆与 renaming 等价

- [Chen–Mengel 原文，§5.1](https://arxiv.org/html/1601.03240v2#S5.SS1)：Definition 5.3、Theorem 5.4，PDF pp.15–16。counting equivalence 与 renaming equivalence 的刻画已存在；其构造用 D_(j,T)，T⊆S、j=1,…,|S|，通过独立克隆、容斥和 Vandermonde 插值。所读证明未给本轮固定两测试。
- [Dell–Roth–Wellnitz 原文，§5](https://arxiv.org/html/1902.04960v2#S5)：Lemma 34(ii)–(iii)、Corollary 35，PDF pp.25–26，已有逐顶点克隆及多变量插值。
- [同一原文，§6.3](https://arxiv.org/html/1902.04960v2#S6.SS3)：Lemma 48 和 Observation 49 的 relational renaming 与 core 性质，使“同一有限 relational core 的计数等价等于 counted-variable subset orbit 相同”成为已知刻画的直接推论。本轮不把这个 orbit 判据作为新贡献。固定 head 的逐点群版本在 theory.md 中直接证明，不假称上述原文逐字陈述本轮全部参数设置。

这些原始论文支持成熟机制与刻画；没有声称本轮已完成计数 CQ 全文献普查或已排除所有直接两点规则。

## 4. 群平均 kernel 是成熟技术

Haasdonk, Vossen, Burkhardt，*Invariance in Kernel Methods by Haar-Integration Kernels*，SCIA 2005，§3，pp.843–844。[出版社原始 PDF](https://link.springer.com/content/pdf/10.1007/11499145_85.pdf)

Definition 1 / Eq. (2) 定义群积分 kernel；Eq. (3) 将其写成平均特征的内积；Proposition 1(i)(ii) 给出不变性及正定性。有限群平均是直接特例。H14 中 Boolean-zeta 特征的可逆性和不同 orbit 的严格 Gram 不等式均在 theory.md 自证；不把标准群平均、Gram 或 Cauchy–Schwarz 技巧归为新创新。

## 5. 老的颜色多项式强控制

David E. DeHaan，*Equivalence of Queries with Nested Aggregation*，Waterloo dissertation 2009，[大学原始 PDF](https://uwspace.uwaterloo.ca/bitstreams/75481061-96ae-4f14-89b7-44c6aab72683/download)。本地只读 /tmp/calibergraph_dehaan_2009_source_20261011.txt，Appendix A.2，印刷 pp.166–171；颜色展开、多项式与 Schwartz–Zippel 是成熟控制。Example 65 的倍数 2 示例不等于本轮一般共同 core 的两点定理；A.2.2 同时讨论选择不同展开点可能产生不同区分结果。

第三方 PDF/TXT 不复制进交付或备份。第 12 轮的 source SHA 可作为原文完整性来源；本轮没有修改它。

## 6. 剩余主张与判定

source → 原反例生成问题 → canonical 独立克隆 → 共同 core 的 orbit 分解 → 群平均 Gram 的两自身点严格性，是本稿明确的推导链。前四项中的基本构造与等价刻画、第五项的通用 kernel 技巧均已知。唯一可能剩余的具体结论是“两固定自身 binary blowup 足够”；直接先例入口未完全核验，公平优势和自然覆盖没有证据。因此 novelty=HOLD，promotable opportunity=NULL。
