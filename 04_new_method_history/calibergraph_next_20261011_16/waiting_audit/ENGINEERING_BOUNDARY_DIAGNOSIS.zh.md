# 等待期只读工程边界诊断

结论：旧第06轮 dev03_04 在恰2/4/8三槽均触发同一个**输出属性未解释函数标记不一致**检查，于 query-check 之前退出；dev03_07 在三槽已有官方 exact-N UNSAT，但固定 replay profile 从未准入它，历史上没有执行失败的 SQLite replay。本文件只解释旧证据，不产生第16轮科学结果，不修改旧分母或新24槽。

## dev03_04：实际异常的精确触发

**旧实际证据。** [case_09](../../calibergraph_next_20261011_06/runs/generation_replay_01/case_09/results.json)、[case_10](../../calibergraph_next_20261011_06/runs/generation_replay_01/case_10/results.json)、[case_11](../../calibergraph_next_20261011_06/runs/generation_replay_01/case_11/results.json) 中，full-C均SAT，两条parse及analyze均RETURNED，query_solver_called=false、query verdict=null。三个trace完全同路：作者backend:354 → environment.compare:942 → verifier.run:103 → bag_semantics_verifier.table_equivalence:116 → verifier.cmp_funcs:53。事件收据也保存了比较编码STAGE_START，随后cleanup，未出现query-check。原工程/strict分类都是INCONCLUSIVE，保留不改。

|旧槽 / 每原表恰N行|analyze公式数（左/右）|符号输出tuple数（左/右）|query-check|终止点|
|---|---:|---:|---|---|
|case_09 / N=2|19 / 36|4 / 6|未到达|verifier.py:53|
|case_10 / N=4|61 / 72|16 / 12|未到达|verifier.py:53|
|case_11 / N=8|217 / 144|64 / 24|未到达|verifier.py:53|

**固定源码证据。** `verifiers/verifier.py:49–53` 对配对的输出属性执行 `getattr(lattr,'is_uninterpreted_func',False) ^ getattr(rattr,'is_uninterpreted_func',False)`；异或为真便抛NotEquivalenceError。trace明确落在53行，不是57行“两者都有标记但函数不相同”的分支，也不是64行通用属性类型分支。异常消息由`errors.py:3–6`固定生成，并非solver返回值。`environment.py:942–952`先构造等价公式，才提交反例公式并调用query solver.check；本次未越过前者。

**边界分类。** parse与scope编码已经返回，因此这不是语法解析失败。trace经过`environment.py:922–924`的列数返回门；两侧保存的SQL/AST均为四输出，不能把表中符号tuple数不等误当输出列数不等。该比较器本来会用DELETED及bag multiplicities比较符号表，tuple容量不同不是这次throw条件。已观察的是内部未解释函数元数据准入边界；不能改写成SQL字段类型错误、CAST不支持、查询SAT/已验证不等价、超时或solver难度证据。

**静态推断，未捕获运行时属性对象。** 第四列是最直接的触发解释：左SQL输出`ROUND(CASE … END,0) AS SALARY`；`encoder.py:911–916`为其内部表达式附FRound，`formulas/expressions/expression.py:54–63`把标记转移到别名属性。右SQL的UNION首分支第四输出为裸`SALARY`，后两分支才有ROUND；`union_all_table.py:15–26`以首分支属性对齐后续分支，`union_table.py:18–25`沿此属性做DISTINCT，`base_table.py:47–49`暴露首tuple属性。这条链解释了左有ROUND标记、右代表输出无标记的异或。但旧收据没有序列化触发列号及lattr/rattr，故“精确throw条件”是实际证据，“第四列对象身份”仍是固定源码重建，不能写成新测得事实。

**另一项仅文本线索。** 原左CASE最后分支为`MAX_SAL > 10000`；原右UNION最后分支为`MAXIMUM >=10000`，而前一分支包含`<=10000`。这个边界重叠可在原SQL文字中看到，但本次元数据guard没有判断它。这里未构造/枚举数据库、未执行SQL或SMT、未生成反例，不据此宣称业务缺陷或已证不等价。dev03_04另有静态replay拒绝理由：小数乘法/ROUND方言语义及VARCHAR相等解码未认证；它与上述实际比较器异常是两条不同边界。

## dev03_07：未准入不等于实际回放失败

**旧实际证据。** case_00/01/02分别为N=2/4/8，均full-C SAT、一次query-check返回UNSAT，strict_class=OFFICIAL_EXACT_N_UNSAT_ONLY。attempt无replay字段，也无replay stage。`contract_model_sanity.status=NOT_ADMITTED`由作者backend:260初始化；backend:295只对dev03_10/15启动C-model sanity。query-SAT重放又只在backend:365之后的SAT分支发生。故不能把这三次UNSAT写成执行SQLite失败，也不能将NOT_ADMITTED当成原SQL已经试过的拒绝收据。

**固定准入代码。** `safe_sqlite_replay.py:25–44`仅登记两个INT profile，并显式写出dev03_07拒绝理由`DATE_SCHEMA_AND_DIVISION_ROUND_SEMANTICS_UNPROVEN`。若未来以该源码调用它，144–146行会在独立full-C检查和sqlite3 import之前拒绝；这是静态路径说明，本次没有调用。

**静态语义边界。** 固定原SQL包含DATE相等、SUM布尔表达式或COUNT计数、除法、乘100及ROUND到2位；schema的两个日期列不是INT。独立full-C checker在66–68行只接收INT列；replay在151行读取raw值，在170–174行统一建INTEGER列，在206–212行只接收并比较INT/NULL输出。上述适用范围没有覆盖这个日期/比例输出任务。

**已有DATE转换，仍缺端到端认证。** 作者backend:215–223已经保留独立NULL标志并能把DATE整数映射成ISO文本；所以不能说“完全没有DATE decoder”。但当前replay并不消费这些decoded_values。固定official visitor:165–179把整数符号除数项提升至Real并处理NULL/零分母；encoder:911–916将ROUND记录为FRound未解释函数，FRound定义及visitor:1952–1954并未建立本profile的DBMS舍入一致性。源码可说明为什么尚未认证，不能外推为SQLite不支持日期。

**fullC边界。** 原日期列间lte是operational C的一部分。固定environment:695–730按所有列值的Cartesian配对构造关系并在该分支要求非NULL；任何将来的独立重放必须保留这份既有C，不能悄悄换成普通逐行CHECK。这里没有做配对枚举或执行，也没有验证业务C真实性/完备性。

## 范围、完整性与仍未知的事项

旧第06轮完整分母仍为12；本诊断只读其中两个来源的6槽，没有挑换/删除任何槽。第16阶段仍为既定4来源、原SQL/schema/fullC、N=2/3/4两遍24槽；等待调度、资源门和唯一batch规则由root维护，本文不构成重试或修parser授权。旧15永久保持停止。工程修复、增加profile或属性诊断不能标作新机制/创新。

旧6份results、6份events、backend/replay源码和注册协议共15文件已与第06轮reviewed manifest逐项哈希相符；15份引用的固定official源码均匹配runtime lock。lock本体SHA为`505e59253be72e73edf236efe647d84cfcebffe15980517072ae20230bdc38d7`且匹配旧注册协议。第16作者禁用freeze所列12文件仍逐项相符；本次只写本md/json两件新产物。精确路径、哈希、trace、JSON字段和核对项见[伴随JSON](ENGINEERING_BOUNDARY_DIAGNOSIS.json)。

仍未知：旧比较器局部属性对象未保存；dev03_04没有query-SAT模型与原SQL回放；dev03_07缺经认证的DATE/除法/ROUND端到端profile；operational C的业务真实性/完备性仍UNKNOWN。本诊断不预测新24槽结果，不把旧query阶段派生字段0当实测零成本：其3个未到达query的overlay为null/NOT_REACHED，旧收据字节不改。

作者和只读辅助代理均未运行/import/compile科学代码、SQL、SMT或枚举；未改源码/parser、priority、资源门或冻结实现。私有备份与原恢复/DataHub阻塞由root统一记录。
