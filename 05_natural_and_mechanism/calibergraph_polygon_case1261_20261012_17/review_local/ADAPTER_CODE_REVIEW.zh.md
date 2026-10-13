# #1261 实际代码独立审核

科学适配准入：**PASS**。没有必须修复项。仅适用于本例冻结SQL、完整原C、N≤1、固定Polygon commit与本轮局部适配。该科学审核本身不扩大用户授权的一次UA→precise批次，也不替代控制器的资源及一次性执行门禁。

已逐行检查case1261_adapter.py及slot_worker.py，并核对ADAPTER.patch/WORKER.patch。新SQL hash准确对应09中的1261；DDL hash未变化。64列全部保留、全抽象schema为Int，七项C完整进入外部constraints列表；PKeys/FKeys留空是已有接入方式，非删除C。Worker固定1261、两模式、bound=1、time_budget=3及solver_timeout_seconds=3。原SQL直接从冻结源读取，未做SQL改写。SAT只有先验验证抽象C、升回原DDL、完整原C验证及原SQL回放后才能成为VALIDATED_NEQ。

原实例验证在映射之前进行：源DDL signature、FK检查、integrity_check、每表≤1，并拒绝TEMP对象及ATTACH数据库。RF/Thrombosis的投影直接在原列SQL表达式内完成；不会把TEXT词序当成数值顺序，也无需解码非法UTF8文本。反向映射先验证抽象所有列、Int/NULL、PK/NN、两FK及N≤1，再将ID统一1，RF按<20升为TEXT '0'/'z'，Thrombosis按=0升为整数0/1。其它列保持NULL性。

独立实际代码实测：independent_adapter_check.py使用另一份自行构造的SQLite oracle，2500组合逐项比对投影值、原SQL输出及升回输出；17项拒绝检查全部通过；非法UTF8 TEXT与81组含任意大Int的逆向类别通过。Python系统SQLite版本3.43.2，作者测试版本3.53.3；两者结果一致。测试未调用solver、未导入Polygon、未覆盖作者TEST_RESULTS。

已审代码SHA256：

- case1261_adapter.py：c2db90b71096f2ddb9447a62daec156e3677376b93c722bc14861881bd2334f6
- slot_worker.py：6609f41cf577a93ff81cdc0b8d5bd8c4d694b72f244683a604fd50a44492efc7

FIVE_CASE_SCREEN与HYPOTHESIS_CLOSURE符合先验选择及关闭旧机制假说要求。1490/1073/45/1526仅静态defer，未运行、未记作baseline失败。45不能声称仅N>1才有差异。本例若UNSAT只能给有限界结果，不能升级无限界、通用支持或新增分母。
