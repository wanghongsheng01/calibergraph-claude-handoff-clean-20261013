# 第15阶段独立审查：资源门停止

审查者：`/root/round15_independent_gate`。结论：**`STOP_RESOURCE_GATE / SCIENTIFIC_NOT_LAUNCHED`**。该结论认可本轮停止，不是启用实现或科学执行的 preexec PASS。

一次非科学能力探针已启动并返回 NOTCOMPLETED：receipt 的 load1=`4.6015625`，超过事先固定上限4；nice15、CPU限制[1,1]、free memory35%、自身ps与wait4虽有成功观测，不能抵消失败的资源门。源码第53行对应 load 断言，第54行 free memory 断言尚未到达。已读外层收据的exit=1与receipt一致，stdout解析结果与receipt相同，stderr为空。这是**已启动的资源门失败**，不是自动审批拒绝，不是旧13的EPERM重跑，也不是查询 UNKNOWN 或科学计算结果。

科学source仍 `EXECUTION_ENABLED=False`，协议仍 `DRAFT_DISABLED`/registered_utc=null，24 planned 槽没有启动。不能将 planned24 写为已注册/已执行24；也不能把 probe 的成功系统调用当成整个科学runtime可用。H15 没有新结果，重复性和成本归因仍未测，机制晋升保持NULL。旧06的12槽2/4/8历史证据另列，不充当本轮新结果；旧13一次失败保持NOTCOMPLETED。

## 本次实际独审

- 先读 `/Users/loctek/AGENTS.md` 及冻结范围报告；独立抽查作者论文/固定官方代码。详细范围和primary链接见 `SCOPE_REVIEW.zh.md`。FewRows/DKE 子抽查由独立审查子代理完成，未委托作者自评。
- author manifest SHA=`0252f52e648ca0c3b019007e3343d2ec71b8828bdfd1b3257c7bc20447f7152a`；旧源6/6、新listed文件12/12哈希相符，新源6份 AST语法通过。协议 SHA=`517948fdec44d51499203388a8166e8fdc9e84accddc0fc5937cce8877814b7a`；24槽完整、ID唯一、两遍预定顺序一致。
- 新源改动集中在轮次/路径/身份、禁用门、24槽及两处计时；两个admission/replay源逐字节沿用06。未发现增加solver调用、删除fullC或科学方法的改动。
- 最终作者停止manifest SHA=`a73a7c9aea510e4b687bcc5b2dd0669c6d11a16079e0fd7a520e5202b24c1bb2`，37/37文件哈希相符；`PLANNED_DENOMINATOR.json`完整保留同次序24槽，全部NOT_LAUNCHED_RESOURCE_GATE，C/query/replay/科学耗时全为null；永久关闭lock已存在。outer收据四项关联哈希全部相符。
- 旧12槽派生历史表的source hash与原06 readout相符；逐槽再读原results，12项input hash、fullC/query状态及query CPU/wall派生值均相符。5 UNSAT、4 UNKNOWN、3未query-check；后3项query成本null的overlay正确，没有改写旧证据。历史数据不与新24槽合并为新独立样本。
- 独审没有科学运行、科学模块import、compile、SQL、SMT、枚举、能力probe、提权请求、修改优先级或修改作者文件。只做文本/JSON/hash/AST及只读文献核验。root的probe是独审之外的一次实际运行，分别记账。

## 资源与成本边界

probe receipt 给出 SELF CPU=`0.044665s`、全部reaped CHILDREN CPU=`0.003567s`，小计`0.048232s`；wait4单个helper的`0.000483s`已在CHILDREN内，不能再加。SELF峰值RSS=`12943360 bytes`；receipt前wall样本=`0.019945667s`。CPU从进程生命周期累计，wall从源码START计，二者范围不同。最终JSON写入/打印/解释器退出未包含于样本，不能称完整实测成本；仍须收在本轮10s准备预留，不把预留冒充测量。科学运行成本是未发生，不是高bound低成本观测。

科学设计保留nice15、单worker、每workerCPU3s/wall4s/采样RSS256MiB、C100ms/query700ms/Z3memory128MB、load≤4/free≥25及批次60s含prep10/tail0.2。但未生成可执行runtime冻结、未提交科学launch，故仅能说静态限额设计被保留，不能声称运行中验证通过。采样RSS/wall与监督记账也不等于对整个进程树的kernel瞬时硬限额。

## 未执行实现的保留限制

1. `official_generation_backend.py:433–437` 沿用空集合sum。C检查提前停止或query check未到达时，parse/query等未测阶段可写为0。当前没有科学输出受到此问题影响；未来任何新阶段若使用该实现，需按stage证据转null/未测，不能直接拿该派生字段作成本归因。compare计时新增None/NOT_REACHED与finally异常耗时处理不解决其他字段的空集合问题。
2. `generation_supervisor.py:543–545,611` 的flock只防并发；maximum_batch_attempts字段校验不能独自防止新输出目录的第二次launch。README已经明确依赖root外层永久exclusive once-lock。当前停止后不为此添加执行或加固工程。
3. supervisor POLICY准备费初始0，到`load_registered`成功后才设为10（:29,161–164）。若未来在更早校验处失败，内部receipt不能单独当含prep10的全成本账。外层必须保留准备费；本轮未启动该supervisor。
4. cold只能表示独立冷进程，未清OS缓存。phase嵌套、日志、序列化、硬中断截尾均要求单列，不以phase总和冒充完整生命周期成本。

以上是供以后明确新阶段使用的静态限制，不构成本轮重试、启用或扩大预算的理由。本轮无必要修补作者源；保留现有冻结字节与停止证据。

## 审查纠错与剩余门

本审查最初误把工具JSON显示层的反斜线转义读成probe源码双转义，误报regex和换行两项。独立AST literal复核证明regex只含单个反斜线，write常量len=1/ordinal10；源码SHA始终`89610d812d9aba116c56cb65f8f96b38ea2cb7d930b420866849b0dd8cc5d94b`。两项已在执行前撤回，无源码修复、无重试，不把误报留作实际缺陷。

DKE全文、fullC业务真实性/完备性、exact与up-to衔接仍未解决，均不可外推。DataHub canonical注册与历史raw/native clean restore阻塞由root保留。独审产物私有备份交root统一；本审查不宣称BACKUP_OK。
