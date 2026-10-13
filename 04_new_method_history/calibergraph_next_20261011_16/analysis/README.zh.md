# 第16阶段只读结果聚合器

状态：**作者静态准备完成；未运行、未import、未compile聚合器或科学代码，未生成派生实验结果。** `AGGREGATOR_STATIC_VALIDATION.json`只记录AST/结构/文本核对，不是功能测试或独审PASS。运行后仍交同一独审逐项对照raw。

`aggregate_results.py`只使用Python标准库，读registered protocol、batch、逐槽supervisor/worker、runtime freeze与可选外层time/exit JSON。它不导入scientific implementation，不连接SQL/SMT，不运行进程、不改变priority，不重试科学slot。输出仅能创建本analysis目录下的一个全新直接子目录，不覆盖既有文件。

root在科学batch结束并允许只读聚合之后使用：

```text
python3 -B -I -S aggregate_results.py --protocol /absolute/generation_replay.registered.json --freeze /absolute/runtime_freeze.json --run /absolute/round16/runs/batch_directory --out /absolute/round16/analysis/derived_once --outer /absolute/outer_time_exit_receipt.json
```

`--freeze`省略时默认protocol同目录的`generation_replay.freeze.json`；路径若不同必须显式给出。`--outer`可重复，每份仅保存path/hash和数值字段；聚合器不臆测不同外层schema或叠加可能重叠的CPU。旧06默认读取相邻`calibergraph_next_20261011_06`的registered protocol、原run和freeze；可用`--historical-root`指向恢复后的同一历史目录。registered protocol缺失或仍为draft时拒绝聚合，不以草案冒充已执行登记。

输出为`derived_results.json`及简短`RESULTS.zh.md`。新轮始终由protocol逐一建立24槽；旧06完整12槽单列引用及哈希，不合并独立样本、不继承旧analyzer的5/4/3等结果分布断言。无查询原文、原始数据库值或回放输出明文；异常消息仅保留类型/阶段/哈希并链接原收据，查询输出仅保留行数、bag差异及哈希。

收据状态分层：计划槽顺序/身份可独立支持最终batch明确NOT_RUN；正式科学结果还要求registration、protocol和runtime freeze绑定、worker输入pin和五份code hash、worker文件hash、supervisor副本及身份相符。缺失/损坏、STARTING残留、partial snapshot或placeholder留在分母，标UNKNOWN_INVALID_OR_CENSORED。无法解析嵌套slot保留invalid行及raw路径；其成本待raw独审，不猜0。NOT_RUN不以worker初始record.status或缺文件单独推断。

阶段进入与实际check分开：query stage但无实际调用证据标STAGE_ENTERED_CHECK_UNPROVEN；完整终态确实没到则null/NOT_REACHED；中断则null/UNKNOWN_OR_CENSORED。旧空sum的0保存在legacy字段，同时规范化query计时为null。runtime缺完整receipt不能证明import未开始，保留active/latest阶段证据。所有stage成本分别保存；parse在analyze内、replay inner在outer内、attempt在worker内、worker wait4在batch CHILDREN内，绝不重复相加。观测实测/尾预留、prep10、batchtail沿用原batch账；外层scope另列，不虚构全成本总和或成功者总体均值。

预先固定配对解释：每source按repeat1/2×N2/3/4对齐；分别检查(2,3)、(2,4)、(3,4)。低界“返回”仅指两遍同为sat或同为unsat，unknown不算；高界两遍必须query unknown且原因为精确相同的`timeout`或`out of memory`，两原因不混同。四个相关槽都须C SAT与实际query-check互证、完整有效receipt，且batch完整总账≤60、无batch/slot违规。其余标判据不满足或收据不足，不挑最快重复。即使出现匹配也仅为本预算下工具成本现象，NONE/NO_GO不变；最终解释仍需root/独审核对外层time/exit和raw。

C_MODEL_SANITY强制作为非query-SAT证据并保留raw scope/flag；query-SAT区分见证必须已有原模型、完整C确认、原SQL不改写、两次输出且INT/NULL bag不同等记录条件。该字段是收据条件派生，不替代独立见证审查，也不把DATE/ROUND未准入profile称为认证。

静态辅助代理建议的边界已纳入：预检查NOT_RUN分层、batch预算门、输入/代码freeze绑定、嵌套无效slot保留、query stage/check分离。功能正确性仍UNTESTED；按用户要求现在没有运行聚合器，包括没有用旧06做试运行。source/readme/静态收据与SHA清单交root统一备份。
