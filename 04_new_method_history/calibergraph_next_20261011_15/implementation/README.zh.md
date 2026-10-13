# 第15阶段最小禁用适配

状态：**DISABLED / DRAFT，未执行、未import科学代码、未compile或py_compile，未做能力测试。** 这里只对六份作者自有源码做文本修改、AST语法/静态结构、JSON和hash检查。运行前仍须root登记/启用/冻结与独立审查。旧06、13字节不改，第13轮一次失败不可重试。

六源从第06轮复制；`official_contract_admission.py`、`safe_sqlite_replay.py`逐字节不变。其他变化仅为15版ID/路径、24槽登记与重复身份、默认禁用开关和两处纯计时。逐源diff见 `round06_to_round15.diff`，源身份和静态核对见 `AUTHOR_DISABLED_MANIFEST.json`、`STATIC_VALIDATION.json`。后端仍用原官方Environment/SQL/schema/full operational C、同一C-model sanity模型和同一SQLite准入profile；无新增fixed-witness comparator、baseline或科学机制。

登记草案：[generation_replay.draft.json](../protocols/generation_replay.draft.json)。rep1按 `[6,9,14,3] × [2,3,4]`；rep2按 `[3,14,9,6] × [4,3,2]`，顺序为先来源后bound。ID含`_rep1/_rep2`且每槽`repeat_id`必须是严格int；common allowlist与supervisor预置24槽一致。来源顺序集合、旧21registry与runtime lock哈希不变。来源在看到第06轮结果后确定，明确为adaptive development diagnostic，非结果盲法或新测试。恰N活行/原表不等于最多N。

保留06全部限额：单worker、每槽一次Environment、nice≥15、RLIMIT_CPU3秒、wall4秒、256MiB采样RSS、C check100ms/query check700ms、Z3内部memory128MB/threads1、累计solver wall2秒与supervisor1.5秒触发、load1≤4/free≥25%、批次SELF+CHILDREN总账60秒（含准备10秒与尾部0.2秒预留）。50/56秒门及失败停止逻辑不改。两次预定重复是不同slot，不是失败retry；不为凑满24槽扩预算。资源/监控/完整性失败时其余NOT_RUN全部保留，普通query UNKNOWN保留并按旧策略继续。

新增 `source_and_structure_admission_cost` 覆盖source/provenance/hash/结构准入及其内部持久化，从STAGE_START写完后到STAGE_END写出前；不包括更早的解释器、registry startup、依赖import或边界日志开销，整体wait4/SELF+CHILDREN兜底。它以try/finally对普通异常落耗时；尚未进入为null；hard signal/kill可能让phase截尾，不能把null或缺收据改为0。未增加budget.check或改变源/结构准入逻辑。

comparison计时仍从SolverTap建立时开始，到真正query-check入口停止；若比较器在query-check前返回或抛异常，finally补时间，状态分别为RETURNED_WITHOUT_QUERY_CHECK/RAISED_BEFORE_QUERY_CHECK。真正check入口标REACHED_QUERY_CHECK；从未到达为null/NOT_REACHED；hard终止留下STARTED时为censored，不是精确elapsed。没有新增query check或solver操作。常规parse含于analyze，inner replay含于outer control/replay；不得双加。phase不能精确相加充当完整成本，日志/启动/尾部仍由整体账覆盖。

旧analyzer未复制，它硬断言历史12槽和历史结果，不适用于24槽及失败批次。后续只读聚合必须以本新slot表出发，不对预测SAT/UNSAT分布作断言；逐槽独立列fullC、querycheck、原SQL replay、异常、unknown/censored/not_run以及全部成本。C sanity永不当query-SAT witness；业务C真实及完备性仍UNKNOWN。

`flock`仍仅为单worker批次互斥。root已同意外层在唯一正式launch前exclusive创建永久once-lock，能力probe另有独立名称/次数；runner不新增daemon/恢复工程。`maximum_batch_attempts=1`必须登记；root不得通过新输出目录绕过已消耗的尝试。审批拒绝记NOT_LAUNCHED，执行syscall失败记NOTCOMPLETED，二者分开。若缺可靠收据，保留全部计划分母、actual status UNKNOWN；不能从初始NOT_RUN快照推断零科学操作。

外层正式执行必须只使用受支持、具体受审的执行请求，保留nice/caps，不改安全设置；完整time/exit收据覆盖解释器启动和退出。当前文件不是可执行审批，不含fresh preflight、能力证明或运行冻结；source gate=False且draft status拒绝科学执行。若获审，只允许root按独审约定变更开关、登记状态/时间并生成包含全部six source、protocol、interpreter、输入、runtime lock及依赖的冻结manifest。对phase补丁的审核不等于runtime测试通过。

私有备份/DataHub及最终freeze由root统一完成；本作者未git/push、访问企业/云数据或凭据。
