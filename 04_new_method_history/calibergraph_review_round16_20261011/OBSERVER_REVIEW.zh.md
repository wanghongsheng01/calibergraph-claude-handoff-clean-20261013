# 第16轮等待观测器独立静态审查

结论：**PASS_OBSERVER_STATIC_ONLY**。只允许root依已冻结调度发出具体受审的低成本资源观测请求；这不是科学source的preexec PASS，也不是实际资源、系统调用或运行环境已通过的证据。

主审：`/root/round16_independent`；预算子审：`/root/round16_independent/wait_budget_criteria`。两者都只读文本、JSON、hash和AST，未执行或import observer/科学源码，未probe、SQL、SMT、提权请求或改作者文件。

核对的冻结输入：

- `WAITING_RULES.zh.md`：`10044dcd309b0c480693c6b7185d7dfaeaadd46bfc838888682405ceee239f5d`
- `resource_observer.py`：`d1b3df4ce504b3496e4a873f1fe33e6a192f8f22a201e864089493779af61894`
- `waiting_schedule.json`：`ac48f60868e24805456c1978c09b5c2db240e31bd7fdceab9220482e1294be12`

三项与`OBSERVER_STATIC_FREEZE.json`逐项相符。AST语法可解析；仅stdlib和一次`/usr/bin/memory_pressure -Q` helper，无SQL、Environment、SMT、科学输入、网络或科学launch路径。nice/RLIMIT设置是observer本身的保护，不将它描述为重复旧15的能力probe；旧13、15停止记录保持。

已复核root对规则文字的计费澄清：receipt前样本不是完整实测，1.2秒不是树级硬上界，早期/外层失败停止等待。规则原hash `4a3e44300af18c4c17c711d3990f3ddab25732498c3b8da02b04575ca02ba591`已由上述现hash替代；observer源码和schedule JSON字节不变。本结论针对现三件冻结。

首次unix时间对应2026-10-11 16:45:00 UTC。以后实际开始时wall和monotonic均须距上次开始至少900秒，没有补跑循环。观测目录连续性、历史status和schedule hash都检查；历史只允许WAIT_RESOURCE/ELIGIBLE，STOP收据、缺收据、batch once-lock或runs目录均拒绝下一次观测。平台、解释器flags、nice、CPU limit、load与memory解析异常不冒充资源繁忙。只有load1≤4且free≥25得到ELIGIBLE。过期且尚无科学启动的ELIGIBLE可在下一900秒门后观测；这不允许科学batch重启。

SELF与全部reaped CHILDREN只相加一次；每次`sample + tail0.2`持久累计，下一观测先校验`10 + prior_observation_charge + 1.2 ≤ 50`，完成后再校验总账。等待wall与CPU分列。科学阶段仍需让累计observer charge实际进入50/56/60门，待six-source冻结后另外核验，不能只写进报告。

必须保留的边界解释与root外层职责：

1. **CPU1仅为observer SELF限额。** helper继承CPU限额但其CPU另计，所以1.2秒不是整个进程树的严格CPU上界。后置核账能拒绝超门后的科学启动，不构成树级硬上界证明；若超门、超时或收据不完整，停止。本结论不声称sampler的RSS/wall或尾部预留是kernel硬限保障。
2. **实测为receipt前样本。** 它包含解释器到采样点的SELF及已回收helper，未覆盖最后写JSON/打印/退出；0.2秒是保守预留，不是实测。不得称“完整实测CPU”。外层time/exit用于完整性与生命周期交叉检查，不能和已覆盖的内部CPU重复相加。
3. **早期失败必须由root永久停止。** 源码9–53行的限额、历史文件、间隔等失败可能发生在receipt创建前；hard kill也可能没有最终receipt。root须保留外层exit/stdout/stderr及已产生文件；任何真实权限、syscall、监控、完整性、非零退出、审批拒绝或缺收据错误均结束本轮等待，不能因obs目录未出现而再调用。只有有效完整WAIT_RESOURCE或过期ELIGIBLE允许按900秒继续。
4. **ELIGIBLE只准入候选。** 最终科学请求须在该观测完成后60秒内提交；这不保证审批后实际执行也在60秒内。真正执行仍由supervisor逐槽fresh资源门守护，全部科学源码、protocol、runtime freeze与独审也须先完成。一次科学supervisor请求/永久锁消耗唯一batch，后续不回等待。

私有备份由root统一负责。本文件与后续科学preexec报告必须分开引用。
