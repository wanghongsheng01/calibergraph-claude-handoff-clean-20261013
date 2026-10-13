# Polygon 单案例串行适配：工程实现与静态等价边界

本轮交付是可重建的小补丁，状态 `IMPLEMENTED_STATIC_ONLY`。单案例 `Environment.check` 已移除 Manager 和计算子进程，原嵌套 task 主体逐字不变；UA 与 precise 共用显式传入的求解超时。本轮不启动 Polygon、SQL、编码器或外部求解器，没有新的科学结果，也不把环境准入失败当作研究终点。

## 已解决的确定工程问题

隔离目录 `isolated_local/` 包含两个修改文件和一个逐字未改的 Z3 接口文件；它是三文件覆盖层，不是完整安装。`serial.patch` 为零上下文差异，`build_adapter.py` 从冻结上游文本严格验哈希、验证语法后生成，拒绝覆盖现有目的目录。上游固定在 polygon-sql/polygon `5e18237394d025dbb805cf833b4f54c321470774`，源文件哈希见脚本与 `BUILD.json`。

改动仅有：

1. `check` 新增必填 keyword-only `solver_timeout_seconds`，拒绝布尔、非整数、零和负数；本次冻结配置为 **3 秒**。两模式同样赋给 `self.formulas.timeout`。
2. 每个 Environment 最多调用一次 `check`，包括解析/编码/求解异常后也不能重用。串行 task 会修改本对象，而原 task 修改计算子进程中的对象；单案例、独占、新对象并且执行后弃置是适配合同。复用拒绝不代表一般 Environment API 等价。
3. 原计算 task 保留原文，以普通 dict 接收结果并直接调用；结果投影、错误处理和 `clear()` 的次序保留。
4. precise 唯一求解侧差异是 `-T:300` 改为 `-T:{self.timeout}`；UA 原来已读取此字段。其余 search、知识库调用、SMT 公式生成、NULL/约束编码及模型解码均未修改。

适配后调用形状为 `env.check(q1, q2, use_precise_encoding=mode, solver_timeout_seconds=3)`。本轮没有真实执行这个调用；测试使用提取方法和替身依赖。

`disambiguate` 不在范围，仍是原多进程代码，不能作为串行入口使用。文件顶层 multiprocess 导入仍存在，但导入本身不是创建 Manager；本轮测试不导入 Polygon 或该第三方模块。

## 等价证据及严格边界

8 项标准库单元测试通过，包含十种 UA/precise × NEQ/EQU/编码异常/求解异常/模型解码异常的 task 接口比较。原计算 task 文本完全相同；其他 Environment 方法 AST 不变；FormulaManager 全 AST 除 precise 超时表达式外相同；SMTLIBv2 文件哈希不变。测试比较传入查询的顺序和内容、追加 neq 的顺序、求解模式、返回值及非计时 ret 字段。

旧执行包装仅在测试中用同步替身模拟 task 入口与 Manager 字典相关拷贝语义，**不是**实际 fork/spawn 或 IPC 行为等价试验，也不是数据库语义测试。普通 dict 会省去 IPC/序列化开销；单案例普通可序列化返回数据的内容合同被测试覆盖，不承诺任意自定义对象、不可序列化返回值或多线程并发。普通 dict 的返回 `result[1]` 与 `result[4]["cex"]` 可指向同一个对象，原 Manager 取值会拷贝；合同只保证只读消费的数据内容，不保证对象身份/后续修改的联动行为。原 task 的 outputs 调试 evaluate_table 位于异常捕获块之外：此处原子进程崩溃会使父端可能因缺少 status 而报 KeyError，串行入口直接传播原异常。未捕获异常类型/堆栈和进程隔离副作用不在等价声明中，不能把这类异常当科学反例或求解结论。

随机流：没有新增、移除或重排生产代码中的 seed/sample/random 调用，没有改 Z3 随机选项。快照中唯一显式 Python RNG 点是 `cover_ua` 的固定 seed 123456 和 sample；测试直接执行原/适配的该生成器，比较输出及结束 RNG 状态；另在任务替身中比较相同入口 RNG 状态下的消耗轨迹。以上保证的是**相同解释器/哈希种子/模块初态、相同 task 输入和入口 RNG 状态下**的调用保持，不宣称恢复过去某次子进程的随机流。原 `string_hash` 用内置 hash，spawn/fork 的解释器初始化和缺失模块的全局状态尚无完整证据；未通过另设 seed 掩盖差异。单案例进程的全局 RNG 可能被 task 改变，调用方应弃置该独占运行上下文。这里须涵盖进程/模块状态：`schemas.py:75–76` 的 `@cache` 不由 `Environment.clear()` 清除，因此仅 new Environment 不能证明跨案例恢复相同状态；本包不支持在长期共享解释器中串行跑多个科学案例。

本轮仅对 #750/#319 的 SQL/DDL 读取字节核对哈希，没有解析、执行或变换，完整 C、SQLite AVG/整数表示等前轮尚未闭合的语义问题不因串行包装而解决。`INVARIANTS.json` 复核前轮 9 项冻结文件/旧标记及 24 个上游内容哈希未变。

## 资源和时间合同变化（不可当官方性能复现）

| 项目 | 原路径 | 本次适配 |
|---|---|---|
| 计算执行 | Manager + 计算 Process | 当前 Python 调用线程 |
| Z3 | `Popen` 外部进程 | 原样保留外部进程，绝非纯单进程 |
| UA 每次 Z3 超时 | Environment 的 time_budget | 显式冻结 3 秒 |
| precise 每次 Z3 超时 | 写死 300 秒 | 同样显式冻结 3 秒 |
| 整例超时 | `join(time_budget)` 后终止计算 Process | 本补丁不提供整例硬截止 |
| 计时起点 | 计算 Process.start 返回后 | 直接调用 task 之前 |

缩短 precise 时间预算可能改变完成/超时结果，故仅称同逻辑的资源配置适配，不能称原官方配置的运行性能复现。3 秒为每次求解器预算，UA 可能多次 check，不是整个案例或整个批次预算。保留的 `time_budget` 构造参数在此串行入口不再提供外层截止；未伪装成仍有外层保护。

原 SMTLIBv2 的 `Popen` 不能靠换包装消除。每次 check 可能启动新的 Z3，接口未显式统一 close/wait/reap；读取状态循环对 EOF/timeout/unknown 没有可靠退出路径，单靠 `-T:3` 不保证 Python 调用按时返回。这些原逻辑本轮不改，以免将协议修复混入串行等价改动；也因此本补丁尚不是可安全启动的运行器。

后续实际执行在现有机器所需的最小工程条件是：补齐同一固定版本当前缺失模块；给独占串行 Python worker 配置总截止；登记**每一个**由本任务创建的 Z3 句柄，覆盖成功/异常/超时/父任务退出时的终止和回收，且既有 1 GiB 采样计数必须覆盖 Python 与仍存活的全部自有 Z3（允许采样间超调，不能冒称硬限制）。不能只看 Python 自身内存，也不能在 Z3 存活时把外部调用当已结束。实际实现需在允许的执行环境内满足这些合同；本轮未验证相应权限或运行保护，没有提出新负载阈值、账户、凭据或硬件升级要求。

没有再次调用 ps，也没有使用另一 API 读取被拒的进程信息；没有任何进程枚举、负载探测或 unrelated_project 操作。本轮子进程禁令适用于测试/适配代码，普通工具启动 Python 测试解释器本身不计为测试创建子进程。测试安装 audit hook 阻止常用派生进程和网络事件，实际命中数为 0；不将此有限 hook 当操作系统级完整沙箱证明。

## 验证记录与审查

初次使用系统 Python 3.9 静态构建，在未改的 SMTLIBv2 `match` 语法处失败；未运行研究代码。该次部分输出保留于 `build_py39_incomplete_local/`，不是交付副本。构建器随后改为全部语法验证成功后才创建输出，使用机器已有 `/opt/homebrew/bin/python3.12` 完成，未安装包。正式测试结果见 `TEST_OUTPUT.txt` / `TEST_RESULTS.json`。

独立审核由非作者任务执行，结果单独保存于 `INDEPENDENT_REVIEW.zh.md`。审核与单元测试均不授权真实求解器运行。历史 raw/native 备份及公共研究源 DataHub 注册缺口沿用前轮状态，本轮只新增已有固定代码的离线适配，不读取外部数据源。
