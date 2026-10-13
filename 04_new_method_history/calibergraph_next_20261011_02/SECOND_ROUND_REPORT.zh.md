# CaliberGraph 第二轮：官方入口实测与固定池机制检验

状态：**HOLD。尚无可晋级的新机制或科学收益。** 本报告包含新目录中的真实轻量运行，不修改原稿或首轮冻结文件，不使用 reserve。六来源组、十二条原SQL都是历史曝光的开发材料；没有独立最终test或自然缺陷gold。

## 首轮独审已结束，P1已接受

独立AI子任务完成审阅，P0=0、P1=1、P2=0。首轮24次SQLite均返回这一事实保留，但dev02人工库违反上游全交叉neq，其2/24执行槽撤回源合同合法性认证。见外部相邻目录 `../calibergraph_review_fallback_20261011/INDEPENDENT_REVIEW.zh.md` 与 `../review_followup_01/ERRATUM_FULL_CONTRACT.zh.md`。不自动认证其余22次执行的完整源方言语义。

该修正不影响另一显式R/W模型的18实例否证、固定E扩张的先例归约或HOLD。独审是未参与作者写作的AI子任务，不是真人盲审，也不是尚无可读输出的原应用独审任务。

## 实际启动与官方入口结果

| 尝试 | 结果 | 实际成本/范围 |
|---|---|---|
| official_smoke_01 | 默认Python3.9导入上游match语法失败；六组NOT_RUN | worker报告CPU0.438751秒；保留失败，不算solver尝试 |
| official_smoke_02 | 现有Python3.12重试；六组完整C均SAT，六组均到query solver | worker报告CPU1.220708秒、峰值118,849,536字节；父监督wall1.380272秒 |
| probe_ordering_01 | NOT_RUN_RESOURCE_GATE，worker未启动 | 一分钟load6.132>冻结阈值4.0；内存可用36%；零SQL/solver |
| probe_ordering_02 | 原门复查通过后重试，十二个case×arm槽均完成 | 64次完整C实例检查、128次初始SQL与4次排除组反向控制均返回；零solver |

两次官方尝试的worker报告CPU合计1.659459秒，父监督wall合计1.993582秒；父进程统计的children CPU含ps采样，另为1.711763秒。worker记录点不覆盖最终报告输出/退出尾部，不将其称完整端到端成本。初次监督器的异常清理缺口已由独审指出，第二版以finally终止并回收本worker进程组；首版及其运行回执不覆盖。

| 原始pair | query check CPU (ms) | 结果边界 |
|---|---:|---|
| dev01 / 182 | 8.045 | 原始SAT，SQLite具体差异复现；裸列GROUP BY边界，DIALECT_UNKNOWN，不计科学SAT |
| dev02 / 614 | 11.463 | 官方exactshape UNSAT；全交叉neq使两列不相交 |
| dev03 / 1075 | 69.914 | 官方exactshape UNSAT；不能推成SQLite整数除法等价 |
| dev04 / 1581 | 19.744 | 官方exactshape UNSAT；NATURAL标记由编码器专门分支生成VISIT_ID共同列条件 |
| dev05 / 1587 | 31.258 | 官方exactshape UNSAT |
| dev06 / 1715 | 14.403 | 官方exactshape UNSAT |

全部使用原SQL、完整原schema/C、每张物理表**恰两行**和`OFFICIAL_OPERATIONAL_IC_V1`。这不是每表≤2、无界等价或一般SQLite等价。六组零solver unknown/timeout；query solver总CPU154.827ms，而锁定依赖核验与导入为655.138ms。当前开发集没有展示求解性能难点。

旧48,910槽零JOIN是窄前端/片段覆盖问题；旧扫描没有solver调用。现在官方入口能让本六组进入求解，但这只是工程覆盖事实，不是新方法优势或所有SQL语义已被普遍认证。详见 `analyses/official_backend_diagnosis.zh.md`、`analyses/official_execution_accounting.json` 与两次原始运行目录。

## 借鉴后的机制选择及反证条件

实际先例的范围、实现入口和代价见 `literature/MECHANISM_TRANSFER.zh.md`。XData式合法小库生成、VeriEQL回退、Polygon多查询分辨、WeTune约束放松、provenance细化、RATest依赖保持缩减都已有先例。当前每来源组只有一对SQL，缺少多查询调度增量的开发条件。

加权COUNT方向在十二条原SQL上**0/12适用**，全部缺少同一聚合块里的根加两个独立叶。标准eager aggregation/FAQ已覆盖基本公式。本轮不造星形查询或把SUM溢出/浮点差异藏起来。详见 `opportunities/weighted_count_admission.md`。

只准备了一个已知技术组合的最小诊断：固定合法池探测，加相同官方回退。固定池有32个人工完整数据库，各表恰两行，保留全部原schema/C。B为强通用NULL优先/重复值排序；C在同一池上只改变AST特征排序，B即去掉查询特征的消融。无探针的官方回退已单独运行。

权重、数据库池、同预算、失败分母与停止条件均在探针执行前冻结。dev01/03不计科学SAT；dev02/04/05/06为登记语义交集。若B/C在这四组都完整扫描且零可接纳差异，则任何排列都无法在此池里省回退，停止该收益假说。缺AST、错误、超时、未启动不能通过该停止门。没有结果导向换样或额外solver重跑；不宣称完整XData复现，不计算虚构端到端加速比。

## 排序短测结果与停止决定

首次启动被资源门拦截，记录保留。约两分钟后的一次只读复查得到load2.78、内存可用36%，通过原阈值，使用原封不动的冻结代码/协议重试。十二个case×arm槽均完整扫描，64次候选尝试、128次初始SQL、4次dev01反向控制全部返回，0合法性/SQL失败、0截断、0solver调用。

四个语义准入组的B/C均为**0个可接纳差异**；每臂完整扫描同一23个数据库。两臂在dev01各观察一次已排除的方言差异，不能算研究收益。dev03在这个固定池上没有输出差异，也不能推成一般等价。

因此触发预注册停止门：**在此固定池和已曝光四组内，查询感知排序不能比强通用排序省去任何一次回退。** 排列相同集合无法提前命中不存在的可接纳实例；不需要再调用相同solver证明这一点。这个结论不否定别的生成器、池、SQL或普遍预探测方法。

探针worker报告CPU0.100579秒、峰值21,544,960字节，父监督wall0.180053秒。B/C微秒级时间差受固定B先C后与热缓存影响，不据此宣称速度胜负。逐臂成本、排序debit、共享加载与历史前端成本分别保留；共享开销不能免费摊成候选优势。官方回退仅为独立依赖门实测，没有伪造全融合端到端速度比。详见 `runs/probe_ordering_02/probe_report.json` 和事件流。

两次官方worker加此次探针的报告点CPU合计**1.760038秒**，三个已启动worker的父监督wall合计**2.173635秒**；另有一次资源拒绝未启动。静态审查/人工池生成成本单列，不包含在这组worker总数里。科学结论保持HOLD，并停止本固定池的排序收益假说；不换样、不加种子或扩大预算寻求正结果。

## 资源与最终测试

实测采用单worker、nice15、线程环境为1、10秒CPU硬上限、25秒父监督截止触发阈值和256MiB采样RSS上限。macOS内存可用比例至少25%、一分钟load≤4才启动。RSS是采样观察而非分配硬限；wall含轮询/调度回收误差，不承诺unrelated_project性能零影响。未修改、终止或重设unrelated_project进程，未安装依赖、使用GPU/API、读取凭据、购买资源或更改系统安全。

真正独立最终测试仍未建立，历史公共扫描/反复开发材料不冒称新test。没有候选达到晋级门，故不解封reserve、不启动大队列、不改原稿或投稿。旧选择器不因本轮结果获得继续调参的依据。
