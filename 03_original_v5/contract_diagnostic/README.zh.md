# literal-left IC 有界诊断

本目录准备了一次构造的合同诊断，尚未执行目标。它不估计自然缺陷发生率，不是 benchmark，不把实现问题宣称为新科学贡献。官方源、`runtime_fair_v4/common.py`、v3 运行锁和独立审阅 fixture 均只读复用。

`INPUT_REGISTRATION.json` 注册原 schema `T(A INT)`、恰一行、原文本 `5 < T.A`、原始 SQL 对及 24 个单元（六比较符 × A=6、4、NULL、5）。运行时通过真实 `ConstraintParser.parse` 取得保留操作数顺序的 wrapper AST。`eq` 是单独标明的 emitter-only 控制：该固定 parser 的 grammar 不支持 `=`，不能伪称它是 parser 输出。

执行顺序：

1. 复用 common 的锁加载、原始标识符 gate 和 exact-row guard。先保存无 IC 的全部基础事实，建立 A=6 和 A=4 两个完整固定模型。
2. 逐项调用官方 `add_constraints`，保存本次追加的原始事实。各 operator 的追加片段分别与基础事实比较，绝不把全部控制约束合取后求解。独立 Python evaluator 按原始二元 AST 的左右顺序取真值。
3. A=6、4 分别记录官方事实 model-eval 和 fixed-SMT。NULL 与边界 A=5 使用显式公式代入，不伪称另有固定模型求解。NULL 为 UNKNOWN，严格合同不把它计为 true；这不是 SQL CHECK 接受 UNKNOWN 的语义。
4. SQLite 执行未改写的两条 SQL，保存 A=6、4、NULL 的完整结果；A=6 预注册正控为 `[[NULL]]` 对 `[[6]]`。单行且绝对值至多 6，整数溢出不可能。没有调用 v3 不具备的通用 int64-audit API。
5. 另建新 Environment，真实 parser 产生原 lt IC，仅加入此 IC，再运行原 SQL pair 的官方 `analyze`。记录全部事实、实际 solver assertions 和 verdict。此 verdict 的合同是官方实际发出的 IC，不能把它当成已经忠实实现原 AST 的证据。

全部步骤在一个计算子进程内，CPU 软 14 秒、硬 15 秒，最多 19 次 solver check（含 guard），单 solver 线程。外部 supervisor 总墙时 alarm 24 秒，在 23 秒停止计算、预留回收与报告时间；每 0.05 秒采样 RSS，达到 1 GiB 或观测不可用即停止。RSS 是采样软限。临时上游 Python 监视线程单独记录，子脚本不创建子进程。

父任务按 `COMMAND.json` 中的 argv 实际启动。必须同时看到 supervisor 的 `result_valid=true`、子进程 exit 0 和 `COMPLETE_DIAGNOSTIC`，才可说诊断完整执行；完整执行本身不等于预期缺陷已证实，应读取每个事实对照。超时、unknown、错误、未运行单元均保留。不要复用或覆盖已存在的运行目录。

当前静态检查不导入或运行 worker、supervisor、第三方目标或 native 库。初始报告 `NOT_RUN_REPORT.json` 不是实验结果。

备份状态：`BACKUP_BLOCKED_BY_USER_NO_UPLOAD_NO_PUSH`。
