# H14 revision_02 独立复核

日期：2026-10-11。复核人：原独审者 `/root/round14_independent_two_corner_review`。初审的 report、decision 和哈希清单保持冻结。本附录只复核初审要求的 R1／R2，不重写原审查结论。

**两项文档修订均已关闭。数学状态仍为 `MATH_PASS_WITHIN_STATED_CORE_FRAGMENT`；新颖性及研究机会仍为 `HOLD / NULL`。**

【证据·文件核验】先对作者 `calibergraph_next_20261011_14/revision_02/SHA256SUMS.outputs` 的 4 个文件全量校验，全部匹配；随后读全修订文件并将两份替代文件逐行对比初始冻结稿。`primaryanchors.md` 的 SHA256 为 `b2c9c084317e36af3c1d454264215c8767104dc85b3598d99f5f6eb370c8032d`；`result.json` 为 `3e230b414d20c08cec6f986bb3535a121f90eb0723aceedfd8555192bb7a9aaa`。

【判断·R1 CLOSED】修订后的书目正确区分 Cohen 2009 的 *Equivalence of queries that are sensitive to multiplicities*（DOI 10.1007/s00778-008-0122-1）与 PODS 2006 的 *Equivalence of queries combining set and bag-set semantics*；与初审直接阅读的 [Springer 记录](https://link.springer.com/article/10.1007/s00778-008-0122-1) 一致。Cohen 2009 原始完整证明仍标注未读，因此书目修订没有伪装成先例检索完成。

【判断·R2 CLOSED】修订后的 hypothesis 和 scope 明确 M,N,S,T⊆V∖supp(H)，声明包含 head 的未归一化计数集不被公式覆盖，并规定 canonical head 逐变量注入、重复头变量重复同一个固定值。修订使用 H 表示头元组、supp(H) 表示支撑，原 theory 使用 h／H；这是明示的记号差异，不扩大数学范围。

【判断】修订所写固定 tag 0 与原 theory 的固定 tag * 有显式命名对应。由于所有克隆集合排除 head，head 的 `(h,0)` 并不是额外克隆选择；按变量的新鲜域仍互不相交，故不引入计数因子或新测试库。

【证据·文件核验】原 `theory/` 中 5 个作者输出继续全部匹配原清单；数学正文 SHA256 仍为 `3925237a0f59110b505982187c56ee92656531d34b67184184f8b892b7d3ff03`。初审自己的输出清单亦保持匹配。没有改动数学正文、手例、旧轮次、作者文件或初审文件。

【判断】当前可采用的阅读组合为：原 `theory/theory.md` 与 `handcontrols.md`；`revision_02` 中两份替代书目／结果文件；原初审加本复核。作者文件中的“待独审”是作者冻结时状态，独审结果以本目录 decision 为准，不要求改写历史记录。

【判断】不再有开放的 R1／R2 文档问题。剩余阻碍为直接先例原证明未核、无匹配总成本优势证据、自然覆盖证据为 0；DataHub 注册仍由父任务处理并保持 BLOCKED，私有备份尚待父任务核验。这些限制不改变当前范围的数学手审通过，也不允许晋升机会或启动科学执行。

【证据·执行记录】本复核仅做文件阅读、文本差分、SHA／JSON 核验和复核文档写入。未执行查询、枚举、SQL、SMT、GPU、模型 API 或实验。复核文件的输入、输出哈希见同目录清单；输入路径相对于 workspace 根，输出路径相对于本目录。恢复时按这两个相对根核验；父任务负责私有远程备份。
