# 关键原始文献核验与强控制

核验日期：2026-10-11。范围仅覆盖 H12 的直接构造、完整性强控制及既有判定路线；不是完整文献普查，不构成新颖性认证。公共来源只读；不保存论文正文到本目录或备份。

## A1. Armstrong 两元组 FD 反模型（PUBLISHED）

Catriel Beeri, Martin Dowd, Ronald Fagin, Richard Statman. *On the Structure of Armstrong Relations for Functional Dependencies*. JACM 31(1):30–46, 1984. DOI 10.1145/2422.322414。

- [IBM Research 原始机构记录](https://research.ibm.com/publications/on-the-structure-of-armstrong-relations-for-functional-dependencies)：核对作者、日期、JACM 出版信息。
- [作者上传全文](https://www.researchgate.net/publication/220431370_On_the_Structure_of_Armstrong_Relations_for_Functional_Dependencies)：§3 Lemma 3.1 及其后构造性证明，印刷 pp.33–34（HTML 行 428–463）。
- 支持：FD 非蕴含有两元组反模型；在 determinant 的闭包内相同、闭包外不同是已知构造。
- 不支持：任意 self-join 投影计数差异都由某个两元组/单组件同步库见证。本轮反例正是拒绝这种额外泛化。

## A2. 完整独立 Cartesian 角点强控制（PREPRINT）

Sara Cohen. *Few Rows Tell Them Apart: Equivalence of Queries Mixing Set and Bag Semantics*, arXiv:2609.09978v1，2026-09-09。[精确版本全文](https://arxiv.org/html/2609.09978v1)

直接核验 §2 投影赋值语义；§3 Proposition 5、Theorem 7；Appendix A Definition A.1；Appendix B.1。A.1 为各计数变量独立取值后对原子做 Cartesian materialization；§3 给出 {1,2} 角点分离。本轮 13 行 D 就是 M 的三个独立域均取大小 2、其余变量固定的这个既有构造。它与 H12 的单组件同步复制不同，不能漏掉这个更强控制。该结论只用无约束部分，不转嫁其约束片段假设，也不把预印本当正式接收论文。

## A3. 成熟约束判定路线与独立颜色证明边界（DISSERTATION）

David E. DeHaan. *Equivalence of Queries with Nested Aggregation*, University of Waterloo PhD dissertation, 2009。[大学原始 PDF](https://uwspace.uwaterloo.ca/bitstreams/75481061-96ae-4f14-89b7-44c6aab72683/download)

- §6.2，印刷 p.153：明确提出 schema chase，FD 扩张 index sets，再做正常的正规化/覆盖判定。临时文本行 10460–10486 已直接读过。
- §6.3，印刷 p.159：讨论 schema dependencies 处理范围；临时文本行 10937–10960 已直接读过。这里不借该讨论补造完整定理证明。
- Appendix A.2，Definitions A.2.3–A.2.4、Theorem A.2.5、Corollaries A.2.6–A.2.8，印刷 p.171：独立颜色/多项式区分是成熟方法；临时文本行 11746–11794 已直接读过。
- 边界：本任务没有证明 Appendix 的独立颜色构造保持任意 PK；成熟判定声称、其 proof transfer 审计、H12 的受限测试族完整性是不同命题。H12 的反例不依赖解决前两者。

本地只读来源为 /tmp/calibergraph_dehaan_2009_source_20261011.pdf 和同名 .txt；来源哈希记录在 SOURCE_SHA256SUMS。文件留在 /tmp，不纳入交付目录或备份。

## 检索失败和结论边界

一次精确题名搜索附带 Fagin/pdf 返回了无关 PDF 页面；未把这些结果当证据。随后直接访问 IBM 机构记录与作者全文，成功核对 A1。未扩张邻居检索或声称穷尽 prior art。

H12 的手工反例证明是本稿自己给出的数学证据；它没有被包装为发表级新颖定理。旧合法构造扣除 Armstrong 先例，区分库扣除完整 Cartesian 先例，决策判据扣除 DeHaan 路线，剩余结论为这个受限族的失败记录。
