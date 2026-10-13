# 第 13 轮实际失败结果独立审查

日期：2026-10-11。结果审查者：`/root/round12_independent_lift_review`；失败材料整合者：`/root`。审查对象为已冻结的第 13 轮一次启动及其失败记账，不是第 14 轮研究材料，也不是新一轮执行许可。

**审查结论：PASS_FAILURE_ACCOUNTING_ONLY；真实 SQLite 复放仍为 NOTCOMPLETED。** 根任务保留失败、未知逐项状态及计划分母的处置正确。无阻断记账缺陷，无必要修订；禁止重跑、修代码后重试、请求主机权限或扩充预算。第 12 轮 H12 的否定仍只由手证与独立理论审查支撑，不能称为 SQLite 实测复现。

## 1. 审查输入与方法

【证据·文件读取】按顺序读取 `protocols/ROOT_EXECUTION_PROTOCOL.json`、实际 preexec `independent_review.json`、第 13 轮 execution freeze、启用源完整 400 行、禁用快照差异、全部 outer_launch 文件、原作者禁用快照材料及根任务实际启动说明。根任务失败冻结清单为 `ROUND13_FAILED_LAUNCH_MANIFEST.json`，SHA-256 为 `a3071c1913136bee4017cb73db4971947dfeba505a71e9a3451dadcd96606fb8`；失败处置 JSON SHA-256 为 `d929038776057732a08f5003991379c8d2ba8d47db9e496e612f77ac7362c02c`。

【证据·文件校验】失败清单的 30 项文件 SHA 全部通过；`author_snapshot_disabled/` 中原作者 9 项 SHA 全部通过；第 13 轮 preexec 审查的 4 项输出 SHA 全部通过。启用源、冻结记录、机器 preflight、实际审查报告、runtime provenance 和原始 stderr/exit 的绑定均匹配。审查输入哈希见 `REVIEW_INPUT_SHA256SUMS`。

【证据·审查方法】本审查只有文件读取、文本 diff、文件 SHA、JSON 语法/元数据检查、路径查看和手工控制流/算式推导。未导入、运行或编译 runner，未建库、执行 SQL、生成 family、枚举赋值、运行 fixture/模型/GPU/SMT/queue。另一只读审查代理独立核对了原始错误、时间打印和 preflight；未读第 14 轮文件、论文稿、源码或报告。没有读取凭据或修改源文件/权限。

## 2. 唯一启用差异与冻结范围

【证据·文件校验】三个禁用源副本的 SHA 均为 `467f8df522a9dbb845ec35542f9dd412452ede05debffb9d9056b144c30a5004`：当前 `code/source_snapshot_disabled.py` 及归档目录中的两个源副本。启用源 SHA 为 `50e6d27ad3ebaa9227e274f4247f97d91a2641bfb79ee8b6cf6d2d47df72d755`，与独立 preexec 批准的预期值一致。

【证据·文本 diff】唯一源差异是第 5 行 `EXECUTION_ENABLED = False` 改为 `EXECUTION_ENABLED = True`。构造、SQL、期望计数、分母和预算没有同时改变。原作者九文件的旧 checksum 应在 `author_snapshot_disabled/` 下解析；当前 live execution freeze 和启用源已经过授权变化，不能假称原作者清单对 live 路径仍全部匹配（根失败清单 `original_author_checksum_scope`）。

【证据·文件校验】实际审查报告 `protocols/independent_review.json` 与审查目录副本字节相同，SHA 为 `68c315fd2c8cb4f1844e8b2ce1a838c5758f5865fbc3b9b10a49d4d5ddb592f3`。批准状态明确是 `PASS_STATIC_PREEXECUTION_ONLY`，不能被当作 SQL 能力或结果验证。实际 execution freeze SHA 为 `0f2ca94b571c0f2d7099429a3b4303a90a965d12fef671d7115ac914bcc3ff12`，与 exit receipt 中的 pin 一致。

## 3. 原始失败证据与执行阶段

| 原始证据 | 独立读取的内容 | 能支持的结论 |
|---|---|---|
| `outer_launch/stderr_and_time.txt:1` | 外层 nice 的 setpriority 返回 Operation not permitted | 外层低优先级设置失败 |
| 同文件 `:3`–`:5` | `replay.py:34` 的 `os.nice(15 - priority)` 抛出 `PermissionError: [Errno 1]` | Python 在模块初始化阶段失败 |
| 同文件 `:6` | `0.05 real / 0.01 user / 0.01 sys` | 只有打印到 0.01 秒的外层时间文本 |
| 同文件 `:7` | time 的 `sysctl kern.clockrate` 返回 Operation not permitted | 完整 time 资源收据失败，日志无 RSS |
| `outer_launch/exit_receipt.json` | exit_code=1、attempt_number=1、retry_allowed=false | 记录的一次启动失败，不能判完成 |
| `outer_launch/stdout.txt` | 空文件，SHA 为标准空文件 SHA | 无 stdout 科学结果 |

【证据·控制流手推】源文件先设 wall alarm（第 21–22 行）、CPU RLIMIT（第 25 行），经过 Darwin 与入口 RSS 条件分支，然后在第 34 行失败。`sqlite3` 导入在第 40 行；state 初始化在第 93 行；`main()` 调用在第 400 行。因此该 traceback 指向 SQLite 导入、runner lock、输入构造和 SQL 执行以前的启动失败。这个推论以已核对的 source/traceback 为依据，不是逐数据库测量值。

【判断】失败种类为沙箱系统调用 EPERM，不是自动审批审核拒绝，也没有资源超限触发的原始证据。没有理由在本轮更换执行权限、删除限制或重试。外层 setpriority 失败后 Python 仍被启动，但内部相同优先级要求再次失败即停止；未绕过该要求继续到科学处理。

【证据·文件存在性】检查时 `run_once/` 不存在，因此在该路径下没有 `inputs_and_98_NOTRUN.json`、`result_receipt.json` 或 `completion.json`。后置 `EXECUTION_ONCE.lock` 存在，内容为 `ROOT_CONSUMED_SINGLE_OUTER_ATTEMPT_AFTER_PRE_MAIN_NICE_FAILURE` 和 `NO_RETRY`，SHA 为 `3f5f388fc21b2274d78249fcc2a26951fd085f0928bb4557adb77d4751456929`。

【判断】这把锁由根任务在保留失败后补记“外层尝试已消费”，不是 runner 运行到第 363 行的证据。文档与失败 JSON 明确区分 `root_added_consumption_lock=true` 和 `runner_created_lock=false`，没有把事后控制误写为原运行产物。

## 4. 计划分母、未知状态与 SQL 计费

【证据·协议】ROOT_EXECUTION_PROTOCOL 在执行前已规定：缺失或无效最终收据时整批 NOTCOMPLETED，98 项实际状态 UNKNOWN，计数 SQL attempted/completed 保守范围各为 0..196，不能用初始 NOTRUN 快照替代实际状态。实际 preexec 审查进一步固定 DDL、PRAGMA、INSERT 和全部显式 SQL 的范围。这不是见到失败后扩大容许范围。

【证据·JSON 元数据检查】失败账本正好包含 98 个不同 ID：`family_000` 至 `family_096` 及 `cartesian_control`，没有遗漏、重复或附加执行条目；每项只有 `id` 和 `actual_status`，后者全部为 `ACTUAL_STATUS_UNKNOWN`。这是计划 ID 的元数据账本，没有运行 family 生成器，也没有伪造 C/S、具体 rowsets、DBrows hash 或 SQL 返回值。`denominator_constructed=false`、初始/结果/completion 存在标志均为 false，与文件现场一致。

| 操作类别 | 完整成功执行的预注册计划 | 实际失败账本 |
|---|---:|---|
| DB 实例 | 98 | 98 个计划 ID；具体输入分母未构造 |
| COUNT SELECT attempted | 196 | null，UNKNOWN，范围 0..196 |
| COUNT SELECT completed | 196 | null，UNKNOWN，范围 0..196 |
| DDL | 98 | null，UNKNOWN，范围 0..98 |
| PRAGMA setter | 588 | null，UNKNOWN，范围 0..588 |
| PRAGMA readback | 588 | null，UNKNOWN，范围 0..588 |
| INSERT | 883 | null，UNKNOWN，范围 0..883 |
| 其他显式 SQL | 0（静态计划） | 不新增任何观测声明 |
| 全部显式 SQL | **2353** | null，UNKNOWN，范围 0..2353 |

【证据·手工计划核对】98 个 DB 每个计划有一个 DDL、六个 setter、六个 readback、两个 count。97 个字面 family 计划行数按区间长度为 48×8 + 24×9 + 12×10 + 6×11 + 6×12 + 1×12 = 870，再加控制 13，INSERT 计划为 883。总显式 SQL 为 98+588+588+883+196=2353；runner 合并 setup 计数为 DDL+setter=686。31 个 distinct-S 和 4 个 cheap 标记不是新增运行项。以上只是静态预算复核，没有生成数据库或执行语句。

【判断】2353 不能改写成 2335，也不能只报告 196 而隐去其他 SQL 成本。未知范围是各计数的保守边界，不授权给它们任意填值；completed≤attempted 等关系仍适用。所有实际 attempted/completed 数值继续为 null。traceback 虽提供很强的前 SQL 控制流证据，仍不能把缺失逐项观测填成 98 个“实测未运行”或“实测 0”。

## 5. preflight、runtime 与资源结论

【证据·机器收据】preflight 时间为 `2026-10-11T15:57:38.815669+00:00`，load1m=2.6533203125≤4，memory_pressure -Q 报告 free=37%≥25%。freeze 登记时间为 15:57:38.816356，exit receipt 为 15:57:50.472185；手算 preflight 到退出收据为 11.656516 秒，符合这次记录与 60 秒新鲜度要求的相容性。没有精确 launch-start 时间戳，故不报告精确启动时年龄。

【判断】外层机器收据合法且阈值通过；内部 `validate_authorization()` 在 main 内，源第 194–200 行的 fresh/live-load 检查没有到达，不能把外层收据通过称为所有运行时门都已验证。

【证据·文件校验】ROOT_RUNTIME_PROVENANCE 中三个文件的当前 SHA 全部与冻结值相符：Python binary `d67ff65d…1951db324`、`_sqlite3` extension `8eee64ea…1853759`、SQLite dylib `7364e142…fc93d47`。配置解释器的符号链接链解析到同一个已 pin 的 Python binary。此项是静态字节/路径核对；没有导入解释器来验证 SQL 能力，也不是对已退出进程的运行时二进制证明。

【证据·原始资源文本】外层只打印 0.05 real、0.01 user、0.01 sys，精度为 0.01 秒；没有 RSS 或完整资源记录。不能把 user+sys 的打印和 0.02 当精确 CPU，不能由打印文本计算精确利用率或据此声称完整资源限制成功。源控制流只能说明先前 guard 没在第 34 行之前阻止该路径，不能恢复未记录的 RSS 数值。

【判断】资源执行成功条件没有满足：nice 未建立，最终/整段资源收据缺失。失败 JSON 已正确记 `rss_available=false`、`complete_whole_launch_resource_receipt=false`、`performance_claim_allowed=false`。无性能、资源成功或科学收益主张可由此次失败获得。

## 6. 对科学结论的影响与最终裁决

【判断】本次执行既没有观测到 H12 的预期 20/19，也没有观测到反方向计数。它只是环境启动失败，不能作为支持或反对 H12 的新科学证据。第 12 轮的 `REJECT_H12` 仍由其冻结手证及独立审查成立；第 13 轮的静态通过和失败保全都不能增加“实测复现”标签。

【判断】根任务冻结说明 `docs/ACTUAL_LAUNCH_RESULT.zh.md:5`、`:7`、`:9`、`:11` 与源、原始日志和失败账本一致。无阻断记账发现，无必须修订项。结果审查可以通过，SQLite 复放不能通过；两种状态分别写入本目录 decision JSON。

| 已完成 | 未完成/不允许推断 | 后续处置 |
|---|---|---|
| 精确源启用与冻结绑定；原始失败保全；计划分母和未知状态记账；独立结果审查 | SQLite 计数、98 具体输入、完整 RSS/时间收据、所有运行时门通过、科学实测复现 | 停止本轮；不重试、不改权限、不扩预算；根任务统一备份 |

## 7. 审查红旗检查

| # | 适用红旗 | 判定与依据 |
|---:|---|---|
| 1 | 数字无证据锚点 | 未命中：时间来自原始 stderr；计划数与实际 null 分开，见 §§3–4 |
| 2 | 叙述与结果相反 | 未命中：exit1、无收据与 NOTCOMPLETED 一致 |
| 3 | 强控制被省略 | 未命中：Cartesian 仍保留一个计划 ID，状态 UNKNOWN，没有删分母 |
| 4 | 换指标改变成功判定 | 未命中：没有以短打印时间替代失败的 completion/RSS 条件 |
| 5 | 隐藏成本或资源优势 | 未命中：全部 2353 显式 SQL 的计划成本保留，没有实测效率主张 |
| 6 | 登记未交付却不披露 | 未命中：输入/结果/completion 缺失明确披露，并保守记账 |
| 7 | 便宜控制掩盖结果 | 未命中：cheap 标签没有新增或缩小 98 项分母 |
| 8 | 跨数据集方向相反 | 未命中：本轮没有自然数据集或跨数据集效果主张 |
| 9 | 正确性错误归因给模型/verifier | 未命中：手证、静态审查和执行失败三者分开 |
| 10 | 核心模块贡献未经证实 | 未命中：没有本轮新机制贡献声称 |
| 11 | 只保留成功样例 | 未命中：唯一失败保留，98 个 UNKNOWN 未删去 |
| 12 | 受限证据外推 | 未命中：没有将 pre-main traceback 外推成逐项 SQL 观测或完整资源成功 |

## 8. 交接及限制

本报告的 PASS 仅认可失败处理和记录，不撤销一次尝试上限。`EXECUTION_ONCE.lock` 必须保留，禁用快照及启用源码也必须保留原字节。原作者文档中“未执行/禁用”的陈述属于其历史静态阶段，根任务实际结果说明和本报告给出后续状态；不重写历史文件。

本审查新产生的文件仅在本目录。原始失败/作者文件未修改；第三方二进制只做哈希，不复制进备份。没有新外部数据源，因此无新增 DataHub 读取或注册动作；已有注册问题仍由父任务处置。私有备份及远端验证由根任务统一完成，本报告不提前声称已备份。
