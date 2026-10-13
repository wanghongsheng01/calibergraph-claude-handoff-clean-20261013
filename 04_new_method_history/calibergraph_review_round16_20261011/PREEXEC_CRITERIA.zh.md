# 第16轮独立执行前审查判据

审查者：`/root/round16_independent`。当前状态：`PENDING_FROZEN_AUTHOR_INPUTS`，不是执行许可或 preexec PASS。只读第15轮结论与既有源码，未运行、import、compile科学模块，未做能力或资源probe。

用户的新授权适用于新第16轮明确调度版本：每15分钟一次低成本资源观测，在当前任务内等待；不自动化、不抢unrelated_project、不放宽门限、不绕过真实拒绝。第15轮的停止及其24个未启动槽和第13轮的一次失败全部不变。

审查以冻结稿、源码与manifest为准，不以作者口头声明替代可核证据。

1. **调度与科学边界。** 观测只允许固定的低成本系统资源读数及自身记账，不加载科学运行时，不读取或求解SQL，不做Environment初始化，不借观测重复旧能力probe。未启动科学supervisor前，未通过资源门的观测不是科学attempt。原子取得永久一次性启动锁后，任何正式supervisor调用都消耗本轮唯一batch尝试；即使第一worker尚未启动而supervisor precheck失败，也不回到等待状态后重试。
2. **间隔与有效期。** 下一次观测必须距上次观测开始至少900秒，使用单调时钟核验，任务中断或重启不能将间隔归零。正式启动使用足够新鲜且可验证的合格观测，并保留supervisor原有逐槽资源门。门未知、收据缺失或格式异常不得视为通过。冻结时写定这些状态的处置。
3. **全部门。** load1≤4、free≥25%、单worker、nice≥15、原CPU/wall/RSS/solver限制和完整性检查共同成立；任何单项成功不能覆盖其他失败。只操作本任务拥有的进程，不停止、重排或提高unrelated_project等其他工作负载的优先级。
4. **预算。** 观测自身及已回收helper CPU、wall、状态、退出码和收据截尾分别保存；wait4明细不得再加到已含它的CHILDREN总账。等待的900秒wall不能写成900秒CPU。观测成本必须明确进入本轮parent60秒总预算，10秒准备和0.2秒尾部预留仍与实测值分列。若观测成本另加，剩余可执行总账相应减少；若它被定义为prep10的子账，必须写定可核的子预算与耗尽停止条件，不能以无限次观测声称总准备成本仍受10秒覆盖。
5. **停止与截尾。** 正式batch一旦开始，沿用原资源、监控、完整性停止规则；保留已运行槽的完整/部分收据、未知状态和未运行槽，不恢复、不补齐、不替换。普通query UNKNOWN按旧规则保存。缺最终收据时依靠证据区分NOT_RUN与UNKNOWN，不能由初始快照推断零科学操作。
6. **科学范围。** 同4个已暴露source、原SQL/schema/full operational C、exact2/3/4、两遍预定24槽与顺序不变；一次Environment/槽，不新增solver调用，原强解析对照与sanity标签保留。旧12槽、15未启动24槽与新16槽不合并为新独立样本。
7. **计时空值和早期准备费。** 未到达阶段必须为null/NOT_REACHED；开始但被硬停的阶段为censored/UNKNOWN。空集合sum不得伪造实测零值。protocol/source/freeze校验之前失败仍保留准备费；完整生命周期与嵌套phase不可双加。冻结审查只验证实现，不冒充运行时保障已经通过。
8. **可追溯性。** disabled作者manifest、注册启用差异、最终runtime freeze、唯一launch请求、outer time/exit、结果和独审各有独立哈希；旧15字节保持不变。真实自动审批拒绝立即停止本轮对应执行动作，不能换壳、降sandbox后再做同一动作。

资料根：`calibergraph_review_round15_preexec_20261011/REVIEW.zh.md`，`calibergraph_next_20261011_15/analysis/RESULTS.zh.md`，第15轮六源及草案协议。私有GitHub备份由root统一执行，本独审不单独宣称BACKUP_OK。
