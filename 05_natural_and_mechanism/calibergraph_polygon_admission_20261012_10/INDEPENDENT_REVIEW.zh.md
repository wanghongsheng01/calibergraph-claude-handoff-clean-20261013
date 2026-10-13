# 独立审核：PASS_WITH_LIMITS

本审核已核对最终RESULT中补充的nullable-FK辅助列表边界、AVG精确表示子域与24+2文件计数。

本审核通过本批“资源准入未满足即停止”的结论，**不通过或授予 Polygon 科学运行准入**。资源探针拒绝未独立重演；对其命令、返回码、stderr、未重试/升级以及零科学调用，仅审核保存记录的一致性与相关代码，不冒称独立观察到当时的外部执行历史。审核者未执行 SQL、解析器、研究包导入、求解、资源探针、下载、安装或新科学测试，也未修改原输入、官方代码和唯一尝试标记。

## 核验与结论

1. **停止原因准确。** `RESOURCE_PROBE.json` 记录默认权限下 `/bin/ps -o pid=,rss= -p $$` 返回127及 operation not permitted。记录的 loadavg 不证明无负载、unrelated_project状态或资源门槛通过。该失败是当前保护准入失败，不是 Polygon 算法失败、超时、UNSAT或EQU。旧 `guard.py` 读取 `RUSAGE_SELF.ru_maxrss`；`supervisor.py` 只对直接 child 调用 kill/wait。Polygon `environment.py:274–285` 建立 Manager 和计算 Process，`smtlibv2.py:171–177` 再启动 Z3；没有全后代RSS/父失联全树退出/回收的证明。因此不将旧单worker验证扩展为完整进程树保护是正确边界。Manager与计算Process应理解为同一调用者启动的两条后代支路，不必假定Manager是计算Process的父进程。
2. **超时差异确实存在。** `formula.py:137–142` 的UA读取 `self.timeout`，`solve_precise:490–501` 固定 `-T:300`。设置Environment预算或UA的3秒配置不能证明precise继承同一Z3预算；本批未运行任何一侧，不能以外层截止替代Z3可靠回收。
3. **全C盘点与当前原DDL一致。** #750为10表、31列、8项PK/8键列、8显式非空列、11单列FK；#319为4表、11列、4项PK/5键列、5显式非空列、5单列FK。逐项对照两份DDL与清单，原列顺序、未被查询引用的表、nullable列、#319复合PK及两条atom外键、DEFAULT NULL和CASCADE动作均有保留；拟约束清单没有Female与id=2业务绑定、数值CHECK或强制表非空。它是静态盘点，尚不是可运行适配器或全C端到端验收。
4. **N=1证明边界合理。** #750在条件限定的整数单值片段内，两侧至多聚合同一行，差异由筛选是否仅一侧纳入非NULL值决定；空输入/全NULL聚合为NULL。这里不能把可存储整数、SQLite AVG浮点表示、SMT无界Int和实际解码当作自动等同。原文已明确保留SQLite亲和性、实数/文本存储、值域和具体化未核限制；该条件推导不是全域编码保真证明。#319两份SQL逐字相同，COUNT DISTINCT在至多一条连接记录时为0或1；同一性结论不依赖求解器，但也不验收当前TEXT hash/lookup编码。
5. **冻结和成本记录可核。** 本审核只用stdlib文件读取/JSON/哈希，独立复算 INPUT_FREEZE 的9个输入及标记哈希、2个盘点哈希、SOURCE_ANCHORS的8个哈希，全部一致。Polygon PROVENANCE列出的24个来源内容文件哈希全部一致；连同两个元数据文件是26个快照文件。四个case×mode槽全部为NOT_RUN_RESOURCE_ADMISSION，各科学阶段耗时、峰值RSS与求解结果为null，调用计数为0，未把未测当零成本。哈希证明当前文件与已存冻结值一致，不能独立证明完整历史上绝无短暂修改或执行。

## 必须保留的限制

- 对资源probe的真实外部结果以及“没有重试/科学调用”的历史事件，本审核没有重演或独立审计系统日志，只核对保存记录和代码；不得改写成独立复现成功。
- `encode_foreign_key:229–249` 返回公式确实允许nullable子键，非NULL子键才需活跃父键匹配。但同函数217–223还将子表非空⇒父表非空的辅助项写入 `env.integrity_constraints`。当前已读快照只将函数返回的And(f)并入公式，Environment第537行合入辅助列表的代码被注释；未发现其他使用。此观察局限于该快照，未来适配器不得误合入辅助列表后继续宣称未加强C。
- `map_source_constraints.py` 的盘点在当前两个固定DDL上与人工对照一致；它不是通用SQL语法验证器。表级PRIMARY KEY分支并未完整验证尾部语法，FK动作尾部仅保留字符串，故“fail-closed”只能按本次冻结文本范围理解，不能推广为任意未知DDL均拒绝。
- 快照不完整、全树资源保护、模式一致超时和端到端类型/完整C/解码验收仍未满足。通过本次停止审计不授权重试、升级权限或启动科学工作。

**最终判定：PASS_WITH_LIMITS；无必须修正项。** 上述限制直接写入审核产物；不形成算法性能、胜负、全域等价、硬内存上限或可运行性主张。备份由根任务统一处理，本审核未另建备份。
