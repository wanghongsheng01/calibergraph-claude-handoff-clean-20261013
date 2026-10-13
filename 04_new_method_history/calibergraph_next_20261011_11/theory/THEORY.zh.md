# Round 11：DeHaan 2009 约束 CEQ 基线复核

2026-10-11。作者稿；独立审核待完成。**机制 NULL，停止将 chased FD-cover 作为新机制。** 本轮唯一假说 H11 是：DeHaan 的约束 CEQ normalization 是否已经包含当前同 body、自连接、partial-counted 查询的候选判等条件。答案分两层：**先例与形式条件的重合已确认；一般约束必要性的完整证明尚未复核闭合。** 后者不使前者重新变成创新。

第09轮“已核四条谱系均未给一般 PK/FK 非 anchorable 迁移”的排除性文献判断为 **WITHDRAWN**。2009 thesis §6.2 明确提出约束判等流程，不能遗漏后再把相同流程当新方向。本轮不改第09轮冻结快照；逐项更正见 [WITHDRAWAL.zh.md](WITHDRAWAL.zh.md)。

## 1. 一手锚点和证据等级

文献为 David E. DeHaan，*Equivalence of Queries with Nested Aggregation*，University of Waterloo 博士论文，2009，共223 PDF页；不是另一个标题的 PODS paper。本文页码写作“印刷页 / PDF页”，PDF页从1起算。[一手 thesis](https://uwspace.uwaterloo.ca/bitstreams/75481061-96ae-4f14-89b7-44c6aab72683/download)

| 亲读位置 | 本轮使用范围 |
|---|---|
| §2.1，12、24–25 / 32、44–45；Defs2.1.14–16 | 抽象无限值域；有限、集合型 base relations |
| Defs2.2.1–2，34–35 / 54–55；Def2.3.3，50 / 70；Def2.3.11，64 / 84 | 索引、输出、CEQ、有限实例等价 |
| Def3.1.11、Lemma3.1.15，79–81 / 99–101；Thm3.1.17，82–84 / 102–104 | core indexes 与 normalization |
| Def3.2.1、Thm3.2.4，84–86 / 104–106；§3.3.2，88 / 108 | 双向 index-cover；combined embedding |
| §6.2，153 / 173；Example63，153、156–157 / 173、176–177 | 约束流程：chase → FD扩充索引 → normalization |
| §6.3，159 / 179；§4.6.4，130–131 / 150–151 | 约束与循环依赖的边界 |
| Appendix A，163–164 / 183–184；DefA.2.2，168 / 188；LemmaA.2.10，173–174 / 193–194 | 原必要性证明的数据库构造 |

作者已亲读整个 Chapter6、以上定义及所依赖的 normalization 证明和 Appendix A.2 bag 必要性证明。完整 §6.2 包含嵌套示例，不能只把 p153 当成孤立摘要句。原文 p153 是**明确的完整判定声称和流程概述**，没有另列约束版定理及一般必要性证明；p159 明示 Chapters2–5 的无约束前提。不能据此断言流程错误，也不能把无约束附录原封不动当作约束版证明。下面数学段落是本轮逐项推导，不是论文原文的改写或新颖性主张。

## 2. 精确语义映射：一个 bag 层足够

限定有限 schema、有限非 NULL set base、纯变量安全 CQ body B，允许任意重复表名及同一变量重复出现。H 是有序输出元组；M、N 是 counted 变量集合，存在变量是其余 body 变量。M∩vars(H) 可删去而不影响任何固定 head 的重数。没有 copy-sensitive atom、bag base、外连接、否定、不等式、算术或 SQL NULL。计数定义为

\[
 \mu_M(D,h)=\left|\{\gamma|_M:\gamma:B\to D,\ \gamma(H)=h\}\right|.
\]

多个存在变量赋值只要产生相同 M 值便只计一次。

构造深度1、signature b 的 CEQ

\[
 E_M(I_M;H)\leftarrow B,\qquad I_M=vars(H)\cup M.
\]

索引取任意固定、无重复的排列，输出仍是原来的有序 H。**H 同时出现在索引与输出是允许的。** Def2.3.3 为 head 每次出现分配不同结果属性名；它们可来自同一逻辑变量，无需创建独立逻辑变量或增加 join。若希望属性名全部不同，写成索引属性 h_i^idx 与输出属性 h_i^out，二者的取值都由同一个 body 变量 h_i 给出。

CEQ 求值先形成集合

\[
 \{(\gamma(I_M),\gamma(H)):\gamma:B\to D\}.
\]

其索引决定输出，故始终 valid。按 b 解码，每个不同索引值产生一个 H 元素；固定 h 的重数恰为 μ_M(D,h)。存在变量不会额外增加 bag 重数。于是

\[
 \forall D\models\Sigma\ \forall h:\mu_M(D,h)=\mu_N(D,h)
 \quad\Longleftrightarrow\quad E_M\equiv_b^\Sigma E_N.
\]

这是等价语义的直接对应，与 §3.3.2 的公式一致。H=unit 时输出零元组也可直接按 CEQ 定义处理；这里不调用对输出 sort 另有限制的 COCQL→CEQ Theorem2.3.12。底层值域可无限，每次 D 及其 active domain 均有限；计数不遍历无限域中的无关元素。

## 3. 将 §6.2 流程落实到当前分支

Σ 只含 PK EGDs 和 FK INDs。先完成成功且有限的 Σ-chase，得到共同 body B*，变量集合 U、商映射 q。若 FK 已显式闭合，仍必须完整执行由 selfjoin 引起的 PK 合并；新增 FK atom 后也必须继续处理新 EGD，直至闭合。记 H*=q(H)，M*=q(M)、N*=q(N)。重复坐标合并是去掉必然相等的坐标，不改变投影元组数。

对 B* 中每个 R(t) atom 加入该表 PK 对全 atom 变量的 FD，所得 Horn 依赖集合记为 F。cl 是 F 的属性闭包。设

\[
 C=cl(vars(H*)\cup M*),\qquad D_0=cl(vars(H*)\cup N*).
\]

合法数据库上，原索引到扩充索引的投影具有唯一扩展：两次满足赋值若在原索引一致，便沿 F 在整个闭包一致。扩充因此保留每个 head 的重数。对深度1的 b，Def3.1.11 的 b 条件保留全部非常量索引；不存在内层索引移动，也不需要 MVD、超图切分或 core 最小化。纯变量的当前分支因而落为

\[
 E_C(C;H*)\leftarrow B*,\qquad E_{D_0}(D_0;H*)\leftarrow B*.
\]

Def3.2.1 在共同 body 上给出的双向候选条件是

\[
 \mathrm{STRONG}:\quad
 \exists\alpha,\beta\in End_{H*}(B*):
 D_0\subseteq\alpha(C),\quad C\subseteq\beta(D_0). \tag{S}
\]

这里 endomorphism 必须逐 atom 映回**同一个关系符号的 body atom**，并逐位置保持 H*。索引覆盖是字面集合包含，不是把 α 与 cl 随意交换。不同 body 的原论文基线使用两个 homomorphisms；本报告只为共同 B* 证明下面的连接。

## 4. 完整小证明：双向 FD-cover 等价于双向闭合索引覆盖

**命题 P11（条件连接，不是约束必要性定理）。** 设 B* 是有限纯变量 body，其 canonical database K 满足 F 所对应的全部 PK。对共同 H*、M*、N* 及 C、D_0 如上，下述 WEAK 与 (S) 等价：

\[
 \mathrm{WEAK}:\quad
 \exists\alpha,\beta\in End_{H*}(B*):
 N*\subseteq cl(vars(H*)\cup\alpha(M*)),\quad
 M*\subseteq cl(vars(H*)\cup\beta(N*)). \tag{W}
\]

同一对 α、β 若满足 (W)，便满足 (S)。允许复合 PK、自连接及重复变量；无需 body 最小化或 key-anchorability。

**canonical 合法性的具体前提。** 将 U 中每个不同变量冻结为不同的新域值；每个 atom 成为一行，同行去重。同表两行若 key 元组相同，完成的 PK chase 已迫使其余列也相同，所以 K 满足全部 PK。若 B* 还对 FK 显式闭合，则每个源 atom 的目标 key 已有匹配 atom，K 也满足 FK。P11 本身只用 PK 部分；不能在未完成 key-chase 的原 B 上假定此性质。纯变量、非 NULL 假设排除了常量冲突及 NULL 相等问题。

**辅助事实 A：闭包映射的正确方向。** 对任意 endomorphism f 及 S⊆U，

\[
 f(cl(S))\subseteq cl(f(S)). \tag{1}
\]

每条 key→atom 的 FD 经 f 后仍来自 B* 中对应的同表 atom；逐步映射一条闭包推导即得 (1)。这没有声称反向包含。

**辅助事实 B：FD agreement。** 若 γ、δ:B*→K 是两个满足赋值，并在 S 上逐点相同，则在 cl(S) 上也相同。每一步应用 PK 时，两赋值在相同 atom 的全部 key 列一致，K 的 PK 迫使其余列一致；沿推导归纳。

**证明。** 由于 α 固定 H*、M*⊆C，以及 (1)，有

\[
 cl(\alpha(C))=cl(vars(H*)\cup\alpha(M*)).
\]

故 (W) 恰好可写为 D_0⊆cl(αC)、C⊆cl(βD_0)。令 f=β∘α、g=α∘β。用 (1) 得

\[
 C\subseteq cl(fC),\quad D_0\subseteq cl(gD_0).
\]

反复应用 (1) 得对所有 n≥1，C⊆cl(fⁿC)、D_0⊆cl(gⁿD_0)。U 有限，故可选共同正整数 t，使 e=fᵗ 与 j=gᵗ 均幂等。例如 |U|≥1 时 t=|U|! 足够；U 为空时结论平凡。

id 与 e 都是 B*→K 的满足赋值，且在 e(C) 上相同，因为 e²=e。由辅助事实 B 和 C⊆cl(eC)，e 在 C 上逐点等于 id。因此 fᵗ(C)=C。同理 gᵗ 逐点固定 D_0。

令 β′=fᵗ⁻¹∘β。由 D_0⊆cl(αC) 和 (1)，

\[
 \beta'(D_0)\subseteq cl(f^{t-1}\beta\alpha C)
 =cl(f^t C)=cl(C)=C.
\]

又 αβ′=gᵗ，故对每个 d∈D_0，d=αβ′(d)∈α(C)。于是 D_0⊆α(C)。对称得到 C⊆β(D_0)。这就是同一对 α、β 的 (S)。反向 (S)⇒(W) 直接由 (1) 及上述闭包等式得到。证毕。

有限集合大小还给出 |C|=|D_0|、α(C)=D_0、β(D_0)=C，因此限制在闭合索引上均为双射。这里使用的是双向映射的共同约束，**不是单个 endomorphism 保持所有闭集**。幂只是证明中的存在性工具；检查给定映射是否满足 (S) 不需要计算或执行 |U|! 步。

**单向不能偷换的手例。** R(k,v) 以 k 为 PK；B*=R(a,b)∧R(b,c)∧R(d,e)，H=unit，M={e}，N={b}。C={e}，D_0={b,c}。令 α 固定 a,b,c，d↦a、e↦b。它是 endomorphism，D_0⊆cl(αC)，但 D_0⊄αC={b}。缺少反向证书。合法 R={(1,2),(2,3)} 给 μ_M=2、μ_N=1，和单向不等式一致。

P11 是给旧条件补上的显式连接证明；没有文献新颖性检查，也没有将它提升为研究贡献。

## 5. 已证明的充分性，仍缺的必要性

**充分性完整成立。** 对 (W) 的 α，固定任意有限合法实例及 head h。为每个不同 N* 取值选一个完整满足赋值 γ，并映到 (γ∘α)|M*。如果两个像相同，原赋值就在 H*∪α(M*) 上相同，沿 FD 闭包得到 N* 也相同。因此这个映射是注入，μ_N≤μ_M。β 给反向不等式。与 chase、FD 扩充的逐实例保值相连，便得到原查询等价。这覆盖非 anchorable、selfjoin、复合 PK；没有小模型或机器运行前提。

**需要补的唯一核心必要性桥。** 在已完成的 B* 上，若只对有限 D⊨Σ 有 E_C≡_b E_D0，为什么能够推出对所有有限无约束 D 也有 E_C≡_b E_D0？后一命题才可以直接应用无约束 Thm3.2.4 得到 (S)。等价地，需要一个保持 Σ 合法性且足以导出 index-cover 的分离构造。§6.2 声称其流程足以判定，然而本文所读的定义与 Appendix A 没有给出这座桥的约束版一般证明。

不能以“论文没新定理编号”否定这个声称。这里指出的是实际证明义务：Appendix A.2.10 使用 D_Q=Δ_r(body_Q)，而 DefA.2.2 对 tuple components 独立染色。最小手例 R(k,v)、PK k，原行 (a,b) 合法；给 b 两种颜色而 a 一种，产生 (a,b₁),(a,b₂)，违反 PK。因而相等只在合法库成立时，不能把这个 D_Q 代入。chase 后 body 合法、索引 FD-closed，均不自动保证后续独立染色合法；反过来，此例也**不反驳**任何修补后的分离证明或 d=1/b 判定结论。

本轮最强可报告状态为：**旧文献已有明确的相同判定主张；形式映射、充分性及 P11 已手证；受约束必要性仍为本次 proof audit 的未闭合环节。** 不把“未复核闭合”改写为“学界未解决”，也不借 FewRows 2026 的 residual 句反向排除 2009。

## 6. 具体非 anchorable 输入和各基线关系

取 X(x PK,y)、C(c PK,x FK→X.x)，共同 body

\[
 B=X(x,y)\land C(c,x)\land C(d,x),\quad H=unit,
 \quad M=\{x\},\quad N=\{x,y\}.
\]

此 body 有 C 的 selfjoin，FK 已闭合，PK chase 不合并 c,d；两个闭包均为 {x,y}。x 同时在 C 的非 key 列出现；y 是 X 的非 key 列。按 counted-only-key 的 anchorability 检查，两侧均无足够的 counted-only-key 种子；空 head 不能决定 x 或 y。例中两个 C atom 可 homomorphically 合并，但 x 的非 key 出现仍保留。

原 CEQ 索引分别是 {x}、{x,y}；只做 chase 而不处理 FD 的字面 index-cover 测试不能从一个索引覆盖两个。FD 扩充把它们都变成 {x,y}，identity 即给双向覆盖。等价是函数性 x→y 的投影双射，不依赖任何合法库枚举。作算术检查可取 X={(11,7),(12,7)}、C={(21,11),(22,12),(23,11)}：满足体的 (c,d) 选择数为5，但 μ_M=μ_N=2；若误把存在变量赋值计数会得到5。

| 比较对象 | 对当前问题能准确说什么 |
|---|---|
| 原始 FD-cover、未 key-chase | 会漏掉第09轮 R(k,x)∧R(k,y) 的等价：key chase 合并 x=y。该反例继续有效。 |
| chase 后，未 FD 扩充的字面索引运输 | 会漏掉本节 {x}/{x,y} 例。 |
| chase 后的**双向** FD-cover | P11 证明与 §6.2 在 d=1/b 下的闭合索引条件一致；不能说 normalization 在此分支严格更强。 |
| 一般 CEQ normalization | 支持不同 body 及多层语义；这些超出本轮 P11 范围。 |
| Chen–Mengel、weak/covering mappings | 第09轮所核无约束运输和注入先例仍成立；本轮不重做其全面依赖扩展检索。 |
| FewRows 的 anchorable 定理与行界 | 其受限结论不变；本例超出该 anchorability 前提，不表示超出 DeHaan 的约束声称。 |

## 7. 循环 FK、一般嵌套 normalization 的两条防误读边界

**循环 FK 不等于标准有限 chase。** §6.3 引 [67] 支持去掉 acyclic 限定；同一 thesis §4.6.4 已区分 chase 不终止、containment 决定性和 finite controllability。原文 [67] 是 Johnson–Klug，*Testing containment of conjunctive queries under functional and inclusion dependencies*，JCSS28(1):167–189，1984；其出版 DOI/PDF 本轮访问失败，故未把它计为亲读全文，也没有独立确认它能提供 CEQ 所需的新计数论证。

直接手例：R(k,next)，PK k，FK next→R.k，查询体 R(x,y)，x、y 为不同变量。使用 fresh-witness 的标准 chase 依次生成 R(y,z₁),R(z₁,z₂),…，没有 PK 冲突可压缩这个序列，过程不终止。R={(a,a)} 却是有限合法实例。故既不能从决定性推出此 chase 有限，也不能从 chase 无限推出不存在有限合法库。当前“已得到有限、PK/FK 闭合 B*”分支不依赖这条循环推广。

**一般 nested 步骤的定义衔接问题，不是 d=1/b 反例。** 仅为核读 p153 的一般声称，取 Σ={R:A→B,R:B→A}，CEQ Q(A,B;C;C)←R(A,B,C)，signature sb。chase 和外层 FD 扩充均不变。内层 b-core={C}。若按原 Def3.1.11 允许任意外层候选并把 MVD 测试换成 Σ 语义，则 {A}、{B} 均满足相应 MVD，而空集在合法两行 (a₁,b₁,c₁),(a₂,b₂,c₂) 上失败，出现两个不可比的最小 core。单超边 ABC 的原无约束超图测试则不删 A 或 B。这个例指出“所有候选是否也须 FD-closed”未在字面定义中接好，不能直接沿用 Lemma3.1.15 的唯一最小性证明。它使用一般 FD，而非当前仅 PK schema；也涉及 s 层。**不据此判定 d=1/b 流程错误，不声称任意修补方案被否证。** 当前分支无该 MVD/core 选择步骤。

## 8. 成本、见证、停止规则

成本应按完成 chase 后的实际 body 大小计。令 v=|U|、h 为不同 head 变量数、a 为 atom 数、L 为总参数位置数。必须计入 T_chase；无环依赖也可能因展开分支使 a、v 增大，不能把 chase 视作免费。两个闭包用有限 FD fixed point 计算，例如朴素 O(vL)。单层 b 的索引规范化只需集合整理。完整枚举 head-fixed 变量映射最多 v^(v−h)，逐个检查 atom 保持和两方向覆盖，成本 O(v^(v−h)·poly(a,L,v))；不用先做 CQ body 最小化。若替换为 CSP/NP solver，求解时间仍须计入。本轮没有任何 wall/CPU 测量。

这条判等声称不自动给一般非 anchorable 的**小合法见证界**。本轮没有从 §6.2 或 Appendix A 推出某个可用的合法行数界，不能把无约束染色界当成 PK/FK 界。第09轮三角体“至少3行”只适用于 full-tuple PK；不能移到 first-column PK 的函数模型。

停止规则已经触发：候选管线与明确旧先例重合，P11 还连接了其两种写法。因此不保留新机制，不启动实验，不以补齐旧论证作为未经查新的创新。本轮没有运行第10轮有限模型检索，也没有读取其结果。

若父任务以后单独授权小宇宙实现检查，证据解释仅为：合法模型与成功证书计数不等会否证本轮充分性或暴露实现/语义错误；所有有限已枚举模型相等且无证书，只能记 bounded candidate，不能否证必要性或证明等价；同一 chased 输入的 (W)/(S) 布尔值不同会与 P11 矛盾，应先审查 chase、闭包和 hom 枚举。已经确认两条件相同后，不得将同一条件实现之间的速度差包装为机制优势。

## 9. 可审计状态

只写本目录。仅进行一手网络阅读、父任务提供的论文临时文本阅读、手推、文件写入、JSON语法检查和 SHA 元数据校验。没有运行 SQL、SMT、科学代码、枚举、benchmark、模型 API、GPU 或队列；未操作 unrelated_project，未读凭据、原稿、finaltest、保留集或其它原始语料。论文完整字节仅在父任务提供的 /tmp 临时文件中，未收入交付或备份。父任务统一私有备份；本稿不声称备份或独立审核已经完成。

独立审核重点：重复 head 属性的 CEQ 映射；finite vs unrestricted 量词；P11 幂等幂与 FD agreement；canonical body 是否真的 key-chased；单向反例；nested 例不得污染 d=1/b 结论；WITHDRAWN 文献判断不得在后续状态文件继续沿用。
