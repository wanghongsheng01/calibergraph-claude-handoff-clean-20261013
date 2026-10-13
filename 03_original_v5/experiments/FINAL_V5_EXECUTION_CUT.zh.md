# v5 执行最终截面

所有注册的逻辑选中槽已有唯一终态。原始结果、严格有效查询结果、预期类型拒绝、资源失败分开记账；新六项只属于构造适配器回归控制。

| 阶段 | 完整注册槽 | 选中逻辑槽 | 已启动尝试 | 严格有效查询结果 | 预期类型拒绝 | 资源/预算失败 |
|---|---:|---:|---:|---:|---:|---:|
| main_cost | 168 | 168 | 169 | 127 | 24 | 4 |
| main_differential | 168 | 168 | 168 | 115 | 24 | 6 |
| spotit_cost | 168 | 28 | 28 | 21 | 3 | 1 |

cost 分母为28×6臂；differential为28×2查询×3candidate，两组168独立。SpotIt仅选每配置official臂28/168，另140未选择，不能说已运行168。旧 campaign/queue 的停滞标签保留；完成依据是逐槽 terminal 与精确 worker SHA。

| 阶段 | 原始 final_decision | 派生类别 |
|---|---|---|
| main_cost | {'unsat': 78, 'sat': 52, 'unknown': 8, 'UNKNOWN_ORACLE_DOMAIN': 6, 'CONTRACT_UNSAT_REJECTED': 18, 'UNVERIFIED_CONTRACT': 6} | {'STRICT_VALID_PAIR_RESULT': 127, 'RESOURCE_STOP_OR_BUDGET_FAILURE': 4, 'SOLVER_UNKNOWN': 7, 'ORACLE_DOMAIN_UNPROVEN': 6, 'EXPECTED_TYPED_NO_QUERY_REJECTION': 24} |
| main_differential | {'UNSAT_DIFFERENTIAL': 120, 'UNKNOWN_OUTPUT_DIFFERENCE': 24, 'CONTRACT_UNSAT_REJECTED': 18, 'UNVERIFIED_CONTRACT': 6} | {'STRICT_VALID_BOUNDED_DIFFERENTIAL_AGREEMENT': 115, 'RESOURCE_STOP_OR_BUDGET_FAILURE': 6, 'SOLVER_UNKNOWN': 23, 'EXPECTED_TYPED_NO_QUERY_REJECTION': 24} |
| spotit_cost | {'unsat': 12, 'sat': 9, 'unknown': 2, 'UNKNOWN_ORACLE_DOMAIN': 1, 'CONTRACT_UNSAT_REJECTED': 3, 'UNVERIFIED_CONTRACT': 1} | {'STRICT_VALID_PAIR_RESULT': 21, 'SOLVER_UNKNOWN': 2, 'ORACLE_DOMAIN_UNPROVEN': 1, 'RESOURCE_STOP_OR_BUDGET_FAILURE': 1, 'EXPECTED_TYPED_NO_QUERY_REJECTION': 3} |

RSS_OBSERVATION_UNAVAILABLE 表示RSS监测不可用，不是实际RSS超限、内存耗尽或OOM证据。这些终态不重跑，原判定、退出码、清理和成本全部保留，严格有效结果计数排除它们。

旧raw pair_work_status原样保留。只有明确pair_work_started且COMPLETE/FINAL_COMPLETE才派生查询工作RETURNED；该值仅说明子阶段回执，不等于solver已决定、oracle验证通过或资源合格。每条派生均附worker/监督日志/汇总源码路径和SHA。

| main cost 臂 | 严格有效/28 | 预期类型拒绝 | 资源/预算失败 | 冷CPU已知合计秒（含失败） | 未测完整冷CPU尝试 |
|---|---:|---:|---:|---:|---:|
| official | 20 | 4 | 1 | 62.612200 | 1 |
| official_generic_smt | 21 | 4 | 0 | 63.179959 | 0 |
| flat | 23 | 4 | 0 | 37.110296 | 0 |
| product | 19 | 4 | 1 | 73.661139 | 0 |
| selector | 22 | 4 | 1 | 36.793204 | 0 |
| official_canonical_sql | 22 | 4 | 1 | 50.485388 | 0 |

| 新控制 | main cost 原始判定（六臂） | main differential 原始判定（两查询×三臂） | SpotIt official |
|---|---|---|---|
| D01_literal_left_forced_A6 | {'sat': 6} | {'UNSAT_DIFFERENTIAL': 6} | {'sat': 1} |
| D02_same_SQL_same_C | {'unsat': 6} | {'UNSAT_DIFFERENTIAL': 6} | {'unsat': 1} |
| D03_no_C_same_pair | {'sat': 6} | {'UNSAT_DIFFERENTIAL': 6} | {'sat': 1} |
| D04_contradictory_literal_left | {'CONTRACT_UNSAT_REJECTED': 6} | {'CONTRACT_UNSAT_REJECTED': 6} | {'CONTRACT_UNSAT_REJECTED': 1} |
| D05_inverted_BETWEEN_contract | {'CONTRACT_UNSAT_REJECTED': 6} | {'CONTRACT_UNSAT_REJECTED': 6} | {'CONTRACT_UNSAT_REJECTED': 1} |
| D06_unsupported_whole_C | {'UNVERIFIED_CONTRACT': 6} | {'UNVERIFIED_CONTRACT': 6} | {'UNVERIFIED_CONTRACT': 1} |

D01 main cost 原C成立、A=6实际见证与原SQL SQLite NULL对6同时验证：6/6。E10、D04、D05的CONTRACT_UNSAT_REJECTED是合同矛盾，不能记作pair UNSAT；D06的UNVERIFIED_CONTRACT须连同无query/无fallback证据保留。

原slot52的STARTED/ OFFICIAL_ATTEMPT及旧worker哈希保留为INTERRUPTED_EFFECT_UNKNOWN，恢复尝试另计；旧终态RSS观察失败保留，不能因raw sat/unsat或exit0就改成严格成功。历史中断缺少完整冷CPU/墙钟，worker checkpoint只作下界，不当零成本。

| 阶段 | base-only SAT | normalized C XOR reference | full-C一致性 | 全尝试清理状态 |
|---|---|---|---|---|
| main_cost | {'sat': 162, 'NOT_RUN': 6} | {'unsat': 162, 'NOT_RUN': 6} | {'sat': 144, 'unsat': 18, 'NOT_RECORDED': 6} | {'COMPLETE': 168, 'NOT_RECORDED': 1} |
| main_differential | {'sat': 162, 'NOT_RUN': 6} | {'unsat': 162, 'NOT_RUN': 6} | {'sat': 144, 'unsat': 18, 'NOT_RECORDED': 6} | {'COMPLETE': 168} |
| spotit_cost | {'sat': 27, 'NOT_RUN': 1} | {'unsat': 27, 'NOT_RUN': 1} | {'sat': 24, 'unsat': 3, 'NOT_RECORDED': 1} | {'COMPLETE': 28} |

原22配置完整字典与v4一致，逐槽对照仅列单次结果与冷进程耗时。v5新增共同合同适配及XOR审计，不能据此宣称加速比或稳定强基线优势。所有失败、fallback、oracle和cleanup成本保留；无完整计时者明确记缺失。

结果仍限于注册源AST及有界编码；不证明源文本解析完整性或任意SQL正确性。SpotIt真实AUTO_SET单独披露，单标量set/bag一致不等于bag实现。

身份核对失败项：0。完整槽位/尝试账本、原结果、SHA及恢复证据见 [FINAL_V5_EXECUTION_CUT.json](FINAL_V5_EXECUTION_CUT.json)。本汇总只读取既有文件，不执行目标。
