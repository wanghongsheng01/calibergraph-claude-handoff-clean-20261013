# 剩余四例静态分析独立审核

结论：**PASS，无未解决的must-fix**。本审核仅阅读18包、冻结原SQL/DDL/dev.json、既有源码与历史审计，计算文件哈希；没有SQL执行、SQLite回放、目标import、parser运行、solver、网络、commit或push。下文确认的是纸面推导与证据标记，不把任何新候选升级为已复算反例。

## 四例核对

- **1490：** FROM/JOIN/WHERE相同；customers.CustomerID显式NOT NULL，所以COUNT该键与COUNT(*)对相同连接bag一致。IIF(P,1,0)与CASE WHEN P THEN 1 ELSE 0 END具有相同NULL/真假分支；FLOAT和REAL转换同属SQLite REAL，余算式相同。空bag两边SUM为NULL。等价推导成立，属于标准内置语义下静态论证，非本轮机器证明；不需要再以某个N的UNSAT证明新机制收益。
- **1073：** League1+Match1满足两个查询的非空INNER JOIN下界；其余五表可空，League.country_id、Match.home_team_api_id置NULL合法解除DDL中相应FK。date='2008-08-invalid'的SUBSTR前缀满足区间而strftime预期NULL，构成N=1、源表总2行纸面候选。另一分支Match.id为`int PRIMARY KEY`，非`INTEGER PRIMARY KEY`且无显式NN/STRICT/WITHOUT ROWID，原SQLite普通行表可允许NULL；因此COUNT(id)/COUNT(*)分歧也须保留。不能把Polygon primary的非NULL编码当原DDL完全相同。两分支均未回放。
- **45：** 完整C包括schools/satscores非空TEXT主键与后者FK；一对一匹配使纯分组合并至少需要两行school及两行satscores，N=2、总4行的下界与构造吻合。此下界只属于分组合并现象，不属于原SQL全值域。INTEGER affinity不禁止TEXT 'x'，原值投影与AVG的数值转换可在N=1有纸面差异；大整数舍入是另一个纸面方向。已要求并核实补全schools全部显式NN，以及satscores.rtype/enroll12/NumTstTakr，当前两类候选共享合法代表，无需补frpm行。未把零分控制或非业务文本说成真实学校记录，未声称执行通过。
- **1526：** 4个非空源表customers/gasstations/transactions_1k/yearmonth各1行的候选，满足显式NN、PK/UNIQUE和yearmonth重复customers REFERENCES，products可空；gold连接站点需要其行，yearmonth需要customers父行。原查询在纸面上得到1.0，pred由于24日查询空集而为NULL；同一yearmonth行缺另一年度标量也参与差异，所以没有把唯一原因归为日期。N=0全空两边NULL，N=1候选若回放确认即达到逐表最小界；未宣称全源域机器最小化。多月辅助控制为transactions2/yearmonth3，明确只是隔离现象，不是原pair必须N=3。

## 原材料与代码定位

直接读取冻结dev.json中question_id1526：question写2012/8/25，evidence写2012/8/24，gold用25，pred用24。**文本冲突已由读取确认**；真实业务日期、真实数据分布和业务错误标签仍未认证。1073和45不自动升级为文本冲突。官方1526是UNKNOWN及row-variable guard，不是Polygon失败，也不是已验证NEQ。

`expression_encoder.py`中COUNT(*)的indicators.append确实缩进在filter_clause非NULL分支内。普通无FILTER调用若走此路，列表为空；源码Sum构造/序列化还须按同一路径理解，报告没有称本轮已复现错误。`sql_parser.py`只有显式groupby键创建GroupBy，query_encoder与project源码显示普通非Grouped投影走ExpressionEncoder，提供更强静态路径依据；仍未执行外部parser验证原SQL的实际AST。GroupExpressionEncoder存在另一COUNT(*)路径，报告未错误推广到所有COUNT(*)。

固定environment默认bound=2、既有分组/AVG代码、Int cell/SMT div及CAST直接返回输入均可在源码定位。它们足以支持“既有N=2能力不能作新颖性”以及“SQLite语义桥接尚需工程验证”，不足以支持本轮宣称目标parser或solver已失败。

## 科学裁决

同意选择0个新solver实验，维持anti-masking关闭与hypothesis=null。旧先例审计明确覆盖递增bound、形状/基数传播、NULL计数、重数压缩、条件推理/abduction/验证器组合；18包没有把这些换名后重新PROMOTE。来源口径澄清目前只是一项真实文本冲突支持的问题定义方向，必须面对直接冲突检查加保守abstain和成熟Polygon的简单控制，不能从一个已暴露案例推导方法贡献或业务错误率。

保留10例开发分母、8例有效、4例已有完成运行、4例未准入；本轮纸面候选不增加已验证NEQ、成功率或独立测试数。完整32项SOURCE_EVIDENCE文件hash匹配。旧文献结论作为已存审计复用，未做新检索或新颖性认证。

唯一审中修正是#45必填字段具体化，作者已修且静态核对通过。最终文件hash及检查项见INDEPENDENT_REVIEW.json。既有17文件未编辑。本审核不验证或重试备份/来源注册，也不授权运行任何新案例。
