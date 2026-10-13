# 第16轮等待期间新增材料独立审查

结论：**PASS_STATIC_DIAGNOSIS_AND_SOURCE_SQL_PROOFS_WITH_EXPLICIT_SCOPE**。认可工程诊断的事实/推断区分，以及两个INT pair在明确语义下的手工等价证明；没有新科学运行、机械证明、实现速度基线或机制晋升。本文件不改变封存preexec的输入、授权和唯一batch边界。

主审`/root/round16_independent`；手工证明子审`/root/round16_independent/wait_budget_criteria`。只读本地文档、JSON、旧results和固定源码，做hash及字段核对；未运行SQL、SMT、目标源码/import/compile、数据库枚举、资源observer或能力probe，未改作者文件。封存preexec的9项产物哈希再次核对全部OK。

## 工程诊断

作者md SHA=`eff03a97f9c90083f533c2346519f09e2986c93a69e7c888cadf21b9e586390c`，JSON SHA=`64ce352c0f9ea63bf9e5cc191cc14c229ea6840c86c6e092ba10425070931751`，均与提交一致。

主审独立读取旧06的case00/01/02/09/10/11六份results，hash与诊断所列一致。dev03_04的三槽C=SAT，两个parse均RETURNED，保存的analyze公式数分别19/36、61/72、217/144，符号tuple数4/6、16/12、64/24；query_called=false、query verdict=null，trace都精确到`verifier.py:53`。该固定源码对输出属性UF标志做XOR并抛NotEquivalenceError，另两分支位于不同位置；`environment.compare`在公式构造完成后才调用solver。故报告正确识别为query-check前的内部比较准入异常，不能把错误文案当已验证不等价、超时或solver难度。

第四列ROUND与UNION首分支裸值的解释有合理固定源码链：ROUND附FRound，FCasePredicate经FBasePredicate继承FExpression，别名处理可转移UF标志，UNION以首分支属性对齐。旧运行没有保存触发列和局部属性对象，因此保持“静态重建”而非实际对象测量是必要且正确的。原SQL可见10000分支边界文字差异，但没有执行或具体见证，报告未将它冒称已证缺陷。符号tuple容量不是SQL输出列数，也不是53行throw条件。

dev03_07三槽C=SAT、query=UNSAT，均无replay字段或replay stage，sanity初始化为NOT_ADMITTED。固定replay仅有两个INT profile，拒绝dev03_07发生在fullC checker和sqlite import前；这只是未准入静态路径，不是实际SQLite失败。原backend确有DATE整数到ISO文本的导出分支，而replay读取raw值、用INTEGER列、只接受INT/NULL输出；真正缺口是DATE/除法/ROUND端到端认证，不能写成所有DATE decoder不存在或SQLite不支持日期。日期列C的全笛卡尔lte及非NULL语义须原样保留。

本主审独立核对的是上述六份results和相关固定源码；没有将作者所称全部events与15项源码完整核验冒充本次逐项重做。旧12分母和新24计划均不变，旧未到达query的派生0仍应在分析层为null/NOT_REACHED。

## 两个INT pair的手工证明

作者证明SHA=`8e5c1b79395a3bd9d7ab0d965503dfc16af6afc94b9212611c485d1637b4d76a`，metadata SHA=`401fdfb5cf39eb8225dfffdb5a18b2351c3b233b549ccb10cd48e9ecf1aa2cbd`，专属输出hash清单全相符。主审重新读取原03 indices9/14的原式及schema/C；独立子审重新计算四条SQL hash，与证明和原replay profile一致。

- **dev03_10：通过。** CASE分支顺序、首TRUE、默认NULL及THEN为NULL的处理相同。内连接以行出现为单位交换形成双射，重复行的重数保留；未限定PAGE_ID在两式均来自LIKES，NOT IN子查询不相关且完全相同。保留原NOT IN函数足以包含NULL与空集合行为，不需要将它转成NOT EXISTS。两边DISTINCT前bag已相同，随后去重仍相同。
- **dev03_15：通过。** 两分量普通行相等与3VL AND具有相同TRUE匹配集合。LEFT/RIGHT反转在两边都保留QUERIES；每个q的所有匹配n逐份输出，无匹配则恰一条补NULL。IFNULL与二参数COALESCE在INT/NULL及纯列/字面量下逐值相同。匹配NPV=NULL、NPV=0与未匹配补空造成的值碰撞都按相同次数相加，不混淆出现身份与输出值身份。

两项论证均允许重复、NULL、空表、不等基数、无FK匹配和负NPV，未使用任何原PK/FK/neq/gte。因此“无显式C即等价，并在完整C子域等价”的声明在所写语义下成立；不授权实验删除C。主/子审未发现源SQL代数缺口，但这仍是人工论证，不是证明助手证书。

适用范围限定为固定两对源SQL的INT/NULL、普通三值逻辑、无序bag、相同schema/name binding与快照、纯内置函数语义。不能外推至SQLite任意动态存储类型、混合类型/重载函数、驱动结果类型元数据或物理顺序。D节局部源码事实只作背景；尤其右外连接helper空输入早退未完成上层链路证明，既不认证空表编码也不据此声称运行bug。

源SQL普遍等价不能代替parser→encoder→SMT→export→replay全链正确性；也不能证明exact2/3/4覆盖up-to、混合基数或给另外两个pair背书。没有实现/计时规则识别器或成熟工具，故不能报告“0秒基线”或性能胜出。即使后续更高界UNKNOWN重复出现，也只能继续研究此实现的成本，不能单据此将两个源SQL问题称为新语义困难或把成本归因给fullC。

## 首次资源观测证据

只读核对obs0001 receipt及root外层关联记录：实际开始2026-10-11 16:46:00.753611 UTC，状态WAIT_RESOURCE，load1=4.38134765625>4，free=38%、nice15、CPUlimit[1,1]；outer记exit0，stderr为空，receipt/stdout/stderr三个hash相符。SELF0.051192+reaped CHILDREN0.001507=0.052699秒，另tail0.2，总charge0.252699；不是完整实测0.252699秒。该有效等待观测不消耗科学attempt，下一次不得早于前次开始+900秒并仍通过monotonic门。

本文件不替代后续每次outer/receipt完整性核验、最终注册与唯一科学launch审查。结果另审；原DATAHUB_REGISTRATION_BLOCKED、历史恢复BACKUP_BLOCKED及root统一私有备份职责保持。
