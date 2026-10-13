# 第15轮：一手范围核验完成，负载门停止科学执行

结论：**STOP_RESOURCE_GATE / SCIENTIFIC_NOT_LAUNCHED**。H15“2行快判是否仅为小界效应”本轮未获得新实验答案；新机制仍为NONE，科学晋升维持NO_GO。不能把机器负载停止当作H15被证伪，也不能把未运行当负结果。

作者与独审分离，参与模型按用户要求为gpt-6-astra/ultra。本文是作者结果记录，最终独审另存；原稿及旧冻结目录未修改。

## 一手研究范围与可回答的问题

|工作|已核贡献/任务|本任务不能借用的结论|
|---|---|---|
|[VeriEQL v2](https://arxiv.org/html/2403.03193v2)|SQL/IC的有界SMT等价检查和反例；论文涉及NULL、连接、聚合|所查固定代码强制每表恰N活行；不能借论文“至多N”声称覆盖空表、混合基数或无界等价|
|[Polygon](https://arxiv.org/html/2504.06542v1)|组合式欠近似与冲突驱动的反例/多查询消歧；相对有限界的完备性|不能排除其NULL、外连接或IC；论文60秒结果不能与本任务700ms直接比速度，终止子集均值也不是全分母成本|
|[SQLSolver](https://www.cs.yale.edu/homes/piskac/papers/2024SIGMOD.pdf)|以U-expression/LIA*处理无行数界的适用等价证明；代码有Unique/NotNull/Reference|不是“没有约束支持”；NEQ/UNKNOWN不等于有效反例；任意fullC、全部NULL语义兼容尚未核定|
|[Few Rows Tell Them Apart](https://arxiv.org/html/2609.09978v1)|限定查询片段的区分数据库界，涉及指定key/FK条件|值块的两份复制不等于每表两行；未报告实验，不能声称给出本SQL工作负载的速度优势|
|[DKE 2019已发表工作](https://researchportal.tuni.fi/en/publications/detecting-measurement-issues-in-sql-arithmetic-expressions-and-ag/)|Thanisch等的SQL算术/聚合measurement issue检测，出版身份已核|全文仍UNRESOLVED；不得臆断其不支持NULL/关系推理/实验，或称本工作填补其空白|

精确章节、版本、代码提交、各论文分母及未决项见 `../literature/` 两组报告。论文性能均NOTREPRODUCED；各自成功含义与超时预算不同，不合并排行榜。VeriEQL当前README与论文LeetCode分母还存在770差额，原因未核，不能混用版本。

已有材料能支持的结论是：最初公开48910条查询只留下6条、0 JOIN时没有调用solver，首先是前端准入覆盖问题；工程放开后，第06轮已经能对4个有来源的JOIN查询对进行实际有界检查。它不能支持“自然业务缺陷”“新方法优于基线”或总体覆盖率。source自带完整operational C，但业务真实性与完备性仍UNKNOWN。

## 原第06轮全12槽仍保留

|来源|恰2行|恰4行|恰8行|
|---|---|---|---|
|dev03_07|UNSAT|UNSAT|UNSAT|
|dev03_10|UNSAT|UNKNOWN timeout|UNKNOWN out of memory|
|dev03_15|UNSAT|UNKNOWN timeout|UNKNOWN out of memory|
|dev03_04|比较编码异常，未query-check|比较编码异常，未query-check|比较编码异常，未query-check|

全部12次C-check为SAT；9次query-check中5 UNSAT、4 UNKNOWN，另3次在比较编码中NotEquivalenceError退出，不是已验证不等价。无query-SAT反例。两个INT来源的6次C-model sanity重放都满足独立fullC且输出相同；这些只是sanity control。

旧两INT来源在N=2的query-check CPU分别约0.025/0.032秒，而单worker全生命周期CPU约0.930/0.831秒，导入占约0.689/0.585秒；“求解快”不能代替总成本。N=4的query-check各约0.706/0.708秒并超时；N=8又有编码增长与内存UNKNOWN。这给出待重复的工具成本现象，尚不是重复验证的科学瓶颈。旧12槽总实测CPU18.274636秒，含10秒准备及0.2秒尾部预留的保守账28.474636秒；预留不是实测。

两个INT pair还有CASE默认NULL、内连接交换、外连接左右互换、IFNULL/COALESCE等成熟恒等式作为强解析对照。尚未实现计时baseline，不能声称比SQLSolver、规范化或其他成熟工具快。即使今后重复出相同timeout，也须先排除这些已有解释。

## 本轮实际动作和失败分母

H15草案保持原4来源、原SQL/schema/fullC和exact-live语义，预置N=2/3/4的两次冷进程重复，共24槽。第二遍反转顺序；cold不表示冷OS cache。21对开发集及这4个来源均已暴露，没有建立新的独立heldout test。草案没有注册启用，也没有执行。

先做了唯一一次无SQL/SMT/数据/网络的能力检查，使用工具支持的`require_escalated`具体受审请求。实际退出码1，**不是自动审批拒绝**：nice15、CPU限制[1,1]、内存余量35%、本进程ps、fork/wait4均取得，但1分钟load为**4.6015625 > 4**，命中预置资源门。未放宽阈值、未重试probe、未启动科学batch。`EXECUTION_CLOSED_NO_BATCH.lock`永久关闭本轮后续启动；旧第13轮也未重试。

probe样本SELF CPU0.044665秒，加全部reaped children 0.003567秒，共**0.048232秒**；其wait4 child 0.000483秒已经包含于children，不能再加。自身峰值RSS12,943,360字节。样本不含最终收据写入/打印/退出；全准备精确CPU未测，仍计10秒保守预留，不能说整轮只花0.048232秒。

`PLANNED_DENOMINATOR.json`逐一保留24槽，全部`NOT_LAUNCHED_RESOURCE_GATE`；每槽C、query、replay、scientific timing均null。启动数0是外层确定未调用科学supervisor的操作事实，不是24个实测零成本。新24槽不和旧12槽拼作独立样本。第13轮98个计划数据库分母及其失败收据独立保留。

## 未执行实现的审查边界与下一步约束

禁用实现只是最小移植：24槽身份及两处纯计时，无新solver调用。独审指出仍继承“未到达phase用空集合sum得到0”的潜在计时歧义；未来若另立阶段，须依据stage证据转null。flock只管并发，不能代替外层永久once-lock；supervisor早期失败也必须在外层补记准备预留。本轮停后不修改冻结代码，更不以修复为理由再跑。

只可报告静态实现和资源停止经过；不得写成enabled preexec PASS、实验完成、H15否定、方法验证、性能提升或新测试结果。资源可用之后如另行开启新阶段，应明确承接该未回答问题及全部既有暴露数据，先修复计时语义、重新冻结并独审，保持强对照、原fullC和完整失败分母，不自动扩大预算或行数。

新作者/独审材料私有备份由root单独核验记录；历史raw evidence/native runtime干净恢复仍BACKUP_BLOCKED，canonical DataHub注册仍DATAHUB_REGISTRATION_BLOCKED。不能用新一轮文件推送掩盖这些缺口。
