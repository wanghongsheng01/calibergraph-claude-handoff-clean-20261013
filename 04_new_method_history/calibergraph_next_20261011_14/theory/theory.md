# H14：共同 relational core 的两个自身 Cartesian 角点

日期：2026-10-11。角色：理论作者；输入包含根任务提供的群平均核线索，文献核验有作者辅助 agent 参与；尚未独立审查。结论：**H14 在下述严格片段内可手工证明。科学机会保持 HOLD / NULL**：构造、orbit 等价刻画和群平均核均有成熟先例，直接两角点结果的新颖性尚未闭合，也没有公平优势或自然数据证据。

本轮只有一个假设，无实验。没有科学代码、SQL、SMT、枚举运行、模型实验、GPU 或 queue；第 12/13 轮文件未修改。

## 1. 原问题与唯一假设

第 12 轮证明：共同 body 的 FD 闭集—单组件同步二索引族不完整，有向六环的两投影在全部 97 个组合上等数，但已有的独立 Cartesian 构造以 13 行给出 20/19。H14 只问：在额外的 **relational-core promise** 下，是否无需遍历全部二值角点，只测两个 query-specific 自身全 2 角点就完整。

设 B 为有限、安全、纯变量 relational CQ body，变量集合 V 非空，关系基表为集合，每表只有满元组 PK，无 FK、其他 FD、常量、比较或 NULL。允许自连接、重复变量、重复 head 坐标；重复 body 原子按集合解释。**core promise 的定义是 End(B)=Aut(B)**，endomorphism 必须把每个带谓词和有序坐标的原子映回 B。没有把一般 CQ 默认当成 core，也没有做最小化来替代这个 promise。

head 为同一变量元组 h，H 为其中不同变量的集合；M,N⊆V\H，可以为空，大小不必相同。单位 head 是 H=∅ 的特例。

对 S⊆V\H，构造 D_S：给每个 v∈S 两个新鲜值 (v,0),(v,1)，给其他变量固定新鲜值 (v,*)；每个变量的域互不相交。对所有逐变量独立选择 materialize B 的原子，再集合去重。重复变量的多次出现必须取同一个值，绝不是逐列独立复制。例如 R(x,x) 产生两个对角行，不产生四个全列配对。D_S 的全部行天然满足满元组 PK。

**H14：** 若 Q_M 和 Q_N 不等价，则 D_M 或 D_N 至少一个是合法区分库。更强地，只比较两库上的 canonical head c_h（由各 head 变量的固定值组成）就足够；不需要检查这些库的其他 head 值。

该 statement 是两点完整性，不是提出新的 Cartesian primitive。新研究贡献若存在，只能是对特定 promise 片段的测试族压缩。

## 2. 精确投影计数公式

令 W=V\H，G=Aut_H(B) 为逐点固定 H 的有限自同构群。对 T⊆W，定义

\[
G_{(T)}=\{g\in G:g(t)=t\text{ 对全部 }t\in T\},
\quad s_T=|G_{(T)}|,\quad b_T=|G|/s_T.
\]

这里是 **pointwise stabilizer（逐点稳定子）**，不是只要求 g(T)=T 的 setwise stabilizer。

记 p_T(S) 为 Q_T 在 D_S 的 canonical head c_h 上的重数。则

\[
\boxed{p_T(S)=\frac1{s_T}\sum_{g\in G}2^{|g(T)\cap S|}.}\tag{1}
\]

证明分三步，不忽略 self-join 或存在变量。

1. 抹去每个值的索引，得到 π:D_S→Can(B)。满足赋值 γ:B→D_S 的标签映射 πγ 是 B 的 endomorphism。core promise 使它属于 Aut(B)；若 head 值为 c_h，它还必须逐点固定 H，故属于 G。反之，对任何 g∈G，独立选择各源变量在其目标标签域内的值，均得到满足赋值：g 把每个源原子映到 B 的一个目标原子，而 D_S 包含该目标原子全部一致的变量取值组合。
2. 固定 g 后，T 的标签互异，因为 g 是双射。因此 T 上的独立颜色选择恰有 2^{|g(T)∩S|} 种，每一种均能给未计数变量任取颜色而扩展成完整满足赋值。此处计数的是可扩展投影，不把存在变量的选择乘进去。
3. 两个自同构 g,g' 的投影标签相同，当且仅当它们在 T 上逐点相同；否则对应投影集合互不相交。每个相同 restriction 的等价类恰有 s_T 个自同构，因为 g'^{-1}g∈G_(T)。同一等价类的投影颜色集合也完全相同。因此除以 s_T，得到式 (1)。

T=∅ 时 s_T=|G|，式 (1) 给 p_∅(S)=1，正确处理单位计数集。head 中的重复坐标只重复相同固定值，不新增变量、因子或约束。所有 S 均与 H 不交。

## 3. 群平均核与严格性

在 W 的全部子集上定义已知形式的 kernel

\[
K(A,S)=2^{|A\cap S|}
      =\sum_{U\subseteq W}{\bf1}[U\subseteq A]{\bf1}[U\subseteq S].
\]

取特征向量 φ_A，其 U 坐标为 1[U⊆A]，于是 K(A,S)=〈φ_A,φ_S〉。按包含关系排列子集时，该 Boolean-zeta 特征矩阵为三角且对角全 1，因此可逆；全部 φ_A 线性独立，K 严格正定。这是基础线性代数，不声称 kernel 技巧创新。

令

\[
\psi_A=\frac1{|G|}\sum_{g\in G}\phi_{g(A)},\qquad
\bar K(A,S)=\frac1{|G|}\sum_{g\in G}K(g(A),S).
\]

集合交大小在置换下不变，故 G 在特征空间的作用为正交坐标置换。有限群平均是正交投影，因此

\[
\bar K(A,S)=\langle\psi_A,\phi_S\rangle
           =\langle\psi_A,\psi_S\rangle
           =\bar K(S,A).\tag{2}
\]

也可直接把双平均展开，并用 g^{-1}h 在 G 中的均匀性化成一次平均，得到同一等式。

最关键的严格性：设 O_A={g(A):g∈G}。ψ_A 是 O_A 上不同 φ 的均匀平均。不同集合轨道彼此不交，且全部 φ 线性独立，故若 O_A≠O_S，则 ψ_A 与 ψ_S 线性独立，尤其不共线。ψ_A 的 ∅ 坐标恒为 1，所以从不为零。由严格 Cauchy–Schwarz：

\[
O_A\ne O_S\quad\Longrightarrow\quad
\bar K(A,A)\bar K(S,S)>\bar K(A,S)^2.\tag{3}
\]

注意：在原始全部子集上做 group average 后，kernel 不再对同一 orbit 的不同成员严格正定；严格性成立在不同 **orbit** 上。证明没有偷换这两层。

## 4. 两自身角点的完整性证明

由式 (1)–(2)，

\[
p_T(S)=b_T\bar K(T,S).
\]

假设两查询在 D_M 和 D_N 的 canonical head 都等数。记

\[
A=\bar K(M,M),\quad B'=\bar K(N,N),\quad C=\bar K(M,N).
\]

两个等式为

\[
b_M A=b_N C,\qquad b_M C=b_N B'.\tag{4}
\]

b_M,b_N,A,B',C 均严格正；消去 b_M/b_N 得 AB'=C²。根据式 (3)，这迫使 M 与 N 属于同一 G 轨道，即存在 α∈Aut_H(B) 满足 α(M)=N。不需要预先假定 |M|=|N|；同 orbit 会在结论处给出相同大小。空集合情形也已包含。

最后，这个自同构给出任意数据库 D、任意 head 值 a 下的投影双射：对满足赋值 γ，把 N 上的投影用 α:M→N 拉回 M，得到 (γ∘α)|M。因为 α 保持 B 并逐点固定 H，该投影仍有满足扩展且 head 不变；逆映射由 α^{-1} 给出。因此 Q_M 与 Q_N 在所有合法数据库上等价。

反之，若所有数据库上等价，当然在 D_M、D_N 上相等。综上：

\[
\boxed{Q_M\equiv Q_N
\iff p_M(M)=p_N(M)\ \land\ p_M(N)=p_N(N)
\iff \exists\alpha\in Aut_H(B):\alpha(M)=N.}
\]

**H14 在给定 promise 下成立。** 右侧 orbit 判据本身应视为已有 counting-CQ renaming 等价理论的特殊情形；这里的候选增量仅是中间固定两测试的完整性结论。

## 5. 最强已知控制与新颖性边界

详见 [primaryanchors.md](primaryanchors.md)。作者辅助 agent 直接核对 FewRows v1 的完整 Appendix A、B.1、B.2、B.3，其明文结论是完整 {1,2} 网格中存在某个区分角点；没有在那里读到本片段的固定两个自身角点规则。这是精确阅读结果，不是“规则不存在”的证明。[FewRows v1](https://arxiv.org/html/2609.09978v1)

FewRows 将 canonical 构造和部分关键证明归于 Cohen 2009 Lemma 5.2 / Theorem 5.3；该 2009 原始全文本次未能读到，因此这个直接先例入口仍未关闭。Chen–Mengel 与 Dell–Roth–Wellnitz 的原始证明已包含独立克隆、插值和 counting/renaming 刻画。群平均特征内积是 Haasdonk–Vossen–Burkhardt 2005 的成熟方法；本稿只是给出这里的有限 Boolean-zeta 特例。

必须保留的强基线为：

| 对照 | 当前证据与必须计算的成本 |
|---|---|
| 已有的直接一/两角点规则（若存在） | 最直接 prior-art 风险；Cohen 2009 全文缺口未闭合，不能当成不存在或弱基线 |
| FewRows 完整二值 Cartesian 角点族 | 在相应无约束片段已有完整性；须匹配生成、去重、评估和失败角点分母，不只数最终命中库 |
| 成熟随机多项式/颜色区分 | 需匹配随机性、失败概率、取值大小、造库行数和求值成本；不能仅比较测试次数 |
| 已知 endomorphism/automorphism/renaming 决策 | 在共同 core 上可直接判断 orbit，不必构造两份可能很大的数据库；若任务要求输出反例，还应搭配最强已知 witness 方法 |

未实施任何基线，因此不存在 measured advantage。固定两库在数量上比全角点族小，只是片段内的理论结论；其总成本可能高于直接决策或提前命中的既有角点。不能由“两个”直接写出“高效”“更快”或发表优势。

## 6. 代价与 scope 不能免费扩张

设 atom a 的不同变量集合为 vars(a)。D_S 对该原子至多产生 2^{|vars(a)∩S|} 行；关系 R 的行数上界为

\[
\sum_{a\in B:\operatorname{pred}(a)=R}2^{|\operatorname{vars}(a)\cap S|}.
\]

多个相同谓词原子还需要集合去重。若按每原子的变量域局部 materialize，可以避免先生成全部 2^{|S|} 个全局赋值再丢弃重复行，但这只是构造实现选择，不消除 atom width 的指数依赖。

全流程须计入：body/core promise 检查或证书成本、两份库的造行与去重、精确 self-join 求值、存在投影的去重、canonical head 限制、两次成功或失败以及输出见证的成本。active domain 至多 2|V|；朴素求值可能面对 (2|V|)^{|V|} 个赋值，不能按“两个小测试”忽略计算量。

本构造和比较算法在已经可信给定 core promise 时**不必显式求 Aut(B)**；群只用于数学证明。但是若输入没有 core 证书，就需要判断是否存在非自同构 endomorphism，这一步不能免费。若实现选择显式求 G 或稳定子，相关计算与存储也须计费；本轮没有运行这些步骤。将 B 最小化后直接搬运 M,N 也不被本证明授权，因为 set 等价的最小化可能改变 projection counting。

边界控制见 [handcontrols.md](handcontrols.md)：非 core 的普通 endomorphism 会打破式 (1)；非平凡 PK 可能使 D_S 根本非法。常量、FK、比较、SQL NULL、bags-as-base、不同 bodies 均不在本定理内。对这些边界没有提出第二个假设。

## 7. 本轮冻结结论

数学状态：**PROVED_BY_AUTHOR_HAND_ARGUMENT，待独立审查**。研究状态：**HOLD；new_promotable_opportunity=NULL**。直接二角点 prior art 尚有未核入口，未测公平优势，未核自然数据适用率（自然覆盖证据为 0 个实例），不写论文、不投稿、不启动代码实验。有限 core（如有向环）可以手工认证，不使自然适用面自动扩大。

DataHub/source 合规边界沿用：registry 在授权 write scope 外，DATAHUB_REGISTRATION_BLOCKED；未访问业务/企业数据、凭据或保护标签。公开文献仅只读核验，不保存或备份第三方正文。根任务负责独立审查和私有备份；作者冻结后停止修改旧轮次。
