# 自然候选与完整语义边界工作包

本轮得到 **10 个有原始 SQL、完整源 DDL 和官方结果的开发案例**，不再只围绕1172挑选。实际发现包括真实等价对照、原查询缺列、ParSEval 执行器支持限制以及 Polygon 数值语义/约束回放边界。**尚无证据证明 Polygon 或 XData 在这些合法原始问题上预算内失败**，也没有新方法效果或投稿就绪结论。下一步只保留一个方案：对预选自然案例执行 Polygon 的有界、完整约束见证准入检查，比较其原生 UA 与同代码 precise 模式。

本轮新增 SQL 执行、SQL 解析器包导入、基线、求解器、训练、安装与队列均为0；仅运行标准库 JSON/文本提取与哈希校验。旧稿、旧冻结结果、1172唯一尝试标记与 unrelated_project 未改。

## 事先规则与全部分母

读取新候选前保存 `SELECTION_PROTOCOL.json`，SHA-256 `fe00aafe46fc18eeefb0548b6bff69247307605ceafb1b609f39b24de8bb1d90`。固定来源为 ParSEval commit `88cfe245bcf249a5b0df561a6b09c116ff2a2896` 的 [官方运行37547685455](https://github.com/sfu-db/ParSEval/actions/runs/37547685455)，既有 artifact `11452059162`，不下载其他结果包。

固定1172为旧锚点；其余按 JOIN 与聚合词法筛选，EQ、NEQ、未决各最多3条，按固定前缀与 `dbid/index` 的 SHA-256 排序，每数据库最多2条，保留原结果，不按本方法胜负、难度或耗时挑选。选择规则、逐条去留与提取器均已保存。词法筛选不冒充 SQL AST：#26 的字段名含 `Count (`，产生已识别的词法假阳性，保留它而不临时补选。

| 范围 | NEQ | EQ | SYNTAX_ERROR | UNKNOWN | TIMEOUT | 总计 |
|---|---:|---:|---:|---:|---:|---:|
| 官方全包 | 853 | 572 | 97 | 10 | 2 | 1534 |
| JOIN+聚合词法池 | 364 | 140 | 41 | 4 | 2 | 551 |
| 10例（含旧锚点） | 3 | 4 | 2 | 1 | 0 | 10 |

词法池没有缺失 schema 的记录。两个 TIMEOUT 未被冻结排序选中，不换样补入；全包理由分别为两方向生成超时、一方向生成超时。它们只证明官方报告了预算截断，不证明非等价或不可支持。分层样本不能估计总体失败率。官方耗时来自作者8 worker环境、包含各阶段、无逐例 CPU/RSS/solver明细，不能拿来与 Mac 或其他系统作公平速度比较。

提取的10例 SQL 均逐字核对同版本 `dev.json`/`dail.txt`；C 按官方脚本 `;\n` 拼接该数据库**全部** DDL，逐字核对 `schema.json`。既有 ZIP 的结果成员与 JSONL 字节一致。这里 full-C 指源文件声明的全部约束，不包含未记录的业务常量或其他外部约束。每例原文在 `sources_local/<case>/`，哈希及路径见 `CANDIDATES.json`；不删表、列、PK、FK、NOT NULL 或改查询。

## 逐例证据与边界

所有“静态”结论都不是本轮执行结果。官方 NEQ 包仅保存截断的输出字符串，未保存候选数据库，因此不能据此独立复算合法性。以下时间单位均为作者原 wall 秒。

| 原案例；全部源表数 | 官方结果/秒 | 当前可确定的分类 | Polygon静态边界与缺失证据 |
|---|---|---|---|
| thrombosis_prediction/1172；3 | EQ / 2.727 | 旧实测确认漏掉合法NEQ；9候选被同ID记录掩盖 | COUNT DISTINCT与NEQ分支存在；REAL阈值、SQLite类型与完整C映射未准入；不能将无补偿行当创新 |
| toxicology/319；4 | EQ / 1.727 | 两 SQL 逐字相同，是真等价对照 | COUNT DISTINCT、JOIN、字符串等值路径存在；复合PK、FK、非空及字符串解码须完整映射；无本例运行 |
| thrombosis_prediction/1261；3 | EQ / 4.950 | 原FK下的等价，静态证明如下 | 加入父表JOIN不自动形成错误；RF为TEXT却与数字比较，SQLite亲和性是跨引擎准入缺项 |
| debit_card_specializing/1490；5 | EQ / 5.787 | 有合理SQLite等价推导，暂不算独立确认真等价或漏判 | IIF/CASE、FLOAT/REAL CAST与SUM比值；Polygon CAST被擦除，数值/函数语义不等价于原SQLite；不支持成本比较 |
| superhero/750；10 | NEQ / 0.330 | 官方输出10.0/NULL；另有完整C静态反例 | JOIN、AVG路径存在；一般AVG整数除法与SQLite不同。N=1时可收窄到单值AVG，作为下一准入对象；原版实际支持/耗时未知 |
| european_football_2/1073；7 | NEQ / 1.484 | 官方计数2/1，未保存D，未独立复算 | SUBSTR/strftime及日期字符串合法域；读取的encoder没有这些函数的直接处理，parser改写是否覆盖未核，故不宣称实际抛错或实测支持 |
| california_schools/45；3 | NEQ / 0.866 | 官方输出保留行与按School聚合后不同；有静态合法反例 | GROUP BY/AVG有路径，但可能多行，整数AVG精度和NULL分组/袋语义须准入；不能原样称精确SQLite支持 |
| debit_card_specializing/1526；5 | UNKNOWN / 3.790 | 官方q2为“A sum does not bind its row variable”，已定位执行器保护条件 | 这是已报告支持边界，不是timeout或EQ；含标量子查询、IIF、CAST、LIKE，原完整语义与标量多行行为未准入 |
| california_schools/26；3 | SYNTAX_ERROR / 0.103 | predicted引用不存在的frpm.Street等列；无合法查询对 | 不作为生成算法失败；也是上述词法假阳性。不修列再算原案例 |
| student_club/1390；8 | SYNTAX_ERROR / 0.071 | predicted引用不存在的expense.link_to_event | 不作为难例或生成器失败；不自动补JOIN改变原SQL |

**#1261的静态等价证明。** gold 的 Examination–Laboratory 内连接已使输出 ID 非空；Laboratory.ID 的原 FK 保证相应 Patient 存在，Patient.ID 为PK。predicted仅多连该父表，再COUNT DISTINCT同一ID，筛选的RF与Thrombosis保持一致。因此合法C下ID集合相同。即使RF的SQLite亲和性复杂，它对两查询是同一谓词；不能把多一个JOIN误认成漏检。

**#1490的保守判断。** 两侧条件求和相同意图、连接中的CustomerID非空，故COUNT(CustomerID)与COUNT(*)相同。IIF/CASE及FLOAT/REAL转换还需锁定实际SQLite语义与空输入处理；本轮不执行或扩大文献核查，因此仅标“静态等价候选”，不拿它作真值标签。

**#750的静态合法反例。** gender一行 `(id=1, gender='Female')`；superhero一行 `(id=1, gender_id=1, weight_kg=10)`，其他可空列NULL，其他八表为空。原10表的PK、NOT NULL、全部FK满足；gold为10.0，predicted的gender_id=2无输入，AVG为NULL。没有给源C发明“Female必须id=2”。这是本轮数学推导，不是新增SQL执行或官方候选恢复，也未用于生成器seed。

**#45的静态反例。** schools两行不同CDSCode、相同School名称且管理员名均满足谓词，satscores对应键各一行、AvgScrWrite为1和3，其他可空列NULL、frpm空。源PK/FK/非空可满足；gold两行，predicted一组平均2.0。这里只证明存在合法差异，不证明任一基线生成策略会找到它。

## 支持边界已落实到代码，未把缺口称为创新

ParSEval [scripts/disprove_bird.py](https://github.com/sfu-db/ParSEval/blob/88cfe245bcf249a5b0df561a6b09c116ff2a2896/scripts/disprove_bird.py) 将两侧输出转为最长300字符的字符串，没有导出counterexample；#1526 的具体错误来自 [instance/machine.py:718–726](https://github.com/sfu-db/ParSEval/blob/88cfe245bcf249a5b0df561a6b09c116ff2a2896/src/parseval/instance/machine.py#L718) 的绑定检查。缺逐目标/求解轨迹，因此不能从UNKNOWN再推断哪个编译阶段导致该绑定缺失。

官方测试包含边界谓词、JOIN去重、NULL计数、超时分类和所有数据集schema目录导入；它们是支持主张的可检查入口，**本轮未运行，不能报PASS**，也不是新的自然案例。原测试没有提供上述10例各自完整见证。`SOURCE_BOUNDARIES.json` 保存准确路径、行锚和哈希。

Polygon固定commit `5e18237394d025dbb805cf833b4f54c321470774`：

- `expression_encoder.py:145–149` 的AVG为sum/count；`smtlibv2.py:101–102,156` 将除法输出为SMT `div`、cell声明为Int。一般整数输入的AVG可为小数，所以SQL有处理分支并不等于SQLite数值保真。
- `expression_encoder.py:611–612` 的CAST直接返回原操作数，不能作为精确FLOAT/REAL转换证明。
- `integrity_constraint.py:15–39` 未识别约束只warning；`mysql_tester.py:161–173` 创建列而不生成原完整约束，手工完整性失败仅记录日志。官方“Refuted”不自动等于原SQLite/full-C的合法见证。
- 原生UA和同代码precise共享上述前端/语义/约束映射；precise不能修复它们。上述均是静态实现边界，不是本例已实测错误，不作为新方法贡献。

XData仍只能确认既有论文覆盖JOIN、聚合、去重与差异传播目标；固定artifact的核心Java、实际类路径、原SQLite方言和这些10例的运行均未核实。逐例均标 `CORE_IMPLEMENTATION_UNVERIFIED / NOT_RUN`，不凭论文或旧NotKilled日志填成本/成败。相关边界沿用已独审的 `mechanism_synthesis_20261012_02/XDATA_EVIDENCE.json`，本轮不重复综述或绕过访问限制。

## 唯一下一方案：完整约束、原语义下的见证准入与成本检查

**具体问题：** 在带原完整C的自然查询上，已发表完整语义方法的符号NEQ能否以低成本转成原SQLite的合法见证？能否严格分离“无编码分支”“编码/解码语义不保真”“真正搜索预算耗尽”？先建立一个可证明的小类型片段，才有资格研究其外部的精度—成本边界；不是修parser或发现整数除法就声称突破。

按事先选择规则，#750是第一个具有JOIN/AVG直接编码路径的选中官方NEQ。它**只通过算子入口筛查，未通过类型/约束语义准入**。下一步只做一个两案例pilot：#750为正例、#319为字面等价负对照。#1172仍是旧开发背景，不重跑。固定每源表行上界N=1，保留全部表/C；#750的两个AVG各至多一个非NULL输入，因此避开多行小数平均问题。这个限制公开收窄可搜索数据库域，只允许有效NEQ主张，不能声称无界或完整SQLite等价。不得给基线提供上面的反例、固定gender映射或改变原SQL。

pilot中两臂仅为**官方Polygon UA 与同commit precise**，使用同N、类型域、完整C映射、输入、副本隔离、solver版本、种子和候选复核器。适配器只做格式/全约束传输和原DDL下见证认证，不改算法或运算语义；每个C条目必须有对应证据，未知即停。若N=1仍无法保持谓词/NULL/键/字符串等值与具体化，则该臂记 `ADMISSION_BLOCKED`，不运行更宽域、更换样本或悄悄修正语义。ParSEval当前仅保留官方参考结果；它没有在本轮获得与Polygon相同的有限行界准入，不将其官方0.330秒纳入公平对比。XData同理。

强基线成本必须分解成 schema/parse、公式构造、solver、model导出、全C验证、原SQL复核和进程总开销。保留solver调用/检查数、SAT/UNSAT/unknown、候选数、合法NEQ数、拒绝见证原因、wall/CPU/RSS；两臂同外部资源上限，实际内部调用不同就报告成本，不假称exact-work公平。输出定义只用“已认证NEQ／给定边界未找到／unsupported／timeout／资源停止”，不把EQU/UNSAT升级成全局等价。

这是**尚未执行**的准入预案：2例×2臂，最多4个串行worker，每worker墙钟10秒、自身CPU10秒；每次solver timeout不超过3秒，并受worker总时限约束，内部调用次数不限量但逐次计费；1GiB采样RSS停止、50ms名义采样且允许超冲。全部科学worker总墙钟最多40秒、另预留最多20秒用于独立复核，总pilot父进程截止60秒、0重试、0GPU/LLM/训练。启动前重新核Mac/unrelated_project状态和独占锁，不沿用旧资源观察。若引擎的solver子进程不能被整个进程组回收、RSS不能覆盖进程树，先停止，不把单worker统计冒称全树限制。

可证伪结果：若两臂均便宜地产生合法见证，#750不是成本难例，记录正结果并放弃其困难性假说；若仅出现语义/适配缺口，只形成工程修复任务；只有准入通过且合法目标已知、在匹配预算下出现可复现搜索差异，才值得另立机制假说并引入未暴露自然样本。任一结果都不会把anti-masking变成创新。当前不修改稿件、不扩队列、不投稿。

## 独立性与交付

这10例全部来自与1172同一个BIRD-dev/DAIL预测结果包；#1261还共享thrombosis数据库。其他数据库不等于来源独立，源码相同也可能有语义重复。旧48910前端扫描与本包的全部语义重叠未彻底核清。因此1534条经本轮提取器访问的记录全部记入开发暴露清单，10例均为 **DEVELOPMENT，0新test**。官方测试为人工fixture，另列不混入自然案例。

作者原始SQL/C只存本地 `sources_local/`，私有Git仅备份作者分析、抽取器、来源/哈希、选择清单与恢复指引，不重新分发第三方材料。历史 raw/native 恢复 `BACKUP_BLOCKED`、研究源 `DATAHUB_REGISTRATION_BLOCKED` 保留。作者外审另存；旧独审不替代本工作包审核。
