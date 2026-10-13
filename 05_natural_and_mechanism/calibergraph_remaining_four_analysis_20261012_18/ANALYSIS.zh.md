# 剩余四例共同分析：停止用 N≤1 适配数量代替科学进展

结论：本轮选择的新求解实验为 **0 个**。#1490有直接等价改写推导；#1073和#1526各有每表一行的原SQL反例候选；#45的自然分组合并现象确实需要每表两行，但成熟Polygon本来支持bound=2，新增行界不是新问题。当前没有证据表明这四例形成Polygon解决不了的科学瓶颈。继续逐例修类型只能提高工程覆盖。anti-masking保持关闭；旧稿、冻结文件与已关闭批次不改。

本轮只读取冻结SQL/DDL、已有代码/输出和既有先例审计；新增SQL执行、parser/import测试、solver调用、见证回放、网络检索、commit/push均为0。下文新给出的数据库是纸面推导的**候选**，不是已运行结果，也不是官方反例数据库。官方只保留结果字符串，无法恢复其真正最小见证。每表界记N=max_R |R|，总行数另列，绝不混用。输出比较使用无序bag、保留NULL、数值相等而非列名/整数浮点显示格式；正式方言为原SQLite，不新增业务CHECK。

| 原案例 | 已有来源证据 | 最小行界判断 | 现有映射可复用程度 | 下一步裁决 |
|---|---|---|---|---|
| debit_card #1490 | 官方EQ，未保存库 | 标准SQLite内置语义下两表达式同值，未发现反例；不是N=1隐藏反例 | 可复用约束/NULL框架和消费阈值观察类别；IIF/CASE、REAL CAST/除法及输出不能直接复用1172/1261映射 | 不为再得一次有界UNSAT补适配 |
| football #1073 | 官方NEQ，结果2/1，无库 | 2行总计：League1、Match1可形成差异，N=1足够（本轮未回放） | 可复用存在性、等值类、完整C验证；必须对同一date的SUBSTR/strftime建立联合观察关系，另保留Match.id可NULL | 日期/计数语义工程；不是行数或求解成本问题 |
| california #45 | 官方6行bag对4组；旧纸面同名两校1/3分数例 | 原全域有N=1值类型候选；**分组合并这一现象**最小N=2，schools2+satscores2，总4行 | 校名/键等值关系、框架可复用；N=1全键→1及未观察值→0不再合法；必须保bag重数、AVG/NULL及两键关系 | 不再用N=1阴性结果评价分组合并；N=2仅有工程诊断价值，不选为新机制实验 |
| debit_card #1526 | 官方UNKNOWN：q2 row-variable guard，非timeout/NEQ；无库 | N=1已可构造gold非NULL/pred NULL；4个非空表各1行，总4行候选 | 可复用约束读取/验证框架；标量子查询空集/首行、日期、算术与SUM数值不能直接映射 | 单例定制成本高，且无需N>1就有差异；不开展大适配 |

## 1. #1490：已知恒等式，不是待挖掘的难反例

两查询FROM/JOIN/WHERE相同。设连接过滤后的bag为J，I(r)=1当Consumption>46.73为真，否则0（含UNKNOWN走else）。内置三参数IIF与该CASE给出同一个整数0/1。customers.CustomerID显式NOT NULL，故COUNT(CustomerID)=COUNT(*)=|J|。FLOAT与REAL转换均转到相同SQLite REAL类型，两边相同SUM后做同样的×100/除法。J空时SUM=NULL，两边NULL；非空时每个聚合输入相同。这里是按原表达式和标准内置函数的代数论证，非依赖某个N下的UNSAT，也不是本轮机器验证或业务真实数据验证。

原REAL消费值只被阈值观察，从查询观察角度有机会用“谓词真/不真/NULL”类别表示；但输出是比率，不能照抄COUNT 0/1的提升。完整5表21列及重复隐式REFERENCES、UNIQUE、AUTOINCREMENT仍需精确快照映射。投入这些适配仅为确认一个已可直接推导的改写，不提供科学收益。

## 2. #1073：行数不是障碍，日期语义和NULL计数才是

纸面候选A：League(id=1,country_id=NULL,name='Germany 1. Bundesliga')；Match(id=1,league_id=1,date='2008-08-invalid')，其余可空列NULL，其他五表空。League.country_id和Match.home_team_api_id均NULL使相关FK无需补父行；主键1合法。SUBSTR前七位为2008-08，gold计1；日期解析失败时strftime为NULL，pred计0。**预期**1/0，本轮未运行。非空INNER JOIN最少需要League和Match各一行，因此此构造若回放通过就达到N=1、总2行的下界。它证明SQL/DDL容许的区分方向，不证明真实赛事表含非法日期，也不能反推官方2/1就是这个机制。

另一个必须审的方向：原Match.id声明是`int PRIMARY KEY`而非`INTEGER PRIMARY KEY`，没有显式NOT NULL或STRICT/WITHOUT ROWID。普通SQLite行表此类PK允许NULL；保持合法可解析日期并令Match.id=NULL，则COUNT(id)与COUNT(*)可不同。现有Polygon `primary`编码却强加键非NULL，直接照搬会排除这类源合法候选。此分支也是静态语义判断，未新增执行；既有PRAGMA结构审计可作声明证据，不能替代本轮回放。

共同映射必须保持(a)League.name是否等于常量，(b)ID的等值/NULL，(c)同一date上两个谓词的**联合**真值/NULL类别。不能独立任选SUBSTR和strftime布尔值，不能把date全部映到一个正规日期，也不能以字符串hash顺序代替日期语义。只修parser名称不够。原记录的question描述月份区间、evidence用strftime解释，gold却用SUBSTR；材料没有给出“所有date均为规范日期且无时区差异”的强制约束。不得补造这一条件来消除反例。

## 3. #45：把“原问题最小见证”与“分组合并最小见证”分开

以下#45纸面候选统一使用完整合法填充值：schools.CDSCode为不同键K1（N=2时另有K2），School='S'、AdmFName1='Ricci'、AdmLName1='Ulrich'，显式非空StatusType、County、District、DOC、DOCType均填非NULL文本'X'，LastUpdate填'2016-01-01'；satscores.cds引用对应键，三个其他显式非空字段rtype='S'、enroll12=0、NumTstTakr=0；AvgScrWrite按各候选填写，其余可空列NULL，frpm为空。这里只满足源DDL，没有声称这些数值来自真实学校数据。

**全SQLite源域，N=1并不排除所有反例。** 建一行schools满足名字过滤和所有显式非空列，一行satscores以cds引用它，frpm空。AvgScrWrite虽为INTEGER亲和性，但无STRICT/类型CHECK，非数值TEXT 'x'可保留为文本；直接投影输出'x'，AVG对非数值文本按0计，预期0.0。也可考虑可存储大整数9007199254740993的直接值与AVG浮点舍入差异。两者均为未回放纸面候选；不将它们包装成真实学校业务缺陷，也不静默加0..800之类来源没有的范围。因此“原SQL最小N=2”的说法不成立。

**自然记录所呈现的同名分组合并则确实要N=2。** 原schools.CDSCode和satscores.cds均为PK，后者FK指向前者，连接至多一对一。在空/单个匹配行、且单值AVG数值保持的片段内，GROUP BY不可能把两条输出合成一条。要出现重数差异，至少两个匹配行；这迫使schools和satscores各至少两行。构造两个不同CDSCode、相同School、相同满足过滤的管理员名、分数1和3，就有gold两个元组与pred一个均值2.0，总4行，达到这个**现象类别**的最小界。若两分数都0，差异仍在2份与1份的bag重数，避免非整数平均值；它只是简化控制，不是新自然样本。

已有N=1映射把合法非NULLID统一成1，N=2时会破坏两个源PK；把所有未观察值变0也可能制造重复键或改变分组。可复用的是验证框架和等值类处理思路，不能原样复用函数或证明。N=2还需保留School是否同组、投影值、NULL、FK和重数，不是“加个bound参数即完成全域保真”。但Polygon默认bound=2且已有GroupAvg/分组公式，单纯扩大界和修正SQLite桥接不能称相对Polygon的机制贡献。

对只寻找反例的任务，不必为所有SQLite值先证明双向完备抽象：明确声明一个有限的**源合法子域**，准确编码且将SAT在原DDL/SQL回放，足以证明一个反例。子域UNSAT只能说该子域无反例。此选择可能避免无尽全类型适配，但属于已有的可靠反驳方式；同一子域/映射必须公平给两模式，不能把手工School碰撞作为仅新方法可见的seed。它也不能使新方法产生科学优势。

## 4. #1526：原pair已有N=1差异，N>1对应另一个现象

纸面构造：customers(CustomerID=1)；gasstations(GasStationID=1)；transactions_1k(TransactionID=1,Date='2012-08-25',CustomerID=1,GasStationID=1,Price=634.8)；yearmonth(CustomerID=1,Date='2012-01',Consumption=1.0)。其余可空列NULL、products空，显式NN满足，两个重复REFERENCES均指向customers1。对相同REAL常量存储/比较、标准SQLite内置函数，gold选中客户1：SUM2012=1、SUM2013=0，预期1.0；pred查24日无客户，三个消费标量均NULL，预期NULL。**未执行**。N≤1下同一yearmonth行不能同时满足2012%与2013%，pred也缺一侧标量；所以此见证混合了日期常量与缺年值语义，不能单凭它把唯一原因归为日期。

N=0时两边都只得到NULL，因此该合法候选若回放成立即达到逐表最小N=1。总4行达到此构造所需customers/交易/站点/yearmonth闭包；不声称已做全源域的机器最小化。官方UNKNOWN属于ParSEval的row-variable guard，不是Polygon超时或等价证明。

若专门研究“多月SUM被一个标量Consumption替换”，才需要额外行：例如两条交易分别25日和24日但同客户，抵消日期选择差异；同客户两个2012月10/20与一个2013月5，gold为25/30，pred首个2012月为10或20时为5/10或15/20，两种都不同。该隔离构造需要transactions2/yearmonth3/customer1/gasstation1；是纸面辅助控制，未改变原SQL，也不是原问题必须N=3的证明。不指定ORDER BY的标量多行首行语义必须保留，不能用任选值/错误处理冒充SQLite。

更关键的新**来源事实**：原dev.json第1526项question说2012/8/25，evidence却说2012/8/24，gold用25，pred用24。可以确认文本自身冲突，不能仅凭这些材料确定用户真正想要哪天。因此形式SQL不等价和“生成SQL业务错误”是两个不同标签。

## 5. 共性阻塞与固定代码中的具体问题

四例不是同一个JOIN困难分布。共同可复用层是完整源C读取、NULL/等值关系、合法模型验证和原SQL回放；当前遗漏集中在**可观察值、方言、约束和输出语义**：

- pinned Polygon以Int声明cell，除法降为SMT `div`，CAST分支直接返回输入。完整REAL/SQLite强制转换不是既有框架已经证明的语义。AVG是sum/count，单值数值类型保真不能由N=1推出。
- 未发现SUBSTR/substring/strftime的显式编码分支；这是源代码静态结论，不冒称本轮parser已报Unsupported。已有LIKE与标量子查询代码也不能笼统说全部缺失。
- `expression_encoder.py:489–499` 的COUNT(*)分支中，`indicators.append`位于`if node.filter_clause is not None`内部：若普通无FILTER COUNT(*)走此路径，则indicators为空并返回0。普通WHERE不等于聚合FILTER。#1490和#1073都有COUNT(*)，必须在后续任何正确性接纳前核查；当前只标**条件性静态缺陷**，未执行parser确认实际路径、未修、未把bug计为创新。GroupExpressionEncoder另有COUNT(*)路径，不能从此推断所有COUNT(*)都错误。
- 普通SQLite nullable PK/UNIQUE与Polygon primary/distinct的NULL行为不同；N=1可能遮掉多行UNIQUE问题，也可能错误排除NULL-key反例。完整C不是照抄constraint标签数量即成立。

这些是前端/编码正确性边界，不能计入“solver失败率”。#45多行问题则是此前自限N=1，现成Polygon默认2已直接提醒此限制。当前没有matched-cost证据支持把四例诊断为求解成本瓶颈。

## 6. 下一实验选择与仍围绕CaliberGraph的转向

**不选择新的solver实验。** #45的N=2原pair是唯一能直接检查“之前界是否排除了目标分组现象”的简短诊断候选；但它相对成熟Polygon没有新增问题，所以不满足本轮要求的新科学实验标准。若以后仅为补全工程覆盖而做，应单独标baseline sanity check，原SQL不改，同一源合法子域同时提供给UA/precise，SAT原SQLite回放；不调参、不换例，UNSAT不外推。这不是本轮执行提案或授权请求。

此前一手先例审计已经否定把增量bound、异构行向量、PK/FK推导行数、NULL计数、组大小阈值、带权重数压缩作为新机制：VeriEQL、Polygon、XData、有限模型查找和Cosette均是近邻。Few Rows的CQ阈值不能覆盖任意AVG/标量子查询，开放阈值问题也不是本项目现成贡献。把源冲突改名“不确定合同推理”同样不够：WeTune、abduction和conditional verification已在旧审计中覆盖，SpotIt+已经讨论挖掘/校验约束。故本轮新机制hypothesis仍为null，不以必须胜过baseline为目标挑案。

用户材料真正支持的一条**新证据驱动的问题澄清方向**是：CaliberGraph生成的反例，在“问题文本—附带evidence—参考SQL”有冲突时，到底能证明哪一个口径错误？能否在生成前明确区分“参考SQL间的形式差异”与“来源支持的业务错误”？1526提供一个可定位的真实文本冲突；1073的月份解释与两种函数、45的学校身份与按名称分组提供需要核实的邻近问题，但后两者不自动标成来源冲突，更不能生成隐藏业务约束。

这比成熟Polygon的输入任务多了**待认证的口径来源**，不是要Polygon替人选择真实需求。它目前只是可研究的问题，不是新算法、新定理或可投稿结果。最小后续应先做来源核验而非求解：在现有已暴露材料中固定question/evidence/gold/pred四联表，让独立审阅只标可逐字验证的矛盾、缺失和可确认一致；不把推断补成合同，不把unknown算错。保持10例开发分母，不增加样本计数或声称代表性。若未来没有独立、明确、可追溯的口径裁决材料，继续HOLD，不能报告业务错误率。

任何方法化之前须先否证最便宜控制：仅精确核对日期/实体/单位等源文本冲突并保守abstain，外加来源明确时运行成熟Polygon。若这个控制解释了全部改善，停止新机制主张；不再重启旧条件合同合成/验证器组合路线。只有出现不能由直接冲突检查、既有条件验证和Polygon解释的多个独立自然任务，才定义可证伪机制和未暴露最终测试。当前仅一项明确日期冲突，证据不足以PROMOTE；用户不提供新材料也不妨碍本轮给出这个负结论。

## 7. 交付与边界

四例的新纸面见证未回放；原官方最小见证未知。新增执行槽为0，已有覆盖仍4/8有效开发例，剩余4例未准入，原10例中另2例输入无效。没有把纸面构造加入已验证NEQ计数，也没有独立test。所有源身份与代码定位见SOURCE_EVIDENCE.json；独立分析审查另存review_local。

本轮不提交或推送，遵循最新明确要求。BACKUP_BLOCKED_BY_EXPLICIT_NO_PUSH；17包的自动审核拒绝继续保留，不尝试绕过。新报告本地可审查，原冻结包保持不变。
