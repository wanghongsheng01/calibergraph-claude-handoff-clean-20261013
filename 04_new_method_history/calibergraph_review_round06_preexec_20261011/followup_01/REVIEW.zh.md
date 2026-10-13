# 第六轮修复后独立静态复核

结论：**静态复核通过，原两项 P1 均已闭合，无遗留 P0/P1。** 仅适用于本次哈希所标识的文件及下述两个最终登记差异；旧审稿、旧哈希清单均保留。

P1-01 已闭合：`safe_sqlite_replay.py:184–205` 在 SQLite 回调外保存 guard 原异常，回调返回 1 中断后，execute/fetch 路径重新抛出原 `BudgetStop`；其他 callback guard 失败转换为带 cause 的 `BudgetStop`。`216–218` 不再吞掉它，backend `383–388` 将其记为 `RESOURCE_STOP`，supervisor 的递归停止检查可识别。新增 sanity control `307–310` 同样重新抛出资源异常。

P1-02 已闭合：supervisor `519–527` 在 lock/registration 预检之前保存 `planned_denominator=12` 和全部 12 个可识别的计划 NOT_RUN 槽；`592–594` 在失败时保留原因。预检未通过前保留 `registered_denominator=null`、`registration_validated=false` 是合理区分，不能误称已经注册成功。common `94–103` 已对 `[6,9,14,3]`、2/4/8、整数类型及全部 slot dictionary 的 id/kind/source ID/index/bound 精确校验，固定来源与槽身份不再可替换。

新增 C-model sanity control 的静态边界通过：只处理两个准入 INT 来源；使用同一个已完成完整 C 验证的 contract model；无额外 solver check、attempt 或预算。`C_MODEL_SANITY_*` 明确计时，费用包含在既有 attempt/process/wait4 总量中。`contract_model_sanity` 及嵌套 replay 明确标为 `C_MODEL_SANITY_ONLY_NOT_QUERY_SAT` 和 `query_sat_witness=false`；正式分类只读取独立的顶层 query replay，因此控制路径出现差异也不能提升正式反例类别。它用于已有合法 DB 生成与原 SQL 回放的动态覆盖探索，不构成新方法、生成反例成功率或科学胜出。

本次复核的 common SHA 为 `ebb0351ed9529c68daa02c9783f571e7f8ef67abb9395e482defd07c78477a6a`。作者 static receipt 中 `723e6819…` 是修复前历史快照；根代理的 canonical-slot amendment 和本次新哈希清单是当前 common 身份依据。其余收到的 backend/supervisor/replay 哈希均与实际字节相符；worker 与 contract admission 的哈希未变。

允许在本结论之后进行的内容变化只有：

1. `generation_common.py` 的唯一 `EXECUTION_ENABLED = False` 改为 `True`，其他字节不变。预期启用后 SHA 为 `74df9d61a87be8fabe311e96d8418e9704baa8e1292ff97a1a5ccf9334265863`。
2. protocol 的 `status` 从 `DRAFT_NOT_REGISTERED` 改为 `REGISTERED`，`registered_utc` 从 null 改为真实最终登记时间；其他字段值不变。允许另存 registered 文件，随后按真实最终文件哈希生成冻结清单。

protocol 去除以上两字段、以 UTF-8/ensure_ascii=false/sort_keys=true/紧凑 separators 规范 JSON 后的 SHA 应保持 `d9eb6458f5c527a406df138103c91d2d7c1294a095d598592f46246e31556ddf`。详细限制见 `allowed_finalization_changes.json`。冻结必须覆盖启用后的六文件、已登记协议、解释器、原输入、runtime lock 及全部锁定依赖。其他代码、预算、来源、槽或控制行为变化需要再次审阅。

本次仅文本和哈希复核，未执行作者代码、SQL、parser、solver、VM 或任何科学试验，未改作者文件。静态通过不保证 C SAT、SQLite 能力、回放成功或预算可行；未知、拒绝、资源停止与 NOT_RUN 仍须全部计入 12 槽。旧 P2 的分层计时与未测量准备成本 reserve 披露仍适用，不阻断当前限定试验。根代理可依已有授权完成上述登记和冻结，无须向人重复请求许可。

追加核对：`ANALYTIC_CONTROLS.zh.md` 与两个准入原 SQL 的限定推导未见明显错误。1264 的默认 ELSE NULL、内连接换序/别名及同一 DISTINCT/NOT IN 保持标准 INT/NULL/bag 语义；1421 的 LEFT/RIGHT 反转保留 QUERIES、row equality 与分量 AND 的三值逻辑一致、两个参数的 IFNULL/COALESCE 对 INT/NULL 同值。此为文本语义推导，不自动认证 official 编码实现正确，未实现或测量所谓零耗时基线。**本批没有候选方法、性能对照实验或消融结果可报告**；固定 official 成本/超时不能被包装为科学 hardness。最新 draft 中 analytic_strong_controls 指针已纳入本次最终哈希，分析文档应一并冻结作为范围证据。
