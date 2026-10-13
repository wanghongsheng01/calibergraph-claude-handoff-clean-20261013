# 恢复边界

`FINAL_RESULT.zh.md` 是终态解释，`analysis/BASELINE_ADMISSION_RECORD.json` 是明确区分原版与适配版的基线记录。`runs/replay_supplement_01/RESULT.json` 保存唯一已重放的 45 行合成 D、完整 typed 两侧输出及新数据库确认。日期/时间以 type/value 对象记录；解码时保留 date 与无时区 datetime，不能把它们混成文本再声称同型。所有 token/password 命名字段中的值均是生成器合成测试值，不是账户凭据。

私有备份 `parseval_admission_04/` 是作者文件精确副本；导出 manifest 记录每份 SHA256，排除 runtime、原始日志/traceback 和派生完整 DDL。作者实现只读继承 `calibergraph_parseval_admission_20261011_03/` 的已锁定代码、类型映射、依赖和来源；恢复时两项目须按这些原名称放入同一工作区父目录。旧 `03/RECOVERY.zh.md` 与该轮官方源/依赖 locks 记录合法来源和校验方法，本轮不重复分发原 SQL/schema、上游仓库、wheels、测试数据或运行时。

原 SQL 必须按旧 SOURCE_INPUTS / REPLAY_SCHEMA 来源链取得并逐字校验，不能由报告摘要改写。worker 使用 `-B -I -S`，新 pycache prefix 避免读取或写入旧目标 bytecode。无凭据、无外部数据库、无 TCP；只使用任务私有 PostgreSQL Unix socket。历史生产环境仍未知；这里只认证已观测 PostgreSQL 16.14 C/UTF8/UTC 下的结果。

保留固定 32 行协议、原越限结果、disabled proposal、单独授权的 64 行补充、两个 freeze 和 once-only locks。恢复不是重跑授权，不能删除 lock 或把原 max1generation/32 行协议改写成成功预算。补充只允许首候选，禁止 SMT；该授权已经消耗。

完整闭环由最终独审及 completion receipt 证明：旧冻结哈希不变，完整分母保留，生成 D/fullC/两侧有序输出一致，私有 Git 远端与本地 HEAD 一致并验证导出 blobs。完整第三方原始输入和原生环境的干净机器恢复仍 NOT_CERTIFIED；clone 仅保证已导出的作者产物与合成结果可恢复。DataHub 通用 SQL 研究来源模块缺口仍为 DATAHUB_REGISTRATION_BLOCKED。
