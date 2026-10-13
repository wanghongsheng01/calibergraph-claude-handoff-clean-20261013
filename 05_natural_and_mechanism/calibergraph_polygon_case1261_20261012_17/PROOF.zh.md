# #1261独立局部适配证明

这是对新SQL对的单独证明，不把#1172证明直接推广。限定09冻结#1261原SQL/DDL、每源表0或1行、标准SQLite快照语义/默认BINARY与内置函数、无TEMP/ATTACH/自定义UDF。3表64列完整保留，C仍2PK声明、3显式NN、2FK。原查询和DDL哈希分别校验。

记E、L、P为Examination、Laboratory、Patient行。任何非NULL合法子ID都指向唯一P。gold只有在E、L存在、E.ID非NULL且匹配L.ID、L.RF<20为真、E.Thrombosis=0为真时输出1，其余输出0。完整C保证L.ID非NULL且存在P；故加入P的predicted具有同一存在条件，所数Patient.ID非NULL，最多1。这里不从N1结论冒称所有基数/类型域的求解器证明。

**RF的新映射。** RF原列是TEXT亲和性。必须在存储后的原SQLite列上计算`RF<20`，其20会按列亲和性参与文本比较：'100'/'020'是真，'3'是假。NULL保持；真类映射抽象Int0，非NULL假类映射20。反向对任意抽象Int v，v<20提升为TEXT '0'，否则TEXT 'z'；两代表在原RF列的同一谓词下分别真/假。不是把所有文本按数值解释，也不按字符串hash数值排序。BLOB、非数值文本、±Inf文本化、NaN变NULL、无效UTF-8文本由原SQL谓词决定类别。

**Thrombosis的新映射。** 原列为INTEGER亲和性。按原SQLite的`Thrombosis=0`存储值比较，NULL保持，真类抽象0、非NULL假类1。反向任意抽象Int v：v=0提升为整数0，否则1；相应原谓词真假保持。SEX和T-BIL在此对SQL中未被观察，不再使用1172的M/2.0分类。

**完整C与其他列。** 保留行存在性、全部列和NULL性；所有合法非NULLID统一重命名1，其余未观察非NULL单元用0代表。Date仅用于Lab PK/NN，N≤1使唯一性空泛，原DATE亲和性允许非NULL0；这不实现通用日历语义。没有删除默认值或级联声明：原DDL原样执行、完整赋值插入，快照问题不执行UPDATE/DELETE。两个主键/三个NN/两个FK全部保留。对原DB先做真正SQLite FK/integrity/N1校验，不能以Python数值相等替代FK；反向也先验证抽象C再重命名，不能把非法模型修好。

因此对每个完整C合法、N≤1的源实例，正向映射保留上述存在条件和两个观察谓词，逐查询输出保持；对每个合法抽象模型，固定反向映射得到原DDL合法实例并保持同一查询输出。两个方向均非逐值可逆，而是查询观察保持。原文本/实数域没有被隐瞒裁剪，代码只保留本对SQL在此界限内所观察的类别。缺表列、超界、非法PK/NN/FK、错误类型和源SQL哈希漂移均拒绝。

这只证明适配层，不证明Polygon整个符号实现。运行若得UNSAT只记有界symbolic_UNSAT；若NEQ则保存抽象与具体见证，独立校验固定映射和原DDL/SQL输出，不修补或重试。两个查询在原完整C下的连接推导是独立静态理由，不能拿运行时UNSAT扩写为通用等价证明。
