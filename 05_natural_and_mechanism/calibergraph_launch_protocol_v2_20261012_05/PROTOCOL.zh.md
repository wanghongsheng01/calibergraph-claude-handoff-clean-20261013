# v2 启动协议：取消未校准负载门槛，当前不运行

状态为 `HOLD_unrelated_project_AND_MEMORY_ENFORCEMENT`。这是一份待实施的最小启动协议，不是可运行性认证；没有创建科学运行器、调度、轮询或启动任何复现。旧 `calibergraph_distinct_diagnostic_20261012_04` 及其关闭锁保持原样。未来另建运行目录，先由父任务依据 unrelated_project 任务的完成记录确认计算已结束，再重新判断准入；unrelated_project 结束本身不自动触发实验。

## 本次明确修订

移除 `load1≤2` 硬门槛，也不换成另一个未经校准的常数。该门槛是本任务上一轮自行提出的保护策略，不是用户、操作系统或 ParSEval 的要求。历史 `RESOURCE_PRECHECK.json` 曾记录逻辑 CPU=10、16 GiB 内存，但它是旧快照，不能证明此刻空闲。负载不再作为单独否决条件。本轮不采集新负载、内存压力或全系统进程信息。

原来“可用内存≥3 GiB”也只是缺少测量定义的启发式，v2 不把它当作已经满足或作为唯一替代门槛。真正保留的条件是：unrelated_project 已结束、没有本实验未结清的作业、一个科学 worker、60 秒 wall / 60 CPU 秒、1 GiB worker RSS 预算，以及零科学重试。内存强制机制未落实，当前不能准入。

## 不扫描进程的防重复方案

1. 所有本协议入口使用同一个规范绝对路径的控制目录 `task-3/calibergraph_launch_protocol_v2_20261012_05/runtime/`，不得复制协议后换锁路径。正式入口先取非阻塞排他 `flock`；失败即退出，不排队。锁文件不删除、不替换 inode。父进程和唯一 worker 均持有继承的同一锁描述符，直到 worker 终止并被回收。
2. 持锁后以 `O_CREAT|O_EXCL` 创建本次唯一 `ATTEMPT_STARTED.json`，写入协议/输入哈希和随机 run ID，刷新文件及目录。此操作在创建 worker 之前完成。一旦存在，无论日志完整与否均禁止再次创建 worker；崩溃、启动失败和状态不明都不自动清锁、删除记录或重试。
3. 父进程仅创建一个直接子进程，并始终保留该 `Popen` 对象；只通过此对象等待、终止及回收。PID 只作日志，不据旧 PID 发信号。停止其他进程、`killall`、`pkill`、全系统 `ps` 均不在方案内。
4. worker 不派生其他进程；使用进程内 SQLite，不启动 PostgreSQL。记录 `CREATED → LIMITS_READY → SCIENCE_STARTED → EXITED/STOPPED` 和父进程回收状态。线程可用于官方 SQLite 查询超时；“单 worker”不虚称绝对单线程。库的数值线程参数固定为 1，未来还需验证无派生进程路径。

这只能防止**使用本协议的入口**重复启动。它不能证明整台机器没有同名进程；不作这种声明。旧版启动日志如有未确认回收的本实验作业，保持 `OWN_JOB_STATE_UNRESOLVED`，不得通过换目录绕过。持锁、排他创建和子进程句柄在本轮仅作静态设计，尚未运行验证。

## 时间和自身资源保护

父进程从创建 worker 前记录单调时钟；worker 初始化、导入、约束验证、已知见证回放和唯一 `disprove` 都共用一个 60 秒 deadline，不能各获 60 秒。到期只终止自己持有的 worker 并回收，记录实际耗时和停止延迟。操作系统调度会造成延迟，不能宣称真实时间绝不超过 60.000 秒。父进程异常或不能确认回收，永久启动记录继续阻止重启。

worker 在科学库导入前将自己的 `RLIMIT_CPU` soft/hard 都降至 60 秒；失败即退出，不进入科学阶段。它限制该进程的累计 CPU，不能冒称包含父进程开销或未来未知子进程。父进程开销另列。未来实现需核实精确退出信号、deadline 与回收，不在本轮进行探测或消耗 CPU 的测试。

**1 GiB RSS 尚无已验证的强制机制。** 旧 worker 的 `getrusage(RUSAGE_SELF).ru_maxrss` 每 50ms 采样是自身历史峰值遥测；能事后发现超限，但采样间可超冲，监控线程也可能延迟。它不是硬内存限制，降低采样阈值也不能证明不会超过 1 GiB。`RLIMIT_DATA` 只覆盖数据段，不能代替全部 RSS；Z3 自身限额也不包含 Python/SQLite 等内存。不得继承旧采样代码并声称预算已满足。

本地 SDK 把 `RLIMIT_RSS` 定义为 `RLIMIT_AS` 别名。Apple 公开 XNU 源码的 `RLIMIT_AS` 路径限制地址空间，当前占用已高于新限额时可拒绝设置；它不是直接的 RSS 计量。公开 main 并非本机内核版本证据。不能用“setrlimit 返回成功”单独证明 1 GiB RSS 有效，也不能把旧 setter 失败断言成沙箱拒绝。参见 [Apple XNU kern_resource.c](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/kern/kern_resource.c) 的 `case RLIMIT_AS`；其结论仅用于排除未经验证的等同关系。

未来若在现有授权下找到并验证覆盖整个科学 worker 的硬内存上限，可以继续；若没有，则停在 `MEMORY_ENFORCEMENT_UNVERIFIED`。读取全系统进程不是解决该问题的必要条件，开放 `ps` 也不会把采样变成硬限制。若确需额外权限或新执行环境，先报告具体缺项，由父任务另行决定；不自行提权、不绕过限制、不安装工具、不改变预算含义。

## 未来执行顺序与当前交付边界

unrelated_project 完成证据 → 本协议入口和旧本实验作业日志核对 → 内存强制能力及必要的轻量工程验证 → 明确记录可运行决定 → 创建新的唯一尝试 → 导入前自身限制 → 全阶段共享预算 → 回收 → 报告。前三项未完成不创建科学尝试。未来工程验证必须与唯一科学尝试分开记账，禁止以验证名义导入求解器或运行查询。

原 SQL、完整约束、官方版本和科学参数引用旧 `INPUT_FREEZE.json`、`RUN_CONFIG.json`，不修改它们；v2 只覆盖资源准入政策，尚无新的运行配置。任何资源停止都标为 `RESOURCE_STOP/CENSORED`，不算 EQ、算法失败或机制否证。本次交付只有协议与一次独立工程判断，不宣称复现已可执行。
