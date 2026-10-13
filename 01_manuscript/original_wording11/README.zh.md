# CaliberGraph 文案勘误小版本 01

本版本只关闭指定独审提出的三处文案问题。**本轮科学实验已关闭，SCIENCE_NO_GO 保持不变。** 不重跑 solver、SQL、原实验、分类回归或数值实验；科学问题需要新研究，不能靠重复既有实验关闭。

当前阅读入口为 [11页修订 PDF](manuscript/build/main.pdf)，SHA-256 `9abfd1cf57de52287c3ab48df02de46ebe99a7646ba4f2f98dbf7e2d56582516`。它是原 v3review 的文案小版本，不替换、修改或覆盖原冻结包。原包 manifest SHA 仍为 `04c596a825cef9dbe6e1ee66805c5fc21e79cb1ed868914636016df88fc85298`。

## 三处闭合内容

1. [退出码原因追加勘误](errata/EXIT2_CAUSE_ERRATUM.zh.md)：选中14槽中的7个合同 STOP 导致 supervisor exit2；未选10槽不参与退出码聚合。结构化勘误定位原回执 `/interpretation`、审查 JSON `/external_execution_receipt/interpretation`，及冻结包的两份同字节副本。全部旧文件原样保留，未改写历史。
2. `manuscript/results_current.tex` 成本段：表3覆盖168个选定返回槽的完整成本，包括失败和拒绝；官方臂另有一次中断尝试，其完整成本未知，不计入这些总和。每配置一个观察明确指选定的返回观察。表格、数值和已有负结果未变。
3. `manuscript/contract_bridge_v5.tex`：在 “SAT or unknown refuses admission” 前加入 “For the XOR audit”，明确这一拒绝条件仅属于 XOR 审计；base SAT 准入条件保持不变。

逐行差异见 [SOURCE_DIFF.patch](evidence/SOURCE_DIFF.patch)。`main.tex`、参考文献、方法图、实验代码及全部原始结果均未改。

## 本次验证与限制

新目录清洁编译成功，仍为11页；最终 LaTeX 日志的 overfull、underfull、undefined、缺字和 LaTeX warning 均为0。非致命 BibTeX Cosette 缺少 pages 告警保持原状，不补造页码。

全部11页重新生成100 dpi灰度图。与已审 v3review 相比，仅第5、8页像素改变，已由本轮作者代理实际目视；另外9页（包括第6页方法图）逐字节相同。此前完整11页人工方式检查系 AI 目视，并非真人审稿。新指定独审验收另行记录，不能预先声称通过。

标准自动表面脚本在新 PDF 上再次实际 exit1：`pdftotext -bbox-layout` SIGABRT；原始 stderr 与命令回执保留，自动 spacing 状态为 **UNAVAILABLE**，不是自动通过。依据 [surface-audit SKILL.md](/Users/loctek/.codex/skills/toppaperos-submission-surface-audit/SKILL.md) 的 “Run `scripts/audit_pdf_surface.py` on every reviewer-visible PDF and its build log.” 要求，本次已调用且如实保留失败；目视与清洁编译不代替自动门。

指定独审任务：`01a129c2-e014-73d6-b92e-f31fff370009`（核验 CaliberGraph 最终实验）。本版本清单冻结后交其只读验收，仅检查三处勘误、差异、旧包不变及文档版面，不要求重跑科学实验。

新颖性、自然公开 JOIN 适用性和有效比较优势仍未建立；作者技术核验和正式声明仍需真实确认。未访问生产、读取凭据、调用模型API或使用GPU，未上传、push或提交。本版本为本地增量材料，远程备份按禁止上传要求未执行。
