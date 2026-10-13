# Polygon 串行适配独立审核

结论：**PASS_WITH_LIMITS**。冻结小补丁在“新建、独占、仅一次 check，返回数据只读消费，调用前状态匹配且整段执行上下文随后弃置”的合同内可作为静态工程交付接受。未发现这个限定范围内仍须修改作者代码的回归。这不是运行准入、数据库语义证明、过去随机流恢复或官方性能复现，也不是研究 NO_GO。

本审核为非作者审核；没有修改作者代码。审核对象是最终 `RESULT.zh.md` SHA-256 `d6a66555f4e8ae3096d5273b25461e4b179730e9562a8741946a6f86f8ba3090`，补丁 SHA-256 `bc4f72b62875efaeb4ec04862f373489acd1790689f3c8ac0ba48c7eda52e9f8`。上游依据本地冻结 provenance 固定在 `5e18237394d025dbb805cf833b4f54c321470774`；没有联网复验远端。完整对象哈希与验证数据在同名 JSON。

## 实際验证范围

使用已有 `/opt/homebrew/bin/python3.12`（3.12.13），以 `-B` 禁止生成字节码，加载测试定义但不执行其写报告的 main。独立重跑其中 7 项无输出目录写入的标准库测试，**7/7 通过**，覆盖 10 个 UA/precise × NEQ/EQU/已捕获错误替身组合、单用守卫、超时参数校验、任务体、AST 和 `cover_ua`。作者原有 8/8 记录已读；本审核没有把它作为独立重跑结果。第 8 项磁盘 build 测试会创建临时树，本审核按写入范围不重跑；改以静态检查构建器和内存重建，确认三个覆盖文件及 `serial.patch` 逐字匹配，两个 BUILD.json 逐字匹配。

另行增加以下验证：

- 提取原/适配的 `search`、`search_naive`、`backtrack`、`solve_precise`，用构造后立即停止的惰性替身捕获 Z3 参数：前三者在 timeout 字段为 3 时均传 `-T:3`；precise 原来传 `-T:300`、适配传 `-T:3`。没有运行这些方法的求解循环。
- 对未改的 `clear()` 使用惰性依赖，证实 `_serial_case_used` 保留；同时 `initialized` 和 `curr_query_id` 不会被重置。没有真实约束编码。
- 用无 IPC 的拷贝字典替身和子失败传递模型，独立证实返回别名及未捕获解码异常两项差异。此模型不冒充真实进程试验。
- 重算 `INVARIANTS.json` 中 9 项冻结输入/旧标记及 24 项上游内容哈希，全部匹配。SQL/DDL 仅按字节读取计算哈希。

全过程未导入 Polygon 模块、未进行真实编码、SQL 或求解器执行；Python 验证代码没有创建子进程，audit denylist 命中 0。没有进程枚举、负载探测、替代 API 查询、unrelated_project 操作或网络安装。有限 audit hook 不等于操作系统级完整证明。工具启动测试解释器本身不计为测试派生子进程。

## 代码及语义判断

1. **任务与求解逻辑保持成立，但只能按限定合同解释。** 原嵌套 task 的源码文本相同；其余 Environment 方法 AST 相同；FormulaManager 全 AST 只有 precise 超时表达式变化；SMTLIBv2 字节未改。输入查询解析順序、编码順序、neq 追加及结果投影未重新实现。替身比较把两侧 timeout 预设为 3，隔离的是任务接口逻辑，不能据此推断原官方预算下运行结果相等。
2. **单用限制必要且生效。** `environment.py:183` 先拒绝非法超时，再在 `:185–188` 检查/置位守卫。有效尝试即消耗对象，包括 parse、encode、solve 失败；非法参数不会消耗守卫。成功分支的 `clear()` 不解除守卫。API 接受任意正整数，但本次冻结配置是显式 3；其他值不是本包冻结实验配置。此限制并不拦截 `disambiguate`，该方法本来就在合同外，仍有 Manager/Process。
3. **串行状态变化仅能条件等价。** task 现在直接修改调用者对象，且可能改变模块 RNG、缓存和其他全局状态。`schemas.py.txt:75–76` 的类级 `@cache` 不由 `clear()` 清除；`clear()` 也保留 initialized/curr_query_id。只新建 Environment 并不足以证明多案例独立。最终报告已明确要求弃置整个独占进程/模块执行上下文，不支持长期共享解释器连续运行科学案例。
4. **随机流没有被重写，完整运行随机流未证。** `formula.py:447–449` 的 seed/sample 与 SMTLIBv2 的 Z3 随机选项保持原文；内置字符串 hash 仍在 `environment.py:82`。当前 `check → search → backtrack` 使用 `cover_ua(left_tops=8)`；显式 RNG 分支来自 `tops_ratio`，测试直接调用该分支不能替代真实 check 的随机轨迹。声明必须依赖相同解释器、hash seed、模块初态、task 入口 RNG 状态及实际走到相同调用路径；没有恢复旧 fork/spawn 子进程状态的证据。最终报告的条件说明可接受。

## 审核发现及最终处置

**R1，未捕获异常传播不同，已补充边界。** `environment.py:252–253` 的输出表 `evaluate_table` 位于 try 外。原计算子进程失败后，父端可能因 `ret['status']` 未设置而抛 KeyError；串行 `task(ret)`（`:283`）直接传播原异常。惰性模型分别产生 KeyError 与 ValueError，均不调用 clear。作者测试的 evaluate 异常只在 base 表处触发，覆盖的是被捕获分支。最终 RESULT 已排除未捕获异常类型/堆栈等价，没有要求改动任务体。

**R2，结果对象共享关系不同，已补充边界。** 普通 dict 使 NEQ 返回的 `result[1] is result[4]['cex']` 为真；模拟 Manager 取值拷贝时为假。修改前者会联动串行 ret 中的 cex。测试只能说明当时的数据内容相等。最终 RESULT 将消费合同明确收窄为只读数据，不保证对象身份或后续修改联动，可接受。

**R3，模块缓存不会随新 Environment 消失，已补充边界。** 共享缓存与全局 RNG 是执行上下文条件的一部分。最终 RESULT 已明确该条件，ADAPTER_CONTRACT 同时要求 discard environment and exclusive execution context。没有将对象守卫描述为全局状态复原。

三项发现均以准确收窄说明闭合；没有改变查询、约束、任务体或随机调用以掩盖差异。最终限定合同下剩余必须修的代码项：**无**。

## 时间、进程与后续执行条件

`SMTLIBv2.check` 仍在 `smtlibv2.py:171–176` 创建外部 Z3；去掉 Manager/计算 Process 不构成纯单进程。UA/search/backtrack 可能多次调用 check，每次还可能覆盖 `self.smt_process`；没有统一回收所有历史句柄的逻辑。`:184–189` 的读取循环只等待 sat/unsat，EOF、unknown 或 timeout 不能保证可靠退出。文档对这些缺口的陈述准确。

3 秒是单次 Z3 调用配置，不是整例硬截止。补丁移除了旧 join/terminate 路径及其 TMO 产生机会，保留的 TMO 投影本身不能制造保护；旧计时在 Process.start 返回后，新计时在 task 之前，而且两者都不包含前置解析。`complete_time` 在输出/数据库模型解码前设置，clear 也在该结束时刻之后，故此返回时间并非全案例墙钟耗时。这些时间字段不适合用于官方运行性能比较。precise 的 300→3、UA 的原 time_budget→显式 3 均可改变完成或超时结果。

后续启动仍需补齐固定版本缺失模块，建立整例截止、所有自有 Z3 句柄的终止/回收，以及 Python 加全部存活自有 Z3 的既有 1 GiB 采样统计；采样不等于硬内存限制。这是下一阶段工程前提，本审核没有实际验证权限或运行保护，也没有新增资源阈值或将其归为研究终点。

本委派仅写两份独审报告，未操作 Git 或联网备份；整体交付和私有备份状态由父任务核验、报告。
