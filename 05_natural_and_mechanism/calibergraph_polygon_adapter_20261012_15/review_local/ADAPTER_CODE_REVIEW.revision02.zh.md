# #1172 适配器修复与局部接线复审

结论：修复已关闭首次发现的 TEMP 遮蔽漏洞；当前适配器及准备态 worker 局部 diff 未发现必须修复的语义问题。首次反例脚本、JSON 和初审报告均保持原样。

本次适配器 SHA256：`d0f13404622f8e78ea8c3549a6f19a65a403dafda6bc49fca8d7e7422ad3a06b`。

## 独立验证

运行新增 `adapter_semantic_check_revision02.py`，新结果保存为 `adapter_semantic_check.revision02.json`，没有覆盖初次证据。SQLite 3.43.2 下 150 个实际适配器交叉案例再次通过；4 个抽象非法模型拒绝通过；原 TEMP TABLE 最小反例现在被拒绝，另外 TEMP VIEW 同名遮蔽与 ATTACH 模式也正确拒绝。零 solver 调用。

`validate_original` 在读取原查询表之前拒绝 TEMP 模式对象与外部附加模式，因而签名和 C 检查现在覆盖与未改写原 SQL 相同的源表。标准新 SQLite 连接、无自定义函数/排序规则的前提应明确保留；代码不需要为任意被篡改的连接保证默认 SQLite 语义。

## worker diff 静态复核

- `slot_worker.py` 在读取参数及建立 broker socket 之前读取 FREEZE 中的 `solver_execution_authorized`，false 或缺失均不能进入求解路径。提交准备态时必须把该键固定为 false。
- 显式仅允许冻结 `thrombosis_prediction__1172` 和 UA/precise 两模式。继续使用 13 的完整固定 runtime/dependencies；没有新的 SQL 功能或通用 REAL/DATE 实现。
- schema 与全部 7 条 C 来自冻结源哈希校验后的 `load_contract`；64 列保留；原 SQL 直接读取冻结文件。
- 原抽象见证独立落入 `abstract_witness.json`；`replay_lifted` 先检查抽象 C，再固定提升、原 C 验证和原 SQL 回放；只有回放确实区分原查询才标为 VALIDATED_NEQ。没有修补或求解重试新增路径。
- 独立确认 `INTEGRATION.patch` 与 13→15 实际 worker 文本差异完全一致，13 源 worker 哈希匹配其 FREEZE。4 个作者 Python 文件 AST 检查通过。
- 继承的计时、资源 broker、超时和清理没有在此局部 diff 中改写；此次仅静态审查，没有执行 worker、native solver 或科学流程。未来真正运行的性能和状态不能由当前测试代替。

观察商证明范围依旧为完整 C 下每源表 N≤1 的快照双查询观察等价和固定反向提升；不是通用 SQL 语义支持、官方 baseline 原样运行或无限界等价结论。作者保存的 parse/encode-only 结果可以证明工程接线到达被阻断的 solver 入口，不能作为科学运行证据。
