# DKE 官方指南核验清单

核验日期：2026-10-12。目标固定为 Data & Knowledge Engineering，常规研究稿候选；未更换 venue、未投稿。下列未核验项不自动填为通过。

|项目|实际核验|当前状态|
|---|---|---|
|历史 venue 与 CCF|CCF 官方第七版目录，第33物理页，数据库 B 第4项 DKE；本地 PDF SHA256 271b630b576bf8a4f802e767f5694caded93680e22b3a19bef7902591c45c1d3，独审重算|已核历史来源，不推断录用|
|现行 DKE author guide|https://www.sciencedirect.com/journal/data-and-knowledge-engineering/publish/guide-for-authors 2026-10-12 实际返回403，独审亦未取得正文|未取得；不能认证完全合规|
|模板|沿用官方 elsarticle 3p,times,authoryear；TeX Live 2026 / elsarticle3.5；未改稿件边距或缩字号|可编译候选；DKE具体选项待核|
|页限、字数、摘要字数、审稿匿名制、参考格式|不能从第三方模板或旧内部十页目标推定|待取得官方正文|
|稿件类型及必须附件|本次备有主稿、源码、cover letter、5条highlights|DKE是否必须及具体命名待核|
|Highlights通用格式|Elsevier官方帮助 https://www.elsevier.support/publishing/answer/how-do-i-include-highlights-with-my-manuscript ：3–5条、每条≤85字符、独立可编辑文件|本文件包5条已按长度核验；不推定DKE必需|
|AI政策|https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals （June2026）已读|独立披露列出Codex、实际研究用途；独审GPT-6-astra/high；既往全部模型版本未保留，真人核验未确认|
|解释性图AI披露|现行政策允许AI辅助解释图，但caption需工具/版本/用途|TikZ可编辑图标明Codex辅助及原模型版本缺失；该缺项未伪装关闭|
|数据与代码公开要求|现有本地证据与源身份可追溯，尚未公开；源码ZIP不是完整实验包|DKE规则与作者发布决定待确认|
|作者、通信、CRediT、资金、冲突|仅历史作者顺序可核，其余不得替作者声明|待真实确认|
|科学新意与比较收益|已知因子化/selector；六臂与强基线不支持新机制优势|NO_GO，不能由格式修复关闭|

当前指南受限是具体访问结果，不以第三方网页替代。独审来源与细项见 review_local/PRE_REVIEW.zh.md。未修改旧稿、P19、系统设置，未提交或推送。
