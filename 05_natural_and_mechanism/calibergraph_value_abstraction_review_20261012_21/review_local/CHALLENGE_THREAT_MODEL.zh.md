# 非作者独立挑战预记录

记录时间：2026-10-12T11:58:39Z。角色：`/root/domain_independent_challenge`。本记录在收到主作者最终候选稿之前形成，不提出候选方法，不是最终裁决。仅静态阅读已有文件和检索原始文献；未运行 SQL、solver、benchmark 或实现。只写入新包 `review_local/`。

## 已有证据确切支持什么

【文件证据】`calibergraph_polygon_adapter_20261012_15/PROOF.zh.md:3–32` 的证明绑定 #1172 的 SQL/DDL、每源表至多一行、默认 SQLite 快照语义和完整声明约束 C。`16/case1172_adapter.py:12,47,73` 主动拒绝超界。C 是源 DDL 的 2 个 PK 声明、3 个显式 NN、2 个 FK，不包括额外临床业务约束。

【文件证据】N≤1 使两个输出各为 0/1；合法 Lab 的非空 FK 必指向唯一 Patient。`15/PROOF.zh.md:7–20` 因而允许非空 ID→1，Lab.Date→0，T-BIL→NULL/below/equal/above 四类，SEX→NULL/M/other。`16/case1172_adapter.py:65–113` 先验证抽象 C，再固定提升，最后原 DDL/C/SQL 回放；此顺序防止把坏 FK 改成 1 以后伪装合法。

【文件证据，未重跑】`16/RESULT.zh.md:3–18` 记录 UA、precise 均输出原 SQL 的 (1,0)，两个运行得到同一个具体数据库。`:30–34` 已明确撤回把 #1172 当作新生成机制必要性的证据。单例成功不证明自动综合、跨例正确性、效率优势或方法新颖性。

【文件证据】`17/PROOF.zh.md:3–15` 是 #1261 的另一份单独手工 N≤1 证明；RF 是 TEXT 亲和性，`RF<20` 必须按原 SQLite 比较，其分类不等于把文本转成数值。重复出现适配劳动可支持工程动机，但不是一种自动算法已经必要或可行的证据。

## 在审稿前固定的决定性攻击

1. **跨行关系不可从独立 unary bucket 恢复。** 静态构造（未执行）：固定 Patient={(10,M),(20,X)}、Examination 空、Lab 恰一行且 T-BIL=2.0/Date=1；Lab.ID=10 与 Lab.ID=20 两个数据库均满足原完整 C。原 #1172 输出分别 (1,0) 与 (0,0)。若每个非空 ID 都独立映射到同一类，两个抽象编码相同；同时两个 Patient 键碰撞。这只反驳超界泛化，不能称旧 N≤1 证明有 bug。关键锚点 `16/case1172_adapter.py:56–60,85–88`。
2. **查询未观察的列仍可能被 C 观察。** 同一父 ID 下两条 Lab 的 Date=1、2 满足复合 PK；Date→0 产生冲突。故 query-only slicing 若遗漏 constraint closure 不保 soundness。旧证明已在 `15/PROOF.zh.md:18,36` 和独审 `15/review_local/SEMANTIC_REVIEW.zh.md:26` 声明这一点。
3. **值域有限化不等于袋关系有限化。** COUNT DISTINCT 依赖相等模式，COUNT 依赖行重数，JOIN 会放大重数，SUM/AVG 还依赖数值关系。声称支持 aggregate 却仅证明单值阈值真值保持，应直接判定证据不足。必须先明确所保持的是每个查询的输出、输出重命名，还是只保持最终 NEQ 谓词；三者不能互换。
4. **有限 unary 商对任意相等关系不可能忠实。** 若无限可比较域映射到有限 unary 集合，存在 x≠y 却 α(x)=α(y)；比较 (x,x) 与 (x,y) 的抽象输入相同而原相等真值相反。这是抽屉原理的静态推论。固定 N 可使关系模式数量有限，但不能让逐单元独立 bucket 自动成为关系商。
5. **顺序与算术不能由同阈值类代替。** x=3、y=4 都可能属于 >2 类，但 x<y 与 y<x 不同；两组各值均 >2 的输入可使 SUM>10 真值不同。以上为一般化威胁，并非 #1172 原查询含这些算子。若直接排除它们，剩余适用面必须如实计入可行性判断。
6. **有限商存在是弱结论。** 对固定数据库大小且只观察最终 EQ/NEQ，按该布尔观察定义两个类总能形式上“存在”；寻找类代表却可能要求先解原问题。没有构造算法、可判定片段、证书检查义务和成本，存在性不构成方法进展。若保持原始投影值逐值相等，则即使 N=1，任意原值投影也不能压成固定有限输出集合。
7. **方向性不可偷换。** 成功提升并真实回放的 SAT 见证只证明存在一个合法反例。以有限代表集 UNSAT 推回所有原值域需要 forward coverage；以抽象 SAT 推回原 SQL 需要 lift soundness。二者都不消除 row bound。没有独立的 cutoff/small-model 定理，不得从 N≤k 升级为所有行数等价。
8. **SQLite 的关系语义有上下文。** 比较受存储类型、列亲和性、操作数表达式、排序规则、NULL/三值逻辑影响。旧证明用原列上的比较计算类，且拒绝 TEMP/ATTACH/UDF，正说明字段名字和 SQL 运算符不是充分语义。抽象器和校验证书若共用同一错误前端，哈希和回放不能证明所有未见数据库上的正向覆盖。

## 独立取得的最近原始文献压力

以下“覆盖”指已发表方法机制，非本人复现；没有以检索未命中断言首次。

| 原始来源 | 读到的位置与直接压力 | 本轮边界 |
|---|---|---|
| Graf & Saidi, CAV 1997, [作者机构页](https://www.csl.sri.com/papers/grafsaidi97/), [出版记录](https://link.springer.com/chapter/10.1007/3-540-63166-6_10) | 摘要已明确以谓词划分状态空间并自动构造抽象状态图。故“查询谓词→有限类”不能独占为新思想。 | 原 PDF 文本编码损坏；仅将机构摘要中明确的机制用于判断，未声称审完其证明。 |
| Clarke 等, [Abstraction and Counterexample-Guided Refinement in Model Checking of Hybrid Systems](https://www.cs.cmu.edu/~emc/papers/Papers%20In%20Refereed%20Journals/Abstraction%20and%20counterexample-guided.pdf) | §2 定义有限抽象与保守性，§3 说明具体反例验证与消除伪反例的细化。证书、反例回放和 refinement 的一般架构已有。 | 与 SQL 类型/袋/约束专门问题不是同一算法；不能据此断言任意具体新算法已被完全覆盖。 |
| Lazić–Newcomb–Roscoe, TPLP 2004, [作者稿](https://arxiv.org/abs/cs/0405103), [出版记录](https://doi.org/10.1017/S1471068404002054) | 摘要的 data independence 明确限制数据操作为相等测试，并为特定系统/逻辑研究有限实例和参数化结论。 | 这不自动覆盖 SQL 顺序、聚合或 SQLite coercion，更不能直接借用其 cutoff。 |
| VeriEQL, [论文](https://arxiv.org/html/2403.03193v2) | Definition 3.5 明确对满足 C、每关系≤N 的数据库量化；Algorithm 1 同时编码约束、查询和输出相等。 | bounded symbolic SQL 和 full-C 目标本身不是新问题；理论片段与真实 SQLite 实现边界仍须分开。 |
| Polygon, [论文](https://arxiv.org/html/2504.06542v1) | §3.3 说明 full semantics 仍有有限行数 bound；§3.2–3.8 是覆盖式算子 UA 族和冲突驱动搜索。 | 新 value abstraction 若成立可能与算子 UA 正交，但“覆盖/搜索/结果差异目标”均已有；旧 #1172 已被适配后的两模式解决。 |
| Cosette, [作者论文](https://www.cs.cmu.edu/~15811/papers/db.pdf) | §2 把 bounded 反例搜索和独立证明路线分开；§3.1 使用整数元组和 multiplicity 表示 bag，并说明当时不支持浮点。 | 字符串整数化、有限实例反例和机器可核验证明不是新概念；不把该原型局限当作今日所有基线的共同缺口。 |
| Ball–Kupferman–Yorsh, CAV 2005, [出版记录](https://link.springer.com/chapter/10.1007/11513988_8) | Abstraction for Falsification 是应当对照的直接机制邻居，Polygon 也引用它。 | 本轮完整正文获取失败，只记录文献威胁，不从标题推断具体定理。 |

## 最終稿的单次判定准则

仅若最终稿给出一个真正方法问题、清楚承认以上已有机制，并明确待证的非平凡余量，才可能给 `ACCEPT_FOR_BOUNDED_FEASIBILITY_ONLY`。这只允许讨论一个有边界的可行性研究，不等于方法正确、足够新颖或值得投稿。若仍缺关键可构造性/自然任务价值证据，给 `HOLD`。若核心只是逐值 bucket 加证书/CEGAR、parser/COUNT 修补或旧 #1172 反例重新包装，给 `REJECT`。
