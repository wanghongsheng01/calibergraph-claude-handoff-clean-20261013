# 独立执行与语义审核

结论：固定四槽中的两份 #750 保存见证，均已由独立脚本在原始 SQLite DDL 与原始 SQL 下回放，满足完整源约束并区分查询。#319 两模式的记录仅接纳为 N=1 符号片段内的 bounded UNSAT；不据此宣称该编码覆盖 SQLite 全域语义。

## 独立复算证据

审核代码：`review_local/independent_sqlite_audit.py`；机器结果：`review_local/SQLITE_AUDIT.json`。审核未导入生产回放函数，未启动求解器、未修改见证、未重试科学实验、未读取进程 RSS、未接触 unrelated_project。

SQLite 3.43.2 下，审核从原始 DDL 的 PRAGMA 反向提取表、列、类型、显式 NOT NULL、默认 NULL、主键、外键及级联动作，逐项比对库存和显式 Polygon 约束映射。#750 为 10 表 31 列、27 项映射；#319 为 4 表 11 列、14 项映射。合计 14 表 42 列、41 项映射，均一致。全部 336 项最终冻结文件哈希一致。

| 槽位 | 已保存求解状态 | 独立原 SQL 回放 | 接纳结论 |
|---|---|---|---|
| #750 UA | SAT、SAT | gold = [(NULL,)]；predicted = [(-54.0,)] | 完整约束下已验证反例 |
| #750 precise | SAT | gold = [(-55.0,)]；predicted = [(NULL,)] | 完整约束下已验证反例 |
| #319 UA | SAT、UNSAT、UNSAT | 未保存见证 | bounded symbolic UNSAT |
| #319 precise | UNSAT | 未保存见证 | bounded symbolic UNSAT |

两份 #750 见证均保留全部源表、全部源列，各表恰好一行。审核检查了行宽、重复列、N=1、Python int/str/None 类型及 SQLite 有符号 64 位整数范围，按原值插入，未裁剪、未替换、未补全。原 DDL 执行并强制外键；提交前 foreign_key_check 为空，提交后 integrity_check 为 ok。原 SQL 结果按 bag 比较不同，NULL 和具体整数/文本存储类型均记录在机器结果。

UA 见证 SHA-256：`3a704deb6e4144ba3d32a793d6e2ebb949bfe1e0ad5371f407630ebe48b7971a`。precise 见证 SHA-256：`c5f0e88854890aad85fe483c739f3bac31315a5d4bd50a94230982219f6c0a9b`。

负体重没有被原 DDL 中的 CHECK 排除，因此两份数据库是原约束允许的合成实例。它们不是业务真实数据，也不证明业务另有未提供的约束时仍有相同反例。

## 执行合同与分类边界

运行前检查确认父 broker 直接持有全部 Python worker 与 Z3 的 Popen 句柄，并通过 Unix SCM_RIGHTS 传递 Z3 stdin/stdout；worker 不自行创建原生子进程。四槽固定为 #750/#319 × UA/precise，N=1；每槽新 Python 进程内工作停止预算至多 12 秒，父 OwnedCase 共享 60 秒。Z3 参数固定 `-T:3 -memory:512`。统一回收路径保留全部历史句柄。

`broker_validation_02` 仅为 `z3 -version` 元数据 fixture，记录两个父 owned 句柄均已回收、无清理错误、零科学调用。旧模块的固定 False science gate 未被修改；本轮由 FREEZE 明示用户批准的不同合同授权父 broker 直接 spawn。

512 MiB 是每个 Z3 进程的原生分配限制；Python 仅采样自身高水位 RSS。这不构成所有外部进程 RSS 的完整监测或 aggregate RSS 硬上限。

四份已读结果的 protocol_events 均为空，没有 unknown/timeout/EOF 记录。#319 UA 首次内部 SAT 不是完整查询不等价见证，不能计入最终反例。静态发现上游会将部分编码异常包装为 PIPELINE_ERR；若未来出现该状态，应结合日志区别 unsupported/error，不能直接当作 SAT/UNSAT。本轮无此状态。

文本经上游哈希与解码映射转成保存字符串；这两份具体见证的原 DDL/SQL 回放有效，不等于证明该映射在整个 SQLite 文本域上保持语义。整数无界符号域、SQLite affinity、算术与聚合语义的全球闭合仍未证明。#319 原始 gold 与 predicted 字节内容相同是另一个输入事实，不能用它给通用编码完整性背书。

## 成本审核状态

已独立读取并断言核查 `science_run_01/BATCH_RESULT.json`、四槽 RESULT、全部 stderr、spawn/wait 事件及唯一尝试标记。结果见 `review_local/EXECUTION_AUDIT.json`：总墙钟 2.249685457907617 秒，11 个父 owned 句柄（4 worker + 7 Z3）全部回收，四 worker 退出码为 0，无清理错误。各 Z3 退出码 -15 来自槽完成后的父进程统一 terminate/reap；七次已记录求解调用正常完成，全部 worker/Z3 stderr 为空。

四槽外层墙钟依次为 0.816278、0.587529、0.434618、0.409159 秒。每个 worker 的 12 秒 guard 无停止原因。参数、槽序、最终 FREEZE 摘要与 ATTEMPT_STARTED 标记一致。阶段时间包括嵌套计时：search_including_solver 已含 solver_calls，因此不能直接相加，也不能把这一次固定小样本视为性能基准。

审核中间遇到 exec-server 短暂断连，恢复后原只读请求完成；未因此重跑任何 solver。目前没有阻碍本批结果接纳的剩余执行问题。研究边界仍为上述 typed fragment 语义未全球闭合及非 aggregate RSS 保证。

最终 `RESULT.zh.md` 文案已独立阅读，对本审核覆盖的见证、完整约束、分类、成本及语义边界未发现实质性夸大。受审核文案的 SHA-256 保存在 `INDEPENDENT_REVIEW.json` 的 result_prose_audit 中。

`RECOVERY.zh.md` 已完成静态文案审核，其保留禁止重试、按固定哈希恢复、独立重放不能替换值等边界。两份最终文档摘要记录于 final_document_audits。审核未重新下载归档/依赖、未执行恢复后的 solver，也未核验私有仓库远端备份；恢复说明的静态接纳不等于已经实际完成第三方复现或远端交付验证。
