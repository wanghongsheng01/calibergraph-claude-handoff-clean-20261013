# 静态分析独立审核

结论：**必须修正（3 项）**。当前稿的案例推导、保存证据解读及“新机制 NO_GO”成立；唯一工程规则的准入范围还不够精确，两处论文定位有误。修正后应定点复核，不能把本结论当作当前整稿 PASS。

审核人：`/root/masking08_independent_review`。作者与审核任务分离。本审核未修改作者稿或历史文件；新增科学执行、SQL、基线、生成器、求解器及实验均为 **0**。只读本地报告、JSON、冻结源码、原 SQL/DDL，并定点核读报告已列出的三篇论文；没有扩大检索、取得新案例、下载源码或 JAR。备份由父任务统一办理。

当前审核对象是 `ANALYSIS.zh.md`、`EVIDENCE.json`、`DECISION.json`。其 SHA-256 依次为 `4b68a9ae7fb400056d5a1c74bdfd644a3a17e2d67011e8e8092103f540f08ff5`、`8aabdf33885f3ec1dda02f17db346588f17dcb3375535e25775a5e88ae9e54ef`、`8f712abcd8c6f56267a6bc21d9052f96cc823d8228c4ccfcc35cf21e7b0a804e`。

必须修正：

1. **R1：收窄工程规则准入及其必然 NEQ 预测。** `ANALYSIS.zh.md:48` 仅列出嵌套谓词和相同 `COUNT(DISTINCT key)`，不足以保证第 57 行的最终输出差异。可空 key 不贡献 COUNT；聚合后的 HAVING、LIMIT/OFFSET 或上层算子也可能使两侧输出继续相同。这是静态逻辑边界，不是本轮执行所得反例。本例原 SQL 没有这些构造，故案例 A/B 证明不受影响。建议将唯一规则明确限为：相同 FROM/INNER JOIN、相同且已证非空的 key、单一无分组的标量 `COUNT(DISTINCT key)`、只允许 WHERE 真值集合之间的包含关系变化；排除 HAVING、LIMIT/OFFSET、集合运算、窗口、外连接、相关子查询及其他投影/聚合后变换，无法证明则 unsupported。`DECISION.json` 同步记录此准入边界。off/on 应共同固定这套准入与非空性条件，仅开关所选 key 的严格侧不存在条件。
2. **R2：ParSEval 去重覆盖引用应改为表 2。** `ANALYSIS.zh.md:34` 和 `EVIDENCE.json` 指向表 1；指定 PDF 第 5 页（印刷页 4754）的表 2 才列出去重前重复元组及至少两个不同元组的覆盖条件。表 1 是 U-expression 定义。结论内容有依据，但定位须修正。[指定 ParSEval 原论文](https://dbgroup.cs.tsinghua.edu.cn/jnwang/papers/vldb2025-parseval.pdf)
3. **R3：Polygon 候选案例来源引用应改为 §4。** `ANALYSIS.zh.md:63` 和 `EVIDENCE.json` 使用 §6；指定 arXiv v1 的 §4 Evaluation、Equivalence refutation benchmarks 段才说明复用 VeriEQL 查询对及 LeetCode 来源。应继续保留“候选来源尚未取得或准入”，不能因此声称已获得独立案例。[指定 Polygon v1，§4](https://arxiv.org/html/2504.06542v1#S4)

已通过的实质核对：

- **精确条件。** 已只读原两查询和完整 DDL：男性筛选相同，连接与 COUNT DISTINCT 相同，仅边界比较不同；Patient.ID 明确非空，Laboratory 的联合主键允许相同 ID 的多次记录。由严格侧 ID 集合为 B、宽侧为 A∪B，可直接得出输出差为 |A\B|；区别存在当且仅当 A\B 非空。只禁止所选 ID 的严格侧成员资格即可，不必禁止其他 ID 的 >2 记录。元组差异、distinct key 差异和聚合值差异已正确区分；非嵌套集合的两个方向可相抵。
- **9 个保存候选。** 逐项对照旧 `run/AUDIT_RESULT.json`，作者表中的 A、B、输出均一致。候选 1、2、3、8 含边界，所有 A\B 均空；9 个完整 DDL 合法及输出复算属于先前独审的结果，本轮没有复算。旧自构造控制的 1/0、非作者原始见证、未供给生成器、非独立测试界线均保留。
- **ParSEval 源码。** 固定 `main.py:111–137` 确实执行并比较两个查询，且分别调用单查询生成；`generate.py:246–260,374–406` 的目标和保持覆盖逻辑支持报告解释。证据只建立这次覆盖遗漏，不能从中认定 seed、只增行或保持覆盖是唯一因果根因。原审计也支持前端、lowering、执行和比较已完成。
- **Polygon 源码及先例。** 固定 `Count_Distinct:99–117` 处理删除标记、NULL 和重复值；`environment.py:220` 添加最终输出不等。论文 §3 的联合语义及输出条件支持“目标已有先例”。报告明确以语义正确和 full-C/方言准入为前提，没有把静态检查冒认成本例限时成功；这足以维持目标本身的新颖性 NO_GO。[Polygon v1，§3](https://arxiv.org/html/2504.06542v1#S3)
- **XData 界线。** 指定论文 §2、§3.5、§4.3、§5.2、§7 支持差异传播、去重后聚合及有界 pair 目标的归纳；§7 明确把直接方案的比较评测留待未来。报告没有用 SELECT DISTINCT mutation 或 §9 成绩冒认本例的 exact-pair 实测。旧 `XDATA_EVIDENCE.json` 的核心 Java、实际 classpath、paper/artifact 映射未核边界保留。本轮未另行访问仓库，也不替作者本轮网络失败陈述出具独立网络日志证明。[XData v1](https://arxiv.org/html/2409.18821v1)
- **单因素和预算。** 在 R1 修正的准入域内，off 的元组差异与 on 额外要求的 key 缺席形成可解释的单因素公式消融。两臂相同 fresh encoder、完整 C、行界、种子和配置，避免与保留旧模型混杂；它不是官方未修改 ParSEval 对照。4×5 秒、总 20 秒 solver timeout、90 秒墙钟、60 秒自身 CPU、1 GiB 采样阈值等全是未执行且未授权的工程预案，不含强基线成本；三份作者文件对此一致。
- **错误和停止线。** 已只读原 `RESULT.json`、traceback 并核对 SHA；`ERROR_NOT_ALGORITHM_FAILURE`、基线 EQ 后回放的 `KeyError('Patient')` 均原样保留。Python 大小写映射解释与保存结构一致。未获得新的独立自然案例，外部开发/封存测试各一例仍是目标，不能把 1172 或控制升级为 test。报告不宣称新机制或优于强基线。

覆盖边界：本审核独立检查了上述静态逻辑、指定源码及三文件关键结论一致性；没有重新验证 SQL 运行、编码器正确性、Polygon full-C 准入/运行、XData 核心实现、未来预算执行能力或整机资源。作者所报旧 MANIFEST 46 项与 FREEZE 588 项全部匹配，本轮只核对关键输入和源码哈希，没有重复扫描全部项目。历史 `BACKUP_BLOCKED`、`DATAHUB_REGISTRATION_BLOCKED` 与未完成基线/独立案例事项仍存在；它们不能由本次静态审核解除。
