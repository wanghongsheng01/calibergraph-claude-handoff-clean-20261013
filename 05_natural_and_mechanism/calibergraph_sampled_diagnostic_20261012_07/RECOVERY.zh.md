# 结果恢复与不可重试边界

本包映射为既有私有仓库 `wanghongsheng01/calibergraph-method-research-20261011` 的 `sampled_diagnostic_20261012_07/`。备份自写启动器、采样保护、worker、合成测试与科学运行的真实日志、生成数据库快照、自构造控制数据库及独立审核。MANIFEST.json 校验备份作者文件；FREEZE.json 是运行前外部输入/源代码/依赖及运行器哈希，不要混用。

第三方原始 SQL/DDL、ParSEval 源码与依赖不再分发。恢复它们沿用既有 `distinct_evidence_20261012_03` 与源锁/依赖锁的来源，在指定官方commit和校验和下恢复。FREEZE 绝对路径标识本次原工作区，不授权换源或更换版本。生成数据库快照和SQLite复算结果是本任务运行产出。

**不要运行 supervisor.py science 或 validate 再造证据。** 本次唯一科学尝试已消耗；canonical `calibergraph_launch_protocol_v2_20261012_05/runtime/ATTEMPT_STARTED.json` 必须保留。包内 ATTEMPT_RECEIPT.json 是其作者记录副本，不是可自动重建活动锁的机制。恢复、目录改名、缺少本机锁文件都不授权重新启动。旧批次未改，新科学运行产生的校验错误同样保持原样。

原 science/RESULT.json 的 ERROR_NOT_ALGORITHM_FAILURE 是官方 disprove 返回之后我方独立候选回放的大小写 KeyError；不能删去或重写为无错误。最终论证须同时读取原阶段日志和独立审核复算，不能只看汇总状态或只看 baseline_verdict。

备份恢复不解决历史第三方 raw/native 永久恢复 BACKUP_BLOCKED、公开研究源模块 DATAHUB_REGISTRATION_BLOCKED。未改原稿、其他任务或系统安全配置。
