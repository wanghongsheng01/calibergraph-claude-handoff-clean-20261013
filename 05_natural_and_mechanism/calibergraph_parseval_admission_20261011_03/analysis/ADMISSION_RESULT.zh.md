# ParSEval 原查询准入诊断：未完成生成

本轮在此前已暴露的 GitLab #47 开发案例上实际启动两次隔离工程探针。确认原版 ParSEval 对原 AFTER SQL 中的 PostgreSQL BOOLEAN 上下文字符串 `'f'` 发生 ValueError。作者探针随后在读取 PostgreSQL 元数据时失败，尚未创建业务表、执行布尔适配器、调用生成器或重放两条原 SQL。因此非空生成目标仍未验证，不能将本次工程失败归为 ParSEval 生成失败，更没有新机制收益证据。

## 已观测事实

- 官方 ParSEval commit `88cfe245bcf249a5b0df561a6b09c116ff2a2896`，SQLGlot 23.12.1，Z3 4.16.0.0；来源、依赖锁和实际文件校验保存在 governance。
- 两条原 SQL 哈希保持绑定；AFTER 为唯一生成引导查询，BEFORE 仅计划独立后端重放，不声称 ParSEval 支持 BEFORE。
- V2 实际构造并审核 Catalog：117 列，32 NOT NULL、3 PRIMARY KEY、6 UNIQUE、2 FOREIGN KEY，共 43 个 active 约束。UNIQUE 使用 NULLS DISTINCT，其中 4 个键含 nullable 列。此事实不等于 PostgreSQL 实测完整 C 已通过。
- V1 在作者 RLIMIT_DATA 平台设置处退出，尚未导入目标软件。V2 原版 lowering 调用 1 次，确认 BOOLEAN 字符串转换缺口；随后第一条后端元数据 SQL 用 `current_setting('lc_collate')` 失败。失败发生在 DDL 之前，不能称建表失败。
- V1+V2 合计 generation=0、solver.check=0、candidate=0、original-query replay=0、confirmation replay=0。V2 driver execute=1，布尔/约束校准数=0。worker exit code 0 来自顶层异常记录机制，不代表探针成功；RESULT.status=PROBE_ERROR。
- V2 launcher 墙钟 3.318238 秒，worker CPU 0.539599 秒，worker peak RSS 87,277,568 bytes。V1 launcher 墙钟约 0.961402 秒。内存采样只覆盖 worker；没有整组 PostgreSQL RSS 测量，不宣称硬 RSS 限额或 unrelated_project 性能零影响。
- V2 开始时 loadavg 5.0835/3.7935/3.3135、memory free 31%，通过预先冻结的资源门；结束时 1m loadavg 6.9185，未追加运行。两次 owned PostgreSQL 均有 stop exit 0、receipt STOPPED 与服务关闭日志。

## 归因与下一最小事实

`'f'` 适配器属于普通 PostgreSQL 语义接入，不能命名为创新。作者元数据读取的最小候选修复是从 `pg_catalog.pg_database` 的 `datcollate` / `datctype` 读取当前数据库属性，而不是把数据库属性当成 current_setting 参数；本轮未执行该候选。应同时对新数据库的 C/UTF8/UTC 实际值做断言，并核 nullable UNIQUE 的 `pg_index.indnullsnotdistinct` 等校准缺口。不能用吞掉缺失元数据的 NULL fallback 代替校验。

当前已消耗冻结的两次工程启动上限，未启动第三次。之后若重新冻结一轮有限接入，目标仍是原 AFTER 的合法非空实例，以及在独立 PostgreSQL 数据库上重放两条未改写原 SQL。GitLab #47 没有已知可满足 NEQ 目标，结果相同不构成生成失败。已有 fresh-key / FK propagation 是 ParSEval 先例，不作为新机制。独立新 test 数仍为 0，科学状态继续 NO_GO_NEW_MECHANISM_CLAIM。

## 审核与交付状态

独立审查者已读取 V2 结果、receipt、两个 traceback、启动/关闭日志和 once-only locks，支持以上失败阶段及零生成边界。本地 exec transport 曾暂时断连，现已恢复；主代理确认 V2 postmaster.pid 与临时 socket 目录均已不存在。独立 post-run hash 与 PID/socket 核验结果以 `calibergraph_parseval_admission_review_20261011_03/RESULT_REVIEW.json` 为准。此前消息审核不替代该终态文件。

断连期间已向获准私有仓库保存恢复检查点，commit `14d7b006e124b7e4043551d8c040b202c763a5e8`、blob `b0cdf5b5bf0845c8fa5e883c63fa269ddc4dd962`，远端读取与提交文本完全相同。该检查点保留当时阻塞状态；连接恢复后的完整作者文件备份需另以最终 completion receipt 确认。第三方原 SQL/schema/source、wheels、运行时和可能回显 SQL 的原始日志不得导出。DataHub 通用 SQL 研究来源模块仍无匹配登记，保持 DATAHUB_REGISTRATION_BLOCKED；未更改其他项目。

主要证据：`runs/admission_01/LAUNCH_RECEIPT.json`、`runs/admission_02/RESULT.json`、`runs/admission_02/LAUNCH_RECEIPT.json`、`governance/PRE_EXEC_FREEZE_v2.json`。本报告不授予新执行授权，也不覆盖旧冻结文件。
