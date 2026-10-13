# 公共可用性最终截面

结论：完整 LeetCode 47,988 查询槽无一被 v3 或 v4 接纳。合并 Calcite / literature 后，48,910 槽仍只有原来的 6 个阳性（2 对双侧阳性），全部是单表、leaf = 0；真正 JOIN 覆盖为 0。不能据此主张外部 JOIN 泛化、因子化收益或稳定强基线增益。

| 数据 / 阶段 | 原始对数 | 查询槽 | ELIGIBLE | INELIGIBLE | FRONTEND_UNSUPPORTED | 原 parse/AST 错误 | UNKNOWN | NOT_RUN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LeetCode v3 | 23,994 | 47,988 | 0 | 46,758 | 1 | 1,229 | 0 | 0 |
| 开发集 v3 | 461 | 922 | 6 | 711 | 188 | 17 | 0 | 0 |
| 合并 v3 | 24,455 | 48,910 | 6 | 47,469 | 189 | 1,246 | 0 | 0 |
| 合并 cached-AST v4 | 24,455 | 48,910 | 6 | 47,431 | 189 | 1,246 | 38 | 0 |

LeetCode 有 56 个原始 `file` 问题标签、24,050 条 distinct 原始 SQL、23,994 个 distinct 有序 SQL 对；重复 SQL 槽超额 23,938、问题标签上的重复对超额 23,938。分母始终保留全部 23,994 对 / 47,988 槽，未按 distinct 数缩减。合并数据有 516 个来源标签和 24,908 条原始 SQL；6 阳性仅对应 4 条 distinct SQL、5 个完整上下文和 4 个来源标签。来源标签不是经真人验证的独立语义问题。

38 个 UNKNOWN 全来自 Calcite 的 35 对；缓存中每槽含一个序列化 `utils.ValuesTable` 节点。v3 原状态均为 INELIGIBLE（原因为 subquery_or_non_inner_join 30、extra_select_clause 5、unsupported_identifier 3），v4 不重建特殊对象而保守标 UNKNOWN。所有原状态、AST 和原因仍保留。没有新增阳性，没有把解析失败修成可答样本。

选定缓存为 chunk 9 和 16 的 attempt_002，其余 22 块 attempt_001。24 个选定 worker 都 exit 0，完整分母已处理；它们与 v4 所用缓存 SHA 一致。两次资源中止保留如下：

| 块 | 首次停止 | 首次已完成 | 首次未完成 | 原 completed 不重跑 | 续跑新增结果 | 最终 worker exit |
|---|---|---:|---:|---:|---:|---:|
| 9 | CPU_SOFT_43_SECONDS_RESERVE_FOR_FINAL_REPORT | 1973 | 27 | 1973 | 27 | 0 |
| 16 | CPU_SOFT_43_SECONDS_RESERVE_FOR_FINAL_REPORT | 1978 | 22 | 1978 | 22 | 0 |

两次首次 worker 均 exit 2；此前 completed 查询记录与续跑结果逐条哈希一致。chunk 9 的原末尾状态为 1 个 ATTEMPTED_EFFECT_UNKNOWN + 26 个 NOT_RUN，chunk 16 为 1 + 21，均由原槽续跑补完。原 parse/AST 错误没有被删去：LeetCode 1,229 槽，加开发集 17 槽，共 1,246 槽。JSON 附有每项原错误原文、定位及原始报告 / 查询记录哈希，也保留全部选中 supervisor、停止与续跑事件摘要。

`GLOBAL_PROGRESS.json` 顶层仍叫 PARTIAL_EXTERNAL_APPLICABILITY_SCAN，不能把旧聚合标签当最终完成依据；这里按 24 个选中报告逐条重算。队列 job 的 exit_code 是 supervisor 进程码，两次停止时为 0，但 supervisor 内记录的计算 worker exit 为 2；本报告保留这一区别。

v4 supervisor 为 COMPLETE / worker exit 0，总墙钟 7.353851 秒，父子合计采样峰值 RSS 198,934,528 字节。这些仅是资源护栏证据，不是与基线的性能比较；它复用固定官方 ALL AST，只运行原始标识符检查及 v4 recognizer，没有新解析、约束断言或求解。

本汇总只执行标准库读取、哈希和计数；122,504 项身份 / 槽位 / 输出核对，失败 0 项。完整输入与输出 SHA 见 [PUBLIC_APPLICABILITY_FINAL_CUT.json](PUBLIC_APPLICABILITY_FINAL_CUT.json)。冻结 kernel SHA：`17f652323839f0395e3224e5d82f646c143f34ff8245fb4d798724d3d7b9fa78`。
