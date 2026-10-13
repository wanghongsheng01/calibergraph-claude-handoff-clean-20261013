# 条件授权执行合同

当前用户明确允许：非作者审核本例最小适配/新证明通过后，直接执行固定#1261 UA→precise各一次。仅此一例，不因结果换例或调参重试。首先冻结FIVE_CASE_SCREEN顺序和条件；实际代码独审PASS后才创建科学FREEZE和唯一ATTEMPT_STARTED，未PASS前不调用solver。

全部新增科学工作共享60秒墙钟，按13固定父broker/OwnedCase串行，每solver -T:3、每Z3 -memory:512；512MiB为单Z3内部计数，不是总RSS限制。沿用单worker≤12秒且受总deadline约束、全部自有Popen句柄统一回收。运行前核验输入/代码/依赖哈希与共同owned.lock并记录机器负载；不操作unrelated_project、不查询外部进程RSS、不启动队列。

schema_C包含新映射构建，记录imports/parse/encode/search/solver/decode/replay及总墙钟，嵌套阶段不相加。保留全部槽结果、unknown/timeout/error/非法见证；总预算耗尽余槽NOT_RUN，无重试。任何SAT最终反例必须在独立原DDL/原SQL回放合法且区分查询才接纳；有界UNSAT不能称原查询通用等价。所有五例均已暴露开发，不是独立测试。

本例无新SQL operator实现，仅改固定输入哈希与RF/Thrombosis观察类别。源schema和C相同不是复用1172证明的理由，新论证见PROOF。其他四例目前需要额外输出/算术/日期/标量子查询语义论证，不自动开发，更不将未准入叫强基线失败。anti-masking新机制假说保持关闭。
