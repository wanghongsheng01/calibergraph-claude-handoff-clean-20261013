# 独立科学审核：原 speculate on/off 方案

日期：2026-10-12 UTC。角色：与作者分离的静态审核者。先独立阅读 `PRIOR_PLAN_FROZEN.zh.md`，再逐项对照冻结官方实现及两份既有成功记录；未执行科学代码、实验、编译或安装，未改旧源、正文及包。

**结论：建议本轮零实验。** 原方案可回答“这个已知成功单例，在指定预算与观测策略下，打开 speculation 的总影响是什么”，不能决定下一条新方法方向。已有 50 来源仅 1 个合法执行、强基线成功、49 NOT_RUN；独立新 test=0、共同支持机制失败=0。无论两臂出现哪种结果，都不产生一个新的、已准入且未被强基线解决的问题。因此应保留 NO_INNOVATION_EVIDENCE / HOLD。可选的两臂运行应降为基线学习，不应列作当前必须完成的关键实验。

## 原方案判断

1. **完整 C 必要，但不足以识别机制。** Discourse 的五列、int32、3 NN、1 PK、2 NULLS DISTINCT UK、原参数 4076、完整 typed bag、后端版本/方言/默认值校准及独立复放使该数据库状态反例有效。它不证明应用可达性、历史部署或用户可见故障。两种列序的 UK 都须保留，但在此单表上不代表两个独立科学难题。本例无 FK，不能评判 FK 闭包改进。
2. **已有成功的可解释部分已经很窄。** SQL 对为同一投影与筛选的 DISTINCT 开关；匹配行的非 NULL `child_theme_id` 受复合 UK 限制，两个匹配 NULL 则合法并形成袋差异。旧记录从五行的单个匹配 NULL 到六行的两个匹配 NULL，在新库得到 `[3,7,NULL]` 对 `[3,7,NULL,NULL]`。记录与调用顺序支持“speculation 种子之后，concolic 接受新版本并分离”。旧日志同时记录 2 次 Z3 check（UNSAT 1/SAT 1）与 1 次 accepted SAT attempt；逐次 check 的阶段归属、调用栈及 UNSAT 具体来源未记录，不能推为两个独立目标，也不能仅从聚合计数断言两次都发生在该 attempt 内。
3. **on/off 是整包开关。** `Session.speculate()` 的 False 分支返回空库；True 改变初始行、已有值、覆盖集合、后续目标/约束、求解负担及剩余时间。完整 C 固定排除了合法域被放宽，但没有把这些中介逐个固定。因此可观察配置总效应，不能区分取样、种子建设、覆盖保护、provider 取值或求解器交互各自的因果贡献。
4. **同 seed 只提高复现性。** seed 传入 Speculator 的 RNG；False 路径不走它，sequential provider 又取决于已有值集合；Z3 的重启 seed 在 `_z3` 内另定。相同 seed 不是共同随机数意义下的逐事件或逐候选配对。同第 n 个候选也不是同一搜索状态。

## Must-fix：若作者仍保留可选诊断

- **先固定估计对象与导向。** 旧 `disprove` 可先后生成 before、after，各自有 generation deadline；不能把它写作整个 arm 仅一次生成或总计五秒。若新方案固定 before、各 arm 只 `generate` 一次、同一回调比较两条 SQL，必须注明它只测这个导向的配置诊断，不测完整官方 `disprove` 效能。旧 True 运行只能作历史参照，不能代替同包装的新 True 臂。
- **资源口径覆盖真实工作。** `solve` 包含完整性闭包、分量拆分、CSP、翻译及可能的 Z3；speculation 内也可调用它。CSP 的 BRANCHES=256、CASE_SPLITS=16、NORMALIZED=10000 是工作量界，不是 500ms 时间界；500ms 也不是整个 `solve` 或整个 arm 的上限。Z3 每个分量独立执行 `_z3`，偏好释放可产生多次 check。32 check 不是 32 个求解目标。五秒 deadline 在 `Session.run` 开始设置，排除了之前 Session 构造/首次 lowering；之后回调耗时进入 deadline，检查是合作式而非绝对硬中断。必须分列端到端 wall、Python worker CPU/RSS、CSP/SMT/内部执行/后端/追踪时间，避免重复相加嵌套计时。`time.process_time`、RUSAGE_SELF 与现有 CPU/RSS 门不包含独立 PostgreSQL 进程；若不能测后端 CPU/RSS，明确记为未测，不能称总 CPU/内存。所有超时、预算停止、不支持及准入错误保留。
- **候选与终点必须分层。** 内部 speculative batch、保留后的 seed、concolic 接受版本、on_instance 事件、后端 load、fresh replay 不是一个计数。需要 arm/run/stage/event/parent 标识、schema/typed ordered D hash 与保留重数的 bag hash；零重数符号槽位、覆盖/目标、求解事件另关联。相同物化 D hash 不等于相同搜索状态。首个合法非空/NEQ 的主终点限于已暴露候选且后端确认；内部未暴露批次的首个 NEQ 未知。不能为了补轨迹而给每个内部 batch 新加 SQL 对重放，否则改变官方候选暴露策略。旧 8 load 与 64 行门主要约束外部物化候选，不应声称约束了全部内部批次/槽位。
- **追踪本身也是预算成本。** 两臂相同包装不代表相同开销，因为事件数不同；必须计入总成本，不额外消费 RNG/改变返回值/重放内部候选。单次、固定执行次序的 wall 差异不支持稳健速度排名。不要因负结果追加 seed、阈值、导向或执行次数。

## 任一结果能够支持的分支

| True / False | 本例可支持的最强结论 | 后续科学决策 |
|---|---|---|
| 成功 / 成功 | speculation 对本例在该固定协议中并非必需；记录观测成本和行数即可。 | 停止该诊断；没有新方法需求。 |
| 成功 / 未成功 | 种子与后续搜索的组合在该预算下有贡献；未成功须区分预算、未知及有效穷尽。 | 最多保留“种子是否降低本例后续搜索成本”的描述性疑问；不能宣称普遍必要或指向新算法。 |
| 未成功 / 成功 | 本例出现开关不利的观测反例，可提出“种子建设成本或搜索状态交互”疑问。 | 不能证明覆盖保护、固定行或某个 provider 导致阻塞，也不能据此启动松保护方法。 |
| 未成功 / 未成功 | 当前协议未复现旧成功，或两臂均受预算/观测限制。 | 先停止；核查协议、追踪与旧成功的差别，不能把已解决单例改称强基线机制失败。 |
| 任一非法 C、后端错误、不支持或资源门未过 | 对应准入/执行/支持/资源状态。 | 停止方法比较，不把它折算为另一臂的机制胜利。 |

所有“未成功”均非 EQ/UNSAT 证明。两臂间的数量或耗时差也不改变新 test=0。若未来要恢复方法研究，所缺的是一个完整契约、共同支持、有效参照下仍未解决的真实问题及可证伪改进假说；当前不能由 49 个 NOT_RUN 代填。

## 建议与证据定位

建议不执行这项诊断；若仅为学习基线而保留，最多是修正上述口径后的同一个条件性两臂诊断，不追加另一实验。GitLab #47 的 45 行首候选、0 Z3 check、1 callback 证实合法非空与复放，并不证实没有 CSP/求解器工作、全覆盖或找到 NEQ；该任务没有已知合法 NEQ，不能当作失败支撑。

本结论基于本地静态证据：官方 `generator/generate.py`（GenerationConfig、Session.speculate、requirements、_attempt、run）、`smt/solve.py`（solve、_z3、_check_minimal）、`smt/csp.py`（界限与 search）、`speculate/speculate.py`（run、_evaluate、_solve、_sample）、`main.py`（disprove）；以及 `calibergraph_real_task_screen_20261011_05/implementation/{baseline_worker.py,discourse3_case.py}` 和 `runs/baseline_01/RESULT.json`、`calibergraph_parseval_admission_20261011_04/implementation/probe_worker_replay_supplement.py` 和 `runs/replay_supplement_01/RESULT.json`。官方源码根为 `calibergraph_parseval_admission_20261011_03/sources_local/parseval_official/src/parseval/`。本次没有重新验证历史执行或重新认证上游 commit。

## 作者新决策稿：一次复核

已静态阅读 `DECISION.zh.md` 与 `EVIDENCE_AND_RECOVERY.json` 一次。**科学决策通过；有一处归属表述须修正。** 新稿明确推荐 0 个下一实验、条件性 on/off 仅用于基线学习且尚未冻结/实现/执行、固定 before 不代表完整 disprove、任何分支均不使研究晋级，符合上述独立判断。

保存的六行数据确实保留五行数据为前缀，二者 fullC pass，且最终 NEQ 在新库确认。因此“本例必须删除/改写这份种子才能找到合法反例”这一必要性命题已有反证；这不等于种子在所有任务都无代价，也不排除其在某预算下影响效率。

唯一 must-fix：新稿表格中“两次 Z3 check 对应旧日志中的一次 accepted SAT attempt”应改成“旧日志同时记录 2 次 Z3 check（UNSAT 1/SAT 1）与 1 次 accepted SAT attempt；逐次 check 的归属及 UNSAT 具体来源未记录，不能按两个目标解释”。旧 worker 只全局包裹 `z3.Solver.check`；统计并存不是调用链证据。原独立稿中同样容易过度归属的表述也已在本次写稿内纠正。

另建议把“500ms 按各 Z3 分量/重启使用”写明为每个 `_z3` 分量在最多 4 次重启间分配预算（默认每次约 125ms），不包含 CSP、闭包及翻译；不能读作每次重启各有 500ms。此建议不改变零实验结论。

本次复核未授权任何实验、未将条件方案升级为可执行协议。修改由作者负责；不再循环审核。备份与提交由根任务统一处理。

作者随后通过消息确认已按建议机械修正上述归属句与 500ms 说明；这是作者修正回执，不是第二次独立审核。本审核结论保持“科学决策通过；唯一文字条件由作者报告已落实”。
