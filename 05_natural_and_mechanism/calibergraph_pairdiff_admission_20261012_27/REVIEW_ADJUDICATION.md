# 独立审阅后的最终交接

结论：停止当前 paired SPJU bag-difference compilation 候选，不构建窄原型，新增求解预算为 0。独立审阅结论为 `ACCEPT_STOP_WITH_LIMITATIONS`，没有阻止该停止决定的待修项。

预登记 25,528 条自然来源配对，按旧产物/任一侧 SQL 重叠规则排除 10,568 条，14,960 条进入 AST 流程。结构准入 315 条，其中完整 AST 相同 132 条、非平凡 183 条；非平凡条目中有 138 条包含自然 inner JOIN。冻结规则下严格 UNION ALL 分支抵消和 JOIN 零项消去均为 0，合格候选为 0。排除数不代表所有这些配对都曾实际开发过。

此次停止仅针对已声明片段、排除规则与可用来源；不证明所有自然 SQL 工作负载没有机会，也没有测得性能胜负。所有公共来源已有整库静态接触，不是新的独立最终测试。共享 DAG 节点数不是 symbolic table、UA、SMT 或运行时成本；增强共享 DAG 加单输出元组重数判别的强对照尚未实现。

## 接受的审阅限制

1. 扫描器的标识符规范化无条件转小写，没有完整保留引号和源方言语义。因此协议中有关方言及带引号标识符的承诺未完全实现。
2. 比较表达式的 scalar 路径没有完成一般操作数类型与全定义性检查，不能据此认证完整 SQL 编译语义。

因此 315 条准入仅是结构筛查，不能作为语义已认证的编译器数据集。如果未来重新提出实现或语义认证，必须先修复或缩窄这两项契约；当前零候选且范围受限的停止结论无需修改规则或重新扫描。保留原始错误分类：11 条 SCANNER_ERROR 实为 TokenError，仅在派生汇总中解释，没有覆盖原始记录。

## 证据与资源

- 作者结果：`RESULT.zh.md`、`FINAL_DECISION.json`。
- 独立审阅：`review/FINAL_REVIEW.md`、`review/FINAL_REVIEW.json`。
- 全分母与冻结：`ALL_RECORDS.jsonl`、`PROTOCOL.md`、`INPUT_FREEZE.json`、`EXCLUSION_FREEZE.json`、`ADMITTED_ID_FREEZE.json`、`ELIGIBLE_ID_FREEZE.json`。
- Polygon 固定提交路径复核：`POLYGON_PATH_CHECK.md`、`POLYGON_CODE_RECEIPT.json`。
- 扫描 CPU 16.605 秒，墙钟 16.627 秒，峰值 RSS 107,577,344 字节（约 102.6 MiB）；单进程。nice 设置被沙箱拒绝，未声称已降低优先级。
- 本轮新 SQL 执行、SMT 调用、基准运行、原稿修改、推送、上传均为 0。未测量 unrelated_project 吞吐，不能声称绝对无影响。

本文件为审阅后的追加裁定；已冻结作者文件与 REJECTED ledger 证据不变。交付后无需继续求解、扩源或扩展片段。剩余停止决定阻塞：无。
