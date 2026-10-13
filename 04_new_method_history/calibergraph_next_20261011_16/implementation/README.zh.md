# 第16阶段最小禁用适配

状态：**DISABLED / DRAFT；本作者未运行科学代码、未import科学模块、未compile/py_compile，未做SQL、SMT、能力probe或优先级变更。** 本目录只承接第15阶段未回答的已暴露开发诊断；第15阶段保持永久停止，第13阶段一次失败也不重试。root负责资源观察调度、唯一batch的永久exclusive once-lock、独审后的启用/注册/runtime冻结和私有备份。

六份作者源从第15阶段复制。`official_generation_worker.py`、`official_contract_admission.py`、`safe_sqlite_replay.py`逐字节不变；common仅改16版ID/标题，仍`EXECUTION_ENABLED=False`。后端只增加读计时证据的派生函数并替换空集合求和；supervisor只改16版ID/输出路径、早期准备费登记与观察账接口。逐源和协议diff见`round15_to_round16.diff`；静态核对及作者禁用freeze见`STATIC_VALIDATION.json`、`AUTHOR_DISABLED_MANIFEST.json`。这不是运行时freeze或科学执行审批。

原4来源、原SQL/schema/full operational C、原runtime lock和21来源registry hash、原官方Environment与C-model sanity模型/SQLite准入profile全部保持。24 planned槽顺序原样：rep1为`[6,9,14,3] × [2,3,4]`，rep2为`[3,14,9,6] × [4,3,2]`，先来源后bound。每槽一次Environment；恰N活行/原表不等于最多N。两遍是预定独立slot，不是retry。来源在旧第06轮结果暴露后选定，是adaptive development diagnostic；没有新机制、fixed-witness comparator、独立最终测试或runtime优势主张。

worker/solver硬限额保持原值：单worker、nice≥15、RLIMIT_CPU3秒、wall4秒、采样RSS256MiB、C100ms/query700ms、Z3memory128MB/threads1、累计solver wall2秒及supervisor1.5秒触发、load1≤4/free≥25%、batch60秒、prepare10秒、batchtail0.2秒。开始slot的50秒门、active56秒门、总账60秒门均包含观察charge；两处active56门从旧observed subtotal改取含batchtail0.2的conservative total，阈值56不变，收紧0.2秒而非扩预算。普通query UNKNOWN仍按旧策略保留并继续；资源/监控/完整性失败仍停止剩余槽。无新增solver check、公式修改、budget.check、超时变更或Environment尝试。

## 纯计时修复

`measured_stage_cpu`只读已有stage。没有匹配stage时返回`null / NOT_REACHED`；有stage但缺目标实测字段时返回`null / UNMEASURED_OR_CENSORED`；存在全部实测字段时才求和。parse与query-check不再因空集合而生成0。query stage已建立而真正check未到达，或收据不完整，不能猜测实测0。

`scope_encode`继续用原`max(0, analyze_cpu - parse_cpu)`公式，但必须同时具有analyze和parse的实测证据；否则为null，并保留未到达或缺依赖状态。该派生项包含analyze中非parse开销，不保证scope encoding已成功完成。comparison沿用第15阶段计时起止和finally，状态原样保留。新增`exclusive_phase_cpu_status`与数值分开；测得0可以保留为0，未测不能改0。hard signal/kill可绕过finally；缺最终派生字段时必须回到stage/progress/外层收据，不能补零。

source/structure准入、import、fullC、C sanity、replay及cleanup等原计时未改。parse嵌在analyze内，inner replay嵌在outer replay内；不能双加，phase不能相加冒充整个进程生命周期成本。

## root观察账接口与等待边界

协议`supervisor`新增三个字段，草案均为null：`prior_resource_observation_measured_cpu_seconds`、`prior_resource_observation_tail_reserve_seconds`、`prior_resource_observation_cpu_charge_seconds`。root在唯一正式launch前封账：每次15分钟资源观测的测得SELF+全部reaped CHILDREN仅计一次，另加每次0.2秒退出尾预留；charge必须等于两者和。三个字段都必须是有限非负数，等式容差1e-9；null或不一致均不能启动科学worker。prep10不在观察charge内，不双计。

supervisor的prep10在POLICY入口即登记，不再等`load_registered`成功。读取protocol后，先登记并校验观察账，再读freeze和做源码/输入准入。缺失或读protocol之前失败时，完整`observed_total_cpu_seconds`与`conservative_charged_total_seconds`为null；另列含prep10、当前SELF/CHILDREN及batchtail的known minimum。最终收据标记`INCOMPLETE_PRIOR_OBSERVATION_ACCOUNTING`，root外层账兜底，known minimum不能当完整账。

等待只存在于root拥有的科学batch启动前15分钟资源观察调度；科学supervisor没有等待循环或恢复机制。首次科学worker启动后仍使用原资源stop截尾/no retry；禁止为了等待版本重跑已执行科学slot，也禁止新输出目录绕过唯一batch尝试。`flock`仍只是并发互斥，不能代替root永久once-lock。任何未启动、失败、UNKNOWN、censored、NOT_RUN或收据缺失均保留在24 planned分母，不对预测SAT/UNSAT作断言。审批拒绝、syscall失败、资源门失败与科学结果分别标记。

下一步最小门：独立静态审查本禁用freeze；root封资源观察账、完成具体执行请求和once-lock；仅当全部门通过，按独审约定改source gate/登记状态并生成包含六源、协议、interpreter、input、runtime lock及依赖的runtime freeze。当前无fresh preflight或科学运行证据。DataHub、历史raw/native恢复与私有备份缺口由root按既有状态保留，本作者不宣称BACKUP_OK。
