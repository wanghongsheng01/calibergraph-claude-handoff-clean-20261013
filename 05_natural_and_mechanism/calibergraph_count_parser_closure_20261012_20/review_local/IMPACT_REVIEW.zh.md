# COUNT 缺陷对四个历史结论的独立静态影响审查

结论：**本次已定位的COUNT(*)专用分支缺陷，不要求撤回#750/#319/#1172/#1261的既有结论。** 该判断逐项依据原SQL、冻结解析/编码代码、保存的真实SMT聚合式及既有SQLite回放记录；不是重新运行parser、solver或旧见证，也不认证Polygon其他路径无缺陷。原baseline与旧包均未修改。

## 共同路径证据

冻结SQLParser的parse_expression在distinct聚合分支保留distinct标志及列Attribute；普通聚合args前加False。FProject在非Grouped输入选ExpressionEncoder。四个历史SQL对都无GROUP BY和聚合FILTER。

ExpressionEncoder的缺陷分支要求同时满足`operator=='count'`、非distinct、参数Attribute.name=='*'。Count(args)辅助函数本来使用`If(non_deleted AND non_null, Int(1), Int(0))`，Count_Distinct(args)也有独立整数指示；二者不调用COUNT(*)专用分支。Avg(args)调用AggSum与Count辅助函数，不构造COUNT(*)节点。因此不能因为AVG“数学上含一个计数”就认为它受此次COUNT(*)缩进错误影响。

保存SMT提供更直接的历史路径证据：750的project约束是sum/count形式的div，分母为NULL/删除判定后的整数ite；319/1172/1261的project约束均为Count_Distinct在N≤1下的整数ite，包含非NULL与非deleted守卫。没有把countstar错误分支产生的常量0当成这些历史聚合的结果。具体公式与hash见IMPACT_REVIEW.json。

## 逐例裁决

| 历史案例 | 原SQL聚合与路径 | 既有结果与直接证据 | 本缺陷影响 |
|---|---|---|---|
| superhero__750 | 两边AVG(weight_kg)；Avg→AggSum/Count辅助函数 | UA/precise均VALIDATED_NEQ；既有原SQLite回放分别NULL/-54.0和-55.0/NULL，完整C合法且区分 | COUNT(*) P1不触及；原SQL回放反例自身也不依赖编码器总体正确性 |
| toxicology__319 | 两边相同COUNT(DISTINCT T1.element)；Count_Distinct | 两模式BOUNDED_SYMBOLIC_UNSAT；gold/pred原字节相同；保存project含整数ite | P1不触及；不能据此升级其他不同SQL或无界baseline保证 |
| thrombosis_prediction__1172 | 两边COUNT(DISTINCT T1.ID)；Count_Distinct；差异是T-BIL≥2 vs >2 | 两模式VALIDATED_NEQ；既有原DDL/SQL回放均1/0 | P1不触及；经过原SQLite回放的具体反例仍成立 |
| thrombosis_prediction__1261 | COUNT(DISTINCT Examination.ID)与COUNT(DISTINCT Patient.ID)；Count_Distinct；后者多Patient连接 | 两模式BOUNDED_SYMBOLIC_UNSAT；保存project含整数ite，完整C与局部观察商既有审核保持 | P1不触及；仍仅保留已审核N≤1有限界结果，不扩大为通用等价 |

适配器里的`SELECT COUNT(*) FROM ...`行数/约束检查是在SQLite连接中执行，不经Polygon ExpressionEncoder，不能据此把四例判为被同一编码缺陷污染。

历史有效开发例Polygon完成覆盖仍为4/8；不新增运行、不重标成功率、不删除旧结果。#750的AVG类型/除法一般性边界、各局部适配的范围、#1261的有界解释等旧限制全部继续适用。

## 本轮新发现的分组COUNT(*) FILTER问题

独立静态确认group_expression_encoder.py的COUNT(*)分支没有读取node.filter_clause。该分支**已有**`Sum([If(in_group, Int(1), Int(0)) ...])`，所以不是直接Bool求和，不应称普通group COUNT(*)具有前一缺陷中的Bool+Bool错误。

最小纸面反例是一个已有组/成员，在FILTER(FALSE)或FILTER(NULL)时应该计0，而当前分支仍按成员计1。本审查没有执行这个例子。建议P2仅在group COUNT(*)专用分支增加每个输入行FILTER观察：用ExpressionEncoder得到filter_val/filter_null，并以`in_group AND NOT filter_null AND EnsureBool(filter_val)`形成原有整数指示。没有FILTER时保留原行为；FALSE/NULL只改变该聚合的成员计数，不改变分组是否存在，已有组应输出0而不是消失。

P2须分别报告original、仅P1、P1+P2结果，保留P1不能修复分组FILTER的证据。当前其他group聚合路径也未处理FILTER，若本轮只修COUNT(*)，不可宣称COUNT(column)、COUNT(DISTINCT column)、SUM/AVG FILTER均已修复。四个历史案例均无GROUP BY/FILTER，因此本新分支也不触及它们。P2实现及新测试结果待独立审阅，当前只接受静态缺陷和最小修复范围，不提前宣称修复PASS。

## 操作边界

此次只读文件、计算哈希和解析既有JSON/SMT文本；SQL执行0、目标导入0、parser运行0、solver0、网络0、push0。不修改旧包。该报告审核的是两个具体COUNT路径的影响范围，不是全baseline正确性证明。
