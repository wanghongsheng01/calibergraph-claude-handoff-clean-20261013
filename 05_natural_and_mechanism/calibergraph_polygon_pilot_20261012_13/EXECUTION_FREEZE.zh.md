# 本次批准的执行合同

用户本次明确同意“Z3 内部分配限制＋整例60秒截止”，并已知它不保证整个进程实际内存不超过1GiB。该授权仅改变本轮保护合同，先前10/11/12包和NOT_RUN记录原样保留。授权由父任务提供逐字同意记录；不是本任务推定同意。

固定顺序：superhero #750 UA、#750 precise、toxicology #319 UA、#319 precise。N=1（每源表0或1活行），不强制非空，不换例、不重试。总控从四槽开始计单个60秒预算，包括worker启动、解析/编码、求解、回放与槽间清理；每槽另有12秒工作停止，目的是为其余槽保留预算，绝非每槽60秒。停止后回收宽限不冒称硬实时；父总控直接持有全部worker和Z3句柄，不留只由worker知道的孙进程。

每次 Z3 调用固定 `-T:3 -memory:512`。内存值512 MiB（512×1024×1024字节）作用于Z3内部计数，每个Z3进程分别应用，不是所有进程合计配额或OS RSS硬限制。Python父/worker仅采样各自RSS峰值，触发阈值仍1GiB，允许采样间超调；不读取被拒的外部RSS。不设新机器负载门槛。unrelated_project当前无训练依据本次用户/父任务陈述，未通过进程枚举验证。共享旧owned.lock本轮预检可独占、执行期间全程持有；新批次marker排他创建。

固定上游提交5e18237394d025dbb805cf833b4f54c321470774，新完整归档补足旧缺模块。24项旧快照与归档比较仅末尾换行不同，SOURCE.json保留两哈希。执行覆盖层的Environment、FormulaManager、SMTLIBv2为11包已审核三文件，其余为完整固定提交；不改原查询。所有新增依赖只安装到本目录，DEPENDENCIES.json记录wheel来源/版本/哈希，不声称原官方环境复现。

fullC：两例完整14表42列；12主键声明、13显式非空列、16外键。schema全列按原顺序放Others，类型INTEGER→int、TEXT→varchar，完整原PK/NOT NULL/FK通过既有约束入口逐项显式输入，避免隐式列重排和重复推断。没有删除无关表，没有添加Female=id2等业务事实，没有强制值范围/CHECK。原型FK额外写入env.integrity_constraints的辅助表非空条件沿原程序不加入实际公式；现已对完整固定源码核对无生效consumer。

类型语义准入为**有条件生成和逐见证验证**，不是整个SQLite值域形式化等价：SMT的无限Int及字符串hash不能代表SQLite所有affinity值；N=1时AVG对可准确表示的非NULL整数与单值一致，但大整数/浮点解码仍必须回放验证。生成值不做clamp、不补行、不更改NULL、不换值；越界或原DDL插入失败保留为非法见证。所有表列用原名插入原始DDL，开启SQLite外键并延迟到完整插入后检查、提交，回放原SQL的bag结果。只有fullC合法且原SQL结果不同才能称已验证NEQ。有界符号UNSAT不扩大为全域等价；unknown、timeout、EOF、unsupported和异常分开保留。

计时：记录导入、schema/C、parse、查询encode、search含solver、单次solver I/O、模型decode、SQLite replay。search与solver为嵌套时间，不可相加；query encode包含initializer，schema/C单独列。上游结果自带total_time并非完整墙钟，另保留控制器槽墙钟。3秒配置（尤其precise原300→3）和父子broker开销使数字不等于原baseline性能。无论结果如何都不据此宣称普遍方法优势。

准备阶段仅import和Z3版本metadata夹具，没有运行这两对查询。第一次broker夹具发现正常peer关闭的ConnectionResetError，已修正为等待自有worker退出；原失败目录保留、后续元数据夹具通过，科学marker仍未创建。最终冻结哈希在FREEZE.json；科学结束后不因结果修改实现再跑。
