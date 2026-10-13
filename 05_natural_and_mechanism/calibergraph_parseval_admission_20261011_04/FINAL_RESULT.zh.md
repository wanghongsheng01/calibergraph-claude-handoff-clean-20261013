# 原查询非空生成与 PostgreSQL 重放完成

本轮已经得到需要的执行事实：**普通布尔适配版 ParSEval 在 GitLab #47 原 AFTER 查询上，首个候选 45 行通过完整 C 检查；两条未改写原查询均返回 11 行、42 列，按原 ORDER BY 的输出一致，并在另一新建 PostgreSQL 数据库上复放确认。** 本次补充只调用一次生成器、只取首候选、SMT 调用为 0。此事实让该适配版成为本开发案例的已准入强基线，不是 CaliberGraph 新方法收益。

## 原版与适配版边界

官方 ParSEval commit `88cfe245bcf249a5b0df561a6b09c116ff2a2896` 原版仍在 BOOLEAN 上下文的 `'f'` 字符串转换处抛出 ValueError，完整保留。适配器只在真实 BOOLEAN 上下文将 t/f 转为相应布尔值，其他类型委托原实现；原 SQL 文件及哈希没有变化。PostgreSQL 实测 TRUE、FALSE、NULL 三个值上的 `'f'` / FALSE 与 `'t'` / TRUE 比较完全一致，另验证 8 个字面量形式。该普通兼容适配不作为创新。

原 AFTER 的 lowering 保留 42 列；原 BEFORE 由 PostgreSQL 完整执行，不声称 ParSEval 能 lower BEFORE。后端是新建 PostgreSQL 16.14、C/UTF8/UTC 环境，不冒称还原 GitLab 历史生产服务器、会话或排序规则。

## fullC、候选与结果

四表 117 列保持原顺序、真实类型和默认值；Catalog 43 条 active C 为 32 NOT NULL、3 PRIMARY KEY、6 UNIQUE、2 FOREIGN KEY。6 个 UNIQUE 均按 NULLS DISTINCT，其中 4 个键含 nullable 列。真实 PostgreSQL 核对全部列、9 个 PK/UNIQUE 索引的 NULL 策略、FK/验证与动作、42 个默认值或 SERIAL 项；16 项语义校准全部通过。生成前校准行已清除。

唯一被实际重放的候选由 projects 13 行、users 1 行、users_star_projects 14 行、project_authorizations 17 行组成。与生成器分离的 Python 验 C 和真实 PostgreSQL 完整行插入均通过，未放松或增添源 C。候选 SHA256 为 `f780633e689cdf9500dc711dbc7419c6c14dae49a5d5aee02a39648e4e487794`，完整合成 D、typed 输出与确认结果保存在 `runs/replay_supplement_01/RESULT.json`。

两侧各 11 行，项目 ID 顺序为 355、189、168、145、116、106、49、10、1、0、-1；42 列的值和类型及行顺序全部一致。独立新数据库再次执行两条原 SQL，也得到完全相同观察。对同一保存 D 的静态解释显示：9 个返回项目同时满足授权与可见性条件，2 个仅依赖授权条件；没有宣称完整分支覆盖。

## 全部分母与成本

| 阶段 | 观察 | 生成 | SMT | 原查询执行 |
|---|---|---:|---:|---:|
| 旧 03 第一次 | 作者 RLIMIT_DATA 设置失败，目标导入前退出 | 0 | 0 | 0 |
| 旧 03 第二次 | 原版 f 拒绝；作者 PG 元数据查询失败，DDL 前退出 | 0 | 0 | 0 |
| 新 04 固定 32 行流程 | 首候选 45 行触发重放上限，未保存 D、未验候选 C | 1 | 0 | 0 |
| 明确授权的独立 64 行补充 | 同一输入/seed/config，只取首候选，非空确认 | 1 | 0 | 2＋2 次确认 |

32 行上限记录及其冻结预算原样保留，独立补充有单独授权、协议、freeze 和 once-only lock。第一轮 D 未持久化，不能因两轮均为 45 行就声称两轮 D 已逐字比较相同。原记录的 NO_NONEMPTY 状态标签过宽，其实际含义已经在 `analysis/OBSERVED_ROW_CAP.json` 明确更正为行数上限阻断，不是观察到空结果。

补充流程总墙钟 5.970048 秒，worker CPU 4.89287 秒，worker peak RSS 85,671,936 bytes；首轮 32 行流程总墙钟 5.846599 秒。两轮均先通过资源门，单 worker、nice19、CPU 20/21 秒与墙钟 35 秒上限，未运行 GPU/大队列。RSS 是 worker 自身采样，非 OS 硬限额，也没有整组 PostgreSQL 内存测量；不声称 unrelated_project 性能零影响。两轮自己的 PostgreSQL 均已停止，PID 与 socket 已清除。

## 科学结论与交付边界

此次关闭的是工程准入和原查询非空重放，不是新方法验证。已有 ParSEval 机制在此案例无需 SMT 已提供非空数据，因此不能再用“这个原 JOIN 无法被强基线激活”支持新机制必要性；fresh-key、FK 传播与原有 speculation 仍是先例。原随机对照使用过不同引擎和预算，本轮不能构成公平的速度/成功率排名。

GitLab #47 没有预设可满足 NEQ；两侧相同不是生成失败，也不是等价性证明。本例此前已暴露，独立新 test 仍为 0。维持 **NO_GO_NEW_MECHANISM_CLAIM**，同时将 `analysis/BASELINE_ADMISSION_RECORD.json` 的适配版纳入后续受控比较基线。

终态只做一次集中独审和作者材料私有备份。最终审查见相邻 `calibergraph_parseval_admission_review_20261011_04/REVIEW_RESULT.json`，备份验证见根目录 completion receipt。来源、软件与旧数据不复制入备份；本轮生成的 D 为合成测试数据。DataHub 通用 SQL 研究模块仍未登记，保持 DATAHUB_REGISTRATION_BLOCKED；未修改 unrelated_project、旧冻结结果、论文或投稿材料。
