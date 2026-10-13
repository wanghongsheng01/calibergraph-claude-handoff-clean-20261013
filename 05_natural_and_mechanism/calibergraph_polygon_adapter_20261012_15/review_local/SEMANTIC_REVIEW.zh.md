# #1172 观察商独立语义复核

结论：在**每个源表至多一行、冻结原始 DDL 的完整约束 C、静态数据库快照**的范围内，所提 query-specific 观察商可行。未发现语义反例。此结论不是全值可逆、官方 Polygon 原样支持、无限界证明或新科学机制。实现尚须独立审查，当前结论只针对候选语义定义。

## 核对对象与边界

直接读取 `calibergraph_coverage_boundary_20261012_09/sources_local/thrombosis_prediction__1172/{full-schema.sql,gold.sql,predicted.sql}`。两查询均为 Patient/Laboratory 的 ID 内连接和 COUNT(DISTINCT Patient.ID)，分别观察 `T-BIL >= 2.0` 和 `T-BIL > 2.0`，以及 `SEX = 'M'`。

C 包含 Patient.INTEGER PRIMARY KEY 与显式 NOT NULL；Laboratory `(ID,Date)` PRIMARY KEY 及两列 NOT NULL；Laboratory.ID 和 Examination.ID 到 Patient.ID 的外键。Examination.ID 可 NULL。DDL 没有 REAL/date CHECK、列范围或值枚举。动态 SQLite 类型是原域的一部分，不能事先把原 T-BIL 限制成普通有限实数，或把 DATE 限制成有效日期字符串。

“所有合法 SQLite 数据库”在此指满足此冻结模式的 C 且每源表行数≤1 的实例；不包括关闭约束后制造的违约状态、ALTER 后模式、被损坏数据库或额外触发器/自定义排序语义。ON UPDATE/DELETE CASCADE 是原 DDL 的一部分并应保留；本证明只观察快照查询，不证明整个修改轨迹的双向模拟。

## 正向保存论证

1. 保持各表存在性和每列 NULL 性。Patient 若存在，其存储 ID 是非 NULL 的 64 位整数。其 ID 规范化为 1。Laboratory.ID 非 NULL，合法 FK 加上至多一个 Patient 意味着 Laboratory 存在时恰指向该唯一父行；其 ID 同时规范化为 1。Examination.ID 若非 NULL 也规范化为 1，若 NULL 则保持 NULL。不可先对不满足原 C 的源数据规范化再宣称合法。
2. 原 Patient 与 Laboratory 的合法非 NULL FK 指向同一个键；此模式两列均为 INTEGER 亲和性、默认排序。对应的 ID 连接真值保持。合法强制转换形式也不需要逐值保留。约束判断必须采用实际 SQLite 行为，不能用 Python 数值相等替代 SQLite FK。
3. 对插入并完成 SQLite 亲和性转换后的 T-BIL，使用原列的 SQL 比较划分 NULL、below、equal、above。分别代表为 NULL、0.0、2.0、3.0，保持 `(IS NULL, >=2.0, >2.0)` 真值。仍为 TEXT/BLOB 的存储值属于 above；可数值转换的输入文本必须先完成 SQLite 存储转换。±Inf 对应 above/below。当前 sqlite3 绑定 NaN 被存为 NULL，故应分类为 NULL，不能按 Python 浮点比较分为 below。不可自行定义“NaN 非 NULL 实数类”。
4. 对存储后的 SEX，按 NULL、原 SQL `SEX='M'` 为真、其他非 NULL，映射为 NULL、'M'、'X'。BLOB b'M'、'm'、'M '、含 NUL 的字符串不能因解码、去空格或大小写折叠而进入 M 类。
5. Laboratory.Date 是非 NULL 的 PK 分量。由于 Laboratory 行数≤1，唯一性不需要其具体值；原 DATE/NUMERIC 亲和性允许数值 0。该变换是规范代表选择，不能描述为真实日期转换。其他未观察列只保持列存在和 NULL 性，非 NULL 代表 0 经各列亲和性转换后仍合法。没有其他 CHECK 需要保留具体值。
6. 原、像实例都满足全部 C；连接最多生成一行，COUNT DISTINCT 的非 NULL 整数 ID 最多贡献 1。因此两输出分别由唯一 Patient/Laboratory 的存在性、SEX 类别和 T-BIL 类别完全决定；两查询输出差只发生于 M 且 T-BIL=equal。

## 反向提升义务

抽象模式必须保留三表、全部列、NULL 性、PK/FK/NN 的对应约束和每表N≤1；必须在求解前固定类别、代表和解码器。每个 C 合法的抽象模型应按固定解码器生成原 DDL 的 SQLite 数据库，开启外键检查，并执行原始两条 SQL。C 合法性和原 SQL 回放均必须通过；不允许解码后补父行、补非 NULL、删除冲突行、改类别、修改 C 或为实现期望差异重新求解。

代表值的小范围是观察商内部规范域，不能被表述为原 SQLite 数据域已受 CHECK 限定。该精确性结论必须附带 N≤1：若 Laboratory 可有两行且同 ID 不同 Date，全部 Date→0 会产生复合主键冲突；若 Patient 可有两行，全部 ID→1 会产生主键冲突。因此本方案不能直接升格为更大 N 的同一证明。

## 独立 SQLite 验证

`semantic_quotient_check.py` 不导入 Polygon、不调用 solver，直接用冻结原 DDL 和 SQL。SQLite 3.43.2 下 7,500 个源实例交叉测试及 11 个存在性配置均通过完整外键检查、逐列 NULL 性保持和原 SQL 双输出相等。覆盖 64 位键两端、负/零键、浮点阈值相邻值、±Inf、NaN、数值/非数值文本、BLOB、各种 SEX 和非日期值。结果与逐输入存储类型真值表见 `semantic_quotient_check.json`。

另外检查 7 个 FK 输入边界：6 个合法强制转换形式通过；父键 -9223372036854775808 配 Python float(-9223372036854775808) 子键，被本地 SQLite 拒绝为 FOREIGN KEY constraint failed。该输入不得因为宿主语言相等而假定是合法源实例。此拒绝是原约束边界记录，不是观察商反例。

有限测试用于核对实现细节，不替代上面的全域、N≤1 论证。本次未执行任何科学 solver、benchmark、新 scientific run，也未改写旧批次文件。
