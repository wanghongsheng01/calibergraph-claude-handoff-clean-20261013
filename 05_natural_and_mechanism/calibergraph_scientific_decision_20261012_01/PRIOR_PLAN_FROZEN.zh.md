# ParSEval 成功路径机制核对与单因素方案（未执行）
日期：2026-10-12 UTC。作者诊断，尚未独立科学审核。状态：NO_INNOVATION_EVIDENCE / HOLD。

## 证据锁
本轮不重跑50来源，不改变旧结果或论文。既有作者备份 commit b523a067af447f2ec965acd0313d1bf06923d58b；官方实际运行版本 88cfe245bcf249a5b0df561a6b09c116ff2a2896。通过已授权 GitHub 连接只读恢复。以下8个官方文件的 Git blob SHA 与 parseval_admission_03/governance/OFFICIAL_SOURCE_LOCK.json 全部一致：
- src/parseval/generator/generate.py：9b270be87b0c6885a8a5f5e2abb0aad40e8c6ece
- src/parseval/generator/coverage.py：fd64ce3f6a18f7d3a04c4e71acb0e54e2aedd57f
- src/parseval/smt/solve.py：8d57cb40e93f4ecfdb8e91672a22044494041c9c
- src/parseval/main.py：9987bbc5ebdc25df7308d5611e070bac8968e82f
- src/parseval/instance/constraints.py：3b971020e73474d633badb905795c9c79bdd79a4
- src/parseval/instance/model.py：a28682535b69c06c187b45ddb1f33865a61c1948
- docs/speculate.md：9404b7f4739f9fa5762f8bc503f00323277c893c
- src/parseval/speculate/speculate.py：3d2a26736f1ac9a558eec96a8e583d559734e156
固定源码入口：https://github.com/sfu-db/ParSEval/tree/88cfe245bcf249a5b0df561a6b09c116ff2a2896
原论文：https://dbgroup.cs.tsinghua.edu.cn/jnwang/papers/vldb2025-parseval.pdf
论文的计划覆盖与推测赋值属于已知先例；下面对现代实现的判断以冻结代码为准，不把当前main或论文概述代替实测版本。

## 真正组合起作用的机制
1. 完整契约先限定合法空间。我们的普通 Catalog 接口适配保持原列、类型、NULL策略、PK/UK/FK，独立Python验C和PostgreSQL插入再验证候选。此步骤是准入，不是新搜索算法。SERIAL/default元数据和实际后端校准不等于生成器模拟历史序列/应用可达性。
2. speculate.py:519-715 从紧凑查询IR恢复列来源、表的不同出现位置、等值类、谓词常数、组大小与LIMIT需求；FK源/目标合并取值类并引入父出现闭包（537-561），非查询使用的父表尽量复用（646-660），唯一键需要新鲜值。它不靠独立随机填列碰出连接。
3. speculate.py:727-789 按正例、NULL、重复、否定等目标构造批次；必须满足C、产生非空并增加覆盖且不丢已有覆盖才保留。尚未产出前不永久留下负子查询阻塞行。1041-1098按键复用已有行、补FK父行；1129-1135从最受限列的provider取新值。
4. generate.py:169-278 用推测实例启动；零重数候选行仍是开放符号输入。先追求根输出，随后覆盖未覆盖的逻辑分支；非空后保护已覆盖分支。候选绑定预算1可扩至2；最初未产出则不按该预算限制连接激活。280-406在必要时扩充见证条件、按重数需求增行并传播父行需求，且接受前重执行确认目标覆盖没有丢失。
5. smt/solve.py:36起对完整性约束作闭包，按共享输入分连通分量，先CSP再Z3；Z3优先保持候选行不出现，必要时通过unsat core释放偏好。speculation内部的联合谓词也可以调用求解。因此“0次Z3 check”不等于“无求解器工作”。
6. main.py的disprove对真实后端比较两条原查询结果，每个接受的实例都可触发早停。该生成器的取值分支含固定概率采样，但不是神经模型的学习概率分布。覆盖是已达到的逻辑结果类别，不保证所有数据库、物理计划或程序行为。

## 对应真实成功与失败
GitLab #47：parseval_admission_04/runs/replay_supplement_01/RESULT.json + implementation/probe_worker_replay_supplement.py。117列、43个active C，普通BOOLEAN字面量兼容适配后，AFTER可lower；BEFORE仅真实后端重放，不声称其能lower。首候选45行通过完整C，两侧均11×42、独立新库复放一致；generation1、Z3 check0、callback1，返回reached/covered为空。这与generate.py:421-423的speculation seed callback即早停吻合，未进入后续覆盖补全，不能宣称全覆盖。此前RLIMIT_DATA、错误PG元数据读取、BOOLEAN转换均为执行/接入问题；32行cap阻断45行候选是预算停止，未观察到“生成空结果”。GitLab没有已知可满足NEQ，两侧相同不是搜索失败。
Discourse #3：real_task_screen_05/implementation/baseline_worker.py和runs/baseline_01/RESULT.json。单表5列，3NN、1PK、2 NULLS DISTINCT UK，无FK。先加载5行，双方[3,7,NULL]相同；随后6行产生[3,7,NULL]和[3,7,NULL,NULL]，新库确认。generation1、Z3 check2（UNSAT1/SAT1），attempt仅1次SAT accepted，最终8/8 reached覆盖。代码与回调顺序支持“推测种子之后由concolic补入第二个NULL重复值”；不能把FK机制归因于无FK的本例。旧日志未记录每次check的调用栈/偏好集，不能确认UNSAT究竟来自哪一条偏好或子目标，更不能把它算作两个独立目标试验。
来源是Discourse原提交5cef71e885004d32c5ee19382389773ecc80e6c8的终端ORM数据库语义重建；不是抓到的wire SQL或已证实应用故障。调用方后续可能去重。
50来源：1执行且已被基线解决，49未运行；共同支持范围内机制失败0，独立新test0。其余准入缺口仍是材料缺口，不能转写为基线失败。

## 唯一建议的关键单因素实验
问题：Discourse中speculation对合法NEQ的成本/达到路径到底贡献多少，还是主要由concolic覆盖求解完成？这是解释强基线的诊断消融，不是Caliber新方法实验。
只用已暴露Discourse #3；两臂仅改GenerationConfig.speculate=True/False。固定原SQL、完整C、官方commit、普通Catalog适配、seed0、sequential provider、袋语义、SQLGlot23.12.1、Z3 4.16.0、PG16.14/C/UTC。原成功数据仅作先验记录，不作为新对照运行；若执行，两臂都用相同只读追踪包装，以控制追踪开销。
最多两次顺序运行，每臂一次；不加seed、不调参数、不扩大分母。保留原5秒generation、500ms/solver、32 check、64行、8次candidate load、20/21秒CPU、35秒worker墙钟、nice19和512MiB采样RSS门；启动前检查实际unrelated_project/本机负载，资源不满足就延期。不要并发启动两臂或开GPU。
追踪：每个speculative goal是否因C/无新覆盖/丢覆盖被拒；首个合法非空、首个合法NEQ时间；CSP调用及回退；每次Z3调用目标、软偏好释放、状态；新鲜键/FK计数（本例应无FK贡献）、所有候选行数与完整C结果、typed bags、独立新库复放。wall/CPU/RSS及全部失败/超时/不支持/预算停止都入分母。
判据：False仍同预算发现NEQ则否定“speculation在本例必需”；True独有成功只支持组合启发式在此预算的贡献；False更省或True更多行，则保留该反例，不追加运行追回优势。任何输入不合法/后端差异先停为准入失败，不进入方法胜负。单种子两臂不支持稳健速度排名，无新test、无创新晋级。
目前没有一个已闭合真实来源且在共同支持完整C下强基线失败的任务，故不提出虚构的新方法收益。覆盖保护导致搜索受限可以是理论疑问，但当前没有已准入真实任务支持该改进，不进行“松保护”等新机制实验。DuckDB定向CSE触发未证新，DQP/QPG不重新命名。

## 交付与阻塞
本机exec只读pwd/目录请求未返回，父线程消息一次自动审批等待超时；未提交冷编译/ZIP/新实验命令。不能声称其已完成。已有本地稿件目录：
/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_overleaf_delivery_20261012_01/
overleaf内4个作者tex/bib文件与旧审核源字节一致，elsarticle class/bst及许可证来源已补齐，图为内嵌TikZ。参考11页PDF SHA256 9abfd1cf57de52287c3ab48df02de46ebe99a7646ba4f2f98dbf7e2d56582516。上一段创建和校验已有成功回执，本轮连接等待期间未重复修改。
本轮未完成冷编译、zip和其SHA；论文科学HOLD不变。正式拒稿/作者证据为2026-10-09留存：AAAI32719 /Users/loctek/Documents/Codex/2026-10-09/task-4/evidence_parsed/AAAI2027_32719/note_njWHyf7lfT.txt（Reject）及同目录evidence.json（Hongsheng Wang第一）；ICDE109 /Users/loctek/Documents/Codex/2026-10-09/task-4/portal_evidence_20261009_after_login/processed_cmt/ICDE2027_109.console_row.visible.txt（Reject）及ICDE2027_109_submission_summary.visible.txt（Hongsheng Wang唯一作者）。不是本日实时portal核验。原稿、投稿、RP平台未改。
