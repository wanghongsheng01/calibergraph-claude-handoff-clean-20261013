# 静态机制研究包恢复说明

本包只保存作者分析、来源/版本/哈希和独立审核；没有第三方论文、代码、原始 SQL、JAR、运行环境或科学运行器。原本地目录 `calibergraph_mechanism_synthesis_20261012_02` 在既有私有仓库中映射为 `mechanism_synthesis_20261012_02`。阅读 `MECHANISM_DECISION.zh.md`、`XDATA_EVIDENCE.zh.md` 和独立审核；用 `MANIFEST.json` 校验每个相对路径的 SHA-256 即可恢复和验证本轮作者文件，不运行 SQL 或上游代码。

上游 ParSEval / Polygon / XData / EvoSQL 的固定 commit、官方来源 URL 与已读取范围见 `DECISION.json`、`SOURCE_LEDGER.json` 和 `XDATA_EVIDENCE.json`。Git blob SHA 不是文件 SHA-256，网页文本/本地快照哈希也不自动等于远端原始字节。需要重新审查来源时，只从这些固定公开来源只读取得；不得按 main 的未来内容替代。论文报告的评测数值仍是作者报告，恢复本包不构成复算。

旧证据链接保留本地原目录名。私有仓库对应关系：`calibergraph_scientific_decision_20261012_01` → `scientific_decision_20261012`；`calibergraph_strong_baseline_prep_20261011_02` → `strong_baseline_prep_02`；`calibergraph_parseval_admission_20261011_03` → `parseval_admission_03`；`calibergraph_parseval_admission_20261011_04` → `parseval_admission_04`；`calibergraph_real_task_screen_20261011_05` → `real_task_screen_05`。若文档路径不同，以各包原恢复表为准。旧原始运行日志与完整 native 环境未在此包中再分发；不要为了恢复去重跑旧实验。

本包的作者文件备份可单独验证。旧项目完整历史 raw/native 恢复仍为 `BACKUP_BLOCKED`，本轮静态作者快照成功不解除它。DataHub 通用公开 SQL 研究源仍无匹配模块，canonical registry 位于另一项目且本轮禁止跨项目修改，`DATAHUB_REGISTRATION_BLOCKED` 延续。

没有新实验获准执行，也没有新 natural JOIN 最终测试集。复制/克隆本包不授权启动实验、下载整库 artifact、安装工具或接触 unrelated_project。后续只有在补齐具体失败来源、完整约束、可靠非等价证据和阶段根因后，才由父任务决定是否按 high 做有限准入诊断。
