# 非作者独立挑战：冻结的唯一 batch 候选

日期：2026-10-12。角色：未参与候选设计的独立挑战者。结论：**REJECT_AS_NOVEL，严格限于当前已指定的新方法主张**。不支持把它写成“已证实没有 batch 收益”，也不支持否定整个 batch business-query audit 方向。无需运行新实验即可作出此范围内的判断。

11/11 冻结输入 SHA-256 一致；另复核 SOURCE_MANIFEST 中 8/8 本地源码快照一致。此校验认证文件身份，不认证其语义正确性。审查只读取冻结材料、相关固定源码片段和两个一手网页；没有改候选、调用 SQL/parser/solver、运行 benchmark/模型、改稿、push 或上传。只新增本目录两份审查文件。

## 结论为何仍是有范围的 REJECT_AS_NOVEL

当前方法的可执行新增步骤，是在已给定且被证明合法的 Cartesian grid 上，逐坐标避开显式非零多项式的根；其正确性由标准单变量根数界和归纳直接得到。候选没有提供经区分的、非平凡的完整 C/SQL 分支区域构造机制，也没有建立确定性需求的实际经济意义。因此，当前材料不足以把此组合提升为新科学机制。

这是对“所提交机制的新颖性论证”的否定，不是文献穷尽证明，不是证明某篇既有论文已实现整个 full-C region compiler，更不是由强 baseline 推出所有可能改进都不存在。Polygon 的可表达性只否定新任务表述；它不证明一个专门算法不会更快。成本数据和随机对照也没有提供经验性淘汰证据。以下必须修正的范围不改变前述有限决定。

## 1. 批次存在，但业务版本与语义复用仍未建立

冻结 inventory 记录 ParSEval 1,534 pairs / 11 完整供应 DDL contexts，全为多记录；VeriEQL 24,455 pairs / 87 完整供应 schema+IC contexts，其中 61 个多记录 contexts 含 24,429 pairs。组合行不能再次相加。LeetCode 23,994 pairs 只有 56 个不同 left SQL 字符串，right 为 23,994；51 schemas 和 52 joint contexts 的差异也说明 schema-only key 不够。报告与 JSON 的这些关键数一致，本审查没有重跑原始计数。

这些是实际公开查询记录上的可组批结构，足以保留研究 batch economics 的动机；不能降格为“根本无 batch”。但“相同供应 schema+IC”仍不等于完整运行语义上下文 K：dialect、engine、bound mode/vector、adapter、original SQL 与版本来源必须匹配。字符串重复证明缓存机会，不证明共享 AST/语义子图。左查询缓存也必须按完整上下文分键，不能把 56 直接当作跨所有上下文只编码 56 次的证据。

独立生产 business-version lineage 未核实。旧 A/B/C 是同 496 问题的不同条件；公开 batch 与 legacy 都是已暴露 development 材料，不能重新标为 new test、真实生产演进或独立业务版本。作者对此主要限定正确。

## 2. 构造证明成立；随机“同样保证”的概括过强

在 characteristic zero 的精确多项式环中，某坐标使非零残差整体归零的特殊值，至多为该坐标次数。对所有残差取 union bound，并在每一步保持它们为非零多项式，|S_j| > sum_i degree_j(P_i) 足以保证最终各残差均非零。逐步特化不会增大剩余次数，因此初始 D_j 上界足够。无需展开乘积多项式。这是正确的条件性存在/构造结论。

**必须修正：确定性网格条件不保证同一网格上的均匀整点采样有常数成功率。** 纯数学反例（非 SQL 实验）：X={0,1}^d，P_i(x)=x_i。每个 D_j=1，|S_j|=2 满足确定性条件，但所有残差同时非零只有全 1 点，均匀独立整点采样成功率为 2^-d。完整合法域完全可以只允许这两个值，不能免费扩成大网格。

作者写出的等宽大网格条件 L >= 2 D_total 时失败率 <= D_total/L、期望至多两次是正确的充分条件；它不覆盖全部确定性可用区域。因此开头“random baseline obtains the same simultaneous coverage guarantee”只能改述为“在同一合法区域确实容纳该大网格时，随机控制具有该常数概率保证”。不能把此条件式当成所有区域的性能等价或支配结论。有限预算下随机采样没有确定性必达保证。该区别具有理论意义，虽不足以证明新颖性或自然 workload 收益。

反过来，以上反例也不是新 SQL candidate、自然实验或性能证据；它只证伪一项拒绝推理。稀疏显式多项式上的根规避仍为 elementary，理论边界应保留而不包装成新定理。

## 3. full C、SQL 与复杂度边界

作者给出的保守边界基本合格：T 必须包含全表、固定 tuple occurrences/counts/tags/NULL flags；pi_legal 对整个 X 验证完整 C 与分支条件，anchor 合法不够；NULL mismatch 常量化和 COUNT 常量化均依赖固定分支；每个 bag occurrence 单独贡献；一般输出 bags 不自动归约到单个标量差；source type、engine intermediate overflow、empty aggregate 与 NULL 语义必须真实一致。C 中未被查询使用的表/字段也不能省略。

只在原始、精确整型 scalar fragment 和可检验残差推导下接受此证明。额外 SQL 特性需要另行证明，现文没有冒领。P_i identically zero 仅给 region equality；有限网格上的零也不等于形式多项式恒零。没有覆盖全部合法数据库的证明，就没有 bounded/global EQ。

“polynomial construction”应指多项式表达对象，不应暗示对 SQL 输入长度为多项式时间。规范化展开、稀疏表示大小、系数 bit growth、次数和扫描次数可能很大；拒绝/size cap 与 fallback 成本是必要组成。singleton box 没有自动跨查询搜索增益。

## 4. SAT/UNSAT 转移规则通过

同语义、同原查询 pair 下，域缩小保留 UNSAT，域扩大保留已在旧域中的具体 SAT witness。C_new stronger 即 valid_new subset valid_old：旧 UNSAT 可转移，旧 witness 需重新验证；C_new weaker 反向。新 query pair 的 mismatch 必须重新检查，不能继承旧 SAT verdict；不同 pair 的 UNSAT 需要明确的 mismatch/domain implication 或映射证明。

at-most bound 的包含关系允许向更大 cap 转移 witness、向更小 cap 转移 UNSAT；exact-row domains 不自动嵌套，padding 会改 C/aggregate。区域缩小仍须检查网格容量，区域扩大须重新证明合法性和分支不变。unknown、unsupported、timeout、under-approximation failure 均不构成 EQ。作者还正确区分 inconsistent C 与成功审计。

依赖失效清单覆盖 original SQL/parse provenance、全部 S/C/types、bound、engine/adapter、NULL/bag/order、残差/符号和验证 provenance。哈希只提供身份，不能替代 soundness；旧 witness 可重新执行验证后取得新记录。

## 5. 既有工作足以否定 generic novelty，不足以宣布具体编译器已经存在

独立打开 Polygon 一手论文，摘要与 §1 明确是 n 个查询、一个输入、输出上的 SMT 属性。因此 AND_i mismatch_i 在其问题表述内。另读取固定 environment.py:304–389，源码路径使用两个输出 groups 的 disambiguation 条件；任意 pair conjunction 是论文支持的适配，不能声称该 stock API 已原样提供。[Polygon 论文](https://arxiv.org/html/2504.06542v1)

独立打开 GreenTrie 一手记录，其已有工作确实涉及 constraint solution 的 implication-based reuse，足以支持“普通 SAT/UNSAT implication cache 不新”的边界。[GreenTrie](https://arxiv.org/abs/1501.07174)

XData、test-suite distillation、VeriEQL 和 ParSEval 的具体锚点本次依赖已冻结 prior audit，不冒称重新全文复核。其正面证据足以要求 query-aware suites、replay-all、query-result memoization、shared schema/IC、incremental solving 和 coverage policies 作为强控制。不能将这些测试工具的 agreement 当完整证明；不能把当前 ParSEval 代码追认给 2025 论文。Few Rows 被限定为相关 preprint，不等于通用 aggregate SQL 批次定理。

八个 inspected files 中没找到 exact compiler，只是 scoped absence；既不授予新颖性，也不证明全领域不存在。当前拒绝的依据是候选没有建立新增机制差异，而非这个 absence。

## 6. 旧成本不能用于否定未来 batch 收益

8 slots / 4 exposed pairs / 两种模式 / N<=1：wall 4.860539542 s；schema+C+encode 0.076072502 s，占 1.5651%；search 已包含 solver，不可叠加。precise 4 slots 的 solver 0.038520208 s / wall 1.765915084 s = 2.1813%。这些值在冻结两份成本 JSON 中相符。

这些数据只约束这几次已记录运行的显式阶段；schema_C 不是所有约束推理成本，warm-cache residual 的分母也不是 cold wall。它们不估计 natural batch、宽界限、共享见证覆盖、未见 workload 或新 region 的收益。作者正文承认这些限制，但前部“cost inventory ... rules out ... large gain”必须限定到旧运行的相应显式阶段。不得将 1.5651% 或 2.1813% 当未来 Amdahl ceiling，也不得仅选 UA 较高 solver 比例制造机会。

成本式 sum s_i > H+A+G+V+F 是有用的会计提醒，但 incremental/replay baseline 的残余成本可能耦合；若 s_i 不是一致分摊的可避免边际成本，不能直接相加。最终应比较匹配预算/正确性口径下完整 batch 的实际成本差，包含未覆盖任务、失败区域和 fallback。

## 7. 可证伪协议有骨架，尚不是完整可执行 preregistration

已有明确问题：去重和旧 witness replay 后是否仍有 multi-pair certified regions；全成本是否低于强控制；优势是否超出 same-region random 和 Polygon joint objective。已有正确性 hard kills 与失败/回退计费要求。故不能说“完全没有可证伪协议”。

但尚未冻结 admitted fragment 的可执行判定、未来独立 batch 选择/时间或 context 分割、primary endpoint、budget/attempt cap、random trials/seeds、最小有意义收益和聚合/不确定性判定。尤其“random matches”与“region cost >= saved cost”目前是概念性停止条件，没有充分的观测判据。本轮不需要补成实验，也不应运行；未来若重开，应先补齐再执行，绝不能以已暴露旧 dev 回填 confirmation。

## 必须修正与保留

1. 收窄“同网格随机有同样保证”：仅在可合法取得足够大网格时给出常数成功概率；保留有限 grid 上的确定性区别。
2. 收窄成本的 rules-out 语言；8 slots 和 precise 2.18% 不否定未来 batch。
3. 保持 REJECT_AS_NOVEL 与“实验上无收益”分离；Polygon 可表达性不等于专门算法无价值。
4. 若未来授权测试，补足可执行 endpoint/budget/stopping 与完整语义 batch 身份；当前不升格为 KEEP_FOR_TEST。

理论上保留：精确、有限、全域合法且分支不变区域内的 simultaneous root-avoidance 构造；region-local equality；严格依赖和域包含下的转移规则；在不能扩大 legal grid 时有区别的确定性保证。实践上保留：公开来源确有可组批记录、强 baseline 之外的经济问题仍值得被具体机制回答。上述保留不提出第二候选，不授权新实验，也不推翻 prior negative decision 或旧稿状态。
