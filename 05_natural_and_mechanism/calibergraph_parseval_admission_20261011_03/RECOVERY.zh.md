# 本轮诊断恢复说明

本轮结果是工程准入未完成：两次启动、零生成、零 SMT check、零原查询重放。`analysis/ADMISSION_RESULT.zh.md` 与 `runs/admission_02/RESULT.json` 解释实际阶段；不能用 worker exit 0 代替 RESULT.status。两次 once-only lock、协议和执行前冻结均保留，不得为重试而删锁。恢复不授予第三次探针运行。

私有备份中的 `parseval_admission_03/` 是本目录的作者文件 exact-copy 导出；`independent_review_parseval_admission_03/` 是分离的审查目录。按 export manifest 校验每个 SHA256。若只恢复作者产物，将本目录恢复为工作区下的 `calibergraph_parseval_admission_20261011_03/`；作者脚本的 WORKSPACE 使用项目父目录。旧依赖项目的名称和文件相对路径见 `implementation/gitlab_schema.py` 的 EXPECTED。不要在备份工作区无差别运行脚本。

为避免重新分发第三方材料，备份排除原 SQL、Ruby schema、上游代码与论文、SQLGlot 源码快照、wheels、解压依赖、PostgreSQL 数据目录、原始日志与 traceback，以及派生完整 DDL 文件。排除文件的哈希与大小写入 manifest；来源 URL/commit/Git blob/SHA256、列约束盘点、作者映射代码、执行配置、收据及失败结果保留。该边界意味着原始输入和原生环境的干净机器恢复仍为 NOT_CERTIFIED，不宣称仅 clone 即可运行。

原案例通过旧项目 `calibergraph_trigger_generation_20261011_01/data/SOURCE_INPUTS.json` / `REPLAY_SCHEMA.json` 的 provenance 与 hash 合法重新取得；两条 SQL 必须与已锁定哈希一致，不能从摘要重写。GitLab/Rails 类型映射来源见 `analysis/FULLC_MAPPING.json`；BOOLEAN 官方来源见 `analysis/BOOLEAN_SOURCE_LOCK.json`。恢复这些原始来源时需按各自明确 URL 和 commit 获取，并验证 Git blob 与本地 SHA256，不能猜测新版本。

官方 ParSEval 唯一源为 `https://codeload.github.com/sfu-db/ParSEval/tar.gz/88cfe245bcf249a5b0df561a6b09c116ff2a2896`；核验 `governance/OFFICIAL_SOURCE_LOCK.json` 的全部 126 个文件。六个 wheel 的精确官方 PyPI URL 与 SHA256 见 `governance/OFFICIAL_DEPENDENCY_LOCK.json`，解压文件哈希见 `DEPENDENCY_ACQUISITION_RECEIPT.json`。作者 `fetch_locked_wheels.py` 实现固定源下载、校验和安全解压，不需要 setup/build 安装钩子；执行下载脚本仍需当前授权和网络权限。不得借用全局 SQLGlot 30.x 代替锁定的 23.12.1，也不得让未知来源依赖混入。

已观测本机环境为 macOS arm64、Python 3.12.13 与 PostgreSQL 16.14 Homebrew。本轮没有安装或改写全局运行时。新 PG 采用 C/UTF8/UTC、无 TCP、只允许任务临时 socket；不是 GitLab 历史生产引擎/会话的重现。后续任何新执行需要重新审核环境、fullC 与低资源门，不重用已结束服务器，不读取默认口令文件。

断连恢复检查点 commit `14d7b006e124b7e4043551d8c040b202c763a5e8` 记录的是当时状态，后续终态以 completion receipt 和独审文件为准。完整备份完成条件是 remote main 与 local HEAD 一致、仓库仍 private、每份作者导出 blob 与 manifest 相符；仅有该检查点不能声称全部产物已备份。

DataHub 通用 SQL 研究来源模块尚无匹配登记，保持 DATAHUB_REGISTRATION_BLOCKED；本轮没有授权修改其他项目的注册实现。未修改旧冻结结果、unrelated_project、论文或投稿材料。
