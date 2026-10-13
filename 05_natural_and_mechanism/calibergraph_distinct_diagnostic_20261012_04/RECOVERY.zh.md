# 本批资源停止记录恢复

本地目录 `calibergraph_distinct_diagnostic_20261012_04` 映射为既有私有仓库目录 `distinct_diagnostic_20261012_04`。本包保存配置、输入及源码哈希、启动前命令的输出记录、NOT_RUN 阶段表、关闭标记和独立审核。没有科学运行器、候选数据库、求解日志或执行过的最小见证；不要为填补空缺而重跑。

先读取 `RESULT.zh.md` 和独立审核，再用 `MANIFEST.json` 校验本包作者文件。`INPUT_FREEZE.json` 中绝对路径是原工作区绑定：原 SQL/DDL 位于前轮 `calibergraph_distinct_evidence_20261012_03/sources_local/`，官方代码位于 `calibergraph_parseval_admission_20261011_03/sources_local/parseval_official/`。在私有仓库中，前轮作者取证包映射为 `distinct_evidence_20261012_03`，其恢复说明提供官方 artifact 和固定源码位置。第三方原始 SQL、DDL、上游代码与依赖不在本包再分发。

本轮仅做输入/源码静态哈希，未验证 runtime 导入或执行兼容性。源码 lock 内不可靠的 `git_tree_sha` 字段未继承为树身份；以固定 commit 与逐文件 Git blob/SHA-256 为准。配置 provider 路径依据实际源码 import，非猜测模块路径。

保留 `CLOSED_NO_SCIENTIFIC_LAUNCH.lock`：本批已在启动前关闭，科学调用数为 0。这里的“零重试”不是一次科学失败；没有科学运行可以复算。克隆文件不解除负载条件、沙箱进程读取限制，亦不授权提权、轮询负载、启动或重试。

本包自身作者文件可私有备份校验。原项目历史 raw/native 恢复和 DataHub 固定公开研究源登记阻塞仍未解决，分别为 `BACKUP_BLOCKED`、`DATAHUB_REGISTRATION_BLOCKED`，与本批是否运行分开报告。未修改其他项目 registry、原稿或 unrelated_project。
