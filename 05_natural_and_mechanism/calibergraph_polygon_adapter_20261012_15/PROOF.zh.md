# #1172局部观察等价适配

范围严格绑定原gold/predicted/全DDL三项SHA（代码常量），每个原表0或1行，标准SQLite内置函数/BINARY排序规则与快照SELECT语义。原查询和DDL不改；不允许TEMP遮蔽、附加数据库或自定义UDF/排序规则。不是对任意SQL、任意连接状态或N>1的证明。

## 为什么可以局部适配

在合法源数据库中，Laboratory存在时，其非NULL ID外键保证恰有唯一Patient，且连接成功。COUNT(DISTINCT Patient.ID)最多为1。令P为Patient.SEX按原SQLite比较等于'M'；令L为存在Lab行；令x为其T-BIL存储值。两个查询输出精确为：gold=1当且仅当L∧P∧(x≥2.0为真)，predicted=1当且仅当L∧P∧(x>2.0为真)，否则为0。Examination不在查询中但完整保留其行和约束。

所以x只需要NULL、below、equal、above四个可观察类别。分类必须由SQLite对插入后的值比较得到，不能用Python float/int转换猜测：REAL亲和性可把数值文本转换成数值，非数值TEXT/BLOB与数字的排序又不同；NaN绑定后是NULL，±Inf属于相应数值类别。代表值分别是NULL、0.0、2.0、3.0。两个代表数值与阈值都可精确表示，没有浮点计算/四舍五入误差。直接int(nextafter(2,+∞))=2破坏严格比较，已列负控制。

## 正向映射α：不是悄悄限制原域

对任意满足完整C且每表≤1行的原SQLite实例，先检查原DDL签名、外键、integrity_check和界限，然后保留行存在性、全部64列以及每格NULL性：

- 所有非NULL ID重命名为1。唯一Patient及完整FK保证合法非NULL子键都指向它；Examination可为NULL键。没有用Python相等来判定原FK是否合法。
- SEX按SQLite的`='M'`结果映射为'M'或'X'，NULL保留；BLOB M、尾随空格、大小写差异不会被混成'M'。
- T-BIL按SQLite比较类别映射0、2、3或NULL。
- 其余未被查询观察的非NULL单元映射0，NULL保留。所有源列仍存在。Date列只用于Lab复合主键和NOT NULL，N≤1时唯一性空泛，0为原DATE亲和性允许的非NULL值；这不是ISO日期转换或通用日期支持。

PK/NN保持；两个FK仍匹配；原非NULL主键保持非NULL。默认值未删除：原DDL原样执行且写入所有列，因此不会依赖默认值填补。ON UPDATE/DELETE CASCADE原样保留，但本问题不执行UPDATE/DELETE。无源CHECK/其他跨REAL或日期约束被略去。

因此对原域每个合法D都有合法抽象α(D)，两条查询的有序结果对保持不变。α是多对一观察等价映射，不是数值逐点同构。原实数/文本/BLOB域没有被假装等于整数域；代码显式使用有限观察类别保留本查询和C所需性质。

## 反向提升γ：先验验证，不修补模型

抽象schema保留3表64列；SEX沿既有varchar编码，其余为Int/NULL，约束仍为2个PK声明、3个显式NN和2个FK，共7项。所有同列同约束的位置按原名绑定。未给求解器灌入旧控制见证，也未把T-BIL强制等于2。

提升前先拒绝缺表/列、重复列、超N=1、非Int值、NULL主键/NN、悬空FK；这一步先于键重命名，故不能把非法FK修成1来过关。然后按事前固定的γ做相同类别映射：非NULL键1、SEX M/X、T-BIL按抽象Int相对2分0.0/2.0/3.0、其余非NULL0。即使抽象Int超64位也按明确的观察类别/键重命名提升，绝不声称原值被SQLite保存，更不是溢出后裁剪。

任意合法抽象A经γ后满足原DDL/C并保持本对抽象查询结果。实际实现仍强制原DDL插入、FK/integrity校验和原SQL回放；若有不匹配，记非法/不区分见证并停止，不修值、不再求解。原始抽象模型和提升后的具体数据库分别归档。

这证明适配层在声明范围内有正反向查询观察保持；不独立证明Polygon整个解析/编码/求解器实现正确。未来NEQ必须由真实SQLite见证支持，UNSAT仍仅记有界符号结论。一次parse/encode到求解入口的测试只证明接入可达，不冒充求解结果。

## 已发现并修复的接口边界

独审复现TEMP Laboratory遮蔽main导致校验源与查询源不一致，旧版可把输出(0,0)错误提升成(1,0)。已拒绝所有TEMP对象和附加schema，并保留首次发现证据与修复回归记录。适配接口只面向标准新SQLite连接，不支持用户替换内置COUNT/比较排序规则的连接。N>1会破坏统一键重命名/复合主键唯一性/COUNT DISTINCT计数，接口直接拒绝；其他五例不在范围。
