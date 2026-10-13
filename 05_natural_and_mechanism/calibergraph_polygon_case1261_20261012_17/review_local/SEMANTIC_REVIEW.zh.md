# #1261 独立观察商审核

结论：所提观察商在冻结原DDL、默认SQLite比较语义、每个源表N≤1及完整C下，正反向均保留两条查询的观察结果。此结论独立推导自1261的两个原SQL，不引用1172的SEX/T-BIL证明。实际代码及接入已完成独立审核，科学适配准入PASS；具体一次性运行资源/冻结门禁由最终运行契约另行控制。

## 冻结边界

原表Examination/Patient/Laboratory列数13/7/44，总64列。完整C包含Patient.ID主键、Laboratory.(ID,Date)主键、Patient.ID/Laboratory.ID/Laboratory.Date三个显式NOT NULL、两个子表ID指向Patient.ID的外键。Examination.ID可NULL。原SQL字节hash见independent_sqlite_quotient.json。

原查询COUNT(DISTINCT Examination.ID)，经Examination.ID=Laboratory.ID连接，并过滤Laboratory.RF<20、Examination.Thrombosis=0。候选查询额外连接Patient，并COUNT(DISTINCT Patient.ID)。SEX未被任何SQL观察。

## 正向映射为何正确

1. 所有行存在性及每列NULL性逐一保留。先验证完整C及每表≤1，不允许先修复非法实例再宣称保持。
2. 非空Patient.ID由原INTEGER PRIMARY KEY约束，两个非空子ID因完整FK必须引用唯一父ID。其原存储值连接相等事实因此由统一整数1保持。空Exam.ID仍NULL，SQL等值连接仍不成立。空父表时完整FK禁止任何非空子ID。
3. RF非NULL值必须由原TEXT affinity列上执行`RF < 20`分类，而不能用Python数值强转、参数比较或CAST代替。true映射Int0，false映射Int20；NULL保持。SQLite非NULL值同非NULL常数的该比较为二值，所以覆盖全部存储类别，包括BLOB。其SQL三值观察由抽象整数比较保留。
4. Thrombosis非NULL值必须由原INTEGER affinity列上执行`Thrombosis = 0`分类，true→Int0、false→Int1，NULL保持。包括非数字TEXT和BLOB的false情况。
5. 其它列不出现在查询观察中；除NULL性外映射非NULL→Int0。Laboratory.Date只参加完整C的复合主键，但N≤1时非NULL足以保持其主键作用，不需要保留日期排序、相等域或格式。SEX同样不再需字符串域。
6. WHERE保留恰相同join行，NULL ID不参与成功join。每表≤1时COUNT DISTINCT只会返回0或1；统一重命名ID不影响每条查询的数值结果。原输出值的ID本身从未返回。

## 反向映射为何正确

对任意满足完整抽象C、N≤1的Int/NULL实例：先验证完整抽象C。保留行存在性及NULL性；全部非空ID统一1。RF Int<20升回TEXT '0'，其余非空Int升回TEXT 'z'；原TEXT列分别满足/不满足`RF<20`。Thrombosis Int=0升回整数0，其余非空Int升回整数1。其它非NULL值升回0。

因此抽象域不限于canonical 0/20或0/1，任意大小Int仍按谓词分区升回安全代表。日期升回0只声明非NULL代表，不声明真实日历日期。原DDL中没有额外日期合法性约束。升回值满足全部C；两条原SQL结果分别等于抽象SQL结果。必须在原DDL下重新装载并验证完整C，SQL保持原字节。

这证明逐查询观察保持，并不声称保留所有原数据库属性或支持N>1；尤其不推广Date代表化到多行复合主键。

## 独立实测（不导入作者adapter）

`python3 .../review_local/independent_sqlite_quotient.py`：SQLite 3.43.2；2500个RF×Thrombosis存储边界组合、11个合法occupancy/null-child形状、81个反向任意Int类别均通过。包含NULL、正负无穷、整数/实数、空串、科学记数、空白、NUL文本、Unicode数字和BLOB。所有正向均比较原SQL在原实例、抽象实例、升回实例的结果；反向测试包括超64位Int分类。零solver调用。

可核对的TEXT边界：'100'/'020'/'2'均满足RF<20；'20'/'20.0'/'3'不满足。未发现语义反例。有限测试是上述证明的补充，不是任意域穷举。

## 冻结5例选择顺序

按09/CANDIDATES过滤后的既定顺序为1261、1490、1073、45、1526。1261仅需已有COUNT DISTINCT、等值join、AND、<与=操作；新内容是本例局部观察商，无须引入新SQL operator。

1490含IIF/CASE、CAST FLOAT/REAL、SUM和比例/decimal边界；1073含SUBSTR/strftime及日期字符串BETWEEN；45涉及直接bag投影与GROUP BY AVG、同名学校及多行行为，且N=1也可能出现原输出值与AVG数值舍入差异；1526含嵌套标量子查询、IIF/SUBSTRING、LIKE、SUM、CAST与decimal。它们不能通过直接套用本例观察商取得同一证明。因此1261是此顺序中首个已独立证明可局部适配的候选；这不是断言后续候选永不可能适配。

## 允许的解释范围

若后续授权的一次UA→precise在完整C、N≤1下得到UNSAT，只能报告本例该有限界/抽象商范围内未找到差异，不得称为通用SQL支持、无限界等价、独立最终测试或新增分母。反掩盖假说已关闭，不在本审核中重开。运行资源和一次性门禁还需实际代码审核。
