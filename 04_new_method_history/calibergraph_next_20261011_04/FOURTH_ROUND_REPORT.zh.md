# CaliberGraph 第四轮研究结果（作者报告）

本轮完成一个真实原始查询对的行数边界诊断，**没有建立新方法，也没有建立 SMT 成本瓶颈**。主题保持 `UNCOMMITTED`。这不是停止整体探索；前三轮负结果、已否定机制与旧冻结文件全部保留。未改原稿、未投稿、未接触独立最终测试。

## 已经实际得到的结果

来源是既有开发注册表 `dev03_18`：LeetCode 596.csv，冻结公共 JSONL 第 2924 行。两条原 SQL、schema 和唯一显式 C（STUDENT 主键）按原始字节及 SHA 绑定；没有改 query、补 NOT NULL(CLASS)，也没有把构造实例叫自然数据。

| N | SQLite 全 NULL CLASS 实例 | 同样 N/STUDENT，CLASS 改为非空常量 | 冻结官方引擎 |
|---|---|---|---|
| 1 | 两查询皆空 | 两查询皆空 | C SAT；相关子查询编码拒绝 |
| 2 | 两查询皆空 | 两查询皆空 | C SAT；相关子查询编码拒绝 |
| 3 | 两查询皆空 | 两查询皆空 | C SAT；相关子查询编码拒绝 |
| 4 | 两查询皆空 | 两查询皆空 | C SAT；相关子查询编码拒绝 |
| 5 | Q1 返回一行 NULL；Q2 为空 | 两查询均返回同一班级一行 | C SAT；相关子查询编码拒绝 |

SQLite 五个 worker 各运行两种机制实例和原始两条 SQL，共 20 次原始 query 执行。每种实例在入库前后独立检查完整显式主键 C：STUDENT 非空、互异，没有丢弃其他 C 子句。

官方五个 worker 均返回 `CorrelatedQueryError`，阶段为 `OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE`。原日志的工程类别 `INCONCLUSIVE` 保留；作者重计另派生 `FRONTEND_CORRELATED_SUBQUERY_REJECTION`，没有改写原 verdict。**五次 solver 调用全部是 C 非空检查；query solver 调用为零。** 因而不能写“官方在 N=5 找到反例”，不能从这五个总耗时推断 SMT 随 N 增长的成本。

标准 PK/NULL/bag 语义下的纸面推导更强：非空班级中主键使 COUNT(*) 与 COUNT(DISTINCT STUDENT) 相等；NULL 班级会被普通相关等号过滤。因此这对原 SQL 的实例等价条件恰为 `NULL 班级行数 < 5`。两条原 SQL 的外层均有 GROUP BY，不需要给 Q2 补 DISTINCT。这个推导和上述 SQLite 实测分别记账；业务是否允许 NULL 仍无来源认证，不能把它标成自然业务缺陷。

## 为什么 exact2 与少量来源不足以关闭研究

这里的五行门槛已给出具体反例：在两行上看不到差异，不代表更大库没有差异。另一个只读静态例 `dev03_12` 的 PK/严格 FK 与等基数强制双射；不论统一 exact-b 多大，都覆盖不到没有 BONUS 的 EMPLOYEE。但该原始查询对在完整 C 下通常 SQL 等价，不能用分支缺失冒充自然反例。

冻结官方 `create_database` 本身为每个基表 slot 加存活事实，本轮完整保留，所以运行语义是 exact N，不是论文里的 ≤N。该差异最初被文献分支误归给 adapter，已经明确撤回；没有修删原始事实。本轮也没有把上界、总行数、支持集大小、带重数元组数混称一种 bound。

前三轮十次快速查询检查只覆盖特定准入子集和 exact2。未完成项、类型/前端拒绝和未知业务合同都仍在分母内；它们不能证明所有 SQL 容易。本轮也没有把被前端拦住的实例重分类为求解超时。

## 机制审查与本轮否定

四篇指定主源已按实际范围核对：[VeriEQL](https://arxiv.org/html/2403.03193v2)、[SpotIt+](https://arxiv.org/html/2603.04334v3)、[Polygon](https://arxiv.org/html/2504.06542v1)、[Few Rows Tell Them Apart](https://arxiv.org/html/2609.09978)。Few Rows 的 Boolean-corner 变量取值不是每表两行；其 combined-CQ 结果不能泛化到任意 HAVING SQL。

通用增量 bound、异构形状枚举、PK/FK 基数传播与 proof-driven 剪枝已有有限模型查找及 Polygon 先例；最小充分约束、条件覆盖及证书组合已有 WeTune、abduction、conditional model checking、CoVeriTeam 先例。此处不把现成组合改名后重新申报贡献。

两项进一步收窄的机制审查也没有留下合格新假说：

1. **主键值擦除、按 payload 合并重数，再恢复新鲜互异主键。** 当前窄片段可由主键上的 DISTINCT 消除、普通袋投影和有限集合基数具体化解释。跨表 FK、键比较和重复 join 又需要额外耦合信息；不能凭一张 histogram 宣称一般保真。
2. **从聚合反例投影得到更弱等价合同。** `n_NULL<5` 比 NOT NULL 弱，但该单例是一元基数消元。WeTune 的原词汇不能表达它，不等于 BAPA/量词消去与聚合约束理论不存在。尚未提出超出这些强控制的机制或复杂度改进。

另补查了 XData 的复杂查询工作：[作者 2024 预印本](https://arxiv.org/pdf/2409.18821) 已有带重数结果表、聚合和相关子查询处理。作者主页列出后续 PACMMOD 2025 / SIGMOD 2026 版本；最终版全文本轮未取得，不能把预印本限制直接归给最终版。新的强基线审计必须包含它，不能仅打冻结 VeriEQL 的已知前端短板。

各项精确定位、适用片段、微例和失败判据在 `literature/` 四份审计中。所有文献性能均为论文报告，未冒充本机复现。

## 冻结、资源与启动例外

原十槽协议和 861 项文件绑定在首次启动前冻结。第一次资源门通过（load1=1.9292，可用内存34%），但沙箱拒绝在 preexec 中把子进程降到 nice15；Popen 未执行 worker。保存首次失败槽和九个 NOT_RUN，没有 SQL/parser/solver 输出。不得将“未执行 worker”写成“没有 fork 过子进程”。

独立标准库诊断确认仅自进程 `setpriority` 在沙箱被拒绝，CPU/CORE 限额调用成功；经工具审批，在宿主执行上下文仅降低自身优先级成功。随后登记**首次失败后、首次科学执行前**的显式恢复例外，保存新协议/新 supervisor 副本/新冻结和新批目录；不是原协议事前允许重试。恢复 supervisor 只改变 prior CPU charge，输入、十槽顺序、N、C、SQL和资源不变。没有第三次批运行。

恢复前全部 861 项原绑定再次匹配；恢复冻结共 868 项。累计 CPU 账为：

| 项目 | CPU 秒 |
|---|---:|
| 先前失败批与原预检/收尾保守计费 | 1.408329 |
| 标准库诊断预留 | 1.000000 |
| 新冻结预检预留 | 1.000000 |
| 恢复父进程与所有回收子进程实测 | 5.927557 |
| 恢复收尾预留 | 0.200000 |
| **保守总计 / 原阶段预算** | **9.535886 / 60.000000** |

十个 worker 实测 CPU 合计4.429287秒，监控子进程1.196587秒，父进程0.301683秒。最大单 worker CPU0.923918秒、峰值 RSS110886912字节（约105.75MiB）；十槽前 load1为3.1973–3.2148，可用内存为32–33%。单 worker/nice15/3秒CPU/4秒wall/256MiB外部RSS采样；所有 guard violations 为空。RSS/wall/solver guard 为采样监控，不声称操作系统提供精确硬内存界。未更改 unrelated_project 进程、系统安全、凭据、网络服务或机器配置。

审查旁注：恢复日志 `measurement_note` 延用了“1.0s prior”文字；数值字段和实际计账是3.408329。原 freeze 的静态检查描述误写七个 Python 源文件，实际清单为六个，加入恢复 supervisor 后才为七个。冻结原日志不改，本段明确这两处陈旧/计数提示文字；权威文件清单及计账数值不受影响。

## 后续进入条件

当前允许的结论是“条件化行数边界成立，官方前端拒绝仍是实际阻碍”；不是新方法胜出。当前两个窄机制不推进论文。阶段状态为 `PROBLEM_EVIDENCE_COMPLETED / METHOD_UNCOMMITTED / CONTINUE_EXPLORATION`。

下一轮优先核实 XData 复杂查询正式 artifact 的版本、许可、原始 DDL、查询集合和结果表编码，再选择一个**强前端共同支持、完整合同可认证、真实成本可观测**的片段。当前仅查了官方论文/项目入口，未下载或查看其 benchmark 个例、没有开始新测试。公开作者构造的 mutant benchmark 也必须标为 mutant，不得叫自然缺陷。

若后续形成具体新算法，必须先写明强基线和已知优化组合的最简单控制、证据产生/验证的全部成本、排除合法反例的失败判据及独立确认分割。没有未被已知机制解释的命题，就继续先例/理论研究，不通过放大 COUNT 常数、修前端或挑超时样例制造胜利。

本报告交给未参与作者工作的独立代理审查。审查完成前不声称最终审核通过；备份与 DataHub 注册状态单列在 governance，不能以本地文件存在冒充已完成远端恢复能力。
