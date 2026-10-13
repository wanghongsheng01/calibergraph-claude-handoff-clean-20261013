# 当前 N1/N2 实际回执审计

时间：2026-10-11T04:05:50.120190+00:00。本报告由实现代理只读审计，不冒称不同独立人类审稿；没有重新执行目标、native、solver 或 SQLite。已有不同 AI 静审另见 `INDEPENDENT_STATIC_REVIEW.*`。

两份实际回执均绑定当前 manifest `32ee11faea4fee939964cd4ae03a9435d2ebe35877cecd221d7e65b2da30f3dd`、v4 runtime lock `29220d333a6a3f9812ab2c24aecd7877f7cf5c9e919e80b612f880bf1dc92f1f`。12 个冻结文件哈希仍一致。两个 supervisor 均 exit 0、无 stop_reason；worker 均 COMPLETE_REGISTERED_DIAGNOSTIC 且 cleanup COMPLETE。

| 项目 | N1 | N2 |
|---|---|---|
| 原顺序 vs 旧编码 XOR | SAT，A=6 | SAT，A=[0,0]（相反方向见证亦合法） |
| 规范化 vs 原顺序参考 XOR | UNSAT | UNSAT |
| base-only SAT / 不可删除基行 | SAT / UNSAT | SAT / UNSAT |
| 固定数据库 | 4/4 EVALUATED | 6/6 EVALUATED |
| 原合同下实际 SQL pair 见证 | A=[6]，NULL / 6 | A=[6,6]，NULL / 12 |
| supervisor child 墙钟 / CPU | 1.618619875 s / 1.483474 s | 1.532590959 s / 1.385889 s |
| worker ru_maxrss | 108986368 B | 112214016 B |

读取固定值独立计算 `v != NULL and 5 < v` 与旧 `v < 5`，10 个数据库的原/参考/规范化真值全部对应；读取两个实际 witness 独立计算原 SQL 的空 SUM 与完整 SUM，也与记录的 SQLite 全关系相符。未重跑 SQLite，不把这一步称为第二次数据库执行。

当前审计只覆盖 **2/34 个注册 case**；其余 **32 项没有这两份回执中的完成证据**，完整名单存 JSON。20 个显式 solver 检查槽均有决定结果，另有 2 次官方 analyze；不能把 analyze 内部求解次数补算为已知。3 个唯一 admission 回归各重复执行两次，不算 6 种新控制或 SQL 证明。

注意实际 `proc_pidinfo` 观察到每个 child 最多 2 个 OS 线程，而 Python checkpoint 为 1；只能称一个计算 child，不能宣称所有原生线程始终为 1。RSS 为软监测，墙钟与最终 checkpoint 的边界不构成完整工具生命周期硬保证。

此结果关闭两个特定方向正控的当前版本诊断。它不认证未运行 32 项，不等于正式六臂接线完成，不外推通用 raw-contract 无丢失性。外部 240 格旧截面的证据单独记录，不合并成当前版本覆盖率。
