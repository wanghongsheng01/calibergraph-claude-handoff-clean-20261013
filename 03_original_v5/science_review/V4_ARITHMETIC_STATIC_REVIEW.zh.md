# v4 算术与整数 oracle 域：独立静态审阅

审阅者 `/root/independent_review`，不同 AI agent，非真人评阅。只读完整 `runtime_v4/aggregate_kernel.py`（548 行）与 `SEMANTIC_DERIVATION.txt`（94 行），核对实现回执；随后按 runtime_guard 请求审查 `runtime_fair_v4` 相对已审 v3 fair 的增量。没有 import 目标、运行 SQL/solver/native、修改候选代码或重新执行既有诊断。

**结论：在文件声明的受限片段与 harness 前提下，本次未发现新增 P0/P1 阻塞缺陷。此结论是源码审查与条件推导，不是完整 SQL 实现正确性认证。新 fair v4 的增量也未发现执行阻塞，但其实际运行没有纳入本报告。**

冻结输入：

- `aggregate_kernel.py` SHA-256 `17f652323839f0395e3224e5d82f646c143f34ff8245fb4d798724d3d7b9fa78`。
- `SEMANTIC_DERIVATION.txt` SHA-256 `f85ea5ce23093845c68230cb7b92538f946fef57db2623248bc16554290b3a7e`。

## 已逐项检查

| 部分 | 源码位置 | 静态判断 |
|---|---|---|
| root-only 表达式识别 | 192–214、229–234 | 接收整数/根列、n-ary add/mul、binary sub、unary neg/pos；拒绝 leaf 依赖。不是任意 SQL 算术。 |
| strict NULL | 308–327 | 递归 NULL bit 为操作数 NULL 的析取；NULL 下 value 任意但不会贡献 SUM/COUNT。 |
| COUNT(expr) 与空 SUM | 360–393 | `contributes = root_ok AND NOT arg_null`；非 NULL 零值仍计数。SUM 的 NULLness 由非 NULL 连接行数为零决定，不由数值和是否为零决定。 |
| BETWEEN | 242–246、329–343 | 三个 column/int 操作数均非 NULL，且两个含端点比较成立时才选入；同 root/single-leaf 路由，反向区间不选入。 |
| multiplicity | 375–387 | 每 leaf 精确计数依赖共享实际元组；selector 使用每 leaf 自己的界，没有引入自由 count 或删 IC。 |
| NIA 边界 | 76–82、289–293、derivation 46–54 | variable-product 是保守语法标记；完整公式标为 NOT_CLASSIFIED。正确地没有声称 selector 消除 root measure/IC 的所有非线性。 |
| 具体 SQLite 域 | 403–548 | 检查全 schema、所有非 NULL base cells、表达式子树及聚合。TRUE 选择语义与 NULLness 保持；未知保留，不负责证明 SQL 正确性。 |

以下为**按源码手工推导的边界输入，不是本审阅者执行所得结果**：

1. `X=NULL` 时 `X*0` 与 `X-X` 仍 NULL；该行对 COUNT(expr) 贡献 0，对 SUM 不贡献。若所有行如此，SUM 为 NULL。`X=0` 且非 NULL 时，COUNT(X) 与 COUNT(X*0) 均计入；SUM 可为非 NULL 的 0。
2. 一条 root 的 `X=Y=-2147483648`，两条同键 leaf：`SUM(X*Y)` 的数学值是 `2^63`。每个 root product `2^62` 尚可表示；域检查把 positive_sum 累计到 `2^63`，在 535–536 行返回 UNKNOWN_ORACLE_DOMAIN。没有只检查输入 INT32 就错误放行。
3. `X*Y*Z*0` 中 `X=Y=-2147483648, Z=2`：最终数学值 0 不能掩盖某个括号/运算顺序中的溢出。449–455 行忽略零因子的捷径，非零因子绝对值乘积达到 `2^63`，保守拒绝。
4. 聚合的正负值最终抵消为小数值，不会绕过 535 行的正和/负和分开检查。因此任意行顺序的可能中间溢出不会被最终和掩盖。
5. `X BETWEEN L AND U` 若任一操作数 NULL，则筛选不是 TRUE；`L>U` 时也无 TRUE 行。连接为空时，COUNT 是 0，SUM 是 NULL，即使物理基表各有正数行。

addition 的正项和/负项和界、multiplication 的非零绝对值总积界，对纯整数运算是保守的子集/括号界；可能拒绝实际顺序安全的情况，但没有把这种保守拒绝冒称方法失败。乘法用 `2^63-1` 作为绝对值上界会连部分合法负端点也拒绝，是允许的保守性，不是 false-safe。

## 接受实际结果前仍必须满足的条件

1. helper 消费候选 plan，故只是 oracle 数值域检查，不能替代对原始 SQL 的独立 SQLite 执行。已知共同前端风险的 raw gate 必须继续先于 parse/判等；本次没有重证整个 parser 的语义。
2. 新 fair v4 必须对 official、各候选及 per-query differential 的每个 SAT witness 统一做对应 query 的域检查，并检查真实 SQLite 标量类型；只有 SAFE 才可解释为数学整数域 witness。unsupported/overflow/error 都保留原 DB、全分母和成本。文档 72–82 行已准确要求，旧 fair 不应直接用于接受 v4 算术 SAT。
3. 上述 helper 只检查具体 witness，不证明任意数据库都无溢出。UNSAT 仍是在声明的数学整数/verifier 模型内解释，不能自动升级为任意有限整数 SQL 引擎的全域保证。
4. 全部原始 IC、exact-N 与共享元组保留，fresh prefix/有序定义由 harness 保证；本报告没有重新运行这些 harness 门控。cheap-canonical-AND 第六臂的静态增量范围见下节。
5. `COUNT(e)` 可能只需要 e 的 NULLness，语法上有乘法不等于最终 COUNT 公式一定有该乘法；当前 flag 只是保守语法标记，不能据它统计实际 NIA 公式。实际公式理论、编码规模与成本应直接测量。

## new fair v4 增量只读检查

以下四个实际文件 hash 已核对：common `035f30492e9fc2f9a46247da0b7a35f5ecc645323f7b3aaec7a1b8a63d1a78e8`；worker `5baf3d5719db583abfc58553392ab4e711ee1c37ca8e0bdc1217dabd8f52efc1`；supervisor `c4bf0a1500198c3e709de8f2baa8eb6743fdca49e965cd7a9368590894c96479`；query_differential `da18141d16395d94c87c4f6b1b9bb1229290b7fd856b5683f5c1d103feffd74e`（差分模块与已审 v3 相同）。

- official、candidate、per-query differential 的 SAT witness 都调用 `guarded_replay`。域不安全/未识别/错误时不执行 SQLite，也不保留成一次成功 sat。SQLite 异常、非一行一列、非整数且非 NULL 的输出均显式报错。候选数学诊断值与原 SQL 不同也显式报错；由于这个检查在二者归因之前，不会继续填写“哪个编码与 SQLite 相同”，但原 SQLite relations 已保留，可追查。这是诊断分类边界，不是错误通过。
- 第六臂要求共同 raw gate 与 v4 recognizer 通过，之后仅递归排序 AND 操作数，所有别的 AST 成分保持。相同 AST 的判定依据是纯片段三值 AND 交换律；不同 AST/片段不适用按剩余预算回退完整 official，阶段成本与错误保留。没有附带 COUNT 消表达式或其他未审 rewrite。该控制不能替代 aggregate pushdown、join elimination 或 IC 推导优化。
- `verifier_semantics` 记录实际 wrapper 身份及锁定源中 run 的构造器集合。其“静态 dispatch 而非观测到函数局部实例”的表述准确；没有据 scalar 结果相同把 SpotIt set 语义称为 bag 语义。
- 新增接线源码符合上述要求，但没有在本审阅中执行。首次真实结果仍需逐项核实状态、完整分母、所有 fallback/unknown 及域拒绝，不能直接承接旧 v3 运行结论。

N4 新增 unknown 及其他失败须原样保留。本审阅没有重读其运行回执、没有把 same-expected 当作一般正确性，也没有产生新的性能/泛化/新颖性结论。作者今日 DKE 主线保持；这些局部静态通过不等于论文科学验收通过。
