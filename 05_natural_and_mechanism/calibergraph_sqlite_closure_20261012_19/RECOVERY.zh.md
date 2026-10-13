# 本地恢复与保全

本包实验已结束。先读 RESULT.zh.md 和 review_local/FINAL_REVIEW.zh.md。不要删除 STARTED/CLOSED、不要重新执行两个运行控制器、不要修改原冻结基线或把隔离补丁静默并入。作者及独立验证的完整输入、输出、失败与后续补完记录均在本包。

首段 independent_validation.json 顶层 FAILED 是真实历史；其 replays 段 PASS 与补完 count_only_completion.json 的 PASS 分开引用。COUNT_STAR.patch 尚未应用。若之后另行授权端到端验证，应新建目录和预算，保留本包。

FREEZE.json 锁定 369 项，COUNT_COMPLETION_FREEZE.json 锁定 378 项；POST_EXECUTION_PRESERVATION.json 记录两者仍匹配及旧 marker 的事后确定字节校验。DELIVERY_MANIFEST.json 仅用于交付内容完整性，不冒称运行前冻结。

未 commit/push。当前用户明确要求等待批准，不运行自动备份钩子，也不另找路径绕过此前备份审批。
