# CaliberGraph DKE 候选稿：非作者预审

审核日期：2026-10-12。审核者为本轮独立 AI agent，未撰写或修改候选稿；先读取了旧稿诊断和阶段汇总，因此不是盲审，也不是真人同行评审。本次不执行 SQL、solver、训练或实验，不修改旧包。最终判定需绑定尚待冻结的候选 PDF 与源码；本文件不是最终验收。

## DKE 目标与官方规则

本机 CCF 第七版正式目录 PDF 已重新读字节，SHA-256 为 `271b630b576bf8a4f802e767f5694caded93680e22b3a19bef7902591c45c1d3`，72页，第33物理页列 DKE 为数据库类 B 级第4项。来源路径和 CCF 官方下载 URL 与 `task-2/ccf_b_retarget_20261009/ccf_local_metadata.json` 一致。这确认历史目标，不推断录用概率或最新门户状态。

2026-10-12 实际访问 [DKE Guide for Authors](https://www.sciencedirect.com/journal/data-and-knowledge-engineering/publish/guide-for-authors) 返回403；官方旧URL、PDF参数、scope页也未取得有效正文。官方搜索索引确认指南存在和刊物数据库/知识库题域，**不能确认现行期刊具体页限、字数、参考文献制式、匿名制、必需附件或数据政策**。第三方模板的250词、单盲等说法不作为正式规则。保留原 elsarticle 模板、不任意改边距或压页是合理准备，但不是DKE完全合规证据。

成功读取 [Elsevier现行AI政策](https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals)（标注June2026）：需要独立AI声明，列工具名称、用途及真实人工监督；研究过程的AI使用需在Methods描述。解释性图可由AI辅助制作，但每图caption需披露工具/version/用途；数据图必须由真实数据经可复现方法产生，并在Methods说明工具/version。不能继承旧的“一律禁止AI绘图”印象，也不能宣称尚未发生的作者核验。这里只是作者授权的内部审查，不冒称期刊正式审稿。

[Elsevier Highlights官方帮助](https://www.elsevier.support/publishing/answer/how-do-i-include-highlights-with-my-manuscript)确认通用规范为3–5条、每条≤85字符及独立可编辑文件，同时明确是否必需由期刊指南决定；DKE的必需状态尚未核验。

## 贡献与证据判定

|对象|能支持的结论|不能支持/已被控制削弱的结论|
|---|---|---|
|受限star SUM/COUNT与赋值级推导|明确语法、NULL/bag约定下的已知分解与selector等价性；独立base变量/契约边界可审查|不是新分解恒等式、一般SQL正确性定理或未界定域的证明|
|v5六臂28配置/22逻辑控制|127/168严格pair结果；selector22、flat23；失败完整保留|selector特有收益、统计加速、独立测试准确率均未建立|
|S01 N4廉价AND控制|普通结构归一化也获严格UNSAT|不能把此成功独占归因于selector|
|48,910公开查询槽|cached recognizer完整分母；6 eligible，两对均无JOIN|没有公开JOIN适用性；今日自然例不能改写旧截面|
|source-AST契约XOR、literal-left修复|某个输入域内两个解释器相等；具体6值反例及修复有效|不能以该工程错误修复充当新算法、合同业务真值、parser认证|
|Polygon四例双模式|4/8有效开发例、8槽，保留另2无效输入；两例有反例、两例有界UNSAT|不是与CaliberGraph同域速度比较；不是8/8覆盖；不支持强验证方法整体失效|
|ParSEval #1172|一次官方EQ与已保存合法1/0控制不符；9候选均相等|不是总体错误率；己方KeyError不能计入基线错误|
|3查询对8个SQLite合成库|具体完整DDL/C与原SQL的NEQ回放|不是8独立任务，不是Polygon求解成功，不建立业务合理性|
|COUNT P1/P2/P3|42个暴露表达式/算子链回归，P3均通过|不是完整QueryEncoder/Environment求解流水线证明，不是新科学贡献|
|历史159/122与1108 SQL|强prompt156/159>CG147/159；longest-alias后122/122平手；1108中1074超时、34首标量|不能恢复生产准确率、用户工时或业务金标；不能借旧指标证明新有界模块|

已知有限值抽象、shiftability、order type、CEGAR、symmetry reduction及anti-masking不能包装为新贡献。既有21包一手先例分析已说明该边界；候选稿如引用，应只用于限定贡献，而不是提出未经验证的新方向。

我的当前判断是 **科学NO_GO**：受限实现和负结果可信地可被描述，但未建立能由新方法/定理/有效比较承担的独立原创贡献。单纯转换为“语义边界研究”也需要明确、可推广、超越个案修复的发现及独立验证；当前暴露开发集不足以自动满足该门槛。这是审稿判断，不是DKE编辑部规定。

## 旧主文9条参考文献核验

|键|核验与建议|
|---|---|
|he2024verieql|[作者arXiv](https://arxiv.org/abs/2403.03193)及本地全文确认题名、四作者、2024、DOI3649849、Article132；原bib核心信息一致。|
|chu2017cosette|[CIDR官方PDF](https://www.cidrdb.org/cidr2017/papers/p51-chu-cidr17.pdf)和本地同文PDF首面确认题名及四作者，2017正确；无稳定出版页码无需捏造。|
|ding2023sqlsolver|[作者PDF](https://www.cs.yale.edu/homes/piskac/papers/2024SIGMOD.pdf)第1页ACM Reference Format明确2023、PACMMOD1(4)、Article227、26页及DOI3626768；文件名2024SIGMOD不使原bib年份错误。八作者一致。|
|olteanu2016factorized|[SIGMOD官方PDF](https://sigmodrecord.org/publications/sigmodRecord/1606/pdfs/03_principles_Olteanu.pdf)确认两作者、45(2)、2016、5–16；可补DOI10.1145/3003665.3003667。|
|thanisch2019measurement|作者本人出版列表与ScienceDirect作者索引确认题名、四作者、DKE122、116–129及2019；DOI页面403，未读全文。原稿承认仅据摘要分析是正确边界。|
|tremante2026spotit|[作者arXiv](https://arxiv.org/abs/2603.04334)确认六作者及2026；旧bib不存在漏作者问题。现页面为v3，原实验使用源码/版本须独立锁定，不能由最新摘要代替。|
|bakibayev2013aggregation|[arXiv](https://arxiv.org/abs/1307.0441)四作者与2013匹配；已正式发表于PVLDB6(14):1990–2001，[DOI10.14778/2556549.2556579](https://dl.acm.org/doi/10.14778/2556549.2556579)。建议引用正式出版项，若细节来自v1另列版本。|
|abo2023faq|2023是[arXiv v7](https://arxiv.org/abs/1504.04044)修订年份，不是首发年份；题名与三作者正确。首次arXiv2015，正式[PODS2016,13–28,DOI10.1145/2902251.2902280](https://dl.acm.org/doi/10.1145/2902251.2902280)。建议正式出版项为主并保留v7注记，避免掩盖既有工作年代。|
|zhao2025polygon|[作者arXiv](https://arxiv.org/abs/2504.06542)与本地全文确认三作者、2025、题名、DOI3729303；已知正式PACMPL9(PLDI),1315–1340，最终bib应统一正式项格式。|

所有旧条目均找到真实一手作品；未发现虚构引用。不把9条元数据核验说成逐篇全文验证。新增ParSEval/BIRD等引用待候选源码冻结后另核。

## 终审前必须保留的边界

1. 完整主稿保留原方法、前提、负结果、失败分母，分开旧v5与自然开发诊断，不能拼成单一准确率/速度榜。
2. “全部输入/完整C”必须指明锁定源约束，不能由PK/NN/FK项数推论SQLite任意类型与业务真值保真；#1526日期冲突保留。
3. 作者、机构、通信、贡献、资金、利益冲突及真实技术核验尚未确认；只可标记待确认，不能默认无冲突/无资金或已核验。
4. Surface和figure-design本轮已读取并应用。待最终PDF逐页、图页100dpi/灰度检查及最终log/hash；旧bbox SIGABRT必须记UNAVAILABLE，不能写自动PASS。
5. 最终独审仅对冻结一次完整稿进行；作者若修订，应明确该报告绑定的版本，不转移通过结论。
