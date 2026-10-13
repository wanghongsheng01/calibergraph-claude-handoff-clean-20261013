# 候选稿逐处修改建议（未应用）

目标为第24轮已交付候选稿；哈希绑定见 SOURCE_BINDING.json。没有发现必须改掉的旧实验计数：旧十对与新33对协议不同，禁止相加作为独立样本；是否存在跨轮重复也未用于去重或泛化推断。主要风险是把局部轮次表述读成全部证据。以下逐条提供精确原文与建议替换；不修改原稿。

## 1. manuscript/main.tex:22

摘要增加独立33对审计，不覆盖十对历史数字；18与1不得排名。

原文：
A separate ten-pair natural-query development inventory exposes a broader SQLite boundary.

建议：
An earlier ten-pair natural-query development inventory exposes a broader SQLite boundary. A separate later audit deterministically selects 33 pairs across 11 schemas from the same previously exposed source corpus. The ParSEval and Polygon pilot13 UA resource-adapted paths retain all 66 system--pair slots, yielding 18 and one replay-validated distinguishing witnesses, respectively; unequal semantic domains and row bounds preclude ranking these counts.

## 2. manuscript/main.tex:36

零JOIN仅限原recognizer扫描，不泛指所有公共SQL或本轮两工具。

原文：
Public eligible pairs contain no join.

建议：
The original cached-recognizer scan has no eligible public join pair.

## 3. manuscript/main.tex:68

INT-only是原v5限制，不适用于后续混合类型源DDL回放。

原文：
The executed harness requires every physical schema column to be

建议：
The original controlled v5 harness requires every physical schema column to be

## 4. manuscript/main.tex:68

区分原编码片段与后来具体SQLite回放。

原文：
Full mixed-type schemas and general DBMS overflow semantics are not supported by these experiments.

建议：
The original v5 experiments do not support full mixed-type schemas or general DBMS overflow semantics. Later source-DDL replay audits are separate and do not extend that encoder or prove general type fidelity.

## 5. manuscript/main.tex:211

旧预算保留，新预算单列；成本不可拼接。

原文：
Each arm uses a fresh process/Environment, common native library and complete input, CPU soft/hard limits of 14/15 seconds, a 25-second supervised wall limit and 1 GiB RSS limit.

建议：
Each original v5 arm uses a fresh process/Environment, common native library and complete input, CPU soft/hard limits of 14/15 seconds, a 25-second supervised wall limit and 1 GiB RSS limit. The separate 33-pair audit uses a single worker, 3-second solver calls, a 10-second system--pair deadline and 512 MiB internal Z3 limits; it does not impose an aggregate RSS hard limit.

## 6. manuscript/sqlite_case_study.tex:33

该段四对八槽与其12秒/60秒预算仅属旧轮。

原文：
We subsequently execute Polygon commit

建议：
For the earlier ten-pair inventory, we execute Polygon commit

## 7. manuscript/sqlite_case_study.tex:55

限定旧四对和具体适配版本，不能推广到本轮全部33对。

原文：
These observations defeat the motivation that existing strong symbolic methods cannot handle the selected cases.

建议：
Within those four earlier admitted pairs and their declared adapters, these observations refute a blanket claim that existing symbolic methods cannot handle the cases.

## 8. manuscript/sqlite_case_study.tex:100

时间边界更新，不能宣称包括本轮的整个工作都没有新执行。

原文：
No human gold labels, independent final test, model training or new experiment in the manuscript-integration phase is claimed.

建议：
No human gold labels, independent final test or model training is claimed. The original manuscript-integration phase launched no new experiment; the later 33-pair audit is an independently versioned development execution reported in a separate addendum.

## 9. manuscript/sqlite_case_study.tex:103

原结论仍成立，但不包括本轮非区分候选；本轮复用pilot13而未装载COUNT补丁。

原文：
Existing Polygon modes resolve the admitted examples;

建议：
The earlier Polygon modes resolve the four examples admitted under their respective local contracts;

## 10. manuscript/main.tex:235

结论新增实际收获，同时保持HOLD，不以所有baseline必须输为门槛。

原文：
These observations motivate careful contracts and failure accounting, but the exposed development evidence does not establish a new mechanism or a generalizable comparative benefit.

建议：
These observations motivate careful contracts and failure accounting. The later 33-pair audit adds independently replayed concrete witnesses and a localized unequal-arity comparison diagnosis, but does not establish a matched cross-tool comparison or a reproducible cross-schema failure law. The combined exposed development evidence still establishes neither a new mechanism nor a generalizable comparative benefit.

## 11. GO_NO_GO.tex:34

原交付后已有私有Library上传；需时间限定，不能继续无条件声称未上传。

原文：
No commit, push, external upload or submission was performed.

建议：
At the original integration cutoff, no commit, push, external upload or submission was performed. Subsequent private Library deliveries are separately recorded; no push or submission is authorized by this addendum.

## 明确保留的原结论

results_current.tex:50 的“matched domain 尚未benchmark”仍成立；selector 22 vs flat 23、零 eligible JOIN 的原扫描数字、十对中四对进入既有适配Polygon及两输入无效均保留。新轮仅用pilot13 UA，不采用COUNT P1/P2/P3；不能把其结果标为修复后版本。原scope的NO_GO与本轮实证稿HOLD分别针对旧机制和当前成稿充分性，均不代表稿件获准投稿。
