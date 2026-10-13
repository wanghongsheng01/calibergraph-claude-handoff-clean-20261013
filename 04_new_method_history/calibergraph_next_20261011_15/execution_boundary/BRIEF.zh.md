# 第15阶段执行边界静态核对

状态：`STATIC_ONLY / NO_EXECUTION_AUTHORIZATION`。日期：2026-10-11。作者：`/root/round15_execution_boundary_audit`。本报告只读旧源、旧协议及已存在结果，做标准库 JSON 读数/文件哈希；未启动 scientific code、SQL、solver、nice、priority 修改、资源能力测试、测试或科学模块 import。第06及第13目录未修改。DataHub 与私有备份由 root 统一处理。

**结论：第06轮的资源监督与成本总账可以作为新协议模板，但不能原样运行新增来源或 `2/3/4`。第13轮保持一次失败 `NOTCOMPLETED`；不得重试或修旧文件。** 新执行是否必要，由 root 完成文献、来源及范围汇报后决定。本报告没有授予执行许可。

## 已有成功与失败证据

第06轮 `runs/generation_replay_01/batch_receipt.json` 记录 `REGISTERED_SEQUENCE_FINISHED`、12 registered/attempted/returned、0 retry、0 reported violation；12 worker exit code 均为0。这表示已注册过程返回，不等于12个查询成功判定。两条 INT 来源 `dev03_10`、`dev03_15` 都是 exact2 UNSAT / exact4 UNKNOWN timeout / exact8 UNKNOWN out of memory；另外 `dev03_07` 三个 UNSAT、`dev03_04` 三个比较编码异常且 query check=0。完整分母是12槽：5 UNSAT、4 UNKNOWN、3 INCONCLUSIVE；full-C check=12，query check=9，合计 solver check=21。

已有6个 C-model sanity 回放共执行12条原 SQL，输出均相同。它们来自 full-C 非空检查的模型，标签为 `C_MODEL_SANITY_ONLY_NOT_QUERY_SAT`，并非查询 SAT 区分反例。两个 INT pair 已有静态等价恒等式强控制，未实现计时基线。较大 bound 的 timeout/OOM 已支持“固定编码在该预算下对 bound 敏感”，不能据此认定科学 hardness、新方法价值或速度优势。业务 C 的真实性及完备性仍为 UNKNOWN；旧21来源全部为已暴露开发材料。

第13轮 `outer_launch/stderr_and_time.txt` 原文显示：

```text
nice: setpriority: Operation not permitted
... replay.py, line 34 ... os.nice(15 - priority)
PermissionError: [Errno 1] Operation not permitted
time: sysctl kern.clockrate: Operation not permitted
```

`exit_receipt.json` 是 exit=1、attempt=1、retry=false。源代码第25行在 `os.nice` 前设 CPU limit，第38–40行的 hashlib/json/sqlite3 import 还在失败点之后。静态控制流可以描述失败位置，但须继续遵守已经冻结的保守失败账本：98个计划 DB / 196条计数 SELECT 的逐项实际状态 `ACTUAL_STATUS_UNKNOWN`；不把缺失收据写成全部运行0次。原静态独审为 PASS；这是一次实际进程中的 OS/sandbox 系统调用 EPERM，**不是可见的 auto-review 权限拒绝**。本审计也未提出任何 escalation 请求，故无新的 auto-review 结果。

## 第06轮实际执行保护及证据限度

| 保护 | 源码与实际证据 |
|---|---|
| 串行/单 worker | `generation_supervisor.py:539–545,573–583` flock 后逐槽等待；新 session/process group；未知子孙拒绝；已回收 PID 不再 signal。 |
| nice | `generation_supervisor.py:296–300` 在 child preexec 调 `setpriority(max(current,15))`；`generation_common.py:47–66` worker 复核 nice≥15。06 supervisor 自身源码没有降低父优先级的语句；外层是否另用 nice 没有保存在已读回执中。 |
| 进程硬 CPU | child preexec 与 worker 均 `RLIMIT_CPU=(3,3)`，core=(0,0)。worker SIGALRM 4秒 wall；软预算预留0.25秒。 |
| RSS / wall / load | 父进程约0.1秒轮询 ps/process group，256MiB RSS、4秒 lifecycle wall、load1≤4；每槽 memory_pressure free≥25%。RSS/wall/load为采样保护，允许并披露overshoot；不宣称kernel瞬时硬RSS。无RLIMIT_RSS，注释说明旧Darwin调用失败。 |
| solver | C check≤100ms、query check≤700ms、线程1、parallel=false、内部memory参数128MB、累计solver wall≤2秒，supervisor 1.5秒触发；不保证现实调度严格无超调。 |
| 批次 CPU | SELF + 全部reaped CHILDREN只相加一次，含ps/memory_pressure、失败preexec和worker；准备10秒是保守预留，尾部0.2秒是预留；新槽门50秒、活动门56秒、总账60秒。此处60秒是监督记账/停止规则，不是一个对整个进程树的kernel硬CPU限制。 |
| 失败 | 监控/环境/资源/完整性失败停止剩余槽；UNKNOWN保留；无自动重试。清理只针对该worker拥有的group，kill/reap并留收据。 |

06实际总 SELF+CHILDREN CPU=18.274636s；含10+0.2预留计费28.474636s；12 worker wait4合计14.442653s（已含在CHILDREN，不能再加）；最大worker CPU=2.166776s、完整生命周期wall=2.239919625s、wait4 RSS=258162688 bytes。独审补充完整生命周期wall，不能只引用较短main wall。源码/历史收据证明当时这些路径成功，不证明当前环境可调用相同syscall。

已读06 artifacts保存了固定解释器、worker argv、env、wait4、probe及源码；**没有发现外层工具名、`sandbox_permissions` 或 auto-review receipt**。不能猜测06使用了 require_escalated，也不能从06成功推断13失败源自代码差异或推断当前可运行。

## 计时与全成本口径

| 成本层 | 现有覆盖 / 局限 |
|---|---|
| 整体 | supervisor绝对SELF+CHILDREN含启动/探针/子进程；wait4覆盖worker完整生命周期，main usage在最终序列化/关闭/打印前采样，不能代替wait4。准备/退出预留另标非测量。事后分析/核验不在旧监督区间内。 |
| runtime | `official_generation_backend.py:92–128` 分别记录锁/依赖hash、native+官方import。 |
| full C | schema/environment、完整C加入、solver setup、非空check、model validation分别记阶段，C-model export/replay也计入同一预算。 |
| parse/encode/check | parse嵌套在analyze/scope总阶段，exclusive scope=analyze-parse，不能双计；comparison编码只在SolverTap.check入口记录（:233–250）。比较阶段提前异常时细分compare_encode=null，不能写0；成本仍在attempt/进程总账。 |
| 回放 | export、独立全C验证、SQLite load、两个原SQL及cleanup有计时；回放内层包含在外层control/replay phase，不能两层相加。 |
| 未闭合部分 | worker `SOURCE_AND_STRUCTURE_ADMISSION`只发START（:77–98），没有独立完整stage计时；stage计时边界外的日志/序列化有开销；父总账覆盖但各phase加总不能称精确全成本分解。硬中断可使阶段未闭合，标censored/unknown。 |

若新诊断的目的包括定位编码增长，建议在**新的15版**最小增加 admission 起止及 comparison 前异常路径的finally耗时，注明包含/排除关系；不增加求解调用、不改SQL/C、不改预算。也可不改测量实现而坦诚保留这些null/未分配成本。任何变化都先静态复核、留diff及新hash；不得回填旧06观测。

## 新 `2/3/4` 不能原样复用的具体原因

1. `generation_common.py:12,73,87–103` 固定06 ID、旧21 registry hash、来源顺序 `[6,9,14,3]` 与所有exact bounds `(2,4,8)`；新bound3会fail closed。
2. `generation_supervisor.py:142,174–175,515–527` 固定协议ID、worker路径、06输出根和预置12槽分母。仅换JSON会被拒绝；从别处直接启动worker会绕过已审保护，禁止这样做。
3. `safe_sqlite_replay.py:24–44,144–150` 只准两个已固定INT来源完整哈希；新增真实query没有自动获准的decoder/dialect/full-C replay。backend C-model sanity分支也只认识旧两来源（:260,295）。新增来源需要独立语义准入，不能只增加ID或把拒绝改通过。
4. 旧 `code/analyze_frozen_run.py:16–26,82–84` 假设恰12结果、均有attempt快照并断言旧结果分布；不能用于新结果。新只读聚合须从已冻结slot表出发，保留未启动/未知/截尾，不把预期结果写成断言。

可复用计算后端与守卫的设计；新15目录需要新明确allowlist、ID、输入与runtime完整hash、固定来源顺序×`(2,3,4)`全槽账本、新路径/lock/一次尝试收据。旧数据若选用仍是development diagnostic。新来源必须由root证明公共出处与完整operational C，业务合同保持UNKNOWN；whole original SQL/schema/C字节固定，只改变每原表exact N。N不是at-most bound，通常不能从N=2 UNSAT推到N=3/4。不得保留快例、丢慢例或按结果补换来源；所有来源在看到新结果前同时固定。

root于本报告冻结前给出的具体**待审提案**为：原4来源 × exact N `(2,3,4)` × 预先登记2重复 = 24 slots；每槽仍只有1次Environment，不是失败后的retry；保持06所有资源、语义及C sanity逻辑。不新增fixed-witness comparator或机制。必须给repeat显式身份、在运行前冻结完整顺序，24槽都进入分母；60秒总账照旧，预算不足即保留剩余NOT_RUN，不能扩预算来完成24槽。本审计未登记该protocol、未生成runner、未授权执行。

## 当前工具支持的最小透明运行边界（仅建议）

当前 `exec_command` schema明确支持 `sandbox_permissions: "require_escalated"` 与 `justification`；当前权限环境为workspace-write、network restricted、`approvals_reviewer=auto_review`。这是工具提供的**单次受审执行请求**，不会自动授予许可，也不是修改system security。现阶段不调用它，不做先行nice/sysctl/SQL/solver能力探测。

只有root完成范围/来源/文献报告并决定执行、准备可审阅的新15代码/协议/冻结/失败规则后，才可提出一个精确命令的require_escalated请求。请求必须明确说明：新15开发诊断、来源数×3个槽、一次batch、每槽一次Environment、保留nice≥15与上表全部限额、只读已pin依赖、结果只写新15目录、无网络/GPU/凭据/系统设置改动；不使用广泛prefix规则。建议新外层完整time+exit收据和永久once-lock在科学worker之前就留存；外层nice≥15及父/child复核保留，避免默认沙箱试跑后再升级。

可提交的 `justification` 内容应具体到最终manifest与命令，例如：“请求在受审批的主机执行环境执行已冻结的第15阶段单次本地开发诊断，使进程能降低自身优先级至nice15并读取本进程资源统计；维持单worker、3秒CPU/4秒wall/256MiB采样RSS、固定solver与60秒批次预算，所有失败保留，无网络访问。” 此示例不是已经提出或批准的请求；来源数、SHA及实际脚本路径还未由本审计确定。

若auto-review明确拒绝：不启动，记录 `APPROVAL_DENIED_NOT_LAUNCHED`，按工具原理由说明；若执行后syscall失败：记录 `ENVIRONMENT_STARTUP_FAILURE / NOTCOMPLETED`，消耗新协议一次尝试；二者不得混写。新协议可预先规定审批拒绝是否消耗外层请求次数，但不能临时更名再次申请来绕过拒绝。不得删nice、降守卫、抬cap、换未审API/terminal或改OS/sandbox安全设置求通过。一次批准也不证明syscall或runtime能力；失败则保留原始stderr/time/exit，不重试。

这份静态报告不发明已知可靠的“host API”，不承诺auto-review会通过；真正剩余门是root的新科学范围、来源与测量合同、独立静态复核、新冻结和受支持执行请求的实际结果。第13轮永远保持既有NOTCOMPLETED。

## 证据与交接

精确输入身份见 `evidence_hashes.json` / `SHA256SUMS.inputs`，机器结论见 `boundary.json`；本目录输出hash见 `SHA256SUMS.outputs`。仅对列明文件本次读字节并hash，不冒称重验了06的全部880依赖或整台机器历史。所有durable备份/DataHub检查交root；本子任务未git/push，未读取企业/云来源或凭据。
