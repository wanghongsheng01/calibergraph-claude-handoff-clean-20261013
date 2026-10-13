# 必须修正项的限定复核

结论：**PASS_AFTER_REQUIRED_CORRECTIONS**。初审 R1–R3 均已修正，当前三份作者文件在这些修正点上一致。本次只核本地修订、差异及哈希，未扩展原审核范围；网络、科学执行、SQL、基线、生成器、求解器和实验调用均为 **0**。

审核人：`/root/masking08_independent_review`。初次 `INDEPENDENT_REVIEW.zh.md/json` 的 **MUST_FIX** 记录未覆盖。`reviewed_initial/` 内三份初稿哈希与初审记录完全一致，当前三份作者文件哈希与 `AUTHOR_REVISIONS.json` 一致。逐文件差异只包含 R1 准入/两臂条件及 R2、R3 引用位置的修订。

| 项目 | 限定核对结果 |
|---|---|
| R1 | `ANALYSIS.zh.md:48` 已限定同一 FROM/INNER JOIN、同一已证非空 key、单一无分组标量 COUNT DISTINCT、仅 WHERE 真值集合包含关系变化，并排除所列后续掩盖算子；不能证明则 unsupported。第 57 行明确两臂共同固定准入与 key 非空性，仅开关所选 key 的严格侧不存在条件。`DECISION.json.proposal_admission` 同步。 |
| R2 | 正文与 `EVIDENCE.json` 均改为 ParSEval 表 2；结构化证据附 PDF 第 5 页、印刷页 4754。 |
| R3 | 正文与 `EVIDENCE.json` 均改为 Polygon §4，独立来源仍保留“尚未取得/准入”状态。 |

当前文件 SHA-256：

- `ANALYSIS.zh.md`：`25569032405ef1a25423494cd906e884424f017e331bb111351d94e4b3df11b4`
- `EVIDENCE.json`：`602cede34915c75b9bff19cf398bb9e4e051bebf05f1fa366e371122d1c5faa1`
- `DECISION.json`：`0b7834b530e7546c7366cf286c0d2d970cb11a9221d3243d78fd1ee45e4593ad`

此 PASS 仅表示已审静态报告在必须修正后通过，不是算法、工程实现、实验或强基线优越性的认证。初审已通过的 A/B 推导和保存证据解释保持原范围；“新机制 NO_GO”保持。Polygon full-C 准入及同预算实测、XData 核心实现和独立自然案例仍未取得，历史 `BACKUP_BLOCKED`、`DATAHUB_REGISTRATION_BLOCKED` 未解除。未来消融预算仍未执行且不含官方强基线。本次只新增复核文件，交父任务统一备份。
