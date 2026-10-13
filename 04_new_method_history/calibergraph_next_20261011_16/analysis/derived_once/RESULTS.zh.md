# 第16阶段收据派生（待独立核对）

结论范围：NONE / NO_GO，仅已暴露开发集的工具成本诊断。新24槽与旧12槽分别列示，未合并独立样本。

|槽|repeat|N|收据状态|C|query|UNKNOWN原因|异常类型|
|---|---:|---:|---|---|---|---|---|
|dev03_07_exact2_rep1|1|2|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_07_exact3_rep1|1|3|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_07_exact4_rep1|1|4|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_10_exact2_rep1|1|2|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_10_exact3_rep1|1|3|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_10_exact4_rep1|1|4|RECORDED_COMPLETED|sat|unknown|timeout|null|
|dev03_15_exact2_rep1|1|2|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_15_exact3_rep1|1|3|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_15_exact4_rep1|1|4|RECORDED_COMPLETED|sat|unknown|timeout|null|
|dev03_04_exact2_rep1|1|2|RECORDED_COMPLETED|sat|null|null|NotEquivalenceError|
|dev03_04_exact3_rep1|1|3|RECORDED_COMPLETED|sat|null|null|NotEquivalenceError|
|dev03_04_exact4_rep1|1|4|RECORDED_COMPLETED|sat|null|null|NotEquivalenceError|
|dev03_04_exact4_rep2|2|4|RECORDED_COMPLETED|sat|null|null|NotEquivalenceError|
|dev03_04_exact3_rep2|2|3|RECORDED_COMPLETED|sat|null|null|NotEquivalenceError|
|dev03_04_exact2_rep2|2|2|RECORDED_COMPLETED|sat|null|null|NotEquivalenceError|
|dev03_15_exact4_rep2|2|4|RECORDED_COMPLETED|sat|unknown|timeout|null|
|dev03_15_exact3_rep2|2|3|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_15_exact2_rep2|2|2|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_10_exact4_rep2|2|4|RECORDED_COMPLETED|sat|unknown|timeout|null|
|dev03_10_exact3_rep2|2|3|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_10_exact2_rep2|2|2|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_07_exact4_rep2|2|4|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_07_exact3_rep2|2|3|RECORDED_COMPLETED|sat|unsat|null|null|
|dev03_07_exact2_rep2|2|2|RECORDED_COMPLETED|sat|unsat|null|null|

两遍各N的配对和所有预定高低界比较见JSON paired_diagnostics；缺收据/阶段未到不补0。
C-model sanity永远不作query-SAT见证；重放仅记原收据证据，独立验证尚待完成。
完整成本查看JSON逐槽成本、batch账与外层path/hash；phase嵌套、worker/CHILDREN及outer范围不重复相加。
外层time/exit收据未在此工具内做schema认证，最终生命周期成本结论仍待root及独审。

## 旧第06轮完整12槽（历史，未与新槽合并）

|槽|N|C|query|收据状态|
|---|---:|---|---|---|
|dev03_07_exact2|2|sat|unsat|RECORDED_COMPLETED|
|dev03_07_exact4|4|sat|unsat|RECORDED_COMPLETED|
|dev03_07_exact8|8|sat|unsat|RECORDED_COMPLETED|
|dev03_10_exact2|2|sat|unsat|RECORDED_COMPLETED|
|dev03_10_exact4|4|sat|unknown|RECORDED_COMPLETED|
|dev03_10_exact8|8|sat|unknown|RECORDED_COMPLETED|
|dev03_15_exact2|2|sat|unsat|RECORDED_COMPLETED|
|dev03_15_exact4|4|sat|unknown|RECORDED_COMPLETED|
|dev03_15_exact8|8|sat|unknown|RECORDED_COMPLETED|
|dev03_04_exact2|2|sat|null|RECORDED_COMPLETED|
|dev03_04_exact4|4|sat|null|RECORDED_COMPLETED|
|dev03_04_exact8|8|sat|null|RECORDED_COMPLETED|
