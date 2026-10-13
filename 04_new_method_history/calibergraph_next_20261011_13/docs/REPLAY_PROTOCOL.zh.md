# 第 13 轮：H12 合成负面控制的真实 SQLite 复放（未执行）

本目录只准备把第 12 轮作者手推的 H12 反例落到真实 SQL 返回值。它是一个预期已知的、人为合成的负面理论控制；不是新 test、自然案例、新机制、泛化或性能胜利。最多一个问题：在最终冻结且独审确认的第 12 轮构造上，真实 SQLite 是否返回这里预先固定的计数？这属于实现一致性复放，不把“标准库行合法性校验 + SQLite”称为科学双重评估。

当前 `EXECUTION_ENABLED=False`，第 12 轮作者 `AUTHOR_MANIFEST.json` SHA-256 已固定为 `dfa81be07edf21839bf83bdaeb9cb1ac065d03d909fc086fbbbaa890155aa33e`。root 已确认第 12 轮独审通过、结论 REJECT_H12 且无阻断，审查证据 SHA 保存在 freeze；第 13 轮代码独审仍 pending。本作者未导入、执行、编译本程序，未执行 SQL、family 枚举、建库或测试。只允许读写源文件、AST 解析、JSON 解析及 SHA-256。旧冻结目录不修改。private GitHub 备份由 root 统一处理。

## 固定对象与唯一假说

Schema 只有关系 `R(a,b)`，`a,b` 均 `TEXT COLLATE BINARY NOT NULL`，唯一 key 是完整二元组 `PRIMARY KEY(a,b)`，没有 FK，也没有额外 FD。不能误用单列 `a` 为 key。`WITHOUT ROWID` 只用于小表存储，不改变该关系约束。完整约束集称 `fullC`，不要与下述变量子集 `C` 混淆。

Body 为有向六环 `R(v0,v1), R(v1,v2), R(v2,v3), R(v3,v4), R(v4,v5), R(v5,v0)`；`H=unit`，`M=(v0,v1,v3)`，`N=(v0,v1,v4)`。opaque 文本 label `vi#t` 注入地编码变量 `vi` 及复制 tag `t`；SQLite 只进行 BINARY 相等比较，不使用数值亲和性、算术或额外排序意义。

`C` 遍历六变量的全部 64 个子集，全部 FD-closed。去掉 `C` 后，在原环的无向诱导图中逐个取非空连通分量 `S`。每个字面 `(C,S)` 均保留；不按 `S`、row hash 或数据库相同而去重。`C=empty,S=all6` 合法；`C=V` 无分量、无 entry。字面分母预注册为 97，distinct-S=31 仅解释重复成本。

对每个 `(C,S)`，分别取共享 tag 0 和 1；`S` 中每个变量以该同一个 tag 复制，其他变量固定 tag 0。每个 tag 对六个原子 materialize 一次完整 body assignment，然后对 relation tuples 进行 set-dedup。不是把每个 edge 单独做 Cartesian 积。预期两计数相等：`|S|=1 -> 9/9`，`|S|=2 -> 11/11`，`|S|>=3 -> 12/12`。因此该 family 预期没有任何分离项。

强控制只有一个：完整 Cartesian variable-clone，`n=(2,2,1,2,1,1)`，每条相邻 edge 使用两层之间的全 Cartesian 积，预期 13 行，`M/N=20/19`。代码中另写 13 个 literal rows，以标准库 set、类型/非空/唯一性检查核对构造合法性；不列举 query answers，也不产生第二套科学评估结果。

总分母是 98 个 DB 实例、196 次 fixed synthetic SQL 计数执行；不存在 original natural SQL source。`C=M` 的 `S={v2}` 与 `{v4,v5}`、`C=N` 的 `S={v2,v3}` 与 `{v5}` 是原 97 项上的 4 个 cheap-family 标签，不额外执行、补采或扩大分母。DDL、INSERT、PRAGMA 同样计费，setup statement、逐行 INSERT、PRAGMA 预算 readback SQL 都各记 attempted/completed，但不混入 196 次 engine count query。成功情况下每实例 7 个 setup statements 与 6 个 budget verification statements；插入语句数是实际 row 数。

## 真实 SQL 与记录

代码内固定两条 SQL，各包含六个 alias 的 `INNER JOIN` 并以 `r5.b=r0.a` 闭环；外层是 `COUNT(*)`，内层对 `r0.a,r1.a,r3.a` 或 `r0.a,r1.a,r4.a` 执行 `SELECT DISTINCT`。不接受查询输入，不以不可信字符串拼接 SQL。每个 entry 新建一个内存 SQLite DB，物理 schema enforce `fullC`，tuple INSERT 使用两个绑定参数。

首次计费生成阶段构造固定输入，并以 exclusive-create 写出 `inputs_and_98_NOTRUN.json`，随后才允许任何 SQLite 构造/计数。每项记录 `C,S,DBrows,DBrows_sha256,Nrows,count_M,count_N,expected_M,expected_N,expectedmatch,status,cost`。hash 是 canonical ASCII JSON row-array 的 SHA-256，不含末尾换行。初始 ledger 文件 hash 包含它自己的末尾换行。若该阶段失败，`denominator_constructed=false`，不得称已成功冻结 98 个具体输入。

实际返回值与每个期望逐条比对；一旦 count M 不符，不再执行 count N。任何 mismatch、限制接口缺失、资源失败、建库/序列化失败均截尾、无重试。已结束项目保留，当前项目标记 FAILED，未开始项目保持 NOTRUN；attempted/completed fixed synthetic count SQL 数分别记录。只在所有 98 项完成且 196 计数返回时才写 COMPLETED。

程序永久保留 `EXECUTION_ONCE.lock`，输出目录 `run_once` 也必须 exclusive-create。失败不删除 lock，不换新目录重试。外层必须把无 `completion.json`、退出非零、SIGKILL/SIGXCPU 或 wall exit 124 判为 NOTCOMPLETED；即使留下部分文件也不能声称成功。

## 资源边界（与 unrelated_project 同一台 Mac）

一个进程；没有 fork、worker、网络、自定义 native ABI、ctypes、ps 或子进程。只用 Python 标准库内建的 sqlite3/resource/signal/os 等。nice 至少 15，不提高已有更低优先级。`RLIMIT_CPU=(2,2)` 是全 `RUSAGE_SELF` 累计 CPU 上限，包含解释器已消耗的启动 CPU；1.95 秒 checkpoint 提前截尾。wall timer 从脚本第一条计时入口算 3 秒，SIGALRM handler 调用 `os._exit(124)`，不等待清理；timer 保持到自然退出，不提前 disarm。解释器启动前那一小段 wall 由外层整个 launch 时间补齐。

仅接受 Darwin；`getrusage(RUSAGE_SELF).ru_maxrss` 在这里按字节，128 MiB sampled peak-RSS guard。各阶段、固定输入循环、限制设置、DDL/INSERT 前后、SQL 前后、序列化前后均 checkpoint；SQLite progress handler 最多每 1000 VM ops 检查一次并立即中断失败。该 RSS 机制不是瞬时 kernel hard-RSS 限制；尚未验证其在该解释器上的实际表现。

结构上限：6 变量、64 masks、97+1 entries、每 DB 至多 13 行，每值只有固定四字符 opaque label `vi#t` 且 `t in {0,1}`，每完整六变量 join 的候选赋值至多 `6*2^6=384`，投影至多三列四字符文本。记录最多 98 项；单 JSON 输出上限 512 KiB；输入 freeze 上限 32 KiB、source 上限 64 KiB、preflight 上限 8 KiB。没有可扩展用户参数、大输入或动态 SQL。

SQLite 每 connection 设置并核对 limits：length=65536、SQL length=4096、column=16、expr depth=32、compound select=4、VDBE op=10000、function args=8、attached=0、LIKE pattern=64、variables=2、trigger depth=0、worker threads=0。page size 4096、max page count 32（主库 128 KiB）、cache size 64 KiB、temp cache 64 KiB、temp store MEMORY、threads=0。temp cache 是缓存预算，不宣称它硬限制 sorter 临时分配；固定最多 384 个三列四字符文本 tuples 的结构边界配合总 RSS guard。任何接口/平台不可测或限制无法建立即拒绝。

root 在启动前只读取得 load≤4、`memory_pressure -Q` 的 system-wide memory free percentage≥25%，写 `machine_preflight.json`，把精确文件 SHA-256 注入 freeze。程序本身用 `os.getloadavg()[0]` 再守门，preflight 年龄必须在 0–60 秒。程序不自行探测 memory 子进程、不读取凭据、不修改系统安全设置。机器 preflight 是本次执行资源门，不是科学数据。

phase costs 与 entry costs 都记录 wall/CPU/过程 peak RSS。全 SELF CPU 用绝对值，不从启动后的某个值减去。最终 receipt 序列化也计费；`completion.json` 记录 result serialization 后的累计时间。completion 最后几个字节、解释器退出与整个 launch 仍由 root 的 `/usr/bin/time -l` 外层收据完整覆盖，不能拿 SQL-only elapsed 声称性能胜利。

## 必须先补齐的 gate

1. 第 12 轮作者 freeze 路径与 SHA-256 已固定；root 另行确认独审通过，独审证据 SHA 已记入 freeze，不以作者 freeze 代替独审。
2. 保存 `code/source_snapshot_disabled.py`，对确切 source 做作者之外的独立静态审查；freeze 保留 author/reviewer 身份、review report SHA 与审过的 disabled SHA。
3. root 将 code、protocol、静态审查结论冻结；只在批准后对执行副本把唯一开关改为 True，保留 disabled snapshot，并记录执行源 SHA。不得趁机改构造、期望、分母或预算。
4. fresh preflight 的精确 hash 注入 freeze，外层 launch receipt 预先准备好。此前不得导入、compile、执行、SQL 或枚举。一次尝试而已，超限/失败截尾，不追加“修到通过”的实验。

当前 unknown：第 13 轮代码独审批准、SQLite 的实际限制/PRAGMA 能力、98 实际行集合/哈希、196 实際 SQL 数字、全部实际成本以及实际资源门。root 只 import 元数据确认 Python 3.12.13 / SQLite 3.53.3 并提供 binary/extension SHA，未连接 DB；该信息记录在 freeze，不能宣称 SQL 能力已运行验证。没有 source-pinned 新外部文献，也不作新颖性/覆盖率外推；外部数据集为 0，合成关系不是企业自然数据。DataHub 单入口规则不要求把本地一次性数学构造包装成自然数据或再注册外部源；继承第 12 轮既有的 DATAHUB_REGISTRATION_BLOCKED 状态，不借本复放绕过它。
