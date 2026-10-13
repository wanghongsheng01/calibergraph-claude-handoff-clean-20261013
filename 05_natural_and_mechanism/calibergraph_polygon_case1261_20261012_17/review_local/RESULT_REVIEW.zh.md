# #1261 一次运行独立后审

结论：**PASS，无必须修复项**。只核对既有原始记录和SMT公式，未启动或重跑solver。

唯一science_run_01批次总墙钟1.3229526248760521秒，固定UA→precise两槽各一次，均BOUNDED_SYMBOLIC_UNSAT。UA槽0.9519907077774405秒，内部调用SAT/UNSAT/UNSAT；precise槽0.36981416679918766秒，一次UNSAT。这些是同一次科学槽内的搜索过程，不是重试科学批次。

UA初始formula_0只有project$3、project$7两个operator约束，尚未加入三个inner_join及两个filter约束；完整IC、scan、neq存在并不使部分operator编码成为完整查询语义。其SAT只被用于内部choice选择和继续搜索，不是有效SQL反例。后续完整operator加入后的formula_1及回溯formula_2均记录UNSAT。precise一次完整式记录UNSAT。此解释来自实际formula labels与冻结search/backtrack/solve_precise代码，而非把任意SAT忽略。

四个实际SMT公式的IC逐字节相同，共七个顶层约束，与两PK、三NN、两FK一致；检查了基表0/1/2 ID关联及Patient.ID/Lab.ID/Date非NULL条款。运行schema_C报告3表64列完整保留。356个冻结文件与360个旧保全文件全通过哈希核验，ATTEMPT_STARTED引用当前FREEZE hash并标记no_retries。

两个RESULT均无协议错误，raw_return的见证位置为NULL，decode/replay计时为NULL，目录没有abstract_witness或witness文件。因此没有具体反例，也没有实际运行见证解码/回放；不能把先前单元测试写成这次UNSAT的回放。

两个worker返回0，四个Z3均使用`--in -T:3 -memory:512`。6个owned句柄全部wait回收、cleanup_errors为空，UA全部回收发生在precise worker启动之前。Z3返回-15对应broker在结果读完、worker正常退出后终止保留的交互进程；无stderr/协议异常。UA三个Z3可同时存活并空闲等待槽末清理，调用串行不意味着任何时刻仅一个Z3进程。512MiB只为单Z3内部计数，非总RSS上限。

允许报告：冻结#1261、每表N≤1、完整C及已审核局部观察商下，两模式均为有界symbolic UNSAT。不得扩写为无限界通用等价、未改造baseline通用类型支持、anti-masking新机制证据或新分母。本后审是静态/日志/公式核对，不是第二次求解或证明证书验证。

机器可读逐文件hash、公式labels、阶段时间与清理证据见RESULT_REVIEW.json。
