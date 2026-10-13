# 第15阶段独立范围审查

审查者：`/root/round15_independent_gate`。初始范围状态：`SCOPE_ACCEPTABLE_FOR_TOOL_DIAGNOSTIC / SCIENTIFIC_PREEXEC_PENDING`。本文件不是科学执行授权；随后能力探针资源门失败，终态以 `REVIEW.zh.md` 为准。

【判断】H15 可以问：在固定四个已暴露公开开发来源、原 SQL/schema/full operational C、exact-N 基础活行与原资源限额下，低 bound 快返回而高 bound UNKNOWN 的现象是否在预先登记的两遍冷进程中重复，现有测量能把成本定位到哪一阶段。这是工具开发诊断，不能晋升为新方法、科学困难、业务错误发现或总体覆盖率。两条 INT pair 已有基础恒等式解释，重复 timeout 不产生新的科学机制证据。

【证据·静态】已读 `STAGE_INTENT.zh.md`、两份 VeriEQL/SQLSolver 作者报告、Polygon/FewRows/DKE 四份报告、执行边界 MD/JSON。Polygon/FewRows/DKE 四份文件的 SHA256 清单通过；执行边界 4 项 outputs 及 50 项 inputs 清单通过。最初 shasum 因环境 C.UTF-8 locale 错误退出；仅改该只读哈希命令的 `LC_ALL=C` 后成功，不涉及科学程序、权限、nice 或系统设置。父任务随后 pin 的 VeriEQL/SQLSolver scope=`fb62efc72aec0e3df9467d3b4bca1fddc74cac4e73246bdab50f5fb0fda0dacd`、evidence=`23d535857024bf19db27da18a8229581531b03d907dd1b71518d0cf2715bf5d8` 也经清单核验通过。

## 独立一手抽查

| 主张 | 已读依据 | 独立结论 |
|---|---|---|
| VeriEQL 论文 up-to N 与本次代码 exact-live N | [作者论文](https://arxiv.org/html/2403.03193v2)，§2、§3.5；[固定 environment.py](https://github.com/VeriEQL/VeriEQL/blob/3b99928bf976c11cb59c9db6a177adba21f75798/environment.py#L518)，518/584；[固定 verifier.py](https://github.com/VeriEQL/VeriEQL/blob/3b99928bf976c11cb59c9db6a177adba21f75798/verifiers/verifier.py#L83)，83 | 论文允许删除位非确定；所查建表路径生成 N 基础行并把非删除加入求解前提。未建立补齐定理，不能把 exact-N 或统一 1..N 当成全部 up-to 基数向量。 |
| SQLSolver 无界 EQ、IC 实际支持 | [作者 PDF](https://www.cs.yale.edu/homes/piskac/papers/2024SIGMOD.pdf)，§2.2 pp.227:5–6、§5 pp.227:20–21；[固定 Constraint.java](https://github.com/SJTU-IPADS/SQLSolver/blob/dcc2a91d8971a4c4d30b055f99d7d8428a1b754b/superopt/src/main/java/sqlsolver/superopt/constraint/Constraint.java#L14)，14–16/44–45；[固定 UExprTranslator.java](https://github.com/SJTU-IPADS/SQLSolver/blob/dcc2a91d8971a4c4d30b055f99d7d8428a1b754b/superopt/src/main/java/sqlsolver/superopt/uexpr/UExprTranslator.java#L957)，957ff | 求和不固定数据库行数，论文证明程序 sound/incomplete。过近似 SAT 不证明不等价。Unique/NotNull/Reference 是正面支持证据，不能说无 IC，也不能推出任意 fullC。 |
| FewRows 两值块不是两行界 | [作者全文](https://arxiv.org/html/2609.09978v1)，§3 Prop.5/Thm.7/Example 8；独立子审查者 `/root/round15_independent_gate/primary_spotcheck` 再开原文 | 每 multiset 变量的新鲜值块取 1/2；每关系界仍含 width 和 self-join 数。不能据此给本轮 N2 完备性。 |
| DKE 能力/实验不能排除 | [机构一手元数据](https://researchportal.tuni.fi/en/publications/detecting-measurement-issues-in-sql-arithmetic-expressions-and-ag/)；独立子审查者再次打开出版社失败 | 2019 年发表身份可核；全文、具体语义、实验仍 UNRESOLVED。阻止排除/优越性陈述，不阻止这次有限工具诊断。 |

以上是范围核对。论文定理未独立验完、实验未复现；没有把论文报告或静态代码事实写为运行验证。FewRows 自述无实验不得转用为 DKE 无实验。Polygon、VeriEQL、SQLSolver 的成功含义、界语义、预算与成功子集成本分母不相同，不做速度排名。

## 科学执行前必要门

1. 新 source、protocol、runtime 与数据逐项冻结；独审只接受冻结版本。旧 06/13 不变，旧 13 一次失败保持 NOTCOMPLETED，禁止重试。
2. 固定来源 `[6,9,14,3]`、N=`[2,3,4]`、两重复、24 槽完整顺序。第二遍反来源、反 bound；所有拒绝/异常/UNKNOWN/截尾/未运行保留。旧 06 的 12 槽 2/4/8 并列报告，不能混成新独立样本。
3. 每槽一次 Environment、完整 operational C、无新 solver 调用或删除 C；fullC 的业务真实性/完备性仍 UNKNOWN。四来源之外的旧 21 来源均已暴露，不能称新 test。
4. 维持 nice15、单 worker、每 worker CPU3s/wall4s/采样 RSS256MiB、C100ms/query700ms/Z3 内存128MB、load≤4/free≥25、总账60s含prep10和tail0.2。能力检查、启动、探针、parse/encode/check/C sanity及全部父/子成本须收费；wait4 与 CHILDREN不能重复相加。
5. 两遍逐 source 成对报告，不取最快；未到达/未闭合阶段为 null/unmeasured/censored，不是零。嵌套 parse/replay 不重复加总。冷启动准确写为“冷进程”；未清 OS 文件缓存，不声称冷缓存。
6. 仅精确受审的新命令可请求工具支持的 require_escalated；审批拒绝是 NOT_LAUNCHED，进程启动后 syscall EPERM 是 NOTCOMPLETED。失败不更名重试、不删 nice 或变更系统安全。

目前范围没有新增科学否决项；source 冻结与静态 preexec 尚未完成。DataHub 注册及统一私有备份由 root 负责，本独审不声称 BACKUP_OK。
