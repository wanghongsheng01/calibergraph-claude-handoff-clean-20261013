# V5 最终全文与视觉独立复审

**最终结论：11 页全部实际目视与全文复核完成，当前审阅范围无开放 P0/P1；机制图 P1 已关闭。科学状态仍为 NO_GO，不代表可投稿。自动 bbox 检查仍失败，不能写自动 PASS。**

最终 PDF：`manuscript_v2/build_final_v3review/main.pdf`，SHA256 `d1b26713fdf5183b75d2ca0125856d65ea431a915024f1d637a9a50b1abb31ed`，11 页。main.tex：`c974f02466638d525c75de88688eba149fccbe6d25098a4156743d7a112aa7e9`。results/bridge/bib 与已核 cut 未变，精确 SHA 见 JSON。

我与稿件作者是不同 AI 执行者；曾参与支持闭包、公开扫描器、隔离诊断及 v5 代码审阅，因此不是盲审、真人同行评审或真人金标。本轮不改稿、不联网，不 import 或运行 target/native/solver。

## 实际逐页范围

旧 v1、v2 的各 10 页均实际看过；收到最终 v3review 后，又用 view_image 将 1–11 页全部重新查看，均为最终页面 100dpi 灰度。没有仅靠旧 PDF 或像素复用声称终审。

|页|所读范围|结论|
|---|---|---|
|1|Title/authors/abstract, internal status, introduction|127/168,115/168,6/48910 correct; explicit scientific NO_GO; ten-page statement is a planning target, actual PDF11；无明显裁切、碰撞或乱码。|
|2|Related work and formal task/domain|Known factors, Polygon at-most, SpotIt set/scalar boundary; exact positive rows and INT32 explicit；无明显裁切、碰撞或乱码。|
|3|Fragment, scalar NULL semantics, Equations2–4|COUNT(expr), root arithmetic, alias union, exact leaf counts and no-leaf product1；无明显裁切、碰撞或乱码。|
|4|SUM/selector Equations5–6, lemmas/proofs|Assignment-wise identities only; strict NULL and no solver-speed guarantee; no proof-end squares；无明显裁切、碰撞或乱码。|
|5|Construction example, frontend/dialect, bridge grammar/Equation7|Example distinct from executed size; full original C; base-only SAT/XOR and no fallback on unsupported C；无明显裁切、碰撞或乱码。|
|6|New mechanism Figure1, bridge continuation, mapping Table1|Exact counts feed alternative product/selector paths and converge on same scalar; readable arrows/labels and correct NULL/example boundary；无明显裁切、碰撞或乱码。|
|7|Oracle domain, evaluation design, Table2|Original SQL replay and shared-oracle limitation; exposed DEV; all categories and denominators visible；无明显裁切、碰撞或乱码。|
|8|Recovery, D01–06, differential outcomes, Table3, SpotIt scope|169 attempts retained, strict/raw distinction, full cost/failure accounting; no selector-specific benefit；无明显裁切、碰撞或乱码。|
|9|Historical controls, public Table4, direction diagnostic|No v5 guarantee inherited by v4; all48910 slots; zero public eligible JOIN; construction not defect prevalence；无明显裁切、碰撞或乱码。|
|10|Lineage/evidence, actual AI role, NO_GO conclusion, references begin|Local AI execution disclosed; human confirmation pending; legacy34/1108 not accuracy; no broad originality proof；无明显裁切、碰撞或乱码。|
|11|Remaining references|All six SpotIt authors visible; URLs/DOIs contained, no clipped text; no body content on reference-only page；无明显裁切、碰撞或乱码。|

## 数字对照

只读逐槽复计已写 `V5_FINAL_NUMERIC_RECOUNT.json`，SHA `ce286e7ec5cb9f6d37ebd50925dc5c90af9a39c5b9b1f9174bc0eda300a51285`；51 项断言通过。重新计数已有 final observation，不是重跑实验或重新证明分类规则。

- Cost 168 槽、169 次尝试；strict 127=77 UNSAT+50 SAT，unknown7/domain6/typed24/monitor4。52 个 raw SAT 原 C/SQL replay 通过，但 2 个监测异常不计 strict。
- Differential 168 槽：115 strict、23 unknown、24 typed、6 monitor。SpotIt 28/168 selected，140 未选；21 strict、2 unknown、1 domain、3 typed、1 monitor，实际 AUTO_SET。
- 六臂表3：strict/unknown/monitor、每臂另1 domain与4 typed、CPU 总和及中位数三位小数均从槽记录核对；不隐去 official 额外中断成本未知。
- 公开 48,910 槽保留6 eligible、47,431 ineligible、189 refused、38 unknown、1,246 errors；24,455对保留2 both-eligible、24,412 definitely-ineligible、41 unresolved。6个eligible全部没有join。
- 162次 baseSAT/XOR 与27/22恢复槽亦核对。历史v4/固定点保持单独身份；不继承v5、不能池化成重复试验。

## 机制图 P1 的闭环

原唯一图只有通用路由，不满足 [figure-design SKILL.md](/Users/loctek/.codex/skills/toppaperos-paper-figure-design/SKILL.md) 对“central operational method”视觉载体的要求。作者在新版本 p6 补成同一 root=3、C=(2,3) 的实际计数对象，经 product 与 selector 两条并列路径回到同一 scalar。逐标签核过：w=6、v=18、贡献计数n=6；selector的value 3→6→18、count 1→2→6；z=(n=0)=false。

caption 明确 R(f)=true、非NULL、C是实际TRUE叶位置之和、N=(2,3)仅示例而非已执行双叶各2行配置、NULL/零贡献规则，以及无实测成本或速度主张。六条连接均有真实目标、可见箭头杆/头和留白。p6最终100dpi灰度可直接追踪两条替代路径，图不再独占空白页。P1-communication 已关闭；不增加实验、新颖性或性能证据。

原生未缩放 small 字体 nominal9pt；11种字体均为嵌入Type1，无Type3。官方DKE字号下限未在本轮核验，不把目视可读等同官方格式合规。两个已实际查看的同领域灰度示例是VeriEQL p3与SQLSolver p7，不作DKE格式权威。表2–4完整且易对照，不需为了装饰另加性能图。

## 自动门限制与真实披露

当前 v3review 的 canonical surface audit 实际 exit1：`pdftotext -bbox-layout` SIGABRT。原 traceback 与 `surface_partial_final_v3review.json` 保留；后者仅报告 Type3=0、suspect glyph=0、overfull=0、undefined=0、missing=0。自动 spacing 仍 UNAVAILABLE。全页 AI 目视未见相应缺陷，是独立替代证据，不冒充自动检查成功。

源码TikZ heuristic的blocking记录保留；当前skill偏好editable/vector文字线条图，没有普遍禁止native TikZ。对其采用实际页面/语义审查，而非删除告警。BibTeX保留Cosette缺pages警告，未编造页码；最终LaTeX log无overfull/underfull/undefined/missing。

最终实际11页，正文在p10结束，参考文献p10–11；p11没有正文。p1原“ten-page working target”是明确的规划目标，不是实报页数或官方期刊限制。现行DKE页数/AI/匿名等政策未在本轮新核。

p10已如实披露AI代码、数学起草、本地实验执行与编排、证据分析和稿件准备；独立AI审阅不是真人review。作者核实/单位/贡献/资助/冲突仍待真实确认，不能套用仅语言润色且作者已核实的虚假模板。

## 书目误报撤回

我曾报告旧520d PDF漏Narodytska，现明确撤回，这是我的视觉误读。旧/新v1/v2 bbl均为`88036d6083373ce8a5d5ad1e0e2db0d148a905bb3d91e3087a8646232474c664`、已有6名作者；作者直接提取文本均为`9b05d7a940396b5b59f11028815c1bfeac852017bddafb8f2688e4afebb89c97`，10页PNG同一身份已独立核过。最终p11再实际查看6名作者齐全。不能把此项写成“修复了漏作者”。Root的primary arXiv核查支持He在Klopfenstein前；旧本地inventory不是权威。

## 科学 NO_GO 与剩余作者依赖

已知factorization/有限分支不是新贡献；自然公开join覆盖仍为零；selector特有收益与稳定性未建立；有限暴露控制不能代替泛化；query frontend与共享oracle仍有条件，IC bridge只覆盖窄AST。正文诚实保留这些边界，不因图文改善升格为可投稿。

最小作者依赖是核实真实技术/贡献/单位/资助/冲突与现行venue披露，并解决可发表的新颖性和有用工作负载。不得靠隐藏负结果解决。没有推断上传、push或正式提交授权。

本轮只写自己的3份science_review产物，报告落盘后停止写入。`BACKUP_BLOCKED_BY_USER_NO_UPLOAD_NO_PUSH`。
