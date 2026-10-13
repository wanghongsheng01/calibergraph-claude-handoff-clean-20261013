# 两个 INT pair 的成熟恒等式：逐式作者证明

结论：对原 `dev03_10 / 1264` 与 `dev03_15 / 1421`，在下述 INT/NULL、三值逻辑、无序 bag 语义下，两个查询对均可用现成规则直接证明对**任意有限输入 bag 等价**。两项证明均不需要原显式 C 中的任何一条。因而这两个来源的 SQL 等价问题已有强解析对照；不能仅因冻结 VeriEQL 在较大 exact bound 变慢就宣称发现新的语义困难或新机制。

这是作者手工推导，未机械检查、未作为程序化基线实现或计时，不是新算法。没有运行 SQL/SQLite/SMT、目标 import/compile、生成测试库或枚举数据库。未重扫全库、未改原 SQL、旧冻结目录或 `16/semantics`。本文件没有复制原始 SQL；源式绑定到原21 registry 的指定索引与 SQL 哈希。元数据和哈希与本文同目录。

## A. 证明对象与共同语义前提

| 对象 | 原21 registry index | 两条 SQL 的 UTF-8 SHA256 |
|---|---:|---|
| dev03_10 / 1264 | 9 | `d6f4e1268f13f698ca86b9079280ef9d56c18a1b8b815aacf0940f90a6303e26`；`c450dc8464a1717929aa7810c6be75b98c150efb82d16bde5a6eaa5f0da88fb5` |
| dev03_15 / 1421 | 14 | `f63915350c6d64ab99bfd7af8702a072da34476f8839a98f9c209753821f8c39`；`e8657124a5d7aea2a9e4648f69af0c916faefbb7eb429cefb979ebc36af306f7` |

读取对象为 `03/data/development_stratified.jsonl` 的这两个记录，全部物理字段均声明 INT。以下允许 INT 值及 NULL，允许输入重复行、空表和各表不同基数，暂不假设任何 PK/FK/数值限制。可取冻结工具的 INT32 子域；论证本身也适用于没有这些范围限制的纯整数域，且不含可能溢出的算术。

两边在同一个数据库快照、相同 schema/name resolution 下求值。采用普通 SQL `=` 和 AND/NOT 的三值逻辑；CASE 按原书写顺序选首个 TRUE 的 WHEN，FALSE/UNKNOWN 都不选；省略 ELSE 等价于 ELSE NULL。JOIN 的 ON 与 WHERE 都只接受 TRUE。输出比较采用 bag 值及重数，NULL 与 NULL 在计算“同一个输出值”的重数时算相同值，不能把这一身份关系混同于 SQL `NULL = NULL`。

采用原回放 profile 所需的内置函数语义：对 INT/NULL 的 `IFNULL(x,0)` 与二参数 `COALESCE(x,0)` 都返回首个非 NULL 参数。原表达式仅含列引用和整数字面量，没有易变函数、副作用、文本排序规则、混合类型转换或标量子查询。两对均无 ORDER BY，因此不主张输出物理顺序一致；这里也不认证驱动层结果类型元数据。若换成不满足这些前提的方言或重载函数，本证明不自动适用。

## B. dev03_10 / 1264

记 FRIENDSHIP 输入 bag 为 F，LIKES 输入 bag 为 L。以“行出现”区分两个值完全相同的重复行；以下求和与配对是数学语义定义，不是数据库枚举或执行。

### B1. 列绑定与别名消除

原左式的派生表别名 TB1 对应右式的 A；原左式 LIKES 别名 TB2 对应右式的 L。两派生表只输出 `USER_ID`，所以外层未限定的 `PAGE_ID` 在两式都唯一绑定到 LIKES.PAGE_ID。外层投影名都为 RECOMMENDED_PAGE。NOT IN 子查询内部的 PAGE_ID 和 USER_ID 均在内部 LIKES 上解析，无外层相关引用。

因此仅做语义上的别名对应后，剩下的差别是：派生 CASE 的显式/省略 ELSE NULL，以及内连接两侧和等式两端的书写顺序。没有把未限定字段错误地当作来自派生表，也没有改变子查询绑定。

### B2. CASE 逐行得到相同派生 bag

对每一个 FRIENDSHIP 行出现 f，记其两列值为 a、b。定义相同的函数

\[
c(f)=\begin{cases}
b,&(a=1)=\mathrm{TRUE};\\
a,&(a=1)\ne\mathrm{TRUE}\ \text{且}\ (b=1)=\mathrm{TRUE};\\
\mathrm{NULL},&\text{其余情况}.
\end{cases}
\]

两原式的 WHEN 顺序和 THEN 值完全相同；一个显式写 NULL 作为缺省值，另一个省略 ELSE 而由 CASE 语义返回 NULL。因此每个 f 的值和 NULL 状态都相同，且每个 f 都产生恰好一个派生行出现。

这一步不要求 a、b 非 NULL，也不要求 a≠b。若首分支为 TRUE 但 THEN 值是 NULL，两边都立即取该 NULL，不转去后续分支；若两个分支都可为 TRUE，两边都采用同一个首分支。派生结果重复 USER_ID 的重数也完全保留，因为派生 SELECT 没有 DISTINCT。

### B3. 内连接有逐行出现的双射

对 f∈F 与 l∈L，记 u(l) 为 LIKES.USER_ID、p(l) 为 LIKES.PAGE_ID。左式保留连接行出现 (f,l) 当且仅当

\[
j(f,l)\equiv [c(f)=u(l)]_{\mathrm{TRUE}}=1.
\]

右式的连接条件对调了等号两端。对 INT/NULL 普通相等是对称的，包括 UNKNOWN，因此右式保留 (l,f) 的条件相同。映射 (f,l)↔(l,f) 是两个连接结果之间的双射，且保留 p(l)。NULL USER_ID 不能通过普通相等连接；两边同时拒绝，不需要假设 NULL 不存在。

若多个 f 产生同一 c(f)，或 L 含重复行，双射仍按行出现逐份成立，因此连接重数没有被忽略。这里用的是内连接换序，未使用一般外连接换序规则。

### B4. 原样保留 NOT IN 的全部 NULL 行为

定义同一个子查询结果 bag

\[
S(L)=\biguplus_{l\in L:\,[u(l)=1]_{\mathrm{TRUE}}=1}\{p(l)\}.
\]

两原式的子查询相同，且与外层不相关，所以在同一快照上得到相同的 S。定义

\[
h(p,S)=[p\ \mathrm{NOT\ IN}\ S]_{\mathrm{TRUE}}.
\]

两边对应连接行带有相同的 p(l)，也使用相同的 S，故 h 完全相同。**没有把 NOT IN 改成 NOT EXISTS、普通反连接或二值逻辑**。即使 S 包含 NULL、p 为 NULL、S 为空，双方也逐行接受或拒绝相同项。更明确地说：存在 TRUE 相等时 NOT IN 为 FALSE；没有 TRUE 相等但有 UNKNOWN 比较时为 UNKNOWN；其余（包括空 S）为 TRUE。WHERE 只保留最后一种情况。这些情况只是解释保留同一函数为何足够，没有假设原 PK 先行排除了 NULL。

### B5. 投影和 DISTINCT 保留等价

对任意 PAGE_ID 输出值 v（可为 NULL），两边 DISTINCT 之前的重数同为

\[
m(v)=\sum_{f\in F}\sum_{l\in L}
j(f,l)\,h(p(l),S(L))\,[p(l)\equiv v],
\]

其中 ≡ 是输出值身份，含 NULL 身份，不是 SQL `=`。外层 SELECT DISTINCT 在两边都将正重数压成 1、零重数保留 0，即

\[
m_{Q_1}(v)=\mathbf 1[m(v)>0]=m_{Q_2}(v).
\]

所以不仅最终 DISTINCT 结果相同，去重前的投影 bag 也已相同。空 F、空 L、空 S、重复行与 NULL 均已包含在上述式子中；没有表基数限制。

### B6. 原 C 不参与证明

| 原 C | 是否必要 | 理由 |
|---|---|---|
| FRIENDSHIP 的复合 primary | 否 | CASE 与连接双射按行出现成立，允许重复和 NULL。 |
| LIKES 的复合 primary | 否 | 重复 LIKES 行逐份贡献，NOT IN 的同源子查询保持全部 NULL 行为。 |
| FRIENDSHIP 两列 operational neq（全笛卡尔比较） | 否 | 两式分支顺序一致；不依赖两列同行或全列不相等。 |

因此在原 schema 下，无显式 C 的 bag 语义已有 Q1≡Q2；把输入域限制为完整原 C 的模型只是取子集，等价仍成立。实验仍必须保持原 fullC，不能用证明不依赖 C 作为偷偷删除实验约束的理由。

## C. dev03_15 / 1421

记 QUERIES 的 bag 为 Q、NPV 的 bag 为 N。两原式均保留 QUERIES：左式是 Q LEFT JOIN N，右式是 N RIGHT JOIN Q。表别名仅影响名称绑定；最终列顺序均对应 QUERIES.ID、QUERIES.YEAR、填空后的 NPV 值。

### C1. 普通行相等与分量 AND

对每个 q∈Q、n∈N，左式 ON 条件为

\[
p_1(q,n)=(q.ID=n.ID)\land(q.YEAR=n.YEAR).
\]

右式先比较两个按 ID、YEAR 同序排列的行值：

\[
p_2(q,n)=(n.ID,n.YEAR)=(q.ID,q.YEAR).
\]

在这里采用的普通 SQL 行相等语义中，该式等于两分量普通相等的 AND；每个 INT/NULL 标量相等又满足对称性，所以 p2=p1，包括 UNKNOWN。两个分量都 TRUE 才为 TRUE；任何分量 FALSE 则为 FALSE；剩余情况为 UNKNOWN。这里没有把行相等解释为 NULL-safe equality。

对连接其实只需较弱且已由上述等式给出的事实：p1 为 TRUE 当且仅当 p2 为 TRUE。于是所有真正匹配的行对完全相同。含 NULL 的 ID/YEAR 不能产生普通相等的 TRUE 匹配，但不因此丢掉被保留侧的 q。

### C2. LEFT/RIGHT 保留侧反转建立相同连接 bag

对每一个 QUERIES 行出现 q，定义匹配 bag

\[
M(q)=\{n\in N\mid p_1(q,n)=\mathrm{TRUE}\},
\]

并保留其中每个 NPV 行的出现次数。

- M(q) 非空：两边都对其中每个 n 出现输出一个配对。写成 (q,n) 或 (n,q) 不影响按列名解析的值，且有逐出现双射。
- M(q) 为空：两边都为这个 q 输出恰好一个 NPV 侧补 NULL 的行。FALSE 与 UNKNOWN 都不计为匹配。

未匹配的 NPV 行在两边都不是需要保留的对象。因此两边保存的 QUERIES 行出现、匹配数量和补空数量完全相同。重复 q 按输入出现逐份保留；重复匹配 n 逐份放大输出；没有用 PK 假设将匹配数强行当成 0 或 1。

### C3. IFNULL 和二参数 COALESCE 的投影相同

对 x∈INT∪{NULL}，定义

\[
g(x)=\begin{cases}0,&x=\mathrm{NULL};\\x,&x\ne\mathrm{NULL}.\end{cases}
\]

此处等号描述元语言的 NULL 身份。两式中的内置 IFNULL(x,0) 与二参数 COALESCE(x,0) 都返回 g(x)。所以每个匹配配对都投影成同一个

\[
o(q,n)=(q.ID,q.YEAR,g(n.NPV)),
\]

而每个无匹配 q 都投影成

\[
o_0(q)=(q.ID,q.YEAR,0).
\]

匹配行的 NPV 为 NULL 时与补空行一样返回 0；负整数、零及正整数则在两边原样返回。只有列引用及整数字面量，没有通过求值顺序不同造成异常或副作用的表达式。

### C4. 输出重数逐项一致

对任意输出值元组 t，两边输出重数同为

\[
m(t)=\sum_{q\in Q}\left(
\sum_{n\in M(q)}[o(q,n)\equiv t]
+[M(q)=\varnothing]\,[o_0(q)\equiv t]
\right).
\]

求和按行出现，≡ 仍为输出值身份。若不同匹配 n、不同 q，甚至 NPV=NULL 与 NPV=0 投影后碰撞为相同 t，两边仍以相同次数相加。原式没有 DISTINCT，所以这里不做去重。Q 为空时两边都为空；N 为空时每个 q 在两边都得到一条补空输出。任意不等表基数也已包含。

### C5. 原 C 不参与证明

| 原 C | 是否必要 | 理由 |
|---|---|---|
| NPV.(ID,YEAR) primary | 否 | 多个重复或非唯一匹配行仍逐份产生相同输出。 |
| QUERIES.(ID,YEAR) primary | 否 | 重复、含 NULL 的被保留行已逐出现处理。 |
| QUERIES.ID → NPV.ID foreign | 否 | 没有匹配时两边均补空；而原部分键引用本来就不保证 YEAR 匹配。 |
| NPV.NPV≥0 | 否 | 任意负整数也由两边相同函数 g 原样返回。 |

故该 pair 在原 INT schema、无显式 C 下已经等价，并因此在完整原 operational C 的子域上等价。没有升级 FK、增加非空假设或删去 NULL 情况。

## D. 源码交叉核对与未认证的实现环节

固定提交仍为 `3b99928bf976c11cb59c9db6a177adba21f75798`，以下是本次新读的局部源码事实，源码哈希见输入清单：

| 位置 | 本次能确认的局部事实 | 不能据此声称的结论 |
|---|---|---|
| `encoder.py:943–963` | 无 ELSE 的 CASE 在 958–959 添加 FNull；同一分支构造 FCasePredicate。 | 原 parser、绑定及全部 CASE 路径均已认证。 |
| `visitors/visitor.py:2281–2325` | 逆向构造分支以保持首个 TRUE 优先；2294–2296 要求条件非 NULL且真。 | 已独立证明整个查询编码的正确性。 |
| `encoder.py:1291–1298` | 两侧都解析为列表的 row equality 降为逐位置 eq 再 AND；本对双方均为两分量。 | 任意不等长 row、其他操作符或类型都受支持。 |
| `encoder.py:898–910,967–979`；`visitor.py:1877–1945` | COALESCE 与 IFNULL 走不同类/构造路径；IFNULL 降为按 NULL 判断的 CASE，COALESCE 按参数顺序取值。 | 二者最终 SMT 公式、全链模型及解码已机械证明等价。 |
| `encoder.py:1096–1112` | NOT IN 的子查询分支保留为 FNotInPredicate。 | 本次手推把 NOT IN 改写为反连接，或独立认证该实现的全部 NULL 路径。 |
| `right_outer_join_table.py:37–64` | 正长度输入的构造按右侧行产生配对和左侧补空候选。 | 已认证空表路径。该函数30–33有空输入早退；上层是否预处理未在此证明，不能用 SQL 层证明替它背书，也不据此宣称运行 bug。 |

这些局部事实与成熟规则的选择相符，但不能填平“原 SQL 语义 → parser/AST → 官方编码 → SMT → model/export → SQLite”的全链认证缺口。新手推是对源 SQL 的论证，若未来实际结果与其冲突，应核对源式哈希、绑定、方言前提、实现路径及证明本身；本文件没有产生这类冲突运行证据。

## E. 对当前研究问题的含义

| 判断 | 结论与范围 |
|---|---|
| 两个 INT pair 是否已有成熟规则完全解决？ | **源 SQL、上述显式语义前提下：是。** B、C 节给出了不依赖 C、不依赖行界的完整作者推导，待独审。 |
| 完整 C 是否仍须实验保留？ | **是。** 无约束等价蕴含该子域等价，但计划要求 same-semantics fullC，不能据此改变输入。 |
| 增加 exact bound 能否使这两对出现真实 SQL 反例？ | 在已声明语义及证明正确的条件下，不能；这是解析论证的推论，不是 solver 的无界证明或本轮运行结果。 |
| 已观察较大 N 的慢/UNKNOWN 还能说明什么？ | 仍可诊断具体编码/求解/总成本的增长；不能单凭它说明这两个 SQL pair 的等价本质困难，也不能直接证明 fullC 是瓶颈。 |
| 已经有实际快速基线或速度优势了吗？ | **没有。** 未实现规则识别器、规范化器或调用成熟证明工具；无计时、成功率及预算可比证据。不能把手推当“0 秒 baseline”。 |
| 是否证明 frozen exact2/3/4 覆盖 up-to 或混合基数？ | **没有。** 对两个特定 SQL 的直接等价证明不是 encoder 完备性或补齐定理；另两个非 INT pair 不在本文范围。 |
| 新机制与独立测试？ | **NONE。** 两来源已暴露；只进一步展开已有强对照，不是新方法或新测试。 |

本轮 C-model sanity 的任何既有成功仍只说明样例生成/回放链，在逻辑上不承担 B、C 节的普遍量化证明，也不构成反例。上述手推未使用历史 UNSAT/UNKNOWN 结果作为证明前提。

恢复时只需原21 registry 的两个既定记录及固定版本源码；按输入清单核哈希，按 B、C 的语义步骤复核。不要复制第三方 raw SQL 或另造测试库作为本文恢复内容。私有备份由 root 统一核验；这里不声称 BACKUP_OK，历史/DataHub 阻塞不变。
