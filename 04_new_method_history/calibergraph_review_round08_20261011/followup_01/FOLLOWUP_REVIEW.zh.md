# 第 08 轮独立复核 followup_01

日期：2026-10-11。本次仅验收 `revision_02` 与 `revision_03` 对冻结初审的四项修复，不改初审、不重审其他轮次、不执行查询或 fixtures。

**结论：四项发现全部解决。修订后的理论规范可作为成熟强控制保留；机制新颖性继续 NULL。** 原初审的 `HOLD_REPAIRABLE` 保留为历史结论；对两份修订合并后的当前规范，该形式化 HOLD 已解除。这里的验收不表示实现测试通过、性能优势成立或备份完成。

## 冻结对象与完整性

【证据·字节核对】revision_02 manifest SHA-256 为 `433ae73a67c1903f7b3b84cdcaccdef53f42a3962cd9de4eb6804efadc51eef5`；revision_03 manifest 为 `fe781f55001ad3dc60f1a3377ac78538008d6ad2363bf6b03ffffefd29e2766e`，均与委派输入精确吻合。前者锚定的 scope/cost 修正文稿、后者列出的三份修复文件的 SHA 和已记录字节数均通过核对。

【证据·字节核对】初审交付的 `REVIEW.zh.md`、`review_result.json`、`PRIMARY_ANCHOR_CHECK.json`、`REVIEW_MANIFEST.json` 全部保持冻结 SHA；原作者 manifest 及其 11 个文件也全部未变。各 JSON 可解析；文献中的评审释义 SHA 与其 UTF-8 文本吻合。以上仅为格式及完整性检查。

## 四项修复的独立裁决

| 初审发现 | 新证据位置 | 复核判定 |
|---|---|---|
| P1-01：域容量与良类型 | revision_02/SCOPE_AND_COST_CORRECTION.md:7–9；revision_03/theory_result.corrected.json 的 fragment.domain_and_typing、hypothesis_math_result、theorem.legal_for | **RESOLVED** |
| P1-02：完整输入成本 | revision_02/SCOPE_AND_COST_CORRECTION.md:13–17；revision_03/REPAIR_ACCEPTANCE.md:7；修正JSON的input_representation、construction_cost、output_bit_cost | **RESOLVED** |
| P2-01：平行FK图口径 | revision_02/SCOPE_AND_COST_CORRECTION.md:21–23；revision_03/REPAIR_ACCEPTANCE.md:9 | **RESOLVED** |
| P2-02：一手链接与定位 | revision_03/references.corrected.json；revision_03/REPAIR_ACCEPTANCE.md:11 | **RESOLVED** |

【判断·手推】P1-01 现在明确：有限数据库取值于共同无限不透明相等域，所有变量/位置良类型，没有有限SQL类型、隐式转换或额外域限制。于是每个有限 n 都能选出变量/索引所需的互异标签，canonical DB 的互异变量冻结也可实现。初审证明中的隐含前提已变成公开前提；没有把定理外推到有限枚举域。修正后的机器结果也将手推与 all-n 结论明确限定于该条件，修复完整。

【判断·手推】P1-02 现在以 S 计完整 schema（包括未用表和全部约束）、L 计显式 body 出现次数、h 计有重复位置的完整有序 head，v 计变量数。在显式整数ID、M/N 为紧凑去重子集时，读取并验证这些输入的代价纳入 `O(S+L+h+v)`；任意额外集合编码长度 j 使用 `O(S+L+h+j+v)`。见证单元格的 `O(L log(v+1))` 位界不再冒充完整输入/证书位成本。隐藏 chase、通用 SQL 求值和不同 body 的同构发现均未计入共同 body 构造的线性声明；不同 body 使用前须提供并验证变量运输。初审缺失的成本项及计费边界均已补齐。

【判断·文本核对】P2-01 现在按原理论的 underlying undirected simple graph 合并平行邻接，因此 dev03_06 的四条同源同目标 FK 本身不造成森林拒绝；每条完整 FK 和显式闭合仍须分别满足。原SQL的聚合排除保持独立充分，0/21 不变。旧 applicability JSON/文稿未改，故当前规范必须按两份修订的优先级共同读取，不能单独把旧“不明”字段当作新结论。这是明确的增补修复，不抹去原初审发现。

【判断·锚点核对】P2-02 与初审已核的一手原文一致：BDFS 使用 Fagin 作者直链原PDF并区分引理与随后构造；DeHaan 的 Definitions A.2.1/A.2.2 改至印刷168/PDF188，后续指定锚点为170/190、171/191；Chirkova 的 HTML/PDF 编号差异与 sound-chase 适用范围均已明列。FewRows 的 key-anchorability 条件及 F1/F2 四侧手推归属得到保留。本次使用初审冻结的来源核验，不重新浏览文献，不把评审释义 SHA 当作论文原字节 SHA。

## 有效规范、保留结论与剩余限制

【证据·文本核对】revision_02 第3行和 revision_03/REPAIR_ACCEPTANCE.md 第3行确立共同增补优先级；修正 JSON 的 revision_precedence 明确替代旧机器可读 scope/cost。故验收对象是“原冻结证明 + 两份权威修订”，不是仍带旧前提缺口的原稿单独版本。

初审手推成立的闭包充要条件、完整PK/FK合法性、恰 n 个满足赋值、T(2) 每表≤2行/总≤2|B|、不同body的head-preserving同构与计数集合运输均保持原范围。四项修复没有引入新机制、额外科学假设搜索或新的自然覆盖论证。机制仍为 NULL；固定开发切片的原始整对静态适用性仍为0/21，该数值继承已冻结初审，本次未重新读取开发语料、重写SQL或运行parser。

七个固定 fixtures 和三个预定消融仍全部未执行；没有新 test、SQL、SMT/solver、科学程序、模型/GPU或队列。标准库仅用于读取/序列化JSON和SHA校验。文献锚点协查只读了指定修复文字；其结果与本评审比较一致。初审与作者原文件均未改动。

本复核范围内未新增 P0/P1/P2 未决项。实现验证未做是明确保留的证据边界，不用追加实验关闭本次文稿修复。DataHub 注册缺口和私有备份状态属于主线治理，未在本复核中解决或宣称完成。最终文件 SHA 见 `FOLLOWUP_MANIFEST.json`；manifest 自身SHA随交付消息提供，避免自引用。
