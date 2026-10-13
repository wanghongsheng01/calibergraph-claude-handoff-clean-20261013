# Z3 自有句柄保护：已执行的工程验证

状态：`EXECUTED_LIFECYCLE_WITH_LIMITS`；科学启动门槛 `BLOCKED_EXTERNAL_Z3_RSS_COVERAGE`。本轮确实创建了轻量受控子进程并完成超时、清理和资源停止验证，也启动了真实 Z3 的元数据/空闲进程；没有停留在静态设计。外部 Z3 RSS 的既定采样覆盖仍未达到，因此固定 #750/#319 × UA/precise 四槽均为 NOT_RUN，SQL/编码/check-sat/科学求解调用为 0，阶段耗时为空。本结论不是方法失败或研究终点。

## 实现与实际执行

`owned_processes.py` 的 `OwnedCase` 是可执行保护组件。它只存储本程序成功创建的 Popen 对象；每次追加，不覆盖前一个句柄。正常退出、异常、整例截止和自身内存停止均逐个 TERM、必要时 KILL、wait 回收，并关闭管道。Popen.poll/wait 仅处理自己创建的子进程退出状态，不查询其内存或枚举系统进程。没有基于裸 PID 搜索或清理其他任务。

工作截止从上下文进入计算，用单次 SIGALRM 和自身采样线程触发停止；登记阶段屏蔽 SIGALRM，watchdog 继承屏蔽，只向本程序自身发唤醒信号。进入或退出失败也恢复原 timer/handler/mask；每个上下文只能使用一次。适用合同是 macOS、主线程、进入前无其他 Python 线程，生命周期不得引入额外线程，子程序不得派生未登记后代。代码在进入/spawn 检查已知线程，但不是拦截一切第三方线程创建的沙箱。

这是**工作截止加清理宽限**，不是声称总返回时间严格等于预算。TERM 宽限最多 0.15 秒，后续 KILL/wait 每个句柄最多等待 1 秒；Python 信号处理不能承诺中断所有长期 C/GIL 调用、内核不可中断操作或 Popen 设置阶段。watchdog 也受解释器调度影响。突然 SIGKILL/宿主崩溃后的子进程回收未被此进程内组件保证；本轮没有因此宣称完整生产运行器已验收。

作者常规验证实际运行三轮，每轮 7 项、7 个轻量受控子进程。第一轮常规测试通过后独审另找出四个缺陷；修复之后重跑为 `validation_run_02/`、`validation_run_03/`，保留全部旧证据，未把失败历史删去。最后一轮 7/7 通过，累计各场景约 1.003 秒，覆盖：

- 正常完成并 wait；阻塞读取超时后对忽略 TERM 的子进程升级 KILL。
- 异常时保留并清理两个自有句柄，而非仅最后一个。
- EOF/unknown 的控制协议替身返回非成功，不转成 EQU。
- 在 Python 自身分配固定 40 MiB，触发测试专用 48 MiB SELF 高水位采样阈值并回收正在等待的子进程。
- 科学入口在 Popen 前因 Z3 RSS 未覆盖而拒绝，零科学子进程。

48 MiB 是低负担工程夹具阈值，不是新的科学阈值；实际科学合同保持 1 GiB。SELF 采样使用已允许的 `getrusage(RUSAGE_SELF).ru_maxrss`（macOS 字节），反映本 Python 进程峰值，**不包含 Z3**。没有使用 RUSAGE_CHILDREN、ps、proc_pidinfo、task_for_pid、其他 API 或包装命令读取已被拒的进程信息。

## 独审发现与修复

非作者任务首先复现了四项缺陷：登记窗口中 SIGALRM 可导致已创建句柄未登记；KILL/第二次 wait 异常中断后续清理；关闭流异常跳过 handler 恢复；极短截止使 __enter__ 失败但不回滚。初次证据保留于 `review_run_01/INDEPENDENT_CHECKS.json`，其中登记竞态产生的临时未登记子进程由审核立即紧急 kill/wait 回收。

修复为：单线程进入并让 watchdog 继承 SIGALRM 屏蔽；主线程登记；逐句柄嵌套异常聚合、继续清理；关闭流失败也聚合；进入/退出的无条件信号恢复。独审对四项缺陷复测全部通过（`INDEPENDENT_RECHECK.json`），又独立验证阻塞读取下的多句柄清理、自身内存自动停止和科学门槛（`INDEPENDENT_LIFECYCLE.json`）。人为注入 kill 失败时只报告 cleanup unconfirmed，不虚称已回收；审核自行恢复真实 kill 并收尾。

## 真实 Z3 探测与内存覆盖判断

已有 Z3 二进制 SHA-256 为 `edae32f9e37ea4b5bb35310d72f0e352d0dc07626cac4e9e30bc1ea9a5bc8efb`。第一次 -version 启动产生 PermissionError 13；随后只读 stat 证实原冻结文件是普通 Mach-O arm64、模式 0644，缺少执行位。只在新 `native_local/` 复制同字节并设 0755，原文件字节/权限不改，也不改安全设置/提权。该操作修正副本文件模式，不是绕过沙箱获取受限进程信息。失败记录保留于 `native_metadata_run_01/START_FAILURE.json`。

隔离副本真实执行结果：

| 探测 | 结果 | 覆盖范围 |
|---|---|---|
| `-version` | 4.16.0，退出 0 | 二进制可启动 |
| `-h`、`-pp:memory_max_size` | 退出 0，支持原生内存参数 | 参数帮助，不是 RSS 实测 |
| `-memory:1 -T:1 -in`，仅输入 `(exit)` | 退出 0 | 接受参数和启动；没有触发内存上限，不证明限制有效性 |
| `-memory:64 -T:1 -in`，零输入保留 stdin | 0.3 秒工作截止，实测返回约 0.306 秒，退出 -15，wait 确认回收 | 真实 Z3 的阻塞管道/截止/清理，未求解 |

共 5 个真实 Z3 进程均已 wait 回收；没有 check-sat，未用高内存求解来试限制。测试专用 1/64 MiB 不作为未来四槽的擅自新预算。

Z3 4.16 [命令行实现](https://raw.githubusercontent.com/Z3Prover/z3/z3-4.16.0/src/shell/main.cpp)把 `-memory` 转为 `memory_max_size`；[参数实现](https://raw.githubusercontent.com/Z3Prover/z3/z3-4.16.0/src/util/env_params.cpp)将其交给内部内存管理器。虽然帮助使用“hard upper limit”等词，[分配器实现](https://raw.githubusercontent.com/Z3Prover/z3/z3-4.16.0/src/util/memory_manager.cpp)比较的是经其分配路径维护的计数，并存在按阈值同步的线程本地计数。它不等价于 OS 对该进程全部 RSS 的测量或硬限制，也不能证明所有分配、库映射、栈及其他进程均被计入。源码说明是针对标签版本的静态依据；未重建二进制以证明编译选项相同。

因此，“Python 自身峰值采样 + Z3 内部内存参数”可以提供两个各自有限的保护面，但不能替代原先要求的“Python 加全部存活自有 Z3 的 1 GiB 采样停止”。本轮没有可用且已允许的外部 Z3 RSS 采样证据，不重试被拒的系统查询，不换 API。不运行无该项保护的科学求解，也不新增机器负载门槛或要求升级机器。

## 科学槽和适配边界

`STAGE_RESULTS.json` 固定保留 #750/#319 两例×UA/precise 四槽，共 60 秒预定总预算；全部 NOT_RUN、阶段时间 null，无重试/换例。未占用科学尝试标记。原冻结 SQL/fullC 与旧唯一尝试标记的 9 项哈希核对一致；原稿和 unrelated_project 未修改。

前轮串行适配仍是新建独占单案例上下文、相同入口解释器/hash/RNG 状态下的条件保持；对象别名、异常传播、模块缓存等限制不消失。UA 显式 3 秒与 precise 原 300→3 秒差异仍必须披露，不是官方运行性能复现。前轮 fullC/SQLite 类型表示准入和缺失固定模块也未被本保护组件自动解决。本轮没有导入真实 Polygon，更没有宣称该组件已与完整 Polygon 端到端联合验证。

工程推进是实际完成并验证了句柄清单、工作截止和回收组件，且证明真实 Z3 可在普通沙箱中进行低负担探测；尚缺项被精确收敛到外部 RSS 采样覆盖及未验收的完整集成。独立最终结论见 `INDEPENDENT_REVIEW.zh.md`。研究科学收益没有新证据，不能据本工程工作宣称方法优势。
