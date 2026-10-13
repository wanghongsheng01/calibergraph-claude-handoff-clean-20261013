# 第三轮单 worker 批量守卫接口

作者实现方文档；未执行 worker。代码为 code/probe_supervisor.py，固定政策为 protocols/probe_supervisor_policy.json。独立预审与 root 冻结通过后才能启动。

## 调用与冻结

使用 root 冻结的现有 Python 3.12，参数为 -B -I -S，然后调用 supervisor 的 --freeze PATH --protocol PATH --out PROJECT/runs/batch_xx。不接受任意 worker 路径，固定启动 code/official_diagnostic_worker.py，其接口为 --protocol PATH --case-index INT --out CASE_DIR。

新输出目录必须此前不存在，直属本项目 runs，名称以 batch_ 开头。整个批次持有 runs/.single_worker.lock 的非阻塞排他 flock。32 个初始槽位先于任何 worker 落盘；JSONL 真实登记数必须为 1–32，且 id 顺序严格等于 protocol.registered_case_ids。不足 32 的尾槽为 NOT_REGISTERED，不进入 registered denominator。失败、unsupported 与未运行不补样、不替换。

本轮仅授权一个 batch，不重启或补跑；若后续另行授权新批次，必须累计此前批次 CPU 债务，不能重新从零计费。

worker 协议另需以下字段，由 root 填值并冻结；policy 与 Python 路径均使用绝对路径：

    supervisor.python_executable
    supervisor.policy.path
    supervisor.policy.sha256
    supervisor.scan_cost_receipt.path
    supervisor.scan_cost_receipt.sha256
    supervisor.pre_registered_scan_cpu_seconds

scan_cost_receipt 是单对象。扫描收据必须 status=RETURNED；预登记扫描成本必填且非零，至少为该收据的 observed_total_cpu_at_report+0.1 秒。若扫描失败、哈希不符或费用不足，批次不启动。若扫描成本尚未验证，失败收据明确 total 未完整核定，不能把扫描成本默认为零。

freeze.interpreter.resolved 必须与 supervisor 自身的 sys.executable.resolve 相同，且版本为 Python 3.12。freeze.files 至少覆盖：supervisor、worker、official_diagnostic_backend.py、official_contract_admission.py、固定 policy、最终 protocol、输入 JSONL、runtime lock、scan receipt 和实际 Python 二进制。root 还需绑定所有执行期依赖与 runtime；此最小集合不替代完整冻结清单。

## worker 进度协议

worker 在开始导入／执行工作时尽早建立 progress.json，后续通过原子替换更新，不能留下半个 JSON。初始化缺文件宽限为 0.75 秒；每次 solver check 之前及之后必须立即更新。

| 字段 | 语义 |
|---|---|
| active_stage | 始终是字符串；无活动阶段可用 BETWEEN_STAGES |
| solver_check_active | 严格布尔值 |
| solver_check_start_monotonic | 活动时为同机 time.monotonic 时间；非活动时必须 null |
| solver_spent_wall_seconds | 已完成检查实际累计墙钟，不包含当前活动检查；非负、非递减 |
| check_count | 已开始的检查数量，非递减，最大 4 |

可以额外写 latest_stage，但守卫不把它当 solver 是否活动的依据。两个独立环境尝试每次最多一个 C check（100ms）及一个 query check（800ms），累计实际 solver 预算为 2 秒。是否重复及科学分类由已冻结 worker 决定，supervisor 不调度额外重试。

## CPU、墙钟、RSS 与机器门槛

计费为：已核定的扫描 charge + supervisor 的绝对 RUSAGE_SELF CPU + 全部 RUSAGE_CHILDREN CPU。memory_pressure、ps、启动、失败、清理和所有已回收 worker 都包含在其中。监控中的 live worker 组 CPU另由 ps 采样，wait4 回收后进入 CHILDREN，避免重复计费。wait4 另外保存 worker 本身的实际 CPU 和 Darwin 峰值 RSS。

- 新 case 启动前，累计 CPU 必须小于 110 秒，距 120 秒预算至少剩 10 秒；机器探测后再次判断。
- active worker 期间，父进程加已回收子进程及 scan charge 达到 115 秒，立即终止自己拥有的 worker 进程组。冻结验证/输入哈希期间也保留 110 秒开始门槛。
- 每 worker 新建 session/进程组，nice 精确设为 15；RLIMIT_CPU=(4,4)，禁止 core dump；wall 目标上限 5 秒。检测到未登记的 worker 后代进程视为监控异常并停批。
- RSS 组采样阈值 256MiB；同时设置 Darwin RLIMIT_RSS，但其为 advisory，不能冒称精确硬分配上限。记录 wait4 峰值及采样峰值，超界保留 violation。
- 每个 case 启动前读取 os.getloadavg 和 memory_pressure -Q：1 分钟负载≤4，可用比例≥25%才启动。期间负载升高只闩锁停止后续 case；当前 worker 按自身预算收尾，绝不操作 unrelated_project 或其他任务。
- 环境采用固定白名单，线程变量均为 1；不复制用户环境，不读取凭据或 PYTHONPATH。外部探测命令也使用同一无凭据环境。

目标轮询间隔为 50ms，ps 子进程自身也有 50ms 超时。每次在 ps 前后检查 solver 进度；已完成 solver 时长加当前活动时长估计达到 1.9 秒便终止自有组并记 SOLVER_BUDGET_STOP。OS 调度、native call 和清理可能超时：已完成 check 的真实记录超过 2 秒与活动 check 被中断时的估计超过 2 秒分别记录，后者明确为 censored。不得声称实现了精确的 2 秒硬 solver 界。

所有监控、启动和信号异常进入 finally；仅当 worker 尚未回收时向其进程组发 SIGKILL，随后 wait4/wait 回收并写收据。已回收时记录跳过发送信号，避免操作可能复用的进程组编号。由于硬 SIGKILL 或磁盘本身失效时任何用户态程序都可能无法继续，收据存在性仍应由外层独审核验。

## 输出与失败保留

batch_xx/batch_receipt.json 和 batch_events.jsonl 记录完整分母与批次停止原因。每个已尝试 case 的 case_00 等目录包含：

- worker 原样写入 results.json、events.jsonl、progress.json；
- supervisor 独立写 supervisor_receipt.json、supervisor_events.jsonl、stdout.log、stderr.log。

已存在的 worker results.json 不覆盖；其 status 与 record 原样嵌入 supervisor 收据，并记录文件哈希。worker 在写结果前被终止时，只新建明确标为 supervisor 作者、WORKER_DID_NOT_COMPLETE、query_verdict=null 的占位结果。此占位不是 solver 结论。所有未启动的真实槽保留 NOT_RUN 及原因。

批次最终 CPU 在报告点测量，另保守 charge 0.1 秒覆盖序列化／退出尾部；该尾部是预留，不是独立实测。超 120 秒的 charge 或任一 worker 实测 CPU/RSS、生命周期 wall、solver 记录超界必须保留 violation。RETURNED／REGISTERED_SEQUENCE_FINISHED 只表示执行状态，不能充当语义正确、稳定成本、自然缺陷或无界等价结论。
