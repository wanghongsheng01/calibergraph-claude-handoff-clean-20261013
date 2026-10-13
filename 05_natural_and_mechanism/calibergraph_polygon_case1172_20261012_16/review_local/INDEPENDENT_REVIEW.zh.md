# #1172 单次双模式运行独立后审

结论：本批两个模式的 `VALIDATED_NEQ` 均有独立的原 SQLite 合法反例支持，运行记录与冻结参数一致。最终作者 RESULT.zh.md、RECOVERY.zh.md、SUMMARY.json、STAGES.csv、BATCH_CLOSED.json 已完成复核，与执行证据一致，无剩余必须修复项。本次审核没有调用 solver、作者 replay/lift 函数或外部进程探测，没有修改原始证据。

独立脚本 `independent_replay.py` 仅用 Python 标准库读取冻结文件、检查 SHA256，并在新的内存 SQLite 连接执行原始 DDL 和 SQL。输出 `independent_replay.json` 保存详细审计结果和已审核运行输入 SHA256。全部 FREEZE 文件与 OLD_PRESERVATION 项当前哈希匹配，attempt marker 绑定的 FREEZE SHA 匹配；15 的准备态 gate 仍为 false，16 的新授权 gate 为 true。

原源为 09/sources_local/thrombosis_prediction__1172，gold、predicted、full-schema 三个 SHA 均独立核对。原 DDL 共 3 表、64 列（Examination 13、Patient 7、Laboratory 44）；2 项 PK 声明为 Patient(ID)、Laboratory(ID,Date)，3 项显式 NN 为 Patient.ID、Laboratory.ID、Laboratory.Date，2 项 FK 为 Examination.ID 与 Laboratory.ID 指向 Patient.ID，两个 FK 的 ON UPDATE/DELETE CASCADE 均保留。声明总数是 7，不能将 Laboratory 复合 PK 的两列误算成两项 PK 声明。

两份抽象见证均逐项检查完整列集、行宽、每表 N≤1、Int/NULL 与 SEX 文本类型、全部 PK/NN 和两个 FK，然后独立实现事前约定的类别提升。升格前没有把错误 FK 重命名为 1 后再验证。提升结果与归档具体见证逐值、逐类型相等；原 abstract_witness 同时与 raw_return 和 cex 相等。每表恰好 1 行，非空 ID 由 58 映射为 1，Laboratory.Date 由 59 映射为 0，SEX 为 M，T-BIL 由抽象 2 映射为具体 2.0，其他已有 NULL 均保持。Date=0 在原 SQLite DATE 亲和性下合法，并不是 ISO 日期或通用 DATE 语义实现。

新连接启用 foreign_keys，原 DDL 原样执行，按父表优先插入所有 64 列并提交。foreign_key_check 为空、integrity_check 为 ok、DDL 签名不变。两模式原查询回放均为 gold=[[1]]、predicted=[[0]]，因此均为合法且区分原 SQL 的具体反例。

运行分母完整为 2 个模式槽，UA→precise 各一次，本批成功 2、未知/失败 0，没有过滤未完成槽。UA 内部两次 SAT 检查、precise 一次 SAT 检查，总共 3 次 solver check / 3 次 native launch；UA 的两次内部调用不能称为科学重试，也不能把两槽误述为总共两次求解。两个 worker 退出码 0。父 controller 的 5 个 owned Popen 句柄均有 wait 记录及确定退出码，3 个 native 句柄为 -15，发生于已产出结果后的清理；未被错记为 3 个 solver 失败。UA 全部句柄 wait 后才启动 precise worker，证实模式槽串行。

controller 执行窗口（含两槽、清理）为 1.292468209285289 秒，低于冻结 60 秒。它不包括执行前输入哈希检查、冻结准备或本次后审；不能当成完整项目开发成本。UA/precise 槽墙钟分别为 0.8917383328080177 / 0.39941275026649237 秒。每次 native 命令都含 -T:3 和 -memory:512，各检查记录耗时低于 3 秒。512 MiB 是每个 Z3 的内部内存限额；本证据没有父子进程合计 RSS 保证，不能把自身 Python RSS 采样扩写为全进程内存验证。未访问 unrelated_project 或外部进程 RSS。

阶段记录包含 imports、schema_C、parse、encode、search_including_solver、solver_calls、decode、replay，均已完成且无 protocol error。solver_calls 是 search_including_solver 的子阶段，decode/encode 也可能嵌套，不能把各字段简单求和当端到端时间。schema_C 覆盖 load_contract；原 SQL 解析、符号编码、搜索与原 SQLite 回放是不同证据阶段。当前没有 unknown/timeout/UNSAT；今后这类结果必须保留在全部已冻结槽的分母，UNSAT 仅能表述为有界符号结论。

两次成功只说明：这个已暴露的开发例，经特定 #1172、N≤1、标准新 SQLite 连接的观察等价适配，可以被此强方法解决。适配沿用 15 的经修复并独审通过的证明边界，包括禁止 TEMP 遮蔽、ATTACH、自定义 UDF/排序规则。不能据此宣称原版 baseline 原样复现、通用 REAL/DATE 支持、N>1/其他案例覆盖、新颖性或性能优势；适配本身不能称为创新。它也不独立证明 Polygon 整个符号引擎的正确性。单例开发暴露和仅一次运行不支持统计比较。

最终摘要的两个 abstract_witness SHA 与两个 concrete_witness SHA 分别相同且与实物相符：是两次模式运行成功、仅一个不同的具体数据库，不能当作两个独立失败现象。SUMMARY 全部分母/状态、STAGES 各项计时、BATCH_CLOSED 的三个绑定哈希逐项与原运行记录核对。RECOVERY 的禁止再次运行/删除 attempt 与 closed marker、恢复固定第三方源码及二进制的规则符合本批唯一尝试边界；私有仓库备份实际完成状态不属于本地后审的验证范围。

参照未修改的 13/RESULT 和 14/RESULT 历史证据，当前固定10例中2个原输入无效，8个有效输入中3个已有运行证据，剩余5个仍未准入。这是准入/运行覆盖 3/8，不是 3/8 的求解成功率；#319 为有界符号 UNSAT 控制。#1172 已不能继续支持新机制必要性，停止为此例追加机制或重跑争胜的结论有证据支持；不将剩余未运行输入记作强基线失败。

本报告及作者最终文档、独立脚本和结果的哈希收录于 INDEPENDENT_REVIEW.json（该 JSON 不自引用）。最终审核完成后本审查者停止修改，可由父任务归档。
