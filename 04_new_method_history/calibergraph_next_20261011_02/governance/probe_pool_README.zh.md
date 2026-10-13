# 02 固定人工候选数据库池

本池有 **6 个已曝光开发来源组、32 个候选数据库**，按组分别为 4、1、5、8、8、6 个。每个候选保留对应来源的全部 schema 表，每张表恰为 2 行；原有 PK 键非 NULL 且元组互异。**这些是人工诊断数据，不是自然数据库、自然缺陷 gold 或未见测试。**

`data/development_v2.jsonl` 是 01 `data/development.jsonl` 的逐字节复制，原 SQL、schema、完整 constraints 和原注册值均未改动。新文件名不改变旧 48,910 查询扫描以及 01 开发/回放所造成的暴露。此次未打开任何 reserve 文件，也未执行 SQL、parser 或 solver。

## 文件与接口

- `data/probe_pool.jsonl`：全部 32 个已选候选。每行包括 `id/case_id/source_group_id/candidate_index/kind/mutation/rows/ic_check`。`rows` 为 `{TABLE:[{COL:value}, {COL:value}]}`；原类型名由开发记录的 schema 保存。
- `data/probe_generation_ledger.json`：全部计划和执行尝试；当前 32 通过、0 拒绝、0 截断，没有以新候选替换失败项。
- `governance/probe_pool_manifest.json`：源文件/复制文件/池/代码 SHA、固定生成规则、完整 C 解释、暴露和实测资源。
- `code/generate_probe_pool.py`：纯标准库单进程生成器和分离的 `check_contract(schema, constraints, rows)` 显式检查器。输出使用独占创建，不覆盖既有文件。

消费方必须先核验 manifest 中的池 SHA，并检查每行 `eligible_for_shared_probe`。若未来出现 `REJECTED_FULL_C`，它仍留在完整尝试分母，不能执行后宣称合法，也不能换入成功候选。被固定上限截断的描述符会以 `NOT_SELECTED_FIXED_CAP` 留账。

## 冻结规则

生成器只接收 schema 与完整原 C，不接收 SQL 或查询输出。先生成一个 base，再按表名、列名字典顺序，对符合条件的列依次加入全 NULL、单 NULL（固定第 0 行）和复制值（固定第 1 行复制第 0 行）变体。最多选前 12 个，**截断发生在完整 C 检查之前**；之后不因检查或查询结果而换样。

NULL 变体排除每个 PK 成员、FK 任一端参与列、`not_null` 列及 `gte` 左侧列。复制变体覆盖所有非 PK 列，包括合法的 FK 源列和 `gte` 列；其合法性另由完整 C 检查器判定。每次只对 base 的一个列做一类变体，不组合变体或进行结果导向搜索。

base 的 INT 值按固定列序号生成 `100*ordinal+row+1`；VARCHAR 保留为表名/列名/行号字符串；DATE 保留 ISO 日期字符串，按固定起点和列序号递增。FK 源值复制对应目标行值，`gte` 的常量下界只按源 C 调整。未从 SQL 中抽取阈值、字符串或聚合结果来挑值。

## 完整 OperationalIC

检查器直接逐条解释原 C，并检查全部原表、精确列集、每表恰 2 行及原 INT/VARCHAR/DATE 类型：

| 原约束 | 本池使用的官方 OperationalIC 解释 |
|---|---|
| primary | 所有键分量非 NULL，复合键元组唯一 |
| foreign | 当前来源均为单列 FK；每个源值非 NULL，且属于非 NULL 目标值集合 |
| not_null | 指定列的全部行非 NULL |
| gte | 参与值非 NULL；列与常量逐值比较，列间比较为全笛卡尔积 |
| neq | 列间所有笛卡尔积组合均不等且非 NULL；同表也包括跨行 |

未知约束/类型保守拒绝。该解释是当前固定官方实现的 OperationalIC，不应替换为常规 SQL 的 nullable FK/CHECK 直觉。旧 01 回放检查器逐行处理 `neq` 且禁止全部 NULL，未被复用。官方源码语义由另一 AI 代理只读核对；这不等于真人盲审或隐藏 gold。

所有 32 候选当前通过完整 C 的有限实例检查。它只证明具体人工实例符合这里明确的合同解释，不证明来源 pair 等价、不证明原业务真值，也不认证任意未来输入。

## 比较与证据界限

所有方法必须共用这份不可变候选集合。强基线使用与查询无关的通用 NULL-first 顺序；candidate 仅改变查询感知的排序；pure-fallback 作为消融。候选池不能按某个方法的输出增加、删除或换样，也不能把不同顺序产生的同一数据库记为独立样本。

这是已知 XData 风格的候选数据库预探测与 VeriEQL fallback 的工程组合。当前没有新科学机制或比较增益证据，可能没有增量；应保留全部零收益、错误、拒绝、未知和预算耗尽结果。科学状态保持 **HOLD**。

本次生成实际用时约 0.00622 秒，完整 C 检查累计约 0.00044 秒，单进程峰值 RSS 23,527,424 字节；1 秒 SIGALRM 没有触发。未使用凭据、网络、SQL 输出、solver verdict 或 reserve 内容；旧 01 文件没有修改。
