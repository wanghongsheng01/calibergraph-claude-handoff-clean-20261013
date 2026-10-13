# 冻结10例最终覆盖：没有新增准入槽位，保留科学负结论

本轮完成原冻结10例（不增加、不替换）的完整支持分类。其余8例中，**2例原输入无效，6例当前类型语义与完整C映射未准入**；因此新增科学运行清单为空，未启动worker或Z3，未使用60秒科学预算，未重跑旧两例。静态检查执行原DDL、PRAGMA与EXPLAIN，只生成元数据/编译结果，不执行查询数据计算。分类先保存于PRE_RUN_DECISION.json，再关闭本批。

这里的“未准入”是当前已审核适配合同的边界，不是证明Polygon原方法绝对不支持该任务，更不是求解超时或新方法胜利。没有以旧提取器不认识语法作为唯一依据：本轮从原DDL得到逐表逐列类型、默认值、PK/FK及索引清单，并核对完整固定源码的Int单元、CAST、日期解码和运算符路径。

| 冻结案例 | 原表/列 | 最终支持分类与证据 | UA | precise |
|---|---:|---|---|---|
| thrombosis #1172 | 3/64 | 类型语义未准入：T-BIL为REAL，原全DDL另含DATE；旧ParSEval假EQ及见证只作已暴露历史 | 静态NOT_RUN | 静态NOT_RUN |
| toxicology #319 | 4/11 | 复用pilot13；原两SQL字节相同 | 有界符号UNSAT | 有界符号UNSAT |
| thrombosis #1261 | 3/64 | 类型语义未准入：RF为TEXT却与20比较，SQLite亲和性/排序不能由字符串hash整数排序替代；全DDL含REAL/DATE | 静态NOT_RUN | 静态NOT_RUN |
| debit_card #1490 | 5/21 | 类型语义未准入：REAL消费、46.73、CAST及除法；重复/隐式目标REFERENCES、UNIQUE、AUTOINCREMENT需完整映射 | 静态NOT_RUN | 静态NOT_RUN |
| superhero #750 | 10/31 | 复用pilot13；两份保存见证按原DDL/SQL独立回放有效 | 已验证反例 | 已验证反例 |
| football #1073 | 7/199 | 类型/函数语义未准入：REAL、INT/VARCHAR别名及SUBSTR/strftime；未证明parser归一化后可由现有编码保真处理 | 静态NOT_RUN | 静态NOT_RUN |
| california #45 | 3/89 | 类型/完整C未准入：原全DDL含REAL/DATE；查询JOIN/AVG形态本身不能据此说实现缺失，N=1也不能暴露已有多行分组反例 | 静态NOT_RUN | 静态NOT_RUN |
| debit_card #1526 | 5/21 | 类型/表达式语义未准入：REAL/DATE、CAST/除法及标量子查询；LIKE已有实现分支，不能笼统称缺失 | 静态NOT_RUN | 静态NOT_RUN |
| california #26 | 3/89 | 无效原输入：EXPLAIN predicted报no such column: T1.Street，T1为frpm | 无效输入NOT_RUN | 无效输入NOT_RUN |
| student_club #1390 | 8/48 | 无效原输入：EXPLAIN predicted报no such column: T2.link_to_event，T2为expense | 无效输入NOT_RUN | 无效输入NOT_RUN |

全部10例保留分母；其中8个SQL对可编译、2个无效。当前完整C/类型生成与回放合同准入2例，其余6个有效输入未准入。20个潜在case×mode槽中，4槽来自pilot13已完成证据，16槽为本轮静态NOT_RUN。已有运行分类：2已验证反例、2有界符号UNSAT、0 unknown、0 timeout、0 error、0无效见证。这些0只属于4个实际运行槽；16个未运行槽没有被计成成功、UNSAT或求解失败。新增阶段成本为null（未运行），不能填写0毫秒冒称测量。全表均为开发材料，包括旧1172、新750/319；不是独立最终测试或总体成功率估计。

## 语义和完整C依据

所有40份原SQL/DDL/官方记录按冻结CANDIDATES逐字节哈希核验；ParSEval来源固定提交88cfe245bcf249a5b0df561a6b09c116ff2a2896、官方run37547685455、artifact11452059162。完整DDL原表均盘点，包括未被查询引用的表/列。SQLite自动sqlite_sequence不当源声明表；其AUTOINCREMENT来源保留在原DDL。

Polygon完整源码固定5e18237394d025dbb805cf833b4f54c321470774；pilot13运行时/输入336项哈希本轮全部一致。现有worker显式只把INTEGER映射int、TEXT映射varchar；所有SMT cell仍为Int，float literal路径返回Int包装，CAST路径返回原表达式，日期具体化对溢出值会截到日期边界。原方法的日期分支存在，不等于当前已验证了原SQLite全域日期/实数语义。没有静默把REAL改int、DATE改TEXT，或裁去无关表/列让某例成为“支持”。关于SUBSTR/strftime仅报告无直接编码分支；本轮没有运行parser，不能假装已观测动态unsupported。

现有生成→具体见证→原DDL/SQL回放可证明具体反例有效，却不能证明全类型域编码完备。已准入两例也只在N=1 typed fragment内解释UNSAT。#750负体重为源DDL允许的合成值，不是真实记录；没有事后补业务CHECK。#45旧多行分组反例不能靠N=1阴性结果推翻。来源和见证哈希绑定见COVERAGE_MATRIX.json、SOURCE_HASHES.json及独审证据。

## 资源与关闭记录

新增批次原授权为串行、整批科学墙钟60秒、每次Z3 3秒、每个原生Z3内部512MiB；不是总RSS硬限制。无准入槽位便不启动空科学批次或版本测试冒充执行。预检共同owned.lock可独占，记录loadavg约5.68/5.18/5.15；不把负载当unrelated_project状态证明，未查询其他进程或操作unrelated_project。仅短暂本地静态检查，无训练或队列。run_batch/slot_worker/生命周期组件直接复用其既有代码证据，因没有运行槽位而不制造新版适配器。旧NOT_RUN及唯一尝试标记保持原样。

## 唯一有证据支持的后续问题与停止条件

**在剩余6个有效输入保持原SQLite类型、原SQL与完整C的前提下，完成可审查的保真建模和具体化后，现有完整强基线是否出现可独立验证的失败？**

这是由当前支持边界提出的可检验问题，首先是语义准入与工程验证问题；本轮没有证明其新颖性，也没有证据支持新求解机制或成本优势。当前实际准入2/2案例已由完整方法处理，UA调用次数也无优势。应停止把这个补丁包装成CaliberGraph创新。

若后续获准做类型/约束适配，必须先冻结保真合同与失败分类，再在同一6例验证；非法模型、真实unknown/timeout、符号UNSAT和原SQL反例分列，不能修复见证后再宣称基线成功或失败。只有在准入闭合后仍有真实未解决缺口，才值得另提机制。**若完整方法覆盖所有有效且可用案例，应更换科学问题，不能继续换名包装支持补丁。** 本轮没有达到8/8有效输入覆盖，因此也不声称这项条件已经在全开发包成立。任何机制的最终验证仍须另留未暴露测试；本包没有这样的test。

独立审核与本轮对旧保存见证的独立回放另存review_local。原稿未改。作者交付可以私有备份，但原公共artifact长期恢复和专用DataHub登记的历史限制并未因分类完成而解除。
