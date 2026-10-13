# 固定自然 JOIN 四槽诊断：执行完成

本次按用户批准的资源合同执行完 #750/#319 × UA/precise，四槽合计墙钟 **2.249685 秒 / 60 秒预算**。共4个全新Python worker、7次Z3调用，父程序持有的11个句柄全部回收；没有科学重试、换例或扩大预算。先前NOT_RUN批次未改写。本次是两例开发诊断，不能冒称独立最终测试或新的方法贡献。

| 固定案例 | 模式 | 结果 | 原SQL回放 gold / predicted | Z3调用次数 | 槽墙钟秒 |
|---|---|---|---|---:|---:|
| superhero #750 | UA | 已验证NEQ | NULL / -54.0 | 2 | 0.816278 |
| superhero #750 | precise | 已验证NEQ | -55.0 / NULL | 1 | 0.587529 |
| toxicology #319 | UA | 有界符号UNSAT | 无见证，不运行回放 | 3 | 0.434618 |
| toxicology #319 | precise | 有界符号UNSAT | 无见证，不运行回放 | 1 | 0.409159 |

四槽全部进入解析、编码和求解。分母4：NEQ经回放验证2，有界符号UNSAT2，unknown/unsupported/timeout/error/非法见证均0。#319 UA的中间调用为SAT→UNSAT→UNSAT，这是固定一次槽尝试内算法的搜索过程，不能把第一个SAT当最终反例，也不属于科学重试。#750 UA两次SAT，precise一次SAT；#319 precise一次UNSAT。原生求解记录、生成公式和原始返回均保存在science_run_01。

## 约束与类型语义

完整C确实执行：#750的10表31列、#319的4表11列全部保留，共12个主键声明、13个显式NOT NULL和16条外键（41项显式约束）。schema将所有原列按顺序放Others，PK/NN/FK通过显式primary/not_null/eq入口编码，未丢弃无关表、补业务事实或篡改原SQL。完整固定源码核对确认：FK编码中的辅助env.integrity_constraints表非空条件沿原程序未追加进公式，未偷偷强化nullable FK。

两份#750见证均逐表插入**原DDL**，全部原列、每表1行；SQLite开启外键，完成插入后foreign_key_check为空、提交成功，原SQL回放结果确有差异。独立任务另写SQLite审核器，逆向核对DDL/库存并分别回放两份保存见证，得出同样结果。没有修补、截断、替换或再搜索见证。

见证中的负体重是**源DDL未禁止的合成值**，不是真实业务记录，也不宣称符合DDL之外的业务常识。若未来添加非负体重等新约束，属于另一个事先冻结的问题，不能在本次结果后偷换C。

类型准入只支持当前生成→逐见证验证链：SMT无限Int、字符串hash、SQLite affinity/AVG数值表示不是完整同一值域。本次具体整数可存入SQLite且AVG准确表示，文本/NULL及PK/NN/FK在真实回放中合法，因此两条NEQ结论有具体有效数据库支撑。没有由此证明全类型域编码完备。

#319两条SQL字节相同，是已冻结的等价控制；本次solver结论仍记录为N=1、有界符号语义下的UNSAT，不将UNSAT泛化为任意大小/任意SQLite类型域的证明。SQL完全相同这一独立事实与控制结果一致。

## 资源授权、执行和成本

用户明确同意以Z3内部分配限制+总60秒工作截止替代此前无法取得的外部RSS覆盖。本次冻结每个Z3 `-memory:512`（512 MiB内部分配计数）和`-T:3`；Python父/worker各自保持1GiB自身RSS峰值采样停止。它不是整机或全进程树RSS硬限制，也不是所有Z3合计512MiB。未使用ps或另一API查询受限进程信息。

父程序直接创建所有worker和Z3，使用Unix域socket传递Z3管道FD，保留每个Popen对象并统一终止回收。4个新解释器避免跨槽缓存共用；固定PYTHONHASHSEED=0，未增加或重排算法随机调用。父OwnedCase单个60秒预算覆盖整个循环，各worker另有≤12秒工作停止；停止后清理宽限和Python信号的既有边界沿用已独审合同。本次未触发任何超时/内存停止，11个句柄均有退出状态，4个worker退出码0。

启动前共同owned.lock可独占且整个批次持有；新ATTEMPT_STARTED排他创建，核对无本任务重复作业。unrelated_project无训练依本次用户/父任务明确陈述，未操作unrelated_project或枚举其进程。准备时loadavg约2.55/2.77/3.00仅作记录，不当新负载门槛。旧输入/旧唯一尝试标记9项哈希未变。

| 案例/模式 | parse ms | 查询encode ms | solver调用累计 ms | replay ms |
|---|---:|---:|---:|---:|
| #750 UA | 259.280 | 6.660 | 37.949 | 7.412 |
| #750 precise | 207.095 | 2.368 | 9.068 | 0.909 |
| #319 UA | 205.677 | 1.800 | 27.145 | — |
| #319 precise | 206.663 | 5.564 | 8.527 | — |

完整导入、schema/C、parse、encode、search含solver、solver、decode、replay和槽墙钟在STAGES.csv/SUMMARY.json。search与solver时间嵌套，不可相加；solver列包括本次broker/管道调用开销，不能等同纯Z3内部时间。编码包含QueryEncoder initializer，schema/C构造另列。—表示未执行，不是0ms。

本次源提交固定为5e18237394d025dbb805cf833b4f54c321470774，补齐完整模块后，24项旧文本快照与tar原文件的区别仅末尾换行；SOURCE.json保留双哈希。串行覆盖三文件来自已独审11包。新隔离依赖版本及wheel哈希全部保存，不声称原官方依赖环境复现。准备阶段第一次metadata broker夹具暴露peer关闭的ConnectionResetError，修正后第二次版本夹具通过；这不涉及科学查询，原失败证据保留。

precise原始300秒改3秒、串行包装、进程broker和新冻结依赖均影响运行条件，因此本表只是本机本轮诊断成本，不是原baseline速度复现或统计性能比较。两个模式都解决阳性案例，等价控制也一致；UA分别用了2/3次调用、precise各1次，**没有支持UA或新机制优势的证据**。可支持的推进仅是：冻结自然JOIN案例在明确适配边界和已批准保护下能够端到端运行、产生可独立验证的合法反例。未提出新的科学机制结论。

独立最终审核见INDEPENDENT_REVIEW.zh.md，完整执行证据见science_run_01/及review_local/。无投稿、原稿修改或资源购买。
