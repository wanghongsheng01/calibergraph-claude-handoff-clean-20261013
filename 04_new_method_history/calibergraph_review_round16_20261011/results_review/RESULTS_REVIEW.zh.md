# 第16轮唯一科学批次独立结果审查

结论：**ACCEPT_COMPLETED_24_SLOT_TOOL_DIAGNOSTIC / NO_METHOD_PROMOTION**。新16的24个预定槽均完成受监控的单次worker执行，记录有效；其中14个query UNSAT、4个query UNKNOWN(timeout)、6个比较编码异常未到query-check。不能把“24槽执行完成”写成24个SQL问题得到判定。两个INT来源满足原先指定的两遍重复工具成本判据；新机制仍NONE/NO_GO。

主审`/root/round16_independent`，成本边界子审`/root/round16_independent/wait_budget_criteria`。主审独立从raw24与旧raw12逐槽读取JSON，核source/schema/C/SQL身份、完整单次attempt、批次与supervisor/worker关联、实际check、stage计时、控制标签和保存的重放输出；未import作者聚合器。另读24份新worker events，实际SOLVER_CHECK_START与每槽调用记录一致。成本子审独立核最终化、freeze、两个observer及334个accounting快照。所有审查仅针对既有文件；无科学、SQL、SMT、目标import/compile、数据生成、资源probe或重跑。

## 原24槽分母与科学结果

两遍按预定反向顺序，均得到以下每来源结果；所有24次full-C check均返回SAT。

|来源|exact2，两遍|exact3，两遍|exact4，两遍|原SQL回放边界|
|---|---|---|---|---|
|dev03_07|UNSAT / UNSAT|UNSAT / UNSAT|UNSAT / UNSAT|无query-SAT；DATE/除法/ROUND profile仍未准入|
|dev03_10|UNSAT / UNSAT|UNSAT / UNSAT|timeout / timeout|6次C-model sanity完整原C通过、输出相同|
|dev03_15|UNSAT / UNSAT|UNSAT / UNSAT|timeout / timeout|6次C-model sanity完整原C通过、输出相同|
|dev03_04|比较编码异常 / 同|比较编码异常 / 同|比较编码异常 / 同|均NotEquivalenceError，未query-check|

24份worker结果及supervisor内嵌副本一致；全部一次attempt、无retry。18次query-check和24次C-check的stage、answer、CPU/wall、timeout参数与solver_calls交叉一致，42次solver调用均有记录。6个dev03_04收据有效、完整记载异常；其query费用null/NOT_REACHED，不是0，也不是“坏收据”。作者聚合器paired状态中的INSUFFICIENT_OR_INVALID_RECEIPTS为笼统选项，这里实际属于query判据不适用，而非完整性失败。

6个比较异常均在相同`verifier.py:53`的UF标志XOR检查抛出，发生在两个parse和analyze已RETURNED之后；comparison finally记录实际异常前耗时，状态RAISED_BEFORE_QUERY_CHECK。它不是query-SAT、已证不等价或solver超时。触发第四列的身份仍是固定源码重建，未新增局部属性对象测量。

12次新C sanity的模型来源均为FULL_C_NONEMPTY_CHECK，保存db与导出raw值一致。主审仅对这些已保存有限值复核完整表/列、exact行数、INT32范围、全部原PK、Cartesian neq、部分键FK存在性及gte，不调用作者C-checker、SQL或solver；12项全部符合原operational C。每项保存两条原SQL的既有输出bag相同，24个原SQL重放阶段RETURNED，所有标签明确非query-SAT。无实际query-SAT和区分见证。

## 重复现象与成本解释

两个INT来源的query CPU如下，每格为rep1 / rep2秒；保留两遍，不取最小值。

|来源|exact2|exact3|exact4|
|---|---:|---:|---:|
|dev03_10|0.025262 / 0.027280|0.283777 / 0.292776|0.715954 / 0.716217，均timeout|
|dev03_15|0.036522 / 0.033867|0.172462 / 0.178103|0.711704 / 0.717968，均timeout|

在两来源中，2→4及3→4都满足预定“低界返回、较高界同原因timeout、两遍重复”判据；2→3不满足，因为N=3仍得到UNSAT。这只确认该冻结工具/预算的成本现象，不证明exact域的等价单调性、一般复杂度或fullC造成瓶颈。两个源SQL已有等待期独审认可的成熟恒等式手工证明，故不可把工具超时提升为新的语义困难或方法创新；未实现/计时规则基线，不能声称胜过成熟工具。

24个worker wait4 CPU共26.406519秒；其中runtime import stage共16.598009秒，进入的18次query-check共3.982466秒。这些是worker内部组成或子集，不另加总账。INT来源N=2的worker生命周期仍约0.895–0.978秒，远大于约0.025–0.037秒的query-check。parse嵌在analyze、actual check嵌在check stage、replay内部阶段嵌在外部sanity阶段；主审逐字段核对派生phase与原记录一致，但不把嵌套phase求和称全部CPU。

4次query设置timeout=700ms，实测wall为0.716614、0.712520、0.719017、0.717027秒；请求值不是严格elapsed上限。单槽累计solver wall最高约0.724455秒，未触及2秒累计限或1.5秒watchdog门。不得隐藏正常超时返回的这段超出700ms参数的耗时。

## 调度、最终化与总账

第一observer为WAIT_RESOURCE，第二为ELIGIBLE（load1=2.69287109375、free37%、nice15）。两次开始间隔UTC约929.465秒、monotonic约929.462秒，均≥900；无补跑。两个完整outer/receipt的测量合0.085291秒，tail合0.4秒，charge合0.485291秒，不消耗科学attempt。

enabled common相较disabled snapshot只改False→True；registered协议仅改状态、UTC及三个封闭观测账字段，其他六源、原source/fullC、24槽及限额保持。最终freeze909项与allowlist、已知runtime绑定一致；固定once-lock和唯一已记载科学请求的全部关联hash相符。批次实际created为17:01:53.700777 UTC，距ELIGIBLE结束23.478715秒；具体请求时间未单独采样，但必不晚于已发生的batch创建，因此60秒准入界有有效上界证据。不能伪称精确测得请求提交时刻。本地JSON及源码无法单独证明O_EXCL系统调用实际发生或完整工具历史无其他调用；root保留原始请求chunk d74bf2与完成chunk 93b879，并对实际一次请求记录负责。

batch状态REGISTERED_SEQUENCE_FINISHED，24/24 RETURNED，无halt、无violations。成本子审核对全部worker与监控记录：worker CPU最大1.736529秒、wall最大1.847812秒、RSS最大131743744字节；261次监控样本最大load1=3.3671875，逐槽free最低35%，记录均符合预定门。采样通过不是全进程树瞬时kernel硬保证。

|总账项|CPU秒|含义|
|---|---:|---|
|科学supervisor SELF|0.759441|receipt前测量|
|全部reaped CHILDREN|32.436312|含worker与memory/ps等helper|
|科学进程树样本小计|33.195753|前两项之和|
|两次observer测量|0.085291|独立于科学进程树|
|observer尾部预留|0.400000|非实测|
|准备预留|10.000000|非实测|
|科学尾部预留|0.200000|非实测|
|保守charged总额|**43.881044**|低于60秒；不是全任务完整实测CPU|

CHILDREN内24个worker已占26.406519秒，余6.029793秒为非worker已回收子进程费用，不能遗漏或再加。外层time报28.49秒wall及33.19秒CPU（user26.05+sys7.14，0.01秒精度），与内部样本作交叉核验；不和内部CPU重复相加。所有measured样本合33.281044秒，预留10.6秒另列。写作、审查和事后聚合CPU不包含在已结束科学launch的总账中，不得将43.881044说成整轮所有工作的实测成本。

## 历史、结论边界与交付

旧06的12槽独立从原始收据再核：5 UNSAT、4 UNKNOWN、3未query-check，全部C=SAT；保留2/4/8历史界，与新2/3/4两遍24槽分开。旧13停止manifest的30项与旧15停止manifest的37项均逐hash相符；13保持NOTCOMPLETED，15保持24槽未启动。封存preexec9项与waiting_followup3项再次hash通过，没有改字节。

这仍是4个已暴露来源的开发诊断，两次冷进程不等于独立测试、冷OS cache或新样本来源。UNSAT只针对原固定官方编码的exact-N域；不能由此认证up-to、空表/混合基数、业务C真实完整或所有SQL方言。数据与native依赖的clean restore和DataHub canonical注册阻塞保持，root统一私有备份另核。

作者最终叙述（SHA256 `d2609b50971c9237eb00fd8c07ecd2f0c8bed82d09942419c6adfbbdcd5728f8`）与独审结果、费用范围和NONE/NO_GO边界一致，接受该固定版本；没有待改的实质问题。7项作者交付文件与170项本地raw出处逐hash及大小通过，raw目录成员恰好170项；12个新sanity模型保存72个物理行。最后再次核对909项freeze、旧13/15各30/37项及已封存审查12项，没有变化。170项仅哈希出处不等于远程raw恢复已通过；本审查没有审查远程Git内容。

独立派生数据见`INDEPENDENT_RAW_RESULTS.json`，成本核验见`COST_BOUNDARY_REVIEW.zh.md`及`COST_BOUNDARY_EVIDENCE.json`，历史不变核对见`PRIOR_ROUNDS_IMMUTABILITY.json`，最终作者交叉核对见`AUTHOR_REPORT_CROSSCHECK.json`。`review_result.json`与`REVIEWER_MANIFEST.json`封存本轮结果审查；不改已封存preexec及waiting_followup。整体数据/native清洁恢复、DataHub canonical登记及root统一私有备份的核验边界仍保留，本报告不宣布BACKUP_OK。
