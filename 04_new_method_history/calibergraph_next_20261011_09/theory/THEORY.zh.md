# Round 09：计数 CSP 的变量运输能迁移到哪里

2026-10-11。**机制结论 NULL；理论门 HOLD。** 本轮只检验一个具体拼接命题 H09。其充分方向有短证；在无约束自连接片段其完整版本早已存在；直接加入原子 FD 闭包后的必要方向有两原子反例。反例可由普通 key-chase 修好，因此它不反驳“先 chase 后运输”的更强命题。本轮没有得到后者在一般非 key-anchorable 片段的必要性或合法分离族，不能把尚未证明改称机会。

全部为一手原文阅读和手推，没有执行 SQL、SMT、科学程序、模型、GPU、unrelated_project/其他队列或查询枚举；没有读取原稿、finaltest、保留集或新增自然语料。源码/输入校验只是文件完整性操作，不是科学实测。08 最终输入已核为 `a29b74cea37477e64addd3c5b5107e4ec7cbf7c31e83a7f633222712094508ed`；仍按待独立审核的上轮作者结论引用。

## 1. 唯一候选命题 H09，先把“运输”写清楚

输入沿用 08 的纯变量、non-NULL、set-base、共同安全 body B、共同有序 head H、显式 FK 闭合、PK/FK-only 语义，**仅放开无自连接限制**。FK 图仍取无环/无向森林；下文反例无 FK，因而满足此限制。M、N 是 V\\H 中的计数变量集合；其余变量存在量化。固定 head 值 h 时，答案重数是可延拓满足赋值在 M 或 N 上的不同投影数，不是完整 witness 个数。

令 F_B 含每个 atom 的 `key-vars -> all-vars`，cl 是这个普通属性 FD 闭包。End_H(B) 是保持每个 head 变量、把每个 atom 送到 B 中同关系 atom 的所有变量自同态。定义：

> **C(M,N)**：存在 α∈End_H(B)，使 `N ⊆ cl(H ∪ α(M))`。
>
> **H09**：对所有上述输入，`Q_M ≡_Σ Q_N` 当且仅当 `C(M,N) ∧ C(N,M)`；若任一方向失败，便能由失败证书构造有限合法分离实例。

这是比“找一次变量交换、比较两个闭包是否相等”更宽的双向 covering 条件：α(M) 可以含原 N 以外的变量，不要求 α、β 是全变量置换，也不要求它们互逆。**这里明确未把 EGD/key-chase 冒充为属性 FD 闭包**；H09 的这个原始版本将被否证。先做 key-chase 后再应用 C 是不同的、更强的版本，本报告不会用原始版本的反例宣称已排除它。

## 2. 充分方向完整保留，但它是旧 covering 论证加 FD

**引理。** 在任意有限合法数据库 D 上，C(M,N) 蕴含每个 head h 的 `mult_N(h) ≤ mult_M(h)`。FK 只限制 D 的范围，不改变这个论证。

证明：给每个不同的可延拓 N 赋值 n，任取一个完整满足赋值 γ_n，其 head 为 h。因 α 是 head-preserving endomorphism，γ_n∘α 仍满足 B、head 仍为 h。将它投影到 M。若 n、n′ 得到相同 M 投影，则 γ_n、γ_n′ 在 α(M) 及 H 上相同；真实 PK 逐条传播 F_B，迫使二者在 cl(H∪α(M)) 上相同，特别在 N 上相同，与 n≠n′ 矛盾。所以得到注入。双向注入给有限重数相等。证毕。

每次只为一个投影选一个 existential witness；没有把 existential witness 的数量算成答案，也没有假定同一个 α 在答案层可逆。这正是 covering-map 的组合赋值注入证明，用 FD 决定性替代直接变量覆盖，属于成熟步骤的组合，不申报新定理。

**一次运输不足。** `B=R(x)∧R(y)∧S(y)`，M={x}、N={y}，全元组 PK；α 把 x,y 都送到 y，是合法 endomorphism，甚至 `cl(α(M))=cl(N)`。但 R={a,b}、S={a} 时重数是 2 与1。只凭一个重命名后闭包相等就宣布等价会产生假阳性。双向 C 不犯此错。

## 3. H09 的两原子反例：所有合法库等价，却没有双向 C

单表 `R(k,v)`，第一列 PK。共同体

`B = R(k,x) ∧ R(k,y)`，H=unit，M={x}，N={x,y}。

**语义证明。** 任意合法 D、任意 B 的满足赋值，都因两个 R 原子具有相同 key k 而满足 x=y。若 `Val(D)={v : ∃k R(k,v)}`，M 投影集合正是 Val(D)，N 投影集合正是 `{(v,v):v∈Val(D)}`。`v↦(v,v)` 是显式双射，包括 D 为空的情形。故在所有有限合法 D 上恒等价；不存在分离数据库。

**条件失败的完全枚举式手证。** 这里 F_B 只有 k→x、k→y。任何 B 自同态都必须把 k 固定为 k，因为 B 中只有 k 出现在第一列；x、y 各可送到 x 或 y，合计恰好四个 endomorphisms。α(M) 始终是 {x} 或 {y}；其 cl 仍是该 singleton。因此 `{x,y}⊄cl(α(M))`，C(M,N) 必失败。反向 identity 已能覆盖 M。H09 的“必要性”和“失败必能生成分离实例”两项都被否证。

这是**atom 数最小**的原始条件反例：一个纯变量 atom 不可能有同表跨 atom 的 EGD；若两闭包不同，冻结一个闭包、同步改变其补集的两行构造既满足 PK 又产生2对1。若闭包相同，identity 已给双向 C。因此一原子不能发生本例的等价漏判。本报告不额外声称在任意 schema 编码下的全局变量数最小性。

**强控制必须承认。** 普通 key-chase 合并 x=y 后，B 化为 R(k,x)，两计数集合均成为 {x}，identity 立刻判等价。正确实现应做这种 EGD quotient，并同步运输 head/count 集；不能把 x,y 仍当两条独立 counted 坐标。此修复是已知 chase，既不是 CaliberGraph 新机制，也不是对 chase 后一般完备性的证明。本例只说明“属性闭包”与“body 内必然相等”是两项不同的义务。

## 4. Chen–Mengel 原定理的精确迁移

一手锚点为 Chen–Mengel，*Counting Answers to Existential Positive Queries: A Complexity Classification*，arXiv:1601.03240v2，2016-04-20，§5.1：Def.5.1（印刷p14）、Def.5.3/Thm.5.4（p15）、证明（pp15–16）。原问题是对**所有有限同签名关系结构**比较 pp 公式的满足 liberal-variable 赋值数；没有 PK/FK 限制，liberal 集可严格包含 free 集。定理等价于双向 liberal-set 满射分别可延拓为结构同态；有限性使两满射都是双射。[原文](https://arxiv.org/pdf/1601.03240v2#page=15)

**迁移所得的旧完整定理。** 若所有 PK 都是全元组且无 FK，则同 body、任意 selfjoin、任意 partial-counted 集合的逐 head 等价，恰好是存在 α,β∈End_H(B)，分别把 M 双射到 N、N 双射到 M。此时 cl 不增加变量，双向 C 就是这个条件。

完整迁移证明：给每个不同 head 变量 h_i 添一个独用 unary 谓词 U_i(h_i)，把 H∪M 当 liberal 集。若两 combined query 逐 head 等价，则对任意 U_i 的解释，将每个符合 unary 条件的 head 重数求和仍相等。原定理给扩充规范结构间的双向满射同态；每个独用 U_i 迫使 h_i 固定，因此剩余 counted 变量必须双射 M↔N。去掉 U_i 得所求自同态。反向由§2注入论证立即成立。空 head 无需加 U_i。这个证明只是在旧定理中显式编码“head 必须固定”，不是新计数机制。

**PK 首先破坏什么。** 原文 Observation5.5 用二元素全关系结构证明等价公式 liberal 数量相等。非平凡 PK 会排除此结构；§3 的合法等价对恰有1与2个 counted 变量。其后必要性证明把被选元素换成副本、每个关系元组取各坐标副本的笛卡尔积。合法 R={(k,v)} 若只把 v 复制两次，立即得到 R={(k,v₁),(k,v₂)}，违反第一列 PK。因此不能把原文插值/容斥必要性推理限定到合法库后照搬。[证明锚点](https://arxiv.org/pdf/1601.03240v2#page=16)

**FK 保留什么、未保留什么。** 对这个全 Cartesian blow-up，若原库满足 FK，源行的某个副本 FK 元组可以在目标原行的完整 Cartesian 副本中找到，故 inclusion 本身保留；目标 PK 仍可能被破坏。修复 PK 时删行或同步函数值，则已改变原计数多项式，不能继续使用原证明的系数。受约束类的充分方向始终保留；必要方向只在另外证明该类具有足够合法分离对象后才可引用。

ep 含析取；同文 Thm.3.1 是查询类之间的 counting-slice 归约，Prop.5.16 是 all-free ep 的整数系数 pp 计数展开，均不是“每个 ep 可当一个 pp 并用一次 renaming 判等价”。本轮不扩至 ep/UNION。[原文§5.3](https://arxiv.org/pdf/1601.03240v2#page=21)

## 5. 必须先扣除的直接先例

| 一手来源/前提 | 本问题可直接复用的步骤 | 不能偷渡的结论 |
|---|---|---|
| Chen–Mengel 2016，Def5.3/Thm5.4；所有有限关系结构、pp | 无约束任意 selfjoin 的双向 counted transport；§4已给逐head迁移 | 非平凡PK/FK合法类的必要性；ep当单个pp |
| Chirkova，*Combined-Semantics Equivalence Is Decidable For a Practical Class of Conjunctive Queries*，1308.4027v2，Def3.5、Thm3.11、Thm4.5 | covering mapping 的满足赋值注入；无copy-sensitive atom属于explicit-wave，双向CVM判等价 | 她的bag/copy-variable推广不是声明PK/FK后的完备定理；不得把一般单向containment也写成 iff |
| DeHaan，*Equivalence of Queries with Nested Aggregation*，2009博士论文，Def3.2.1/Thm3.2.4、§3.3.2、AppendixA.2 | normal form上的双向index-covering hom；combined语义是单层特例；diversification已存在 | 不把query-implied规范化误写成任意schema PK/FK下的新完备性 |
| Cohen，*Few Rows Tell Them Apart: Equivalence of Queries Mixing Set and Bag Semantics*，2609.09978v1，Thm4/7、Lemma11、Thm13/15 | 无约束hom刻画和row bound；FD demotion；key-chased reduct、key-anchorability、acyclic-FK chase在其前提内已有完整结果 | 非anchorable的一般合法分离族；把domain sizes {1,2}误读成每表2行 |

Chirkova 原文 [Def3.5及Thm3.11](https://arxiv.org/html/1308.4027v2#S3.SS2)、[Thm4.5](https://arxiv.org/html/1308.4027v2#S4)。DeHaan 原文 [2009 thesis，PDF pp104–108及AppendixA](https://uwspace.uwaterloo.ca/bitstreams/75481061-96ae-4f14-89b7-44c6aab72683/download)。注意此前下载链接确实是这篇223页论文，不是PODS文章 *Equivalence of nested queries with mixed semantics*；后者另有[CS-2009-12原始技术报告](https://uwspace.uwaterloo.ca/items/fbefd812-fcd1-42ff-88eb-489a85fb7def)。

FewRows 是本轮日期下的预印本。其Thm13明确要求两侧key-anchorable，Thm15要求FK chase后的两侧key-anchorable；这套“FD降维 + chase + hom”的受限完备管线已经覆盖自连接，不能把它重新命名后称为新机制。非anchorable残余问题在§4末尾明说尚缺legal realizability。FK chase成本应按实际展开大小计，不能继承其未加schema固定限定的reference-depth-only句子。[原文§4](https://arxiv.org/html/2609.09978v1#S4)

“weak maps”不被当成一个可互换的总术语：本报告准确使用上述原文的 renaming equivalence、CVM、index-covering homomorphism、multiset-homomorphism；只凭一个普通/弱 hom 可证明支持关系，不能证明计数等价。无copy变量的本轮语义不需要冒用更强的copy-sensitive结果。

这是一轮定向核验，截止2026-10-11；没有据有限搜索宣称“文献中不存在一般定理”。四条已核谱系均没有给出本轮需要的一般PK/FK非anchorable完备迁移。

## 6. 自连接使每表两行界失效：一个精确最小 row 阈值

这是父任务提出、这里独立手证的控制，不是自然来源或实测。

全元组PK二元R，共同体 `B=R(x,y)∧R(y,z)∧R(z,x)`，H=unit，M={x}，N={x,y}。

取 R={(a,a),(a,b),(b,a)}，a≠b。满足赋值恰为

`(a,a,a), (a,a,b), (a,b,a), (b,a,a)`。

x投影有2个，(x,y)投影有3个。因此这是合法3行分离实例。

**任意≤2行R都不能分离。** 一个满足赋值是长度3的闭合有向walk。如果其三个顶点全不同，必须用3条不同边；如果恰有两个不同顶点，必须用一条loop和两个反向非loop边，也有3条不同边。因此≤2行时所有满足赋值都是(a,a,a)，与R的loop逐一对应；两投影数都等于loop数。空库、一个loop、两个loop、两边2-cycle及path均被该论证包含。故此pair的最小物理行阈值**恰为3**。

这不反驳FewRows：这里 sj=3、w_R=2，其Thm7给的是≤12行而非2行。其Example8甚至已用同一三行库分离另一4-cycle计数对，因此这种小图控制不具新颖性。它只禁止把08每表2行结论无条件带到自连接；也不能据此推出所有selfjoin只需3行。

## 7. 完整成本与停止规则

记v=|V|、h=|vars(H)|、a=|B|、L=总变量出现数、r=最大arity。不得将运输搜索当免费oracle。

| 操作/强控制 | 保守全成本或边界 |
|---|---|
| H09原始检查 | 至多v^(v-h)个head-fixed映射；逐个核atom-preservation并计算两向FD闭包，哈希atom索引的期望成本O(v^(v-h)(L+v)) word operations；若要求确定性字典，可用排序后二分而支付log(a+1)因子。两向可独立在同次枚举找到，非免费也不必平方枚举 |
| key-chase强控制（显式闭合输入，无新增FK atom） | 至多v−1次实质变量合并；朴素每轮比较同表atom对，O(v a² r)上界；每次必须同步更新M、N、H。可优化但不声称已实现 |
| 旧无约束hom精确基线 | 与候选同样的全部head-preserving映射搜索，cl为空增量；通过是旧定理，不计作候选优势 |
| FewRows受限基线 | 先核scope；作用于实际chased/reduced query sizes。无约束每表bound `2^(w_p) sj_p`；key-anchorable改用相应key-width。不把不适用计为失败 |
| 固定rowbound equality-type枚举 | 同语义、PK/FK检查及精确投影去重；只在已知rowbound上完备。本轮不给非anchorable一般bound |
| 具体手例 | 反例C2证明恒等价，无分离rowbound；C3最小分离3行；C1交换例恒等价 |

**冻结的最小反证协议，仅计划、不执行。** `hand_cases.json` 固定四项：C1交换对、C2遗漏key-chase对、C3三角2/3row边界、C4单向运输假阳性。若另行获准做一次实现核验：同步单CPU进程，总墙钟预算1秒、无重试、无solver/SQL/模型/队列，只对这四项做映射列举、closure、key-chase，以及给定显式库的有限赋值去重；不给C3“所有≤2行”的手证伪造枚举receipt。记录全时延和TIMEOUT；任何输出/PK/投影数不符即停止，不改fixture，不追加有利样例。该协议检验已有控制的实现，不用于晋升、自然覆盖率或性能优越性。

理论停止规则已经触发：H09原始必要性被C2否证；自连接运输核心被直接先例覆盖；唯一未闭合部分是chase后、非anchorable合法分离必要性。本轮不保留新的窄片段机制，不宣称新small-model定理，不启动实验。新的知识是三个边界被分开并可复核：head固定的成熟运输刻画、属性FD与EGD quotient的区别、selfjoin下2行阈值的实际失败。

父任务另行准备的有限模型检索不属于本轮证据。对于一个固定有限宇宙，若C证书通过而某个合法模型计数不同，会反驳本报告充分性证明或暴露实现/输入不符；若C证书失败而所有已列模型计数相等，**只能记为有界候选，不能反驳一般必要性、更不能证明等价**。本报告未读取这类运行结果，也不因它调整H09。尤其§6三行库包含同一第一列的两行，只在全元组PK下合法；不能用它约束第一列为PK的部分函数模型族。后一schema上的三角体由x唯一决定y,z，计数{x}与{x,y}本就恒相等。

## 8. 交付与审核边界

本目录只含本轮报告、结构化结果、一手锚点、四项手例和SHA清单；没有第三方论文副本。独立审核应尤其检查：C2没有被误用成chase后反例；§2注入方向；§4 head-pinning迁移；C3四个满足赋值和≤2行证明。父任务统一私有备份；此作者交付不声称已完成远程备份。研究状态NULL、一般理论门HOLD，未实测。
