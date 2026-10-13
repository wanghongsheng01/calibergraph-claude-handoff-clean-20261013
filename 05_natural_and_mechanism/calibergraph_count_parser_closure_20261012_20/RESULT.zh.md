# COUNT(*) 工程闭环：真实 parser 与 SQLite 对照

最终隔离版 **P3 在固定的 28 项 parser 回归、14 项真实投影/分组算子链测试中全部通过**。独立脚本重建 SQLite 数据库，并用另一份纯 Python COUNT 参考核验四版本共 168 条记录，结果 PASS。原基线、历史实验与原稿未改，没有 commit/push。

独立后审结论为 `PASS_WITH_DISCLOSED_PRESERVATION_EXCEPTION`，无必须修复项；记录例外在下文完整披露。

这次确认并修复的是三个工程问题，没有产生方法创新或性能优势证据。#750/#319/#1172/#1261 不受这三个特定分支缺陷影响，原有结论保留；其中有界结果仍然只是有界结果。

## 四版本对照

| 版本 | 修改内容 | 28项 parser→表达式 | 14项 parser→真实算子链 |
|---|---|---|---|
| original | 13包冻结运行基线 | 12通过、4值错、12类型错误 | 7通过、6值错、1类型错误 |
| P1 | 19包普通 COUNT(*) 补丁 | 28通过 | 9通过、5值错 |
| P2 | P1 + 分组 COUNT(*) FILTER | 28通过 | 11通过、3值错 |
| P3 | P2 + FILTER 裸列名解析 | 28通过 | 14通过 |

每版使用相同 SQL、输入数据和 28+14 分母。original 指已有冻结运行基线及共同的测试依赖适配，不冒称全新、无适配的官方安装。四版数据均在 `PARSER_RESULTS_V2.json` 中，失败未筛除，结果不是性能比较。

P1 把 COUNT(*) 的整数指示 append 移出 FILTER 条件：无 FILTER 的非空输入原来计 0；有 FILTER 且多个槽时原来产生 Bool+Bool。P2 在分组路径上加入成员、非NULL、过滤谓词三者的条件，保留已有组；例如两组原计 2、1，FILTER(FALSE) 应输出 0、0，而不是删组。原分组路径已有整数指示，不能把它也称为 Bool 求和问题。

P3 修正三个聚合 FILTER 解析入口：`FILTER (WHERE x)` 的裸列名原来被转成 `Literal('x')`，现在成为 `Attribute('x')`。原版的字符串哈希行为在测试 Env 中如实保留，让错误可见。例如 x=[NULL,7,0] 时，P1/P2 输出 3，SQLite 输出 1；P3 输出 1。限定变更没有改全局 parse_expression 的原始值规则。带引号 literal 的原字典分支保持不变是静态核对结果，本轮未新增对应动态用例。

## 验证范围

28项复用19包 bound=0/1/2、所有删除掩码、无 FILTER / TRUE / FALSE / NULL，但改由真实 `SQLParser.parse → parse_query` 生成 AST，不再人工构造 COUNT 节点。

14项覆盖逻辑空库、NULL行、重复行、COUNT(column)/COUNT(DISTINCT)无FILTER回归、NULL分组键、分组重复、FALSE/NULL FILTER、逐行列值过滤与删除槽。经过真实 `FProject`；分组时还经过真实 `FGroupBy`。具体赋值中的 Choice、Deleted、SMTGrouping 以及输出单元格代入全部生成公式，经严格类型 AST 求值检查，再和 SQLite 原 SQL 的 bag 输出比较。独立脚本重新建库并计算独立 Python 参考；它没有重跑 Polygon 算子编码，算子部分由代码审查和作者运行证据复核。

空库算子链采用一个全部 deleted 的物理槽；物理 bound=0 仅在28项表达式矩阵中测试，未声称零槽完整算子链已验证。这是具体输入下的 parser/COUNT 编码闭环，不是完整 `Environment.check`、QueryEncoder/求解器流水线验证，也不是一般正确性证明。固定分组赋值没有做模型搜索或唯一性证明。

为维持一线程，共同测试适配将依赖 mo_imports 的超时监控 start/join 替换为空操作，真实 import/expect/export 照常执行，导入后未解析 export 为0，共2个监控实例、0个真实监控线程。该适配不是SQL语义修复；P1/P2 parser源码未改，只有P3含明确记录的parser补丁。

其余 grouped COUNT(column)/DISTINCT/SUM/AVG 的 FILTER、SQLite 任意字符串的数值转换等未包含在此次修复保证中。42项均为开发回归，不是新的自然任务或独立最终测试。

## 历史影响独立裁决

| 案例 | 实际路径与原结果 | 本次三个缺陷的影响 |
|---|---|---|
| #750 | AVG→AggSum/Count辅助函数；旧原SQLite合法NEQ反例 | 不触及 COUNT(*) 专用分支；反例保留 |
| #319 | COUNT(DISTINCT)，原SQL两边字节相同；旧有界UNSAT | 不触及；保持既有范围 |
| #1172 | COUNT(DISTINCT)，旧原SQLite输出1/0 | 不触及；合法反例保留 |
| #1261 | COUNT(DISTINCT)，旧 N≤1 有界UNSAT | 不触及；不得升级为无界等价 |

独立审查核对原SQL、冻结代码、14份真实历史SMT与已有SQLite回放。这四例均无 GROUP BY/聚合 FILTER；辅助校验SQL里的 COUNT(*) 在SQLite执行，不经过有缺陷的Polygon编码器。无需因这些缺陷将它们标为待重算，但不因此认证整个baseline无其他问题。旧 Polygon bounded-run 覆盖保持4/8。

## 成本、失败与保全

三个执行段累计 **0.847167750秒**，总预算60秒；各段结束线程数1，求解器调用0，子进程/网络事件0，进程峰值RSS约57.7 MiB。运行前检查机器负载、内存概况并取得公共锁；采用256MiB、50ms虚拟CPU定时采样的RSS停止门，这不是OS硬内存限制。未启动大队列，未使用可选自然查询对求解额度。

001因shell默认Python3.9不支持原代码类型注解而导入失败。002显式Python3.12，但测试解释器误读Implies字段，且缺少string_hash；所有部分成功和错误保留。003只修正测试解释器、补齐原string_hash行为并加入独立P3版本，原数据/SQL未改，成功完成四版及独立核验。旧 `parser_test.py`、`PARSER_RESULTS.json`、各次freeze/收据均保留。

最终003冻结541项全部匹配。早期001/002各有一个**未执行**辅助文件 `review_local/verify_results.py` 的hash变化：冻结时审核者仍在准备脚本，随后在READY前补了INTERRUPTED初始状态。001/002只执行作者脚本，未执行该文件；真正执行的v2核验脚本被003完整冻结。通过去掉唯一新增初始化行可以重建早期hash，此为事后解释，不回改freeze假装从未变更。详见 `PRESERVATION.json`。

## 交付与停止状态

可用隔离代码在 `patched_p3/polygon/`，最小合并差异为 `COUNT_P3.patch`；P1/P2副本与差异保留供比较。主证据为 `PARSER_RESULTS_V2.json`、`review_local/VERIFY_RESULTS_V2.json`、`review_local/IMPACT_REVIEW.zh.md` 及最终独立审核。

科学状态：修复具有真实的计数正确性价值；尚无 CaliberGraph 新机制优于强基线的证据，不重启 anti-masking，不把parser/编码bug当创新。本轮停止于本地工程闭环。按用户要求禁止push且未commit，备份状态 `BACKUP_BLOCKED_USER_NO_PUSH`，等待既有备份批准。
