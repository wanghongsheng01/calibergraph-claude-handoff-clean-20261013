# DKE 一手核实：measurement issues 目标论文

日期：2026-10-11。执行范围：只读、有界文献核实；未运行 SQL、SMT、代码或实验，未 clone/install，未保存或分发第三方论文全文。

## 目标如何确定

最初任务没有提供具体 DKE 标题，因此最初按透明候选检索。随后父任务从旧冻结稿 `references.bib/main.tex` 找到明确目标，下述记录据此只保留这一篇；文件名 `dke_candidates` 仅为预先约定的交付路径，不表示猜测它是用户唯一意指的论文。未纳入第二篇低相关候选。

**已核实书目**：Peter Thanisch, Tapio Niemi, Jyrki Nummenmaa, Marko Niinimäki. *Detecting measurement issues in SQL arithmetic expressions and aggregations*. **Data & Knowledge Engineering 122 (2019), 116–129**. DOI: [10.1016/j.datak.2019.06.001](https://doi.org/10.1016/j.datak.2019.06.001)。作者机构的[论文记录](https://researchportal.tuni.fi/en/publications/detecting-measurement-issues-in-sql-arithmetic-expressions-and-ag/)完整显示作者、期刊、年份、卷页、DOI 及 peer-reviewed 状态；[作者公开 publication list](https://sites.google.com/webster.ac.th/niinimaki/niinimaki-publications)独立列出同一题目和卷页。出版社[122 卷目录](https://www.sciencedirect.com/journal/data-and-knowledge-engineering/vol/122/suppl/C)搜索索引也列出该文和 DOI。**VERIFIED_PUBLICATION；不是仅候选投稿。**

## 来源与获取边界

| ID | 真实 URL | 本轮可观察状态 / 可用层级 |
|---|---|---|
| S1 | https://researchportal.tuni.fi/en/publications/detecting-measurement-issues-in-sql-arithmetic-expressions-and-ag/ | 已读机构一手元数据；没有可读全文或摘要正文 |
| S2 | https://www.sciencedirect.com/science/article/pii/S0169023X1730589X | 出版社 article URL 搜索索引可见标题与摘要片段；直接打开 HTTP 403 |
| S3 | https://www.sciencedirect.com/science/article/abs/pii/S0169023X1730589X | 直接打开 HTTP 403 |
| S4 | https://www.sciencedirect.com/journal/data-and-knowledge-engineering/vol/122/suppl/C | 出版社卷目录搜索索引有该文；直接打开 HTTP 403 |
| S5 | https://www.sciencedirect.com/author/6507393852/jyrki-nummenmaa | 出版社作者页搜索索引可见该文 metadata rules / static checks 的摘要片段；直接打开 HTTP 403 |
| S6 | https://sites.google.com/webster.ac.th/niinimaki/niinimaki-publications | 已读作者公开书目；无全文 |
| S7 | https://dl.acm.org/doi/10.1016/j.datak.2019.06.001 | ACM 索引可见题目、Elsevier 出版信息及摘要起句；直接读取失败；不是本文出版方 |
| S8 | https://www.academia.edu/91459592/Detecting_measurement_issues_in_SQL_arithmetic_expressions_and_aggregations | 搜索索引出现自称 accepted manuscript 的文字，含 DOI、PII、摘要和引言；上传者/字节/版本未核，不作为一手全文证据 |
| S9 | https://doi.org/10.1016/j.datak.2019.06.001 | 本轮 web 读取失败；DOI 由 S1/S4 交叉核对 |
| S10 | https://api.elsevier.com/content/article/pii/S0169023X1730589X?httpAccept=text/xml | 本轮 web 无法读取，不绕过访问控制 |
| S11 | https://api.crossref.org/works/10.1016/j.datak.2019.06.001 | 本轮 web 读取失败；本机 urllib 只读请求 DNS 失败，没有据此新增元数据 |
| S12 | https://www.sciencedirect.com/science/article/pii/S0169023X1730589X/pdf | 本轮 web 读取失败 |

**FULLTEXT_UNRESOLVED**：未取得可核身份与版本的出版社或作者一手全文；没有 PDF 校验和、没有有效页级实验表锚点。搜索索引片段不等于阅读全文。第三方稿件只能作为寻找一手稿件的线索，不能把它升级为 publisher-verified evidence。

## 任务、方法与 novelty 边界

| 事项 | 当前可写内容 | 层级与定位 |
|---|---|---|
| 任务 | 研究 SQL 算术表达式与聚合中的 measurement issues；出版社摘要片段明确把违反数据数值属性限制的错误聚合作为研究对象 | 【声称·摘要片段】S2；书目题目 S1 |
| 方法 | 出版社作者页索引出现由数据提供方供应 metadata rules，以及已实现 static checks 的描述；与镜像摘要一致 | 【声称·摘要片段】S5；完整方法链、规则集、soundness/completeness 均 UNRESOLVED |
| 相关主题 | Aggregation、Measurement scale and unit、SQL、Summarizability | 【证据·机构元数据】S1 的 keywords |
| 新颖性 | 不能据此判定它是首次、覆盖全部聚合语义，或已经解决 CaliberGraph 的全部任务 | 【判断】仅有书目与局部摘要，缺全文和共同任务定义 |
| 任务定位 | 是需要认真比较的聚合测量语义相关工作；不得降格为 syntax-only | 【判断】S2 把数值属性导致的聚合错误单列，已足以反驳 syntax-only 的描述 |
| 与查询等价/反例搜索关系 | 是否定义双查询等价、生成区分数据库、给出 bounded/unbounded 证明，均未取得一手证据 | UNRESOLVED；不是 UNSUPPORTED，也不是 NOT_IMPLEMENTED |

## 语义支持矩阵

| 语义/能力 | 核实状态 | 正确解释 |
|---|---|---|
| 数值测量属性与错误聚合 | ABSTRACT_LEVEL_SUPPORTED | 仅问题定位及摘要声称；未验规则正确性 |
| Measurement scale/unit、summarizability | METADATA_CONFIRMED | 机构关键词，不等于每种操作均支持 |
| PK | UNRESOLVED | 未读到一手定义/实现，不能填 No |
| FK | UNRESOLVED | 同上 |
| NULL / SQL 三值逻辑 | UNRESOLVED | 摘要不提不构成排除证据 |
| bag/set 与 duplicate multiplicity | UNRESOLVED | 无一手形式语义锚点 |
| join/fanout、outer join | UNRESOLVED | 无一手规则或覆盖表 |
| GROUP BY / HAVING 的精确覆盖 | UNRESOLVED | 标题中 aggregation 不足以推出所有构造 |
| 关系/分组语义 | UNRESOLVED | 不能因“measurement”名称就判为不涉及关系语义 |
| 跨查询等价性与反例数据库 | UNRESOLVED | 未证实有，也未证实没有 |
| tuple bound、域 bound、穷尽性保证 | UNRESOLVED | 无可核正文；不得代入 FewRows/Polygon 的 bound |

## 实验分母、预算、成本与复算状态

所有结果状态为 **NOT_REPRODUCED**。没有采集实验原始数据或执行作者程序。

| 项目 | 状态 |
|---|---|
| 查询数、受试者数、数据集数、错误类别数 | UNRESOLVED |
| 成功/失败/排除/超时的总分母 | UNRESOLVED |
| baseline 身份与相同输入/元数据预算 | UNRESOLVED |
| bound、timeout、机器/硬件、重复次数、随机种子 | UNRESOLVED |
| 构建元数据规则的人力成本、覆盖率及人工标注协议 | UNRESOLVED |
| 运行时间/内存、端到端成本、精确率/召回率 | UNRESOLVED |
| 已公开可复现代码/数据与许可 | UNRESOLVED |

S8 的引言索引提示 §7 包含 interface/performance，§8 包含 experiment，但其上传和版本身份未核。这条只作为全文定位线索，不据它填写任何性能数字；同时明确禁止写“本文没有实验”。需要一手全文检查这些节的实际内容及表格后，才能改变上述状态。

## CaliberGraph 可支持与不可支持的陈述

可支持：DKE 已于 2019 年发表围绕 SQL 聚合测量属性错误的相关工作；CaliberGraph 的背景和相关工作必须正面引用。可以把“测量属性规则检查”和“带指定 schema/约束/语义的关系结果差异证据”列成待核比较轴，但后一个轴只是 CaliberGraph 需要自行证明的目标，不是本轮已验证功能。

不可支持：CaliberGraph 是首个检测 aggregation semantic errors 的方法；该 DKE 文只检查语法；该文没有 NULL、PK/FK、关系语义、反例或实验；CaliberGraph 已在效果、成本、完整性或表达能力上超越该文；有限样例排除该文全部能力；或已经独立复现 DKE 结果。

最小后续证据：取得出版社或作者公开的身份和版本可核全文，逐项定位其规则、输入/输出、语义边界、§7/§8 及表格；在共同任务、共同元数据输入和明确分母下，才规划另行获授权的比较。本轮不扩展为实验。

## 运维与交付状态

按父任务指示，DataHub 映射已由 root 执行且无匹配；canonical registry 不在可写范围，**DATAHUB_REGISTRATION_BLOCKED**（父任务统一记录和处理）。这里只写本文件及同目录 `dke_candidates.json`。私人 GitHub 备份由父/root 统一处理，本文不声称已备份；交付给父任务时为 **BACKUP_PENDING_PARENT**。
