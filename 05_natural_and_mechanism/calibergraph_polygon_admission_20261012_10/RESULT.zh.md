# #750/#319 准入实查：资源保护未通过，本批结束

本批已实际完成固定输入核验、两例全C逐项映射盘点、Polygon源码路径核对和一次仅针对自身进程的RSS可用性探测。结论是 **ADMISSION_FAILED_RESOURCE_SCOPE**：不能把已验证的单进程保护宣称为Polygon完整进程树保护，因此依本轮停止条件结束，**没有启动SQL、编码器、求解器或见证回放**。这不是又给出一个运行计划，也不是算法失败/超时/等价结果；4个原定case×mode槽全部保留为NOT_RUN。

## 确切资源缺口

在默认权限、不升级权限下执行 `/bin/ps -o pid=,rss= -p $$`，只请求当前自有shell进程，返回127及 `operation not permitted: /bin/ps`。没有全系统进程枚举，也没有重试或换进程接口绕过拒绝。stdlib记录负载为2.3545/2.5693/2.8921；这不证明unrelated_project状态、空闲资源或任何负载门槛通过。unrelated_project仅采集的状态来自用户，本任务未接触unrelated_project。

此前通过的 `sampled_diagnostic_20261012_07/guard.py` 使用 `getrusage(RUSAGE_SELF)`，其采样只覆盖调用进程；supervisor仅对子对象 `kill()/wait()`。Polygon固定代码 `environment.py:274–285` 实际启动multiprocess Manager及计算Process，后者在 `smtlibv2.py:171` 再Popen外部Z3。子进程不会自动执行我方Guard的采样线程；杀掉父worker也不能据此证明已终止并回收Manager、计算进程和Z3。

所以尚缺：所有自有后代的RSS合计/停止信号、父失联后的全树终止、整组回收与孤儿检查，以及对应轻量验证证据。旧合成测试只证明旧单worker路径，不证明新拓扑。单进程1GiB采样阈值仍允许短暂超冲；本轮连全树采样路径都未准入，不能称已有1GiB全树保护，更不是硬限。没有危险地先启动Z3来测试它是否会超限。

另核实公平超时配置缺口：UA使用 `-T:{self.timeout}`，而 `FormulaManager.solve_precise` 第500行固定 `-T:300`。仅设置Environment.time_budget或self.timeout并不能让precise满足预案的每次3秒solver限制；外部worker截止也不能替代可靠Z3回收。要解决它需独立、留痕的运行配置适配与保护验证，本批没有修改官方实现或用不同预算硬跑。

## 两例完整C已逐项盘点

原SQL、官方实际输入中的空白规范化、完整源DDL与旧唯一尝试标记哈希保持不变。受限文本提取器 `map_source_constraints.py` 仅接受本次两份DDL语法，不导入SQLite、SQL parser或研究包；不认识的字段直接失败。

| 案例 | 全部表/列 | PK声明/列 | 显式NOT NULL列 | 单列FK |
|---|---:|---:|---:|---:|
| #750 superhero | 10 / 31 | 8 / 8 | 8 | 11 |
| #319 toxicology | 4 / 11 | 4 / 5 | 5 | 5 |

所有源列仅声明INTEGER或TEXT。没有删掉未被查询引用的表/列/FK；没有增加`Female↔id=2`等业务规则。#319保留connected的两列复合PK及两条指向atom的FK。原ON DELETE/UPDATE CASCADE及DEFAULT NULL留在原DDL/本地盘点中；它们不改变一个无UPDATE/DELETE的静态完整实例是否合法，但原DDL回放仍须保留这些声明，显式赋全列时也不能通过漏赋值改变默认行为。

拟映射只对应原`primary`、逐列`not_null`、单列FK`eq`入口，未加两侧非空要求，也未把nullable FK变成强制父表非空。固定 `encode_foreign_key:229–249` 对活跃子行允许NULL；非NULL值要求活跃非NULL父键相等。`encode_primary`包含键非空和唯一性；N=1使单表多行唯一性比较退化，但不授权删除源PK。每个源列原顺序保存在本地清单；Polygon按PK/FK/其他列重组时，具体化必须按列名映射回原DDL顺序，不能按位置盲插。

另有必须保留的源码细节：`encode_foreign_key:217–223`向`env.integrity_constraints`辅助列表写入“子表非空⇒父表非空”，这对nullable FK会加强C；当前快照文件中，Environment加入的是函数返回的And(f)，第537行加入该辅助列表的语句被注释，未找到其他消费。不能把辅助列表自动合入拟议适配器。该判断限定为当前已读源码范围，不冒称缺失模块已经审完。

这些是**静态映射清单，不是已执行/已验收适配器**。源类型亲和性、符号值域、字符串解码、行Deleted标志及约束映射的端到端保真还未闭环。完整约束不能靠事后挑出一个碰巧合法的样本就宣称编码已等价，更不能忽略未知C条目。

## N=1解决什么，未解决什么

**#750。** 每表0或1个活跃行，gender连接有源PK，因此gold和predicted各至多包含同一条superhero记录。对同时可由SQLite保存、且可由其AVG浮点结果精确表示的整数非NULL weight，非空AVG在数值上等于该单值，空输入/NULL输入AVG为NULL。故在这个条件片段内，两侧差异只取决于两种筛选是否恰好一侧纳入该非NULL记录；不存在多行均值小数导致的差异。这是N=1下的查询对差异推导，不把AVG输出的SMT整数类型和SQLite浮点表示声称为逐位相同。

但N=1只限行数，不限单元值。Polygon的SMT cell为无界Int、除法为`div`；原SQLite INTEGER亲和性并不等于无界整数域，也不能仅凭列声明排除实数/文本存储。大整数的可存储范围、AVG浮点表示与具体化仍须校验。我们没有偷偷添加数值范围/类型CHECK或修改原SQL来让“精确语义”成立，因而**全域数值保真未通过**。既有#750静态合法反例仍成立，但不能作为seed交给基线或替代实际准入。

**#319。** 两SQL逐字相同；N=1时连接最多一行，COUNT(DISTINCT element)只能0或1，取决于连接、过滤及element非NULL。等价结论来自SQL同一性，不需要求解器。源TEXT键和常量`TR001_3_4`在符号整数与具体字符串间仍要求等值保持、可存储且约束保持的解码；不能将当前hash/lookup实现自动视为全TEXT语义等价。N=1不授权改变字符串字面值、nullable element或复合PK。

两模式共享这些语义/约束入口，precise不是类型/NULL/解码修复器。若未来运行得到有界UNSAT/EQU，也只能谈所声明有限边界与编码范围内未找到见证，不能替代全域等价证明。普通UA/precise差异不构成创新。

## 运行资产与成本记录

现有Polygon固定快照是26个文件（24个来源内容文件和2个来源元数据文件），不是完整可导入源码：它引用的 `polygon/smt/ast.py`、`knowledgebase.py`、`ast/expressions/operator.py`、`errors.py`、`utils.py` 在该快照中不存在。仅说明此已检查快照不完整，不断言整机没有其他安装。PATH上无z3，已有ParSEval依赖目录中有Z3可执行文件；存在文件不等于已验证可用于Polygon。本批未下载源码或安装依赖，因为资源准入已失败且用户要求失败即结束本批。

`STAGE_RESULTS.json` 为 #750/#319 × UA/precise分别保存 `NOT_RUN_RESOURCE_ADMISSION`。各槽的编码、求解、导出、全C回放与总科学耗时为 **null（未测）**，不是伪造的0秒；科学worker/solver/SQL调用计数均0。没有数据胜负、成本优势、超时结果、重试、替换案例或新test。所有原数据/稿件保持原样。

本批关闭后的确切未满足条件是：受现有权限允许、经验证的自有进程树遥测和清理；一致且可记录的solver超时控制；完整固定源码/依赖；以及原类型/完整C与具体化的独立验收。这里记录阻塞，不在本批另起方案或请求提升系统权限。非作者独审另存，作者备份与历史第三方恢复/DataHub登记阻塞分别报告。
