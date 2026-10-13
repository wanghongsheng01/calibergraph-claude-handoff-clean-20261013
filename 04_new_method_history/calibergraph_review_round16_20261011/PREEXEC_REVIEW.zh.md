# 第16轮独立科学执行前审查

结论：**PASS_STATIC_PREEXEC_WITH_ALLOWED_FINALIZATION**。认可新第16轮在本文明确边界内做一次科学batch的静态设计；当前作者源码仍禁用、protocol仍为草案，尚未观察资源、提交科学launch或取得科学结果。本结论不是实际运行时安全门已通过，更不授权绕过自动审批或重试失败。

主审`/root/round16_independent`与预算子审`/root/round16_independent/wait_budget_criteria`独立于作者。只做文本、JSON、diff、hash、AST解析；未执行/import/compile科学源码，未运行observer、probe、SQL、SMT或枚举，未发提权请求、修改优先级或作者文件。旧15资料及停止锁13项基线再次核对不变。

作者disabled manifest SHA=`5cdb99e32522017e837e8b47925a6236c33e10236451102128c1a6dfd7a517a5`，协议SHA=`64bf3f54077888baca66439f10c35b77c4853015a516732a57bb3d15c44ec0ce`。新listed文件12/12、旧six source6/6哈希一致；新six source AST通过。独立另对root的runtime/input继承清单880项逐字节重hash，880/880一致，无native加载。详细20项当前输入与静态结果分别见`PREEXEC_INPUT_HASHES.json`、`STATIC_VERIFICATION.json`。

## 核心检查

原4个已暴露source、原SQL/schema/full operational C、registry/runtime pins、exact-live N=2/3/4、rep1和反序rep2、24唯一槽、每槽一次Environment和原科学限额均保留。worker、contract admission和safe replay三源逐字节不变；common仅轮次ID/标题且gate=False；backend仅新增计时派生函数与修复空集合sum；没有新solver call、fullC删除、SQL更改、基线替换或科学机制。

后端`measured_stage_cpu`只读已产生stage，缺stage返回null/NOT_REACHED，缺真正check计时字段返回null/UNMEASURED_OR_CENSORED；仅已有实测才求和。scope_encode依赖analyze和parse同时实测，否则null；comparison初始化状态及第15轮finally保留。实测partial stage不等于该阶段成功；硬停止仍可截尾，不能用此修复声称每个phase都精确测得。嵌套parse/analyze和replay不得双计，phase不替代生命周期。

supervisor POLICY入口即prep10，协议必须恰为10。观测账三个字段均须有限非负且charge=measured+tail；草案null正确阻止执行。总账只加一次`prep10 + 已闭合观测charge + 当前SELF/全部reaped CHILDREN + batchtail0.2`。观测charge实际覆盖precheck50、开槽前后50、活动56两处、含live worker的60及最终60；活动56相较旧版又计入0.2尾部，属于收紧。wait4明细不重复加。

protocol读取或观测账加载前失败，完整总额为null并带INCOMPLETE_OUTER_LEDGER_REQUIRED，known minimum仍保留prep10和已知当前CPU/tail；不是完整总成本。更早参数/路径/初始收据失败甚至无内部final，root必须用闭合observer账和外层证据保留全成本，不得以缺收据重试。

## 唯一等待与启动边界

observer已经独立通过`OBSERVER_REVIEW.zh.md`，现规则hash=`10044dcd309b0c480693c6b7185d7dfaeaadd46bfc838888682405ceee239f5d`。每900秒的等待观测仅在科学启动前，所有费用累计另计进同一个parent60，不吞并到prep10，也不追加另一份60。首次不得早于16:45 UTC，后续双时钟开始间隔≥900秒，不补跑。只有完整外层成功、有效收据且load1≤4/free≥25等全部门满足才可能ELIGIBLE。错误、审批拒绝、缺收据、非零退出立即停止，不能改称普通繁忙。

**第一次正式supervisor启动请求前永久消耗本轮固定once-lock；该请求是唯一batch尝试。** 即使自动审批拒绝、time或precheck失败、第一worker或solver尚未出现，也不回到等待。协议中“first scientific worker launch”不构成较晚例外；WAITING_RULES和本文的更早supervisor边界统一适用。flock仅防并发，root固定O_EXCL永久锁防第二次launch/换输出目录。

ELIGIBLE收据结束后60秒内提交一次具体受审科学命令；不是保证审批后60秒内实际执行。supervisor执行时仍逐槽fresh资源门，运行中按原资源/监控/完整性/预算停止逻辑保留截尾与余下NOT_RUN，绝不恢复或补齐24。普通query UNKNOWN按旧规则留存。旧15的24未启动、旧13失败与新16分母分别保留。

## 允许的最终化

完整机器规则见`allowed_finalization_changes.json`。只允许root把common gate False→True、草案状态/登记UTC转REGISTERED、从全部有效观测的实测与tail封闭总账填三个null字段，并生成最终freeze/账本/固定launch收据。不得改任何其他科学源码、输入、槽、顺序、预算或分析判据。

最终freeze须保持继承的880项一致绑定并补充本16六源、registered protocol、输入、interpreter、runtime lock/全部依赖、observer/schedule、封闭观测账、固定独审文档及相应输出文件。重复path只可同sha去重。原子永久lock记protocol/freeze/ELIGIBLE hash与时间，root保留唯一受审请求、`/usr/bin/time -l /usr/bin/nice -n 15`外层stdout/stderr/exit。外层time与内部SELF+CHILDREN交叉核对，不重复相加；缺可靠外层或final receipt时NOTCOMPLETED，实际槽状态按证据UNKNOWN，不能从初始NOT_RUN推断零科学动作。

最终化差异和冻结哈希应落盘，任何超出allowlist的变动须先重新独审。结果另写新文件，不更改被runtime freeze绑定的本preexec文件。

## 解释和交付边界

ANALYSIS_PLAN SHA=`a533eac9199c6a7b51f4700527e537d7f1cdf9fff96de815eaae40c6937e3231`，预定两遍逐source对齐，C非SAT、阶段未到、未知原因不一致或缺收据不支持重复瓶颈；全24与旧12分别列示，不挑最快成功项。即使满足预定重复判据，也只是此预算和工具下的开发成本现象。exact域不嵌套，不能推广至at-most N；C sanity不是query-SAT见证。强解析控制尚未计时，不能声称优于SQLSolver/Polygon。机制维持NONE/NO_GO，没有新独立测试。

另核读语义作者报告`SEMANTICS_AUDIT.zh.md`（SHA=`797cb30735667c29bcea0819fceb27576bc863a23ec89d17794dc5ad20eb57ee`）：其完整operational C而非业务DDL、exact域非up-to、两个INT回放profile而非一般SQL回放的限制，与本轮未改的传参和准入边界一致。四条raw定点3598字节及11C分支核对属于该语义作者报告的证据；本主审未重复读取raw，也不据此声称一般编码正确性已独立证明。列间比较为笛卡尔约束、FK为原非空存在性，不能私自改成同行CHECK或复合外键。

资源观测CPU1是SELF限额，helper另计；RSS/wall为采样或监控，不能声称瞬时kernel树级硬上界。每次尾部0.2和prep10是保守预留，非实测。fullC业务真实性/完备性、DKE全文、exact与up-to衔接未解。DataHub canonical注册和历史raw/native clean restore仍由root保留阻塞；新独审私有备份由root统一完成，本报告不宣称BACKUP_OK。
