# statusfix supervisor 14 槽实际集成独立复核

结论：**本次注册的 14 槽日志/监督器集成修复有实际回执支持**。全部 14 槽已回收，无资源/观察异常，cleanup 均 COMPLETE；另 10 个未选中槽完整保留初始 NOT_RUN，未产生 job 目录。本轮没有运行任何 target、native、solver 或 SQLite；只做原始回执、854 个锁定文件、六源哈希与独立整数算术核验。复核者为不同 AI，非真人评阅；早期窄参考模块参与编写的边界继续披露。

| 实际结果 | 槽数 | 工作状态 | child exit |
|---|---:|---|---:|
| SAT | 1 | RETURNED | 0 |
| 查询 UNSAT | 6 | RETURNED | 0 |
| 合同 UNSAT 拒绝 | 6 | NOT_RUN_CONTRACT_STOP | 2 |
| 不支持的完整合同 | 1 | NOT_RUN_CONTRACT_STOP | 2 |
| 未选择 | 10 | 原始 NOT_RUN | 未运行 |

13 个支持合同槽均有 base SAT 与 normalized/reference XOR UNSAT 回执；其中 7 个合同可满足、6 个合同不可满足。唯一不支持 OR 的槽在整体合同门停止，没有部分编译、查询或 fallback。7 个正常查询的 RETURNED 回执早于 cleanup；7 个 typed stop 无 QUERY_WORK_BEGIN，supervisor 原样传播全部工作状态与回执。正常/typed 各 7 槽 child exit0/2，supervisor exit2 是这一注册负控的预期，不能改写为全零退出或全部查询成功。

唯一 SAT 是 D01 canonical 分支回退官方路径，完整数据库 T=[[6]]。独立按原始左右顺序计算 5<A 且 A<=6 为真；两条原 SQL 的值为 NULL 与 6。原始回执保留完整 SQLite 输出 [[[null]],[[6]]]，int64-domain 门通过，原合同和 SQL 身份一致。本复核只检查该真实回放回执并作独立算术计算，没有再次执行 SQLite。D02 的 canonical UNSAT 来自 AST identity shortcut，不能算一次 pair solver 证明。

资源观测（本次单独集成，不与旧 168 槽合并）：

- `supervisor_wall_seconds_before_final_write`: 18.63190387468785
- `max_full_child_wall_seconds`: 1.4928985419683158
- `max_full_child_cpu_seconds`: 1.385514
- `max_sampled_rss_bytes`: 118423552
- `max_worker_ru_maxrss_bytes`: 118685696
- `sampled_kernel_thread_counts`: [2]

RSS 为采样/软门，不能宣称持续硬 RSS 上限；OS 线程数按实际观测报告，不与 solver_threads=1 混同。监督器计时止于最后写入前，不是整个工具调用的精确墙时。

父任务回收回执 `c6f70a9942508dfee0d2f16136fd8086c2018830f17158e2a8412a278563c201` 的 session56495/exit2/报告路径与实际 supervisor SHA `ec1836bdab9b3f7980fb7a209a9a9d83bc1ddcd575e4b9e354633987197605de` 完全一致。READY 锁仍为 `16c76c134cdca4ef9461506968cecbbdb73ce6bc6304acdbeb7e878f19613d18`；suite 为 `84b1077a998a5cac1d05e6ad5631fc3f6b0f6a618f0e228402c2eb70c08f12e9`。检查结束再次核全部引用回执哈希未变；旧 `FINAL_V5_EXECUTION_CUT.json` 仍为 `1d6d0291fda36937a26da6b46c9d07b18899a21686708fa4279c7a814e48b95c`。

JSON 回执：`STATUSFIX_SUPERVISOR_EXECUTED_REVIEW.json`，SHA `7c8d23d8cfb0f2734051ca517c66880d1062eb3e3a7bb5724b6d3e8ad2829903`。逐槽原始路径/哈希、attempt/fallback、工作回执和资源均保留。

限制：此次只关闭正常返回和 typed stop 的日志/监督器传播，不覆盖 incomplete-receipt 故障注入、资源竞争或一般正确性证明。RETURNED 不等于科学正确；XOR 结果不是可携证明证书。此次既不新增独立科学样本，也不支持 selector 优势、泛化或投稿放行。
