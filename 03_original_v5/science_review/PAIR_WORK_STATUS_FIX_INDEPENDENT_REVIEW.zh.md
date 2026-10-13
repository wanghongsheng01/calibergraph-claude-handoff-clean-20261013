# pair_work_status 修复与历史衍生状态独立审阅

结论：**新日志修复静态可接受；冻结最终截面的逐行衍生状态已核实。未见剩余 P0/P1。** 新 worker 的 native/solver/SQL 集成运行仍未执行，future lock 保持 pending。本审阅不能把纯日志 fixtures 当作目标实验，也不改变旧 v5 或旧回执。

审阅者为不同 AI agent `/root/independent_review`，不是真人。此次只读取文件、计算哈希、解析 AST 和逐行重算记录状态；没有导入或执行作者 helper/classifier、目标 worker、native、solver 或 SQLite。

## 修复与发现回合

新目录 `runtime_fair_v5_statusfix` 在真实查询分派返回点写入 `QUERY_WORK_RETURNED`。RETURNED 仅表示查询分派已经返回一个记录的结果，与“有解/无解”“科学有效”“进程正常退出”“资源合格”分别记录。UNKNOWN、unsupported、oracle 域不明和回放不一致仍保留原始非成功结果；canonical identity 不冒称运行了 pair solver，逐查询 differential UNSAT 不冒称两条 SQL 等价。

未闭合的 attempt、fallback、differential 或 oracle 标记会产生 RETURNED_INCOMPLETE_RECEIPT；无开始回执的 return 产生 INCONSISTENT_RETURN_RECEIPT。合同提前停止仍是 NOT_RUN_CONTRACT_STOP，晚停止保留真实尝试；cleanup 异常保留此前返回回执。父 supervisor 仍独立检查退出、hash 和资源，helper 不生成科学成功标志。

独立 AST 比较确认：去除新增 logger import/calls 和唯一 QUERY_WORK_RETURNED checkpoint 后，新旧 worker AST 相同。reference 与 differential 源逐字节未变；common/supervisor 的其他差异限新增 helper 锁定和日志字段复制。25 项作者执行的纯 helper fixtures 回执与源码哈希一致；本审阅没有重跑这些 fixtures。新增落盘有成本，未来 statusfix 的计时必须属于另一个源锁批次。

本轮发现并关闭一项 **P1-DERIVE-NO-START**：旧候选汇总器 `ad834850…` 对 COMPLETE/FINAL_COMPLETE 且 `pair_work_started=false` 仍派生 RETURNED。最终 `83a23fc0…` 已要求 started 严格为 True；缺失/false 均为 NO_PAIR_RETURN_RECEIPT。作者回归 02 的 16 项记录包含这两个断言，同时覆盖空/null stop 字段、缺失 UNSAT attempt、异常退出、资源异常、typed stop、differential unknown 和旧 slot 52。回归中的 identity=True 是单位 fixture，不是实验身份核验。

## 历史记录逐行核验

按最终 selector 核对 364 个选中终态，以及旧 slot 52 保留的一次未完成尝试，共 **365 条真实观察**。全部原始 pair/parse/solver 字段、final decision、stop 字段、源路径与 SHA 均对应原文件。1020 个不同锁定源码/依赖文件的字节哈希、最终截面列出的 534 个 provenance 文件均匹配。

| 阶段 | 选中槽 | 严格有效结果 | 预期合同拒绝 | 求解 UNKNOWN | oracle 域未证明 | 资源观察失败 |
|---|---:|---:|---:|---:|---:|---:|
| main cost | 168 | 127 | 24 | 7 | 6 | 4 |
| main differential | 168 | 115 | 24 | 23 | 0 | 6 |
| SpotIt official cost | 28 | 21 | 3 | 2 | 1 | 1 |

原记录的 312 条 ATTEMPTED_EFFECT_UNKNOWN 在具备 started + COMPLETE + FINAL_COMPLETE 回执时，新增独立字段派生为 RETURNED；原字段没有改写。其中资源异常和未知结果依然在相应失败类别，不能将 312 写成成功数。另 52 条保留 NOT_RUN_CONTRACT_STOP，但只有 51 条通过严格 typed-rejection 门：SpotIt slot 129 虽有原始 CONTRACT_UNSAT_REJECTED，仍因 RSS_OBSERVATION_UNAVAILABLE 归入资源失败。

11 个资源异常全部保留：main cost 19/39/51/83，main differential 11/28/44/88/106/147，SpotIt cost 129。资源异常以 stop_reason **字段存在**判定，包括空值，不以其字符串是否 truthy 判定。

旧 main cost slot 52 的 OFFICIAL_ATTEMPT / NOT_RUN 外层状态、ATTEMPTED_EFFECT_UNKNOWN、缺失 cleanup 和完整冷成本全部保留为历史未完成尝试；恢复结果另行选择，不覆盖旧记录。初始化 RSS=0 仍保留为原始字段，统计中记缺失，不以 checkpoint 替代完整冷成本。因此 main cost 为 168 个逻辑槽、169 次启动尝试。SpotIt 未选的 140 个臂保持 NOT_SELECTED。

## 冻结依据与限制

- statusfix manifest：`runtime_fair_v5_statusfix/SOURCE_AND_DIFF_MANIFEST.json`，SHA `8b2f6fe59b659c1c5810b378c1bed5545e527c8a340a436061086df1af935d3c`。
- 新 worker：`5848538a168495d3a336afedd5d1efe696d43eea8a15d353679b905be7ecc320`；helper：`65edfe932aee49a64f3986d420eb3115bb71d271d3ac402e039052ea5826ca5f`。
- 最终汇总器：`experiments/BUILD_FINAL_V5_EXECUTION_CUT.py`，SHA `83a23fc07b0185f39bd106be2a4c1d893c5c18a4a99592012ca6ed098275fe32`。
- 最终截面：`experiments/FINAL_V5_EXECUTION_CUT.json`，SHA `1d6d0291fda36937a26da6b46c9d07b18899a21686708fa4279c7a814e48b95c`。
- 逐槽 selector：`experiments/V5_SLOT_SELECTION_FINAL.json`，SHA `791693b25afdbae2be4143dadac51cf9a2af315417086ca56a96a3d9076f9e1b`。
- 本报告机器证据：`PAIR_WORK_STATUS_FIX_INDEPENDENT_REVIEW.json`，SHA `8df48aa798c9422cef6bc92a8c169b7a612bd0a88dba582394d21c6164bb4d5d`；逐行独立审计代码为 `audit_v5_status_derivation.py`。

最终截面基于旧冻结 v5 的真实回执，不能称 statusfix 已生成这些历史记录。本审阅只确认状态修复与衍生记账，不新验证一般 SQL 语义、方法创新、性能优势、自然数据泛化或未冻结稿件。所有上传、push 和目标重跑均未进行。
