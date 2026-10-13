# CaliberGraph DKE 候选稿：冻结版非作者终审

日期：2026-10-12。结论：**可以交付为完整、如实限定的作者审阅候选；正式提交仍为 NO_GO。** 这不是编辑部决定或拒稿预测，也不提供录用概率。

## 身份、对象与实际范围

本审核由独立 AI agent `/root/dke_candidate_independent_review` 完成。我没有撰写、修改候选正文或图表，没有运行 SQL、solver、训练或科学实验；仅在 `review_local/` 写报告。已先阅读历史诊断、旧稿与阶段汇总，故为**非作者、非盲审的内部AI审查**，不是人类同行评审。前一阶段的 `PRE_REVIEW.zh.md` 是预审；本报告是唯一一次完整冻结稿终审。

- 主稿：`manuscript/build/main.pdf`，14页，SHA-256 `07ac0553fdebc0200fb2cfc4751b258f991a177801748c26ad5e3db470528847`。
- 主源码：`manuscript/main.tex`，SHA-256 `ada1b12ed886acac445dd38e2f71ee4beb1d68754be2e4c59a77f1285b11f0b0`。
- 一页决策书：`decision_build/GO_NO_GO.pdf`，SHA-256 `52a3d3cd2a12f68bc33ee462ab1cefc28a420299f7957a9165ac437f3bb81e88`。
- `REVIEW_FREEZE.json` 所列9个文件均实际重算SHA且匹配。`results_current.tex` 与 `contract_bridge_v5.tex` 和旧11页文案勘误版逐字节一致。
- 实际阅读主tex、3个输入tex、12条bib、最终log、bbl、surface回执、claim matrix、guide checklist、cover-letter草稿、highlights及GO/NO_GO源码；逐页查看全部14张最终页面；查看决策书、独立图、独立灰度图和第6页灰度合成图。
- 保留并复用旧数值/源码审计，新增核对Polygon八槽墙钟/调用数与13/16/17包结果，SQLite八见证和COUNT四版42项与19/20包及阶段最终表一致。本次未重新执行科学回放，不称复现实验。

## 贡献、实验与强基线

|审核对象|冻结稿判断|
|---|---|
|问题与对象|固定SQL对、给定契约、有限tuple域的受限实现已明确；不再把业务意图、旧NL2Metric结果与新模块合并。|
|Lemma 1–2及方法|固定赋值下分离叶谓词的Cartesian计数与selector分支恒等式成立于声明前提；NULL标志、bag重数、fresh定义、cross-leaf拒绝和非线性残留均交代。它们是已知构造，不是新的一般正确性定理。|
|原完整结果|168成本槽/127严格结果；168差分槽/115严格一致；SpotIt28/21均保留typed/domain/unknown/monitor失败。169成本尝试及未知完整成本的中断未抹除。|
|六臂与cheap控制|flat23、selector22；medians1.314/1.333秒，单次不同结果混合不能推断稳定速度。cheap AND也解决S01 N4。正文、摘要、结论与决策书均没有将其写成selector特有收益。|
|公开适用性|48,910查询槽、6eligible、两对均无JOIN，完整分母和cached AST边界保留。未用新增自然开发例改写原覆盖率。|
|自然开发样本|10对/8合法/4准入Polygon；先见anchor1172、分层/去重/hash选择、无refill和开发暴露均披露。4个未准入不计solver失败，2无效输入仍在分母。|
|ParSEval1172|阈值≥2.0对>2.0、9保存库相等、独立合法1/0控制、DISTINCT掩盖与己方Patient KeyError均分开。其单例不足以推断总体错误率或独有因果机制，文中已明确。|
|Polygon|八槽14调用、两对具体NEQ/两对bounded UNSAT；墙钟与源记录相符。3秒/512MiB内部限制、12秒worker/60秒batch、平台改变、局部observation adapter、固定lift和中间SAT不构成见证均披露。没有与v5混榜，也没有将bounded UNSAT提升成unbounded EQ。|
|SQLite8见证|三个已暴露查询对中的8个合成库；表7保留NULL、bag、coercion、grouping差异、N和总行数。#1490仍static，#1526日期意图未定；未说成8独立任务、Polygon成功或真实业务数据库缺陷。|
|COUNT|Original/P1/P2/P3各28表达式+14算子链；P3=42/42，四版168记录。明确零solver与未跑完整pipeline，属修复而非创新。|
|历史边界|156/159强prompt对147/159CG、alias敏感122/122与120/122，以及1108SQL中1074超时/34首标量、1488 semantic unknown完整保留。|

**科学NO_GO依据**：目前可确认的是受限实现、已知恒等式、失败保留及若干可追溯诊断；selector没有独有比较收益，现有强方法已经处理被准入的自然例，COUNT/parser/契约修复属于工程纠错。有限值抽象、anti-masking及先例里的观察等价思想没有被本稿重新包装成创新。将标题改为“语义边界”并不能自动建立可推广的独立研究贡献。该判断并非要求所有论文必须发明算法；一项足够扎实、可推广的独立经验发现也可能承担贡献，但当前暴露个案/回归材料尚未建立它。

## 参考文献与声明

12条bib与12条输出bibitem一致，无未定义引用。旧9条的题名、作者和主要出版身份预审已核；本次确认两项建议已落实：Bakibayev使用PVLDB2013正式项；FAQ使用PODS2016并另注2023 arXiv v7。SQLSolver的2023出版年正确，不能由作者PDF名2024SIGMOD改成2024。Cosette无确定页码，BibTeX保留一条empty pages警告，不应编造页码。

新增三条分别为：[ParSEval官方PVLDB PDF](https://www.vldb.org/pvldb/vol18/p4750-miao.pdf)的Chen/Miao/Zhang/Wang，18(11):4750–4762(2025)；[Few Rows作者arXiv](https://arxiv.org/abs/2609.09978)的Sara Cohen，2026 v1；[Aggregate Queries作者记录](https://arxiv.org/abs/cs/0210028)及21包已核出版信息的Cohen/Nutt/Sagiv，TOCL6(2):328–360(2005)。未见虚构条目。Few Rows作为预印本列出，没有冒称已同行评审。此次不是对所有被引论文全文的独立形式验证。

AI披露和figure caption如实列Codex用途，包含代码、实验、分析与写作，并承认旧模型版本未留存、真人核验和批准未完成。此诚实性足够支持作者审阅候选，但不是完整投稿声明。现行[Elsevier AI政策](https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals)要求工具/用途/监督及相关研究过程说明；可恢复的版本记录及实质人类核验仍待作者处理，不能靠独立AI报告代替。

Cover letter明确DRAFT/DO NOT SUBMIT，保留相关投稿谱系、待确认信息和NO_GO，不虚构利益冲突、资助或所有作者批准。Highlights为5条，长度分别78/77/72/72/76字符，满足已核Elsevier通用长度规则；不据此宣称DKE必须附件已核验。历史作者顺序可以保留，机构、通信、贡献和各种声明仍需真实作者确认。

## 页面、图表与自动门

- 全14页实看：无可见缺字方框、剪裁、覆盖、表行丢失、公式编号冲突、图注错位或不可读正文。主文至第13页结论，第13页开始参考文献，第14页仅参考文献。14页为观察值，不是DKE页限通过。
- 7个显示公式、2条lemma、1幅方法图、8张表可识别。表2–4保留完整原实验，表5–8清楚区分新增诊断和修复。表3已使flat/selector及cheap控制比较直接可读，不强加重复装饰性结果图。
- 图1在第6页；role=受限编码机制/例解。连续对象是root measure3和leaf counts(2,3)，通向product18与selector3→6→18；count1→2→6及scalar NULL条件可追踪。headline任务及机制任务均通过，独立与100dpi/灰度/页内版本的文字、箭头、框均有可见间距，未见几何阻塞。不是新机制或性能证据。
- 匹配的已发表先例：Olteanu/Schleich, *Factorized Databases*, SIGMOD Record2016，真实关系→分解表示用于校准具体数学对象；Chen等, *ParSEval*, PVLDB2025，具体数据库和对比输出用于校准可读的语义证据载体。只借鉴证据组织，不复制布局。Few Rows未用作已发表图形先例。
- 主稿最终LaTeX log中overfull、underfull、undefined、missing-character/LaTeX warning为0；字体清单全部嵌入Type1，无Type3。独立PyMuPDF文本检查未发现U+25A0/U+25A1/U+FFFD。BibTeX另有上述Cosette页码警告，不能统称所有构建警告均0。
- 主稿与决策书的标准脚本实际退出1，bbox提取SIGABRT，故自动spacing=**UNAVAILABLE**。目视和零日志异常不是自动PASS替代品。
- 独立图标准脚本完成PDF分析，spacing/type3/suspicious glyph/log均0；原始结果仍为**FAIL**，仅两条`forbidden_tikz_figure_source`。这与当前已读skill优先保留可编辑向量并避免仅因工具类别重画既有有效图的文字要求冲突。本审按现行文字要求接受图的视觉/科学表达，保留原始FAIL与解释，**不改脚本、不隐藏警告、不宣称整项自动通过**。

## 必须解决项与最终边界

**交付这一冻结作者审阅候选前：本次未发现新增P0/P1数值、引用或版面修复项。无需为本次审查重复已有科学实验。** 报告通过范围仅是完整候选材料的忠实性与人工方式的AI目视审查。

**正式提交前仍不能跳过：**

1. 科学贡献/可推广经验发现与适当强对照的证据缺口；这不是措辞或页数能修复的问题。本报告不授权启动新实验。
2. 取得现行DKE官方Guide核实具体模板选项、页/字数、匿名制、参考格式、必需附件及数据声明。当前403访问结果只支持“未核验”。
3. 真实作者技术核验、全体批准、作者元数据、CRediT、资金/冲突、同期投稿/重叠及数据代码发布声明；补齐可恢复的AI版本来源，对不可恢复项维持披露。
4. 自动surface门的bbox不可用及TikZ旧规则冲突需继续留在交付状态中；不得对外描述为所有格式/自动审计均通过。

本报告绑定上述冻结SHA。后续若仅修订报告或清单，不影响主稿对象；任何主PDF/源码改动必须标明新hash，并只对其实际差异追加核验，不能把本报告未经核验地移植到新版本。
