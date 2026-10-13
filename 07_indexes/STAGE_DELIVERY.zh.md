# CaliberGraph 阶段交付 · 2026-10-12

**这是供用户审核和后续继续工作的研究阶段包，不是可投稿稿，也不表示总体投稿工作结束。** 本次仅整理已有事实与作者文件、生成本地 ZIP 并验证解压/哈希；不新提抽象或 anti-masking 方向，不追加 SQL/solver 实验，不修改旧结果，不 commit/push。

## 已完成的原稿基础

原有窄 AST、完整合同入口审计、六臂开发实验及失败分母、状态修复、独立数值/代码/版面审阅均有冻结材料。已有 11 页文案勘误版 PDF SHA 为 `9abfd1cf57de52287c3ab48df02de46ebe99a7646ba4f2f98dbf7e2d56582516`，本次仅核哈希，不重新编译或装入 ZIP。依据：[原交接](</Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/FINAL_CALIBERGRAPH_HANDOFF.zh.md>)、[勘误版入口](</Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/wording_revision_20261011_01/README.zh.md>)、[PDF](</Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/wording_revision_20261011_01/manuscript/build/main.pdf>)。

科学负结论保持：selector 严格有效 22、flat 23，没有建立方法优势；48,910 个公开查询槽仅 6 eligible、两对可接纳 pair 均无 JOIN，不能用今天的另一个自然 JOIN 开发包改写这个旧截面。成本及未完成尝试仍按旧账本解释。自动 bbox/spacing 门仍为 UNAVAILABLE，真人作者核验/声明仍未完成；不因已有 PDF 就称投稿就绪。[原实验截面](</Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/experiments/FINAL_V5_EXECUTION_CUT.zh.md>)、[公开分母](</Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/experiments/PUBLIC_APPLICABILITY_FINAL_CUT.json>)。exit2 的追加勘误保留：14个选中槽中的7个合同STOP造成exit2，另10个未选槽不是原因。[勘误](</Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/wording_revision_20261011_01/errata/EXIT2_CAUSE_ERRATUM.zh.md>)。

## 今天的强基线成功与失败证据

ParSEval 在 #1172 的一次官方调用实际返回 EQ；独立合法控制为 1/0，九个保存候选均相等。这是一次已证实的漏区别行为，不是强方法普遍失效。进程内我方后验回放的 KeyError 原样保留，独审另行复算，不能把我方错误算给基线。[结果及边界](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_sampled_diagnostic_20261012_07/RESULT.zh.md>)。

Polygon 固定上游 commit 为 `5e18237394d025dbb805cf833b4f54c321470774`；实际运行使用串行资源适配、各次 Z3 3秒及每Z3内部512MiB，并非原官方预算/环境的速度复现。#750、#1172 的两模式均产生原SQLite合法反例；#319、#1261 的两模式均为有界符号UNSAT。四例八槽共14次Z3调用，无科学重试；三个批次墙钟分别2.249685、1.292468、1.322953秒，不能据此给统计排名。已完成覆盖为 **4/8有效开发例**，另外2例无效仍在10例分母；未准入不等于求解失败。[13包](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_polygon_pilot_20261012_13/RESULT.zh.md>)、[16包](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_polygon_case1172_20261012_16/RESULT.zh.md>)、[17包](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_polygon_case1261_20261012_17/RESULT.zh.md>)。

19包把 #1073/#45/#1526 的八个合成反例做成原DDL/C及原SQL的独立复算证据；这是3个已暴露自然查询对的8个构造，不是8个独立任务，更不增加Polygon运行覆盖。#1490仍是静态推导。合成值满足源DDL，不代表业务合理性；#1526的来源日期冲突仍不能裁决真实业务意图。[19包结果](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_sqlite_closure_20261012_19/RESULT.zh.md>)。

资源保护的工程推进包括串行适配和父程序持有/清理自有句柄。早期10/12包的资源准入失败与NOT_RUN保留，后续另获合同授权的13包成功不覆盖它们。内部512MiB不是全进程树RSS硬上限。[10包停止](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_polygon_admission_20261012_10/RESULT.zh.md>)、[11包适配](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_polygon_serial_adapter_20261012_11/RESULT.zh.md>)、[12包生命周期](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_z3_lifecycle_20261012_12/RESULT.zh.md>)。

## 真实 COUNT 修复及其范围

P1修复普通 COUNT(*) 的漏指示与 Bool+Bool；P2补分组 COUNT(*) FILTER；P3把聚合 FILTER 的裸列名按列解析。P3 的28项真实parser表达式与14项真实投影/分组算子链全部通过。独立脚本用SQLite和另一份Python参考核验四版168记录，未重跑Polygon编码器。没有执行完整 Environment.check/QueryEncoder/求解器流水线，也不覆盖其他聚合FILTER或任意字符串数值转换。[最终修复证据](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_count_parser_closure_20261012_20/RESULT.zh.md>)、[历史影响审核](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_count_parser_closure_20261012_20/review_local/IMPACT_REVIEW.zh.md>)。

四个既有Polygon案例不受这三个特定缺陷影响；保留原结果及原有界范围。001的Python3.9导入失败、002的测试解释器错误全部保留。独审为 PASS_WITH_DISCLOSED_PRESERVATION_EXCEPTION：001/002的一个未执行辅助文件在READY前变化，003实际冻结541项全匹配；不回写旧freeze。[保全例外](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_count_parser_closure_20261012_20/PRESERVATION.json>)。最小增量为包内 COUNT_P1/P2/P3.patch；未修改旧基线。

## 尚未完成的科学贡献

尚无通过审查的新方法、新定理增量、公平强基线优势或未暴露最终测试。最近有限值域方向已由作者和非作者独审共同拒绝，保留候选0个；#1172固定N手工构造只是静态数学分析，不是新实现。[方向判定](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_value_abstraction_review_20261012_21/RESULT.zh.md>)、[独立裁决](</Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_value_abstraction_review_20261012_21/review_local/FINAL_INDEPENDENT_VERDICT.zh.md>)。不重启同类抽象/anti-masking补丁，也不为避免HOLD增加样本或开队列。

## 最终事实表与继续工作的确定起点

完整单表见 [FINAL_CASE_VERSION_TABLE.zh.md](FINAL_CASE_VERSION_TABLE.zh.md)，同内容可读CSV见 [FINAL_CASE_VERSION_TABLE.csv](FINAL_CASE_VERSION_TABLE.csv)。所有行均明确版本、原约束/行界、成功/失败/未执行及独立性；独立复算不能升级为新test。

审核从本报告→最终表→所链接原证据开始。工程可复用起点为20包P3增量与固定42项回归、13/16/17包作者运行器及局部适配；它们不是新方法。后续工作必须另建目录，保留旧标记及失败，不在冻结路径重跑。当前待用户审核的是这份阶段事实和后续工作边界；本包不自动启动下一轮。

ZIP仅含显式白名单的作者代码/测试、最小增量补丁、短报告/表、来源路径与哈希清单以及纯标准库包校验器。未打包第三方SQL/DDL/官方记录、合成库原始日志、上游源码、依赖/二进制、凭据、旧稿/PDF或旧冻结全包。补丁仅含作者改动和必要的少量上下文；不包含完整上游文件。作者代码保持原字节，局部源数据哈希只是恢复引用。

这是本地源码与证据索引包，不是脱离本机即可完成科学复现的全依赖包。外部原始来源与依赖的恢复仍需单独解决，不能因ZIP校验通过便称clean-machine科研复现通过。备份批准未收到，状态为 **BACKUP_BLOCKED_USER_NO_PUSH**；未commit/push、未运行备份钩子。总体研究/投稿工作继续保留未完成状态。
