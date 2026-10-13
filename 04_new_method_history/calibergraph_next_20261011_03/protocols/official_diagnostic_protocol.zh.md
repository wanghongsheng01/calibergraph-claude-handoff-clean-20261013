# 03 共同官方前端诊断协议（执行前）

本协议只准备代码，尚未运行目标。父任务负责登记最多32个来源标签组、绑定输入hash和扫描成本、检查unrelated_project/机器资源、冻结源码与最终协议，再由串行监督器执行。32不是已证明的语义独立问题数；不读取reserve或原结果标签，不为失败槽补样，不构造新机制。02代码和结果保持冻结。

输入沿用`case={id,source_group_id,source,original_sql_sha256,source_record:{schema,constraint,pair,...}}`。worker只读取协议绑定JSONL中的指定索引，不去上游搜索或选样。整份输入hash和case顺序先核验，最多32组且组标识不得重复。原SQL、整个schema、全部原C均进入结果和哈希；没有删除未引用列、表、PK/FK，没有SQL规范化。

## 执行与预算

每组一个独立冷子进程，CLI固定：

```text
python3.12 -B -I -S code/official_diagnostic_worker.py
  --protocol <root冻结的最终协议>
  --case-index <登记顺序0起点>
  --out <该组新输出目录>
```

每组最多两次独立Environment：每次重新建完整schema、加入完整原C、完整C非空检查、两条原SQL解析、官方Scope编码、绑定的原compare及新solver。第一次query check CPU≥250ms或返回UNKNOWN才考虑第二次。第二次不是重用旧公式的warm solver recheck；只有Python/本机动态库等进程级缓存可共享，因此也不宣称是两个独立冷进程复现。

单次C timeout100ms、query timeout800ms，两次名义上限1.8秒。每个timeout还按实际已消耗solver wall和剩余worker预算截断，并在solver累计2秒上限前保留100ms。实际check时间逐次记录；若超过2秒，明确`BUDGET_VIOLATION/INCONCLUSIVE`，不得计成功。父监督器根据实时progress在已完成solver wall加当前active elapsed达到1.9秒时终止该进程组，超2秒另计违例。超时值不等于严格原生执行时限，独立父守卫仍必要。

每进程hard CPU4秒、父进程hard wall5秒、父监控RSS256MiB、Z3 memory参数128MB。worker在CPU/wall到限前留250ms收尾；Python闹钟只做补充，不能代替父强杀。全局120CPU包括扫描、每次冷导入、所有失败、worker、监督器自身及监控子进程；父监督器采用更早停止新组/终止active的门限。未跑槽记NOT_RUN，不补运行、不换样。

## 准入和语义边界

来源轴为`PRESENT_JSON`、`EXPLICIT_EMPTY_OPERATIONAL`、`NULL_UNSPECIFIED`、`MISSING`、`INSUFFICIENT`。`null`和缺失constraint键都不补成空C，直接来源不足且solver不运行；`[]`可运行上游明确的无附加operational C，但不证明真实业务无约束。非空JSON列表的存在也只证明基准声明，不证明业务C正确或完整。

结构准入检查识别官方全部IC操作符和实际schema类型，不沿用02的四类concrete validator。每个IC对象必须单key，参数数量必须匹配，引用必须能按官方规则绑定；不支持时整个输入拒绝，不过滤条款。官方create_database对未知类型静默pass，因此明确拒绝未被编码的类型或None；DATE/BOOL/BOOLEAN/VARCHAR/INT保留。`date(column)`仅限制第一行、跨表primary依赖位置zip等有信息损失的形状明确拒绝。完整C仍按锁定官方操作语义解释，包括strict非NULL FK、跨列Cartesian比较、inc物理行序等，不替换为通用SQL DDL真值。

每表固定**恰两行存活**；不是0..2、不同表行数向量或更大数据库覆盖。query返回UNSAT也只描述该官方编码的固定形状；SAT只记录raw模型并检查所有原始提交facts和实际query assertions。可解码的INT/BOOL/DATE及全部原始值写出；VARCHAR保留官方数值symbol，不能假造一般字符串/排序/常量映射。泛用独立concrete C检查器、DBMS原SQL回放、跨方言或自然缺陷gold均未实现，不据SAT作相应主张。

## 阶段和分类

事件分开记录runtime核验/导入、schema、IC admission、C solver setup/check/model validation、原SQL逐条parse、Scope编码、compare公式编码、query check、SAT核验与cleanup。逐条parse保存实际AST与canonical hash；不能JSON无损表示的官方节点仍原样送编码器，只把审计表示标为NON_JSON_AST，并明确其repr/hash不是完整JSON AST。来源token层标签不替代运行后实际AST核查。

`engineering_class`描述可观察执行行为，`provenance_class`保留来源证据，`strict_class`限制最终可声称范围。schema/C/SQL异常归具体阶段，不当作成本成功；编码阶段资源停止为`COST_SIGNAL_ENCODING_UNCONFIRMED`。`SUPPORTED_FAST`只表示query check CPU低于250ms且已返回known verdict；初始化、解析和编码仍单列，不自动断言端到端快。

重复成本时序门要求：两个独立Environment均完整返回、完整C均SAT、query verdict均已知且相同、两次query CPU均≥250ms、最大/最小CPU比≤2。只有通过这些条件才有`REPEATED_COST_SIGNAL_STABLE_TIMING`，UNKNOWN/timeout和预算不足均不满足。进一步提升为`STABLE_COST_CANDIDATE_EXACT2`，还必须显式给出`semantic_admission.complete_original_schema_and_C=true`与`semantic_admission.original_sql_to_official_ast_reviewed=true`，且来源为PRESENT_JSON；缺少证据则fail closed为`COST_SIGNAL_UNCONFIRMED`。这仍不等于科学瓶颈、真实业务缺陷或新方法收益。

## 监督器文件接口

worker写`results.json`（原子替换）、`events.jsonl`（每条flush+fsync）、`progress.json`（原子替换）。进入目标前已有初始NOT_RUN/STARTED槽，任何异常不能删除登记分母。事件保留部分attempt；监督器强杀后应保留最后阶段、全部已发生事件与资源回执，不把未完成阶段的空结果当返回。

progress至少包含`active_stage`、`solver_check_active`、`solver_check_start_monotonic`（同OS monotonic或null）、`solver_spent_wall_seconds`（已完成check，不含active）、`check_count`（已开始数）及更新时间。每次原生check前后立即更新；父监督器独立写`supervisor_receipt.json`和`supervisor_events.jsonl`，不覆盖worker证据。

最终协议从`official_diagnostic.template.json`复制并由root填写登记input路径/hash/registered_case_ids、扫描CPU及绑定回执、资源policy/hash。实际登记数量可小于32，严格按JSONL顺序，不硬填。模板占位状态不得执行。依赖使用既有pinned官方源码/native/runtime lock，不安装包、不改原源码；历史原native pin未追溯核实的限制继续保留。
