# 新贡献判断与两个有限切口

**当前结论：没有已验证的新方法贡献。** 现有 factorization、tuple multiplicity、finite-domain selector、IC 下等价验证、反例重放及一般 conflict/constraint guidance 都不能单独作为新意。此处不建议另造术语。父任务提供的 Polygon（PLDI 2025，arXiv:2504.06542）冲突引导反例搜索先验必须纳入比较；本轮没有新查全文，不能声称全面超越它。SpotIt 仅保留已有版本/配置证据，不使用尚未核实的“分阶段”描述。

本人只读代码与保存结果；未运行目标。对当前 60 个不同 `(case_id, arm)` 成本槽重新读 JSON 计数：N2 为 30/30 有判定；N4 为 23 有判定、7 unknown；总计 35 unsat、18 sat、7 unknown。它们是暴露的构造 DEV，same-expected 不是一般正确性，未知不删除。公开旧 DEV 的零 join 适用及当前大语料未完成扫描，也不能支持广泛效用。

## 1. 方法根因：所有臂共享了未独立验证的合同含义

发现具体静态风险：原文 `5 < T.A` 的 producer 保留左右顺序，但 emitter 的 literal-left 分支生成 `A < 5`。这不是方向约定猜测：`parsers/constraint_parser.py:37–41,57–58,69–70,107` 明确给出 `[5,{value:T__A}]`；`environment.py:718–723` 却对列值先应用同一个 lt operator。固定一行 `A=6`，原合同成立、现有约束不成立；查询 `SUM(A) WHERE A<5` 与 `SUM(A)` 的原 SQL 结果应为 NULL 与 6。完整未执行 fixture 在 `IC_LITERAL_LEFT_STATIC_CASE.json`，含 A=6/4/NULL 三个控制、schema、exact-N、源 AST 与精确索引。

另一个源头：`ConstraintVisitor.unsupported`（66–67）返回 None，`constraints`（87–88）直接删除该节点；`parse_file`（148–156）的 unsupported flag 只在异常时置位。因此语法已识别的“不支持合同句”可能在没有异常的情况下消失。这里是源码路径判断，尚未运行或统计自然发生率。

现在的合同 SAT 门、保留全部已编译 IC/hash、全部方法一致、甚至 per-query 输出差分，都可能继承同一个错误合同。**缺少的是“原始合同意义没有被换掉”的保证。** 修一处比较、增加日志或返回 UNKNOWN 本身仍只是修复，不自动成为论文贡献。

## 2. 切口 A（优先）：可独立检查的合同保真桥

**目标保证：**在明确受限的合同语言、固定 schema/exact-N 下，每条原句有唯一来源 ID、类型、NULL 规则和完整编译覆盖；独立参考语义 `C_ref(B)` 与实际发给所有求解臂的 `C_emit(B)` 等价。不是重复“合同 SAT”。

最小首版只支持整数 literal/单列两向比较 `<,≤,>,≥,=,≠`、NOT NULL、常数闭区间、AND/OR；不支持的整句保留并阻止全合同声明。比较合同采用显式定义的 strict TRUE（NULL 不满足），不能冒充 SQL CHECK 的 UNKNOWN 容许语义。初版不混入 FK、日期、字符串或跨行依赖。

**实施物：**独立小型源句解析/类型检查与固定 DB evaluator（不得调用旧 parser/emitter）；源句跨度→规范节点→编译公式的 ledger；一个参考 SMT emitter 的规则归纳证明/小型证书检查。固定 DB evaluator 逐行直接按原顺序比较，所有行都须满足，NULL 拒绝；整句 AND/OR 按明确量化位置解释，未知节点报 UNSUPPORTED，不能默认为真。它是合同 oracle，不是 SQL 输出 oracle。

**核心检查：**令 `B_N` 为物理类型/基表精确行数约束，检查 `SAT(B_N ∧ (C_ref XOR C_emit))`。SAT 输出完整 DB，分别用独立 evaluator 与实际 emitter 核对；UNSAT 仅在参考编译规则已成立的子集内证明合同桥。再单独检查 `SAT(B_N ∧ C_ref)`，避免矛盾合同导致假等价。最终 SAT witness 除原 SQL 重放外，还须通过原合同 evaluator；可行但不同义的错误合同不能混成“不可行”。

**证伪与贡献门槛：**先执行已保存的方向正控及静默丢句控制，再扫描完整原始合同语料；保留未支持与无错合同。对照现有 VeriEQL/SpotIt IC 编译、仅 SAT/非空门、仅输出重放，以及本桥；评价真实识别的语义偏移、错误判断变化、桥覆盖率和总成本。若只修一个 operator 或只检出人为注入的例子，没有一般保真保证/独立来源问题证据，应写工程修复，不能称新科学贡献。合同翻译验证本身也不是凭空新概念，最终新颖性仍需具体已有方法对照。

## 3. 切口 B（次选）：官方编码对全部合法基础状态的覆盖证书

现有 `official_premise_sat` 只证 `∃B,A. C(B)∧G(B,A)`；而 encoder-relative UNSAT 不应靠 `G` 悄悄排除难输入。需要的新保证是 `∀B. C_ref(B) ⇒ ∃A. G(B,A)`，再比较输出。候选 fresh 整数定义已有无环审计；官方 Scope 辅助约束没有同等级证明。

**最小实现：**仅对已支持 inner-star/scalar 片段，从实际 Scope 公式提取有限 ground cell 的 fresh、无环、全定义方程，给每条规则标注源算子；验证所有非基础自由量都已定义。通过代换得到残余基础约束 `R(B)`，检查 `UNSAT(B_N∧C_ref∧¬R)`。只有提取和规则证书成立，才能用它证明覆盖；UF 应用别名、tuple-sort 身份、非定义约束、循环或不完备 guard 都不得假当独立 fresh 常数。无法消除的部分保留 COVERAGE_UNPROVED，而不是把一次 SAT 升级成全覆盖。

**可证伪实验：**对当前单表、连接、NULL/空聚合真实 Scope 输出，记录可证覆盖的比例、残余约束、完整反模型和时间；以“仅 premise SAT”“当前 encoder-relative 差分”为控制。一个人为排除 `A=6` 的辅助前提只是检测器正控，不能充当自然发现。若完整片段不能实际提取，或所有结果只是重复已有 total-definition 检查且没有新增可验证保证/问题识别，则该切口无独立贡献，今天不扩为大项目。

A 针对合同意义，B 针对编码可覆盖的数据库集合；两者都不是 Polygon 式反例搜索加速的别名。**建议先完成 A 的唯一正控和可复查参考子集，再决定是否值得实现 B。当前不能把任一提案写成已实现或已建立新颖性。**

## 4. 当前实现的精确范围与查询形态

以下路径均相对 `today_20261011`。列出的上游 handler 是代码接收面，不代表已经独立验证其全部语义。

| 层 | 当前实现索引与边界 |
|---|---|
| 原始合同文本 | `sources/verieql_v1/parsers/constraint_parser.py:101–124`：列 membership、NOT NULL、两向 comparison、unique、inc；部分已识别 unsupported 会被删。原始文字到完整合同覆盖尚未闭合。 |
| 编译合同 JSON | `environment.py:594–782`：primary（627）、foreign（646）、inc（657）、value/literal（669/671）、boolean/int/varchar/date（673–694）、比较（695）、AND/OR（751）、not_null（754）、in（757）、between（766）。这些算子名不能直接当作全部标准 SQL DDL 保证。当前 stress 的实际合同只含 null/空合同与 not_null；更广 handler 不由该实验认证。 |
| 外层输入契约 | `runtime_fair_v4/common.py:109–115,179–192`：完整物理 schema、全 INT、每表正 exact-N、全部给定 IC 原样加入。`guard:137–148` 检查 C 可满足及 `C∧∨deleted` 不可满足。不是 ≤N，也不是原始合同保真证明。 |
| SQL 子集 | `runtime_v4/aggregate_kernel.py:24–51,113–268`：安全 raw 名称；唯一物理表、无 self-join 的 root-star inner equijoin；单 scalar SUM/COUNT、root-only 整数 +,-,*、unary +/-；比较/NULL test/BETWEEN，AND，root+最多单 leaf；无 GROUP/DISTINCT/OR/outer/order/limit/cast/division。 |
| 候选 SMT | `worker.py:253–256`（fair v4）：`C_emit ∧ D1 ∧ D2 ∧ [n1≠n2 ∨ (¬n1∧¬n2∧v1≠v2)]`；D 为 flat/product/selector 定义，`kernel:271–393`。 |
| 官方 SMT | `sources/verieql_v1/verifiers/verifier.py:79–127` 与 `environment.py:942–952`：`¬(P ⇒ output_equal)`，即含 DBMS/IC、双方公式和 bounds 的 `P∧¬output_equal`。 |
| 单查询差分 | `runtime_fair_v4/query_differential.py:244–367`：C SAT；exact-N；官方 premise SAT；单 alive 输出；候选 fresh DAG；joint SAT；NULL/value mismatch。当前最后的 UNSAT 仍相对官方 premise，尚无 B 的全覆盖证明。 |
| 原 SQL oracle | `kernel:403–548` 与 `common.py:251–301`：具体 DB int64 安全门后原 SQL SQLite；不能替代原合同语义审查。 |

本轮不改稿、不改代码、不求解、不作新文献泛查。继续作者今日 DKE 主线，但目前只有具体可检验的研究切口，没有可承诺的科学突破。
