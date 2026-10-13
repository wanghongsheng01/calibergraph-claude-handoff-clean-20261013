# 一次有界运行方案（未执行）

仅冻结#1172原SQL/DDL、N=1、当前观察等价适配器，顺序UA→precise，各一次；不是旧1172未暴露test，不是原版Polygon性能复现。用户本轮要求先不调用科学求解器，FREEZE.solver_execution_authorized=false，准备worker执行门关闭。需要后续明确允许此两槽的新批次才可运行；不更改旧冻结批次。

复用13包父broker、OwnedCase句柄所有权和统一终止回收；全部新增科学槽共享60秒墙钟，每次Z3 -T:3、每个Z3内部-memory:512，逐worker至多12秒且受总deadline约束。512MiB不是总RSS限制。启动前核对共同owned.lock、机器负载与unrelated_project无训练状态；串行，不开队列。Hash固定runtime、native、依赖、原SQL/DDL及新adapter/worker；PYTHONHASHSEED=0，单线程环境。

正式执行前只需接入已审核13父broker的新批路径和本worker，不改变求解主体；同一新批必须另有不可重复attempt标记。当前文件准备的是worker小diff，不假装本轮已经创建或运行controller。计时保留imports、schema_C（包含约束盘点/适配构建）、parse、encode、search含solver、每次solver、decode、固定lift与原SQL replay、槽/批总墙钟；search/solver嵌套不相加。

保存每次SMT输入/状态、原始抽象见证和提升后的具体见证及其哈希。独立审计用原DDL/C/SQL回放具体见证，并核对它严格等于事前固定lift，禁止反例修补。分别报告validated_NEQ、有界symbolic_UNSAT、unknown、timeout、unsupported/error、无效/不区分见证；各有分母，失败不换例不重试，总预算到时余槽NOT_RUN。两模式都成功就保留强基线成功的负创新结论；适配本身不叫新机制。任一失败先定位语义/工程原因，不能直接称基线方法失败。
