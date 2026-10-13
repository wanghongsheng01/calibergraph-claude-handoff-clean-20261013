# 第16轮实际结果：成本、调度与最终冻结独审

审查者：`/root/round16_independent/wait_budget_criteria`。结论：**`PASS_COST_AND_SCHEDULING_BOUNDARY_WITH_STATED_LIMITS`**。保存证据支持两次资源观测后的一次完整24槽批次，收费未超过原60秒；未发现观测费、worker/helper CPU漏入总账或重复相加。此结论只审本次成本和执行边界，不评价query判定的业务真值、方法晋升或无界等价。

本审查读取原始observer/outer/batch/24个supervisor与worker收据、261条MONITOR及冻结源码，独立重算334个CPU账快照；没有运行SQL、SMT、科学模块、目标import/compile或作者聚合器。可复算代码是本目录的`audit_cost_boundaries.py`，仅做JSON读取、SHA及算术，结果为`COST_BOUNDARY_EVIDENCE.json`（`issues=[]`）。最终冻结与字节差异另由独审子代理`finalization_allowlist_readonly`只读复核，不委托作者自评。

1. 调度与一次尝试

| 证据 | 核验结果 |
|---|---|
| 第一次观测 | 16:46:00.753611 UTC；load1=4.38134765625、free=38%，正确保持WAIT_RESOURCE；无科学操作。 |
| 第二次观测 | 17:01:30.218608 UTC；load1=2.69287109375、free=37%，ELIGIBLE；两次outer exit均0，stdout JSON均与receipt相同，stderr为空。 |
| 两次间隔 | monotonic 929.461709083秒，UTC 929.464997053秒；均大于900秒，首次也晚于预定16:45。 |
| 启动时效 | ELIGIBLE结束17:01:30.222062；永久lock在其后19.775016秒；batch创建17:01:53.700777，即23.478715秒后。请求发生在lock与batch创建之间，故满足60秒上界；精确请求提交时间仍为null。 |
| 唯一批次 | 仅`runs/diagnostic_01`；once-lock、finalization、registered protocol、freeze及outer均关联同一批次；24注册槽和batch逐项同序，全部RETURNED、worker exit0、无stop_remainder、无violations。worker事件逐槽不重叠。 |

收据关联支持一次启动，但本地JSON本身不能独立证明O_EXCL系统调用或完整工具请求历史没有其他调用。root/主审须保留原始请求chunk `d74bf2`及完成chunk `93b879`。第一次正式supervisor请求已消耗本轮唯一batch；本报告不授权再次等待、补槽或重跑。

2. CPU账与外层交叉核对

| 范围 | CPU秒 | 记账方式 |
|---|---:|---|
| 两次observer SELF+reaped CHILDREN样本 | 0.085291 | 实测样本，只加一次。 |
| 两次observer尾部预留 | 0.400000 | 每次0.2，非实测。 |
| 原准备预留 | 10.000000 | 原封套不变，非实测。 |
| 当前supervisor SELF | 0.759441 | 实测样本。 |
| 当前全部reaped CHILDREN | 32.436312 | 已含全部24worker及已回收监测helper。 |
| 批次最终输出/退出尾部预留 | 0.200000 | 非实测。 |
| **保守累计收费** | **43.881044** | **低于60，余量16.118956。** |

当前SELF+CHILDREN为33.195753秒；加observer实测样本后为33.281044秒。24worker的wait4总和26.406519秒，是CHILDREN的子项，不能再加。CHILDREN减去worker为6.029793秒，包含本次非worker已回收子进程费用；源码路径对应memory_pressure与ps等监测工作，但没有逐helper独立wait4明细足以把此残差进一步精确归因。只报worker费用会漏掉这部分以及supervisor自身费用。

外层`/usr/bin/time`记录28.49秒wall、26.05秒user和7.14秒system（分别保留两位小数，和为33.19秒），与内部高精度样本差−0.005753秒，处于两个四舍五入字段的合计精度范围内。内部batch创建到结束28.440053秒与外层完整生命周期范围不同。外层是交叉核对，不再加入内部账；尾部预留也不冒充实测终止费用。observer的CPU为生命周期累计，而wall从源码START计，二者起点不同。

所有334个账快照均与`10 + observer累计0.485291 + 当前SELF + 当前reaped CHILDREN + batch tail0.2`一致。前launch的50秒门最大收费42.699540；监测56秒门最大42.922806；另加live worker采样的60秒门最大43.782806，均未触及门。准备10与观测费在本次成功注册后的所有账中保留。

3. 实测资源边界

| 项目 | 本次最大值/最小值 | 原门 |
|---|---:|---:|
| worker wait4 CPU | 1.736529秒 | 3秒 |
| supervisor记录worker lifecycle wall | 1.847811959秒 | 4秒 |
| worker wait4/采样RSS最大值 | 131743744 bytes | 268435456 bytes |
| 每槽累计C+query实际solver wall最大值 | 0.724454500秒 | 2秒 |
| monitor solver watchdog estimate最大值 | 0.724454500秒 | 1.5秒 |
| 活动监测load1最大值 | 3.3671875 | 4 |
| 24次槽前free最小值 | 35% | 25% |

24worker均有匹配pid与exit0的wait4、成功reap、结果hash及原始嵌入收据一致性；261次监测仅观察到所拥有worker pid，没有已观测未注册后代。冻结preexec路径设置nice15及CPU3；这不等于另行查询验证整棵进程树的kernel瞬时硬限制。RSS/wall和load是采样证据；free是槽前证据，不能声称整个槽期间连续观测free。

**700ms是query solver超时设置，不是实际wall硬上限。** 四次实际query check超过该设置：case05=0.716613667、case08=0.712520458、case15=0.719017375、case18=0.717027208秒。它们仍低于独立累计solver和watchdog门，不应删除，也不能叙述为“每次query实测≤700ms”。24次C check最大0.005730583秒；共18次实际query check，另6槽没有query call。

4. phase范围与未归因成本

24槽的parse、analyze-minus-parse、compare和actual query check字段均从原始阶段重新核对；本次analyze≥parse，未依赖`max(0,...)`掩盖负残差。6个未到达query的槽正确为null/NOT_REACHED，其compare异常前耗时保留为实际样本，不伪造query的0秒成本。

parse嵌于analyze；实际solver check嵌于check阶段；sanity回放内部phase嵌于外层sanity阶段；attempt嵌于worker；worker wait4嵌于batch CHILDREN。不能把这些层逐项相加当完整生命周期。独立重算的runtime+admission+attempt均小于worker自身样本：合计还剩1.076359秒未分配到这三个范围；worker样本到wait4另有0.040615秒。它们已包含于worker/batch CPU总账，没有从总成本漏掉，但不能无证据拆为特定日志、初始化或退出原因。四个exclusive phase只覆盖部分处理，不能由其和推断完整流程、fullC占比或瓶颈因果。

5. 最终冻结与允许差异

独立子审确认runtime freeze 909条路径唯一且909/909当前hash匹配；原round06的880条绑定原样保留，新增29条。disabled snapshot与作者manifest相符；最终六源仅`generation_common.py`的`EXECUTION_ENABLED=False→True`发生允许单行变更，其余字节相同。协议仅status、registered_utc及三项observer费用发生allowlist允许的5字段变化。closed ledger与两份实际观测收据一致。

| 对象 | SHA256 |
|---|---|
| 最终runtime freeze | `d4ceea578897f81d0a7043040216965698ce19c0c16d422321259d7c76ea2388` |
| registered protocol | `6d4f9bfb6939bf4af5f94b0813c303f9aaa30617cb197b16605b7683b6d0ff87` |
| FINALIZATION_RECEIPT | `6c764b0fad1a332be0c6f1f2ba985e37cbe84df2802a608003cb056057714e14` |
| batch_receipt | `c83af7e09dac28b17c5ee7b38db9b903b57abd3ba46cc63911602ce96ebfb904` |

上述hash与outer/lock/batch中的关联一致。这里的收费封套覆盖已注册准备预留、等待观测和这一次科学launch；不宣称后续报告制作、分析及独审CPU也已包含在43.881044秒内。没有独立测量的准备与尾部仍是预留。本审查产物私有备份交root统一核验，本子审不声称BACKUP_OK；最终作者叙述若后续更新，由主审再核其措辞。
