# 数据注册范围归因追加勘误

本文件仅更正备份限制的归因，不改变来源预选、注册数据或科学状态。原冻结文件保持原样，SHA 记录在同名 JSON 勘误中。

此前 `registry_manifest.json`、`registry_README.zh.md` 末段及登记脚本中的备份措辞，把 no-upload 归因为本轮用户明确指令，表述不准确。本轮新指令要求写入新目录、保留旧冻结材料和不读取凭据等，**未单独复述 no-upload**。先前旧材料确有 no-upload 限制，但不能称为本轮新用户原话。本子任务另受父代理下达的 only-new-root 写入与 no-network 边界约束。

正确状态为 **`BACKUP_NOT_ATTEMPTED_LOCAL_ONLY`**：本次本地注册工作未尝试备份或上传。不得再把这里的状态解读为新用户明确禁止上传，也不得据此声称存在备份尝试失败。

DataHub 外部注册仍未执行：其 canonical registry 在本子任务允许的新根写入范围之外，因此保持 `DATAHUB_REGISTRATION_BLOCKED`。

本勘误为追加记录，不回写或静默修改原冻结 registry、数据及登记脚本；后续阅读应将本勘误与原文件一起使用。科学状态仍为 `HOLD_NO_AUTOMATIC_PROMOTION`。
