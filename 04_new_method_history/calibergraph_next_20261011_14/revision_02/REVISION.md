# H14 revision_02：两项文档更正

日期：2026-10-11。原 `theory/` 作者冻结稿保持不动。本目录只提供两份完整替代文件；数学证明、假设数量和研究 HOLD / NULL 状态没有变化。

1. **R1，书目题名。** `primaryanchors.md` 中 DOI `10.1007/s00778-008-0122-1` 的 Springer 期刊题名改为 *Equivalence of queries that are sensitive to multiplicities*；另列 PODS 2006 前身 *Equivalence of queries combining set and bag-set semantics*，不再把会议题名配给期刊 DOI。原完整证明仍标为未读，不把书目纠正冒充证明核验。
2. **R2，JSON 范围。** `result.json` 的 hypothesis/scope 显式限定 `M,N,S,T ⊆ V ∖ supp(H)`。canonical head 使用按变量注入的新鲜值 `(h,0)`，重复 head 变量的全部位置固定相同；`0` 是原正文 `(h,*)` 固定值的等价命名。未归一化的、含 head 变量的计数集合不在该公式声称范围内。

替代关系、原文件 SHA-256 和不变数学正文 SHA-256 见 `REVISION_MANIFEST.json`；本目录内容哈希见 `SHA256SUMS.outputs`。只做文件复制、两项文本修订、JSON 语法及哈希核验，没有科学代码、查询、枚举或新假设。原独审者随后复核本修订；私有备份由根任务统一完成。
