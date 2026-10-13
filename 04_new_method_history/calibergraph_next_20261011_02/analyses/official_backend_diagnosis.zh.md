# 官方后端实际运行诊断：02 development smoke

这是研究作者对已有运行日志的诊断，不是独立审查。本次只读取报告、监督回执和冻结源码，未再次运行 parser、solver 或 SQL，未改动冻结代码、协议、01或旧根。数据为已经曝光的6组12条 development 原SQL；不是新的自然测试或保留测试。

**结论：旧公开结果“6个eligible且无JOIN”首先暴露的是窄recognizer/完整合同bridge的覆盖边界，不能解释成官方VeriEQL不会处理JOIN或求解器失败。** 此次完整官方入口在6/6组上完成原SQL双侧解析、编码和查询solver check，6/6完整C先验检查均为SAT。查询check为8.045–69.914毫秒CPU，无UNKNOWN、超时或资源停止；本开发集、此精确形状下没有展示待解决的solver性能难点，也没有建立任何新方法收益。

## 1. 两个入口的证据应分开

冻结01诊断说明：48,910个公开槽位的v4结果来自cached-AST适用性扫描，47,437槽到达recognizer，仅6槽eligible且leaf_count=0；扫描没有调用query solver。派生表、额外子句、重复基表、单输出单聚合和类型等门会先拒绝；v5完整合同bridge还要求整个schema为INT并拒绝原PK/FK。这些限制属于旧实验入口，不是完整官方前端的支持上限。依据：[冻结01诊断](../../calibergraph_next_20261011_01/audits/code_diagnosis.zh.md) §1–4。

本次使用冻结官方源码的`Environment → create_database(所有表) → add_constraints(完整原C) → analyze(两个原SQL) → 原compare`。新增代码只拦截compare输入以分离计时，然后调用绑定的原compare，并用透明solver代理记录实际check。没有使用旧v5窄bridge，没有删除类型、表、PK/FK或改写查询。数据组原编号依次为LeetCode 182、614、1075、1581、1587、1715；6组均含JOIN路径。准入6/6只说明这6组具体输入成功，不能外推为48,910槽均已适配。

## 2. 每组结果和阶段成本

下表单位均为**毫秒CPU**，来自成功报告的`exclusive_phase_cpu`和对应stage字段。parse是两个原SQL的合计；Scope编码已减去嵌套parse计时；compare编码单列；query check是实际官方solver阶段。非空C检查包含其solver创建、提交、check及SAT模型全事实核验；这些是带仪器开销的阶段测量，不是裸求解内核基准。每组总CPU另含建库、IC、日志、cleanup等，因此不可只以query check代表端到端成本。

| pair | parse | Scope编码 | compare编码 | query check | IC准入 | 完整C非空检查 | 每组总CPU | 原始query verdict / 有效标签 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| dev_01 | 60.112 | 5.692 | 4.312 | 8.045 | 0.694 | 11.814 | 100.487 | SAT / DIALECT_UNKNOWN |
| dev_02 | 4.613 | 10.767 | 4.433 | 11.463 | 0.845 | 8.623 | 48.345 | UNSAT / exact-shape official |
| dev_03 | 5.079 | 16.282 | 5.411 | 69.914 | 1.673 | 9.158 | 118.602 | UNSAT / exact-shape official |
| dev_04 | 3.790 | 18.657 | 5.373 | 19.744 | 1.383 | 9.559 | 67.325 | UNSAT / exact-shape official |
| dev_05 | 4.645 | 21.057 | 5.809 | 31.258 | 1.512 | 9.397 | 83.943 | UNSAT / exact-shape official |
| dev_06 | 6.283 | 21.182 | 4.078 | 14.403 | 2.051 | 9.626 | 68.042 | UNSAT / exact-shape official |
| 合计 | 84.522 | 93.637 | 29.416 | 154.827 | 8.158 | 58.177 | 486.744 | 1 SAT；5 UNSAT；0 UNKNOWN |

六组完整C检查全部SAT，每阶段均登记500ms timeout；query check均返回。原C条款数依次为1、2、4、3、4、7；完整非空检查实际提交事实数依次为13、12、36、37、42、53，包含基表/类型/行存在事实与完整C。此非空门避免把矛盾C下的vacuous UNSAT当成功。

成功worker报告CPU为**1.220708秒**（user 1.133081 + system 0.087627），自报峰值RSS **118,849,536字节**。848个冻结文件核验用了0.055778秒CPU，native及官方模块导入用了0.599360秒；两者合计0.655138秒，超过本次全部query check合计0.154827秒。六组case合计0.486744秒；其余差额含启动、日志、GC及报告等开销。最早的dev_01首条parse为57.644ms，后续单条parse约1.466–3.153ms；单次串行观察不能将首条差异归因于查询复杂度，可能含惰性初始化。

监督器记录完整子进程wall为**1.380272秒**；worker内部wall为1.289033秒，起点更晚，不能替代前者。这里没有重复试次、误差估计、其他n或更大数据证据。可以说初始化是本次短worker的最大已记录阶段，不能据此宣称官方后端一般由初始化或solver主导。

## 3. exact n=2、完整operational C与方言边界

本协议固定每张原始物理表**恰好两行且均存活**；所有未引用列仍存在。这不是每表0..2行，不包括空表或异构行数向量，也不是有限界完备性或无界等价定理。5个UNSAT的准确标签是`UNSAT_EXACT_SHAPE_OFFICIAL_SEMANTICS`：在本锁定官方编码的精确形状中未存在反等价模型；不能改写为“SQLite证明等价”“≤2行等价”或“一般等价”。此时没有SAT模型，因此没有进行原SQL反例回放。

`OFFICIAL_OPERATIONAL_IC_V1`保留原C，但忠实解释为官方实际操作语义：组合PK所有分量非NULL且元组唯一；FK使用双方非NULL的严格相等；`gte(col,0)`每行非NULL且≥0；跨列`neq`约束两整列的全部Cartesian配对不等且非NULL。这不是一般SQL nullable FK或允许UNKNOWN的CHECK语义，不代表原题目意图已独立核实。

| pair | 语义上必须保留的限制 |
|---|---|
| dev_01 | PERSON.ID为PK，EMAIL仍可NULL。SAT模型是ID为−1和0、EMAIL都为NULL的两行；完整C及实际query assertions核验通过。SQLite 3.53.3回放原SQL得到`[]`与`[[null]]`，逆序装载仍相同。但第二个SQL含GROUP BY中的裸列/SELECT *代表行语义，冻结协议明确排除该方言交集，故仍为DIALECT_UNKNOWN，不能升为有效自然缺陷或融合方法成功。 |
| dev_02 | composite PK与全交叉neq使FOLLOW的两个列值集合不相交；IN/self-JOIN匹配被完整C排除。C本身SAT，输出分支却可因合同而简化；不能把此例当困难JOIN。 |
| dev_03 | 完整PK、非NULL FK和经验值非负约束保留。此次官方UNSAT只属于该编码；之前已曝光的SQLite AVG与SUM/COUNT整数除法、ROUND差异仍为独立方言控制。不得把该差异计为新方法反例收益。 |
| dev_04 | strict FK令TRANSACTIONS.VISIT_ID非NULL且有目标；不能构造NULL外键毒化NOT IN后声称满足本C。 |
| dev_05 | USERS.ACCOUNT与NAME为分别登记的PK；裸NAME投影受完整合同中的函数依赖限制。保留VARCHAR、DATE及未引用列；不是删列后的INT-only问题。 |
| dev_06 | strict FK强制每个BOXES行匹配CHESTS，LEFT JOIN未匹配分支不可达；四个数量字段非NULL且非负。不得用违约NULL或缺失目标制造阳性。 |

dev_04的AST另作静态追踪：`from=[{value:VISITS,name:NATURAL},{left join:TRANSACTIONS}]`没有显式ON/USING，但不能仅凭这个外观判为错误别名或无条件连接。冻结官方`encoder.py:312–318`的`is_outer_join2`恰好识别此表示；`:550–576`进入natural outer专门路径，无ON/USING时在`:572–573`调用`_find_overlapping_attributes`，并设置`by='using'`。辅助函数`formulas/tables/join_tables/_utils.py:14–19`按列名求交集；原完整schema的共同列唯一为VISIT_ID。`outer_join_tables/left_outer_join_table.py:96–113`调用`_analyze_using`构造两侧等值条件并处理重复公共列；`encoder.py:657–660`也明确排除将NATURAL当普通alias。**该具体疑点已由代码路径解除，不是已确认parser bug，不降低dev_04当前注册资格。** 这仍不是整个前端语义正确性的形式化证明，不能仅凭UNSAT或6/6执行完成替代保真审查。

当前成功计数因此是：官方执行依赖门6/6返回；完整C可满足性6/6；SQLITE_INTERSECTION有效SAT反例**0/6**；跨方言自然gold或新科学机制收益**未建立**。执行状态`ALL_SIX_ATTEMPTS_RETURNED`不是语义PASS。

## 4. 首次失败和重试都计账

第一次`official_smoke_01`使用Python 3.9，在导入冻结`environment.py:557`的`match`语法时发生SyntaxError，六组都保留NOT_RUN，没有query solver结果。这是解释器兼容性失败，不是六组SQL unsupported，也不是solver性能失败。第二次在执行前另立freeze-v2，改用本机已有Python 3.12.13与审阅后的监督器v2；原SQL/C、backend、worker和正式语义协议hash不变。不得把第一次失败从历史成本删去。

| 尝试 | 状态 | worker报告CPU秒 | 监督器wall秒 | worker峰值RSS字节 | supervisor采样峰值RSS字节 |
|---|---|---:|---:|---:|---:|
| official_smoke_01 | 导入失败；6 NOT_RUN | 0.438751 | 0.613310 | 65,208,320 | 61,046,784 |
| official_smoke_02 | 6 RETURNED | 1.220708 | 1.380272 | 118,849,536 | 118,046,720 |
| 两次已记录合计 | 1失败+1完成；不变成12个独立pair | **1.659459** | **1.993582** | 峰值不相加 | 峰值不相加 |

worker CPU是各报告采样时的本进程user+system；监督器另记children CPU（含`ps`子进程）为0.455812和1.255951秒，合计1.711763秒。这是不同口径，不与worker CPU再次相加；仍未包含监督器自身全部CPU或任何宿主任务影响。worker报告保存及退出后的尾部成本应以父进程口径补充，不能声称1.659459秒是整个宿主的精确成本。

两次执行都在单worker、nice15、10秒CPU/25秒wall、256MiB RSS监测、500ms/check预算下登记。RSS由父进程每50ms采样，不是硬分配上限或瞬时峰值完整证明；以上同时列出worker ru_maxrss。成功运行preflight load=3.0390625、memory-pressure可用34%，postflight可用32%；这些只证明资源门读数和此次未触发停止，不能证明对并行unrelated_project任务零影响。旧01资源政策与结果不修改。

## 5. 对后续融合原型的实际含义

官方丰富语义入口已通过此小规模依赖门，故后续工程实验可以复用它；不能继续拿旧窄bridge作“官方baseline”。但这六组并未提供solver timeout、明显编码膨胀或可计分的SQLite交集反例，当前没有solver加速的实证需求。共享合法probe池的查询感知排序只能作为已知技术融合的工程诊断，并须与同池强简单排序、pure fallback及移除组件对照，在相同完整C、原SQL、预算下计入初始化、失败和探测开销。若以后只节省了冷导入，结论应是避免了启动成本；若只出现dev01或dev03，则不能记为注册交集中的反例收益。

这次成功不会解除科学HOLD，也不否定其他规模或未测输入可能有solver困难；它只是把当前证据中的覆盖问题和性能问题分清。不得由一次短smoke制造速度比较、新算法主张或自然数据泛化。

## 6. 源证据和SHA-256

以下路径相对02根；本次实读核对后生成报告，没有改写源文件。

| 文件 | SHA-256 |
|---|---|
| `runs/official_smoke_02/official_smoke_report.json` | `c319ed2832408050ad99f13eabb30952aa6977981191b60368adb6ce0f48f3cd` |
| `runs/official_smoke_02/receipt.json` | `84bdcfab66bb722563041f5beb01ee4f71b2c9bd9924bfd5de692b1a4dbb7b90` |
| `runs/official_smoke_01/official_smoke_report.json` | `50ea712917568348639559d0c6caea71a2d271e230c1d17f12df76909cf53769` |
| `runs/official_smoke_01/receipt.json` | `b390376a6e34aed827e8407f7dfc1860eb5ff447c141b42e82120c7105c8d5a2` |
| `protocols/official_smoke_freeze.json` | `4bf14b803eceb36cec1eb9d7be06fa41617cd6c027daf95630e827eb5a51db84` |
| `protocols/official_smoke_freeze_v2.json` | `a84e485cdec036fd5239cef3f45ccfbbdf02cb7689bebfd4b9787dc2f6601493` |
| `protocols/official_smoke.json` | `8f43a0053aeec5d3a9430232883f3b7a533fa5f4bb3ec4fae275660b213b0c59` |
| `code/official_smoke_backend.py` | `1ecf4a7bdd199913ee79f2efec6cc21c9904fd75a6cf36d7a2f1f10cc06b880c` |
| `code/official_smoke_worker.py` | `15993cfcca91142691074799e94cef205d60c6664b6e86b40309868384019b97` |

两个运行报告均绑定development输入hash `a51307167fb80e5caaf83b18fcd929e8781183fd7130821134eae18782e32430`。runtime记录native版本4.12.0.0、native hash `7dd2a17e5138323e90da56a3786e8a253f83130bd518cef86ef771e4ea982d0c`，848个lock文件匹配；这确认此次运行的本地冻结实现身份，不追溯证明未知的历史原始native pin。

dev_04追加静态证据位于旧根 `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/sources/verieql_v1/`：

| 旧官方源文件 | SHA-256 |
|---|---|
| `encoder.py` | `ad9558583ad88f62c8dce7630bd4b09dc794d174083a3b3209c958d73786e614` |
| `formulas/tables/join_tables/_utils.py` | `27719f99950d3641d20258d8938c166dbb73098ada97ee5baac176a092c63941` |
| `formulas/tables/join_tables/outer_join_tables/left_outer_join_table.py` | `c55ac728d3fa5e51dae11defb0203aa956c77c9cabb716deef4bfc9068e99fb9` |

冻结01诊断SHA-256为 `a4bf6ca3b4cc566d82eda4a8576459e7bf7f1a305e241192e3f558b025f6bea5`。本诊断由作者编写；另一个静态子任务只核对两份运行报告的计数和语义措辞，正式独审结论由父任务单独处理。
