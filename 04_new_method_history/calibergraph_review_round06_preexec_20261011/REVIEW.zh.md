# 第六轮独立静态预执行审阅

结论：**先修复两项 P1，再启用并最终冻结；未发现 P0。** 这是静态审阅结论，不是执行或科学有效性的证明。根任务已有实施必要修复和冻结的授权，无须再次向人请求许可。

审阅了六个 Python 文件、接口、静态适配报告、draft protocol 和选样说明；按精确 diff 复核了已通过审阅的第四轮 supervisor 的变更。仅进行文本、AST、JSON 和哈希工作，未导入作者模块，未运行 SQL、目标 parser、solver、VM 或科学试验，未扩读 whole source/test/reserve，未修改作者文件。额外语义复核由独立子审阅完成。

## 必要修复

### P1-01：SQLite 回调会掩盖资源停止

`safe_sqlite_replay.py:180–183` 在 SQLite progress callback 中直接调用 `budget.check()`。若这里抛出 `BudgetStop`，CPython 的 SQLite C 回调会清理该 Python 异常并中断 SQL；外层看到的是数据库错误，而不是原异常。`199–202` 的类型名判断因此无法恢复它，只会写入普通 `REPLAY_ERROR`。随后 backend `351–352` 进入 `QUERY_RETURNED`，supervisor 的 `resource_status_in` 没有 `RESOURCE_STOP` 可识别，可能继续下一槽。

必要修复是：回调将原始 guard 异常保存到闭包，返回非零中断 SQLite；`execute/fetchall` 捕获数据库错误时，优先重新抛出已保存的原异常；监测失败同样必须走停止剩余槽的路径。外部硬 CPU/wall/RSS 防护仍在，因此本发现是停止政策和结果分类失真，不是声称会无限执行。依据为 [CPython 3.12 官方 connection.c 的 progress_callback](https://raw.githubusercontent.com/python/cpython/v3.12.0/Modules/_sqlite/connection.c)，约 1300–1322 行；[官方 SQLite progress handler 文档](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.set_progress_handler) 也说明非零返回通过数据库异常结束查询。未运行复现。

### P1-02：固定 12 槽在早期失败时会消失，输入准入也未固定四个来源

`generation_supervisor.py:517–519` 创建首份 receipt 时使用 `registered_denominator=None`、`slots=[]`。必须等 `validate_inputs` 中的 `load_registered(...,0)` 成功后，`165–168` 才填入分母。因此 lock、注册、execution gate、原始输入或 runtime 哈希等早期失败会留下空分母，而不是 12 个带原因的 NOT_RUN。

此外 `generation_common.py:92–99` 接受 21 例内任意非空且无重复的索引列表，仅检查其与 2/4/8 的笛卡尔积，未强制 `[6,9,14,3]`、固定 12 槽及其规范 identity。draft 当前正确，但可执行准入没有实现接口所说的固定四组、不可替换规则。

必要修复是：用规范的 `[6,9,14,3] × [2,4,8]` 固定槽在首份 receipt、lock 和所有可能失败的操作性预检之前初始化 NOT_RUN；准入逐项拒绝来源索引、source ID、slot ID、kind、bound 或顺序差异。任何预检失败均保留 12 槽及 halt reason。

## 静态核对通过的边界

- 原 SQL、完整 schema/C 的哈希和未改写传递路径保持；不能将“完整给定 JSON”提升为业务合同真值认证。
- 独立 C checker 的 FK 非 NULL 成员关系、复合 PK、Cartesian column comparison、literal-left swap、not-null 与完整 AND/OR 检查和固定 official 操作语义相符。
- query solver 的实际 SAT model 经全部事实/断言检查后，以实际物理元组和独立 NULL flag 导出；两个准入 INT profile 在同一数据库上执行原 SQL，再作 bag 比较。未见模型替换、格式化 sentinel 误判或伪造 witness。
- dev03_07、dev03_04 的 DATE/division/ROUND 或 decimal/ROUND/VARCHAR 原 SQL 回放仍被明确拒绝。DATE 的显示解码符合固定 official epoch/range 事实，但这不认证 DATE 查询方言。
- supervisor 的 single-worker、3 CPU 秒、4 wall 秒、256 MiB、nice≥15、parent 60 秒、load1≤4/可用内存≥25 的入口门槛、monitor fail closed、所有权敏感的 kill/reap 与第四轮相同。采样可能超限，当前已经披露并保留实际资源证据。
- 六个文件仅 AST 语法解析；审阅快照中 `EXECUTION_ENABLED=False`，protocol 为 draft。

## 可选 P2 与范围判断

1. **C_MODEL_SANITY_ONLY 可选。** 若两个 INT query pair 全部 UNSAT 或前端拒绝，本轮可能完全未动态经过 SAT 导出和回放；这不让当前 baseline 成本 feasibility 试验无效，但结论必须明确“该链动态覆盖仍未建立”。可事前注册同一个 C-model 的 sanity replay并完整计费；它不能被称作 query-SAT 反例、distinguishing generation 收益，也不是本审阅要求的准入条件。本轮无新增方法，不要求为了执行而实现新方法。
2. **计时不是扁平分区。** replay phase 嵌套在 decode/replay stage 中，不能两层相加；SQLite import/connect/close 与日志开销未全部单列，仍被外围阶段/attempt/process/wait4 总量覆盖。未见严重总量漏计或双计，细分归因可后续改进。
3. **10 秒准备成本是 reserve。** draft 已明确不是测量，不能后来写成 measured CPU。最终注册应说明覆盖依据，并统一接口“actual prior charge”的措辞。精确测得的端到端准备成本仍未知。

精确审阅输入见 `reviewed_input_hashes.json` 和 `SHA256SUMS.reviewed_inputs`。修复后的文件必须重新哈希、注册和冻结；本报告不自动覆盖修复后或启用后的文件。动态 SQLite 能力、native import、预算适配与真实执行正确性均尚未验证。
