# 第六轮：完整约束模型生成、原 SQL 回放与成本实测

2026-10-11 14:29 UTC 实验结束；作者读数，待结果独审。**本轮没有新方法、没有公平强基线优势，没有可报告的区分反例。** 十二槽全部保留：5 个 exact-N 官方编码 UNSAT，4 个 UNKNOWN，3 个在查询 SMT 检查前退出。两个整数来源实际生成的 6 个完整约束模型通过独立 C 核验，并执行原 SQL 共 12 次，输出均相同；这是生成与回放链的可行性证据。

## 固定分母与结果

四个来源在本轮结果出现前按已记录规则固定，来源于**已经暴露的 21 组开发数据**。其 SQL、schema、完整 operational C 与旧来源哈希不变。该选择没有结果盲法，不是新的独立测试。旧完整公开语料也已经扫描，不能重新命名为未见测试；最终保留测试未访问。

| 来源 / 原公开行号 | exact-N=2 | exact-N=4 | exact-N=8 | C 模型独立回放 |
|---|---|---|---|---|
| dev03_07 / LeetCode1173 / 11415 | UNSAT | UNSAT | UNSAT | 不准入：DATE、除法和 ROUND 方言/解码未建立 |
| dev03_10 / LeetCode1264 / 13041 | UNSAT | UNKNOWN：timeout | UNKNOWN：out of memory | 3/3 完整 C 通过，原 SQL 输出相同 |
| dev03_15 / LeetCode1421 / 15534 | UNSAT | UNKNOWN：timeout | UNKNOWN：out of memory | 3/3 完整 C 通过，原 SQL 输出相同 |
| dev03_04 / LeetCode1468 / 17255 | 比较编码退出 | 比较编码退出 | 比较编码退出 | 不准入：小数 ROUND 与 VARCHAR 解码未建立 |

N 表示**每张原始表恰有 N 个活行**，不是最多 N 行。12 次完整 C 非空检查全部 SAT；9 次查询检查为 5 UNSAT、4 UNKNOWN；另外 3 槽查询检查次数为 0。共 21 次 SMT 检查。没有查询 SAT 模型，也没有经查询 SAT 导出的、独立 C 核验和原 SQL 确认的区分反例。

1468 的三个失败均为 `OFFICIAL_COMPARISON_FORMULA_ENCODING` 的 `NotEquivalenceError`，消息为 “Symbolic reasoning: NOT EQUIVALENT.”。它没有给本协议所要求的查询 SAT 检查、模型及回放，因此保留为 inconclusive；不把异常字符串升级为自然缺陷或无界不等价证据。

## 真实生成与回放，不能混作方法成功

1264 和 1421 的 6 个模型取自同一次已验证的 `FULL_C_NONEMPTY_CHECK`。它们合计物化 56 个行，逐模型独立检查所有原 operational C（包括官方笛卡尔列比较与严格 FK 语义），并在 SQLite 3.53.3 内存数据库原样执行两条 SQL。输出按 bag 比较，允许输出顺序不同。

1264 的 N=2、4 模型，两边输出都为空；N=8 两边各输出 1 行。1421 的 N=2、4、8 模型，两边分别各输出 2、4、8 行。六个回放均未发现差异。这些模型记录为 `C_MODEL_SANITY_ONLY_NOT_QUERY_SAT`、`query_sat_witness=false`；全部成本与正式查询路径共用原预算，没有增加求解次数或预算。不得把 6/6 回放完成写成“反例生成成功率 100%”。

## 成本与机器保护

| 可核查项目 | 实测 / 登记值 |
|---|---:|
| 注册 / 返回 / 未运行槽 | 12 / 12 / 0 |
| 监督器及所有已回收子进程 CPU | 18.274636 秒 |
| 准备 CPU 保守预留（非测量） | 10 秒 |
| 报告尾部保守预留 | 0.2 秒 |
| 总计费 CPU / 上限 | 28.474636 / 60 秒 |
| 12 个 worker 的 wait4 CPU 合计 | 14.442653 秒 |
| 最大单 worker CPU / 上限 | 2.166776 / 3 秒 |
| 最大 worker 主流程 wall / 上限 | 2.147482 / 4 秒 |
| 最大 wait4 峰值 RSS / 上限 | 258162688 / 268435456 字节（约 246.20 / 256 MiB） |
| 查询 SMT check CPU 合计 | 2.500993 秒 |
| 完整 C SMT check CPU 合计 | 0.063040 秒 |
| 官方与 native import CPU 合计 | 7.620111 秒 |
| 各槽启动前 1 分钟负载范围 | 2.5762–2.7139（阈值 4） |
| 各槽启动前可用内存比例 | 34%–36%（阈值 25%） |
| 并发 worker / nice | 1 / 15 |
| 监督器资源违规 / 重试 | 0 / 0 |

两次 `out of memory` 是 Z3 在登记的 128 MB 内部限制下返回 UNKNOWN；不是监督器外部 256 MiB RSS 违规。两次 timeout 在登记的 700 ms check 限制附近返回。计时为单次观测，不能据此宣布实例科学上困难。worker、父进程和内存探针 CPU 的总账避免重复相加；内层回放阶段包含于外层控制阶段，不能再重复相加。逐槽 import、parse、scope encode、comparison encode、SMT、C 验证、物化和回放成本见 `observed_readout.json` 与原始 receipts。此报告的读取聚合和事后哈希核验不属于监督器测量区间。

## 强控制如何改变解释

运行前冻结的 `protocols/ANALYTIC_CONTROLS.zh.md` 指出：1264 是 CASE 默认 ELSE NULL 加内连接换序/别名变化；1421 是 LEFT/RIGHT 保留侧互换、行相等与逐列 AND、IFNULL 与二参数 COALESCE 的同义关系。这些基础恒等式已经解释两对查询。它们是语义控制，**没有实现或测量为计时基线**。

因此，N=4/8 下出现 timeout/OOM 说明该固定 bounded 编码在这些资源限制下未返回判定；不能把“已知恒等式可以直接判定的对”包装成一个新反例机制的科学收益。下一算法若仅做这些正规化，也属于既有证明/优化控制。没有候选方法可进行消融，本轮不编造消融结果。

同时，本轮说明“原系统没有 JOIN”的成因不能全部归为求解成本：旧入口筛选时根本没有进入求解器；现在完整 schema/C 进入官方链后，有 9 次真实查询检查，且另 3 次停在比较编码。前端覆盖、语义准入、编码成本和求解预算必须分开统计。

## 机制裁决与已执行的下一步

本轮共同 equitable quotient 候选被直接先例否定：2026 年 *Structural Indexing of Relational Databases for the Evaluation of Free-Connex Acyclic Conjunctive Queries* 已有相应类大小/邻接度树 DP；本轮约束恢复只是受限分组分配。公开暴露 21 来源中严格候选片段覆盖 0/21。`literature/EQUITABLE_QUOTIENT_FALSIFICATION.zh.md` 记录其范围、反例和原文锚点。以上是作者理论审计，结果独审会复核，不能把索引已有实例的算法自动等同于未知实例反例搜索。

`new_validated_mechanism=null`，不能进入论文优势结论或投稿阶段。没有扩大 N、延长预算、换来源或重跑来求胜。后续已实际启动两项分离工作：独立审核第七轮约束多项式/PIT 的否定结论；在第八轮独立新目录研究一个严格超出 key-anchorability 的小片段是否具有保持碰撞的合法分离模板，要求给出非枚举成本界，否则继续明确否定。其理论工作不占用本机 SQL/SMT 资源，最终保留测试保持未访问。

## 证据身份与局限

- 登记协议 SHA256：`7a5c6fd9a38f59529031d8c6f475e9b2dacebb274474e8993f1d8dd188421f36`。
- 执行冻结清单 SHA256：`124434da8e12c466c7e7138f8cbfcd4eb06f5443419274b6cf99f1f31a5bfde7`。
- 批次 receipt SHA256：`16ca6e4d6e056e97afe764754eb3091f5d374fea2edc1ca53271ecad35538029`。
- 执行后全部 880 个冻结文件重算哈希一致；前三轮 manifest 身份均与之前固定值一致。前三轮这里只重查 manifest 文件身份，并非重新核验其全部历史文件。
- `INTERFACE.md`、静态作者 receipt 的“未执行/待审”文字是预执行快照，原样保留；真实执行状态以本轮 finalization receipt、登记协议和 batch receipt 为准。执行后新增的只读分析脚本不属于那 6 个执行源文件，也未进入这次 supervisor 运行。
- 业务 C 的真实性和完备性、自然业务缺陷身份、不同数据库方言全面一致性未建立。所有结论限于明示 operational C、exact-N 官方编码与两个获准 SQLite 回放的来源。
- 本轮结果独审与私有作者备份仍需完成。原始第三方来源和带来源内容的原始日志不向备份仓库再分发；完整可恢复性门仍是 `BACKUP_BLOCKED`，DataHub canonical 注册仍是 `DATAHUB_REGISTRATION_BLOCKED`，不能伪报整体完成。
