# 第三轮来源、分组与约束合同审计

日期：2026-10-11。角色：作者研究中的来源核验；不是独立终审。

**结论：现有三源足以支持工程问题定位；尚不能建立真实业务缺陷 gold，也不能仅凭 32 个不同记录标签声称有 32 个语义独立问题。** LeetCode 的题目文件标签是当前最可用的分组近似；Calcite/literature 应单列为优化器与文献工程控制。接下来的有预算探测可以定位支持域、约束适配、编码或求解在哪一阶段失效；任意 2 秒超时不足以成立科学瓶颈。

本轮没有执行 parser、solver 或 SQL，没有网络访问、下载或完整数据扫描，没有读取 reserve。只读取已有说明/收据，并对三个公开源分别用 `readline()` 读取第一条 JSON record；输出字段、schema、约束和 SQL 长度，没有执行 SQL。旧冻结文件未修改。

## 实际证据与其能力

主要只读文件：

- 上游冻结 `sources/verieql_v1/README.md`，SHA 沿用既有收据：`51401a36ac82711f0e4eda818f43b446ab5421d26258e9e0d5dfdc2e9ed67189`。
- `public_leetcode/SOURCE_RECEIPT.json`：固定仓 `VeriEQL/VeriEQL`、commit `3b99928bf976c11cb59c9db6a177adba21f75798`；记录完整文件传输及结构清点。
- `calibergraph_next_20261011_01/governance/registry_source_inventory.json` 与 `registry_README.zh.md`：三个冻结文件的身份及已曝光/分组边界。
- `calibergraph_next_20261011_02/governance/probe_pool_README.zh.md`：上一轮明确采用的 OperationalIC 解释。

本轮未找到 Calcite/literature 各自独立的 `SOURCE_RECEIPT` 或逐约束提取台账，二者身份沿用已有三源 inventory；没有把继承的 SHA 表述为本轮全文件重新哈希。为定位来源曾检查旧 `overlap/SOURCE_MANIFEST.json` 与 `related_work/workload_inventory/source_manifest.json`，它们不提供本次三源配对或约束逐项出处，故不用于补足这些证据空白。

| 源 | 冻结身份（来自既有收据） | 本次仅一条 record 的字段证据 | 可以支持 | 不能支持 |
|---|---|---|---|---|
| LeetCode | `leetcode.jsonlines`，SHA `b97fc1293701682a25a2f6345f3630b3482ce49912463a7f4b76ab52665a13c9`；收据 23,994 对/47,988 SQL 槽 | `file,index,schema,constraint,pair`；首行 `file=benchmark/leetcode/raw_data/175.csv,index=0`，pair 恰两串 | 固定上游文件中的一对公开 SQL 与附带合同原样保留 | 哪条是正确答案、是否真缺陷、每条真人/生产来源、接受状态、配对采样/笛卡尔组对算法、约束提取忠实度 |
| Calcite | `calcite2.jsonlines`，SHA `5fc6e0740134220856e93743147038cacaf22cb9d9823e7d6b8da2b461939ac4`；inventory 397 对 | `benchmark,index,schema,constraint,pair`；首行 `benchmark=Calcite-397,index=1`；无原始规则ID/测试方法ID | 优化器改写验证的工程控制、相应 SQL 语义/编码覆盖问题 | 独立真实业务缺陷；每个 index 是独立规则族；具体使用哪条规则及如何生成此 pair 的完整链路 |
| Literature | `literature-rewrite.jsonlines`，SHA `4c5e2661797177fd865a3f57c887376cb01bcbeec57ec77a032124e04c77f42f`；inventory 64 对 | `benchmark,name,index,schema,constraint,has-symbolic-predicates,pair`；首行 `benchmark=conditional-ex1sigmod92,name=ex1sigmod92,index=0`，symbolic=false | 文献例子及改写后的工程控制 | 原封不动的自然业务 SQL；无加工缺陷；文献所有假设已被现有 C 完整编码 |

上游 README 明说 Literature 文件通过改写相关子查询简化，且实验运行的是此文件。Calcite 的优化器基准身份由既有来源库存支持，但此次一行 record/README 没有恢复到优化规则或测试方法的生成日志；不可把“优化器基准”扩张成已核每一对的生成机制。

LeetCode 收据计数为 23,994 对，README 声明 23,224 对，相差 770；这是已有收据记录的版本/计数不一致，不能自动归因某种配对方式。收据证实所有行包含 `constraint` 字段，其中 list 为 23,037，null 为 957；它没有说明 null 的语义，也没有给空 list 的个数。本轮不重新扫描、不推断这些缺失数字。

## 上游组对与约束来源：当前知道和不知道的分界

“原 SQL pair”目前严格指上游某一 JSONL 行原有的 `pair[0]` 和 `pair[1]`；不是本轮人为组对。但现有 README/收据没有给出采集脚本、submission ID、作者、AC/WA 状态、问题原文/DDL 到每条约束的映射，因而不能核实：是随机配对、全组合、错误答案对正确答案，还是研究者选取/调整后的对。记录 `index` 不能自行回答这些问题。**组对构造记 `UPSTREAM_PAIR_CONSTRUCTION_UNVERIFIED`。**

同样，C 是公开基准随行给定的 AST，其存在证明“上游给出了这些约束”，不证明“这些就是自然题目或业务域的全部正确约束”。例如本次 LeetCode 首行同时列出 ADDRESS.ADDRESSID 与 ADDRESS.PERSONID 各自的 primary 约束；这里只报告字面事实，不访问原题推定其正确/错误，也不凭常见 schema 印象删改它。该例说明必须分别标注公开合同忠实保留与合同业务来源核验。

README 还记录 LeetCode 603/607/1132 的 unsupported constraints 更新和 2025-10-31 错误信息更新。因此 paper 版本、当前 README、固定数据 commit、实际 engine 版本应分别锁定；不能以论文的一般支持声称固定代码对每条源 C 均可执行。

## 可用 source_group_id 与跨 pair 审查

| 源 | 建议可操作标签 | 独立性强度与限制 |
|---|---|---|
| LeetCode | `leetcode:<完整原file>`，例如 `leetcode:benchmark/leetcode/raw_data/175.csv`；另存 source commit、原file、原index、原行号 | 同一题目文件内所有 pair 合并一组，不能每个 pair/index 独立计数。不同 file 只是不同题目标签的近似，仍可能共享模板/SQL/数据合同；不是已证语义独立。 |
| Calcite | 记录定位 `calcite:Calcite-397:<index>`；**不要用它冒充独立组** | 缺原 test case/rule-family 映射。保守将当前 Calcite 来源作为一个控制族，或将多个 record 仅称控制记录；若后续恢复规则/测试族 provenance，再按原族分组。 |
| Literature | 优先 `literature:<name>`；并保留完整 `benchmark/index` | 不能把 conditional 前缀等合同变体直接拆为独立例子。name 仍是例子标签，需原论文/例子映射才能审查更深依赖；若存在不同 name 同例/同模板，要合并。 |

对最多 32 组的第三轮，建议真实来源近似组分母只使用 LeetCode 的不同原 `file`；Calcite/literature 单列控制数，不混为“独立自然组”。若 protocol 选择混源，至少同时报告 `source_label_groups` 和 `provenance_confirmed_independent_groups`，后者目前不能凭字段填成 32。

探测执行者在获准选中的候选上应保留：原 SQL 字节 SHA、canonical schema/C SHA、无序 pair 两侧 SHA；同组内不得重复计数，跨组完全相同 SQL/pair 应建立重合链接并保守合并/披露。仅有不同字符串 SHA 不证明不同模板；当前没有 parser/语义归一化审计，所以模板独立性继续标未知。不要为增加组数而替换失败、重复或不支持项。

## Full OperationalIC 不等于真实业务合同

OperationalIC 的“full”指将**本条上游记录所有 schema/C** 按冻结 engine 的实际解释完整保留、逐项支持或明确拒绝；包括约束类型、NULL 处理、列间比较对应关系及全部原表。它不意味着 C 在自然来源中正确、没有遗漏，也不意味着引擎解释与常规 SQL DDL 完全相同。

上一轮固定解释中：primary 是非空联合唯一；foreign 使用当轮源数据单列非空引用；`neq` 的列数组按全笛卡尔积比较；`gte` 的列间比较亦按全笛卡尔积。它们是特定上游实现合同，不能悄悄换成逐行比较或常规 nullable FK。第三轮遇到新的操作符/复合 FK/类型时，必须扩展审计或标 unsupported；不能因为上一轮六组合法就认证新 32 组。

建议将两个维度并行记录：

- `operational_contract_status`：是否原样、有定义、全操作符可解释、实例通过检查。
- `natural_contract_provenance`：每项约束是否有原题/DDL/业务说明出处、是否已核完整；本次三源不能统一填 VERIFIED。

具体数据库满足 C 且使两条原 SQL 输出不同，只能证明声明的方言、比较语义和 C 下的一个差异。它不决定原题哪条答案正确，更不生成自然业务 gold。

## 缺 C 与明确空 C 的分类

| 原始情况 | 建议状态 | 可执行/可声称范围 |
|---|---|---|
| JSON 没有 `constraint` key | `C_MISSING_FIELD` | 数据缺失；不得补成 `[]` 后宣称 full C。保留失败分母。 |
| `constraint: null` | `C_NULL_UNSPECIFIED` | 生产者未在该行给出约束列表；在无 producer 语义说明前不得断言自然域无约束。若另做空约束控制，必须显式标派生的 assumption，而非原合同。 |
| `constraint: []` | `C_EXPLICIT_EMPTY_OPERATIONAL` | 可运行“无额外 C”的操作合同；不等于原业务确实没有 PK/FK/其他约束。自然完整性仍未知。 |
| 非空 list，所有元素合法且全支持 | `C_PRESENT_FULL_OPERATIONAL` | 可按原 C 探测，SAT 必须独立验所有 C；业务真值另记。 |
| 非空 list 含未知/不支持/无效 AST | `C_PRESENT_UNSUPPORTED` 或 `C_MALFORMED` | 必须保留具体条目与原因；不能过滤未知项后降为 full。 |

若已有引擎把 null 作为“添加零条约束”，这只能证明 engine 行为；它不能解决源数据中 null 是未知、缺失还是明确无约束的出处问题。可单列 `engine_accepts_null_as_no_constraints=true`，同时保留 `C_NULL_UNSPECIFIED`。

## 32 组低资源探测的证据出口

用户授权上限：最多 32 个来源标签组、每组 solver 2 秒、单 worker、总 CPU 120 秒。本审计未消耗任何 solver 配额。执行方应按事先定义的 semantic strata 选择而非根据 verdict 换样；semantic strata 的标签本身若来自 token，应写成语法候选，不能当已确认 SQL 语义。

至少分开记账：`JSON/CONTRACT_INVALID`、`PARSER_UNSUPPORTED`、`ENCODING_ERROR`、`SOLVER_UNKNOWN`、`SOLVER_TIMEOUT_2S`、`SAT_INVALID_CONTRACT`、`SAT_REPLAY_MISMATCH`、`SAT_VALIDATED_DIFFERENCE`、`UNSAT_FIXED_SHAPE`、`NOT_RUN_GLOBAL_BUDGET`。若 timeout 在导入/编码/回放阶段，按该阶段另标，不能移名为 SMT timeout。单组多次 check 时保留累计 solver 用时，避免将“每组2秒”变成每次2秒。

总 CPU 应覆盖进程及子进程实际消耗，包括导入/编码/验证；单 worker 不意味着 fork 的 CPU 可以省略。保留墙钟、CPU、阶段时长和具体表行数向量。固定2秒或某固定行数上的 unknown/UNSAT不等于无界等价或难例下界。

若失败主要来自 C 缺失、字段/方言适配或 parser，只得到数据/工程支持缺口；若部分来源标签在完整合同及可用语义下进入 solver仍耗尽预算，只得到**这一实现、这一表示和这一预算下的候选求解难例**。建立科学瓶颈还需稳定复现、简单基线/编码成本分解及更广独立来源；第三轮不提前做此推论。

本轮没有构造或推荐新机制。后续是否建立真实问题，应由这份来源边界与低资源原始结果共同决定。
