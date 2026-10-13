# 冻结十例支持分类：独立静态核对与保存见证回放

独立结论：余下八例没有新增案例符合 **pilot13 原有 INTEGER/TEXT、N=1、完整原DDL/原SQL回放合同**。这足以支持本轮不启动新求解，但不支持“八例已求解失败”“Polygon 一般不支持这些任务”或任何方法新颖性结论。

我直接核对09包 CANDIDATES.json 中全部十例及40份来源文件的 SHA-256，读取完整原始DDL和SQL，独立在内存SQLite执行DDL、PRAGMA及EXPLAIN。没有调用Polygon解析器、编码器或求解器，没有查询实际数据。逐表/逐列/外键/类型库存及SQL编译状态与作者输出一致。我的SQLite版本为3.43.2，作者为3.53.3，EXPLAIN opcode数量不同不构成查询语义差异；本审核只用EXPLAIN判定引用能否绑定。

| 余下案例 | 独立主分类 | 具体依据 |
|---|---|---|
| thrombosis #1172 | 完整C/类型映射未闭合 | 全DDL有13个REAL、5个DATE；查询直接比较REAL T-BIL。COUNT(DISTINCT)/JOIN本身有实现。 |
| thrombosis #1261 | 完整C/类型与比较语义未闭合 | 全DDL同上；RF实际是TEXT，RF<20不是字符串hash整数比较。 |
| debit_card #1490 | 实现缺口，且完整C/类型未闭合 | IIF无对应编码分支；CAST返回输入而不实现SQLite FLOAT/REAL转换；DDL还有REAL/DATE、重复且隐式目标的外键声明等映射义务。 |
| football #1073 | 实现缺口，且完整C/类型未闭合 | SUBSTR/STRFTIME无对应编码分支；字符串BETWEEN不能由hash数值次序代替；30个REAL列必须保留。INT/VARCHAR也不是原worker映射键。 |
| schools #45 | 完整C/类型映射未闭合 | JOIN/投影/GROUP BY/AVG在代码中有实现；完整三表含12个REAL、3个DATE，包括NOT NULL LastUpdate。N=1不是独立拒绝准入理由。 |
| debit_card #1526 | 实现缺口，且完整C/类型未闭合 | IIF/SUBSTRING无对应编码分支；CAST及日期/数值/标量子查询语义尚未闭合。LIKE与visit_Query确有分支，不应笼统声称不存在。 |
| schools #26 | 无效输入 | EXPLAIN原预测SQL独立报 `no such column: T1.Street`；T1为frpm。 |
| student_club #1390 | 无效输入 | EXPLAIN原预测SQL独立报 `no such column: T2.link_to_event`；T2为expense。 |

这些分类是交叉的：所有余下八例都含原合同不接受的类型；其中两例先因无效输入停止，三个有效输入另有具体实现缺口。作者将六个有效未准入例统一写为TYPE_SEMANTICS_NOT_ADMITTED是可接受的总类，但应同时保留实现缺口与完整C映射未闭合的区别。不能把静态检查冒充运行时Unsupported异常；本轮没有新增parse/encode/solver阶段。

“所有余下例都未运行”有共同且事先固定的合同依据，不是按结果挑例：清单原顺序与十例分母保留，SQL/DDL哈希不变，所有原表列均纳入检查。#45虽查询触及的主要列为TEXT/INTEGER，未引用的frpm及学校日期/实数列仍属于完整C，不能裁掉来换取准入。原代码具有date解码分支也不等于当前SQLite类型合同已经完成日期保真验证；该分支还有越界截断，不应静默启用。未来若扩展类型或修改映射，必须承认为新合同，不可倒写本轮准入。

作者把#45既有两行反例超出N=1作为界限说明是合理的；它不能单独作为停机原因。即使N=1未找到反例，也只能得到本界限下结果。当前实际停止原因是全DDL类型与C映射未闭合。

另外，原SQLite中非INTEGER主键可空、UNIQUE的NULL语义、隐式目标外键及重复外键声明都需要逐项映射验证。N=1下某些唯一性条件可能空泛成立，DEFAULT/AUTOINCREMENT在明确提供全部插入值时也可能无需额外生成约束；因此不能把这些DDL词项一概当成数学上无法支持，只能说当前映射未被准入审计闭合。

本轮另用独立脚本回放pilot13保存的#750两个见证，没有新求解、修补或搜索见证。确认全部10表31列、每表至多1行、开启外键、foreign_key_check为空、提交成功、integrity_check为ok。UA得到gold=NULL、predicted=-54.0；precise得到gold=-55.0、predicted=NULL。见证等于各自保存raw_return，原SQL/DDL同时与09 CANDIDATES和13 FREEZE哈希一致，13包336项冻结文件哈希全部匹配。负体重为DDL允许的合成值，不是业务数据真实性声明。

因此有效输入覆盖仍为2/8；全部冻结案例分母为10，其中2无效、6有效但未准入、2复用先前运行。模式分母20：4个旧执行槽、16个静态NOT_RUN槽、新执行槽0。旧#750两条NEQ有具体数据库证据；旧#319两条只可引用为N=1有界符号UNSAT，SQL字节相同是独立事实。不能把2/2已准入案例通过写成8/8有效输入覆盖，也不能将NOT_RUN记成timeout、unknown、UNSAT或算法失败。

唯一可支持的后续问题是：**保持原SQLite类型、原SQL与完整C，并完成保真建模和具体化后，现有强方法在剩余六个有效输入上是否出现可独立验证的失败？** 这是尚待开展的准入和基线检验问题，不是已成立的新机制；如现有方法覆盖，应更换科学问题，不把兼容性补丁包装成贡献。

证据：`STATIC_AUDIT.json`、`independent_static_audit.py`、`SAVED_WITNESS_REPLAY.json`、`independent_saved_replay.py`。静态审计新数据查询0；单独旧见证回放执行原查询4次，新solver0、新见证0、进程RSS查询0、unrelated_project操作0。
