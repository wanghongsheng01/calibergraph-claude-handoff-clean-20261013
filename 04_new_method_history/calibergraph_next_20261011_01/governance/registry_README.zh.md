# 公开 JOIN 开发注册：HOLD

本注册冻结 **6 个开发来源组、6 对上游原始 SQL、12 个查询槽**，另保留 **4 个来源组、4 对、8 个查询槽**作为确认候选。两侧来源组标签交集为 0，原 SQL SHA-256 交集为 0。所有来源都来自同一个 VeriEQL LeetCode 数据集家族；问题文件标签不是已经证明的语义独立单位，也不能写成 10 个独立数据集。

当前仅完成离线 JSONL 结构清点、来源锁定和原文复制，**没有运行 SQL parser、solver 或 SQL 回放**。注册状态为 `HOLD_NO_AUTOMATIC_PROMOTION`，不提供自然缺陷金标，不支持 accuracy、自然缺陷检测率、未见测试泛化或方法优势的结论。

## 作者可读入口

- `data/development.jsonl`：完整开发记录；每行的 `source_record` 原样保留上游 `file/index/schema/constraint/pair` 的 JSON 值。
- `governance/registry_manifest.json`：注册承诺、分母、资源与暴露记录。reserve 只报告数量、文件路径和 SHA，不展开来源身份、SQL、标签或结果。
- `governance/registry_source_inventory.json`：旧 48,910 查询分母中三个输入文件的实际 SHA、大小和来源证据。
- `governance/registry_validation.json`：来源组分离、原 SQL 字节身份和实际静态检查摘要。
- `data/registration_attempts.json`：全部 10 个已预选注册尝试，包含失败占位规则；当前 10 个注册成功，均未回放。
- `data/source_json_errors.json`：此次 JSON 结构扫描全部错误；当前为空。
- `code/register_dataset.py`：标准库、单进程、离线登记与身份校验脚本。

`data/reserve_private/` 仅由数据注册方保存，不应交作者代理展开。它使用 0700 目录和 0600 文件，但所有代理共享同一 UID 和工作区，因此这只是工作流程约定，**不是 OS 隔离或可信隐藏测试**。没有可信隐藏 gold。独立评估环境、独立金标、访问边界和最终协议未建立前，不可晋级确认试验。

## 预选与保持失败

开发来源组为 182、614、1075、1581、1587、1715。先根据公开原 SQL 的 token/长度结构清点固定来源组，再在每组中选择满足“同一查询同时含 JOIN token 与 SUM/COUNT 调用 token”的上游原 pair，按 `(pair 中最长 SQL 长度, 两条 SQL 总长度, 源行号)` 升序取首个。没有读取逐例 solver verdict、最终测试标签或使用执行成功率来预选。其作用是选出可审查的小规模结构开发材料，并非随机抽样或总体适用率估计。

固定组分别保留自连接/派生表、DISTINCT 聚合、AVG 与 SUM/COUNT、NATURAL LEFT JOIN、SUM+HAVING、多个标量 SUM+LEFT JOIN 等边界。不能为匹配现有方法而删除 GROUP BY、改写 USING、移除 DISTINCT 或只留下 pair 中可支持的一侧；也不能因回放失败而换入另一条查询。后续每侧执行、拒绝、未知、错误和未运行均应另行记账，原注册文件保持不变。

该 token 筛选并不把 `JOIN` 理解为已经通过语义检查的连接，也不认证支持的 SQL 域。上游完整 schema 和 constraints 不得删除后再声称“无损适配”。旧 v5 对完整 schema/合同的支持域与 query eligibility 是不同问题；这批开发样本不能被预标成 v5 可运行。

## 三类资料的定义

| 类别 | 本注册中的含义 | 当前证据边界 |
|---|---|---|
| 原公开查询 / natural-query 候选 | LeetCode 上游冻结文件中的 SQL 字符串逐字不变 | 有公开文件、固定 commit、原问题文件标签、源行与 SHA；未逐条独立证明真人作者、生产使用或缺陷历史 |
| 原公开 pair / natural-pair 候选 | 同一上游行原有的两条 SQL 及上下文完整复制 | 配对构造过程未重新验证；没有独立缺陷标签，不能把一条视为 gold，不能把另一条视为错误 |
| 人工 adversarial fixture | 研究者专门构造的 SQL、改写、数据或约束 | 本注册没有构造 SQL 缺陷对；未来极小数据库 fixture 必须单独标为人工诊断数据，不能叫自然缺陷 |

因此，**本次没有找到可确认的自然缺陷对**。原始 pair 的存在不证明二者不等价；一个可回放的 counterexample 也只能支持明确前提下的该具体差异，不能反推原始业务/题目真值。

旧 Calcite 与 Literature 输入同样进入了来源清单，但没有加入本开发集。Calcite 是优化器基准；上游 README 明说 `literature-rewrite.jsonlines` 通过改写相关子查询简化。因此二者不能在没有额外出处链时被包装为未加工的自然缺陷来源。这里没有新网络核验或下载，固定 commit 与 URL 沿用旧下载回执。

## schema / constraints / 回放接口

每行 `source_record.schema` 为 `{表名: {列名: SQL类型}}`。`source_record.constraint` 是原上游 AST 列表或 null，可能包括 `primary`、`foreign`、`not_null` 等；必须保留全部。`source_record.pair[0]` 与 `[1]` 是两条原 SQL。`original_sql_sha256` 对字符串 UTF-8 字节计算，`schema_sha256/constraint_sha256` 对排序键的紧凑 JSON 计算；`source.raw_line_sha256` 还绑定原 JSONL 的整行字节（含换行）。

SQL/schema 回放由另一执行方单独完成，并保留失败。若将 schema AST 转换为 SQLite DDL，应把它标为**回放适配产物**，记录每条 constraints 是否精确保留、是否未验证以及 SQLite 与源方言的语义差异。空库或人工极小合法 fixture 上执行原 SQL 仅检验相应方言下的语法/绑定/回放；它不认证完整源合同或 pair 等价性，更不产生自然缺陷 gold。不得以剔除复杂 schema/constraints 换取运行成功。

## 暴露与独立终测条件

旧 v3/v4 已扫描完整 48,910 查询槽；旧汇总只有 6 个 eligible 查询且全部无 JOIN。该历史曝光不能因创建新目录或新 split 消除。本代理又读取了交接、措辞说明、来源回执、上游 README 和最终适用性报告；首次输出大 JSON 时被截断，截面中包含旧 parser 错误原 SQL。所有这些均明确属于暴露，不是新标签。后续仅用原来源的 JSON 结构、token 和长度选择，未读取逐例 solver verdict 或冻结终测标签。

reserve 必须称为“有历史暴露的确认候选”，不能称为全新未见 test。若未来进行终测，应先冻结代码/协议，由具备独立 gold 的评估方控制访问和执行，审查更深的来源/模板重合并保留所有失败；若主张未见泛化，需要来自独立受控新来源的数据，而不能自动提升本 reserve。任何暴露改变都必须追加审计记录。

## 实际静态验证与运行方法

冻结登记单进程实际用时约 0.477 秒、观测峰值 RSS 25,362,432 字节；原文身份验证 15 项、失败 0，用时约 0.067 秒、峰值 21,905,408 字节。脚本无网络/子进程/solver 导入；55 秒 SIGALRM 加逐行 RSS 观测，内存阈值 256 MiB，未声称 OS 硬内存隔离。

```text
python3 -B -I -S code/register_dataset.py verify
```

`build` 使用已保留的 private selector，并以新文件独占写入方式防止覆盖；本冻结输出存在时不能再次 build 到同目录。任何后续 schema/SQL 运行需使用新回执文件，不改这个注册快照。

已执行 `datahub list`，未发现覆盖本冻结 VeriEQL 输入的模块。按本任务仅写新根的明确限制，未修改外部 canonical DataHub，状态为 `DATAHUB_REGISTRATION_BLOCKED`。按 local-only/no-upload 限制没有远程备份，状态为 `BACKUP_BLOCKED_BY_EXPLICIT_NO_UPLOAD`。未读取凭据、下载网络材料、改旧文件或提交任何论文材料。
