# 第六轮结果独立审核

本审查接受限定结论 **`NO_NEW_METHOD_NO_FAIR_SUPERIORITY`**：真实批次记录支持生成与回放链的可行性，但没有查询 SAT 反例、新候选算法、消融或公平强基线胜出。**实验读数通过；理论原稿仍有 1 项 P1 和 1 项 P2 待修。** 不能把整份理论稿标成无保留通过，也不能把本轮结束写成总研究完成。总研究仍须继续。

本结论绑定作者快照 `SIXTH_ROUND_AUTHOR_MANIFEST.json` SHA256 `ab22d1fcb9ec4964441c6b6f5b316b23a3978c094298b9d25bbc26d17a3e8b57`，其 115 个成员全部重算一致。作者与 reviewer 分离；没有修改作者文件。审查只执行自编标准库读数核验器，不 import 作者或上游代码，不执行 SQL、SMT、parser 或科学实验。外部冻结依赖只对清单中的精确路径读字节哈希，没有展开语义或读取其他目录。

## P0 / P1 / P2 与修复要求

**P0：未发现。** 未发现会推翻本轮负面研究结论的伪计数、漏槽、隐式重试、异常升格或资源账目不一致。

**P1-01 — P_lift 缺少 FK 源列与 PK 分离的必要前提。** 位置：作者 `literature/EQUITABLE_QUOTIENT_FALSIFICATION.zh.md:9,33–35`。S0 只明确 FK 列彼此不重叠，未明确 FK 源列不能同时是本表 PK；其恢复证明却先分配互异 PK，再独立填 FK。按文字允许的范围，取 `T(id,payload)`，`id` 既是单列非 NULL PK，又是指向 `T.id` 的唯一 self-FK。证书有两个 payload 不同的类 A、B，各大小 1，目标 A→B、B→A，度数均为 1，满足全部列出的平衡式。任何具体数据库中，行的 `id→T.id` 都只能匹配该行自身，因此该证书不可实现。此为 reviewer 手推反例，未运行 SQL/SMT。

修复：在新版本中显式要求每个 FK 源列不占本表 PK 列，FK 源列彼此不重叠，payload 字段与 PK/FK 字段分离；或给共享 PK/FK 加独立的联合可实现性条件及证明。不能仅以“互相独立”一句话跳过字段重叠。修复前不认证原文 P_lift 的普遍性。这不推翻合法实例上的 P_count，也不逆转 novelty 否定；反而进一步限制了当前候选可主张范围。

**P2-01 — 适用性筛选口径与正式片段不一致。** 位置：`data/selection_rules.zh.md:19` 与理论稿 `:17`；相关分母记录 `data/structure_denominator.jsonl`。前者要求表图 forest、每表一次、COUNT/tree aggregate；后者允许普通 self join，条件落在查询别名的无向简单树，输出严格为 COUNT(*)。因此“重复表/self-reference”不能单独证明超出后者。

修复：把旧规则明确标成更强的选样子集，或统一为正式片段；逐来源改用独立充分的超片段理由；不要把 COUNT/tree aggregate 当成已有 COUNT(*) 定理。独立逐项检查 21 组原查询，两边均符合正式严格语法的组数仍为 **0/21**，四个实际来源为 **0/4**。此数是原 SQL 整体对当前严格片段的静态覆盖，不能外推为 quotient 对这些任务语义上均无用，更不是自然总体覆盖率。

本审查只记录修复需求，没有代作者修改；后续版本必须单独留存并再次核对，不能替换本次被审字节或改写已有实验记录。

## 原始实测读数

以下为 reviewer 从 `runs/generation_replay_01/batch_receipt.json`、12 份 `results.json`、12 份 `supervisor_receipt.json`、worker/supervisor events 与 progress 独立聚合的结果。不是运行作者 analyzer 后转述。自编核验器共 **1288 项检查，0 失败**，详细输入哈希和逐项结果见 `independent_evidence.json`。

| 来源 | exact-N=2 | exact-N=4 | exact-N=8 | 记录中 C-model sanity |
|---|---|---|---|---|
| dev03_07 / 1173 | UNSAT | UNSAT | UNSAT | 3 槽均不准入 SQLite 回放 |
| dev03_10 / 1264 | UNSAT | UNKNOWN timeout | UNKNOWN out of memory | 3 个完整 C 模型，原 SQL bag 相同 |
| dev03_15 / 1421 | UNSAT | UNKNOWN timeout | UNKNOWN out of memory | 3 个完整 C 模型，原 SQL bag 相同 |
| dev03_04 / 1468 | 比较编码退出 | 比较编码退出 | 比较编码退出 | 3 槽均不准入 SQLite 回放 |

12/12 槽返回，12 个单次 attempt；没有重试、替换或 NOT_RUN。12 个 C 非空检查记录为 SAT；9 个查询 check 中为 5 UNSAT、4 UNKNOWN；共 21 次 solver check。12 份原始结果与监督器内嵌副本完全相同，结果文件哈希及最终事件记录一致，check-start/end 次数与进度一致。三个 1468 错误均是 `OFFICIAL_COMPARISON_FORMULA_ENCODING / NotEquivalenceError`，query check 为 0，保留 INCONCLUSIVE 正确；`NOT EQUIVALENT` 字符串本身不构成查询 SAT、反例或无界不等价证明。

N 是**每张原表恰 N 个活行**。协议中的行数、结果 exact_rows 与六个导出数据库的实际行数一致；导出代码还逐行拒绝 DELETED 标志。UNSAT 只能称 exact-N 官方编码结果，不是 at-most-N、不是真实 DBMS 全方言或无界等价证明。12 个 solver SAT/UNSAT 的实际逻辑求解结果本审查没有重跑；这里只认证记录和代码路径相符。

批次回执 SHA256：`16ca6e4d6e056e97afe764754eb3091f5d374fea2edc1ca53271ecad35538029`。作者结果报告 SHA256：`80c6a8ca5ccb1a2f2bac4e8f8b452a4da990823f4b746701b639003d70abfe4a`。两者与委派时身份完全一致。

## 完整 C、NULL、bag 与原 SQL

六个 sanity 数据库合计 56 个物理行。reviewer 对保存的具体整数值重新逐条计算两组全部 operational C：1264 的两个复合主键及 **全笛卡尔** USER1_ID≠USER2_ID；1421 的两个复合主键、严格非 NULL 的 QUERIES.ID→NPV.ID 外键及 NPV≥0。全部 21 次顶层条款核验成立，表/字段集合、32 位整数范围、非 NULL 主键、exact-N 均保持。该核验不调用作者 `check_full_original_C`。

两组每个模型都记录两次未改写 SQL 执行，hash 与原 `source_record.pair` 相同；记录的 SQLite 版本均是 3.53.3。reviewer 重新按 bag 多重性比较保存输出：1264 为 0/0、0/0、1/1 行；1421 为 2/2、4/4、8/8 行，全部相等。静态路径 `safe_sqlite_replay.py:147–175,193–212` 使用原字符串执行、保留字段顺序和重数；只有这两个哈希绑定的 INT 来源准入。DATE/ROUND/除法或 VARCHAR 解码未认证的另外两组被拒绝是合理边界。

这些模型来自同一次 `FULL_C_NONEMPTY_CHECK`，不是 query SAT。sanity 与内层 replay 都有 `C_MODEL_SANITY_ONLY_NOT_QUERY_SAT` 和 `query_sat_witness=false`，顶层查询反例路径没有 replay；源码未增加 solver check。**查询 SAT 模型=0，经查询 SAT+完整 C+原 SQL确认的区分反例=0。** 6/6 sanity 完成不能改称反例生成成功率100%。

NULL 路径静态使用独立模型 NULL 标志，不用哨兵99999；bag 比较不把结果转成 set。但这六个保存的输入及输出中 NULL 单元均为0，不能声称本次动态实验充分覆盖 NULL 分支或一般 bag/NULL 语义。原 SQL 在本次审查没有再执行；“12 次回放”是经过交叉核对的原始执行证据，不是 reviewer 独立 SQL 复跑。

## 成本与资源保护

| 项目 | 独立重算 / 回执值 |
|---|---:|
| 监督器 SELF + 所有已回收 CHILDREN CPU | 18.274636 s |
| 准备预留（非测量）+ 退出尾部预留 | 10 + 0.2 s |
| 总计费 / 批次上限 | 28.474636 / 60 s |
| 12 worker 的 wait4 CPU 合计 | 14.442653 s |
| 最大 worker CPU / 上限 | 2.166776 / 3 s |
| 最大 worker main wall | 2.147482041 s |
| 最大监督器记录的 worker 生命周期 wall / 上限 | 2.239919625 / 4 s |
| 最大 wait4 RSS / 上限 | 258162688 / 268435456 bytes |
| 查询 check CPU / 完整 C check CPU | 2.500993 / 0.063040 s |
| native 与官方 import CPU | 7.620111 s |
| 12 个启动门的 1-min load | 2.576171875–2.7138671875，均≤4 |
| 12 个启动门的可用内存比例 | 34%–36%，均≥25% |
| 监督器 MONITOR 样本 | 140 |
| worker 并发 / nice 最低要求 | 1 / 15 |
| 报告的资源违规 / 自动重试 | 0 / 0 |

SELF 与 CHILDREN 相加一次即可；worker wait4 是其中子集，不能再加到总账。回放内层 phase 包含于外层控制阶段，不能重复计费。准备10秒及尾部0.2秒是预留，不伪装成测量。parse、scope 的拆分以及作者逐槽 runtime/attempt/cleanup/回放内外层费用均与原始记录一致。三个比较编码退出的细分 compare_encode 是 null，不能说该阶段耗时为0；其成本仍含于完整 attempt 和进程总账。作者报告的最大 main wall 正确；本审查补出较大的完整生命周期 wall，仍低于4秒。

源码 `generation_supervisor.py:93–109,296–312,345–404,471–478` 与 receipts 支持父进程总账、RLIMIT_CPU、单进程组监控、load/RSS/wall 检查、wait4 回收及最终违规检查。`generation_common.py:48–64` 检查 nice≥15；12 个 worker 正常完成这一路径。监控事件次序显示上一个 worker 结束后才启动下一个。没有做故障注入，不能因此认证任意故障时的保护完整性；RSS、wall、load 本来就是采样保护，不保证永不瞬间越界。

两次 OOM 是记录中的 Z3 UNKNOWN reason，配合冻结的内部128 MB参数；不是外部256 MiB违规。两次 timeout 对应700 ms请求。只能报告该编码在该预算下未返回判定，不能从一次耗时推断复杂度、科学 hardness、跨机器成本或胜过强控制。

## 运行前控制、先例与范围

`ANALYTIC_CONTROLS.zh.md` 在执行前被冻结：1264 可由 CASE 缺 ELSE 默认为 NULL、内连接换序/别名解释；1421 可由保留同一侧的 LEFT/RIGHT 反转、行等式与分量 AND，以及 INT 输入上 IFNULL/二参数 COALESCE解释。这是 reviewer 对两条原 SQL 的静态推导；相关函数与三值逻辑见 [SQLite CASE](https://www.sqlite.org/lang_expr.html#the_case_expression)、[row-value comparisons](https://www.sqlite.org/rowvalue.html#row_value_comparisons)、[IFNULL](https://www.sqlite.org/lang_corefunc.html#ifnull)。这些控制没有实现为计时基线，不能赋予虚构的0秒运行时间。它们已足以阻止把两个 INT 对的超时/OOM包装成新的科学机会。

一手文献重点复核了 S3 与 S2。S3 的 §5.2/Lemma5.5 已给出颜色邻接度加权求和、子树乘积、类大小汇总的同型递推；将全部行别名作为 full CQ 自由变量时可对应 COUNT(*) 赋值数。其 Theorem3.3 以给定数据库D建立索引，不能被升级为未知反例合成算法。本轮特化未显示新增算法步骤。[Structural Indexing, arXiv:2601.04757v1](https://arxiv.org/html/2601.04757v1)

RCR 的 Theorems A/C 与 atomic/similarity type 确认：其 α-acyclic 同态计数范围依赖完整关系标签和 tuple overlap，强于各 FK 独立度数。作者的“双 FK 同对变量：2 vs 0”手例正确提示本片段边界；不能把 simple-tree single-edge 偷换成所有 α-acyclic 查询。[Color Refinement for Relational Structures, MFCS2025](https://drops.dagstuhl.de/storage/00lipics/lipics-vol345-mfcs2025/html/LIPIcs.MFCS.2025.88/LIPIcs.MFCS.2025.88.html)

支持“现有计数机制＋受限简单恢复没有形成申报的新合成算法”的否定结论；不据此声称所有未来 quotient 合成研究已被先例解决。P_count 的逐树归纳在明示的单边简单别名树片段下未见问题；P_lift 必须先修P1。0/21支持的是严格原查询适用性，未实作任何quotient、未测压缩比，未证明更广语义不可处理。S1/S4/S5未在本结果审查中完成全文逐项独立复核，不能将本审查当成完整文献穷尽证明。

## 冻结、证据链与未核验事项

880 个冻结精确文件路径全部重新计算 SHA256，一致；前三轮 manifest 精确文件身份也全部一致，但未重审它们的所有历史成员。执行六源文件与修复后静态审查一致，唯一 common 差异确为 `EXECUTION_ENABLED=False→True`；逆向恢复 False 的哈希等于已审版本。draft 与 registered 仅 status/registered_utc 改变，去掉这两字段后的规范哈希与允许值一致。注册时间先于冻结、先于执行；analytic control 文档包含于冻结清单。预执行“未运行/待审”文字仍是历史快照，不能覆盖真实 batch 状态。

未独立认证的边界：业务 C 的真实或完整含义、自然缺陷标签、所有 SQL 方言一致性、上游编码全局健全性、其他轮次新成果、历史整机访问记录、任意故障保护、完整文献穷尽。依已审代码路径和可见回执未见 finaltest 使用；reviewer 自己未读最终保留测试或其他未见语料，也不能从有限 artifacts 证明整台机器历史上从未访问过它们。

`REVIEW_MANIFEST.json` 为全部本地审查输入与输出提供SHA256；其中第三方依赖仅留路径/大小/哈希，不复制内容。网页使用固定版本/官方URL与锚点，保存的是 reviewer 原创来源核对说明，不宣称保存或哈希了完整网页原字节。manifest 自身哈希放在侧文件，避免自包含哈希悖论。

私有备份由根代理统一处理，本子审查未执行 git/push。作者原有 `BACKUP_BLOCKED` 与 `DATAHUB_REGISTRATION_BLOCKED` 不因读数通过自动解除；全项目完结、投稿或方法晋级均不获本轮授权。**本轮负面结论可接受，已知理论范围需修复，总研究继续。**
